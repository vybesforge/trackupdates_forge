# I-29 Speedway for Assetto Corsa

An open-source Assetto Corsa track of **I-29 Speedway** (formerly Raceway Park of the Midlands / Mid America Motorplex) in Pacific Junction, Iowa.

## Features
- Three layouts: **Long Course** (`main`, 3.644 km), **Short Course** (`short`, 2.380 km), and **Long Course Chicane** (`chicane`, the long course plus two cone chicanes on the west double-straight). All three have AI lines and 36 pit boxes.
- Elevation re-draped to real USGS lidar ground.
- 1/8-mile drag strip with a reactive two-lane tree. It runs on the pole with CSP; without CSP, the bundled Python app shows it on the monitor.
- Paddock, north extension roads to the fuel stations and US-34, and night lights (CSP).

## What's new in v1.1.4
- Exit soft-cut on both chicanes is pulled out to the innermost remaining exit cone. The cut no longer starts in the gap where the closest exit cone was removed. Stations, weave offsets, and the AI line are unchanged. **Checksum changed:** `vf_chicane.kn5`.

## What's new in v1.1.3
- **Long Course Chicane** (`chicane`): the long course plus two soft-cut cone chicanes on the west double-straight, aligned across from each other. The AI `fast_lane` and `ideal_line` follow the weaves. Driving through a chicane is off-track (invisible SCUT, no hard walls); the cone line stays valid. The short-course hairpin stays closed.
- `main` and `short` are unchanged apart from the version string.
- **Checksums added** (`vf_chicane.kn5`, `models_chicane.ini`, `chicane/data/surfaces.ini`): the server and every client need the v1.1.3 files.

## What's new in v1.1.2
- Drag-area ad tent `vftent_slot20` moved to the old back-tent spot next to slot 19 (opening towards the apron); the south spot is empty. Collision and gravel follow. **Checksums changed** (`vf_dragtents.kn5`, `vf_dragcol.kn5`, `vf_westlot.kn5`).

## What's new in v1.1.1
- **Cracked concrete roads** (CONCRETE grip): the drag return road, the south road (Jesup Ave, bumps smoothed ~50%), and the **west-lot loop** (lot access road, exit to 190th St, return-road extension and cross links), all connected.
- **West parking lot** grass vs dirt from the satellite: dirt patches are gravel, grass stays grass, gravel kept off objects.
- **Drag-area collision** on the existing objects, buildings and fences (invisible `1WALL_DRAG_*` boxes; lanes and staging stay clear).
- **2 new drag-area ad tents** (`vftent_slot19/20`) replace the old staging tents: **20 tent slots** in total.
- **Checksums changed** (`vf_i29_speedway.kn5`, `models_*.ini`, new `vf_roads.kn5`, `vf_dragcol.kn5`, `vf_westlot.kn5`, `vf_dragtents.kn5`): the server and every client need the v1.1.1 files.

## What's new in v1.1.0
- **Paddock drift course** on cracked concrete (CONCRETE grip): a flowing 309 m line with transitions, a sweeper and a donut. Painted red/white jersey barriers and banded tyre stacks with collision, cones, painted clipping zones, and a marked entrance lane from the spawn rows.
- **Ad slots:** 18 vendor tents plus the 2 drag-strip end billboards, each a sellable slot. Advertiser art is loaded from `skins/default/tent_slotNN.dds` / `board_slotNN.dds` (works in vanilla AC and with CSP, not checksummed). The fallback art reads "YOUR AD HERE / Advertise: vybesforge.com". `tools/make_ad.py` makes new ad textures.
- **Paddock Drift** replay camera set (`cameras_3.ini`, both layouts): 3 wide elevated cameras.
- **File rename:** `zw_*.kn5` are now `vf_*.kn5`. **Delete the old `zw_*.kn5`** from existing installs (server and clients).
- **Checksums changed** (`vf_tents.kn5`, `vf_vr5.kn5`, `vf_vr6.kn5`, `models_*.ini`, and all renamed kn5s): the server and every client need the v1.1.0 files.

v1.0.4: `.gitattributes` EOL fix for git installs. v1.0.3: server docs corrected (AssettoServer `cfg/data_track_params.ini` only). v1.0.2: added the track params snippet. v1.0.1: rebuilt replay cameras (3 sets per layout) and restored dirt/gravel textures.

## Install
Download `I-29_Speedway_v1.1.4.zip` (current release **v1.1.4**) from the GitHub Releases page or from `release/`. Unzip it into your Assetto Corsa root folder, or drag it onto Content Manager. It installs `content/tracks/vf_i29_speedway/` and the optional `apps/python/i29_dragtree/` app. Custom Shaders Patch (0.2.x) is recommended, but the track also runs in vanilla AC.

If you have an old `content/tracks/zw_rpm` install, delete it first. If you clone this repo instead, you need Git LFS (`git lfs pull`), because the large files are stored in LFS. See [`INSTALL_AGENT.md`](INSTALL_AGENT.md) for scripted client and server installs (release zip + SHA-256 check, clean replace, server setup, repair of earlier system/data edits).

## Checksums / installing from git
Install from the release zip. AC checksums `*.kn5`, `surfaces.ini` and `models*.ini` byte-for-byte; a Windows git checkout with `core.autocrlf=true` (before the v1.0.4 `.gitattributes` fix) converted `.ini` files to CRLF and caused "checksum failed" online. If you copy from git, use a fresh clone of main/v1.1.4 or set `core.autocrlf false`. MD5s of all checksummed files are listed in `INSTALL_AGENT.md`.

## Running a server
- **Vanilla acServer** does not need any track params; nothing to do.
- **AssettoServer** reads only `<server root>/cfg/data_track_params.ini` (auto-downloaded from the CSP list if missing; it never reads `system/data`). If it reports missing track params for `vf_i29_speedway`, append the zip's `server/data_track_params_vf_i29_speedway.ini` to that file (section name = track folder name):

```ini
[vf_i29_speedway]
NAME=I-29 Speedway
LATITUDE=41.024167
LONGITUDE=-95.832778
TIMEZONE=America/Chicago
```

  Or run `python server/add_track_params.py "<server root>"` (idempotent, keeps a `.bak`, refuses `system/data`). Leave the shared `system/data/data_track_params.ini` (server or game) untouched.
- **Alternative:** in `cfg/extra_cfg.yml` set `IgnoreConfigurationErrors:` → `MissingTrackParams: true` (time then runs in UTC; not usable with LiveWeatherPlugin).

**Checksum failed when joining?** `data_track_params.ini` is not checksummed, but the track's `surfaces.ini`, `models*.ini` and `*.kn5` are. Install the identical v1.x release on server and client, delete any old `zw_rpm` or stale `vf_i29_speedway` folders first, then restart the server.

## License
Apache License 2.0. Copyright 2026 vybesforge. See `LICENSE` and `NOTICE`. The original track was shared on condition that it stays open source. The Vybes Forge name and logo are trademarks and are not licensed.

## Credits
Based on zwiss's *Raceway Park of the Midlands* v0.9 (with sections by Fanapryde), extensively rebuilt and expanded by Vybes Forge. Some original assets remain. Earlier versions of this track by Porsche Guy, Bud Lucas & Andy55 and derDumeklemmer served as inspiration.

Data sources: USGS 3DEP lidar, USDA NAIP imagery, © OpenStreetMap contributors (ODbL), and CC0 textures from ambientCG and Poly Haven.

See `CREDITS.md` for full attribution.
