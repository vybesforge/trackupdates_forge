"""VR12 camera validator. python tools/vr12_cams_validate.py [layout ...] [--png]. Exit 1 on any failure.
Per set (cameras.ini, cameras_1.ini, cameras_2.ini): header count matches, IN/OUT contiguous and covering exactly 0..1,
camera inside the map raster with known ground, height above ground in the set's range, not inside/under any mesh,
off every track surface (>= 5 m from all AI lines), clear line of sight to the car (0.8 m over the AI line) for every
AI point in its window, max camera-to-car distance (set 1 <= 110 m). --png renders docs_preview/cams_<layout>.png."""
import os, re, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vr12_cams as V
SETS = {'cameras.ini': ((1.5, 6.5), 110), 'cameras_1.ini': ((14, 31), 260), 'cameras_2.ini': ((0.7, 1.6), 95)}
def parse(p):
    s = open(p).read(); hdr = int(re.search(r'CAMERA_COUNT=(\d+)', s).group(1)); cams = []
    for b in re.split(r'\n(?=\[CAMERA_\d+\])', s)[1:]:
        g = lambda k: re.search(rf'^{k}=(.*)$', b, re.M).group(1).strip()
        cams.append(dict(pos=np.array([float(x) for x in g('POSITION').split(',')]), a=float(g('IN_POINT')), b=float(g('OUT_POINT')),
                         fov=(float(g('MIN_FOV')), float(g('MAX_FOV'))), name=g('NAME')))
    return hdr, cams
def check(lay):
    tr = V.Track(lay); errs = []; res = {}
    for fn, ((h0, h1), maxd) in SETS.items():
        hdr, cams = parse(f'{V.Z}{lay}/data/{fn}')
        if hdr != len(cams): errs.append(f'{fn}: CAMERA_COUNT {hdr} != {len(cams)}')
        e = 0.0
        for c in cams:
            if abs(c['a'] - e) > 1e-5: errs.append(f"{fn} {c['name']}: gap/overlap at {e:.6f} -> {c['a']:.6f}")
            e = c['b']
        if abs(e - 1) > 1e-5 or cams[0]['a'] != 0: errs.append(f'{fn}: coverage does not span 0..1 (ends {e})')
        worst = 1.0; wd = 0
        for c in cams:
            p = c['pos']; g = float(tr.ground(p[0], p[2]))
            if not np.isfinite(g): errs.append(f"{fn} {c['name']}: outside map"); continue
            if not h0 <= p[1] - g <= h1: errs.append(f"{fn} {c['name']}: height {p[1]-g:.1f} m outside {h0}-{h1}")
            if not tr.clear_spot(p, p[1] - g): errs.append(f"{fn} {c['name']}: inside/under geometry or on track")
            W = tr.idx(c['a'] * tr.len, c['b'] * tr.len); pts = tr.P[W]
            vis = tr.los(p, pts).mean(); d = np.linalg.norm(pts + [0, V.CAR_H, 0] - p, axis=1).max()
            worst = min(worst, vis); wd = max(wd, d)
            if vis < 1: errs.append(f"{fn} {c['name']}: LOS {vis:.3f}")
            if d > maxd: errs.append(f"{fn} {c['name']}: max distance {d:.0f} m > {maxd}")
        res[fn] = (len(cams), worst, wd); print(lay, fn, len(cams), 'cams, contiguous 0..1, min LOS %.3f, max dist %.0f m' % (worst, wd))
    return tr, errs
def png(lay, tr):
    import cv2
    G = tr.G; T = tr.S - tr.G; P = tr.P; x0, x1, z0, z1 = P[:, 0].min() - 80, P[:, 0].max() + 80, P[:, 2].min() - 80, P[:, 2].max() + 80
    sc = 1.6; Wd, Hh = int((x1 - x0) * sc), int((z1 - z0) * sc)
    to = lambda x, z: (int((x - x0) * sc), int((z - z0) * sc))
    img = np.full((Hh, Wd * 3, 3), 245, np.uint8)
    obst = np.nan_to_num(T) > 1.0; js, is_ = np.nonzero(obst)
    xs = R0 = V.R.BOX[0] + is_ * V.R.RES; zs = V.R.BOX[2] + js * V.R.RES
    cols = [(40, 40, 220), (220, 120, 30), (30, 160, 30)]
    for k, fn in enumerate(SETS):
        off = k * Wd; sub = img[:, off:off + Wd]
        u = ((xs - x0) * sc).astype(int); v = ((zs - z0) * sc).astype(int); ok = (u >= 0) & (u < Wd) & (v >= 0) & (v < Hh); sub[v[ok], u[ok]] = (200, 200, 200)
        for a in range(len(P)): cv2.line(sub, to(P[a - 1, 0], P[a - 1, 2]), to(P[a, 0], P[a, 2]), (90, 90, 90), 2)
        _, cams = parse(f'{V.Z}{lay}/data/{fn}')
        for i, c in enumerate(cams):
            W = tr.idx(c['a'] * tr.len, c['b'] * tr.len); col = cols[i % 3]
            for q in W[::3]: cv2.line(sub, to(c['pos'][0], c['pos'][2]), to(P[q, 0], P[q, 2]), tuple(int(x * 0.5 + 127) for x in col), 1)
            for q in range(1, len(W)): cv2.line(sub, to(*P[W[q - 1]][[0, 2]]), to(*P[W[q]][[0, 2]]), col, 4)
            cv2.circle(sub, to(c['pos'][0], c['pos'][2]), 5, (0, 0, 0), -1); cv2.putText(sub, str(i), to(c['pos'][0] + 4, c['pos'][2]), 0, 0.45, (0, 0, 0), 1)
        cv2.putText(sub, f'{lay} {fn} ({len(cams)} cams)  x right, z down', (10, 25), 0, 0.8, (0, 0, 0), 2)
    out = f'/workspace/rpotm/docs_preview/cams_{lay}.png'; cv2.imwrite(out, img); print('wrote', out)
if __name__ == '__main__':
    lays = [a for a in sys.argv[1:] if not a.startswith('--')] or ['main', 'short']; bad = []
    for l in lays:
        tr, e = check(l); bad += e
        if '--png' in sys.argv: png(l, tr)
    for e in bad: print('FAIL', e)
    print('ALL OK' if not bad else f'{len(bad)} failures'); sys.exit(1 if bad else 0)
