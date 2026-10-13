# I-29 Speedway drag tree + timeslip -- vanilla Assetto Corsa Python app (no CSP needed).
# Install: copy apps/python/i29_dragtree into <assettocorsa>/apps/python/, enable "i29_dragtree"
# in Content Manager > Settings > Assetto Corsa > Apps (or in-game app bar).
# Works only on the I-29 Speedway track (folder vf_i29_speedway); on other tracks the window shows a notice.
# Python 3.3 (AC's bundled interpreter): no f-strings.
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ac
import acsys
import dragtree_logic as D

TRACKS = ('vf_i29_speedway',)
W_, H_ = 260, 330
app = None
tree = D.Tree()
clock = 0.0
on_track = False
labels = {}
slip_labels = []
_contact_ok = [True]

COL = {'prestage': (1.0, 0.85, 0.45), 'stage': (1.0, 0.85, 0.45), 'amber1': (1.0, 0.5, 0.05),
       'amber2': (1.0, 0.5, 0.05), 'amber3': (1.0, 0.5, 0.05), 'green': (0.1, 1.0, 0.2), 'red': (1.0, 0.05, 0.05)}
ROWS = [('prestage', 34, 12), ('stage', 52, 12), ('amber1', 74, 22), ('amber2', 102, 22),
        ('amber3', 130, 22), ('green', 158, 22), ('red', 186, 22)]
COLX = {'W': 40, 'E': 150}

def front_contact(i):
    """Front-axle tyre-contact midpoint (x, z); falls back to car position + 1.3 m along velocity."""
    if _contact_ok[0]:
        try:
            a = ac.getCarState(i, acsys.CS.TyreContactPoint, acsys.WHEELS.FL)
            b = ac.getCarState(i, acsys.CS.TyreContactPoint, acsys.WHEELS.FR)
            return (a[0] + b[0]) / 2.0, (a[2] + b[2]) / 2.0
        except Exception:
            _contact_ok[0] = False
    p = ac.getCarState(i, acsys.CS.WorldPosition)
    v = ac.getCarState(i, acsys.CS.Velocity)
    sp = (v[0] ** 2 + v[2] ** 2) ** 0.5
    if sp > 0.5:
        return p[0] + 1.3 * v[0] / sp, p[2] + 1.3 * v[2] / sp
    return p[0], p[2] - 1.3     # parked: assume facing down the strip (-z)

def acMain(ac_version):
    global app, on_track
    app = ac.newApp('I-29 Drag Tree')
    ac.setSize(app, W_, H_)
    ac.setBackgroundOpacity(app, 0.6)
    try:
        on_track = ac.getTrackName(0) in TRACKS
    except Exception:
        on_track = False
    for k, x in (('W', 'LEFT'), ('E', 'RIGHT')):
        lb = ac.addLabel(app, x)
        ac.setPosition(lb, COLX[k] - 6, 212)
    labels['state'] = ac.addLabel(app, '' if on_track else 'Drag tree: I-29 Speedway only')
    ac.setPosition(labels['state'], 8, 232)
    for i in range(6):
        lb = ac.addLabel(app, '')
        ac.setPosition(lb, 8 + (i // 3) * 126, 250 + (i % 3) * 18)
        ac.setFontSize(lb, 12)
        slip_labels.append(lb)
    ac.addRenderCallback(app, on_render)
    return 'I-29 Drag Tree'

def acUpdate(deltaT):
    global clock
    if not on_track:
        return
    clock += deltaT
    cars = []
    for i in range(ac.getCarsCount()):
        try:
            if i > 0 and not ac.isConnected(i):
                continue
            x, z = front_contact(i)
            cars.append((i, x, z))
        except Exception:
            pass
    tree.update(clock, cars)
    ac.setText(labels['state'], {'IDLE': 'Pull into a lane and stage', 'ARMED': 'Staged - hold',
                                 'COUNT': 'Tree dropping', 'RUN': 'GO', 'DONE': 'Run complete'}[tree.state])
    res = tree.last_results
    txt = []
    for r in res[:2]:
        txt.append(('LEFT' if r['lane'] == 'W' else 'RIGHT') + (' RED' if r['red'] else ''))
        txt.append('RT %s  60ft %s' % (_f(r['rt']), _f(r['60ft'])))
        txt.append('1/8 %s @ %s' % (_f(r['660ft']), _f(r['mph'], 1)))
    for i, lb in enumerate(slip_labels):
        ac.setText(lb, txt[i] if i < len(txt) else '')

def _f(v, n=3):
    return '-' if v is None else ('%.' + str(n) + 'f') % v

def on_render(deltaT):
    if not on_track:
        return
    b = tree.bulbs(clock)
    ac.glColor4f(0.05, 0.05, 0.05, 1)
    ac.glQuad(W_ / 2 - 3, 30, 6, 182)          # centre post
    for lane in ('W', 'E'):
        for g, y, s in ROWS:
            c = COL[g]
            on = b[lane][g]
            k = 1.0 if on else 0.13
            n = 2 if g in ('prestage', 'stage') else 1
            for j in range(n):
                x = COLX[lane] + j * (s + 6) - (s + 6) * (n - 1) / 2.0
                ac.glColor4f(c[0] * k, c[1] * k, c[2] * k, 1)
                ac.glQuad(x, y, s, s)
