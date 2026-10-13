"""VR11: replace every remaining byte-identical zwiss texture (66) with CC0 (ambientCG) or project-made equivalents.
Same name, size, DDS format and mip count, so UVs/materials are untouched. Recipes:
  tile   ambientCG material fitted to the texture, colour statistics (per-channel mean/std) transferred from the old
         texture so the look/brightness stays, alpha (spec/detail mask in AC's shaders) re-synthesised from the CC0
         roughness map with the old alpha's mean/std.
  nm     ambientCG NormalDX (or a normal map derived from our own new colour map) with the old map's strength.
  atlas  UV-island textures: only the 1/f-resolution colour layout of the old texture is kept (as in
         tools/build_open_textures.py), detail from an ambientCG material; cut-out alpha = the coarse layout
         thresholded and re-smoothed (shape of the islands only).
  mask   ksMultilayer masks: coarse 1/16 channel layout (no pixels of the original).
  solid  flat colour.   draw  project-drawn (PIL): signs, boards, banner, kerbs, lines, lens, grass blades,
         tree line, horizon, water normals.
Writes the new blobs into every kn5 that carries the zwiss bytes, and updates docs/assets.csv.
Usage: python tools/vr11_textures.py"""
import os, sys, io, glob, csv, json, hashlib, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K, build_open_textures as B
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); Z = ROOT + '/vf_i29_speedway/'
ORIG = '/workspace/rpotm/original/zwiss_rpotm_v0.9/zw_rpm/'
OUT = '/workspace/vr11/tex_new'; os.makedirs(OUT, exist_ok=True)
FB = '/usr/share/fonts/truetype/sand-box/google/Barlow Condensed/BarlowCondensed-ExtraBold.ttf'
rng = np.random.default_rng(1129)
CC0 = 'CC0 1.0 https://docs.ambientcg.com/license/'; PROC = 'CC0 1.0 (project-made) https://creativecommons.org/publicdomain/zero/1.0/'
T = {  # name: (recipe, ambientCG id or None, note)
 'dragroad.dds': ('atlas8', 'Asphalt015', 'drag strip asphalt'), 'rpm_cracks_01.dds': ('tile', 'Asphalt031', 'cracked pit-in asphalt'),
 'rpm_cracks_02.dds': ('tile', 'Asphalt031', 'crack detail'), 'track_cracksa.dds': ('tile', 'Concrete034', 'cracked concrete'),
 'rpm_road01.dds': ('tile', 'Asphalt012', 'track asphalt'), 'rpm_road_new.dds': ('tile', 'Asphalt015', 'pit-out asphalt'),
 'roadpit.dds': ('tile', 'Asphalt012', 'pit asphalt'), 'highway.dds': ('atlas8', 'Asphalt015', 'I-29 lanes (coarse layout)'),
 '0tarmac-detail6.dds': ('tile', 'Asphalt012', 'tarmac detail'), '001tarmac-noise.dds': ('tile', 'Asphalt031', 'tarmac noise detail'),
 '001white-line.dds': ('tile', 'Concrete031', 'white paint detail'), 'rpm_grass1.dds': ('tile', 'Grass004', 'ground grass'),
 'rpm_grass2.dds': ('tile', 'Grass001', 'berm grass'), 'rpm_adds_01.dds': ('tile', 'Asphalt031', 'tarmac patches detail'),
 'RPM_adds_02.dds': ('atlas16', 'PaintedMetal004', 'small props atlas'), 'grass_nm.dds': ('nm', 'Grass004', ''),
 '0tarmac-detail5_nm2.dds': ('nm', 'Asphalt012', ''), '001tarmac-noise_nm.dds': ('nm', 'Asphalt031', ''),
 'RPM_armco_NM.dds': ('nm_own', None, 'from new armco colour'), 'RPM_frame_01_NM.dds': ('nm_own', None, 'from new frame'),
 'drag_boot_roof_NM.dds': ('nm', 'CorrugatedSteel005', ''), 'rmblb2_NEW_NM.dds': ('nm_own', None, 'from new kerb'),
 'tower_door_NM.dds': ('nm', 'Metal046A', ''), 'rpm_road_line2_NM.dds': ('nm_flat', None, ''),
 'vesi_normalmap.dds': ('water', None, 'procedural ripples'), 'waterbump2.dds': ('water', None, 'procedural ripples'),
 'RPM_armco.dds': ('atlas8', 'Metal032', 'galvanised rail'), 'RPM_armco_BL.dds': ('atlas8', 'PaintedMetal004', 'blue rail'),
 'RPM_frame_01.dds': ('atlas8', 'Metal032', 'truss (cut-out)'), 'RPM_frame_01RED.dds': ('atlas8', 'PaintedMetal004', 'red truss (cut-out)'),
 'fence_stands.dds': ('atlas8', 'Fence006', 'fence (cut-out)'), 'fence_track.dds': ('atlas8', 'Fence006', 'fence (cut-out)'),
 'fence_outside.dds': ('atlas8', 'Fence006', 'fence (cut-out)'), 'gate_01.dds': ('atlas8', 'Fence006', 'gate (cut-out)'),
 'gate_02.dds': ('atlas8', 'Fence006', 'gate (cut-out)'), 'tentroof.dds': ('tile', 'Fabric026', 'tent roof'),
 'pittent01.dds': ('tile', 'Fabric045', 'tent fabric'), 'drag_boot_roof.dds': ('tile', 'CorrugatedSteel005', 'kiosk roof'),
 'drag_enter_wall1.dds': ('tile', 'CorrugatedSteel005', 'drag entry wall'), 'factory_w.dds': ('atlas16', 'PaintedPlaster010', 'factory wall'),
 'paddock01.dds': ('atlas8', 'PaintedPlaster017', 'paddock wall/window'), 'paddock02.dds': ('atlas8', 'PaintedPlaster017', 'paddock wall'),
 'towerpaint.dds': ('tile', 'PaintedMetal004', 'tower paint'), 'door_tower.dds': ('atlas8', 'PaintedMetal004', 'door'),
 'tower_door.dds': ('atlas8', 'Metal046A', 'roller door'), 'grass_blend.dds': ('atlas8', 'Grass004', 'track-edge blend'),
 'rpm_road_mak_nerpm_roadmask_new.dds': ('mask', None, ''), 'rpm_road_pits_mask.dds': ('mask', None, ''),
 'tarmacmask5.dds': ('mask', None, ''), 'rmbl_NEW_msk.dds': ('mask', None, ''), 'rpm_road_detail.dds': ('tile', 'Asphalt012', 'road detail'), '001tarmac_mask-2.dds': ('mask', None, ''),
 'black_1.dds': ('solid', None, ''), 'black_2.dds': ('solid', None, ''), 'green.dds': ('solid', None, ''), 'NULL.dds': ('solid', None, ''),
 'RPM_marsh_signs.dds': ('draw', None, 'marshal post numbers'), 'signs_new.dds': ('draw', None, 'distance boards'),
 'dragboard.dds': ('draw', None, 'I-29 shield + timing board'), 'logomam.dds': ('draw', None, 'START / FINISH banner (replaces Fanapryde MAM logo)'),
 'rmblb2_NEW.dds': ('draw', None, 'kerb red/white'), 'line.dds': ('draw', None, 'white line'), 'rpm_road_line2.dds': ('draw', None, 'road line'),
 'roadsf_new.dds': ('draw', None, 'start/finish checker'), 'red01.dds': ('draw', None, 'red reflector lens'),
 'rpm_grasses.dds': ('draw', None, 'grass tuft billboards'), 'rpm_treeline2.dds': ('draw', None, 'tree line silhouette'),
 'rpm_horizon.dds': ('draw', None, 'horizon silhouette'),
}
def stats_match(img, ref):
    img = img.astype(np.float32); ref = ref.astype(np.float32); o = np.empty_like(img)
    for c in range(3):
        s = img[..., c].std() + 1e-3; o[..., c] = (img[..., c] - img[..., c].mean()) / s * ref[..., c].std() + ref[..., c].mean()
    return np.clip(o, 0, 255).astype(np.uint8)
