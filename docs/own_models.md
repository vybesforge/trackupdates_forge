# Own models (branch assets/own-models)
Built procedurally in Blender 4.2.3 (headless) by `tools/own_models_blender.py`; sources `assets_src/<name>/<name>.blend|.fbx|_mesh.json`; textures `assets_src/textures/` (ambientCG CC0 + procedural, DDS DXT1 with mips) via `tools/own_models_textures.py`. Reference stills from Dylan's video in `docs/reference/` (tower clearly visible at 16 s, 107 s).

| model | tris | parts / materials | notes |
|---|---|---|---|
| tower | 848 | body, cab (window band), roof slab, windows, external switchback stair + rails, antenna; own_tower_paint (NM), own_tower_glass, own_galv | light-blue, 7×5 m, roof 9.9 m, antenna 13.3 m. Old zwiss tower footprint is ~10×15 m → size is an estimate from footage; check vs reality |
| grandstand (module) | 888 | 8-row aluminium bleacher 20×6 m, frame, rails; own_alu, own_galv | 4 modules replace Grandstand_001 |
| brake boards | 36 each | 2 posts + 1.2×0.9 m board; atlas own_boards (3 \| 2 \| 1) | '1' assumed (not confirmed in notes). Visual only, no collision |
| hut | 100 | white 2.4×2.0 m hut, window/door, sloped awning on 2 poles | new (no single old node to replace) |
| flagpole | 128 (+flag ×2 sides) | 18 m tapered pole, 2.44×1.52 m flag (procedural US flag) | replaces whitepole_001 + flag_001 |

## Integration (done, no ksEditor needed)
- New `zw_rpm/zw_rpm_own.kn5` written by `tools/kn5write.py` (KN5 v5: 9 textures, 8 materials cloned from zwiss ksPerPixel/ksPerPixelNM property sets, 26 meshes, 4,800 tris, LOD out 600–1500 m). Re-parsed OK with kn5info/kn5patch.
- Added as `[MODEL_4]` in `models_main.ini` and `models_short.ini`.
- Old meshes hidden in `zw_rpm.kn5` by clearing castShadows/isVisible/isRenderable flags (23 nodes: tower_SUB0–8, tower_metal_SUB0–3, Grandstand_001_SUB0–3, Grandstand_001metal1–4, whitepole_001, flag_001). Backup `/workspace/rpotm/backup/zw_rpm.kn5.pre_own_models`.
- Placement/transforms: `docs/own_models_placement.csv` (AC coords, yaw about +Y; Blender→AC conversion (x,y,z)→(x,z,−y), v flipped).
- Fallback if anything misbehaves in game: import the FBX files in ksEditor (Windows), assign the same materials/DDS, export kn5.

## Needs in-game check (Dylan)
Scale/position of tower and stands vs. footage; brake-board distances (150/100/50 m before T5 entry at short-lane d=2019, 9 m left) and whether '1' exists; hut location (back straight, 14 m right); shading (normals/winding: verified CCW vs stored normals on zwiss meshes, same convention used); shadows; LODs; no z-fighting with leftover zwiss pieces (e.g. tower stair/door bits in other nodes, Drag_tent, drag_boards).
