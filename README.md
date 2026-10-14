# I-29 Speedway for Assetto Corsa

An open-source Assetto Corsa track of **I-29 Speedway** (formerly Raceway Park of the Midlands / Mid America Motorplex) in Pacific Junction, Iowa.

## Features
- Two layouts: **Long Course** (`main`, 3.644 km) and **Short Course** (`short`, 2.380 km), both with AI lines and 36 pit boxes.
- Elevation re-draped to real USGS lidar ground.
- 1/8-mile drag strip with a reactive two-lane tree. It runs on the pole with CSP; without CSP, the bundled Python app shows it on the monitor.
- Paddock, north extension roads to the fuel stations and US-34, and night lights (CSP).

## What's new in v1.0.4
- Fixes "checksum failed" for git-based installs: `.gitattributes` disables EOL conversion for all shipped files, so checkouts on any OS are byte-identical to the zip. Track files (`*.kn5`, `surfaces.ini`, `models*.ini`) are byte-identical to v1.0.3.
- `server/add_track_params.py` hardened: append-only, refuses a missing/empty target unless `--create`, refuses `system/data`; tests added.

v1.0.3: server docs corrected (AssettoServer `cfg/data_track_params.ini` only). v1.0.2: added the track params snippet. v1.0.1: rebuilt replay cameras (3 sets per layout) and restored dirt/gravel textures.

## Install
Download `I-29_Speedway_v1.0.4.zip` (current release **v1.0.4**) from the GitHub Releases page or from `release/`. Unzip it into your Assetto Corsa root folder, or drag it onto Content Manager. It installs `content/tracks/vf_i29_speedway/` and the optional `apps/python/i29_dragtree/` app. Custom Shaders Patch (0.2.x) is recommended, but the track also runs in vanilla AC.

If you have an old `content/tracks/zw_rpm` install, delete it first. If you clone this repo instead, you need Git LFS (`git lfs pull`), because the large files are stored in LFS. See [`INSTALL_AGENT.md`](INSTALL_AGENT.md) for scripted client and server installs (release zip + SHA-256 check, clean replace, server setup, repair of earlier system/data edits).

## Checksums / installing from git
Install from the release zip. AC checksums `*.kn5`, `surfaces.ini` and `models*.ini` byte-for-byte; a Windows git checkout with `core.autocrlf=true` (before the v1.0.4 `.gitattributes` fix) converted `.ini` files to CRLF and caused "checksum failed" online. If you copy from git, use a fresh clone of main/v1.0.4 or set `core.autocrlf false`. MD5s of all checksummed files are listed in `INSTALL_AGENT.md`.

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
