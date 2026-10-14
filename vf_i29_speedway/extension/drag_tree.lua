-- I-29 Speedway: reactive drag-strip Christmas tree (CSP track script, model in vf_draglaunch.kn5).
-- Loaded by [SCRIPT_DRAG_TREE] in ext_config.ini. Visual + timing display only; does not affect physics or race.
-- Logic is a 1:1 port of apps/python/i29_dragtree/dragtree_logic.py (unit-tested in tests/test_dragtree.py).
--   * Each lane (west/left x -255.75, east/right x -246.75) has its own bulb column (drtree_<group>_W / _E).
--   * Pre-stage / stage bulbs follow the front-tyre contact points of the car in that lane
--     (stage beam z -347.5, pre-stage 0.178 m behind it, beam counted as broken within 0.30 m).
--   * Both lanes staged for 1.0 s (or one lane staged 8 s with the other lane occupied but not staged,
--     or one lane with the other empty) -> sportsman tree: 3 ambers 0.5 s apart, green 0.5 s after amber 3.
--   * Leaving the stage beam before green = red light. RT, 60 ft, 330 ft, 1/8 mile ET + trap speed
--     (594-660 ft) shown as an on-screen message (ac.setMessage, if available) and in the Lua debug app.
--   * If no car is within 60 m of the start line for 10 s the old 60 s attract loop runs (both lanes);
--     it stops the moment a car comes back.
local STAGE_Z, PRESTAGE_GAP, BEAM_HALF = -347.5, 0.178, 0.30
local LANE_X = { W = -255.75, E = -246.75 }
local LANE_IDS = { 'W', 'E' }
local LANE_HALF, APPROACH, STAGE_HOLD, AMBER_STEP = 2.4, 25.0, 1.0, 0.5
local SOLO_WAIT, TIMEOUT, RESET_DELAY, MS_TO_MPH = 8.0, 30.0, 4.0, 2.236936
local MARKS = { { '60ft', 18.288 }, { '330ft', 100.584 }, { '594ft', 181.051 }, { '660ft', 201.168 } }
local GROUPS = { 'prestage', 'stage', 'amber1', 'amber2', 'amber3', 'green', 'red' }

local function laneOf(x, z)
  if z > STAGE_Z + APPROACH or z < STAGE_Z - 260 then return nil end
  for _, k in ipairs(LANE_IDS) do
    if math.abs(x - LANE_X[k]) <= LANE_HALF then return k end
  end
  return nil
end
local function beams(z)
  local s = z - STAGE_Z
  return math.abs(s - PRESTAGE_GAP) <= BEAM_HALF, math.abs(s) <= BEAM_HALF
end
local function contains(list, v) for _, x in ipairs(list) do if x == v then return true end end return false end

local L = {}
DragLogic = L

local function newLane(id) return { lid = id, marks = {}, pre = false, stg = false, done = false, red = false } end
function L.reset(tr)
  tr.lanes = { W = newLane('W'), E = newLane('E') }
  tr.state, tr.t0, tr.green_t, tr.done_t, tr.participants = 'IDLE', nil, nil, nil, {}
end
function L.new()
  local tr = { last_results = {} }
  L.reset(tr)
  return tr
end

local function dist(z) return (STAGE_Z - BEAM_HALF) - z end

local function launch(tr, l, t, z, prev)
  local zb = STAGE_Z - BEAM_HALF
  if prev and prev[2] > zb and zb > z then
    t = prev[1] + (t - prev[1]) * (prev[2] - zb) / (prev[2] - z)
    z = zb
  end
  l.leave_t = t
  l.pre, l.stg = false, false
  if tr.green_t == nil or t < tr.green_t then l.red = true end
  l.last = { t, dist(z) }
  if tr.state == 'ARMED' then
    tr.state, tr.t0, tr.green_t = 'COUNT', t, t + 3 * AMBER_STEP
  end
end

local function finish(tr, l, aborted)
  l.done = true
  local rt = nil
  if tr.green_t ~= nil and l.leave_t ~= nil then rt = l.leave_t - tr.green_t end
  local r = { lane = l.lid, car = l.car, rt = rt, red = l.red, aborted = aborted }
  for _, m in ipairs(MARKS) do r[m[1]] = l.marks[m[1]] end
  if r['594ft'] and r['660ft'] and r['660ft'] > r['594ft'] then
    local v = (MARKS[4][2] - MARKS[3][2]) / (r['660ft'] - r['594ft'])
    r.mph, r.kmh = v * MS_TO_MPH, v * 3.6
  end
  l.result = r
