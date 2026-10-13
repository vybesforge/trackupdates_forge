"""VR12: rebuild the replay/TV cameras from scratch for both layouts, using the AI fast_lane spline for
IN_POINT/OUT_POINT (normalized spline position = cumulative length / lap length, point 0 = 0).
  Set 1 cameras.ini   "TV Trackside": one camera per corner, close to apex/exit on the outside (8-20 m off the line,
                      2-6 m above ground); straights get a mid camera and a braking-zone camera (more if long).
                      Cuts at corner entries. Windows are split until the max camera-to-car distance is small.
  Set 2 cameras_1.ini "TV High": elevated wide shots, 15-30 m above ground, 25-60 m off the line.
  Set 3 cameras_2.ini "TV Kerbside": low (0.8-1.5 m) close cameras 5-9 m off the line at corners and along straights.
Every candidate camera is checked against the 0.5 m rasters from tools/vr12_camraster.py: not inside any mesh
(buildings, fences, trees, props), not on any track surface, line of sight to the car (0.8 m above the AI line)
over its whole window. FOV: MIN_FOV is used when the car is far, MAX_FOV when near (frames ~12 m at the far end,
~24 m close, clamped 6-60 deg). IS_FIXED=0 (camera turns to follow the car).
Usage: python tools/vr12_cams.py [main short]   (originals backed up to assets_src/cameras_zwiss_orig/<layout>/)"""
import os, sys, shutil, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vr7_common as C, vr12_camraster as R
Z = C.Z; ROOT = os.path.dirname(Z.rstrip('/'))
CAR_H = 0.8
class Track:
    def __init__(s, lay):
        a = C.read_ai(f'{Z}{lay}/ai/fast_lane.ai'); s.P = a['P']['p'].astype(float); n = len(s.P)
        seg = np.linalg.norm(np.diff(np.r_[s.P, s.P[:1]], axis=0), axis=1); s.L = np.r_[0, np.cumsum(seg)[:-1]]; s.len = seg.sum()
        t = np.roll(s.P, -1, 0) - np.roll(s.P, 1, 0); s.hd = np.arctan2(t[:, 2], t[:, 0]); s.n = n
        s.N = np.c_[-t[:, 2], np.zeros(n), t[:, 0]]; s.N /= np.linalg.norm(s.N, axis=1)[:, None]   # left/right normal (sign checked by curvature)
        G, T = R.build(lay); s.G = G; s.S = np.fmax(G, np.nan_to_num(T, nan=-1e9)); s.S[~np.isfinite(s.S)] = np.nan
        sp = np.median(seg); w = max(3, int(12 / sp))                    # curvature, smoothed over ~25 m
        dh = np.angle(np.exp(1j * (np.roll(s.hd, -w) - np.roll(s.hd, w)))); s.k = dh / (2 * w * sp)
        s.track_pts = [C.read_ai(f'{Z}{l}/ai/fast_lane.ai')['P']['p'].astype(float) for l in ('main', 'short')]
        s.track_pts += [C.read_ai(f'{Z}{lay}/ai/pit_lane.ai')['P']['p'].astype(float)]
        s.allp = np.vstack(s.track_pts)[:, [0, 2]]
    def cell(s, x, z):
        i = ((np.asarray(x) - R.BOX[0]) / R.RES).astype(int); j = ((np.asarray(z) - R.BOX[2]) / R.RES).astype(int)
        ok = (i >= 0) & (i < s.G.shape[1]) & (j >= 0) & (j < s.G.shape[0]); return np.clip(j, 0, s.G.shape[0] - 1), np.clip(i, 0, s.G.shape[1] - 1), ok
    def ground(s, x, z): j, i, ok = s.cell(x, z); g = s.G[j, i]; return np.where(ok, g, np.nan)
    def surf(s, x, z): j, i, ok = s.cell(x, z); g = s.S[j, i]; return np.where(ok, g, np.nan)
    def idx(s, a, b):   # point indices of window [a,b) in metres along lap (wraps)
        w = b - a; a = a % s.len; b = a + w
        L = s.L; return np.nonzero((L >= a) & (L < b))[0] if b <= s.len else np.r_[np.nonzero(L >= a)[0], np.nonzero(L < b - s.len)[0]]
    def los(s, c, pts):
        out = np.ones(len(pts), bool)
        for q, p in enumerate(pts):
            tgt = p + [0, CAR_H, 0]; d = np.linalg.norm(tgt - c); m = max(2, int(d / 0.4))
            u = np.linspace(0, 1, m)[1:-1]; u = u[(u * d > 1.0) & ((1 - u) * d > 2.5)]
            X = c + u[:, None] * (tgt - c); h = s.surf(X[:, 0], X[:, 2])
            out[q] = not np.any(np.nan_to_num(h, nan=1e9) > X[:, 1] + 0.05)
        return out
    def clear_spot(s, c, h):
        # camera not inside/under anything: top surface within 1.5 m must be below the camera, ground known, off every track
        r = np.arange(-1.5, 1.51, 0.5); X, Zz = np.meshgrid(c[0] + r, c[2] + r); top = s.surf(X.ravel(), Zz.ravel())
        if np.isnan(top).any() or top.max() > c[1] - 0.3: return False
        return np.min(np.hypot(*(s.allp - [c[0], c[2]]).T)) >= max(5.0, 0.0)
