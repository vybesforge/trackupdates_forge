"""VR10: better heads for the 2 paddock figures (vf_vr6.kn5, rewritten in place with kn5write).
Adds per person: eye whites + pupils, brows (hair colour), nose and ears (skin), mouth (lip colour), a denser
hair shell with a softer hairline and sideburns; the grey-shirt figure also gets a navy cap (crown + brim).
All parts are small ellipsoids (~1.9k tris per person), placed on the VR8 head (same centre/axes as
tools/vr7_people.py) and shifted by the lidar warp the head already received. Visual only, contact shadows unchanged."""
import os, sys, struct, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K, kn5write as W, vr5_meshlib as L, vr7_people as P
F = os.path.join(P.Z, 'vf_vr6.kn5')
def read_meshes(fn):
    d = open(fn, 'rb').read(); out = []
    for name, o, l, c in K.scan(fn)[1]:
        if c != 2: continue
        q = o + l + 8; nv, = struct.unpack_from('<I', d, q); V = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11).copy()
        q2 = q + 4 + nv * 44; ni, = struct.unpack_from('<I', d, q2); I = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3).copy()
        mat, = struct.unpack_from('<I', d, q2 + 4 + ni * 2); out.append(dict(name=name, verts=V, idx=I, mat_index=mat))
    return out
def hair_shell(cen, r, fw, nu=28, nv=18):
    fw = np.asarray(fw, float); sd = np.cross([0, 1, 0], fw); V = []; I = []
    for j in range(nv + 1):
        th = np.pi * j / nv
        for i in range(nu + 1):
            ph = 2 * np.pi * i / nu; n = np.array([np.sin(th) * np.cos(ph), np.cos(th), np.sin(th) * np.sin(ph)])
            bump = 1.0 + 0.06 * max(n[1], 0) ** 2              # a little volume on top
            p = cen + (sd * n[0] * r[0] + np.array([0, 1, 0]) * n[1] * r[1] + fw * n[2] * r[2]) * bump
            nn = sd * n[0] / r[0] + np.array([0, 1., 0]) * n[1] / r[1] + fw * n[2] / r[2]; nn /= np.linalg.norm(nn) + 1e-9
            V.append(np.r_[p, nn, i / nu, j / nv, sd])
    V = np.array(V, np.float32)
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; b = a + nu + 1
            for t in ((a, a + 1, b), (a + 1, b + 1, b)):
                n = (V[list(t), :3] - cen).mean(0); up = n[1] / r[1]; front = np.dot(n, fw) / r[2]; side = abs(np.dot(n, sd)) / r[0]
                line = -0.15 + 0.42 * max(front, 0) ** 1.5 - 0.25 * max(-front, 0)     # soft forehead curve, lower nape
                sideburn = side > 0.8 and front > -0.1 and front < 0.45 and up > -0.45
                if up < line and not sideburn: continue
                I.append(t)
    I = np.array(I); return V, L.fix_winding(V, I)
def blob(cen, r, fw, nu=10, nv=7):
    return P.ellip(np.asarray(cen, float), r, fw, nu=nu, nv=nv)
