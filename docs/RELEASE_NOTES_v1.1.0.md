# I-29 Speedway v1.1.0

Paddock drift course and in-server ad slots. **The checksummed files changed:** install v1.1.0 on the server and on every client, and delete the old `zw_*.kn5` files.

## Changes
- **Drift course** in the paddock lot (behind the spawns), resurfaced in the track's cracked concrete with matching CONCRETE physics:
  - 309 m line with entry, transitions, north sweeper, donut and east S
  - painted outer clipping zones
  - red/white jersey barriers with a weathered texture, rubber scuffs and a reflective strip that glows at night with CSP (`1WALL_DRIFT_n`, collision)
  - banded tyre stacks at the clipping points and donut (`1WALL_DRIFT_TYRES`, collision)
  - cones
  - an entrance lane from the spawn rows: edge lines, chevrons, a "DRIFT ENTRY" decal and cones
- **Ad slots:**
  - 18 pop-up vendor tents (`vftent_slot01..18`) and the 2 drag-strip end billboards (`vfboard_slot01..02`), each with its own texture.
  - Ads are swapped through the track skin folder `skins/default/tent_slotNN.dds` / `board_slotNN.dds`. AC replaces kn5 textures with same-named files there, in vanilla AC and with CSP, and this folder is not checksummed.
  - The fallback art baked into the kn5 reads "YOUR AD HERE / Advertise: vybesforge.com".
  - Sample advertiser art is included on several slots.
  - `tools/make_ad.py` generates ad textures. `docs/ADS_DISTRIBUTION.md` covers pushing ads to players.
- **Paddock Drift replay camera set** (`cameras_3.ini`, both layouts): 3 wide elevated cameras with long windows.
- **Rename:** `zw_ext/tents/vegetation/draglaunch/dragexit/vr5/vr6/vr7_longcut.kn5` are now `vf_*.kn5`, and `models_main.ini` / `models_short.ini` are updated to match.
- **Night:** the tents and billboards are subtly self-lit with CSP.
- Version 1.1.0 in both layouts.

## Upgrading
1. Delete `content/tracks/vf_i29_speedway/` (or at least every `zw_*.kn5` in it) on the server and on the clients.
2. Install the v1.1.0 zip.
3. Restart the server.