end

local function track(tr, l, t, sk)
  if l.done then return end
  if sk == nil or sk[1] ~= l.car or t - l.leave_t > TIMEOUT then finish(tr, l, true) return end
  local d = dist(sk[2])
  local t1, d1 = l.last[1], l.last[2]
  for _, m in ipairs(MARKS) do
    if l.marks[m[1]] == nil and d1 < m[2] and m[2] <= d and d > d1 then
      l.marks[m[1]] = t1 + (t - t1) * (m[2] - d1) / (d - d1) - l.leave_t
    end
  end
  l.last = { t, d }
  if l.marks['660ft'] then finish(tr, l, false) end
end

function L.results(tr)
  local out = {}
  for _, k in ipairs(LANE_IDS) do if tr.lanes[k].result then out[#out + 1] = tr.lanes[k].result end end
  return out
end
function DragResults(tr) return tr.last_results end

local function sequence(tr, t)
  local LN = tr.lanes
  if tr.state == 'IDLE' then
    for _, k in ipairs(LANE_IDS) do if LN[k].staged_since then tr.state = 'ARMED' end end
  end
  if tr.state == 'ARMED' then
    local present, staged = {}, {}
    for _, k in ipairs(LANE_IDS) do
      if LN[k].car ~= nil then
        present[#present + 1] = k
        if LN[k].staged_since then staged[#staged + 1] = k end
      end
    end
    if #staged == 0 then tr.state, tr.participants = 'IDLE', {} return end
    tr.participants = present
    local hold, maxh = math.huge, -math.huge
    for _, k in ipairs(staged) do
      hold = math.min(hold, t - LN[k].staged_since); maxh = math.max(maxh, t - LN[k].staged_since)
    end
    if #staged < #present and maxh >= SOLO_WAIT then present = staged; tr.participants = staged end
    if #staged == #present and hold >= STAGE_HOLD then
      tr.state, tr.t0, tr.green_t = 'COUNT', t, t + 3 * AMBER_STEP
    end
  end
  if tr.state == 'COUNT' or tr.state == 'RUN' then
    if tr.green_t and t >= tr.green_t then tr.state = 'RUN' end
    local all = #tr.participants > 0
    for _, k in ipairs(tr.participants) do
      local l = LN[k]
      if l.leave_t == nil and l.car == nil and not l.done then l.done = true end
      if not l.done then all = false end
    end
    if all then tr.state, tr.done_t = 'DONE', t; tr.last_results = L.results(tr); tr.newResults = true end
  end
  if tr.state == 'DONE' and t - tr.done_t >= RESET_DELAY then
    local res = L.results(tr)
    L.reset(tr)
    tr.last_results = res
  end
end

-- cars: array of {id, x, z} (front-tyre contact midpoint)
function L.update(tr, t, cars)
  local seen = {}
  for i = 1, #cars do
    local cid, x, z = cars[i][1], cars[i][2], cars[i][3]
    local k = laneOf(x, z)
    if k then
      local l, s = tr.lanes[k], seen[k]
      if l.car ~= nil and cid == l.car then seen[k] = { cid, z }
      elseif s == nil or (s[1] ~= l.car and math.abs(z - STAGE_Z) < math.abs(s[2] - STAGE_Z)) then seen[k] = { cid, z } end
    end
  end
  for _, k in ipairs(LANE_IDS) do
    local l, sk = tr.lanes[k], seen[k]
    if l.leave_t == nil then
      if sk == nil then
        l.car, l.pre, l.stg, l.staged_since = nil, false, false, nil
      else
        if l.car ~= sk[1] then l.prev = nil end
        l.car = sk[1]
        local z = sk[2]
        local prev = l.prev
        l.prev = { t, z }
        l.pre, l.stg = beams(z)
        if l.stg then
          if l.staged_since == nil then l.staged_since = t end
        else
          l.staged_since = nil
          if z - STAGE_Z < -BEAM_HALF and contains(tr.participants, k)
              and (tr.state == 'COUNT' or tr.state == 'RUN' or tr.state == 'ARMED') then
            launch(tr, l, t, z, prev)
          end
        end
      end
    else
      track(tr, l, t, sk)
    end
  end
  sequence(tr, t)
end

function L.bulbs(tr, t)
  local out = {}
  for _, k in ipairs(LANE_IDS) do
    local l = tr.lanes[k]
    local b = { prestage = l.pre, stage = l.stg, amber1 = false, amber2 = false, amber3 = false, green = false, red = l.red }
    if tr.t0 and contains(tr.participants, k) and not l.red then
      local dt = t - tr.t0
      for i = 0, 2 do
        if dt >= i * AMBER_STEP and dt < (i + 1) * AMBER_STEP then b['amber' .. (i + 1)] = true end
      end
      if tr.green_t and t >= tr.green_t then b.green = true end
    end
    out[k] = b
  end
  return out
end

local function attract(t)   -- old 60 s loop, both lanes
  t = t % 60
  local b = { prestage = t >= 2 and t < 9, stage = t >= 4 and t < 9, amber1 = t >= 6 and t < 6.5,
    amber2 = t >= 6.5 and t < 7, amber3 = t >= 7 and t < 7.5, green = t >= 7.5 and t < 12, red = false }
  return { W = b, E = b }
end
L.attract = attract

local function fmt(v, n) if v == nil then return '-' end return string.format('%.' .. (n or 3) .. 'f', v) end
function L.slip(r)
  return string.format('%s lane%s  R/T %s  60ft %s  330ft %s  1/8 %s @ %s mph',
    r.lane == 'W' and 'Left' or 'Right', r.red and ' RED LIGHT' or (r.aborted and ' (aborted)' or ''),
    fmt(r.rt), fmt(r['60ft']), fmt(r['330ft']), fmt(r['660ft']), fmt(r.mph, 2))
end

if TEST_MODE then return end

-- ===================== CSP glue (not exercised by the unit tests) =====================
local INTENSITY = 40
local OFF = rgb(0, 0, 0)
local COL = { prestage = rgb(1.0, 0.85, 0.45), stage = rgb(1.0, 0.85, 0.45), amber1 = rgb(1.0, 0.45, 0.02),
  amber2 = rgb(1.0, 0.45, 0.02), amber3 = rgb(1.0, 0.45, 0.02), green = rgb(0.05, 1.0, 0.15), red = rgb(1.0, 0.03, 0.02) }
local meshes, state = {}, {}
for _, k in ipairs(LANE_IDS) do
  for _, g in ipairs(GROUPS) do
    local n = 'drtree_' .. g .. '_' .. k
    meshes[n] = ac.findMeshes(n)
  end
end
local tree = L.new()
local clock, idle, attractClock = 0, 0, 0

local function frontContact(car)
  -- midpoint of the two front tyre contact points; fallback: car origin pushed 1.3 m forward
  local ok, p = pcall(function()
    local w0, w1 = car.wheels[0], car.wheels[1]
    local a = w0.contactPoint or w0.position
    local b = w1.contactPoint or w1.position
    return vec3((a.x + b.x) / 2, 0, (a.z + b.z) / 2)
  end)
  if ok and p then return p end
  return car.position + car.look * 1.3
end

local function apply(b)
  for _, k in ipairs(LANE_IDS) do
    for _, g in ipairs(GROUPS) do
      local n = 'drtree_' .. g .. '_' .. k
      local s = b[k][g] and true or false
      if s ~= state[n] then
        meshes[n]:setMaterialProperty('ksEmissive', s and COL[g] * INTENSITY or OFF)
        state[n] = s
      end
    end
  end
end

function script.update(dt)
  clock = clock + dt
  local sim = ac.getSim()
  local cars, near = {}, false
  for i = 0, sim.carsCount - 1 do
    local car = ac.getCar(i)
    if car and car.isConnected ~= false then
      local p = frontContact(car)
      cars[#cars + 1] = { i, p.x, p.z }
      if math.abs(p.z - STAGE_Z) < 60 and math.abs(p.x - (-251.25)) < 30 then near = true end
    end
  end
  L.update(tree, clock, cars)
  if tree.newResults then
    tree.newResults = false
    for _, r in ipairs(tree.last_results) do
      local s = L.slip(r)
      ac.debug('drag ' .. r.lane, s)
      if ac.setMessage then pcall(ac.setMessage, 'I-29 Drag Strip', s) end
    end
  end
  idle = near and 0 or idle + dt
  if idle > 10 and tree.state == 'IDLE' then
    attractClock = attractClock + dt
    apply(attract(attractClock))
  else
    attractClock = 0
    apply(L.bulbs(tree, clock))
  end
end

ac.onRelease(function()
  for _, m in pairs(meshes) do m:setMaterialProperty('ksEmissive', OFF) end
end)
