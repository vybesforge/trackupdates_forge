# I-29 Speedway v1.1.1

Concrete roads, the west-lot loop, drag-area collision and 2 more ad tents. **Checksummed files changed:** install v1.1.1 on the server and on every client.

## Changes
- **Cracked concrete roads** (the drift lot's Concrete01 look, CONCRETE physics):
  - the drag return/access road west of the drag strip and its east jogs
  - the south boundary road (Jesup Ave), with its bumps smoothed about 50% (centre-line RMS 7.7 -> 3.8 mm, max 39 -> 19 mm); no steps at the edges
  - the **west-lot loop**: lot access road, its exit to 190th St, the return-road extension to the apron and the two cross links (z ~-801 / -624), all joined into one connected surface with the apron
- **West parking lot** surfaces from the satellite (google + NAIP): dirt/bare patches are gravel (GRAVEL physics), grass stays grass; grass verges along the new concrete; gravel is kept off containers, tents and other objects.
- **Drag-area collision:** invisible box proxies (`1WALL_DRAG_*`) on the existing drag-area objects, buildings and fences: timing tower, grandstand, huts, containers, toilets, light poles, gantry legs, signs, barrels, fences. Nothing on the racing surface or the staging lanes.
- **2 new drag-area ad tents:** the 3 old staging tents are gone; the 2 front ones are now v2 ad tents `vftent_slot19` / `vftent_slot20` (same design and "YOUR AD HERE / Advertise: vybesforge.com" fallback, `skins/default/tent_slot19.dds` / `tent_slot20.dds`). **20 tent slots** in total. `tools/make_ad.py --tent 19 20` and `tools/export_ads_web.py` support them.
- New files: `vf_roads.kn5`, `vf_dragcol.kn5`, `vf_westlot.kn5`, `vf_dragtents.kn5` (listed in `models_main.ini` / `models_short.ini`).
- Version 1.1.1 in both layouts.

## Upgrading
1. Install the v1.1.1 zip over v1.1.0 (or clean-install) on the server and all clients.
2. Restart the server.
