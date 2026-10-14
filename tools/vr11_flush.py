"""VR11: flush joins + edge ramps on the north extension (fixes the 'car jumps up onto the Love's / BP lots').
Diagnosis (VR11, raster of every physics mesh): the station lots were never stitched to the roads. 1XLOT_bp_1 sat
3.8-9.6 cm above 1XROAD_r309854951 where they overlap and 5-22 cm above its gravel shoulder, 1GRAVEL_EXT_lot4 up to
0.9 m off 1XROAD_r15976346, two extension roads met with a 27 cm step, and every lot/shoulder edge stood 15-25 cm
above the grass (the grass was dropped 0.2 m under all pavement, so each pavement edge was a vertical 20 cm 'curb' in
physics with nothing visible). Identical in pre-VR10, so not a re-drape regression; VR10 only moved it up/down.
Fix (visual = physics, both are the same meshes):
 1. priority stitching: vf_i29_speedway pavement (fixed) > 1XROAD (largest first) > 1GRAVEL_EXT_r* shoulders > lots.
    Each lower mesh gets a smooth offset field (Shepard over contact points, Gaussian decay 25 m) so that where it
    overlaps a higher mesh it sits 3 mm below it, and where it only touches, its edge meets the higher edge's plane.
 2. grass vertices that poke up through pavement are pushed 10 cm under it.
 3. ramps: on every pavement boundary edge that faces grass (not another pavement) with a step > 8 mm a grass skirt
    (1GRASS_RAMP_nn, visible + physics, grass material/UVs) starts exactly on the pavement edge vertices and runs out
    (<= 8 % grade, 1-6 m) until it dives 2 cm under the grass. No coplanar overlap, no step.
Usage: python tools/vr11_flush.py   (operates on vf_i29_speedway/vf_ext.kn5 in place; restore from backup/pre_vr11 to rerun)"""
import os, re, sys, struct, json, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K
from vr9_split_phys import parse_tree
from vr9_fill_holes import mesh_bytes, split_mesh
Z = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vf_i29_speedway')) + '/'
EXT = Z + 'vf_ext.kn5'
PAVE = re.compile(r'^1(ROAD|XROAD|XLOT|GRAVEL|PITS|CONCRETE|DRAG|CURB|LAUNCH)')
def files():
    fs = []
    for ini in ('models_main.ini', 'models_short.ini'):
        for l in open(Z + ini):
            m = re.match(r'\s*FILE\s*=\s*(\S+)', l)
            if m and m.group(1) not in fs: fs.append(m.group(1))
    return fs
def load(fn):
    d = open(Z + fn, 'rb').read(); out = []
    for name, o, l, c in K.scan(Z + fn)[1]:
        if c != 2 or not re.match(r'^\d+[A-Z]', name): continue
        q = o + l + 8; nv, = struct.unpack_from('<I', d, q); V = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11).copy()
        q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); I = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3).astype(int)
        I = I[(I[:, 0] != I[:, 1]) & (I[:, 1] != I[:, 2]) & (I[:, 0] != I[:, 2])]
        mat, = struct.unpack_from('<I', d, q2 + 4 + ni * 2)
        out.append(dict(fn=fn, name=name, V=V, I=I, voff=q + 4, mat=mat))
    return out
