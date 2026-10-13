# I-29 Speedway v1.0.0

This is a free, open-source Assetto Corsa track. It is a recreation of I-29 Speedway (formerly Raceway Park of the Midlands) near Pacific Junction, Iowa.

It is built on zwiss's *Raceway Park Of The Midlands* v0.9 and released under Apache-2.0 (see LICENSE, NOTICE and CREDITS.md). The full change log is in `docs/CHANGES.md` in the repository.

## Install
Unzip into your Assetto Corsa root folder, or drag the zip onto Content Manager. This installs:
- `content/tracks/vf_i29_speedway/`: the track. Layouts: **I-29 Speedway Long Course** (`main`, 3.644 km) and **I-29 Speedway Short Course** (`short`, 2.380 km). The track folder id stays `vf_i29_speedway`, so existing installs and servers keep working.
- `apps/python/i29_dragtree/`: an optional drag tree and timeslip app. It works without CSP; enable it in the app bar.

Custom Shaders Patch is recommended (0.2.x). It enables the live drag tree on the pole, the night lights and the emissive bulbs. The track loads and drives in vanilla AC too.

## Highlights
- **Elevation:** re-draped to the USGS 3DEP 1 m lidar. The road follows the real ground, with typically ±0.14 m change vs v0.9 and up to about 0.4 m. Visual and physics surfaces stay identical, and there are no steps at the joins.
- **1/8-mile drag strip:**
  - Launch-grip bands and rubber.
  - A reactive two-lane sportsman tree with pre-stage/stage beams, red lights, RT, 60 ft, 330 ft, 1/8 ET and trap mph.
  - Real exit turnoffs and a return road.
  - With CSP the tree runs on the pole (also in VR). Without CSP, the vanilla Python app shows it in a window on the monitor (not in the headset).
- **Layouts:** Long Course with cut detection through the short-course hairpin. Short Course with T1/T5 transition bumps.
- **AI:** regenerated and validated AI lines for both layouts.
- **Pits and paddock:** 36 pit boxes and spawns behind the green paddock building. Gravel tent paddock, Vybes Forge tents, figures, contact shadows.
- **North extension:** 190th/188th St to the fuel stations and the US-34 four-way stop, now also on the real lidar ground (road grades under 6 %, smooth joins).
- **Night:** CSP pit, paddock and drag-strip lights.
- **Drag strip line:** a painted start line now sits exactly on the stage beam, with pre-stage ticks 7 in behind it.
- **Figures:** the two paddock figures have faces (eyes, brows, nose, mouth, ears), better hair, and one wears a cap.
- **Surfaces:** curbs are valid, grass flags cuts, and the paddock is gravel.

## Known limitations / please test
- Fixed in this build: cars fell through the grass after the lidar re-drape (one oversize grass collision mesh). It is now split, and the old holes (ponds, the railway-embankment cut beside the extension road, under I-29) are filled. Please confirm in game.
- The AI lines are geometric, not recorded from driving. Braking points are estimates.
- Drag tree: the app's VR visibility (vanilla AC shows app windows on the monitor only), the CSP car-position API, and online opponents are all untested in game.
- The higher mesh density after the lidar re-drape needs a VR frame-rate check.
- The paddock now has real slope (0.4–1.0 % at the 36 spawns, measured). Check that cars sit still in the boxes.
- North extension re-draped in this build (up to about 7 m of lift). Drive it for steps, bumps and floating or buried props.

## Screenshots
Preview renders are in `docs/previews/`: `vr9_lidar_delta.png` (lidar height change), `vr9_tree_lanes.png` (two-lane tree), `vr7_ai.png` / `vr7_long.png` (AI lines and Long Course), `vr10_people_blue.png` / `vr10_people_grey.png` (figures), `vr10_stageline.png` (start line), `vr10_ext_delta.png` (extension re-drape), `vr6_night_drag.png`, `drag_launch.png`.