def fov_for(dmin, dmax, near_w=24, far_w=12):
    f = lambda w, d: float(np.clip(np.degrees(2 * np.arctan(w / 2 / max(d, 1))), 6, 60))
    return round(f(far_w, dmax), 1), round(f(near_w, dmin), 1)
def solve(tr, a, b, anchor_m, side, spec):
    """best camera for window [a,b) metres. side: +1/-1 preferred (outside), spec: offsets, heights, shifts."""
    W = tr.idx(a, b); pts = tr.P[W]
    if not len(W): return None
    best = None
    for sd in (side, -side):
        for sh in spec['shift']:
            k = int(np.argmin(np.abs(((tr.L - (anchor_m + sh)) + tr.len / 2) % tr.len - tr.len / 2))); p = tr.P[k]; nrm = tr.N[k] * sd
            for off in spec['off']:
                for h in spec['h']:
                    x, z = p[0] + nrm[0] * off, p[2] + nrm[2] * off; g = tr.ground(x, z)
                    if not np.isfinite(g): continue
                    c = np.array([x, g + h, z])
                    if not tr.clear_spot(c, h): continue
                    vis = tr.los(c, pts); f = vis.mean(); d = np.linalg.norm(pts + [0, CAR_H, 0] - c, axis=1)
                    score = (round(f, 3), -(sd != side), -d.max() - spec.get('hw', 3) * abs(h - spec['h'][0]) - 8 * (off < spec['off'][0]))
                    if best is None or score > best[0]: best = (score, c, vis, d, sd, off, h)
            if best and best[0][0] >= 0.999 and best[0][1] == 0: break
        if best and best[0][0] >= 0.999 and best[0][1] == 0: break
    if best is None: return None
    sc, c, vis, d, sd, off, h = best
    return dict(a=a, b=b, pos=c, los=float(vis.mean()), dmin=float(d.min()), dmax=float(d.max()), side=int(sd), off=off, h=h, anchor=anchor_m)
def place(tr, windows, spec, maxd, minlen=30):
    out = []
    stack = list(windows)[::-1]
    while stack:
        a, b, anc, side, tag = stack.pop()
        r = solve(tr, a, b, anc, side, spec)
        if (r is None or r['los'] < 0.995 or r['dmax'] > maxd) and b - a > 2 * minlen:
            m = (a + b) / 2; stack += [(m, b, (m + b) / 2, side, tag), (a, m, (a + m) / 2, side, tag)]; continue
        if r is None: raise SystemExit(f'no camera for window {a:.0f}-{b:.0f} m')
        r['tag'] = tag; out.append(r)
    return out
