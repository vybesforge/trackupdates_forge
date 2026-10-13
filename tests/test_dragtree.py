"""Unit tests for the drag-tree timing logic with simulated car positions.
Runs the Python module and (via lupa, if installed) the CSP Lua script's identical logic."""
import math, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'apps', 'python', 'i29_dragtree'))
import dragtree_logic as D

DT = 1.0 / 120

def sim(tree, plans, t_end):
    """plans: {car_id: (x, launch_time, accel)}; car sits staged at STAGE_Z until launch_time
    (approaching from 10 m back first), then accelerates at accel from rest."""
    t = 0.0
    while t < t_end:
        cars = []
        for cid, (x, tl, a) in plans.items():
            if t < 1.0:
                z = D.STAGE_Z + 10.0 * (1.0 - t)            # roll in to the stage beam
            elif tl is None or t < tl:
                z = D.STAGE_Z
            else:
                z = D.STAGE_Z - 0.5 * a * (t - tl) ** 2
            cars.append((cid, x, z))
        tree.update(t, cars)
        t += DT
    return tree

def expect(a, dist):   # time from beam clear to dist past clear, from rest at the line
    return math.sqrt(2 * (dist + D.BEAM_HALF) / a) - math.sqrt(2 * D.BEAM_HALF / a)

class TestTree(unittest.TestCase):
    def test_two_lane_run(self):
        tr = D.Tree()
        # both staged by t=1.0, hold 1.0 -> t0 = 2.0, green at 3.5
        sim(tr, {1: (-255.75, 3.6, 8.0), 2: (-246.75, 3.55, 6.0)}, 20)
        res = {r['lane']: r for r in tr.last_results}
        self.assertEqual(set(res), {'W', 'E'})
        for lane, a in (('W', 8.0), ('E', 6.0)):
            r = res[lane]
            self.assertFalse(r['red']); self.assertFalse(r['aborted'])
            self.assertAlmostEqual(r['60ft'], expect(a, 18.288), delta=0.01)
            self.assertAlmostEqual(r['660ft'], expect(a, 201.168), delta=0.01)
            v = 20.117 / (expect(a, 201.168) - expect(a, 181.051))
            self.assertAlmostEqual(r['mph'], v * D.MS_TO_MPH, delta=0.3)
        tl_clear_W = 3.6 + math.sqrt(2 * 0.3 / 8.0)
        self.assertAlmostEqual(res['W']['rt'], tl_clear_W - 3.5, delta=2 * DT)

    def test_red_light(self):
        tr = D.Tree()
        sim(tr, {1: (-255.75, 3.0, 8.0)}, 15)    # green would be 3.5
        r = tr.last_results[0]
        self.assertTrue(r['red']); self.assertLess(r['rt'], 0)
        self.assertIsNotNone(r['660ft'])

    def test_bulb_sequence(self):
        tr = D.Tree()
        seen = []
        t = 0.0
        while t < 3.6:
            tr.update(t, [(1, -246.75, D.STAGE_Z)])
            b = tr.bulbs(t)['E']
            seen.append((round(t, 3), b))
            t += 0.05
        def at(tt):
            return min(seen, key=lambda s: abs(s[0] - tt))[1]
        self.assertTrue(at(0.5)['stage'] and at(0.5)['prestage'])
        self.assertTrue(at(1.2)['amber1']); self.assertTrue(at(1.7)['amber2'])
        self.assertTrue(at(2.2)['amber3']); self.assertTrue(at(2.6)['green'])
        self.assertFalse(tr.bulbs(2.6)['W']['green'])     # empty lane stays dark

    def test_wait_for_other_lane_then_solo(self):
        tr = D.Tree()
        t = 0.0; started = None
        while t < 12:
            cars = [(1, -255.75, D.STAGE_Z), (2, -246.75, D.STAGE_Z + 6.0)]   # car 2 never stages
            tr.update(t, cars)
            if started is None and tr.t0 is not None: started = tr.t0
            t += DT
        self.assertIsNotNone(started)
        self.assertAlmostEqual(started, D.SOLO_WAIT, delta=0.05)
        self.assertEqual(tr.participants, ['W'])

    def test_lane_assignment(self):
        self.assertEqual(D.lane_of(-255.0, -340), 'W')
        self.assertEqual(D.lane_of(-247.0, -340), 'E')
        self.assertIsNone(D.lane_of(-251.25, -340))
        self.assertIsNone(D.lane_of(-255.0, -300))

    def test_abort_leaving_lane(self):
        tr = D.Tree()
        t = 0.0
        while t < 15:
            if t < 4.0: z, x = D.STAGE_Z - (0 if t < 3.6 else 0.5 * 8 * (t - 3.6) ** 2), -255.75
            else: z, x = -360, -230.0                 # swerved out of the lane
            tr.update(t, [(1, x, z)]); t += DT
        r = tr.last_results[0]
        self.assertTrue(r['aborted']); self.assertIsNone(r['660ft'])

