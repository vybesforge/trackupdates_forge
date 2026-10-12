# I-29 Drag Tree (vanilla Assetto Corsa Python app)

Live two-lane sportsman tree and timeslip for the I-29 Speedway drag strip. No CSP needed.

**Install:** copy this folder to `<assettocorsa>/apps/python/i29_dragtree/`. Then enable *I-29 Drag Tree*, either in the in-game app bar (right edge of the screen) or in Content Manager under Settings > Assetto Corsa > Apps.

**Use:**
1. Drive to the drag strip, either through the paddock or from the drag exits.
2. Line up in the left or right lane and roll forward slowly. PRE-STAGE lights first, then STAGE (stage beam at z −347.5).
3. When both lanes are staged for 1 s, the tree drops: three ambers 0.5 s apart, then green. If only one lane is occupied it drops for that lane alone. If the other lane is occupied but not staged, it runs solo after 8 s.
4. Leaving before green gives a red light.

The timeslip shows reaction time, 60 ft, 330 ft, the 1/8-mile ET and the trap speed (mph over 594–660 ft).

**Notes:**
- Times use sim time. A paused game pauses the tree.
- On a multiplayer server every connected car is tracked, so a remote car in the other lane can be your opponent.
- The front-tyre contact points come from `acsys.CS.TyreContactPoint`. If that call is unavailable, the app falls back to the car position plus 1.3 m.
- **VR:** vanilla AC draws Python app windows only on the desktop monitor, not inside the headset. VR players should use the physical tree on the pole, which needs CSP (`extension/drag_tree.lua`, same logic) and shows the same results as a message. CSP can also show apps in VR. *This has not been tested in a headset.*