class TriIndex:
    def __init__(self, cell=4.0): self.c = cell; self.g = {}; self.T = []
    def add(self, T, tag):
        base = len(self.T); self.T.extend([(t, tag) for t in T])
        mn = np.floor(T[:, :, [0, 2]].min(1) / self.c).astype(int); mx = np.floor(T[:, :, [0, 2]].max(1) / self.c).astype(int)
        for k in range(len(T)):
            for i in range(mn[k, 0], mx[k, 0] + 1):
                for j in range(mn[k, 1], mx[k, 1] + 1): self.g.setdefault((i, j), []).append(base + k)
    def query(self, x, z, skip=None, plane_tol=0.0):
        """top height of indexed triangles at (x,z) (point inside, or within plane_tol of the triangle in xz -> plane value)."""
        best = None
        for k in self.g.get((int(np.floor(x / self.c)), int(np.floor(z / self.c))), ()):
            t, tag = self.T[k]
            if skip is not None and tag == skip: continue
            a, b, c = t; v0 = (b[0] - a[0], b[2] - a[2]); v1 = (c[0] - a[0], c[2] - a[2]); den = v0[0] * v1[1] - v1[0] * v0[1]
            if abs(den) < 1e-9: continue
            px, pz = x - a[0], z - a[2]; u = (px * v1[1] - v1[0] * pz) / den; v = (v0[0] * pz - px * v0[1]) / den
            if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6:
                if plane_tol <= 0: continue
                # distance from the triangle in xz (approx via clamped barycentrics)
                uu, vv = max(u, 0), max(v, 0); s = uu + vv
                if s > 1: uu, vv = uu / s, vv / s
                qx = a[0] + uu * v0[0] + vv * v1[0]; qz = a[2] + uu * v0[1] + vv * v1[1]
                if (qx - x) ** 2 + (qz - z) ** 2 > plane_tol ** 2: continue
            y = a[1] + u * (b[1] - a[1]) + v * (c[1] - a[1])
            if best is None or y > best[0]: best = (y, tag)
        return best
def shepard(P, O, X, lam=25.0, k=48):
    """smooth offset field: Gaussian-kernel regression of the contact offsets (sigma 2 m, then a 0.75 m pass on the
    residual so contacts end up within mm), times a Gaussian decay with the distance to the nearest contact."""
    if len(P) == 0: return np.zeros(len(X))
    tr = cKDTree(P); kk = min(k, len(P))
    def kr(vals, Q, sig):
        d, ix = tr.query(Q, k=kk); d = d.reshape(len(Q), -1); ix = ix.reshape(len(Q), -1)
        w = np.exp(-(d / sig) ** 2) + 1e-12; return (w * vals[ix]).sum(1) / w.sum(1), d[:, 0]
    o1, _ = kr(O, P, 2.0); r = O - o1
    a, d0 = kr(O, X, 2.0); b, _ = kr(r, X, 0.75)
    return (a + b) * np.exp(-(d0 / lam) ** 2)
