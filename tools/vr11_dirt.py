"""VR11 (b): make gravel / dirt surfaces readable.
 1. own_gravel(_nm,_maps).dds (paddock lot 1GRAVEL_PADDOCK, north-extension shoulders/lot 1GRAVEL_EXT_*): rebuilt from two
    ambientCG gravels (Gravel022 + Gravel040, CC0) blended by a seamless low-frequency mask, with slight tan/grey colour
    variation, more local contrast, stronger normal map and roughness-derived maps.  Same 2 m UV tile, UVs untouched.
 2. Ground layers of the ortho-photo terrain shader (ksMultilayer 'google' / 'ext_ground'):
    txDetailB 'concrete_seams.dds' is the ROAD/GRAVEL mask layer (google_mask B: dirt tracks, paddock, lots).  It was a
    concrete-with-joints texture, which is why dirt tracks read as smeared concrete.  Now a compacted gravel-road texture
    (ambientCG Gravel023 stones in Ground054 fines).  txDetailG 'Muld Detailne.dds' (bare soil) -> Ground054+Ground068 dirt.
 3. Tyre ruts: dirt tracks are found in google_mask B (thin features 2.5-8 m wide, not under any paved physics mesh, near
    the venue), skeletonised, and two soft dark wheel tracks (0.45 m wide, 1.65 m track) are laid along them as an
    alpha-blended, shadowless decal in the new vf_ruts.kn5, draped on the terrain mesh +2.5 cm.
Run once from the repo root (idempotent: rebuilds from the VR11 backup)."""
import os, sys, io, glob, math, struct, numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K, kn5write as W, build_open_textures as B
from vr10_faces import read_meshes
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); TR = ROOT + '/' + os.environ.get('TRACK_DIR', 'vf_i29_speedway') + '/'
rng = np.random.default_rng(3429)
def pnoise(w, h, cyc):  # seamless (periodic) value noise with ~cyc blobs per tile
    f = np.fft.fft2(rng.standard_normal((h, w))); fy = np.fft.fftfreq(h)[:, None] * h; fx = np.fft.fftfreq(w)[None] * w
    g = np.exp(-(fx ** 2 + fy ** 2) / (2 * cyc ** 2)); n = np.real(np.fft.ifft2(f * g)); n -= n.min(); return (n / n.max()).astype(np.float32)
