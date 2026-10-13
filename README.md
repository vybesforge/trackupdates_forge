# I-29 Speedway for Assetto Corsa

An open-source Assetto Corsa track of **I-29 Speedway** (formerly Raceway Park of the Midlands / Mid America Motorplex) in Pacific Junction, Iowa.

## Features
- Two layouts: **Long Course** (`main`, 3.644 km) and **Short Course** (`short`, 2.380 km), both with AI lines and 36 pit boxes.
- Elevation re-draped to real USGS lidar ground.
- 1/8-mile drag strip with a reactive two-lane tree. It runs on the pole with CSP; without CSP, the bundled Python app shows it on the monitor.
- Paddock, north extension roads to the fuel stations and US-34, and night lights (CSP).

## Install
Download the release zip from `release/`. Unzip it into your Assetto Corsa root folder, or drag it onto Content Manager. It installs `content/tracks/vf_i29_speedway/` and the optional `apps/python/i29_dragtree/` app. Custom Shaders Patch (0.2.x) is recommended, but the track also runs in vanilla AC.

If you have an old `content/tracks/zw_rpm` install, delete it first. If you clone this repo instead, you need Git LFS (`git lfs pull`), because the large files are stored in LFS. See `INSTALL_AGENT.md` for a scripted install.

## License
Apache License 2.0. Copyright 2026 vybesforge. See `LICENSE` and `NOTICE`. The original track was shared on condition that it stays open source. The Vybes Forge name and logo are trademarks and are not licensed.

## Credits
Based on zwiss's *Raceway Park of the Midlands* v0.9 (with sections by Fanapryde), extensively rebuilt and expanded by Vybes Forge. Some original assets remain. Earlier versions of this track by Porsche Guy, Bud Lucas & Andy55 and derDumeklemmer served as inspiration.

Data sources: USGS 3DEP lidar, USDA NAIP imagery, © OpenStreetMap contributors (ODbL), and CC0 textures from ambientCG and Poly Haven.

See `CREDITS.md` for full attribution.
