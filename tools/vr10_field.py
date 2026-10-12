"""VR10: full-map lidar field including the north extension (z -2400..-3000 + the long access road).
T(x,z)   = w_all * (F_all - F(start/finish))   (same recipe as vr9: normalised convolution over ALL paved cells,
           sigma 10 m, blended to sigma 25 m terrain, sigma 6 m smooth; taper 120 -> 400 m from pavement)
           + road-grade limiting on the extension (iterated smoothing over extension pavement until grade <= 6 %)
T_final  = we * D_vr9 + (1 - we) * T,   we = 0 within 25 m of extension pavement -> 1 at 85 m
           (so the VR9 main-track field is kept bit-for-bit away from the extension).
Grid = the full-map 1 m raster of tools/vr9_holecheck.py (cov_fullold = flat stage). DEM: docs/elevation/dem_crop_1m_wide.tif."""
import os, sys, numpy as np, rasterio
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vr7_common as C
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = np.load('/workspace/rpotm/geo/xz_to_utm.npy')
PAVED = {'ROAD', 'CURB', 'PITS', 'CONCRETE', 'DRAG', 'LAUNCHA', 'LAUNCHB', 'LAUNCHC', 'XROAD', 'XLOT', 'GRAVEL', 'SCUT'}
EXTK = ('XROAD', 'XLOT', 'GRAVEL_EXT')
SF = (-224.27, -291.61)
OUT = '/workspace/vr10/field.npz'
def smooth(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def build():
    r = np.load('/workspace/vr9/cov_fullold.npz', allow_pickle=True); xs, zs = r['xs'], r['zs']
    names = [str(n) for n in r['names']]; Kd = C.keys()
    kn = np.array([(C.mesh_key(n, Kd) or '') for n in names] + ['']); KEY = r['KEY']
    isext = np.array([n.startswith(('1XROAD', '1XLOT', '1GRAVEL_EXT')) for n in names] + [False])
    pav = np.isin(kn[KEY], list(PAVED)) & r['UP']; epav = pav & isext[KEY]
    X, Zg = np.meshgrid(xs, zs)
    dr = rasterio.open(f'{ROOT}/docs/elevation/dem_crop_1m_wide.tif'); Dm = dr.read(1).astype(np.float64); Ti = ~dr.transform
    u = np.c_[X.ravel(), Zg.ravel(), np.ones(X.size)] @ A; c, rr = Ti * (u[:, 0], u[:, 1])
    dem = ndimage.map_coordinates(Dm, [rr - 0.5, c - 0.5], order=1, mode='nearest').reshape(X.shape).astype(np.float32)
    M = pav.astype(np.float64)
    num = ndimage.gaussian_filter(M * dem, 10); den = ndimage.gaussian_filter(M, 10); Fp = num / np.maximum(den, 1e-9)
    Ft = ndimage.gaussian_filter(dem.astype(np.float64), 25); a = np.clip(den / 0.15, 0, 1); F = ndimage.gaussian_filter(a * Fp + (1 - a) * Ft, 6)
    dist = ndimage.distance_transform_edt(~pav); w = smooth(1 - (dist - 120) / 280)
    j0, i0 = int(round(SF[1] - zs[0])), int(round(SF[0] - xs[0])); f0 = F[j0, i0]
    T = w * (F - f0)
    de = ndimage.distance_transform_edt(~epav); we = smooth((de - 25) / 60)
    # grade limiting on extension pavement: blend in a heavier smooth where the grade exceeds 6 %
    band = de < 30
    for it in range(12):
        gz, gx = np.gradient(T); g = np.hypot(gx, gz)
        bad = band & (g > 0.06)
        if not bad.any(): break
        Ts = ndimage.gaussian_filter(T, 12)
        m = ndimage.gaussian_filter(ndimage.binary_dilation(bad, iterations=30).astype(float), 10)
        T = T * (1 - m) + Ts * m
        print('grade iter', it, 'cells > 6 %', int(bad.sum()))
    # VR9 field on this grid
    f9 = np.load('/workspace/vr9/field.npz')['D']; D9 = np.zeros_like(T)
    gj = np.arange(len(zs)) + int(zs[0] - (-1400.0)); gi = np.arange(len(xs)) + int(xs[0] - (-800.0))
    vj = (gj >= 0) & (gj < f9.shape[0]); vi = (gi >= 0) & (gi < f9.shape[1])
    D9[np.ix_(vj, vi)] = f9[np.ix_(gj[vj], gi[vi])]
    Tf = we * D9 + (1 - we) * T
    gz, gx = np.gradient(Tf); g = np.hypot(gx, gz)
    os.makedirs('/workspace/vr10', exist_ok=True)
    np.savez(OUT, xs=xs, zs=zs, Tf=Tf.astype(np.float32), D9=D9.astype(np.float32), we=we.astype(np.float32), epav=epav, pav=pav, dem=dem)
    print('ext pavement cells', int(epav.sum()), 'Tf on ext pavement: min/max/rms', float(Tf[epav].min()), float(Tf[epav].max()), float(np.sqrt((Tf[epav] ** 2).mean())))
    print('max grade on ext pavement %', float(g[epav].max() * 100), 'p99', float(np.percentile(g[epav], 99) * 100))
    tp = pav & ~epav; print('change vs VR9 on track pavement: max', float(np.abs(Tf - D9)[tp].max()), 'cells > 1 mm', int((np.abs(Tf - D9)[tp] > 0.001).sum()))
def load():
    f = np.load(OUT); return f
def evaluate(f, x, z, key='Tf'):
    return ndimage.map_coordinates(f[key], [np.asarray(z, float) - float(f['zs'][0]), np.asarray(x, float) - float(f['xs'][0])], order=1, mode='nearest')
if __name__ == '__main__': build()