def ss(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def cc(id_, m, w, h): return B.fit(B.cc(id_, m), w, h).astype(np.float32)
def local_contrast(img, amt=0.35, r=9):
    bl = cv2.GaussianBlur(img, (0, 0), r); return np.clip(img + (img - bl) * amt, 0, 255)
def gravel(w, h):
    m = ss(pnoise(w, h, 3), 0.35, 0.65)[..., None]; c1 = cc('Gravel022', 'Color', w, h); c2 = cc('Gravel040', 'Color', w, h)
    c2 = (c2 - c2.mean((0, 1))) * (c1.std((0, 1)) / (c2.std((0, 1)) + 1e-3)) + c1.mean((0, 1))
    rgb = c1 * (1 - m) + c2 * m
    v = pnoise(w, h, 2)[..., None]; tan = np.array([1.06, 1.0, 0.90]); grey = np.array([0.95, 0.98, 1.02])
    rgb = rgb * (grey * (1 - v) + tan * v) * (0.92 + 0.16 * pnoise(w, h, 5)[..., None])
    rgb = local_contrast(rgb)
    n1 = cc('Gravel022', 'NormalDX', w, h); n2 = cc('Gravel040', 'NormalDX', w, h); n = n1 * (1 - m) + n2 * m
    xy = (n[..., :2] - 128) * 1.35; z = np.sqrt(np.clip(127 ** 2 - (xy ** 2).sum(2), 0, None))
    nm = np.dstack([xy + 128, z + 128]).clip(0, 255)
    r = cc('Gravel022', 'Roughness', w, h)[..., 0] * (1 - m[..., 0]) + cc('Gravel040', 'Roughness', w, h)[..., 0] * m[..., 0]
    return rgb.astype(np.uint8), nm.astype(np.uint8), r
def dirtroad(w, h):
    g = cc('Gravel023', 'Color', w, h); d = cc('Ground054', 'Color', w, h); g = (g - g.mean((0, 1))) * 0.8 + d.mean((0, 1)) * 1.1; gm = 0.25 + 0.3 * pnoise(w, h, 20)[..., None]
    rgb = d * (1 - gm) + g * gm; rgb *= (0.9 + 0.2 * pnoise(w, h, 2)[..., None]) * np.array([1.03, 1.0, 0.94]); return local_contrast(rgb, 0.3).astype(np.uint8)
def soil(w, h):
    a = cc('Ground054', 'Color', w, h); b = cc('Ground068', 'Color', w, h); b = (b - b.mean((0, 1))) * (a.std((0, 1)) / (b.std((0, 1)) + 1e-3)) + a.mean((0, 1))
    m = ss(pnoise(w, h, 3), 0.3, 0.7)[..., None]; rgb = a * (1 - m) + b * m; rgb *= (0.92 + 0.16 * pnoise(w, h, 4)[..., None]); return local_contrast(rgb, 0.3).astype(np.uint8)
def dds_like(old, rgba):
    w, h, mm, fmt = B.info(old); return B.write_dds(rgba, fmt, 1 if mm == 1 else int(math.log2(max(w, h))) + 1, old[:128])
def keep_alpha(old, w, h):
    o = np.array(Image.open(io.BytesIO(old)).convert('RGBA'))[..., 3]; return cv2.resize(o, (w, h))
def textures():
    out = {}; prev = {}
    for fn in ('vf_i29_speedway_own.kn5', 'vf_ext.kn5', 'vf_i29_speedway.kn5'):
        p = TR + fn; names = [t[0] for t in K.scan(p)[0]]; rep = {}
        for n in names:
            old = K.get_tex(p, n); w, h, _, _ = B.info(old); key = (n, w, h)
            if key not in out:
                if n == 'own_gravel.dds': rgb, nm, r = gravel(w, h); out[key] = rgb; out[('own_gravel_nm.dds', w, h)] = nm; out[('_rough', w, h)] = r
                elif n == 'own_gravel_nm.dds' and ('own_gravel_nm.dds', w, h) not in out: out[key] = gravel(w, h)[1]
                elif n == 'own_gravel_maps.dds':
                    r = cv2.resize(next(v for k, v in out.items() if k[0] == '_rough'), (w, h)); g = 255 - r
                    out[key] = np.dstack([g * 0.25, g, np.zeros_like(g)]).clip(0, 255).astype(np.uint8)
                elif n == 'concrete_seams.dds': out[key] = dirtroad(w, h)
                elif n == 'Muld Detailne.dds': out[key] = soil(w, h)
                else: continue
            nc = out[key][..., :3].astype(np.float32)
            if not n.endswith('_nm.dds') and not n.endswith('_maps.dds'):   # keep each layer's overall brightness/tint: the shader mixes these with the ortho photo
                om = np.array(Image.open(io.BytesIO(old)).convert('RGB')).reshape(-1, 3).mean(0); nc = nc * (om / (nc.reshape(-1, 3).mean(0) + 1e-3))
            rgba = np.dstack([np.clip(nc, 0, 255), keep_alpha(old, w, h)]).astype(np.uint8); rep[n] = dds_like(old, rgba)
            prev.setdefault(n, (np.array(Image.open(io.BytesIO(old)).convert('RGB')), rgba[..., :3]))
        if rep: K.patch(p, p + '.tmp', texrep=rep); os.replace(p + '.tmp', p); K.scan(p); print(fn, 'replaced', sorted(rep))
    return prev
# ---------------- ruts
UC = (6.4e-6, -2.631e-4, 0.3065788); VC = (5.268e-4, 1.27e-5, 1 - 0.4465427)   # v wraps: texture v = frac(mesh v)
def ruts():
    p = TR + 'vf_i29_speedway.kn5'; msk = np.array(Image.open(io.BytesIO(K.get_tex(p, 'google_mask.dds'))).convert('RGBA')); H, Wd = msk.shape[:2]
    A = np.array([[UC[0], UC[1]], [VC[0], VC[1]]]); Ai = np.linalg.inv(A)
    def px2w(px, py): u = (px + 0.5) / Wd; v = (py + 0.5) / H; xz = Ai @ np.vstack([u - UC[2], v - VC[2]]); return xz[0], xz[1]
    def w2px(x, z): return (UC[0] * x + UC[1] * z + UC[2]) * Wd - 0.5, (VC[0] * x + VC[1] * z + VC[2]) * H - 0.5
    mpp = 1 / (abs(UC[1]) * Wd)
    # paved / other physics footprint (anything physical that is not the ortho terrain)
    paved = np.zeros((H, Wd), np.uint8)
    for f in glob.glob(TR + '*.kn5'):
        try: ms = read_meshes(f)
        except Exception: continue
        for m in ms:
            if m['name'][0] != '1' or m['name'].startswith(('1GRASS',)): continue
            V = m['verts']; I = m['idx'].reshape(-1, 3).astype(int); qx, qy = w2px(V[:, 0], V[:, 2]); P = np.c_[qx, qy].astype(np.int32)
            for t in I: cv2.fillConvexPoly(paved, P[t], 255)
    paved = cv2.dilate(paved, np.ones((9, 9), np.uint8))
    B_ = (msk[..., 2] > 128).astype(np.uint8); B_ = cv2.morphologyEx(B_, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); B_ = cv2.morphologyEx(B_, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    B_[paved > 0] = 0
    # pond shores are mud banks, not tracks: drop anything within 8 m of open water (dark ortho pixels)
    g2 = np.array(Image.open(io.BytesIO(K.get_tex(p, 'google2.dds'))).convert('RGB')).astype(np.float32)
    water = ((g2.mean(2) < 70) & (g2[..., 0] >= g2[..., 1])).astype(np.uint8); water = cv2.morphologyEx(water, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    B_[cv2.dilate(water, np.ones((35, 35), np.uint8)) > 0] = 0
    # venue region: within 450 m of the paddock / track
    yy, xx = np.mgrid[0:H, 0:Wd]; cx, cy = w2px(60.0, 0.0); B_[np.hypot(xx - cx, yy - cy) * mpp > 450] = 0
    dt = cv2.distanceTransform(B_, cv2.DIST_L2, 5) * mpp
    from skimage.morphology import skeletonize
    sk = skeletonize(B_ > 0) & (dt > 1.25) & (dt < 4.0)
    print('dbg B', int(B_.sum()), 'paved', int((paved>0).sum()), 'sk', int(sk.sum()), 'mpp', round(mpp,3))
    n, lab = cv2.connectedComponents(sk.astype(np.uint8), connectivity=8)
    terr = [m for m in read_meshes(p) if m['name'].startswith('1GRASS')]
    from scipy.spatial import cKDTree
    TT = np.concatenate([m['verts'][m['idx'].reshape(-1, 3).astype(int)][:, :, :3] for m in terr]).astype(np.float64)
    ctr = cKDTree(TT[:, :, [0, 2]].mean(1))
    def hgt(x, z):
        out = np.full(len(x), np.nan); _, ix = ctr.query(np.c_[x, z], k=48)
        for j in range(ix.shape[1]):
            t = TT[ix[:, j]]; a, b_, c = t[:, 0], t[:, 1], t[:, 2]
            v0 = b_[:, [0, 2]] - a[:, [0, 2]]; v1 = c[:, [0, 2]] - a[:, [0, 2]]; v2 = np.c_[x, z] - a[:, [0, 2]]
            den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]; den[np.abs(den) < 1e-9] = np.nan
            l1 = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den; l2 = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den; l0 = 1 - l1 - l2
            ins = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6); y = l0 * a[:, 1] + l1 * b_[:, 1] + l2 * c[:, 1]
            k = ins & (np.isnan(out) | (y > out)); out[k] = y[k]
        return out
    paths = []
    for c in range(1, n):
        ys, xs = np.nonzero(lab == c)
        if len(xs) * mpp < 30: continue
        # order pixels along the component: greedy nearest-neighbour walk from an endpoint
        pts = np.c_[xs, ys].astype(float); from scipy.spatial import cKDTree
        tr = cKDTree(pts); deg = np.array([len(tr.query_ball_point(q, 1.5)) - 1 for q in pts]); start = int(np.argmin(deg))
        used = np.zeros(len(pts), bool); cur = start; seq = [cur]; used[cur] = True
        while True:
            d, ix = tr.query(pts[cur], k=min(12, len(pts)))
            nxt = [j for dd, j in zip(np.atleast_1d(d), np.atleast_1d(ix)) if not used[j] and dd < 2.5]
            if not nxt:
                if len(seq) * mpp > 30: paths.append(pts[seq])
                rest = np.nonzero(~used)[0]
                if not len(rest): break
                cur = int(rest[0]); seq = [cur]; used[cur] = True; continue
            cur = nxt[0]; used[cur] = True; seq.append(cur)
    Vs = []; Is = []; nv = 0; total = 0.0
    for P in paths:
        x, z = px2w(P[:, 0], P[:, 1]); xy = np.c_[x, z]
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
        if seg[-1] < 30: continue
        s = np.arange(0, seg[-1], 1.0); xy = np.c_[np.interp(s, seg, xy[:, 0]), np.interp(s, seg, xy[:, 1])]
        xy = cv2.GaussianBlur(xy.reshape(-1, 1, 2).astype(np.float32), (1, 9), 0).reshape(-1, 2) if len(xy) > 9 else xy
        t = np.gradient(xy, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9; nrm = np.c_[-t[:, 1], t[:, 0]]
        for off in (-0.825, 0.825):
            L = xy + nrm * (off - 0.225); R = xy + nrm * (off + 0.225); Q = np.r_[L, R]; hh = hgt(Q[:, 0], Q[:, 1])
            ok = np.isfinite(hh[:len(L)]) & np.isfinite(hh[len(L):])
            # break the strip where the terrain is missing; emit runs
            runs = np.split(np.arange(len(L)), np.nonzero(~ok)[0])
            for r in runs:
                r = r[ok[r]]
                if len(r) < 6: continue
                if nv + 2 * len(r) > 60000: Vs.append(None); nv = 0
                vv = []
                for k_, i in enumerate(r):
                    for side, PP, hy in ((0, L, hh[i]), (1, R, hh[len(L) + i])): vv.append([PP[i, 0], hy + 0.025, PP[i, 1], 0, 1, 0, side, s[i] / 4.0, 1, 0, 0])
                vv = np.array(vv, np.float32); m_ = len(r); ii = []
                for k_ in range(m_ - 1): a = nv + 2 * k_; ii += [(a, a + 2, a + 1), (a + 1, a + 2, a + 3)]
                Vs.append(vv); Is.append(np.array(ii)); nv += len(vv); total += (len(r) - 1)
    # group into meshes <65k verts
    meshes = []; cv_ = []; ci = []; off = 0
    def flush():
        if cv_:
            V = np.concatenate(cv_); I = np.concatenate(ci); meshes.append(dict(name='vf_ruts_%02d' % len(meshes), mat_index=0, verts=V, idx=I.astype('<u2'), flags=(0, 1, 1)))
    k = 0
    for V in Vs:
        if V is None: flush(); cv_.clear(); ci.clear(); off = 0; continue
        I = Is[k]; k += 1; base = I.min(); cv_.append(V); ci.append(I - base + off); off += len(V)
    flush()
    for m in meshes: m['idx'] = W_fix(m['verts'], m['idx'])
    return meshes, total, paths
def W_fix(V, I):
    from vr5_meshlib import fix_winding
    return fix_winding(V, np.asarray(I, int)).astype('<u2')
def rut_texture():
    w, h = 64, 512; x = np.linspace(-1, 1, w); prof = np.exp(-(x / 0.55) ** 4)
    a = prof[None, :] * (0.55 + 0.45 * B.noise(w, h, 24)) ; a = (np.clip(a, 0, 1) * 0.55 * 255).astype(np.uint8)
    d = cc('Ground054', 'Color', w, h) * np.array([0.62, 0.58, 0.52])
    return np.dstack([d.astype(np.uint8), a])
def build_ruts():
    meshes, total, paths = ruts(); tex = rut_texture(); b = io.BytesIO(); Image.fromarray(tex, 'RGBA').save(b, 'DDS', pixel_format='DXT5')
    tpl = W.read_materials(TR + 'vf_i29_speedway_own.kn5')['own_gravel']
    props = [(n, raw) for n, raw in tpl['props'] if n in ('ksAmbient', 'ksDiffuse', 'ksSpecular', 'ksSpecularEXP', 'ksEmissive', 'ksAlphaRef')]
    mat = dict(name='vf_ruts', shader='ksPerPixel', ab=1, at=0, dm=1, props=props, samplers=[('txDiffuse', 0, 'vf_ruts.dds')])
    W.write_kn5(TR + 'vf_ruts.kn5', [('vf_ruts.dds', b.getvalue())], [mat], meshes, rootname='vf_ruts'); K.scan(TR + 'vf_ruts.kn5')
    for ini in glob.glob(TR + 'models_*.ini'):
        s = open(ini).read()
        if 'vf_ruts.kn5' not in s:
            n = len([l for l in s.splitlines() if l.startswith('[MODEL_')]); s = s.rstrip('\n') + f'\n\n[MODEL_{n}]\nFILE=vf_ruts.kn5\nPOSITION=0,0,0\nROTATION=0,0,0\n'; open(ini, 'w').write(s)
    print('ruts: %d meshes, %.0f m of wheel track (x2), %d paths' % (len(meshes), total, len(paths)), [(m['name'], len(m['idx']) // 3) for m in meshes])
    return paths
if __name__ == '__main__':
    prev = {} if os.environ.get('RUTS_ONLY') else textures(); paths = build_ruts()
    os.makedirs('/workspace/vr11/dirt', exist_ok=True)
    for n, (a, b) in prev.items():
        s = 512; A = cv2.resize(a[:s * 2, :s * 2] if a.shape[0] >= 1024 else a, (s, s)); Bb = cv2.resize(b[:s * 2, :s * 2] if b.shape[0] >= 1024 else b, (s, s))
        Image.fromarray(np.hstack([A, np.full((s, 8, 3), 255, np.uint8), Bb])).save('/workspace/vr11/dirt/%s_before_after.png' % n.replace(' ', '_')[:-4])
    np.save('/workspace/vr11/dirt/paths.npy', np.array(paths, dtype=object), allow_pickle=True)