try:
    import lupa
    HAVE_LUPA = True
except ImportError:
    HAVE_LUPA = False

@unittest.skipUnless(HAVE_LUPA, 'lupa not installed')
class TestLuaMatchesPython(unittest.TestCase):
    def test_same_results(self):
        from lupa import LuaRuntime
        lua = LuaRuntime()
        src = open(os.path.join(ROOT, 'vf_i29_speedway', 'extension', 'drag_tree.lua')).read()
        lua.execute('TEST_MODE = true')
        lua.execute(src)
        Logic = lua.globals().DragLogic
        tree = Logic.new()
        plans = {1: (-255.75, 3.6, 8.0), 2: (-246.75, 3.55, 6.0)}
        pt = D.Tree()
        t = 0.0
        while t < 20:
            cars = []
            for cid, (x, tl, a) in plans.items():
                z = D.STAGE_Z + 10 * (1 - t) if t < 1 else (D.STAGE_Z if t < tl else D.STAGE_Z - 0.5 * a * (t - tl) ** 2)
                cars.append((cid, x, z))
            pt.update(t, cars)
            lt = lua.table_from([lua.table_from([c, x, z]) for c, x, z in cars])
            Logic.update(tree, t, lt)
            t += DT
        lres = {r['lane']: r for r in lua.globals().DragResults(tree).values()}
        for r in pt.last_results:
            l = lres[r['lane']]
            for k in ('rt', '60ft', '330ft', '660ft', 'mph'):
                self.assertAlmostEqual(r[k], l[k], places=6)

try:
    from lupa import luajit21 as LJ
except ImportError:
    LJ = None

@unittest.skipUnless(LJ is not None, 'lupa.luajit21 not installed')
class TestLuaGlueMockCSP(unittest.TestCase):
    """Runs the full drag_tree.lua under LuaJIT (CSP's interpreter) against a mocked CSP API."""
    def test_glue(self):
        r = LJ.LuaRuntime()
        r.execute('''
local mt={__mul=function(a,s) return {a[1]*s,a[2]*s,a[3]*s} end}
function rgb(a,b,c) return setmetatable({a,b,c},mt) end
function vec3(x,y,z) return {x=x,y=y,z=z} end
LOG={}; LIT={}
CARZ=-337.5
ac={findMeshes=function(n) return {setMaterialProperty=function(self,k,v) LIT[n]=(v[1]+v[2]+v[3])>0 end} end,
 getSim=function() return {carsCount=1} end,
 getCar=function(i) local w=vec3(-246.75,0,CARZ) return {wheels={[0]={contactPoint=w},[1]={contactPoint=w}}} end,
 debug=function(k,v) LOG[#LOG+1]=v end, setMessage=function(a,b) end, onRelease=function(f) end}
script={}''')
        r.execute(open(os.path.join(ROOT, 'vf_i29_speedway', 'extension', 'drag_tree.lua')).read())
        r.execute('''
GREEN_E,GREEN_W=false,false
local t=0; local dt=1/60
while t<20 do
  if t<1 then CARZ=-337.5-10*t elseif t<3.6 then CARZ=-347.5 else CARZ=-347.5-4*(t-3.6)^2 end
  script.update(dt); t=t+dt
  if LIT.drtree_green_E then GREEN_E=true end
  if LIT.drtree_green_W then GREEN_W=true end
end''')
        g = r.globals()
        self.assertTrue(g.GREEN_E); self.assertFalse(g.GREEN_W)
        logs = list(g.LOG.values())
        self.assertEqual(len(logs), 1); self.assertIn('Right lane', logs[0]); self.assertIn('mph', logs[0])