def main():
    fs = files(); allm = []
    for fn in fs: allm += load(fn)
    ext = [m for m in allm if m['fn'] == 'vf_ext.kn5']
    lo, hi = np.min([m['V'][:, [0, 2]].min(0) for m in ext], 0) - 50, np.max([m['V'][:, [0, 2]].max(0) for m in ext], 0) + 50
    near = lambda m: (m['V'][:, 0].max() > lo[0]) & (m['V'][:, 0].min() < hi[0]) & (m['V'][:, 2].max() > lo[1]) & (m['V'][:, 2].min() < hi[1])
    btree = {}
    def bdist(name, x, z):
        if name not in btree:
            mm = next(q for q in allm if q['name'] == name); I = mm['I']
            e = np.sort(np.r_[I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]], 1); key = e[:, 0] * 1000003 + e[:, 1]
            u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True); B = np.unique(e[cnt[inv] == 1])
            btree[name] = cKDTree(mm['V'][B][:, [0, 2]])
        return btree[name].query((x, z))[0]
    fixed = TriIndex(); rep = {}
    for m in allm:
        if m['fn'] != 'vf_ext.kn5' and PAVE.match(m['name']) and near(m): fixed.add(m['V'][m['I']][:, :, :3].astype(float), m['name'])
    def pr(m):
        n = m['name']
        if n.startswith('1XROAD'): return (0, -len(m['I']))
        if re.match(r'1GRAVEL_EXT_r', n): return (1, -len(m['I']))
        if n.startswith(('1XLOT', '1GRAVEL_EXT_lot')): return (2, -len(m['I']))
        return None
    order = sorted([m for m in ext if pr(m)], key=pr)
    # 0. de-bevel: zwiss-style slab edges drop 15-20 cm over ~0.5 m (a hidden 30-40 % 'curb' in physics).
    #    Raise boundary vertices onto the local plane of the interior vertices next to them.
    nb = 0
    for m in order:
        V = m['V']; I = m['I']; e = np.sort(np.r_[I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]], 1)
        key = e[:, 0] * 1000003 + e[:, 1]; u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
        B = np.unique(e[cnt[inv] == 1]); used = np.unique(I)
        if len(B) == 0: continue
        db, _ = cKDTree(V[B][:, [0, 2]]).query(V[used][:, [0, 2]])
        rim = used[db < 0.6]; inner = used[(db > 0.8) & (db < 3.0)]
        if len(inner) < 3: continue
        tr = cKDTree(V[inner][:, [0, 2]]); d, ix = tr.query(V[rim][:, [0, 2]], k=min(16, len(inner)))
        for bi, dd, ii in zip(rim, d, ix):
            ok = dd < 3.5
            if ok.sum() < 3: continue
            Q = V[inner[ii[ok]]][:, :3].astype(float); A = np.c_[Q[:, 0], Q[:, 2], np.ones(len(Q))]
            if np.linalg.matrix_rank(A) < 3: continue
            c = np.linalg.lstsq(A, Q[:, 1], rcond=None)[0]; y = c[0] * V[bi, 0] + c[1] * V[bi, 2] + c[2]
            if 0.01 < y - V[bi, 1] < 0.45: V[bi, 1] = y; nb += 1; m['moved'] = True
    rep['debevelled_vertices'] = nb
    # 0b. lots: replace the noisy, bevelled re-draped heights by a smoothing bicubic spline of their interior
    #     (rim < 0.8 m from the boundary excluded) - lots become smooth, graded pads with no edge bevel.
    from scipy.interpolate import SmoothBivariateSpline
    groups = {}
    for m in order:
        if m['name'].startswith(('1XLOT', '1GRAVEL_EXT_lot')): groups.setdefault(re.sub(r'_\d\d$', '', m['name']), []).append(m)
    for gname, ms in groups.items():                  # split siblings (lot4_00/_01) are fitted as one surface
        X = []; Y = []; Zs = []
        for m in ms:
            V = m['V']; I = m['I']; used = np.unique(I)
            e = np.sort(np.r_[I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]], 1); key = e[:, 0] * 1000003 + e[:, 1]
            u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True); B = np.unique(e[cnt[inv] == 1])
            if len(ms) > 1:   # seam vertices shared with a sibling are not a real boundary
                other = np.concatenate([q['V'][:, [0, 2]] for q in ms if q is not m]); ds, _ = cKDTree(other).query(V[B][:, [0, 2]]); B = B[ds > 0.05]
            db, _ = cKDTree(V[B][:, [0, 2]]).query(V[used][:, [0, 2]]) if len(B) else (np.full(len(used), 9.0), None)
            inn = used[db > 0.8]; X.append(V[inn, 0]); Zs.append(V[inn, 2]); Y.append(V[inn, 1])
        x, z, y = (np.concatenate(v).astype(float) for v in (X, Zs, Y))
        allV = np.concatenate([m['V'] for m in ms]); k = 3 if len(x) > 40 else 1
        sp_ = SmoothBivariateSpline(x, z, y, kx=k, ky=k, s=len(x) * 0.015 ** 2, bbox=[allV[:, 0].min() - 1, allV[:, 0].max() + 1, allV[:, 2].min() - 1, allV[:, 2].max() + 1])
        rep['spline_' + gname] = dict(rms_change=round(float(np.sqrt(np.mean((sp_.ev(x, z) - y) ** 2))), 4))
        for m in ms:
            m['V'][:, 1] = sp_.ev(m['V'][:, 0].astype(float), m['V'][:, 2].astype(float)).astype(np.float32); m['moved'] = True
    for m in order:
        V = m['V']; P3 = V[:, :3].astype(float); own = TriIndex(); own.add(P3[m['I']], m['name'])
        cp, co = [], []
        for x, y, z in P3:
            r = fixed.query(x, z)
            if r: cp.append((x, z)); co.append(r[0] - 0.003 - y); continue
            r = fixed.query(x, z, plane_tol=0.35)
            if r: cp.append((x, z)); co.append(r[0] - y)
        # fixed triangle vertices inside this mesh: own surface must be below them
        for k in set(i for key in own.g for i in fixed.g.get(key, ())):
            for p in fixed.T[k][0]:
                r = own.query(p[0], p[2])
                if r and r[0] > p[1] - 0.003: cp.append((p[0], p[2])); co.append(p[1] - 0.003 - r[0])
        cp = np.array(cp).reshape(-1, 2); co = np.array(co)
        if len(cp):
            off = shepard(cp, co, P3[:, [0, 2]]); V[:, 1] += off.astype(np.float32); m['moved'] = True
            for i in range(len(V)):                       # exact clamp: never above a higher-priority surface
                r = fixed.query(float(V[i, 0]), float(V[i, 2]))
                if r:   # under a higher surface: flush (3 mm) near its edge, 3 cm deeper inside (no z-fighting)
                    lim = r[0] - (0.03 if bdist(r[1], float(V[i, 0]), float(V[i, 2])) > 0.6 else 0.003)
                    if V[i, 1] > lim: V[i, 1] = lim
            rep[m['name']] = dict(contacts=len(cp), contact_off_max=round(float(np.abs(co).max()), 3), vert_off_max=round(float(np.abs(off).max()), 3))
        fixed.add(V[m['I']][:, :, :3].astype(float), m['name'])
    # 2. grass under pavement
    pav = TriIndex()
    for m in allm:
        if PAVE.match(m['name']) and near(m): pav.add(m['V'][m['I']][:, :, :3].astype(float), m['name'])
    grass = [m for m in allm if m['name'].startswith('1GRASS') and near(m)]
    gl = 0
    for m in grass:
        V = m['V']
        for i, (x, y, z) in enumerate(V[:, :3].astype(float)):
            r = pav.query(x, z)
            if not r: continue
            lim = r[0] - (0.10 if bdist(r[1], x, z) > 1.5 else 0.025)
            if y > lim: V[i, 1] = lim; gl += 1; m['moved'] = True
    rep['grass_lowered_vertices'] = gl
    gi = TriIndex()
    for m in grass: gi.add(m['V'][m['I']][:, :, :3].astype(float), m['name'])
    # 3. skirts on pavement boundary edges facing grass
    skirts = []; nsk = 0
    for m in order:
        V = m['V']; I = m['I']; P3 = V[:, :3].astype(float)
        e = np.sort(np.r_[I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]], 1); opp = np.r_[I[:, 2], I[:, 0], I[:, 1]]
        key = e[:, 0] * 1000003 + e[:, 1]; u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
        be = np.where(cnt[inv] == 1)[0]
        vn = {}; edges = []
        for k in be:
            a, b = e[k]; pa, pb = P3[a, [0, 2]], P3[b, [0, 2]]; t = pb - pa; L = np.linalg.norm(t)
            if L < 1e-4: continue
            n = np.array([t[1], -t[0]]) / L; c = P3[opp[k], [0, 2]]
            if np.dot(c - pa, n) > 0: n = -n
            mid = (pa + pb) / 2 + n * 0.3
            if pav.query(mid[0], mid[1]): continue                      # faces another pavement: a join, flushed above
            g = gi.query(mid[0], mid[1])
            if g is None: continue
            he = (P3[a, 1] + P3[b, 1]) / 2
            if abs(he - g[0]) < 0.008: continue
            edges.append((a, b)); vn.setdefault(a, []).append(n); vn.setdefault(b, []).append(n)
        if not edges: continue
        VV = []; II = []; vid = {}
        S = (0.0, 0.25, 0.5, 0.75, 1.0)
        def ring(a):
            if a in vid: return vid[a]
            n = np.mean(vn[a], 0); n /= np.linalg.norm(n) + 1e-9
            p = P3[a]; g1 = gi.query(p[0] + n[0], p[2] + n[1])
            g1 = g1[0] if g1 else p[1] - 0.2
            W = float(np.clip(abs(p[1] - g1) / 0.08, 1.0, 6.0)); ids = []; end = len(vn[a]) == 1   # run end: taper under the grass
            hit = None                                   # another pavement within 4 m: bridge the gap instead
            for t in np.arange(0.5, 4.01, 0.25):
                r = pav.query(p[0] + n[0] * t, p[2] + n[1] * t)
                if r: hit = (t, r[0]); break
            if hit and not end:
                th, hh = hit; Wb = th + 0.3
                for s in S:
                    t = Wb * s; x, z = p[0] + n[0] * t, p[2] + n[1] * t
                    y = p[1] + (hh - p[1]) * min(t / th, 1.0) - (0.03 if t > th else 0.0)
                    ids.append(len(VV)); VV.append([x, y, z, 0, 1, 0, 0, 0, 1, 0, 0])
                vid[a] = ids; return ids
            for s in S:
                x, z = p[0] + n[0] * W * s, p[2] + n[1] * W * s
                if s == 0: y = p[1]
                else:
                    g = gi.query(x, z); g = g[0] if g else g1
                    ss = 1.0 if end else s * s * (3 - 2 * s); y = p[1] + (g - 0.06 - p[1]) * ss
                ids.append(len(VV)); VV.append([x, y, z, 0, 1, 0, 0, 0, 1, 0, 0])
            vid[a] = ids; return ids
        for a, b in edges:
            ra, rb = ring(a), ring(b)
            for s in range(len(S) - 1): II += [(ra[s], rb[s], rb[s + 1]), (ra[s], rb[s + 1], ra[s + 1])]
        VV = np.array(VV, np.float32); II = np.array(II)
        T = VV[II, :3]; nn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); flip = nn[:, 1] < 0; II[flip] = II[flip][:, [0, 2, 1]]
        skirts.append((VV, II)); nsk += len(edges)
    rep['skirt_edges'] = nsk
    # write: in-place y for moved meshes, then splice skirts after the last 1GRASS_EXT mesh
    d = bytearray(open(EXT, 'rb').read())
    for m in ext:
        if m.get('moved'):
            d[m['voff']:m['voff'] + len(m['V']) * 44] = m['V'].astype('<f4').tobytes()
    d = bytes(d); info = parse_tree(d, EXT)
    for fn in sorted({m['fn'] for m in allm if m.get('moved') and m['fn'] != 'vf_ext.kn5'}):
        dd = bytearray(open(Z + fn, 'rb').read())
        for m in allm:
            if m['fn'] == fn and m.get('moved'): dd[m['voff']:m['voff'] + len(m['V']) * 44] = m['V'].astype('<f4').tobytes()
        open(Z + fn, 'wb').write(bytes(dd)); K.scan(Z + fn); rep.setdefault('also_patched', []).append(fn)
    assert not any(x['name'].startswith('1GRASS_RAMP') for x in info), 'already applied'
    g0 = next(m for m in ext if m['name'].startswith('1GRASS_EXT'))
    A = np.c_[g0['V'][:, 0], g0['V'][:, 2], np.ones(len(g0['V']))]
    ua = np.linalg.lstsq(A, g0['V'][:, 6], rcond=None)[0]; va = np.linalg.lstsq(A, g0['V'][:, 7], rcond=None)[0]
    from vr5_meshlib import merge
    VV, II = merge(skirts); B = np.c_[VV[:, 0], VV[:, 2], np.ones(len(VV))]; VV[:, 6] = B @ ua; VV[:, 7] = B @ va
    anchor = [x for x in info if x['name'].startswith('1GRASS_EXT')][-1]
    blob = b''; cnt = 0
    for q, (Vs, Is) in enumerate(split_mesh(VV, II)):
        blob += mesh_bytes('1GRASS_RAMP_%02d' % q, Vs, Is, g0['mat'], True, None); cnt += 1
    d2 = bytearray(d); par = info[anchor['parent']]
    c0, = struct.unpack_from('<I', d2, par['o'] + par['l']); struct.pack_into('<I', d2, par['o'] + par['l'], c0 + cnt)
    open(EXT, 'wb').write(bytes(d2[:anchor['next']]) + blob + bytes(d2[anchor['next']:])); K.scan(EXT)
    rep['ramp_meshes'] = cnt; rep['ramp_tris'] = int(len(II))
    json.dump(rep, open('/workspace/vr11/flush_report.json', 'w'), indent=1); print(json.dumps(rep, indent=1))
if __name__ == '__main__': main()
