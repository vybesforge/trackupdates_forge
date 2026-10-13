"""VR12: 0.5 m top-height rasters for camera placement. ground = physics meshes (digit-prefixed names),
top = every mesh of the layout (buildings, fences, trees, props; world transforms applied).
Triangles are point-sampled (<=0.35 m spacing) so walls/poles/tree cards register. Cached in /workspace/vr12/camr_<layout>.npz."""
import os, sys, re, struct, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vr7_common as C
Z = C.Z; BOX = (-330.0, 370.0, -1010.0, 330.0); RES = 0.5
SKIP = re.compile(r'horizon|treeline|sky|AC_|shadow', re.I)
def rd(d, o, f): return struct.unpack_from('<' + f, d, o), o + struct.calcsize(f)
def meshes(p):
    d = open(p, 'rb').read(); o = 6; (ver,), o = rd(d, o, 'I')
    if ver > 5: o += 4
    (nt,), o = rd(d, o, 'I')
    for _ in range(nt): o += 4; (n,), o = rd(d, o, 'I'); o += n; (sz,), o = rd(d, o, 'I'); o += sz
    (nm,), o = rd(d, o, 'I')
    def rs(o): (n,), o = rd(d, o, 'I'); return d[o:o + n].decode('utf8', 'replace'), o + n
    for _ in range(nm):
        _, o = rs(o); _, o = rs(o); o += 2
        if ver > 4: o += 4
        (k,), o = rd(d, o, 'I')
        for _ in range(k): _, o = rs(o); o += 40
        (k,), o = rd(d, o, 'I')
        for _ in range(k): _, o = rs(o); o += 4; _, o = rs(o)
    out = []
    def node(o, W):
        (cls,), o = rd(d, o, 'I'); name, o = rs(o); (nc,), o = rd(d, o, 'I'); o += 1; M = W
        if cls == 1: M = np.frombuffer(d, '<f4', 16, o).reshape(4, 4).astype(float) @ W; o += 64
        elif cls in (2, 3):
            o += 3; (nv,), o = rd(d, o, 'I'); st = 11 if cls == 2 else 19
            V = np.frombuffer(d, '<f4', nv * st, o).reshape(nv, st)[:, :3].astype(float); o += nv * st * 4
            (ni,), o = rd(d, o, 'I'); I = np.frombuffer(d, '<u2', ni, o).reshape(-1, 3).astype(int); o += ni * 2 + 8
            if cls == 3:
                (nb,), o = rd(d, o, 'I')
                for _ in range(nb): _, o = rs(o); o += 64
            else: o += 25
            if cls == 2 and not SKIP.search(name):
                Vw = np.c_[V, np.ones(len(V))] @ W; out.append((name, Vw[:, :3][I]))
        for _ in range(nc): o = node(o, M)
        return o
    node(o, np.eye(4)); return out
def splat(H, T):
    if not len(T): return
    e = np.max(np.linalg.norm(T - np.roll(T, 1, 1), axis=2), 1); n = np.clip(np.ceil(e / 0.35).astype(int), 1, 400)
    for k in np.unique(n):
        S = T[n == k]; a, b = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = a + b <= k
        u = a[m] / k; v = b[m] / k; P = S[:, None, 0] + u[None, :, None] * (S[:, None, 1] - S[:, None, 0]) + v[None, :, None] * (S[:, None, 2] - S[:, None, 0])
        P = P.reshape(-1, 3); i = ((P[:, 0] - BOX[0]) / RES).astype(int); j = ((P[:, 2] - BOX[2]) / RES).astype(int)
        ok = (i >= 0) & (i < H.shape[1]) & (j >= 0) & (j < H.shape[0]); np.fmax.at(H, (j[ok], i[ok]), P[ok, 1])
def build(lay):
    c = f'/workspace/vr12/camr_{lay}.npz'
    if os.path.exists(c): r = np.load(c); return r['G'], r['T']
    sh = (int((BOX[3] - BOX[2]) / RES), int((BOX[1] - BOX[0]) / RES)); G = np.full(sh, np.nan); T = np.full(sh, np.nan)
    for fn in C.FILES[lay]:
        for name, tri in meshes(Z + fn):
            k = (tri[:, :, 0].max(1) > BOX[0]) & (tri[:, :, 0].min(1) < BOX[1]) & (tri[:, :, 2].max(1) > BOX[2]) & (tri[:, :, 2].min(1) < BOX[3])
            if not k.any(): continue
            if re.match(r'^\d+[A-Z]', name): splat(G, tri[k])
            else: splat(T, tri[k])
    np.savez(c, G=G, T=T); return G, T
if __name__ == '__main__':
    for l in sys.argv[1:] or ['main', 'short']:
        G, T = build(l); print(l, 'ground cells', int(np.isfinite(G).sum()), 'top cells', int(np.isfinite(T).sum()))
