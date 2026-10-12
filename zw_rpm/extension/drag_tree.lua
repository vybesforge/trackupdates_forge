-- I-29 Speedway: automatic drag-strip Christmas tree (self-made model in zw_draglaunch.kn5).
-- Loaded by [SCRIPT_DRAG_TREE] in ext_config.ini (CSP track script). Visual only, does not time or start anything.
-- Cycle (60 s, sim time; paused sim = paused tree), "sportsman" tree, both lanes together:
--   0.0  all off
--   2.0  pre-stage on          4.0  stage on
--   6.0  amber 1 (0.5 s) -> 6.5 amber 2 -> 7.0 amber 3 -> 7.5 GREEN
--   9.0  pre-stage/stage off (cars gone)      12.0 green off, reset;  red: never (no foul) in the auto loop
local CYCLE = 60
local groups = {
  prestage = { mesh = 'drtree_prestage', col = rgb(1.0, 0.85, 0.45), on = function(t) return t >= 2 and t < 9 end },
  stage    = { mesh = 'drtree_stage',    col = rgb(1.0, 0.85, 0.45), on = function(t) return t >= 4 and t < 9 end },
  amber1   = { mesh = 'drtree_amber1',   col = rgb(1.0, 0.45, 0.02), on = function(t) return t >= 6.0 and t < 6.5 end },
  amber2   = { mesh = 'drtree_amber2',   col = rgb(1.0, 0.45, 0.02), on = function(t) return t >= 6.5 and t < 7.0 end },
  amber3   = { mesh = 'drtree_amber3',   col = rgb(1.0, 0.45, 0.02), on = function(t) return t >= 7.0 and t < 7.5 end },
  green    = { mesh = 'drtree_green',    col = rgb(0.05, 1.0, 0.15), on = function(t) return t >= 7.5 and t < 12 end },
  red      = { mesh = 'drtree_red',      col = rgb(1.0, 0.03, 0.02), on = function(t) return false end },
}
local INTENSITY = 40   -- bright enough to read in daylight and bloom at night / in VR
local OFF = rgb(0, 0, 0)
for _, g in pairs(groups) do g.ref = ac.findMeshes(g.mesh); g.state = nil end
local clock = 0
local function apply(t)
  for _, g in pairs(groups) do
    local s = g.on(t)
    if s ~= g.state then
      g.ref:setMaterialProperty('ksEmissive', s and g.col * INTENSITY or OFF)
      g.state = s
    end
  end
end
function script.update(dt)
  clock = (clock + dt) % CYCLE
  apply(clock)
end
ac.onRelease(function()
  for _, g in pairs(groups) do g.ref:setMaterialProperty('ksEmissive', OFF) end
end)
