"""VR11: fix z-fighting found by tools/vr11_zfight.py. For every reported pair in which at least one mesh is visual-only
(name without a leading digit: road-line decals xline_*, visual roads xroad_*, zwiss highway_*/Railway_* overlays),
the visual-only mesh (the smaller one if both are) is lifted LOCALLY: each of its vertices lying within 3 cm of the
other surface is set 3 cm above it (vertex count/UVs unchanged, patched in place). Physics/physics pairs are handled by
tools/vr11_flush.py (hidden lower surfaces 3 cm under). Usage: python tools/vr11_zfix.py <zfight json>"""
import os, re, sys, json, struct, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K
from vr11_flush import TriIndex
Z = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vf_i29_speedway')) + '/'
GAP = 0.03
def mesh(fn, name):
    d = open(Z + fn, 'rb').read()
    for n, o, l, c in K.scan(Z + fn)[1]:
        if c == 2 and n == name:
            q = o + l + 8; nv, = struct.unpack_from('<I', d, q); V = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11).copy()
            q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); I = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3).astype(int)
            return dict(fn=fn, name=name, V=V, I=I, voff=q + 4)
def main(js):
    pairs = json.load(open(js)); rep = []; todo = {}
    for p in pairs:
        a, b = p['a'].split(':'), p['b'].split(':')
        va, vb = not re.match(r'^\d', a[1]), not re.match(r'^\d', b[1])
        if not (va or vb): continue
        if va and vb:
            if a[1].startswith('xline') != b[1].startswith('xline'): up, other = (a, b) if a[1].startswith('xline') else (b, a)
            else:
                ma, mb = mesh(*a), mesh(*b); up, other = (a, b) if len(ma['I']) <= len(mb['I']) else (b, a)
        else: up, other = (a, b) if va else (b, a)
        todo.setdefault(tuple(up), []).append(tuple(other))
    cache = {}
    for up, others in todo.items():
        m = cache.setdefault(up, mesh(*up)); idx = TriIndex()
        for o in others:
            mo = cache.get(o) or mesh(*o); idx.add(mo['V'][mo['I']][:, :, :3].astype(float), o[1])
        n = 0
        for i in range(len(m['V'])):
            r = idx.query(float(m['V'][i, 0]), float(m['V'][i, 2]))
            if r and -GAP < m['V'][i, 1] - r[0] < GAP: m['V'][i, 1] = r[0] + GAP; n += 1
        m['n'] = n; rep.append((up[0] + ':' + up[1], [o[1] for o in others], n))
        if n == 0:   # coplanar only inside large triangles of the upper mesh: push the other mesh's vertices down instead
            ui = TriIndex(); ui.add(m['V'][m['I']][:, :, :3].astype(float), up[1])
            for o in others:
                mo = cache.setdefault(o, mesh(*o)); k = 0
                for i in range(len(mo['V'])):
                    r = ui.query(float(mo['V'][i, 0]), float(mo['V'][i, 2]))
                    if r and -GAP < mo['V'][i, 1] - r[0] < GAP: mo['V'][i, 1] = r[0] - GAP; k += 1
                mo['n'] = mo.get('n', 0) + k; rep.append(('  lowered ' + o[0] + ':' + o[1], [up[1]], k))
    for fn in sorted({k[0] for k in cache}):
        d = bytearray(open(Z + fn, 'rb').read())
        for k, m in cache.items():
            if k[0] == fn and m.get('n'): d[m['voff']:m['voff'] + len(m['V']) * 44] = m['V'].astype('<f4').tobytes()
        open(Z + fn, 'wb').write(bytes(d)); K.scan(Z + fn)
    json.dump(rep, open('/workspace/vr11/zfix_report.json', 'w'), indent=1)
    for r in rep: print(r)
if __name__ == '__main__': main(sys.argv[1])
