"""VR9 hotfix: split oversize physics meshes so every collision mesh stays <= 20000 triangles
(60000 indices). AC's track collision silently drops / mis-handles meshes beyond 65535 indices,
so cars fell through the re-draped (refined) 1GRASS (104526 tris) -> "void" on grass.
(The VR3 north-extension grass was already split at 21000 tris for this reason.)
Splits by recursive spatial bisection of triangle centroids; chunk names <name>_00, _01 ... keep the
surfaces.ini KEY prefix (GRASS_00 matches KEY=GRASS). Shared border vertices are duplicated at
identical positions, so chunks join with zero gap. Run AFTER tools/vr9_lidar.py.
Usage: python tools/vr9_split_phys.py zw_rpm/zw_rpm.kn5 [...]   (idempotent)"""
import os, re, struct, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K
MAXT = 20000

def ws(s):
    b = s.encode(); return struct.pack('<I', len(b)) + b

def parse_tree(d, fn):
    _, nodes = K.scan(fn)
    # rebuild parent / end offsets by walking again with child counts
    info = []
    for name, o, l, c in nodes:
        nc, = struct.unpack_from('<I', d, o + l)
        info.append(dict(name=name, o=o, l=l, cls=c, nc=nc, start=o - 4))
    for i, n in enumerate(info):
        n['next'] = info[i + 1]['start'] if i + 1 < len(info) else len(d)
    stack = []
    for i, n in enumerate(info):
        n['parent'] = stack[-1][0] if stack else None
        if stack:
            stack[-1][1] -= 1
        while stack and stack[-1][1] == 0:
            stack.pop()
        if n['nc'] > 0:
            stack.append([i, n['nc']])
    return info

def chunks(C, idx):
    if len(idx) <= MAXT:
        return [idx]
    span = C[idx].max(0) - C[idx].min(0); ax = 0 if span[0] >= span[2] else 2
    order = idx[np.argsort(C[idx, ax], kind='stable')]; h = len(order) // 2
    return chunks(C, np.sort(order[:h])) + chunks(C, np.sort(order[h:]))

def split_file(fn):
    d = open(fn, 'rb').read(); info = parse_tree(d, fn)
    big = [n for n in info if n['cls'] == 2 and re.match(r'^\d+[A-Z]', n['name'])
           and struct.unpack_from('<I', d, n['o'] + n['l'] + 8 + 4 + struct.unpack_from('<I', d, n['o'] + n['l'] + 8)[0] * 44)[0] > MAXT * 3]
    if not big:
        print(fn, 'nothing to split'); return
    out = bytearray(); pos = 0; extra = {}
    for n in big:
        extra[n['parent']] = extra.get(n['parent'], 0)
    reps = {}
    for n in big:
        o, l = n['o'], n['l']; p = o + l + 5; flags = d[p:p + 3]; q = p + 3
        nv, = struct.unpack_from('<I', d, q); V = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11)
        q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); I = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3)
        q3 = q2 + 4 + ni * 2; mat, layer, lod0, lod1 = struct.unpack_from('<II2f', d, q3); rend = d[q3 + 32:q3 + 33]
        assert q3 + 33 == n['next'], 'unexpected mesh tail'
        C = V[I, :3].mean(1); parts = chunks(C, np.arange(len(I)))
        blob = bytearray()
        for k, sel in enumerate(parts):
            T = I[sel]; u = np.unique(T); m = np.full(nv, -1, np.int64); m[u] = np.arange(len(u))
            Vs = np.ascontiguousarray(V[u], '<f4'); Is = np.ascontiguousarray(m[T], '<u2')
            c = Vs[:, :3].mean(0); r = float(np.linalg.norm(Vs[:, :3] - c, axis=1).max())
            blob += struct.pack('<I', 2) + ws('%s_%02d' % (n['name'], k)) + struct.pack('<I', 0) + b'\x01' + flags
            blob += struct.pack('<I', len(Vs)) + Vs.tobytes() + struct.pack('<I', Is.size) + Is.tobytes()
            blob += struct.pack('<II2f', mat, layer, lod0, lod1) + struct.pack('<3ff', *c, r) + rend
        reps[n['start']] = (n['next'], bytes(blob))
        extra[n['parent']] += len(parts) - 1
        print(fn, n['name'], len(I), 'tris ->', len(parts), 'meshes', [len(s) for s in parts])
    # patch parent child counts, then splice
    d2 = bytearray(d)
    for pi, add in extra.items():
        pn = info[pi]; cnt, = struct.unpack_from('<I', d2, pn['o'] + pn['l']); struct.pack_into('<I', d2, pn['o'] + pn['l'], cnt + add)
    for s in sorted(reps):
        e, blob = reps[s]; out += d2[pos:s] + blob; pos = e
    out += d2[pos:]
    open(fn, 'wb').write(bytes(out)); K.scan(fn)

if __name__ == '__main__':
    for f in sys.argv[1:]:
        split_file(f)
