# I-29 Speedway drag tree / timing logic (pure Python, no AC imports).
# Written for the Python 3.3 interpreter bundled with vanilla Assetto Corsa: no f-strings, no type hints.
# Mirrored 1:1 in vf_i29_speedway/extension/drag_tree.lua (CSP pole tree). Unit tests: tests/test_dragtree.py
#
# Geometry (AC world coords, drag strip runs toward -z):
#   stage beam at z = STAGE_Z, pre-stage beam 7 in (0.178 m) behind it (at +z).
#   lanes: west/left x = -255.75, east/right x = -246.75.
# A beam is "blocked" while the front-tyre contact point is within BEAM_HALF of it
# (stands in for the tyre's footprint/radius breaking a low light beam).
# Sportsman (full) tree: 3 ambers 0.5 s apart, green 0.5 s after amber 3.
# Reaction time = time the car clears the stage beam - green time (negative = red light).
# ET clock starts when the stage beam clears (as at a real strip).
STAGE_Z = -347.5
PRESTAGE_GAP = 0.178
BEAM_HALF = 0.30
LANE_X = {'W': -255.75, 'E': -246.75}
LANE_HALF = 2.4
APPROACH = 25.0          # m behind the line in which a car counts as "in the lanes"
STAGE_HOLD = 1.0         # s both lanes must be staged before the tree drops
AMBER_STEP = 0.5
MARKS = (('60ft', 18.288), ('330ft', 100.584), ('594ft', 181.051), ('660ft', 201.168))
TIMEOUT = 30.0
RESET_DELAY = 4.0
SOLO_WAIT = 8.0          # s a staged car waits for the other lane before running solo
MS_TO_MPH = 2.236936

def lane_of(x, z):
    """Lane id for a position, or None (outside both lanes / outside the strip area)."""
    if z > STAGE_Z + APPROACH or z < STAGE_Z - 260.0:
        return None
    for k in ('W', 'E'):
        if abs(x - LANE_X[k]) <= LANE_HALF:
            return k
    return None

def beams(z):
    """(prestage_blocked, stage_blocked) for a front contact z."""
    s = z - STAGE_Z
    return (abs(s - PRESTAGE_GAP) <= BEAM_HALF, abs(s) <= BEAM_HALF)

class Lane(object):
    def __init__(self, lid):
        self.lid = lid
        self.reset()
    def reset(self):
        self.car = None
        self.pre = self.stg = False
        self.staged_since = None
        self.leave_t = None
        self.red = False
        self.last = None        # (t, d) previous sample after leaving
        self.marks = {}
        self.done = False
        self.result = None
        self.prev = None        # (t, z) previous sample, for sub-frame interpolation
    def distance(self, z):
        return (STAGE_Z - BEAM_HALF) - z

