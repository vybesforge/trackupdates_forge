"""VR10: painted start (stage) line on the drag strip. The strip texture (dragroad.dds, mask 001tarmac_mask-2) has NO
painted transverse line anywhere near the launch area (sampled every 5 cm, z -333..-400: only a gradual light-to-dark
fade at z -337..-340 and the centre stripe), so the scripts' stage beam z -347.5 (pre-stage 0.178 m / 7 in earlier,
z -347.322) had nothing to line up with. This paints the line where the beam is: a 10 cm white line (z -347.45..-347.55)
across both lanes plus a thin 5 cm pre-stage tick per lane at z -347.322, draped on 1LAUNCHA_strip +1.2 cm.
Visual only, added to vf_draglaunch.kn5 (rewritten via kn5write; existing meshes/materials untouched)."""
import os, sys, struct, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K, kn5write as W, vr5_meshlib as L
Z = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vf_i29_speedway')); F = f'{Z}/vf_draglaunch.kn5'
STAGE_Z, PRE_GAP = -347.5, 0.178
def meshes(fn):
    d = open(fn, 'rb').read(); out = []
    for name, o, l, c in K.scan(fn)[1]:
        if c != 2: continue
        q = o + l + 8; nv, = struct.unpack_from('<I', d, q); V = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11).copy()
        q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); I = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3).copy()
        mat, = struct.unpack_from('<I', d, q2 + 4 + ni * 2); out.append(dict(name=name, verts=V, idx=I, mat_index=mat))
    return out
def surf(T, x, z):
    A = T[:, 0, [0, 2]]; B = T[:, 1, [0, 2]]; C = T[:, 2, [0, 2]]; v0 = B - A; v1 = C - A; v2 = np.array([x, z]) - A
    den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]; den[den == 0] = 1e-12
    b = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den; c = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den; a = 1 - b - c
    k = np.where((a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6))[0][0]; return a[k] * T[k, 0, 1] + b[k] * T[k, 1, 1] + c[k] * T[k, 2, 1]
def strip(T, x0, x1, z0, z1, dx=0.5):
    xs = np.linspace(x0, x1, max(2, int(abs(x1 - x0) / dx) + 1)); V = []; I = []
    for i, x in enumerate(xs):
        for z in (z0, z1): V.append([x, surf(T, x, z) + 0.012, z, 0, 1, 0, i / (len(xs) - 1), z == z1, 1, 0, 0])
        if i: a = 2 * (i - 1); I += [(a, a + 2, a + 1), (a + 1, a + 2, a + 3)]
    V = np.array(V, np.float32); I = np.array(I); return V, L.fix_winding(V, I)
def build():
    ME = meshes(F)
    if any(m['name'] == 'drag_stageline' for m in ME): print('already applied'); return
    T = next(m['verts'][m['idx']] for m in ME if m['name'] == '1LAUNCHA_strip')
    mats = [dict(name=k, **v) for k, v in W.read_materials(F).items()]; tex = [(t[0], K.get_tex(F, t[0])) for t in K.scan(F)[0]]
    base = next(m for m in mats if m['name'] == 'drtree_black')
    tex.append(('drag_paint_white.dds', L.solid_dds((226, 226, 220))))
    m = dict(base); m['name'] = 'drag_paint_white'; m['samplers'] = [(s, sl, 'drag_paint_white.dds') for s, sl, _ in base['samplers']]; mats.append(m)
    mi = len(mats) - 1
    ME.append(dict(name='drag_stageline', mat_index=mi, verts=None, idx=None))
    V, I = strip(T, -259.6, -242.9, STAGE_Z + 0.05, STAGE_Z - 0.05); ME[-1].update(verts=V, idx=I.astype('<u2'))
    parts = [strip(T, cx - 1.2, cx + 1.2, STAGE_Z + PRE_GAP + 0.025, STAGE_Z + PRE_GAP - 0.025) for cx in (-255.75, -246.75)]
    V, I = L.merge(parts); ME.append(dict(name='drag_prestageline', mat_index=mi, verts=V.astype(np.float32), idx=I.astype('<u2')))
    W.write_kn5(F, tex, mats, ME, rootname='vf_draglaunch'); K.scan(F); print('ok', [(m['name'], len(m['idx'])) for m in ME[-2:]])
if __name__ == '__main__': build()
