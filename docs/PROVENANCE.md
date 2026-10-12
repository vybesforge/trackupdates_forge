# Provenance audit at b004057 (zwiss v0.9 original vs this project)
Script: `tools/provenance_audit.py`. It compares every shipped kn5 mesh, texture blob and data file with `original/zwiss_rpotm_v0.9`.

Rules:
- Meshes are matched by name. Each one is classed by whether its position/index data and its material/textures are byte-identical to the original.
- Triangle counts are as shipped: they include the triangles that the lidar refinement added to zwiss meshes.
- "Visual" means rendered meshes. "Physics" means meshes whose names start with a digit. A mesh like `1GRASS` counts in both.

## 1. Visual triangles (640,332)
| class | tris | % |
|---|---:|---:|
| zwiss, unchanged | 2,051 | 0.3 |
| zwiss, re-draped only (heights moved ≤ ~0.4 m on pavement) | 59,985 | 9.4 |
| zwiss, retextured only | 3,000 | 0.5 |
| zwiss, re-draped + retextured | 290,618 | 45.4 |
| zwiss 1GRASS, refined 4,006 → 104,526 + split + re-draped | 104,526 | 16.3 |
| zwiss geometry copied into our files (people, overlays) | 5,424 | 0.8 |
| fully ours (own models, extension, drag strip/tree, tents, props, hole fills) | 174,728 | 27.3 |

## 2. Physics triangles (440,770)
| class | tris | % |
|---|---:|---:|
| zwiss, unchanged | 0 | 0 |
| zwiss, re-draped (roads, walls, pits, curbs, concrete, drag strip) | 189,991 | 43.1 |
| zwiss 1GRASS, refined + split + re-draped | 104,526 | 23.7 |
| zwiss geometry copied (1SCUT_hairpin) | 3,865 | 0.9 |
| fully ours (extension roads/lots/grass, drag exits, launch bands, paddock gravel, hole fills) | 142,388 | 32.3 |

## 3. Textures (unique by content: 219, 302 MB)
| origin | count | MB |
|---|---:|---:|
| zwiss original (byte-identical) | 66 | 62.2 |
| CC0 / public-domain third party (ambientCG, Poly Haven, USDA NAIP; per docs/assets.csv) | 55 | 185.6 |
| ours, project-made (procedural, branding, signs, own-model maps) | 98 | 54.4 |

Caveat: some own-model textures processed from ambientCG sources have no `assets.csv` row, so they are counted under "ours".

## 4. Data files (track folder, excluding kn5: 49; plus the app: 3)
- **zwiss, unchanged (37):** cameras ×4/layout, sections.ini (Fanapryde), ideal_line.ai, groove, lighting, map.ini, map.png, crew, audio, overlays, semaphore, ui images, ZWISS.txt.
- **Modified by us (11):**
  - fast_lane/pit_lane.ai ×2 layouts (regenerated geometrically from zwiss's seed lines)
  - surfaces.ini ×2
  - ui_track.json ×2
  - models_main/short.ini
  - extension/ext_config.ini
- **New (1 + 3):** extension/drag_tree.lua, and apps/python/i29_dragtree (3 files).

## 5. Headline (visual triangles)
- **Original zwiss content unchanged: 9.7 %.** This counts zwiss meshes that are byte-identical (0.3 %) or only re-draped to lidar heights with the same shape, textures and triangulation (9.4 %).
  - Strictly byte-identical it is 0.3 % visual and 0 % physics.
- **Ours or substantially modified: 90.3 %.** This counts new geometry (27.3 %), retextured zwiss meshes (45.9 %), re-triangulated grass (16.3 %) and copied/reworked zwiss parts (0.8 %).
  - On physics triangles it is 33.2 % ours + 23.7 % re-triangulated = 56.9 %. The remaining 43.1 % is zwiss geometry that was only re-draped.
- Even where it is modified, the track's layout, the road and wall placement, the buildings and the overall scene are still zwiss's work, and zwiss's credit and open-source condition apply (see NOTICE / CREDITS.md).
