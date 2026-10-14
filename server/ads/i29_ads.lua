-- I-29 Speedway: live ad textures for CSP clients (CSP online script, DRAFT, untested in-game).
-- Loaded by the server via csp_extra_options.ini [SCRIPT_I29_ADS]. Fetches a JSON manifest and repaints
-- tent / billboard materials with remote PNG/JPG images. Nothing is written to disk on the client, and nothing is checksummed.
-- Manifest: { "version": 7, "slots": { "vftent_slot13": "https://.../tent_slot13.png", "vfboard_slot01": "https://.../board_slot01.png" } }
local cfg = ac.configValues({ manifest = '', refreshMinutes = 0 })
local SIZE = { tent = vec2(2048, 2048), board = vec2(2048, 1024) }
local applied = {}

local function paint(material, url)
  local meshes = ac.findMeshes('material:' .. material)
  if meshes:size() == 0 then ac.log('i29_ads: no meshes for ' .. material) return end
  local size = material:find('board') and SIZE.board or SIZE.tent
  ui.onImageReady(url, function ()
    meshes:setMaterialTexture('txDiffuse', {
      textureSize = size, background = rgbm(0, 0, 0, 1),
      callback = function () display.image({ image = url, pos = vec2(0, 0), size = size }) end })
    applied[material] = url
    ac.log('i29_ads: ' .. material .. ' <- ' .. url)
  end)
end

local function fetch()
  if cfg.manifest == '' then return end
  web.get(cfg.manifest, function (err, response)
    if err or not response or response.status ~= 200 then ac.log('i29_ads: manifest failed ' .. tostring(err)) return end
    local ok, data = pcall(JSON.parse, response.body)
    if not ok or type(data) ~= 'table' or type(data.slots) ~= 'table' then ac.log('i29_ads: bad manifest') return end
    for material, url in pairs(data.slots) do
      if type(url) == 'string' and applied[material] ~= url and material:match('^vf[a-z]+_slot%d%d$') then paint(material, url) end
    end
  end)
end

fetch()
if cfg.refreshMinutes > 0 then setInterval(fetch, cfg.refreshMinutes * 60) end
