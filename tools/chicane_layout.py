"""Long Course Chicane layout.

Clones `main` into layout id `chicane` and adds two track-day cone chicanes on the
west double-straight, where Dylan marked them on the Content Manager outline.

Mark registration (screenshot 347x194, outline.png 365x192):
  outline px = z * 0.293033 + 323.344
  outline py = -x * 0.293033 + 87.117
  shot px = outline_px * 0.97 - 3.1
  shot py = outline_py * 0.97 + 5.1
The two orange-red ticks (RGB 255,85,0) sit on the white straights at shot x≈139:
  main/drag straight (southbound)  world (-230.07, -601.75)
  return straight (northbound)     world (-112.92, -602.81)
Driver's left is the AC left normal (tz, -tx). The main chicane enters to the
driver's right and exits to the left. The return enters to the driver's left
and exits to the right. Soft cut is an invisible 1SCUT_* ribbon (KEY=SCUT)
over the shortcut; cones are visual only.

Both chicanes keep their tightened 22 m gates and the same edge-margin weave
(main right-then-left, return left-then-right). Their stations meet at the
midpoint of the previous pair (main z −582.17 and return z −510.86), so the
two features sit across the double straight. On this southbound straight,
"back" is upstream, which is north (+Z); that is the direction the main
station moves. The return station moves south to the same z.

Each exit gate keeps the outer cone (the one PR #5 removed, farthest from
the racing line) and instead drops the cone closest to the exit opening.

Run from the repo root: python3 tools/chicane_layout.py
"""
import io, os, re, shutil, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import kn5patch as K
import kn5write as W
import vr5_meshlib as ML
import vr7_common as C

Z = os.path.join(ROOT, 'vf_i29_speedway') + os.sep
LAY = 'chicane'
# Original symmetric gates, metres along the spline from the station.
# Positive = downstream. BLEND is how far the line eases back to centre
# outside each gate (the old FAR − GATE).
GATE = 14.0
BLEND = 22.0
FAR = GATE + BLEND
HW = 1.90          # valid-channel half-width in the core (m)
WHEEL = 0.90       # half the width that must stay on ROAD / on SCUT
EDGE = 1.25        # keep the AI line at least this far from the asphalt edge
MU, G, VMAX, BRK = 1.55, 9.81, 72.0, 11.0
MAIN_MARK = np.array([-230.07, -601.75])
RETURN_MARK = np.array([-112.92, -602.81])
# Designed lateral offsets (metres, driver's left positive).
# clamp_off holds the line EDGE metres inside the asphalt, so a large design
# value lands 1.25 m off that edge. Main enters on the wide right side
# (design −12 → about −8.8) and exits on the narrow left side (design +12 →
# about +0.7). Return enters on its wide left side and exits on the right.
# s_exit on main is 6 m closer to the entrance than the original +GATE.
# Return gates are symmetric about the station place_return() sets.
RETURN_SPAN = 8.0 - (-GATE)          # 22 m, same as the main gates
RETURN_HALF = RETURN_SPAN / 2.0
RETURN_BIAS = 8.0                    # metres from halfway toward the short-course rejoin
# Southbound travel is −Z, so upstream (back toward the corner that feeds
# the straight, north, more positive z) is a negative along-track shift.
# MAIN_PREV_ALONG is the PR #5 station (20 m upstream of the screenshot mark).
# main() replaces both `along` values with the shared midpoint station.
MAIN_PREV_ALONG = -20.0
PLAN = {
    'main': dict(mark=MAIN_MARK, enter=-12.0, exit=12.0, mesh='1SCUT_chicane_main',
                 s_enter=-GATE, s_exit=8.0, along=MAIN_PREV_ALONG),
    'return': dict(mark=RETURN_MARK, enter=12.0, exit=-4.0, mesh='1SCUT_chicane_return',
                   s_enter=-RETURN_HALF, s_exit=RETURN_HALF),
}


