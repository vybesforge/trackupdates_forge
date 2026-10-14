"""VR11: z-fight fix for coplanar overlaps that lie inside big triangles of both meshes (I-29 crossing: zwiss
highway_SUB1 over the grass, Railway_bridge001 over highway_SUB1). For each pair (upper visual-only mesh first) the
upper mesh's triangles whose plan area contains a coplanar cell (|gap| < 3 cm, 0.25 m raster) get their vertices lifted
so the gap is 3 cm. Pairs are processed in order, so a lifted highway is re-measured against the bridge.
Usage: python tools/vr11_zfix_tri.py"""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K, physraster as PR
from vr11_zfix import mesh, Z
from vr11_flush import TriIndex
PAIRS = [(('vf_i29_speedway.kn5', 'highway_SUB1'), [('vf_i29_speedway.kn5', '1GRASS_02'), ('vf_i29_speedway.kn5', '1GRASS_00_02'), ('vf_ext.kn5', '1GRASS_EXT_2')]),
         (('vf_i29_speedway.kn5', 'Railway_bridge001'), [('vf_i29_speedway.kn5', 'highway_SUB1')])]
GAP = 0.03
def main():
    cache = {}; rep = []
    get = lambda k: cache.setdefault(k, mesh(*k))
    for up, others in PAIRS:
        m = get(up); T = m['V'][m['I']][:, :, :3].astype(float); idx = TriIndex()
        for o in others:
            mo = get(o); idx.add(mo['V'][mo['I']][:, :, :3].astype(float), o[1])
        lift = {}
        for t, tri in zip(T, m['I']):
            x0, x1, z0, z1 = t[:, 0].min(), t[:, 0].max(), t[:, 2].min(), t[:, 2].max()
            if (x1 - x0) * (z1 - z0) > 4e5: continue
            for x in np.arange(x0, x1, 0.5):
                for z in np.arange(z0, z1, 0.5):
                    a, b, c = t; v0 = b - a; v1 = c - a; den = v0[0] * v1[2] - v1[0] * v0[2]
                    if abs(den) < 1e-9: continue
                    u = ((x - a[0]) * v1[2] - v1[0] * (z - a[2])) / den; v = (v0[0] * (z - a[2]) - (x - a[0]) * v0[2]) / den
                    if u < 0 or v < 0 or u + v > 1: continue
                    y = a[1] + u * v0[1] + v * v1[1]; r = idx.query(x, z)
                    if r and -GAP < y - r[0] < GAP:
                        need = r[0] + GAP - y
                        for vi in tri: lift[vi] = max(lift.get(vi, 0.0), need)
        for vi, dv in lift.items(): m['V'][vi, 1] += dv
        m['n'] = len(lift); rep.append((up[1], len(lift), round(max(lift.values()), 3) if lift else 0))
    for fn in sorted({k[0] for k in cache}):
        d = bytearray(open(Z + fn, 'rb').read())
        for k, m in cache.items():
            if k[0] == fn and m.get('n'): d[m['voff']:m['voff'] + len(m['V']) * 44] = m['V'].astype('<f4').tobytes()
        open(Z + fn, 'wb').write(bytes(d)); K.scan(Z + fn)
    print(rep)
if __name__ == '__main__': main()
