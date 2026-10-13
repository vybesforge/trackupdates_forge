"""VR10: pit-box spawn pads. Measures the local slope under each of the 36 AC_PIT_n footprints
(plane fit of the collision surface over 5.2 x 2.2 m at 0.25 m) and, where it exceeds LIMIT, flattens a pad:
delta(x,z) = w(x,z) * (h0 - plane(x,z)), h0 = plane at the spawn; w = 1 within the footprint + 1 m,
smoothstep to 0 over the next 4 m. The same delta field is applied to every ground-like mesh (visual + physics)
in all kn5 so layers stay consistent; meshes are refined to <= 1 m inside the pad zones first.
Usage: python tools/vr10_pads.py measure|apply"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5tree as T, physraster as PR, vr9_lidar as L, vr7_common as C
Z = C.Z; LIMIT = 0.015; LA, WA, MARG, BLEND = 2.6, 1.1, 1.0, 4.0
FILES = ['vf_i29_speedway.kn5', 'vf_i29_speedway_physical.kn5', 'vf_i29_speedway_gp.kn5', 'vf_i29_speedway_own.kn5', 'zw_tents.kn5']
def pits():
    return sorted([(int(n['name'][7:]), n['W']) for n in T.walk(Z + 'vf_i29_speedway.kn5') if n['cls'] == 1 and n['name'].startswith('AC_PIT_')])
def measure():
    P = pits(); box = (-230, 180, -60, 245); PR.Z = Z
    xs, zs, H, KEY, UP, names = PR.raster(PR.physmeshes(FILES, box), box, 0.25)
    out = []
    for i, W in P:
        p, f, r = W[3, :3], W[2, :3], W[0, :3]; pts = []
        for a in np.linspace(-LA, LA, 21):
            for b in np.linspace(-WA, WA, 9):
                q = p + a * f + b * r; ii = int(round((q[0] - xs[0]) / 0.25)); jj = int(round((q[2] - zs[0]) / 0.25)); pts.append((q[0], q[2], H[jj, ii]))
        q = np.array(pts); A = np.c_[q[:, 0] - p[0], q[:, 1] - p[2], np.ones(len(q))]; c = np.linalg.lstsq(A, q[:, 2], rcond=None)[0]
        slope = float(np.hypot(c[0], c[1])); along = float(abs(c[0] * f[0] + c[1] * f[2]) / (np.hypot(f[0], f[2]) + 1e-9))
        out.append(dict(pit=i, x=float(p[0]), z=float(p[2]), h0=float(c[2]), gx=float(c[0]), gz=float(c[1]), slope_pct=slope * 100, along_pct=along * 100,
                        fx=float(f[0]), fz=float(f[2]), resid=float(np.abs(A @ c - q[:, 2]).max())))
    return out
def pad_delta(pads):
    def delta(x, z):
        x = np.asarray(x, float); z = np.asarray(z, float); d = np.zeros(x.shape)
        for p in pads:
            fx, fz = p['fx'], p['fz']; n = np.hypot(fx, fz); fx, fz = fx / n, fz / n
            dx, dz = x - p['x'], z - p['z']; a = np.abs(dx * fx + dz * fz); b = np.abs(-dx * fz + dz * fx)
            e = np.maximum(np.maximum(a - (LA + MARG), b - (WA + MARG)), 0) / BLEND; w = 1 - np.clip(e, 0, 1); w = w * w * (3 - 2 * w)
            d += w * (-(p['gx'] * dx + p['gz'] * dz))      # h0 - plane = -(gradient . offset)
        return d
    return delta
def apply(pads):
    delta = pad_delta(pads); R = LA + MARG + BLEND + 1
    def inzone(x, z):
        return any(np.hypot(x - p['x'], z - p['z']) < R + 2 for p in pads)
    def near(x, z, Lv): return 1.0 if inzone(x, z) else 1e9
    rep = {}
    for fn in FILES:
        d, nodes = L.nodes_full(Z + fn); newmesh = {}
        for n in nodes:
            if n['cls'] != 2: continue
            V, I = n['V'], n['I'].astype(np.int64); Wm = n['W'].astype(float); Pw = np.c_[V[:, :3], np.ones(len(V))] @ Wm
            dl = delta(Pw[:, 0], Pw[:, 2])
            if np.abs(dl).max() < 0.0005: continue
            if not (L.is_flat_ground(n) or np.ptp(V[:, 1]) < 0.6): continue
            V2, I2 = L.refine(V, I, 0.0, near) if True else (V, I)
            P = np.c_[V2[:, :3], np.ones(len(V2))] @ Wm; P[:, 1] += delta(P[:, 0], P[:, 2])
            Vn = V2.copy(); Vn[:, :3] = (np.c_[P[:, :3], np.ones(len(P))] @ np.linalg.inv(Wm))[:, :3]
            assert len(Vn) < 65536, (n['name'], len(Vn))
            newmesh[n['name'] + '#' + str(n['vo'])] = (Vn, I2); rep[f'{fn}:{n["name"]}'] = (len(I), len(I2))
        if newmesh: L.write(Z + fn, d, nodes, newmesh, {})
    return rep
if __name__ == '__main__':
    m = measure(); bad = [p for p in m if p['slope_pct'] > LIMIT * 100]
    print('slope %: max', round(max(p['slope_pct'] for p in m), 2), 'mean', round(np.mean([p['slope_pct'] for p in m]), 2), 'over', LIMIT * 100, ':', len(bad))
    print(sorted((p['pit'], round(p['slope_pct'], 2)) for p in m))
    json.dump(m, open('/workspace/vr10/pads_before.json', 'w'), indent=1)
    if len(sys.argv) > 1 and sys.argv[1] == 'apply' and bad:
        print(apply(bad)); m2 = measure(); json.dump(m2, open('/workspace/vr10/pads_after.json', 'w'), indent=1)
        print('after: max slope %', round(max(p['slope_pct'] for p in m2), 2), sorted((p['pit'], round(p['slope_pct'], 2)) for p in m2))
