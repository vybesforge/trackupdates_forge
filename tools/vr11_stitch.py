"""VR11: final stitch of every collision join on the north extension (after tools/vr11_flush.py).
vr11_joincheck still found 1-58 cm steps where a big triangle of the lower mesh spans the join (the flush pass can only
move existing vertices).  This pass is raster-driven and iterative:
  1. raster all physics meshes of both layouts (0.25 m); at every cell where the top mesh changes, measure the step
     exactly like vr11_joincheck (jump minus local grade);
  2. the LOWER-priority side (pavement of zwiss > 1XROAD (bigger first) > 1XLOT > 1GRAVEL_EXT shoulders > gravel lots >
     grass ramps > zwiss terrain > extension terrain) gets the correction at that cell;
  3. that mesh is refined around the join (conforming red-green edge split down to 0.5 m within 3 m of the join, UVs and
     normals interpolated, no T-junctions) and its vertices are moved by a smooth field: full correction at the join,
     fading out with a smoothstep over max(1.5 m, |step| / 6 %) so no new ramp is steeper than ~6 %;
  4. repeat until no step > 1 cm (max 6 rounds).  Visual = physics (same meshes), vertex order/UVs kept.
Usage: python tools/vr11_stitch.py   (in place; backup first)"""
import os, re, sys, struct, json, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K, physraster as PR, vr11_joincheck as J
from vr9_split_phys import parse_tree
MODE = os.environ.get('STITCH_MODE', 'pave')   # 'pave': pavement/pavement joins only; 'all': also grass
Z = PR.Z; BOX = (-1000.0, 300.0, -3000.0, -2380.0); RES = 0.25; LIM = 0.008
def prio(n, ntri):
    if re.match(r'^1(ROAD|PITS|CONCRETE|DRAG|CURB|LAUNCH)', n): return 1000
    if n.startswith('1XROAD'): return 800 + min(ntri, 99999) / 1e3
    if n.startswith('1XLOT'): return 700
    if n.startswith('1GRAVEL_EXT_r'): return 600
    if n.startswith('1GRAVEL'): return 550
    if n.startswith('1GRASS_RAMP'): return 300
    if n.startswith('1GRASS_EXT'): return 100
    if n.startswith('1GRASS'): return 200
    return 400
def load_all():
    out = {}
    for fn in J.files(Z):
        d = open(Z + fn, 'rb').read()
        for name, o, l, c in K.scan(Z + fn)[1]:
            if c != 2 or not re.match(r'^\d+[A-Z]', name) or name.startswith('1WALL'): continue
            q = o + l + 8; nv, = struct.unpack_from('<I', d, q); V = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11).astype(np.float64)
            q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); I = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3).astype(int)
            x, zz = V[:, 0], V[:, 2]
            if x.max() < BOX[0] or x.min() > BOX[1] or zz.max() < BOX[2] or zz.min() > BOX[3]: continue
            out[name] = dict(fn=fn, name=name, V=V, I=I, dirty=False)
    return out