def rough(id_, w, h):
    try: r = B.cc(id_, 'Roughness').mean(2)
    except Exception: r = B.noise(w, h) * 255
    return B.fit(np.dstack([r] * 3).astype(np.uint8), w, h)[..., 0].astype(np.float32)
def synth_alpha(oa, w, h, id_):
    m, s = float(oa.mean()), float(oa.std())
    if s < 2: return np.full((h, w), int(round(m)), np.uint8)
    r = rough(id_ or 'Asphalt012', w, h); r = (r - r.mean()) / (r.std() + 1e-3)
    return np.clip(m + r * s, 0, 255).astype(np.uint8)
def is_cutout(oa): return (oa < 16).mean() > 0.05 and (oa > 240).mean() > 0.05
def nm_strength(o):
    xy = o[..., :2].astype(np.float32) - 128; return float(np.sqrt((xy ** 2).mean()) + 1e-3)
def scale_nm(n, target):
    xy = n[..., :2].astype(np.float32) - 128; cur = np.sqrt((xy ** 2).mean()) + 1e-3; xy *= target / cur
    zc = np.sqrt(np.clip(127.0 ** 2 - (xy ** 2).sum(2), 0, None))
    return np.clip(np.dstack([xy + 128, zc + 128]), 0, 255).astype(np.uint8)
