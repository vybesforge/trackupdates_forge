# I-29 Speedway for Assetto Corsa

An open-source Assetto Corsa track of **I-29 Speedway** (formerly Raceway Park of the Midlands / Mid America Motorplex) in Pacific Junction, Iowa.

## Features
- Two layouts: **Long Course** (`main`, 3.644 km) and **Short Course** (`short`, 2.380 km), both with AI lines and 36 pit boxes.
- Elevation re-draped to real USGS lidar ground.
- 1/8-mile drag strip with a reactive two-lane tree. It runs on the pole with CSP; without CSP, the bundled Python app shows it on the monitor.
- Paddock, north extension roads to the fuel stations and US-34, and night lights (CSP).

## What's new in v1.0.2
- Server fix: ships a `data_track_params.ini` entry for `vf_i29_speedway` (see *Running a server*). Fixes the dedicated-server / Content Manager server crash "No track params found for vf_i29_speedway".

v1.0.1: rebuilt replay cameras (3 sets per layout) and restored dirt/gravel textures.

## Install
Download `I-29_Speedway_v1.0.2.zip` (current release **v1.0.2**) from the GitHub Releases page or from `release/`. Unzip it into your Assetto Corsa root folder, or drag it onto Content Manager. It installs `content/tracks/vf_i29_speedway/` and the optional `apps/python/i29_dragtree/` app. Custom Shaders Patch (0.2.x) is recommended, but the track also runs in vanilla AC.

If you have an old `content/tracks/zw_rpm` install, delete it first. If you clone this repo instead, you need Git LFS (`git lfs pull`), because the large files are stored in LFS. See `INSTALL_AGENT.md` for a scripted install.

## Running a server
The AC dedicated server (and Content Manager's server) needs an entry for the track in `data_track_params.ini`, otherwise it stops with `No track params found for vf_i29_speedway`. This is required since the track folder was renamed from `zw_rpm`. Do **not** replace the whole file; append the snippet from the zip's `server/data_track_params_vf_i29_speedway.ini` (also in this repo under `server/`):

```ini
[vf_i29_speedway]
NAME=I-29 Speedway
LATITUDE=41.024167
LONGITUDE=-95.832778
TIMEZONE=America/Chicago
```

Append it to the end of:
- `<server>/system/data/data_track_params.ini` (dedicated server), and
- `<Assetto Corsa>/system/data/data_track_params.ini` (game copy, used when hosting locally with Content Manager).
- AssettoServer users: `<server>/cfg/data_track_params.ini`.

Or run the idempotent helper, which only appends if the entry is missing and keeps a `.bak`:
`python server/add_track_params.py "<server>/system/data/data_track_params.ini" "<AC>/system/data/data_track_params.ini"`

## License
Apache License 2.0. Copyright 2026 vybesforge. See `LICENSE` and `NOTICE`. The original track was shared on condition that it stays open source. The Vybes Forge name and logo are trademarks and are not licensed.

## Credits
Based on zwiss's *Raceway Park of the Midlands* v0.9 (with sections by Fanapryde), extensively rebuilt and expanded by Vybes Forge. Some original assets remain. Earlier versions of this track by Porsche Guy, Bud Lucas & Andy55 and derDumeklemmer served as inspiration.

Data sources: USGS 3DEP lidar, USDA NAIP imagery, © OpenStreetMap contributors (ODbL), and CC0 textures from ambientCG and Poly Haven.

See `CREDITS.md` for full attribution.
