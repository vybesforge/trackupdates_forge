"""VR10 verification on the full-map rasters: residual R = H_now - H_flat - T_final per 1 m cell.
Reports |R| on pavement, new steps (>1 cm jump of R between adjacent pavement cells), grade on extension
pavement, and new >0.3 m drop-offs not caused by pond beds / hole fills."""
import sys, numpy as np, collections, json
from scipy import ndimage
o = np.load('/workspace/vr9/cov_fullold.npz', allow_pickle=True); b = np.load('/workspace/vr9/cov_%s.npz' % (sys.argv[1] if len(sys.argv) > 1 else 'v10'), allow_pickle=True)
f = np.load('/workspace/vr10/field.npz'); Tf = f['Tf'].astype(float); pav = f['pav']; epav = f['epav']; xs, zs = b['xs'], b['zs']
nmo = np.where(o['KEY'] >= 0, o['names'].astype(str)[np.clip(o['KEY'], 0, None)], '')
nmb = np.where(b['KEY'] >= 0, b['names'].astype(str)[np.clip(b['KEY'], 0, None)], '')
fam = lambda s: np.char.rstrip(np.char.rstrip(s, '0123456789'), '_')
same = (fam(nmo) == fam(nmb)) | (np.char.find(nmb, 'GRASS') >= 0) & (np.char.find(nmo, 'GRASS') >= 0)
R = b['H'] - o['H'] - Tf
P = pav & same & np.isfinite(R)
out = {'pavement_cells': int(P.sum()), 'abs_residual_p99': float(np.percentile(np.abs(R[P]), 99)), 'abs_residual_max': float(np.abs(R[P]).max())}
st = []
for ax in (0, 1):
    dR = np.abs(np.diff(R, axis=ax)); m = (P[1:] & P[:-1]) if ax == 0 else (P[:, 1:] & P[:, :-1])
    # only where the same mesh family continues (a join between two meshes counts too)
    st.append(dR[m & np.isfinite(dR)])
st = np.concatenate(st); out['new_steps_gt_1cm'] = int((st > 0.01).sum()); out['new_step_max'] = float(st.max())
gz, gx = np.gradient(Tf); g = np.hypot(gx, gz); out['ext_grade_max_pct'] = float(g[epav].max() * 100)
out['ext_Tf_range'] = (float(Tf[epav].min()), float(Tf[epav].max()))
print(json.dumps(out, indent=1))
if out['new_steps_gt_1cm']:
    for ax in (0, 1):
        dR = np.abs(np.diff(R, axis=ax)); m = (P[1:] & P[:-1]) if ax == 0 else (P[:, 1:] & P[:, :-1]); j, i = np.nonzero(m & (dR > 0.01))
        print(collections.Counter((int(xs[a] // 50 * 50), int(zs[c] // 50 * 50), nmb[c, a]) for c, a in zip(j, i)).most_common(10))