def smoother(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def path_offset(s, spec):
    """Lateral offset. The core runs from s_enter to s_exit; each side blends over BLEND."""
    se, sx = spec['s_enter'], spec['s_exit']
    enter, exit = spec['enter'], spec['exit']
    s = float(s)
    if s <= se - BLEND or s >= sx + BLEND:
        return 0.0
    if s < se:
        return enter * smoother((s - (se - BLEND)) / BLEND)
    if s < sx:
        span = sx - se
        return enter + (exit - enter) * smoother((s - se) / span)
    return exit + (0.0 - exit) * smoother((s - sx) / BLEND)


def clamp_off(off, le, re):
    """Stay on asphalt. The return straight narrows on the entrance side."""
    if le is None or re is None or le - re < 2 * EDGE + 0.5:
        return off
    return float(np.clip(off, re + EDGE, le - EDGE))


def channel_half(s, spec):
    """Core width through the gates, flaring out to full road by the end of each blend."""
    se, sx = spec['s_enter'], spec['s_exit']
    s = float(s)
    if s < se:
        a = se - s
    elif s > sx:
        a = s - sx
    else:
        a = 0.0
    if a <= 4.0:
        return HW
    if a >= BLEND:
        return 80.0
    return HW + (40.0 - HW) * smoother((a - 4.0) / (BLEND - 4.0))


def load_roads():
    p = Z + 'vf_i29_speedway_physical.kn5'
    d = open(p, 'rb').read()
    tris = []
    for nm, o, l, c in K.scan(p)[1]:
        if c != 2 or not nm.startswith('1ROAD'):
            continue
        q = o + l + 8
        nv, = struct.unpack_from('<I', d, q)
        V = np.frombuffer(d, '<f4', nv * 11, q + 4).reshape(nv, 11)[:, :3]
        q2 = q + 4 + nv * 44
        ni, = struct.unpack_from('<I', d, q2)
        I = np.frombuffer(d, '<u2', ni, q2 + 4).reshape(-1, 3)
        P = V[I]
        tris.append((P[:, :, [0, 2]].astype(np.float64), P[:, :, 1].astype(np.float64)))
    XZ = np.concatenate([t[0] for t in tris])
    Y = np.concatenate([t[1] for t in tris])
    mn = XZ.min(1)
    mx = XZ.max(1)
    return XZ, Y, mn, mx


def height_at(x, z, XZ, Y, mn, mx):
    m = (mn[:, 0] <= x) & (mx[:, 0] >= x) & (mn[:, 1] <= z) & (mx[:, 1] >= z)
    best = None
    for tri, yv in zip(XZ[m], Y[m]):
        p0, p1, p2 = tri
        v0, v1 = p1 - p0, p2 - p0
        v2 = np.array([x, z]) - p0
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        a = (v2[0] * v1[1] - v1[0] * v2[1]) / den
        b = (v0[0] * v2[1] - v2[0] * v0[1]) / den
        if a >= -1e-3 and b >= -1e-3 and a + b <= 1.001:
            y = (1 - a - b) * yv[0] + a * yv[1] + b * yv[2]
            best = y if best is None else max(best, y)
    return best


def edges_at(origin, left, XZ, Y, mn, mx, reach=14.0, step=0.15):
    """Outermost continuous road, metres along `left` (positive = driver's left)."""
    def walk(sign):
        off, gap, edge, hy = 0.0, 0.0, None, None
        while off < reach:
            off += step
            q = origin + sign * off * left
            h = height_at(q[0], q[1], XZ, Y, mn, mx)
            if h is None:
                gap += step
                if edge is not None and gap > 0.75:
                    break
            else:
                gap = 0.0
                edge = sign * off
                hy = h
        return edge, hy
    le, _ = walk(+1)
    re, _ = walk(-1)
    return le, re


def local_polyline(xz, anchor, reach):
    """Indices and signed arc from anchor, walking both ways up to `reach` metres."""
    n = len(xz)
    back, fwd = [anchor], [anchor]
    acc = 0.0
    i = anchor
    while acc < reach:
        j = (i - 1) % n
        acc += np.linalg.norm(xz[i] - xz[j])
        back.append(j)
        i = j
    acc = 0.0
    i = anchor
    while acc < reach:
        j = (i + 1) % n
        acc += np.linalg.norm(xz[j] - xz[i])
        fwd.append(j)
        i = j
    idxs = list(reversed(back[1:])) + fwd
    s = np.zeros(len(idxs))
    for k in range(1, len(idxs)):
        step = np.linalg.norm(xz[idxs[k]] - xz[idxs[k - 1]])
        s[k] = s[k - 1] + step
    s -= s[idxs.index(anchor)]
    return np.array(idxs), s


def tangent_left(xz, idxs):
    n = len(xz)
    out = np.zeros((len(idxs), 2))
    for k, i in enumerate(idxs):
        t = xz[(i + 6) % n] - xz[(i - 6) % n]
        t = t / np.linalg.norm(t)
        out[k] = (t[1], -t[0])
    # keep the normal continuous (no flips)
    for k in range(1, len(out)):
        if np.dot(out[k], out[k - 1]) < 0:
            out[k] *= -1
    return out


def sample_at(xz, idxs, s, left, query):
    """Interpolate origin + left at signed arc `query`."""
    k = int(np.clip(np.searchsorted(s, query), 1, len(s) - 1))
    span = s[k] - s[k - 1]
    f = 0.0 if span < 1e-9 else (query - s[k - 1]) / span
    o = (1 - f) * xz[idxs[k - 1]] + f * xz[idxs[k]]
    nrm = (1 - f) * left[k - 1] + f * left[k]
    nrm = nrm / np.linalg.norm(nrm)
    return o, nrm


def place_return(xz):
    """Put the return-chicane centre between the feeding corner and the short rejoin.

    The corner landmark is where that sweeper has finished and the northbound
    return straight has begun (heading nearly +Z, curvature gone). The short
    landmark is where `short/ai/fast_lane.ai` rejoins this line and stays on it.
    `along` is signed arc from the screenshot mark, positive downstream.
    """
    from scipy.spatial import cKDTree
    short = C.read_ai(Z + 'short/ai/fast_lane.ai')['P']['p'].astype(np.float64)[:, [0, 2]]
    dshort, _ = cKDTree(short).query(xz)
    hd_t = np.roll(xz, -4, 0) - np.roll(xz, 4, 0)
    hd = hd_t / np.maximum(np.linalg.norm(hd_t, axis=1), 1e-9)[:, None]
    kap = _curvature(xz, k=6)
    seg = np.linalg.norm(np.diff(np.vstack([xz, xz[:1]]), axis=0), axis=1)
    arc = np.r_[0.0, np.cumsum(seg)]
    n = len(xz)

    def step(i, direction):
        j = (i + direction) % n
        return j, float(np.linalg.norm(xz[j] - xz[i]))

    onset = None
    for i in range(n):
        if xz[i, 0] > -90 or not (-780 < xz[i, 1] < -250):
            continue
        if hd[i, 1] < 0.98 or abs(kap[i]) > 0.003:
            continue
        acc, j, ok = 0.0, i, True
        while acc < 20.0:
            j, ds = step(j, +1)
            acc += ds
            if hd[j, 1] < 0.97:
                ok = False
                break
        if ok:
            onset = i
            break
    if onset is None:
        raise SystemExit('return straight onset not found')

    rejoin = None
    i, acc = onset, 0.0
    while acc < 700.0:
        i, ds = step(i, +1)
        acc += ds
        if dshort[i] >= 2.0:
            continue
        acc2, j, ok = 0.0, i, True
        while acc2 < 30.0:
            j, ds2 = step(j, +1)
            acc2 += ds2
            if dshort[j] > 3.0:
                ok = False
                break
        if ok:
            rejoin = i
            break
    if rejoin is None:
        raise SystemExit('short-course rejoin not found on the return straight')

    a0, a1 = float(arc[onset]), float(arc[rejoin])
    if a1 <= a0:
        raise SystemExit('short-course rejoin is not downstream of the return straight')
    halfway = 0.5 * (a0 + a1)
    target = float(np.clip(halfway + RETURN_BIAS, a0 + 40.0, a1 - 40.0))
    mark_i = int(np.argmin(np.hypot(xz[:, 0] - RETURN_MARK[0], xz[:, 1] - RETURN_MARK[1])))
    along = target - float(arc[mark_i])

    def at_arc(a):
        i = int(np.clip(np.searchsorted(arc[:-1], a, side='right') - 1, 0, n - 2))
        span = arc[i + 1] - arc[i]
        f = 0.0 if span < 1e-9 else (a - arc[i]) / span
        return (1 - f) * xz[i] + f * xz[i + 1]

    old_along = -20.0  # previous layout: 20 m south of the screenshot mark
    info = dict(
        along=along, old_along=old_along,
        onset_i=int(onset), onset_z=float(xz[onset, 1]), onset_xz=xz[onset].copy(),
        rejoin_i=int(rejoin), rejoin_z=float(xz[rejoin, 1]), rejoin_xz=xz[rejoin].copy(),
        onset_arc=a0, rejoin_arc=a1, halfway_arc=halfway, target_arc=target,
        from_onset=target - a0, from_rejoin=a1 - target,
        mark_i=mark_i, mark_z=float(xz[mark_i, 1]), mark_arc=float(arc[mark_i]),
        new_z=float(at_arc(target)[1]), old_z=float(at_arc(float(arc[mark_i]) + old_along)[1]),
        moved_from_old=along - old_along,
    )
    print('return placement:')
    print(f'  straight onset idx {onset} z {info["onset_z"]:.2f}  '
          f'(corner has fed onto the return straight)')
    print(f'  short rejoin   idx {rejoin} z {info["rejoin_z"]:.2f}  '
          f'(short fast_lane within 2 m)')
    print(f'  halfway arc {halfway - a0:.1f} m from onset, '
          f'biased {RETURN_BIAS:.0f} m toward the rejoin')
    print(f'  centre is {info["from_onset"]:.1f} m downstream of the onset, '
          f'{info["from_rejoin"]:.1f} m upstream of the rejoin')
    print(f'  z {info["old_z"]:.2f} (previous, 20 m south of the mark) -> {info["new_z"]:.2f}  '
          f'spline {info["moved_from_old"]:+.1f} m')
    return info


def station_origin(xz, mark, along):
    """World XZ of the s=0 station `along` metres from `mark`."""
    anchor0 = int(np.argmin(np.hypot(xz[:, 0] - mark[0], xz[:, 1] - mark[1])))
    idxs, s = local_polyline(xz, anchor0, FAR + 80 + abs(along))
    left = tangent_left(xz, idxs)
    return sample_at(xz, idxs, s, left, along)[0]


def along_for_z(xz, mark, target_z, hint):
    """Signed arc from `mark` whose station z equals `target_z`, nearest `hint`."""
    anchor0 = int(np.argmin(np.hypot(xz[:, 0] - mark[0], xz[:, 1] - mark[1])))
    idxs, s = local_polyline(xz, anchor0, 250.0)
    pts = xz[idxs]
    best = None
    for i in range(1, len(s)):
        z0, z1 = float(pts[i - 1, 1]), float(pts[i, 1])
        if (z0 - target_z) * (z1 - target_z) > 0:
            continue
        dz = z1 - z0
        if abs(dz) < 1e-6:
            continue
        f = (target_z - z0) / dz
        if not (0.0 <= f <= 1.0):
            continue
        along = float(s[i - 1] + f * (s[i] - s[i - 1]))
        err = abs(along - hint)
        if best is None or err < best[0]:
            best = (err, along)
    if best is None:
        raise SystemExit(f'no spline point at z {target_z:.2f} near {mark}')
    return best[1]


def align_stations(xz, info):
    """Park both chicane stations on the midpoint of the PR #5 stations.

    Prior "back" on the southbound main straight is upstream, which is north
    (+Z, a more negative `along`). The return straight travels north, so the
    matching move toward the main is south (a smaller positive `along`).
    """
    prev_main_z = float(station_origin(xz, MAIN_MARK, MAIN_PREV_ALONG)[1])
    prev_ret_z = float(info['new_z'])
    shared_z = 0.5 * (prev_main_z + prev_ret_z)
    main_along = along_for_z(xz, MAIN_MARK, shared_z, MAIN_PREV_ALONG)
    ret_along = along_for_z(xz, RETURN_MARK, shared_z, info['along'])
    main_z = float(station_origin(xz, MAIN_MARK, main_along)[1])
    ret_z = float(station_origin(xz, RETURN_MARK, ret_along)[1])
    if abs(main_z - shared_z) > 0.05 or abs(ret_z - shared_z) > 0.05:
        raise SystemExit(f'stations missed the shared z {shared_z:.2f} '
                         f'(main {main_z:.2f}, return {ret_z:.2f})')
    info['prev_along'] = info['along']
    info['prev_z'] = prev_ret_z
    info['along'] = ret_along
    info['new_z'] = ret_z
    info['shared_z'] = shared_z
    info['main_prev_z'] = prev_main_z
    info['main_prev_along'] = MAIN_PREV_ALONG
    info['main_along'] = main_along
    info['main_z'] = main_z
    target = info['mark_arc'] + ret_along
    info['from_onset'] = target - info['onset_arc']
    info['from_rejoin'] = info['rejoin_arc'] - target
    info['moved_from_prev'] = ret_along - info['prev_along']
    print('shared station:')
    print(f'  midpoint of z {prev_main_z:.2f} and z {prev_ret_z:.2f}  ->  z {shared_z:.2f}')
    print(f'  main   along {MAIN_PREV_ALONG:+.2f} -> {main_along:+.2f}  '
          f'Δz {main_z - prev_main_z:+.2f} m  (upstream / north, prior "back")')
    print(f'  return along {info["prev_along"]:+.2f} -> {ret_along:+.2f}  '
          f'Δz {ret_z - prev_ret_z:+.2f} m  (south, toward the main)')
    PLAN['main']['along'] = main_along
    PLAN['return']['along'] = ret_along
    PLAN['return']['place_info'] = info
    return info


def build_zone(name, spec, xz, XZ, Y, mn, mx):
    anchor0 = int(np.argmin(np.hypot(xz[:, 0] - spec['mark'][0], xz[:, 1] - spec['mark'][1])))
    dist = np.hypot(*(xz[anchor0] - spec['mark']))
    along = float(spec.get('along', 0.0))
    idxs, s = local_polyline(xz, anchor0, FAR + 30 + abs(along))
    left = tangent_left(xz, idxs)
    shift = dict(arc=0.0, dz=0.0, z0=float(xz[anchor0][1]), z1=float(xz[anchor0][1]), origin_s=0.0,
                 info=spec.get('place_info'))
    if abs(along) > 0.01:
        if along < s.min() + 1 or along > s.max() - 1:
            raise SystemExit(f'{name}: polyline does not reach the new station (along {along:+.1f}, '
                             f's {s.min():.1f}..{s.max():.1f})')
        o_new = sample_at(xz, idxs, s, left, along)[0]
        z0 = float(sample_at(xz, idxs, s, left, 0.0)[0][1])
        s = s - along
        shift = dict(arc=along, dz=float(o_new[1] - z0), z0=z0, z1=float(o_new[1]),
                     origin_s=along, info=spec.get('place_info'))
        if s.min() > -FAR - 1 or s.max() < FAR + 1:
            raise SystemExit(f'{name}: polyline does not cover the shifted station '
                             f'({s.min():.1f}..{s.max():.1f})')
    anchor = int(idxs[int(np.argmin(np.abs(s)))])
    # edges at the AI samples (cached)
    edge = {}
    for i, k in enumerate(idxs):
        if abs(s[i]) > FAR + 8:
            continue
        edge[int(k)] = edges_at(xz[k], left[i], XZ, Y, mn, mx)
    stations = np.arange(-FAR, FAR + 1e-6, 1.0)
    rows = []
    for q in stations:
        o, nrm = sample_at(xz, idxs, s, left, q)
        # edges from the nearest cached sample, walked from the interpolated origin
        le, re = edges_at(o, nrm, XZ, Y, mn, mx)
        hy = height_at(o[0], o[1], XZ, Y, mn, mx)
        off = clamp_off(path_offset(q, spec), le, re)
        rows.append(dict(s=q, o=o, n=nrm, le=le, re=re, y=hy, off=off, hw=channel_half(q, spec)))
    span = spec['s_exit'] - spec['s_enter']
    print(f'{name}: mark idx {anchor0} at {xz[anchor0]}  mark miss {dist:.2f} m  '
          f'station idx {anchor} at {xz[anchor]}')
    if abs(along) > 0.01:
        print(f'  station {shift["arc"]:+.2f} m along the spline from the mark  '
              f'Δz {shift["dz"]:+.2f} m  z {shift["z0"]:.2f} -> {shift["z1"]:.2f}')
    le0 = min(rows, key=lambda r: abs(r['s']))
    print(f'  edges at station  left {le0["le"]:.2f}  right {le0["re"]:.2f}  road y {le0["y"]:.3f}')
    print(f'  gates {spec["s_enter"]:+.1f} .. {spec["s_exit"]:+.1f}  spacing {span:.1f} m  '
          f'shortened {2 * GATE - span:.1f} m')
    print(f'  offset enter {path_offset(spec["s_enter"], spec):+.2f}  '
          f'mid {path_offset(0.5 * (spec["s_enter"] + spec["s_exit"]), spec):+.2f}  '
          f'exit {path_offset(spec["s_exit"], spec):+.2f}')
    return dict(name=name, spec=spec, anchor=anchor, anchor0=anchor0, idxs=idxs, s=s,
                left=left, edge=edge, rows=rows, shift=shift, spacing=span)


def on_road_lat(row, lat):
    if row['le'] is None or row['re'] is None or row['y'] is None:
        return False
    return row['re'] + 0.05 <= lat <= row['le'] - 0.05


def scut_intervals(row):
    """Lateral intervals (left-positive) covered by SCUT. Channel is the gap."""
    if row['le'] is None or row['re'] is None:
        return []
    lo, hi = row['off'] - row['hw'], row['off'] + row['hw']
    spans = []
    if row['re'] < lo:
        spans.append((row['re'], min(lo, row['le'])))
    if hi < row['le']:
        spans.append((max(hi, row['re']), row['le']))
    return [(a, b) for a, b in spans if b - a > 0.25]


def ribbon(a_xz, b_xz, ya, yb, lift=0.012):
    """Triangle strip between two polylines. a/b are Nx2, ya/yb are heights."""
    parts = []
    for i in range(len(a_xz) - 1):
        p = []
        for ii, sd in ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1)):
            xz = a_xz[ii] if sd == 0 else b_xz[ii]
            y = (ya[ii] if sd == 0 else yb[ii]) + lift
            p.append((xz[0], y, xz[1]))
        V, I = ML.quad(*p)
        if V[0, 4] < 0:
            V[:, 3:6] *= -1
        parts.append((V, I))
    if not parts:
        return None
    V, I = ML.merge(parts)
    return V, ML.fix_winding(V, I)