def build():
    T0, ME0 = P.people_meshes()            # the VR8 heads as generated at Y = 0 (before the lidar warp)
    cur = read_meshes(F); byname = {m['name']: m for m in cur}
    tex = [(t[0], K.get_tex(F, t[0])) for t in K.scan(F)[0]]
    mats = [dict(name=k, **v) for k, v in W.read_materials(F).items()]
    names = [m['name'] for m in mats]
    if 'vr10_eye_white' in names: print('already applied'); return
    tpl = mats[names.index('vr8_head_blue')]
    def addmat(name, texname, rgb):
        tex.append((texname, L.solid_dds(rgb))); m = dict(tpl); m['name'] = name; m['samplers'] = [(s, sl, texname) for s, sl, _ in tpl['samplers']]
        mats.append(m); return len(mats) - 1
    m_white = addmat('vr10_eye_white', 'vr10_eye_white.dds', (232, 228, 220)); m_dark = addmat('vr10_eye_dark', 'vr10_eye_dark.dds', (34, 26, 22))
    m_lip = addmat('vr10_lips', 'vr10_lips.dds', (150, 84, 76)); m_cap = addmat('vr10_cap', 'vr10_cap.dds', (32, 42, 72))
    meshes = [m for m in cur]
    V0, I0, atlas = P.marshal(); base = V0[:, :3].copy(); c = np.r_[base[:, 0].mean(), base[:, 1].min(), base[:, 2].mean()]; yaw0 = P.facing(V0)
    h = base[:, 1] - base[:, 1].min(); hc = base[(h > 1.40) & (h < 1.5)][:, [0, 2]].mean(0); f0 = np.array([np.sin(yaw0), -np.cos(yaw0)])
    y0 = base[:, 1].min(); hcen = np.r_[hc[0], y0 + 1.635, hc[1]]; fw = np.r_[f0[0], 0, f0[1]]; sd = np.cross([0, 1, 0], fw); up = np.r_[0, 1., 0]
    gen = {m[0]: m for m in ME0}
    rep = []
    for x, z, yaw, rgb, nm, hair in P.PEOPLE:
        dy = float(byname[f'vr8_head_{nm}']['verts'][:, 1].mean() - gen[f'vr8_head_{nm}'][2][:, 1].mean())
        a = yaw - yaw0; R = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
        put = lambda Q: (Q - c) @ R.T + [x, P.Y + dy, z]
        S = lambda s, u, f: hcen + sd * s + up * u + fw * f
        parts = {m_white: [], m_dark: [], m_lip: [], 'skin': [], 'hair': [], m_cap: []}
        for s in (-1, 1):
            parts[m_white].append(blob(S(0.031 * s, 0.012, 0.086), (0.015, 0.010, 0.007), fw))
            parts[m_dark].append(blob(S(0.031 * s, 0.012, 0.092), (0.0065, 0.0065, 0.004), fw, 8, 6))
            parts['hair'].append(blob(S(0.033 * s, 0.033, 0.088), (0.019, 0.0045, 0.006), fw, 8, 5))
            parts['skin'].append(blob(S(0.090 * s, 0.002, -0.006), (0.011, 0.027, 0.017), fw))
        parts['skin'].append(blob(S(0, -0.010, 0.094), (0.011, 0.022, 0.016), fw))
        parts[m_lip].append(blob(S(0, -0.047, 0.086), (0.021, 0.0045, 0.006), fw, 10, 5))
        hairV = [hair_shell(hcen + [0, 0.010, 0] - fw * 0.006, (0.099, 0.118, 0.106), fw)]
        if nm == 'grey':      # cap: crown + brim
            cv, ci = hair_shell(hcen + [0, 0.016, 0], (0.104, 0.122, 0.110), fw, 24, 14)
            n = (cv[:, :3] - hcen); keep = np.all((n[ci, 1].mean(1, keepdims=True)) > 0.035, 1)
            parts[m_cap].append((cv, ci[keep]))
            parts[m_cap].append(blob(S(0, 0.052, 0.112), (0.078, 0.008, 0.062), fw, 14, 6))
        def emit(mname, mat, plist):
            if not plist: return
            Vh, Ih = L.merge(plist); Vh = Vh.copy(); Vh[:, :3] = put(Vh[:, :3]); Vh[:, 3:6] = Vh[:, 3:6] @ R.T; Vh[:, 8:11] = Vh[:, 8:11] @ R.T
            meshes.append(dict(name=mname, mat_index=mat, verts=Vh.astype(np.float32), idx=Ih.astype('<u2'))); rep.append((mname, len(Ih)))
        # replace hair shell, add features
        Vh, Ih = L.merge(hairV + parts['hair']); Vh = Vh.copy(); Vh[:, :3] = put(Vh[:, :3]); Vh[:, 3:6] = Vh[:, 3:6] @ R.T; Vh[:, 8:11] = Vh[:, 8:11] @ R.T
        hm = byname[f'vr8_hair_{nm}']; hm['verts'] = Vh.astype(np.float32); hm['idx'] = Ih.astype('<u2'); rep.append((hm['name'], len(Ih)))
        emit(f'vr10_face_skin_{nm}', byname[f'vr8_head_{nm}']['mat_index'], parts['skin'])
        emit(f'vr10_eyes_{nm}', m_white, parts[m_white]); emit(f'vr10_pupils_{nm}', m_dark, parts[m_dark])
        emit(f'vr10_mouth_{nm}', m_lip, parts[m_lip]); emit(f'vr10_cap_{nm}', m_cap, parts[m_cap])
        print(nm, 'warp dy', round(dy, 3))
    W.write_kn5(F, tex, mats, meshes, rootname='vf_vr6'); K.scan(F); print(rep, 'total new tris', sum(n for _, n in rep))
if __name__ == '__main__': build()
