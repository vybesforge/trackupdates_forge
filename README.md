# I-29 Speedway (Assetto Corsa) — open-source update

Goal: an open, maintained Assetto Corsa track for **I-29 Speedway** (formerly Raceway Park of the Midlands / Mid America Motorplex), 19340 Jesup Ave, Pacific Junction, IA (41°01′27″N 95°49′58″W).

## Lineage
1. Porsche Guy — GTR2 / Sports Car GT original
2. Dumeklemmer — 2015 Assetto Corsa port
3. zwiss — 2023 scratch rebuild in 3ds Max, v0.9 (OverTake.gg #58166) — **primary base** (imported unmodified in `vf_i29_speedway/`)
4. Geronimo Designs / MoxyShredz / Temple Productions — CNDS Raceway Park 2024 remodel (v3.0) — **reference only**

Reuse approved by the original authors on condition the result stays open source (per Dylan; get written confirmation into `docs/permissions/`).

## Planned fixes over v0.9
Real elevation (USGS 3DEP 2020 lidar), corrected curbs, working cut detection, highway traffic, rain/grass FX, renamed layout/branding.

## Borrowed / original assets
In the spirit of zwiss's own `ZWISS.txt` credits ("Fanapryde: sections file and logo. I did borrow a few objects and textures left and right…"), these parts of this release are **not ours**. They come from zwiss's *Raceway Park Of The Midlands* v0.9 (2023) and are shipped with thanks:

**zwiss (Raceway Park Of The Midlands v0.9):**
- Base layout, terrain and building meshes: `vf_i29_speedway.kn5` (track, terrain, buildings, pits/paddock, drag strip, grandstand shells), `vf_i29_speedway_physical.kn5`, `vf_i29_speedway_gp.kn5`, `vf_i29_speedway_sh.kn5`, and the `zw_vegetation.kn5` placement. The track was re-draped on lidar, stitched and extended by this project, but the modelling is zwiss's.
- Textures: the 68 zwiss v0.9 textures restored in VR11b (asphalt, grass, road masks/lines, kerbs, armco, fences, gates, trusses, tents, paddock/tower/factory walls, signs, drag board, horizon/tree line, water normals, etc.). They are byte-identical to zwiss's originals.
- Cameras (`cameras*.ini`, `camera_facing.ini`), the AI seed lines and the layout outline, the marshal figure, overlays and other data files carried over from v0.9.

**Fanapryde (via zwiss):** `sections.ini` and the MAM track logo/banner (`logomam.dds`).

**Earlier lineage:** Porsche Guy (layout outline, via zwiss's rebuild), Bud Lucas & Andy55, derDumeklemmer. No files from them are used directly.

**Gravel / dirt textures:** `own_gravel*.dds`, `concrete_seams.dds` and `Muld Detailne.dds` are the pre-VR11 (VR2-era) versions: ambientCG CC0 materials with project edits. They are listed here because VR11b put them back, not because they are zwiss's.

zwiss's own borrowed bits ("a few objects and textures left and right") are not separately documented upstream. See `docs/PROVENANCE.md` and `docs/assets.csv` for the per-texture audit, and `CREDITS.md` for full attribution.

## License
Apache License 2.0. Copyright 2026 vybesforge. See `LICENSE` and `NOTICE`.

This track is based on zwiss's *Raceway Park Of The Midlands* v0.9, which was shared on condition that it stays open source. It also includes:
- © OpenStreetMap contributors data (ODbL)
- USGS 3DEP and USDA NAIP public-domain data
- CC0 textures from ambientCG and Poly Haven

The CNDS 2024 remodel was used for reference only. See `CREDITS.md` for full attribution. The Vybes Forge name and logo are trademarks and are not licensed.