class TestVanillaAppMockAC(unittest.TestCase):
    """Loads i29_dragtree.py against stub ac/acsys modules and drives one solo run."""
    def test_app(self):
        import types, importlib
        st = {'z': D.STAGE_Z + 10, 'texts': {}, 'quads': 0}
        ac = types.ModuleType('ac'); acsys = types.ModuleType('acsys')
        acsys.CS = types.SimpleNamespace(TyreContactPoint=1, WorldPosition=2, Velocity=3)
        acsys.WHEELS = types.SimpleNamespace(FL=0, FR=1)
        n = [0]
        def lab(app, text=''):
            n[0] += 1; st['texts'][n[0]] = text; return n[0]
        ac.newApp = lambda name: 99; ac.setSize = ac.setBackgroundOpacity = ac.setPosition = ac.setFontSize = lambda *a: None
        ac.getTrackName = lambda i: 'vf_i29_speedway'; ac.addLabel = lab
        ac.setText = lambda lb, t: st['texts'].__setitem__(lb, t)
        ac.addRenderCallback = lambda app, f: st.__setitem__('render', f)
        ac.getCarsCount = lambda: 1; ac.isConnected = lambda i: True
        ac.getCarState = lambda i, what, wheel=None: (-255.75, 0.0, st['z'])
        ac.glColor4f = lambda *a: None
        def quad(*a): st['quads'] += 1
        ac.glQuad = quad
        sys.modules['ac'] = ac; sys.modules['acsys'] = acsys
        app = importlib.import_module('i29_dragtree')
        app.acMain(1)
        t = 0.0
        while t < 20:
            st['z'] = D.STAGE_Z + 10 * (1 - t) if t < 1 else (D.STAGE_Z if t < 3.6 else D.STAGE_Z - 4 * (t - 3.6) ** 2)
            app.acUpdate(DT); st['render'](DT); t += DT
        joined = ' '.join(st['texts'].values())
        self.assertIn('LEFT', joined); self.assertIn('1/8 6.8', joined)
        self.assertGreater(st['quads'], 1000)

class PaintedLineTest(unittest.TestCase):
    """VR10: the painted stage / pre-stage lines in zw_draglaunch.kn5 sit exactly on the beams used by the Lua script,
    the Python app and (via the same constants) the tests."""
    def test_painted_lines_match_beams(self):
        import re, struct
        sys.path.insert(0, os.path.join(ROOT, 'tools')); import kn5patch as K
        f = os.path.join(ROOT, 'vf_i29_speedway', 'zw_draglaunch.kn5'); d = open(f, 'rb').read(); zc = {}
        for n, o, l, c in K.scan(f)[1]:
            if n in ('drag_stageline', 'drag_prestageline') and c == 2:
                q = o + l + 8; nv, = struct.unpack_from('<I', d, q)
                zz = struct.unpack_from('<%df' % (nv * 11), d, q + 4)[2::11]; zc[n] = (min(zz) + max(zz)) / 2
        self.assertAlmostEqual(zc['drag_stageline'], D.STAGE_Z, places=3)
        self.assertAlmostEqual(zc['drag_prestageline'] - zc['drag_stageline'], D.PRESTAGE_GAP, places=3)
        lua = open(os.path.join(ROOT, 'vf_i29_speedway', 'extension', 'drag_tree.lua')).read()
        m = re.search(r'local STAGE_Z, PRESTAGE_GAP, BEAM_HALF = ([-\d.]+), ([\d.]+)', lua)
        self.assertEqual((float(m.group(1)), float(m.group(2))), (D.STAGE_Z, D.PRESTAGE_GAP))
        self.assertAlmostEqual(D.PRESTAGE_GAP, 7 * 0.0254, places=3)

if __name__ == '__main__':
    unittest.main(verbosity=2)
