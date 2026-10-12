"""VR9 hotfix: close every enclosed hole in the collision map (pre-existing zwiss/VR3 gaps:
ponds without a physical bed, the gaps beside the north-extension road where it cuts through the
railway embankment, a few slivers at x ~330). Uses the full-map raster from tools/vr9_holecheck.py.
Fill height per hole cell: nearest LOW boundary cell (boundary cells within 0.3 m of the component's
10th-percentile boundary height) -> a floor level with the road/bank, never a nodata/0 value.
Pond components (a visual 'ponds' mesh over them) get an invisible flat bed at the water mesh minimum - 0.3 m (8 m quads).
Each fill quad grid is extended 1 cell under the neighbouring surfaces (5 cm lower) so there is no seam.
Meshes are spliced into zw_rpm.kn5 next to 1GRASS_xx: 1GRASS_FILL_nn (visible, grass material,
same planar UVs) and 1GRASS_PONDBED_nn (invisible physics). Idempotent (removes old fill first is NOT
supported: run on a file without fill meshes). Usage: python tools/vr9_fill_holes.py <cov npz> <kn5>"""
import os, re, struct, sys
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K
import physraster as PR
from vr9_split_phys import parse_tree, ws, chunks

def mesh_bytes(name, V, I, mat, visible, tail_tpl):
    c = V[:, :3].mean(0); r = float(np.linalg.norm(V[:, :3] - c, axis=1).max())
    flags = bytes([0, 1, 0]) if visible else bytes([0, 0, 0])
    b = struct.pack('<I', 2) + ws(name) + struct.pack('<I', 0) + b'\x01' + flags
    b += struct.pack('<I', len(V)) + np.ascontiguousarray(V, '<f4').tobytes()
    b += struct.pack('<I', I.size) + np.ascontiguousarray(I, '<u2').tobytes()
    b += struct.pack('<II2f', mat, 0, 0, 0) + struct.pack('<3ff', *c, r) + (b'\x01' if visible else b'\x00')
    return b