def zone_meshes(zone, XZ, Y, mn, mx):
    """SCUT ribbons + cone positions for one chicane."""
    rows = zone['rows']
    # lateral samples of each SCUT span, matched station-to-station by side
    left_rib = []   # (xz Nx2, y N) outer=road edge, inner=channel
    right_rib = []
    cones = []
    for row in rows:
        spans = scut_intervals(row)
        # classify: a span whose centre is left of the path is the left block
        L = R = None
        for a, b in spans:
            if (a + b) / 2 >= row['off']:
                L = (a, b)  # higher lat = driver's left
            else:
                R = (a, b)
        def line(span, inset=0.0):
            if span is None:
                return None
            a, b = span
            if b - a < 0.3:
                return None
            # keep a small inset from the road edge so the strip sits on asphalt
            if abs(a - row['re']) < 0.2:
                a += 0.15
            if abs(b - row['le']) < 0.2:
                b -= 0.15
            if b - a < 0.3:
                return None
            xs, ys = [], []
            for lat in (a + inset, b - inset):
                q = row['o'] + lat * row['n']
                h = height_at(q[0], q[1], XZ, Y, mn, mx)
                if h is None:
                    return None
                xs.append(q)
                ys.append(h)
            return np.array(xs), np.array(ys)
        # store inner (channel side) and outer
        left_rib.append(line(L))
        right_rib.append(line(R))
        # cones: gate rows and corridor edges
        # role, dist and lat let the caller identify the exit-gate cones.
        # The outer cone (max dist) stays. The cone closest to the exit
        # opening (min dist to the racing line) is the one that is removed.
        s = row['s']
        se, sx = zone['spec']['s_enter'], zone['spec']['s_exit']
        if abs(s - sx) < 0.51:
            role = 'exit'
        elif abs(s - se) < 0.51:
            role = 'enter'
        else:
            role = 'mid'
        near_gate = role in ('exit', 'enter')

        def add_cone(lat):
            q = row['o'] + lat * row['n']
            h = height_at(q[0], q[1], XZ, Y, mn, mx)
            if h is None:
                return
            cones.append((q[0], h, q[1], role, abs(float(lat) - row['off']), float(lat)))

        if near_gate or (se <= s <= sx and abs(s) % 4.0 < 0.51):
            for side, span in (('L', L), ('R', R)):
                if span is None:
                    continue
                a, b = span
                # corridor-edge cone, just inside the block
                edge_lat = b - 0.75 if side == 'L' else a + 0.75
                if a + 0.4 < edge_lat < b - 0.2 or side == 'R' and a + 0.2 < edge_lat < b - 0.4:
                    add_cone(edge_lat)
        if near_gate:
            for a, b in scut_intervals(row):
                lat = a + 0.9
                while lat < b - 0.9:
                    add_cone(lat)
                    lat += 1.75
    def pack(seq):
        # seq items are None or ((outer_xz, inner_xz) wait line() returns (xs[2], ys[2])
        # xs[0] is outer-ish (a), xs[1] is inner (b) depending on side. Build from consecutive.
        A, B, YA, YB = [], [], [], []
        for item in seq:
            if item is None:
                if len(A) >= 2:
                    yield np.array(A), np.array(B), np.array(YA), np.array(YB)
                A, B, YA, YB = [], [], [], []
                continue
            xz, yv = item
            A.append(xz[0]); B.append(xz[1]); YA.append(yv[0]); YB.append(yv[1])
        if len(A) >= 2:
            yield np.array(A), np.array(B), np.array(YA), np.array(YB)
    parts = []
    for seq in (left_rib, right_rib):
        for A, B, YA, YB in pack(seq):
            r = ribbon(A, B, YA, YB)
            if r is not None:
                parts.append(r)
    scut = ML.merge(parts) if parts else None
    # dedupe cones
    kept = []
    for c in cones:
        if all(np.hypot(c[0] - k[0], c[2] - k[2]) > 1.25 for k in kept):
            kept.append(c)
    return scut, kept


