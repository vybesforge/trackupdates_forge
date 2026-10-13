"""VR11: find z-fighting candidates: pairs of VISIBLE meshes whose surfaces overlap (in plan) within TOL vertically.
Per mesh: top-down raster (0.5 m) of its own triangles inside the region; pairs with >= MINCELLS overlap cells where
|h_a - h_b| < TOL are reported with the share of their overlap that is coplanar. Usage: vr11_zfight.py [tag]"""
import os, re, sys, struct, json, glob, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K, physraster as PR
Z = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vf_i29_speedway')) + '/'
BOX = (-1000.0, 820.0, -3005.0, -2380.0); RES = 0.5; TOL = 0.02; MINCELLS = 8
def visible_meshes(fn):
    d = open(fn, 'rb').read(); out = []
    for name, o, l, c in K.scan(fn)[1]:
        if c != 2: continue
        p = o + l + 5; fl = d[p:p + 3]; q = p + 3; nv, = struct.unpack_from('<I', d, q)
        q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); rend = d[q2 + 4 + ni * 2 + 4 + 4 + 8 + 16]
        if fl[1] != 1 or rend != 1: continue
        V = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11)[:, :3].astype(float); I = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3).astype(int)
        T = V[I]; C = T[:, :, [0, 2]]
        k = (C[:, :, 0].max(1) > BOX[0]) & (C[:, :, 0].min(1) < BOX[1]) & (C[:, :, 1].max(1) > BOX[2]) & (C[:, :, 1].min(1) < BOX[3])
        if k.sum(): out.append((os.path.basename(fn), name, T[k]))
    return out
def main(tag):
    M = []
    for f in sorted(glob.glob(Z + '*.kn5')): M += visible_meshes(f)
    R = []
    for fn, name, T in M:
        b = (max(BOX[0], T[:, :, 0].min() - 1), min(BOX[1], T[:, :, 0].max() + 1), max(BOX[2], T[:, :, 2].min() - 1), min(BOX[3], T[:, :, 2].max() + 1))
        b = (BOX[0] + np.floor((b[0] - BOX[0]) / RES) * RES, b[1], BOX[2] + np.floor((b[2] - BOX[2]) / RES) * RES, b[3])
        xs, zs, H, _, _, _ = PR.raster([(fn, name, T)], b, RES)
        R.append((fn, name, int(round((b[0] - BOX[0]) / RES)), int(round((b[2] - BOX[2]) / RES)), H))
    rep = []
    for a in range(len(R)):
        fa, na, ia, ja, Ha = R[a]
        for b in range(a + 1, len(R)):
            fb, nb, ib, jb, Hb = R[b]
            i0, i1 = max(ia, ib), min(ia + Ha.shape[1], ib + Hb.shape[1]); j0, j1 = max(ja, jb), min(ja + Ha.shape[0], jb + Hb.shape[0])
            if i1 <= i0 or j1 <= j0: continue
            A = Ha[j0 - ja:j1 - ja, i0 - ia:i1 - ia]; B = Hb[j0 - jb:j1 - jb, i0 - ib:i1 - ib]
            m = np.isfinite(A) & np.isfinite(B)
            if m.sum() < MINCELLS: continue
            dd = np.abs(A[m] - B[m]); cop = (dd < TOL).sum()
            if cop >= MINCELLS:
                jj, ii = np.nonzero(m); k = np.argmin(np.abs(A - B)[m])
                rep.append(dict(a=f'{fa}:{na}', b=f'{fb}:{nb}', coplanar_m2=float(cop * RES * RES), overlap_m2=float(m.sum() * RES * RES),
                                median_gap_m=round(float(np.median(dd[dd < TOL])), 4), at=(BOX[0] + (i0 + ii[k]) * RES, BOX[2] + (j0 + jj[k]) * RES)))
    rep.sort(key=lambda r: -r['coplanar_m2'])
    json.dump(rep, open('/workspace/vr11/zfight_%s.json' % tag, 'w'), indent=1)
    for r in rep[:40]: print(r)
    print('pairs', len(rep), 'total coplanar m2', round(sum(r['coplanar_m2'] for r in rep)))
if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else 'now')