def font(sz): return ImageFont.truetype(FB, sz)
def draw(name, w, h, o):
    a = None
    if name == 'RPM_marsh_signs.dds':
        im = Image.new('RGB', (w, h), (214, 200, 160)); d = ImageDraw.Draw(im); nums = ['2', '4', '5', '7', '9', '11', '12', '14']; cw = w / 9
        for i, t in enumerate(nums): d.text((cw * (i + 0.5), h * 0.5), t, font=font(int(h * 0.8)), fill=(30, 28, 26), anchor='mm')
        d.rectangle([w - cw * 0.9, h * 0.1, w - cw * 0.1, h * 0.9], fill=(20, 20, 20)); rgb = np.array(im)
    elif name == 'signs_new.dds':
        im = Image.new('RGB', (w, h), (222, 222, 216)); d = ImageDraw.Draw(im)
        for i, t in enumerate('12345'): d.text((w * (0.12 + i * 0.17), h * 0.16), t, font=font(int(h * 0.26)), fill=(150, 40, 30), anchor='mm')
        d.text((w * 0.5, h * 0.62), '50', font=font(int(h * 0.4)), fill=(150, 40, 30), anchor='mm'); rgb = np.array(im)
    elif name == 'dragboard.dds':
        im = Image.new('RGB', (w, h), (0, 0, 0)); d = ImageDraw.Draw(im); r = h * 0.22; cx, cy = r + 6, h * 0.28
        d.polygon([(cx - r, cy - r * 0.8), (cx + r, cy - r * 0.8), (cx + r * 0.95, cy + r * 0.3), (cx, cy + r), (cx - r * 0.95, cy + r * 0.3)], fill=(20, 60, 160), outline=(255, 255, 255), width=4)
        d.rectangle([cx - r, cy - r * 0.8, cx + r, cy - r * 0.45], fill=(200, 30, 30)); d.text((cx, cy + r * 0.15), '29', font=font(int(r * 1.0)), fill=(255, 255, 255), anchor='mm')
        d.text((cx, cy - r * 0.62), 'I-29', font=font(int(r * 0.32)), fill=(255, 255, 255), anchor='mm')
        for row, t in enumerate(('7.842', '93.17')): d.text((w * 0.19, h * (0.06 + row * 0.24)), t, font=font(int(h * 0.2)), fill=(255, 40, 30), anchor='lt')
        d.rectangle([w * 0.19, h * 0.52, w * 0.3, h * 0.6], fill=(20, 40, 200)); rgb = np.array(im)
        a = np.full((h, w), 255, np.uint8)
    elif name == 'logomam.dds':
        im = Image.new('RGB', (w, h), (25, 25, 25)); d = ImageDraw.Draw(im)
        d.text((w * 0.17, h * 0.5), 'START', font=font(int(h * 0.62)), fill=(245, 245, 245), anchor='mm')
        d.text((w * 0.83, h * 0.5), 'FINISH', font=font(int(h * 0.62)), fill=(245, 245, 245), anchor='mm')
        d.rectangle([w * 0.37, h * 0.15, w * 0.63, h * 0.85], fill=(245, 245, 245)); d.text((w * 0.5, h * 0.5), 'I-29', font=font(int(h * 0.62)), fill=(25, 25, 25), anchor='mm'); rgb = np.array(im)
    elif name == 'rmblb2_NEW.dds':
        rgb = np.zeros((h, w, 3), np.uint8); rgb[: h // 2] = (236, 236, 232); rgb[h // 2:] = (176, 30, 28)
        n = (B.noise(w, h, 16) * 24 - 12)[..., None]; rgb = np.clip(rgb + n, 0, 255).astype(np.uint8)
    elif name in ('line.dds', 'rpm_road_line2.dds'):
        x = np.linspace(-1, 1, w); prof = np.clip((0.75 - np.abs(x)) * 6, 0, 1)
        rgb = np.full((h, w, 3), 236, np.uint8); rgb = np.clip(rgb - (B.noise(w, h, 8) * 30)[..., None], 0, 255).astype(np.uint8)
        a = (np.tile(prof, (h, 1)) * float(o[..., 3].max())).astype(np.uint8)
    elif name == 'roadsf_new.dds':
        q = h // 2; yy, xx = np.mgrid[0:h, 0:w]; c = ((xx // q + yy // q) % 2).astype(bool)
        rgb = np.where(c[..., None], 232, 22).astype(np.uint8).repeat(3, 2) if False else np.where(c[..., None], np.uint8(232), np.uint8(22)) * np.ones((1, 1, 3), np.uint8)
    elif name == 'red01.dds':
        yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot(xx - w / 2, yy - h / 2) / (w / 2)
        ring = (np.sin(r * 40) * 0.5 + 0.5) * 0.25; base = np.clip(1.0 - r, 0, 1)
        rgb = np.dstack([140 + 100 * base + 40 * ring, 10 + 30 * ring, 15 + 30 * ring]).clip(0, 255).astype(np.uint8); rgb[r > 0.98] = (60, 60, 60); a = np.clip((1.0 - r) * 60, 0, 1) * 255; a = a.astype(np.uint8)
    elif name == 'rpm_grasses.dds':
        im = Image.new('RGBA', (w, h), (60, 80, 30, 0)); d = ImageDraw.Draw(im)
        for cx in (w * 0.25, w * 0.75):
            for _ in range(140):
                x0 = cx + rng.normal(0, w * 0.06); top = h * rng.uniform(0.05, 0.6); lean = rng.normal(0, w * 0.05); g = int(rng.uniform(70, 140))
                d.polygon([(x0 - 3, h), (x0 + 3, h), (x0 + lean, top)], fill=(int(g * 0.55), g, int(g * 0.3), 255))
        arr = np.array(im); rgb, a = arr[..., :3], arr[..., 3]
    elif name in ('rpm_treeline2.dds', 'rpm_horizon.dds'):
        x = np.arange(w); top = np.zeros(w)
        for k, amp in ((7, 0.10), (23, 0.07), (61, 0.05), (151, 0.03), (409, 0.02)): top += amp * np.interp(x, np.linspace(0, w, k + 1), rng.random(k + 1))
        lo = 0.15 if name == 'rpm_treeline2.dds' else 0.55
        top = (lo + top / top.max() * (0.85 - lo)) * h if name == 'rpm_treeline2.dds' else (lo + top * 0.6) * h
        yy = np.arange(h)[:, None]; a = np.clip((yy - top[None, :]) * 0.8 + 1, 0, 1); a = (cv2.GaussianBlur(a.astype(np.float32), (3, 3), 0) * 255).astype(np.uint8)
        leaf = B.fit(B.cc('Grass004'), w, h).astype(np.float32); depth = np.clip((yy - top[None, :]) / (h * 0.5), 0, 1)[..., None]
        tint = np.array([52, 70, 40], np.float32) if name == 'rpm_treeline2.dds' else np.array([92, 104, 110], np.float32)
        rgb = np.clip(tint * (0.7 + 0.6 * leaf / leaf.mean()) * (1 - 0.35 * depth), 0, 255).astype(np.uint8)
        if name == 'rpm_horizon.dds': rgb = stats_match(rgb, o[..., :3][o[..., 3] > 128] .reshape(-1, 1, 3)) if (o[..., 3] > 128).any() else rgb
    else: raise KeyError(name)
    return rgb, a
def build(name, o):
    h, w = o.shape[:2]; rec, src, note = T[name]; oa = o[..., 3]; a = None
    if rec == 'tile':
        rgb = stats_match(B.fit(B.cc(src), w, h), o[..., :3]); s = 'ambientCG ' + src; lic = CC0
    elif rec == 'nm':
        rgb = scale_nm(B.fit(B.cc(src, 'NormalDX'), w, h), nm_strength(o)); s = 'ambientCG %s NormalDX' % src; lic = CC0
    elif rec in ('atlas8', 'atlas16'):
        f = 8 if rec == 'atlas8' else 16; rgb = B.atlas(o, w, h, B.cc(src), f); s = 'ambientCG %s + 1/%d colour layout' % (src, f); lic = CC0
        if is_cutout(oa):
            ca = B.coarse_alpha(oa, w, h, f // 2); a = (cv2.GaussianBlur(((ca > 127) * 255).astype(np.uint8), (3, 3), 0))
    elif rec == 'mask':
        rgb = B.coarse(o[..., :3].astype(np.float32), w, h, 16).astype(np.uint8); a = B.coarse_alpha(oa, w, h, 16).astype(np.uint8); s = 'project-made (1/16 channel layout)'; lic = PROC
    elif rec == 'solid':
        c = o.reshape(-1, 4).mean(0); rgb = np.full((h, w, 3), c[:3], np.uint8); a = np.full((h, w), int(c[3]), np.uint8); s = 'project-made solid'; lic = PROC
    elif rec == 'water':
        hgt = sum(B.noise(w, h, sc, 3) * wt for sc, wt in ((64, 1.0), (16, 0.5), (6, 0.25))); rgb = scale_nm(B.h2n(hgt * 255, 0.03), nm_strength(o)); s = 'project-made procedural'; lic = PROC
    elif rec == 'nm_flat':
        rgb = np.dstack([np.full((h, w), 128), np.full((h, w), 128), np.full((h, w), 255)]).astype(np.uint8); s = 'project-made flat normal'; lic = PROC
    elif rec == 'nm_own':
        base = {'RPM_armco_NM.dds': 'RPM_armco.dds', 'RPM_frame_01_NM.dds': 'RPM_frame_01.dds', 'rmblb2_NEW_NM.dds': 'rmblb2_NEW.dds'}[name]
        lum = cv2.resize(NEW_RGB[base].mean(2).astype(np.float32), (w, h)); rgb = scale_nm(B.h2n(lum, 0.05), nm_strength(o)); s = 'project-made (from new %s)' % base; lic = PROC
    elif rec == 'draw':
        rgb, a = draw(name, w, h, o); s = 'project-made (drawn)'; lic = PROC
    if a is None:
        a = cv2.resize(oa, (w, h)) if (is_cutout(oa) and rec != 'tile') else synth_alpha(oa, w, h, src)
        if is_cutout(oa) and rec in ('nm', 'nm_own', 'tile'): a = synth_alpha(oa, w, h, src) if not is_cutout(oa) else B.coarse_alpha(oa, w, h, 4).astype(np.uint8)
    return np.dstack([rgb[..., :3], a]).astype(np.uint8), s, lic, note
NEW_RGB = {}
def main():
    zh = {}
    for f in glob.glob(ORIG + '*.kn5'):
        d = open(f, 'rb').read(); tex, _ = K.scan(f)
        for n, so, sz in tex: zh[hashlib.md5(d[so + 4:so + 4 + sz]).hexdigest()] = n
    found = {}
    for fn in sorted(glob.glob(Z + '*.kn5')):
        d = open(fn, 'rb').read(); tex, _ = K.scan(fn)
        for n, so, sz in tex:
            if hashlib.md5(d[so + 4:so + 4 + sz]).hexdigest() in zh: found.setdefault(n, []).append(fn); found[n + '#blob'] = d[so + 4:so + 4 + sz]
    names = sorted(k for k in found if not k.endswith('#blob')); missing = [n for n in names if n not in T]; assert not missing, missing
    order = sorted(names, key=lambda n: T[n][0] == 'nm_own'); blobs = {}; meta = {}
    for n in order:
        b = found[n + '#blob']; w, h, mm, fmt = B.info(b); o = np.array(Image.open(io.BytesIO(b)).convert('RGBA'))
        rgba, s, lic, note = build(n, o); NEW_RGB[n] = rgba[..., :3]
        mips = 1 if mm == 1 else int(math.log2(max(w, h))) + 1
        blobs[n] = B.write_dds(rgba, fmt, mips, b[:128]); Image.fromarray(rgba).save(f'{OUT}/{n}.png')
        meta[n] = dict(src=s, lic=lic, note=note, fmt=f'{w}x{h} {fmt} mips{mips}', files=[os.path.basename(x) for x in found[n]])
        print(n, T[n][0], s)
    for fn in sorted({f for n in names for f in found[n]}):
        rep = {n: blobs[n] for n in names if fn in found[n]}; K.patch(fn, fn + '.tmp', texrep=rep); os.replace(fn + '.tmp', fn); K.scan(fn)
    rows = list(csv.DictReader(open(ROOT + '/docs/assets.csv'))); flds = rows[0].keys()
    for r in rows:
        if r['texture'] in meta and r['file'] in meta[r['texture']]['files']:
            m = meta[r['texture']]; r.update(likely_origin='replaced', license_risk='low', replacement_plan='DONE VR11: ' + (m['note'] or T[r['texture']][0]), source=m['src'], license_url=m['lic'], new_format=m['fmt'])
    w_ = csv.DictWriter(open(ROOT + '/docs/assets.csv', 'w', newline=''), fieldnames=list(flds)); w_.writeheader(); w_.writerows(rows)
    json.dump(meta, open('/workspace/vr11/tex_meta.json', 'w'), indent=1); print('replaced', len(names))
if __name__ == '__main__': main()
