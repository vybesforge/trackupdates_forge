# Provenance audit at 39c3beb (VR10) (zwiss v0.9 original vs this project)
Re-run 2026-10-12 at 39c3beb. The previous run was at b004057; its numbers are given in brackets as [was …]. The script reproduces the b004057 numbers exactly (`PROV_NEW=<dir>/zw_rpm/` runs it on another checkout).
Script: `tools/provenance_audit.py`. It compares every shipped kn5 mesh, texture blob and data file with `original/zwiss_rpotm_v0.9`.

Rules:
- Meshes are matched by name. Each one is classed by whether its position/index data and its material/textures are byte-identical to the original.
- Triangle counts are as shipped: they include the triangles that the lidar refinement added to zwiss meshes.
- "Visual" means rendered meshes. "Physics" means meshes whose names start with a digit. A mesh like `1GRASS` counts in both.

## 1. Visual triangles (857,448 [was 640,332])
| class | tris | % |
|---|---:|---:|
| zwiss, unchanged | 1,417 | 0.2 [0.3] |
| zwiss, re-draped only (same material/textures, heights moved) | 60,619 | 7.1 [9.4] |
| zwiss, retextured only | 1,654 | 0.2 [0.5] |
| zwiss, re-draped + retextured | 291,964 | 34.1 [45.4] |
| zwiss 1GRASS, refined + split + re-draped (VR10: extension re-drape refined it further) | 226,306 | 26.4 [16.3] |
| zwiss geometry copied into our files (people, overlays) | 5,424 | 0.6 [0.8] |
| fully ours (own models, extension, drag strip/tree/start line, tents, props, faces, hole fills) | 270,064 | 31.5 [27.3] |

## 2. Physics triangles (654,286 [was 440,770])
| class | tris | % |
|---|---:|---:|
| zwiss, unchanged | 0 | 0 [0] |
| zwiss, re-draped (roads, walls, pits, curbs, concrete, drag strip) | 189,991 | 29.0 [43.1] |
| zwiss 1GRASS, refined + split + re-draped | 226,306 | 34.6 [23.7] |
| zwiss geometry copied (1SCUT_hairpin) | 3,865 | 0.6 [0.9] |
| fully ours (extension roads/lots/grass, drag exits, launch bands, paddock gravel, hole fills) | 234,124 | 35.8 [32.3] |

The zwiss triangle counts barely changed. The shares moved because VR10 added geometry: the extension re-drape refined the grass and the extension meshes, and the hole fills, faces and start line are new.

## 3. Textures (unique by content: 224 [219], 302 MB)
| origin | count | MB |
|---|---:|---:|
| zwiss original (byte-identical) | 66 [66] | 62.2 |
| CC0 / public-domain third party (ambientCG, Poly Haven, USDA NAIP; per docs/assets.csv) | 55 [55] | 185.6 |
| ours, project-made (procedural, branding, signs, own-model maps; VR10 +5 solid colours) | 103 [98] | 54.4 |

Caveat: some own-model textures processed from ambientCG sources have no `assets.csv` row, so they are counted under "ours".

## 4. Data files (track folder, excluding kn5: 49; plus the app: 3)
- **zwiss, unchanged (37):** cameras ×4/layout, sections.ini (Fanapryde), ideal_line.ai, groove, lighting, map.ini, map.png, crew, audio, overlays, semaphore, ui images, ZWISS.txt.
- **Modified by us (11, unchanged count; VR10 only re-heighted fast_lane.ai):**
  - fast_lane/pit_lane.ai ×2 layouts (regenerated geometrically from zwiss's seed lines)
  - surfaces.ini ×2
  - ui_track.json ×2
  - models_main/short.ini
  - extension/ext_config.ini
- **New (1 + 3):** extension/drag_tree.lua, and apps/python/i29_dragtree (3 files).

## 5. Headline (visual triangles)
- **Original zwiss content unchanged: 7.2 % [9.7 %].** This counts byte-identical meshes (0.2 %) plus meshes that were only re-draped (7.1 %).
  - Strictly byte-identical it is 0.2 % visual and 0 % physics.
- **Ours or substantially modified: 92.8 % [90.3 %].** This is new geometry 31.5 % + retextured zwiss 34.3 % + re-triangulated grass 26.4 % + copied parts 0.6 %.
  - Physics: 35.8 % ours + 0.6 % copied + 34.6 % re-triangulated = **71.0 % [56.9 %]**. The remaining 29.0 % is zwiss geometry that was only re-draped.
- Even where it is modified, the track's layout, the road and wall placement, the buildings and the overall scene are still zwiss's work, and zwiss's credit and open-source condition apply (see NOTICE / CREDITS.md).

## 6. Lineage & inspirations
See CREDITS.md, "Lineage & inspirations", for the full chain and source URLs. Checked by hash on 2026-10-12:
- **CNDS 2024 (Geronimo Designs / MoxyShredz / Temple Productions) is derived from zwiss v0.9:**
  - 108 of its 165 textures (126.6 of 248.8 MB) are byte-identical to zwiss's.
  - 103 meshes (2,562 tris, the bushes) have zwiss-identical geometry.
  - 361 node names are shared, including zwiss's physics names (`1ROAD_001..010`, `1PITS*`, `1DRAGstrip`, `AC_PIT_*`).
  - 12 data files are identical (sections.ini, surfaces.ini, map.ini/map.png, groove, lighting, …).
- **No CNDS-only content ships:**
  - 0 of the 57 CNDS-only textures (kn5 textures plus the 161 files in its `unpacked…/texture` folder) are in our kn5s.
  - 0 CNDS-only mesh geometries (vertex-position hash at 1 cm).
  - 0 CNDS-only node names.
  - 0 CNDS-only data files.
  - Limitation: the geometry of 4 CNDS kn5 files (v6 format with trailing data: `_physical`, `cnds_physics`, `_gp`, `cnds_objects`) could not be parsed and so was not hash-compared. Their textures were checked. No project tool ever reads CNDS files.
- **Porsche Guy's SCGT original and the rF, GTL/GTR2 and AC (Dumeklemmer 2015) conversions:** none of their files are in this repo or the originals folder. Their only trace here is indirect: zwiss started from "the outline of the main layout".
