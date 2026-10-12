"""VR10: re-drape the north extension and make the whole map follow one lidar field (tools/vr10_field.py).
For every kn5: delta = T_final - (field already applied): VR9 field for the track files, 0 for zw_ext.kn5
(taken from the flat stage backup/pre_vr9). Ground-like meshes are warped per vertex (refined first so long
triangles follow the field); 3D props in zw_ext (stations, canopies, signs, poles, lamps...) are moved rigidly per
connected part by the field value at their footprint. AC_ dummies and AI lines get the same delta.
Input zw_rpm.kn5 must be the split, un-filled VR9 file (hole fills are regenerated afterwards).
Then run: vr9_split_phys.py on all kn5, vr9_holecheck.py, vr9_fill_holes.py, vr9_holecheck.py."""
import os, sys, json, shutil, numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vr9_lidar as L, vr10_field as F, vr7_common as C
FLAT = '/workspace/rpotm/backup/pre_vr9/zw_rpm/'
DST = C.Z
def main(zw_rpm_src):
    f = F.load(); D9f = np.load('/workspace/vr9/field.npz')['D']
    def D9(x, z): return L.field_eval(D9f, x, z)
    def Tf(x, z): return F.evaluate(f, x, z)
    NEARD = ndimage.distance_transform_edt(~f['pav']); x0, z0 = float(f['xs'][0]), float(f['zs'][0])
    def near(x, z, Lv):
        dd = NEARD[int(np.clip(round(z - z0), 0, NEARD.shape[0] - 1)), int(np.clip(round(x - x0), 0, NEARD.shape[1] - 1))]
        return Lv[0] if dd < 12 else (Lv[1] if dd < 60 else Lv[2])
    rep = {}
    for fn in sorted(os.listdir(DST)):
        if not fn.endswith('.kn5'): continue
        ext = fn == 'zw_ext.kn5'
        src = FLAT + fn if ext else (zw_rpm_src if fn == 'zw_rpm.kn5' else DST + fn)
        d, nodes = L.nodes_full(src); newmesh = {}; dummy = {}; moved = set(); nref = 0; nrigid = 0; dmax = 0.0
        applied = (lambda x, z: np.zeros(len(np.atleast_1d(x)))) if ext else D9
        for n in nodes:
            if n['cls'] == 1 and n['name'].startswith('AC_'):
                p = n['W'][3, :3]; dummy[n['name']] = float(Tf([p[0]], [p[2]])[0] - applied([p[0]], [p[2]])[0]); moved.add(tuple(n['path'] + [n['name']]))
        for n in nodes:
            if n['cls'] != 2: continue
            if any(tuple(n['path'][:k]) in moved for k in range(1, len(n['path']) + 1)): continue
            V, I = n['V'], n['I'].astype(np.int64); Wm = n['W'].astype(float)
            Pw = np.c_[V[:, :3], np.ones(len(V))] @ Wm
            dl = Tf(Pw[:, 0], Pw[:, 2]) - applied(Pw[:, 0], Pw[:, 2])
            if np.abs(dl).max() < 0.002: continue
            V2, I2 = V, I
            ground = L.is_flat_ground(n) or (len(I) and (V[:, 1].max() - V[:, 1].min()) < 0.6 and n['name'].startswith(('xline', '1', 'xlot', 'xmark')))
            if ground:
                if np.ptp(dl) > 0.004:
                    drv = n['name'][:1].isdigit() and 'WALL' not in n['name']
                    if 'GRASS' in n['name'] or 'google' in n['name'].lower(): V2, I2 = L.refine(V, I, (4.0, 10.0, 50.0), near)
                    else: V2, I2 = L.refine(V, I, 4.0 if drv else 16.0)
                    if len(V2) >= 65536:
                        V2, I2 = L.refine(V, I, (6.0, 16.0, 60.0), near) if 'GRASS' in n['name'] else L.refine(V, I, 6.0 if drv else 24.0)
                    if len(V2) >= 65536:
                        V2, I2 = L.refine(V, I, (8.0, 24.0, 80.0), near) if 'GRASS' in n['name'] else L.refine(V, I, 10.0 if drv else 40.0)
                    if len(V2) > len(V): nref += 1
                P = np.c_[V2[:, :3], np.ones(len(V2))] @ Wm
                P[:, 1] += Tf(P[:, 0], P[:, 2]) - applied(P[:, 0], P[:, 2])
            else:
                # rigid per connected part, by the field at the part's footprint (lowest 20 % of its vertices)
                nv = len(V); g = coo_matrix((np.ones(len(I) * 2), (np.r_[I[:, 0], I[:, 1]], np.r_[I[:, 1], I[:, 2]])), shape=(nv, nv))
                nc, lab = connected_components(g, directed=False)
                P = Pw.copy()
                for c in range(nc):
                    m = lab == c; yy = P[m, 1]; low = m.copy(); low[m] = yy <= np.percentile(yy, 20) + 1e-6
                    cx, cz = P[low, 0].mean(), P[low, 2].mean()
                    P[m, 1] += float(Tf([cx], [cz])[0] - applied([cx], [cz])[0])
                nrigid += 1
            Vn = V2.copy(); Vn[:, :3] = (np.c_[P[:, :3], np.ones(len(P))] @ np.linalg.inv(Wm))[:, :3]
            dmax = max(dmax, float(np.abs(dl).max()))
            newmesh[n['name'] + '#' + str(n['vo'])] = (Vn, I2)
        dummy = {k: v for k, v in dummy.items() if abs(v) > 1e-4}
        if not newmesh and not dummy and not ext: print(fn, 'unchanged'); continue
        L.write(DST + fn, d, nodes, newmesh, dummy)
        rep[fn] = dict(meshes=len(newmesh), refined=nref, rigid=nrigid, dummies=len(dummy), max_delta=round(dmax, 3))
        print(fn, rep[fn])
    for lay in ('main', 'short'):
        for lane in ('fast_lane', 'pit_lane'):
            a = C.read_ai(DST + f'{lay}/ai/{lane}.ai'); p = a['P']['p'].astype(float)
            dl = Tf(p[:, 0], p[:, 2]) - D9(p[:, 0], p[:, 2]); p[:, 1] += dl; C.write_ai(DST + f'{lay}/ai/{lane}.ai', p, a['E'].copy())
            rep[f'ai_{lay}_{lane}'] = round(float(np.abs(dl).max()), 3)
    json.dump(rep, open('/workspace/vr10/ext_report.json', 'w'), indent=1); print(rep)
if __name__ == '__main__': main(sys.argv[1])