def corners(tr, kth=1 / 120):
    on = np.abs(tr.k) > kth; segs = []; i = 0; n = tr.n
    # rotate so we start on a straight
    st = int(np.argmin(np.abs(tr.k))); idx = np.r_[st:n, 0:st]; cur = None
    for q in idx:
        if on[q] and cur is None: cur = [q]
        elif on[q]: cur.append(q)
        elif cur is not None: segs.append(cur); cur = None
    if cur: segs.append(cur)
    out = []
    for sgm in segs:
        Ls = tr.L[sgm]; ln = (Ls[-1] - Ls[0]) % tr.len
        if ln < 12: continue
        ap = sgm[int(np.argmax(np.abs(tr.k[sgm])))]
        out.append(dict(entry=float(tr.L[sgm[0]]), exit=float(tr.L[sgm[-1]]), apex=float(tr.L[ap]), sign=float(np.sign(tr.k[ap])), kmax=float(np.abs(tr.k[ap]))))
    out.sort(key=lambda c: c['entry'])
    m = []   # merge corners closer than 35 m (chicanes/esses stay one camera only if same direction)
    for c in out:
        if m and (c['entry'] - m[-1]['exit']) % tr.len < 35 and c['sign'] == m[-1]['sign']:
            m[-1]['exit'] = c['exit']; m[-1]['apex'] = c['apex'] if c['kmax'] > m[-1]['kmax'] else m[-1]['apex']; m[-1]['kmax'] = max(c['kmax'], m[-1]['kmax'])
        else: m.append(c)
    return m
def outside(tr, apex_m, sign):
    k = int(np.argmin(np.abs(tr.L - apex_m)))   # outside of the turn = away from the curvature centre
    p = tr.P[k]; t = tr.P[(k + 3) % tr.n] - tr.P[k - 3]; nrm = tr.N[k]; cross = t[0] * nrm[2] - t[2] * nrm[0]
    left = np.sign(cross)   # +1 if N points left of travel in xz (AC: x right, z forward... sign handled numerically)
    return -int(np.sign(sign) * left) or 1
def wrap(x, L): return x % L
def set1(tr):
    cs = corners(tr); L = tr.len; win = []
    # cut points: each corner window starts 25 m before entry; straights in between get mid + braking-zone windows
    cuts = []
    for i, c in enumerate(cs):
        nxt = cs[(i + 1) % len(cs)]; s0 = c['entry'] - 25; e0 = c['exit'] + 30
        gap = (nxt['entry'] - 25 - e0) % L
        if gap > L / 2: gap = gap - L          # next corner starts before this one's exit window ends
        cuts.append((s0, e0, 0.6 * c['apex'] + 0.4 * c['exit'] if c['exit'] >= c['apex'] else c['apex'], outside(tr, c['apex'], c['sign']), 'corner'))
        if gap > 60:
            nb = max(2, int(np.ceil(gap / 170)))
            edges = [e0 + gap * q / nb for q in range(nb + 1)]
            for q in range(nb):
                tag = 'braking' if q == nb - 1 else 'straight'
                anc = edges[q + 1] - 15 if tag == 'braking' else (edges[q] + edges[q + 1]) / 2
                cuts.append((edges[q], edges[q + 1], anc, outside(tr, nxt['apex'], nxt['sign']), tag))
        else:
            cuts[-1] = (s0, e0 + gap, cuts[-1][2], cuts[-1][3], 'corner')
    # make windows contiguous, normalized to the lap starting at 0
    W = []
    for i, (a, b, anc, sd, tag) in enumerate(cuts):
        b = cuts[(i + 1) % len(cuts)][0]
        a = wrap(a, L); b = wrap(b, L); b = b if b > a else b + L
        W.append((a, b, wrap(anc, L) if wrap(anc, L) >= a else wrap(anc, L) + L, sd, tag))
    spec = dict(off=[10, 13, 16, 19, 8, 22], h=[3, 4.5, 2, 6], shift=[0, 10, -10, 20, -20, 35, -35])
    return place(tr, W, spec, maxd=110)
def set2(tr, n=11):
    L = tr.len; W = [(L * i / n, L * (i + 1) / n, L * (i + 0.5) / n, 1, 'high') for i in range(n)]
    spec = dict(off=[30, 40, 25, 50, 60], h=[20, 25, 15, 30], shift=[0, 25, -25, 50, -50])
    return place(tr, W, spec, maxd=260, minlen=60)
