# Getting ad changes onto players' clients (proposal, tents-v1.1)

Ads are baked as track-skin textures in `vf_i29_speedway/skins/default/*_slotNN.dds`. AC swaps kn5 textures by file name and doesn't checksum this folder.

## A. Live ads for CSP clients (recommended, no client download). DRAFT, needs in-game test
The server tells every CSP client to run an online script. The script downloads a JSON manifest plus PNGs and repaints the slot materials (`vftent_slotNN`, `vfboard_slotNN`).
1. Host `server/ads/i29_ads.lua` (raw text) and the web bundle on HTTPS, for example `https://vybesforge.com/i29/`.
2. Add to the server's `cfg/csp_extra_options.ini`. For AssettoServer, that file is read directly. For vanilla acServer, put the same text into the Content Manager server preset under "CSP extra options"; CM embeds it into the welcome message:
```ini
[SCRIPT_I29_ADS]
SCRIPT = "https://vybesforge.com/i29/i29_ads.lua"
REQUIRED = 0
manifest = "https://vybesforge.com/i29/ads/ads.json"
refreshMinutes = 30
```
3. To change an ad: `python3 tools/make_ad.py --brand X --tent NN --apply`, then `python3 tools/export_ads_web.py https://vybesforge.com/i29/ads`, then upload `assets_src/ads/web/*`. Clients that are already connected pick it up within refreshMinutes; everyone else gets it on their next join. No server restart is needed.
Players without CSP keep whatever `skins/default` they installed, or the kn5 fallback.

## B. Fallback: CM auto-download with a version bump (everyone, including non-CSP players)
1. Bump `"version"` in `ui/main/ui_track.json` and `ui/short/ui_track.json` (for example 1.1.1), and rebuild the zip with `tools/build_release.py`.
2. Upload the zip to a direct-download URL.
3. AssettoServer: set `cfg/cm_content/content.json` and `EnableServerDetails: true` in `extra_cfg.yml`.
   Vanilla acServer: use the CM server preset (Details, Share mode: Download URL). This needs CM's server wrapper (ac-server-wrapper) running.
```json
{ "track": { "url": "https://.../vf_i29_speedway_v1.1.1.zip", "version": "1.1.1" } }
```
Content Manager compares the version and offers the download or update when a player joins. The version text must match the track's version shown in CM.