def grid_mesh(cells, Hc, xs, zs, uvfit, step=1):
    """cells: list of (j,i) 1 m cells; Hc: height per cell; quads with per-cell flat height, shared corners averaged."""
    if step > 1:   # coarse blocks (constant-height pond beds)
        blk = {}
        for (j, i), h in zip(cells, Hc):
            blk.setdefault((j // step, i // step), []).append(h)
        cells = list(blk); Hc = [min(v) for v in blk.values()]
    corner = {}
    for (j, i), h in zip(cells, Hc):
        for dj in (0, 1):
            for di in (0, 1):
                corner.setdefault((j + dj, i + di), []).append(h)
    keys = list(corner); kid = {k: n for n, k in enumerate(keys)}
    x0, z0 = xs[0] - 0.5, zs[0] - 0.5
    P = np.array([[x0 + k[1] * step, np.mean(corner[k]), z0 + k[0] * step] for k in keys])
    V = np.zeros((len(P), 11), np.float32); V[:, :3] = P; V[:, 4] = 1.0; V[:, 8] = 1.0
    a, b = uvfit; A = np.c_[P[:, 0], P[:, 2], np.ones(len(P))]; V[:, 6] = A @ a; V[:, 7] = A @ b
    I = []
    for j, i in cells:
        p00, p01, p10, p11 = kid[(j, i)], kid[(j, i + 1)], kid[(j + 1, i)], kid[(j + 1, i + 1)]
        I += [(p00, p10, p11), (p00, p11, p01)]
    I = np.array(I)
    T = P[I]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    if (n[:, 1] < 0).mean() > 0.5: I = I[:, [0, 2, 1]]
    return V, I

def split_mesh(V, I, maxt=20000):
    C = V[I, :3].mean(1); out = []
    for sel in chunks(C, np.arange(len(I))):
        T = I[sel]; u = np.unique(T); m = np.full(len(V), -1); m[u] = np.arange(len(u)); out.append((V[u], m[T]))
    return out

def main(cov, fn):
    r = np.load(cov, allow_pickle=True); H = r['H']; xs = r['xs']; zs = r['zs']
    hole = ~np.isfinite(H); lab, n = ndimage.label(hole)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    # pond visual raster (highest hit = water/bank surface; we use its minimum per component)
    PR.Z = os.path.dirname(os.path.abspath(fn)) + '/'
    d = open(fn, 'rb').read(); _, nodes = K.scan(fn)
    pondT = []
    for name, o, l, c in nodes:
        if c == 2 and name.startswith('ponds'):
            q = o + l + 8; nv, = struct.unpack_from('<I', d, q); Vp = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11)[:, :3].astype(float)
            q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); Ip = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3).astype(int)
            pondT.append(('v', name, Vp[Ip]))
        if c == 2 and name == '1GRASS_00':
            q = o + l + 8; nv, = struct.unpack_from('<I', d, q); Vg = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11)
            q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); gmat, = struct.unpack_from('<I', d, q2 + 4 + ni * 2)
            A = np.c_[Vg[:, 0], Vg[:, 2], np.ones(nv)]
            uvfit = (np.linalg.lstsq(A, Vg[:, 6], rcond=None)[0], np.linalg.lstsq(A, Vg[:, 7], rcond=None)[0])
    box = (xs[0] - 0.5, xs[-1] + 0.5, zs[0] - 0.5, zs[-1] + 0.5)
    _, _, Hp, _, _, _ = PR.raster(pondT, box, 1.0) if pondT else (0, 0, np.full(H.shape, np.nan), 0, 0, 0)
    vis_cells, vis_h, bed_cells, bed_h = [], [], [], []
    rep = []
    sl = ndimage.find_objects(lab)
    for k in range(1, n + 1):
        if k in edge: continue
        s = sl[k - 1]; s = (slice(max(s[0].start - 3, 0), s[0].stop + 3), slice(max(s[1].start - 3, 0), s[1].stop + 3))
        m = lab[s] == k; Hs = H[s]
        ring = ndimage.binary_dilation(m) & ~m & np.isfinite(Hs)
        bh = Hs[ring]; p10 = np.percentile(bh, 10); low = ring & (Hs <= p10 + 0.3)
        _, (jj, ii) = ndimage.distance_transform_edt(~low, return_indices=True)
        fillh = Hs[jj, ii]
        pond = np.isfinite(Hp[s]) & m
        is_pond = pond.sum() > 0.3 * m.sum()
        if is_pond:
            floor = np.nanmin(Hp[s][pond]) - 0.3; fillh = np.full(fillh.shape, floor)
        cover = m | (ndimage.binary_dilation(m) & np.isfinite(Hs))      # 1-cell overlap under neighbours
        hh = np.where(m, fillh, np.minimum(fillh, Hs) - 0.05)
        J, I_ = np.nonzero(cover); cells = list(zip(J + s[0].start, I_ + s[1].start)); hv = hh[J, I_]
        (bed_cells if is_pond else vis_cells).extend(cells); (bed_h if is_pond else vis_h).extend(hv)
        rep.append((k, int(m.sum()), 'pond bed' if is_pond else 'floor', round(float(hh[m].min()), 2), round(float(hh[m].max()), 2)))
    for x in rep: print('fill comp', x)
    info = parse_tree(d, fn)
    names = [x['name'] for x in info]
    assert not any(nm.startswith('1GRASS_FILL') or nm.startswith('1GRASS_PONDBED') for nm in names), 'already filled'
    anchor = next(x for x in info if x['name'] == '1GRASS_07')
    blob = b''; cnt = 0
    for tag, cells, hv, vis, st in (('FILL', vis_cells, vis_h, True, 1), ('PONDBED', bed_cells, bed_h, False, 8)):
        if not cells: continue
        V, I = grid_mesh(cells, hv, xs, zs, uvfit, st)
        for q, (Vs, Is) in enumerate(split_mesh(V, I)):
            blob += mesh_bytes('1GRASS_%s_%02d' % (tag, q), Vs, Is, gmat, vis, None); cnt += 1
            print('  mesh 1GRASS_%s_%02d' % (tag, q), len(Is), 'tris', 'visible' if vis else 'invisible')
    d2 = bytearray(d); par = info[anchor['parent']]
    c0, = struct.unpack_from('<I', d2, par['o'] + par['l']); struct.pack_into('<I', d2, par['o'] + par['l'], c0 + cnt)
    out = bytes(d2[:anchor['next']]) + blob + bytes(d2[anchor['next']:])
    open(fn, 'wb').write(out); K.scan(fn); print('wrote', fn, cnt, 'fill meshes')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
