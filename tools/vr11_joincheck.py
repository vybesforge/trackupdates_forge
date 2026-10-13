"""VR11: step check at every join between different collision meshes on the north extension.
Top-down raster (0.25 m) of all physics meshes of both layouts over the extension; at every cell where the top mesh
changes between neighbours, the step is the second difference |h[i-1] - 2 h[i] + h[i+1]| style: the jump between the two
sides after removing the local grade (each side's slope estimated from its own next cell). Reports per mesh pair the
max step and its location (candidates re-sampled at 2 cm, see run()); FAIL if any step > LIMIT between pavement/pavement or pavement/grass(ramp).
Usage: python tools/vr11_joincheck.py [tag] [x0 x1 z0 z1]"""
import os, re, sys, json, collections, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import physraster as PR
LIMIT = 0.010
def files(Z):
    fs = []
    for ini in ('models_main.ini', 'models_short.ini'):
        for l in open(Z + ini):
            m = re.match(r'\s*FILE\s*=\s*(\S+)', l)
            if m and m.group(1) not in fs: fs.append(m.group(1))
    return fs
def run(box, res=0.25, Z=PR.Z):
    PR.Z = Z; M = [m for m in PR.physmeshes(files(Z), box) if not m[1].startswith('1WALL')]
    xs, zs, H, KEY, UP, names = PR.raster(M, box, res)
    st = collections.defaultdict(lambda: [0.0, None, 0, []])
    for ax in (0, 1):
        h = np.moveaxis(H, ax, 0); k = np.moveaxis(KEY, ax, 0)
        a2, a1, b1, b2 = h[:-3], h[1:-2], h[2:-1], h[3:]
        ka, kb = k[1:-2], k[2:-1]
        sa = a1 - a2; sb = b2 - b1                       # slopes on each side
        step = np.abs((b1 - a1) - 0.5 * (sa + sb))
        ok = (ka != kb) & (ka >= 0) & (kb >= 0) & np.isfinite(step) & (k[:-3] == ka) & (k[3:] == kb)
        for j, i in zip(*np.nonzero(ok)):
            p = tuple(sorted((names[ka[j, i]], names[kb[j, i]]))); s = st[p]; s[2] += 1
            jj_, ii_ = (j + 1, i) if ax == 0 else (i, j + 1)
            if step[j, i] > LIMIT: s[3].append((float(step[j, i]), float(xs[ii_]), float(zs[jj_])))
            if step[j, i] > s[0]:
                jj, ii = (j + 1, i) if ax == 0 else (i, j + 1)
                s[0] = float(step[j, i]); s[1] = (round(float(xs[ii]), 2), round(float(zs[jj]), 2))
    # refine: a 0.25 m stencil also flags kinks (grade changes) as 'steps'. Re-sample the worst 25 candidates per
    # pair at 2 cm in a 0.6 m window and take the largest jump between neighbouring 2 cm cells minus the local grade.
    for p, s in st.items():
        s[3].sort(reverse=True); best = 0.0; where = s[1]
        for _, x, z in s[3][:25]:
            b = (x - 0.3, x + 0.3, z - 0.3, z + 0.3)
            MM = [m for m in M if m[1] in p]
            MM = [(f, n, T[(T[:, :, 0].max(1) > b[0]) & (T[:, :, 0].min(1) < b[1]) & (T[:, :, 2].max(1) > b[2]) & (T[:, :, 2].min(1) < b[3])]) for f, n, T in MM]
            _, _, h, k, _, _ = PR.raster([m for m in MM if len(m[2])], b, 0.02)
            for ax in (0, 1):
                hh = np.moveaxis(h, ax, 0); kk = np.moveaxis(k, ax, 0)
                a2, a1, b1, b2 = hh[:-3], hh[1:-2], hh[2:-1], hh[3:]
                stp = np.abs((b1 - a1) - 0.5 * ((a1 - a2) + (b2 - b1)))
                ok = (kk[1:-2] != kk[2:-1]) & np.isfinite(stp)
                if ok.any():
                    v = float(stp[ok].max())
                    if v > best: best = v; where = (round(x, 2), round(z, 2))
        if s[3]: s[0] = best; s[1] = where
    return st
if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'now'
    box = tuple(float(v) for v in sys.argv[2:6]) if len(sys.argv) > 5 else (-1000.0, 300.0, -3000.0, -2380.0)
    st = run(box); bad = {p: v for p, v in st.items() if v[0] > LIMIT}
    out = {'box': box, 'limit_m': LIMIT, 'pairs': len(st), 'fail_pairs': len(bad),
           'worst': sorted([(p[0], p[1], round(v[0], 4), v[1], v[2]) for p, v in st.items()], key=lambda r: -r[2])}
    json.dump(out, open('/workspace/vr11/joincheck_%s.json' % tag, 'w'), indent=1)
    for r in out['worst'][:25]: print(r)
    print('pairs', len(st), 'pairs with step >', LIMIT, ':', len(bad))