def refine(m, P, rad=1.5, maxlen=0.6, passes=3, cap=19500):
    tr = cKDTree(P)
    for _ in range(passes):
        V, I = m['V'], m['I']; E = np.sort(np.r_[I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]], 1); E = np.unique(E, axis=0)
        L = np.linalg.norm(V[E[:, 0], :3][:, [0, 2]] - V[E[:, 1], :3][:, [0, 2]], axis=1); mid = (V[E[:, 0], :3] + V[E[:, 1], :3]) / 2
        d, _ = tr.query(mid[:, [0, 2]]); S = E[(L > maxlen) & (d < rad + L / 2)]
        if not len(S): break
        if len(I) + 3 * len(S) > cap: S = S[np.argsort(-L[(L > maxlen) & (d < rad + L / 2)])][:max(0, (cap - len(I)) // 3)]
        if not len(S): break
        newV = (V[S[:, 0]] + V[S[:, 1]]) / 2; nn = newV[:, 3:6]; newV[:, 3:6] = nn / (np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12)
        key = {(a, b): len(V) + k for k, (a, b) in enumerate(S)}; V2 = np.r_[V, newV]
        def mp(a, b): return key.get((a, b) if a < b else (b, a))
        T = []
        for a, b, c in I:
            ab, bc, ca = mp(a, b), mp(b, c), mp(c, a); k = (ab is not None) + (bc is not None) + (ca is not None)
            if k == 0: T.append((a, b, c))
            elif k == 3: T += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
            elif k == 1:
                if ab is not None: T += [(a, ab, c), (ab, b, c)]
                elif bc is not None: T += [(a, b, bc), (a, bc, c)]
                else: T += [(a, b, ca), (ca, b, c)]
            else:
                if ab is None: T += [(ca, bc, c), (a, b, bc), (a, bc, ca)]       # bc, ca split
                elif bc is None: T += [(ab, b, c), (a, ab, ca), (ab, c, ca)]     # ab, ca split
                else: T += [(a, ab, bc), (ab, b, bc), (a, bc, c)]                # ab, bc split
        m['V'] = V2; m['I'] = np.array(T, int)
    m['capped'] = len(m['I']) >= cap - 3
def one_round(ms):
    M = [(m['fn'], n, m['V'][m['I']][:, :, :3]) for n, m in ms.items()]
    xs, zs, H, KEY, UP, names = PR.raster(M, BOX, RES); ntri = {n: len(ms[n]['I']) for n in names}
    corr = {}; worst = 0.0
    for ax in (0, 1):
        h = np.moveaxis(H, ax, 0); k = np.moveaxis(KEY, ax, 0)
        a2, a1, b1, b2 = h[:-3], h[1:-2], h[2:-1], h[3:]; ka, kb = k[1:-2], k[2:-1]
        s = (b1 - a1) - 0.5 * ((a1 - a2) + (b2 - b1))
        ok = (ka != kb) & (ka >= 0) & (kb >= 0) & np.isfinite(s) & (k[:-3] == ka) & (k[3:] == kb) & (np.abs(s) > LIM) & (np.abs(s) < 1.0)
        for j, i in zip(*np.nonzero(ok)):
            na, nb = names[ka[j, i]], names[kb[j, i]]; st = float(s[j, i]); worst = max(worst, abs(st))
            if prio(na, ntri[na]) <= prio(nb, ntri[nb]): low, c, jj = na, st, j + 1     # move a-side up by s
            else: low, c, jj = nb, -st, j + 2
            if prio(low, 0) >= 1000: continue
            if MODE == 'pave' and min(prio(na, 0), prio(nb, 0)) < 550: continue
            if ax == 0: x, z = xs[i], zs[jj]
            else: x, z = xs[jj], zs[i]
            corr.setdefault(low, []).append((x, z, c))
    return corr, worst
def apply(ms, corr):
    for n, L in corr.items():
        m = ms[n]; A = np.array(L); P = A[:, :2]; C = A[:, 2]
        refine(m, P)
        V = m['V']; R = np.maximum(1.5, np.abs(C) / 0.06); tr = cKDTree(P)
        nb = tr.query_ball_point(V[:, [0, 2]], r=float(R.max()))
        dy = np.zeros(len(V))
        for vi, ids in enumerate(nb):
            if not ids: continue
            ids = np.array(ids); d = np.linalg.norm(P[ids] - V[vi, [0, 2]], axis=1); t = np.clip(1 - d / R[ids], 0, 1)
            f = t * t * (3 - 2 * t); g = f / (d * d + 0.02)
            if g.sum() <= 0: continue
            dy[vi] = (g * C[ids]).sum() / g.sum() * f.max()
        V[:, 1] += dy; m['dirty'] = True
    clamp(ms, set(corr))
def clamp(ms, names):
    # no poke-through: where a higher-priority pavement covers a vertex, keep the vertex >= 3 mm below it
    from vr11_flush import TriIndex
    idx = TriIndex(4.0); pr = {}
    for n, m in ms.items():
        if prio(n, 0) >= 550: idx.add(m['V'][m['I']][:, :, :3], n); pr[n] = prio(n, len(m['I']))
    for n in names:
        if prio(n, 0) < 550: continue
        m = ms[n]; V = m['V']; me = pr[n]; used = np.unique(m['I'])
        for vi in used:
            x, y, z = V[vi, :3]; best = None
            for k in idx.g.get((int(np.floor(x / 4.0)), int(np.floor(z / 4.0))), ()):
                t, tag = idx.T[k]
                if pr[tag] <= me: continue
                a, b, c = t; v0 = (b[0] - a[0], b[2] - a[2]); v1 = (c[0] - a[0], c[2] - a[2]); den = v0[0] * v1[1] - v1[0] * v0[1]
                if abs(den) < 1e-9: continue
                px, pz = x - a[0], z - a[2]; u = (px * v1[1] - v1[0] * pz) / den; v = (v0[0] * pz - px * v0[1]) / den
                if u < 0.02 or v < 0.02 or u + v > 0.98: continue      # strictly inside (not on the shared edge)
                yy = a[1] + u * (b[1] - a[1]) + v * (c[1] - a[1]); best = yy if best is None else max(best, yy)
            if best is not None and y > best - 0.003: V[vi, 1] = best - 0.003
def save(ms):
    byfn = {}
    for m in ms.values():
        if m['dirty']: byfn.setdefault(m['fn'], []).append(m)
    for fn, L in byfn.items():
        d = open(Z + fn, 'rb').read(); info = {x['name']: x for x in parse_tree(d, Z + fn)}; edits = []
        for m in L:
            x = info[m['name']]; q = x['o'] + x['l'] + 8; nv, = struct.unpack_from('<I', d, q); q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2)
            t0 = q2 + 4 + ni * 2; mat, layer = struct.unpack_from('<II', d, t0); lod = d[t0 + 8:t0 + 16]; last = d[t0 + 32:x['next']]
            from vr9_fill_holes import split_mesh
            parts = split_mesh(m['V'], m['I']) if len(m['I']) > 19500 else [(m['V'], m['I'])]
            hdr = d[x['start']:q]; nm0 = m['name'].encode(); nbts = b''
            for pi_, (Vp, Ip) in enumerate(parts):
                if len(parts) > 1:   # sibling chunks: same header, name gets _sNN
                    nm = nm0 + b'_s%02d' % pi_; h2 = hdr[:4] + struct.pack('<I', len(nm)) + nm + hdr[8 + len(nm0):]
                else: h2 = hdr
                V = np.asarray(Vp).astype('<f4'); I = np.asarray(Ip).astype('<u2'); assert len(V) < 65536
                c = V[:, :3].mean(0); r = float(np.linalg.norm(V[:, :3] - c, axis=1).max())
                nbts += h2 + struct.pack('<I', len(V)) + V.tobytes() + struct.pack('<I', I.size) + I.tobytes() + struct.pack('<II', mat, layer) + lod + struct.pack('<4f', *c, r) + last
            edits.append((x['start'], x['next'], nbts))
            if len(parts) > 1:
                par = parse_tree(d, Z + fn)[x['parent']]; edits.append((par['o'] + par['l'], par['o'] + par['l'] + 4, ('ADD', len(parts) - 1)))
        add = {}
        for a, b, r in edits:
            if isinstance(r, tuple): add[a] = add.get(a, 0) + r[1]
        edits = [e for e in edits if not isinstance(e[2], tuple)] + [(a, a + 4, struct.pack('<I', struct.unpack_from('<I', d, a)[0] + n)) for a, n in add.items()]
        edits.sort(); out = bytearray(); pos = 0
        for a, b, r in edits: out += d[pos:a] + r; pos = b
        out += d[pos:]; open(Z + fn, 'wb').write(bytes(out)); K.scan(Z + fn); print('wrote', fn, [m['name'] for m in L])
def main():
    ms = load_all(); hist = []
    for it in range(6):
        corr, worst = one_round(ms); hist.append(dict(round=it, worst_step_m=round(worst, 4), meshes=len(corr), cells=sum(len(v) for v in corr.values())))
        print(hist[-1])
        if not corr: break
        apply(ms, corr)
    save(ms)
    json.dump(dict(history=hist, tris={n: len(m['I']) for n, m in ms.items() if m['dirty']}), open('/workspace/vr11/stitch_report.json', 'w'), indent=1)
if __name__ == '__main__': main()