def cone_mesh(x, y, z):
    """Same taper as the drift-course cones in tools/tents_v11.py."""
    V, I = ML.cyl((x, y, z), 0.15, 0.70, n=10, cap=False)
    V = V.astype(float)
    top = V[:, 1] > y + 0.35
    V[top, 0] = x + (V[top, 0] - x) * 0.15
    V[top, 2] = z + (V[top, 2] - z) * 0.15
    base = ML.box((x, y + 0.02, z), (0.38, 0.03, 0.38))
    return ML.merge([(V.astype('<f4'), I), base])


def solid_dds(rgb, n=8):
    im = Image.new('RGBA', (n, n), tuple(rgb) + (255,))
    buf = io.BytesIO()
    im.save(buf, 'DDS', pixel_format='DXT1')
    bb = buf.getvalue()
    hdr = bytearray(bb[:128])
    bs = 8
    struct.pack_into('<I', hdr, 20, max(1, (n + 3) // 4) * max(1, (n + 3) // 4) * bs)
    struct.pack_into('<I', hdr, 88, 0)
    struct.pack_into('<I', hdr, 8, 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000)
    return bytes(hdr) + bb[128:]


def apply_weave(xz, y_ai, zones, XZ, Y, mn, mx):
    new = xz.copy()
    new_y = y_ai.copy()
    moved = np.zeros(len(xz), bool)
    s_of = np.full(len(xz), np.nan)
    info = np.zeros(len(xz), dtype=[('le', 'f8'), ('re', 'f8'), ('off', 'f8'), ('zone', 'i4')])
    for zi, zone in enumerate(zones):
        for i, k in enumerate(zone['idxs']):
            if abs(zone['s'][i]) > FAR + 1:
                continue
            s_of[k] = zone['s'][i]
            spec = zone['spec']
            le, re = zone['edge'].get(int(k), (None, None))
            off = clamp_off(path_offset(zone['s'][i], spec), le, re)
            nrm = zone['left'][i]
            p = xz[k] + off * nrm
            h = height_at(p[0], p[1], XZ, Y, mn, mx)
            if h is None:
                raise SystemExit(f'{zone["name"]} idx {k} left the road at offset {off:+.2f}')
            new[k] = p
            new_y[k] = h + 0.40
            moved[k] = abs(off) > 0.02
            info[k] = (le if le is not None else np.nan, re if re is not None else np.nan, off, zi)
    return new, new_y, moved, s_of, info


def speeds(xz, v0):
    n = len(xz)
    seg = np.linalg.norm(np.diff(np.vstack([xz, xz[:1]]), axis=0), axis=1)
    kap = np.abs(_curvature(xz))
    cap = np.minimum(v0, np.minimum(VMAX, np.sqrt(MU * G / np.maximum(kap, 1e-6))))
    v = cap.copy()
    for _ in range(4):
        for i in range(n):
            j = (i + 1) % n
            a = max(1.2, 7.5 * (1 - v[i] / 75.0))
            v[j] = min(v[j], np.sqrt(max(v[i] ** 2 + 2 * a * seg[i], 0.0)))
        for i in range(n):
            j = (i - 1) % n
            v[j] = min(v[j], np.sqrt(max(v[i] ** 2 + 2 * BRK * seg[j], 0.0)))
        v = np.minimum(v, cap)
    return v, kap, seg


def _curvature(p, k=4):
    a = np.roll(p, k, 0)
    c = np.roll(p, -k, 0)
    ab = np.linalg.norm(p - a, axis=1)
    bc = np.linalg.norm(c - p, axis=1)
    ac = np.linalg.norm(c - a, axis=1)
    cr = (p[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (p[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    return 2 * cr / np.maximum(ab * bc * ac, 1e-9)


def point_in_mesh(x, z, V, I):
    tri = V[I][:, :, [0, 2]]
    yy = V[I][:, :, 1]
    mn, mx = tri.min(1), tri.max(1)
    m = (mn[:, 0] <= x) & (mx[:, 0] >= x) & (mn[:, 1] <= z) & (mx[:, 1] >= z)
    for p, yv in zip(tri[m], yy[m]):
        v0, v1 = p[1] - p[0], p[2] - p[0]
        v2 = np.array([x - p[0, 0], z - p[0, 1]])
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        a = (v2[0] * v1[1] - v1[0] * v2[1]) / den
        b = (v0[0] * v2[1] - v2[0] * v0[1]) / den
        if a >= -1e-3 and b >= -1e-3 and a + b <= 1.001:
            return True
    return False


def validate(zones, xz_old, xz_new, meshes, XZ, Y, mn, mx):
    fails = []
    for zone, (V, I) in zip(zones, meshes):
        # straight-through: original line, both wheel tracks on SCUT for a long run
        run = best = 0.0
        prev = None
        weave_bad = 0
        weave_n = 0
        straight_hit = 0
        straight_n = 0
        se, sx = zone['spec']['s_enter'], zone['spec']['s_exit']
        for row in zone['rows']:
            if row['s'] < se - 8 or row['s'] > sx + 8:
                continue
            for lat, kind in ((0.0, 'c'), (-WHEEL, 'w'), (WHEEL, 'w')):
                q = row['o'] + lat * row['n']
                hit = point_in_mesh(q[0], q[1], V, I)
                if kind == 'c':
                    straight_n += 1
                    straight_hit += int(hit)
                    if hit:
                        best = best + (0 if prev is None else abs(row['s'] - prev))
                        run = max(run, best)
                    else:
                        best = 0.0
                    prev = row['s'] if hit or best == 0 else prev
            # weave centre ± wheels must miss SCUT and stay on road
            if abs(row['s']) <= FAR - 2:
                for lat in (row['off'] - WHEEL, row['off'], row['off'] + WHEEL):
                    q = row['o'] + lat * row['n']
                    weave_n += 1
                    on = height_at(q[0], q[1], XZ, Y, mn, mx) is not None
                    hit = point_in_mesh(q[0], q[1], V, I)
                    if hit or not on:
                        weave_bad += 1
        print(f'  {zone["name"]}: straight centre samples on SCUT {straight_hit}/{straight_n}, '
              f'longest fully-covered approach run tracked separately')
        # recompute a clean run length of the centre being on SCUT
        on = []
        for row in zone['rows']:
            q = row['o']
            on.append((row['s'], point_in_mesh(q[0], q[1], V, I)))
        longest, cur, s_prev, open_run = 0.0, 0.0, None, False
        for s, hit in on:
            if hit and open_run:
                cur += s - s_prev
            elif hit:
                cur, open_run = 0.0, True
            else:
                longest = max(longest, cur)
                open_run = False
            s_prev = s
        longest = max(longest, cur)
        # both wheels of the straight car
        both = []
        for row in zone['rows']:
            ok = True
            for lat in (-WHEEL, WHEEL):
                q = row['o'] + lat * row['n']
                if not point_in_mesh(q[0], q[1], V, I):
                    ok = False
            both.append((row['s'], ok))
        longest_w, cur, s_prev, open_run = 0.0, 0.0, None, False
        for s, hit in both:
            if hit and open_run:
                cur += s - s_prev
            elif hit:
                cur, open_run = 0.0, True
            else:
                longest_w = max(longest_w, cur)
                open_run = False
            s_prev = s
        longest_w = max(longest_w, cur)
        print(f'    centre-on-SCUT run {longest:.1f} m, both-wheels-on-SCUT run {longest_w:.1f} m, '
              f'weave samples off road or on SCUT {weave_bad}/{weave_n}')
        if longest_w < 8.0:
            fails.append(f'{zone["name"]}: straight car is not on SCUT for 8 m ({longest_w:.1f} m)')
        if weave_bad:
            fails.append(f'{zone["name"]}: {weave_bad} weave samples hit SCUT or left the road')
        ai_bad = 0
        for i, k in enumerate(zone['idxs']):
            if abs(zone['s'][i]) > FAR - 2:
                continue
            for lat in (-WHEEL, 0.0, WHEEL):
                q = xz_new[k] + lat * zone['left'][i]
                on = height_at(q[0], q[1], XZ, Y, mn, mx) is not None
                hit = point_in_mesh(q[0], q[1], V, I)
                if hit or not on:
                    ai_bad += 1
        print(f'    AI samples off road or on SCUT {ai_bad}')
        if ai_bad:
            fails.append(f'{zone["name"]}: {ai_bad} AI-line samples hit SCUT or left the road')
        # direction check uses the clamped line the car actually drives
        ent = min(zone['rows'], key=lambda r: abs(r['s'] - se))['off']
        ex = min(zone['rows'], key=lambda r: abs(r['s'] - sx))['off']
        print(f'    clamped gate offsets {ent:+.2f} -> {ex:+.2f}')
        # Main: racing line is near the left edge and the road runs ~10 m to
        # the right. Entrance must sit on that right edge, exit on the left edge.
        if zone['name'] == 'main':
            erow = min(zone['rows'], key=lambda r: abs(r['s'] - se))
            xrow = min(zone['rows'], key=lambda r: abs(r['s'] - sx))
            centre = 0.5 * (erow['le'] + erow['re'])
            print(f'    road centre at entrance {centre:+.2f}  right edge {erow["re"]:.2f}  '
                  f'left edge at exit {xrow["le"]:.2f}')
            if not (ent < centre - 3.0
                    and abs(ent - (erow['re'] + EDGE)) <= 0.05
                    and abs(ex - (xrow['le'] - EDGE)) <= 0.05):
                fails.append(f'main weave is not right-then-left on the edges '
                             f'({ent:+.2f} -> {ex:+.2f}, road centre {centre:+.2f})')
        # The racing line hugs the right edge, so the road centre is several
        # metres to the driver's left. Both gates stay 1.25 m inside the
        # asphalt. Further south the line sits closer to the left edge, so
        # the racing-line number is not the old +8.20; the edge margin is.
        if zone['name'] == 'return':
            erow = min(zone['rows'], key=lambda r: abs(r['s'] - se))
            xrow = min(zone['rows'], key=lambda r: abs(r['s'] - sx))
            centre = 0.5 * (erow['le'] + erow['re'])
            print(f'    road centre at entrance {centre:+.2f}  left edge {erow["le"]:.2f}  '
                  f'right edge at exit {xrow["re"]:.2f}')
            if not (ent > centre + 2.0 and ent > 6.0
                    and abs(ent - (erow['le'] - EDGE)) <= 0.05
                    and abs(ex - (xrow['re'] + EDGE)) <= 0.05):
                fails.append(f'return weave is not left-then-right on the edges '
                             f'({ent:+.2f} -> {ex:+.2f}, road centre {centre:+.2f})')
        tris = len(I)
        print(f'    {zone["spec"]["mesh"]} tris {tris}')
        if tris > 30000:
            fails.append(f'{zone["spec"]["mesh"]} has {tris} tris')
        if V[:, 4].mean() < 0.5:
            fails.append(f'{zone["spec"]["mesh"]} normals are not up')
    return fails


def closed_cum(xz):
    seg = np.linalg.norm(np.diff(np.vstack([xz, xz[:1]]), axis=0), axis=1)
    return np.r_[0.0, np.cumsum(seg)]


def remap_u(u, cum_old, cum_new):
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    arc = u * cum_old[-1]
    i = int(np.clip(np.searchsorted(cum_old, arc, side='right') - 1, 0, len(cum_old) - 2))
    span = cum_old[i + 1] - cum_old[i]
    f = 0.0 if span < 1e-9 else (arc - cum_old[i]) / span
    neu = cum_new[i] + f * (cum_new[i + 1] - cum_new[i])
    return float(neu / cum_new[-1])


def rewrite_norm(path, cum_old, cum_new, keys):
    raw = open(path, 'rb').read()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    text = raw.decode('utf-8')
    def sub(m):
        u = float(m.group(2))
        return f'{m.group(1)}{remap_u(u, cum_old, cum_new):.6f}'
    # '=' sits outside the alternation; otherwise only the last key is rewritten.
    pat = re.compile(r'^((?:' + '|'.join(re.escape(k) for k in keys) + r')=)([0-9.]+)', re.M)
    text = pat.sub(sub, text.replace('\r\n', '\n')).replace('\n', nl)
    open(path, 'wb').write(text.encode('utf-8'))
    if 'IN_POINT' in keys:
        ins = [float(x) for x in re.findall(r'^IN_POINT=([0-9.]+)', text.replace('\r\n', '\n'), re.M)]
        outs = [float(x) for x in re.findall(r'^OUT_POINT=([0-9.]+)', text.replace('\r\n', '\n'), re.M)]
        if not ins or ins[0] != 0 or abs(outs[-1] - 1) > 1e-6:
            raise SystemExit(f'{path}: camera window does not cover 0..1')
        for a, b, c in zip(ins, outs, ins[1:]):
            if b <= a or abs(b - c) > 1e-6:
                raise SystemExit(f'{path}: camera windows do not tile ({a}, {b}, next {c})')


def clone_layout(cum_old, cum_new, length_km):
    dest = Z + LAY
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(Z + 'main/data', dest + '/data')
    os.makedirs(dest + '/ai', exist_ok=True)
    shutil.copy(Z + 'main/ai/pit_lane.ai', dest + '/ai/pit_lane.ai')
    shutil.copy(Z + 'main/map.png', dest + '/map.png')
    ui = Z + 'ui/' + LAY
    if os.path.isdir(ui):
        shutil.rmtree(ui)
    shutil.copytree(Z + 'ui/main', ui)
    for fn in ('cameras.ini', 'cameras_1.ini', 'cameras_2.ini', 'cameras_3.ini'):
        rewrite_norm(dest + '/data/' + fn, cum_old, cum_new, ['IN_POINT', 'OUT_POINT'])
    rewrite_norm(dest + '/data/sections.ini', cum_old, cum_new, ['IN', 'OUT'])
    surf = dest + '/data/surfaces.ini'
    with open(surf, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('\n; chicane layout: 1SCUT_chicane_main / 1SCUT_chicane_return in vf_chicane.kn5\n')
        fh.write('; use this KEY=SCUT. Cone meshes in that kn5 are visual only.\n')
    models = open(Z + 'models_main.ini', encoding='utf-8').read()
    if not models.endswith('\n'):
        models += '\n'
    models += '\n[MODEL_17]\nFILE=vf_chicane.kn5\nPOSITION=0,0,0\nROTATION=0,0,0\n'
    open(Z + 'models_chicane.ini', 'w', encoding='utf-8', newline='\n').write(models)
    ui_json = {
        'name': 'I-29 Speedway Long Course Chicane',
        'description': (
            'Long course of I-29 Speedway with two track-day cone chicanes on the west '
            'double-straight: right-then-left on the southbound main straight, left-then-right '
            'on the northbound return. Driving through a chicane is off-track (soft SCUT); '
            'the cone line stays valid. The short-course T1 hairpin stays closed. 36 paddock pit boxes. '
            f'Length is the fast_lane closed loop ({length_km:.3f} km).'
        ),
        'tags': ['circuit', 'drag', 'drift', 'Vybes Forge', 'zwiss', 'USA', 'open source'],
        'geotags': ['41° 01′ 27″ N', '95° 49′ 58″ W'],
        'country': 'USA', 'city': 'Pacific Junction',
        'length': f'{length_km:.3f} km', 'width': '12 m', 'pitboxes': '36',
        'run': 'clockwise', 'author': 'Vybes Forge', 'version': '1.1.2',
        'url': 'https://vybesforge.com', 'year': 2026,
    }
    import json
    open(ui + '/ui_track.json', 'w', encoding='utf-8', newline='\n').write(json.dumps(ui_json, indent=2) + '\n')


def render_preview(xz_old, xz_new, zones, meshes, cones, length_m, out_path):
    # overview + two zooms
    Wd, H = 1680, 980
    im = Image.new('RGBA', (Wd, H), (236, 232, 220, 255))
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        font_s = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    except Exception:
        font = font_s = ImageFont.load_default()

    def panel(box, pts_for_fit, title):
        x0, y0, x1, y1 = box
        dr.rectangle([x0, y0, x1, y1], fill=(248, 246, 238, 255), outline=(60, 60, 60))
        pad = 36
        xs = np.concatenate([p[:, 0] for p in pts_for_fit])
        zs = np.concatenate([p[:, 1] for p in pts_for_fit])
        span = max(xs.max() - xs.min(), zs.max() - zs.min(), 1)
        sc = min((x1 - x0 - 2 * pad) / (xs.max() - xs.min() + 4), (y1 - y0 - 2 * pad) / (zs.max() - zs.min() + 4))
        cx, cz = (xs.min() + xs.max()) / 2, (zs.min() + zs.max()) / 2
        ox, oy = (x0 + x1) / 2, (y0 + y1) / 2

        def P(x, z):
            return ox + (x - cx) * sc, oy - (z - cz) * sc

        def poly(pts, fill=None, outline=None, width=1):
            xy = [P(p[0], p[1]) for p in pts]
            if len(xy) >= 2:
                dr.line(xy, fill=outline or fill, width=width)

        # road edges
        for zone in zones:
            el, er = [], []
            for i, k in enumerate(zone['idxs']):
                if abs(zone['s'][i]) > FAR + 2:
                    continue
                le, re = zone['edge'].get(int(k), (None, None))
                if le is None:
                    continue
                el.append(xz_old[k] + le * zone['left'][i])
                er.append(xz_old[k] + re * zone['left'][i])
            if len(el) > 2:
                poly(el, outline=(90, 130, 90, 255), width=2)
                poly(er, outline=(90, 130, 90, 255), width=2)
        # SCUT
        for V, I in meshes:
            for tri in V[I][:, :, [0, 2]]:
                xy = [P(p[0], p[1]) for p in tri]
                dr.polygon(xy, fill=(210, 40, 40, 170))
        poly(xz_old, outline=(70, 70, 70, 255), width=2)
        poly(xz_new, outline=(0, 90, 190, 255), width=4)
        for (x, y, z) in cones:
            px, py = P(x, z)
            r = max(3, int(0.45 * sc))
            dr.ellipse([px - r, py - r, px + r, py + r], fill=(235, 90, 20), outline=(40, 20, 0))
        for zone in zones:
            o = xz_old[zone['anchor']]
            nrm = zone['left'][list(zone['idxs']).index(zone['anchor'])]
            a, b = o - 8 * nrm, o + 8 * nrm
            dr.line([P(*a), P(*b)], fill=(255, 40, 40), width=3)
            # travel arrow at the mark, downstream
            t = xz_old[(zone['anchor'] + 8) % len(xz_old)] - xz_old[(zone['anchor'] - 8) % len(xz_old)]
            t = t / np.linalg.norm(t)
            tip = o + 18 * t
            dr.line([P(*o), P(*tip)], fill=(255, 230, 80), width=3)
            dr.ellipse([*np.array(P(*tip)) - 4, *np.array(P(*tip)) + 4], fill=(255, 230, 80))
        dr.text((x0 + 10, y0 + 8), title, font=font, fill=(20, 20, 20, 255))
        # scale bar 20 m
        bar = 20 * sc
        dr.line([(x0 + 12, y1 - 16), (x0 + 12 + bar, y1 - 16)], fill=(20, 20, 20, 255), width=3)
        dr.text((x0 + 14, y1 - 34), '20 m', font=font_s, fill=(20, 20, 20, 255))

    def around(zone, rad=58):
        o = xz_old[zone['anchor']]
        ring = []
        for i, k in enumerate(zone['idxs']):
            if abs(zone['s'][i]) <= rad:
                ring.append(xz_old[k])
        return [np.array(ring)]
    panel((10, 40, 830, 960), around(zones[0]),
          'Main straight  southbound   entrance RIGHT, exit LEFT')
    panel((850, 40, 1670, 960), around(zones[1]),
          'Return straight  northbound   entrance LEFT, exit RIGHT')
    dr.text((12, 6),
            f'I-29 Long Course Chicane   closed loop {length_m:.1f} m    '
            f'grey = old straight    blue = cone line (valid)    red = SCUT shortcut (invalid)    '
            f'orange = cones    yellow arrow = travel',
            font=font, fill=(20, 20, 20, 255))
    # inset full lap
    ix0, iy0, ix1, iy1 = 1280, 740, 1655, 950
    dr.rectangle([ix0, iy0, ix1, iy1], fill=(255, 255, 255, 230), outline=(40, 40, 40))
    xs, zs = xz_new[:, 0], xz_new[:, 1]
    sc = min((ix1 - ix0 - 16) / (xs.max() - xs.min()), (iy1 - iy0 - 16) / (zs.max() - zs.min()))
    cx, cz = (xs.min() + xs.max()) / 2, (zs.min() + zs.max()) / 2
    ox, oy = (ix0 + ix1) / 2, (iy0 + iy1) / 2

    def Pi(x, z):
        return ox + (x - cx) * sc, oy - (z - cz) * sc
    dr.line([Pi(p[0], p[1]) for p in xz_new], fill=(0, 90, 190, 255), width=1)
    for zone in zones:
        px, py = Pi(*xz_old[zone['anchor']])
        dr.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 60, 40))
    dr.text((ix0 + 6, iy0 + 4), 'full lap', font=font_s, fill=(20, 20, 20, 255))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path)
    print('preview', out_path)


def main():
    ai = C.read_ai(Z + 'main/ai/fast_lane.ai')
    pos = ai['P']['p'].astype(np.float64)
    xz = pos[:, [0, 2]].copy()
    E = ai['E'].astype(np.float64)
    print('loading road collision...')
    XZ, Y, mn, mx = load_roads()
    print(f'  {len(XZ)} road tris')
    info = place_return(xz)
    align_stations(xz, info)
    zones = [build_zone(n, PLAN[n], xz, XZ, Y, mn, mx) for n in ('main', 'return')]
    if abs(zones[0]['shift']['z1'] - zones[1]['shift']['z1']) > 0.05:
        raise SystemExit(
            f'stations are not across from each other '
            f'(main z {zones[0]["shift"]["z1"]:.2f}, return z {zones[1]["shift"]["z1"]:.2f})')
    xz_new, y_new, moved, s_of, info = apply_weave(xz, pos[:, 1], zones, XZ, Y, mn, mx)
    v, kap, seg = speeds(xz_new, E[:, 0].copy())
    changed = np.abs(v - E[:, 0]) > 0.35
    cap = np.minimum(E[:, 0], np.minimum(VMAX, np.sqrt(MU * G / np.maximum(kap, 1e-6))))
    brake = np.clip((cap - v) / np.maximum(cap, 1) * 6, 0, 1)
    gas = np.where(brake > 0.02, 0.0, np.where(v < cap - 0.3, 1.0, np.clip(0.35 + v / VMAX * 0.4, 0, 1)))
    E2 = E.copy()
    E2[changed, 0] = v[changed]
    E2[changed, 1] = gas[changed]
    E2[changed, 2] = brake[changed]
    E2[changed, 4] = np.minimum(1 / np.maximum(kap[changed], 1e-7), 9e5)
    for i in np.nonzero(moved)[0]:
        le, re, off = info[i]['le'], info[i]['re'], info[i]['off']
        if np.isnan(le):
            continue
        E2[i, 5] = max(0.2, le - off)
        E2[i, 6] = max(0.2, off - re)
        if E2[i, 5] < EDGE - 0.05 or E2[i, 6] < EDGE - 0.05:
            raise SystemExit(f'idx {i} too close to the road edge (sideL {E2[i,5]:.2f} sideR {E2[i,6]:.2f})')
    pos_new = np.c_[xz_new[:, 0], y_new, xz_new[:, 1]]
    # y for unmoved points stays the original AI height
    pos_new[~moved, 1] = pos[~moved, 1]

    def exit_count(cs):
        return sum(1 for c in cs if c[3] == 'exit')

    def label_exit(cs):
        """E0 is the driver's-right cone (most negative lateral)."""
        exits = sorted((c for c in cs if c[3] == 'exit'), key=lambda c: c[5])
        return [dict(id=f'E{n}', cone=c, lat=c[5], dist=c[4], x=c[0], z=c[2])
                for n, c in enumerate(exits)]

    def trim_exit_gate(cs):
        """Keep the outer cone. Remove the cone closest to the exit opening."""
        labeled = label_exit(cs)
        if len(labeled) < 2:
            raise SystemExit('exit gate needs at least two cones')
        outer = max(labeled, key=lambda r: (r['dist'], abs(r['lat'])))
        close = min(labeled, key=lambda r: (r['dist'], abs(r['lat'])))
        if outer['id'] == close['id']:
            raise SystemExit('outer exit cone and closest exit cone are the same')
        kept = [c for c in cs if c is not close['cone']]
        return kept, labeled, outer, close

    scuts = []
    mesh_list = []
    zone_cones = {}
    for zone in zones:
        scut, cs = zone_meshes(zone, XZ, Y, mn, mx)
        if scut is None:
            raise SystemExit(f'no SCUT for {zone["name"]}')
        scuts.append(scut)
        zone_cones[zone['name']] = cs
        mesh_list.append(scut)
        print(f'{zone["name"]}: {len(cs)} cones ({exit_count(cs)} at the exit gate), '
              f'scut tris {len(scut[1])}')
    # PR #5 dropped the farthest-from-line cone. Put that one back and drop
    # the cone closest to the exit opening instead. One cone per gate.
    before = {n: exit_count(cs) for n, cs in zone_cones.items()}
    exit_report = {}
    for name in ('main', 'return'):
        kept, labeled, outer, close = trim_exit_gate(zone_cones[name])
        zone_cones[name] = kept
        exit_report[name] = (labeled, outer, close)
        print(f'{name} exit gate  (E0 = driver\'s right, increasing lateral):')
        for rec in labeled:
            if rec['id'] == outer['id']:
                tag = 'RESTORED outer (PR #5 had removed this)'
            elif rec['id'] == close['id']:
                tag = 'REMOVED closest to the exit'
            else:
                tag = 'kept'
            print(f'  {name}-exit-{rec["id"]}  lat {rec["lat"]:+.2f}  '
                  f'dist {rec["dist"]:.2f}  world ({rec["x"]:.2f}, {rec["z"]:.2f})  {tag}')
    after = {n: exit_count(cs) for n, cs in zone_cones.items()}
    print(f'exit cones  main {before["main"]} -> {after["main"]}   '
          f'return {before["return"]} -> {after["return"]}')
    if after['main'] != 4 or after['return'] != 4 or before['main'] != 5 or before['return'] != 5:
        raise SystemExit('expected 5 exit cones trimmed to 4 on both gates')
    cones = [(c[0], c[1], c[2]) for n in ('main', 'return') for c in zone_cones[n]]
    fails = validate(zones, xz, xz_new, mesh_list, XZ, Y, mn, mx)
    if fails:
        print('VALIDATION FAILED')
        for f in fails:
            print(' -', f)
        sys.exit(1)
    print('validation ok,', len(cones), 'cones')

    cone_parts = [cone_mesh(x, y + 0.02, z) for x, y, z in cones]
    coneV, coneI = ML.merge(cone_parts)
    print(f'cone mesh tris {len(coneI)} verts {len(coneV)}')

    base = W.read_materials(Z + 'vf_vr7_longcut.kn5')['vr7_cut_invisible']
    def mat(name, tex=None, amb=0.4, diff=0.5, spec=0.2, exp=20):
        m = dict(name=name, shader='ksPerPixel', ab=0, at=0, dm=int(base['dm']),
                 props=ML.props(base['props'], ksAmbient=amb, ksDiffuse=diff, ksSpecular=spec, ksSpecularEXP=exp),
                 samplers=[('txDiffuse', 0, tex)] if tex else [])
        return m
    texs = [('vfc_cone.dds', solid_dds((235, 90, 20)))]
    mats = [mat('vr7_cut_invisible'), mat('vfc_cone', 'vfc_cone.dds', 0.45, 0.55, 0.2, 20)]
    meshes = []
    for zone, (V, I) in zip(zones, mesh_list):
        meshes.append(dict(name=zone['spec']['mesh'], mat_index=0, verts=V, idx=I, lod_out=0))
    meshes.append(dict(name='cone_chicane', mat_index=1, verts=coneV, idx=coneI, lod_out=0))
    kn5 = Z + 'vf_chicane.kn5'
    W.write_kn5(kn5, texs, mats, meshes, rootname='vf_chicane')
    hidden = W.hide_nodes(kn5, kn5, [z['spec']['mesh'] for z in zones])
    print('hid SCUT nodes', hidden)
    # reparse
    K.scan(kn5)

    cum_old, cum_new = closed_cum(xz), closed_cum(xz_new)
    print(f'length main {cum_old[-1]:.2f} m  chicane {cum_new[-1]:.2f} m  delta {cum_new[-1]-cum_old[-1]:+.2f} m')
    print(f'min speed through moved points {E2[moved,0].min()*3.6:.0f} km/h  '
          f'(was {E[moved,0].min()*3.6:.0f}..{E[moved,0].max()*3.6:.0f})')
    # braking reach
    for zone in zones:
        i = zone['anchor']
        print(f'  {zone["name"]} apex speed {E2[i,0]*3.6:.0f} km/h (was {E[i,0]*3.6:.0f})')

    os.makedirs(Z + LAY + '/ai', exist_ok=True)
    C.write_ai(Z + LAY + '/ai/fast_lane.ai', pos_new, E2.astype(np.float32))
    # layout folders are cloned after the AI exists; write_ai above is into a folder
    # created by clone. Order: clone first would wipe ai. Clone now, then rewrite ai.
    length_km = cum_new[-1] / 1000.0
    clone_layout(cum_old, cum_new, length_km)
    C.write_ai(Z + LAY + '/ai/fast_lane.ai', pos_new, E2.astype(np.float32))
    C.write_ai(Z + LAY + '/data/ideal_line.ai', pos_new, E2.astype(np.float32))

    # pit lane must not run through either chicane
    pit = C.read_ai(Z + 'main/ai/pit_lane.ai')['P']['p'][:, [0, 2]]
    from scipy.spatial import cKDTree
    for zone in zones:
        d, _ = cKDTree(pit).query(xz_new[zone['idxs']])
        print(f'pit clearance {zone["name"]} {d.min():.1f} m')
        if d.min() < 8:
            raise SystemExit('pit lane conflicts with a chicane')

    prev = os.path.join(ROOT, 'docs', 'previews', 'chicane_layout.png')
    render_preview(xz, xz_new, zones, mesh_list, cones, cum_new[-1], prev)
    art = '/opt/cursor/artifacts'
    if os.path.isdir(art):
        shutil.copy(prev, os.path.join(art, 'chicane_layout.png'))
    # stash numbers for the changelog
    placed = zones[1]['shift']['info']
    open('/tmp/chicane_stats.txt', 'w').write(
        f'length_m {cum_new[-1]:.2f}\nmain_m {cum_old[-1]:.2f}\n'
        f'delta_m {cum_new[-1]-cum_old[-1]:+.2f}\ncones {len(cones)}\n'
        f'apex_main {E2[zones[0]["anchor"],0]*3.6:.1f}\n'
        f'apex_return {E2[zones[1]["anchor"],0]*3.6:.1f}\n'
        f'main_spacing {zones[0]["spacing"]:.2f}\n'
        f'main_shortened {2 * GATE - zones[0]["spacing"]:.2f}\n'
        f'return_along {zones[1]["shift"]["arc"]:+.2f}\n'
        f'return_dz {zones[1]["shift"]["dz"]:+.2f}\n'
        f'return_z0 {zones[1]["shift"]["z0"]:.2f}\n'
        f'return_z1 {zones[1]["shift"]["z1"]:.2f}\n'
        f'return_old_z {placed["old_z"]:.2f}\n'
        f'return_new_z {placed["new_z"]:.2f}\n'
        f'return_prev_z {placed["prev_z"]:.2f}\n'
        f'return_prev_along {placed["prev_along"]:+.2f}\n'
        f'return_moved_from_prev {placed["moved_from_prev"]:+.2f}\n'
        f'shared_z {placed["shared_z"]:.2f}\n'
        f'main_prev_z {placed["main_prev_z"]:.2f}\n'
        f'main_prev_along {placed["main_prev_along"]:+.2f}\n'
        f'return_moved {placed["moved_from_old"]:+.2f}\n'
        f'from_onset {placed["from_onset"]:.2f}\n'
        f'from_rejoin {placed["from_rejoin"]:.2f}\n'
        f'onset_z {placed["onset_z"]:.2f}\n'
        f'rejoin_z {placed["rejoin_z"]:.2f}\n'
        f'main_z0 {zones[0]["shift"]["z0"]:.2f}\n'
        f'main_z1 {zones[0]["shift"]["z1"]:.2f}\n'
        f'main_along {zones[0]["shift"]["arc"]:+.2f}\n'
        f'main_dz {zones[0]["shift"]["dz"]:+.2f}\n'
        f'main_enter {min(zones[0]["rows"], key=lambda r: abs(r["s"] - zones[0]["spec"]["s_enter"]))["off"]:+.2f}\n'
        f'main_exit {min(zones[0]["rows"], key=lambda r: abs(r["s"] - zones[0]["spec"]["s_exit"]))["off"]:+.2f}\n'
        f'return_enter {min(zones[1]["rows"], key=lambda r: abs(r["s"] - zones[1]["spec"]["s_enter"]))["off"]:+.2f}\n'
        f'return_exit {min(zones[1]["rows"], key=lambda r: abs(r["s"] - zones[1]["spec"]["s_exit"]))["off"]:+.2f}\n'
        f'exit_cones_main {after["main"]}\n'
        f'exit_cones_return {after["return"]}\n'
        f'exit_cones_main_before {before["main"]}\n'
        f'exit_cones_return_before {before["return"]}\n'
        f'cones_main {len(zone_cones["main"])}\n'
        f'cones_return {len(zone_cones["return"])}\n'
        + ''.join(
            f'exit_{name}_{kind} {rec["id"]} lat {rec["lat"]:+.2f} dist {rec["dist"]:.2f} '
            f'x {rec["x"]:.2f} z {rec["z"]:.2f}\n'
            for name, (labeled, outer, close) in exit_report.items()
            for kind, rec in (('restored', outer), ('removed', close))
        )
        + ''.join(
            f'exit_{name}_all {rec["id"]} lat {rec["lat"]:+.2f} dist {rec["dist"]:.2f} '
            f'x {rec["x"]:.2f} z {rec["z"]:.2f}\n'
            for name, (labeled, outer, close) in exit_report.items()
            for rec in labeled
        )
        + '\n'.join(f'tris_{z["name"]} {len(m[1])}' for z, m in zip(zones, mesh_list))
        + f'\ncone_tris {len(coneI)}\n'
    )
    print('done')


if __name__ == '__main__':
    main()