class Tree(object):
    """Feed update(t, cars) every frame; cars = list of (car_id, x, z) front-contact positions."""
    def __init__(self):
        self.lanes = {'W': Lane('W'), 'E': Lane('E')}
        self.last_results = []
        self.reset()
    def reset(self):
        for l in self.lanes.values():
            l.reset()
        self.state = 'IDLE'     # IDLE -> ARMED (someone staged) -> COUNT (tree dropping) -> RUN -> DONE
        self.t0 = None          # first amber time
        self.green_t = None
        self.done_t = None
        self.participants = []
    # ---- bulbs ----
    def bulbs(self, t):
        """{'W': {prestage,stage,amber1,amber2,amber3,green,red: bool}, 'E': {...}}"""
        out = {}
        for k, l in self.lanes.items():
            b = {'prestage': l.pre, 'stage': l.stg, 'amber1': False, 'amber2': False,
                 'amber3': False, 'green': False, 'red': l.red}
            if self.t0 is not None and k in self.participants and not l.red:
                dt = t - self.t0
                for i in range(3):
                    a0 = i * AMBER_STEP
                    if a0 <= dt < a0 + AMBER_STEP:
                        b['amber%d' % (i + 1)] = True
                if self.green_t is not None and t >= self.green_t:
                    b['green'] = True
            out[k] = b
        return out
    # ---- main step ----
    def update(self, t, cars):
        seen = {'W': None, 'E': None}
        for cid, x, z in cars:
            k = lane_of(x, z)
            if k is None:
                continue
            l = self.lanes[k]
            # keep following the car that owns the lane; otherwise take the one nearest the line
            if l.car is not None and cid == l.car:
                seen[k] = (cid, z)
            elif seen[k] is None or (seen[k][0] != l.car and abs(z - STAGE_Z) < abs(seen[k][1] - STAGE_Z)):
                seen[k] = (cid, z)
        for k, l in self.lanes.items():
            sk = seen[k]
            if l.leave_t is None:
                if sk is None:
                    l.car = None; l.pre = l.stg = False; l.staged_since = None
                    continue
                if l.car != sk[0]:
                    l.prev = None
                l.car, z = sk
                prev = l.prev
                l.prev = (t, z)
                l.pre, l.stg = beams(z)
                if l.stg:
                    if l.staged_since is None:
                        l.staged_since = t
                else:
                    l.staged_since = None
                    # cleared the stage beam forwards = launch
                    if z - STAGE_Z < -BEAM_HALF and k in self.participants and self.state in ('COUNT', 'RUN'):
                        self._launch(l, t, z, prev)
                    elif z - STAGE_Z < -BEAM_HALF and self.state == 'ARMED' and k in self.participants:
                        self._launch(l, t, z, prev)   # rolled before the tree dropped: red light
            else:
                self._track(l, t, sk)
        self._sequence(t)

    def _launch(self, l, t, z, prev):
        zb = STAGE_Z - BEAM_HALF
        if prev is not None and prev[1] > zb > z:
            t = prev[0] + (t - prev[0]) * (prev[1] - zb) / (prev[1] - z)   # exact beam-clear time
            z = zb
        l.leave_t = t
        l.pre = l.stg = False
        if self.green_t is None or t < self.green_t:
            l.red = True
        l.last = (t, l.distance(z))
        if self.state == 'ARMED':
            self.state = 'COUNT'
            self.t0 = t
            self.green_t = t + 3 * AMBER_STEP

    def _track(self, l, t, sk):
        if l.done:
            return
        if sk is None or sk[0] != l.car or t - l.leave_t > TIMEOUT:
            self._finish(l, aborted=True)
            return
        d = l.distance(sk[1])
        t1, d1 = l.last
        for name, m in MARKS:
            if name not in l.marks and d1 < m <= d and d > d1:
                tc = t1 + (t - t1) * (m - d1) / (d - d1)   # linear interpolation between frames
                l.marks[name] = tc - l.leave_t
        l.last = (t, d)
        if '660ft' in l.marks:
            self._finish(l, aborted=False)

    def _finish(self, l, aborted):
        l.done = True
        rt = None
        if self.green_t is not None and l.leave_t is not None:
            rt = l.leave_t - self.green_t
        r = {'lane': l.lid, 'car': l.car, 'rt': rt, 'red': l.red, 'aborted': aborted}
        for name, m in MARKS:
            r[name] = l.marks.get(name)
        if r['594ft'] is not None and r['660ft'] is not None and r['660ft'] > r['594ft']:
            v = (MARKS[3][1] - MARKS[2][1]) / (r['660ft'] - r['594ft'])
            r['mph'] = v * MS_TO_MPH
            r['kmh'] = v * 3.6
        else:
            r['mph'] = r['kmh'] = None
        l.result = r

    def _sequence(self, t):
        L = self.lanes
        if self.state == 'IDLE':
            staged = [k for k in L if L[k].staged_since is not None]
            if staged:
                self.state = 'ARMED'
        if self.state == 'ARMED':
            present = [k for k in L if L[k].car is not None]
            staged = [k for k in present if L[k].staged_since is not None]
            if not staged:
                self.state = 'IDLE'; self.participants = []
                return
            self.participants = present
            hold = min(t - L[k].staged_since for k in staged)
            if len(staged) < len(present) and max(t - L[k].staged_since for k in staged) >= SOLO_WAIT:
                self.participants = present = staged      # other lane never staged: run solo
            if len(staged) == len(present) and hold >= STAGE_HOLD:
                self.state = 'COUNT'
                self.t0 = t
                self.green_t = t + 3 * AMBER_STEP
        if self.state in ('COUNT', 'RUN'):
            if self.green_t is not None and t >= self.green_t:
                self.state = 'RUN'
            parts = [L[k] for k in self.participants]
            for l in parts:   # never launched and drove away / left the lane
                if l.leave_t is None and l.car is None and not l.done:
                    l.done = True
            if parts and all(l.done for l in parts):
                self.state = 'DONE'
                self.last_results = self.results()
                self.done_t = t
        if self.state == 'DONE' and t - self.done_t >= RESET_DELAY:
            results = self.results()
            self.reset()
            self.last_results = results
    def results(self):
        return [self.lanes[k].result for k in ('W', 'E') if self.lanes[k].result is not None]

def fmt_slip(r):
    def f(v, n=3):
        return '-' if v is None else ('%.' + str(n) + 'f') % v
    lines = ['Lane %s %s' % ('LEFT' if r['lane'] == 'W' else 'RIGHT',
             'RED LIGHT' if r['red'] else ('ABORTED' if r['aborted'] else ''))]
    lines.append('R/T   %s' % f(r['rt']))
    lines.append('60\'   %s' % f(r['60ft']))
    lines.append('330\'  %s' % f(r['330ft']))
    lines.append('1/8 ET  %s' % f(r['660ft']))
    lines.append('1/8 MPH %s  (%s km/h)' % (f(r['mph'], 2), f(r['kmh'], 1)))
    return lines