def set3(tr):
    cs = corners(tr); L = tr.len; W = []
    edges = sorted({wrap(c['entry'] - 15, L) for c in cs})
    for i, a in enumerate(edges):
        b = edges[(i + 1) % len(edges)]; b = b if b > a else b + L
        c = [c for c in cs if wrap(c['entry'] - 15, L) == a][0]
        W.append((a, b, a + 15 + ((c['apex'] - c['entry']) % L), outside(tr, c['apex'], c['sign']), 'kerb'))
    if W[0][0] > 0:   # rotate so windows cover 0..1 (first window wraps)
        pass
    spec = dict(off=[6, 7.5, 9, 5], h=[1.0, 1.4, 0.8], shift=[0, 6, -6, 12, -12])
    return place(tr, W, spec, maxd=90, minlen=25)
def normalize(cams, L):
    """sort by window start (wrapped), split any window that crosses 0 so coverage is exactly 0..1."""
    out = []
    for c in cams:
        a, b = c['a'] % L, c['a'] % L + (c['b'] - c['a'])
        if b > L + 1e-6: out += [dict(c, a=a, b=L), dict(c, a=0.0, b=b - L)]
        else: out.append(dict(c, a=a, b=b))
    out.sort(key=lambda c: c['a']); return out
def write(path, name, cams, tr):
    L = tr.len; s = [f'[HEADER]\nVERSION=3\nCAMERA_COUNT={len(cams)}\nSET_NAME={name}\n']
    for i, c in enumerate(cams):
        W = tr.idx(c['a'], c['b']); tgt = tr.P[W].mean(0) + [0, CAR_H, 0]; f = tgt - c['pos']; f /= np.linalg.norm(f)
        right = np.cross(f, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, f); up = up if up[1] > 0 else -up
        mn, mx = fov_for(c['dmin'], c['dmax']); ia, oa = c['a'] / L, c['b'] / L
        v = lambda a: ' ,'.join(f'{x:.4f}' for x in a)
        s.append(f'''[CAMERA_{i}]
NAME={c['tag']}_{i}
POSITION={v(c['pos'])}
FORWARD={v(f)}
UP={v(up)}
MIN_FOV={mn}
MAX_FOV={mx}
IN_POINT={ia:.6f}
OUT_POINT={oa:.6f}
SHADOW_SPLIT0=50
SHADOW_SPLIT1=200
SHADOW_SPLIT2=600
NEAR_PLANE=0.3
FAR_PLANE=5000
MIN_EXPOSURE=0.35
MAX_EXPOSURE=0.55
DOF_FACTOR=10
DOF_RANGE=10000
DOF_FOCUS=0
DOF_MANUAL=0
SPLINE=
SPLINE_ROTATION=0
FOV_GAMMA=1
SPLINE_ANIMATION_LENGTH=15
IS_FIXED=0
''')
    open(path, 'w', newline='\r\n').write('\n'.join(s))
def main(lays):
    for lay in lays:
        tr = Track(lay); d = f'{Z}{lay}/data/'; bk = f'{ROOT}/assets_src/cameras_zwiss_orig/{lay}/'
        if not os.path.exists(bk):
            os.makedirs(bk)
            for f in os.listdir(d):
                if f.startswith('cameras'): shutil.copy(d + f, bk + f)
        for f in os.listdir(d):
            if f.startswith('cameras') and f.endswith('.ini'): os.remove(d + f)
        meta = {}
        for fn, name, fnc in (('cameras.ini', 'TV Trackside', set1), ('cameras_1.ini', 'TV High', set2), ('cameras_2.ini', 'TV Kerbside', set3)):
            cams = normalize(fnc(tr), tr.len); write(d + fn, name, cams, tr)
            meta[fn] = [dict(tag=c['tag'], pos=c['pos'].round(2).tolist(), a=c['a'], b=c['b'], los=c['los'], dmax=c['dmax'], h=c['h'], off=c['off']) for c in cams]
            print(lay, fn, len(cams), 'cams, min LOS %.3f, max dist %.0f m' % (min(c['los'] for c in cams), max(c['dmax'] for c in cams)))
        json.dump(meta, open(f'/workspace/vr12/cams_{lay}.json', 'w'))
if __name__ == '__main__': main(sys.argv[1:] or ['main', 'short'])
