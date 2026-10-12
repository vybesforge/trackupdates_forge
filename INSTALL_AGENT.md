# I-29 Speedway (zw_rpm) — install instructions for an automation agent

Goal: install this Assetto Corsa track from GitHub so the user only has to launch it.

## Source
- Repo: https://github.com/vybesforge/trackupdates_forge
- Branch: `i29-speedway`
- Track folder in repo: `zw_rpm/`
- Large files (`.kn5`, `.dds`, `.fbx`, `.png`, `.jpg`, `.ai`) are stored with **Git LFS**. A plain "Download ZIP" from GitHub gives LFS pointer files, NOT the real data. Use git + git-lfs.

## Prerequisites (Windows VR/gaming PC)
1. Git for Windows (includes git-lfs): `winget install --id Git.Git -e`
2. `git lfs install`
3. Assetto Corsa installed (Steam). Default path:
   `C:\Program Files (x86)\Steam\steamapps\common\assettocorsa`
   If not there, read Steam library folders from
   `C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf` and look for `steamapps\common\assettocorsa`.
4. Recommended: Content Manager + Custom Shaders Patch (CSP) 0.2.x or newer (grass FX, ext_config).

## Install (PowerShell)
```powershell
$AC = "C:\Program Files (x86)\Steam\steamapps\common\assettocorsa"   # adjust if needed
$Work = "$env:USERPROFILE\trackupdates_forge"
git lfs install
if (Test-Path $Work) { git -C $Work fetch origin; git -C $Work checkout i29-speedway; git -C $Work pull; git -C $Work lfs pull }
else { git clone --branch i29-speedway https://github.com/vybesforge/trackupdates_forge.git $Work; git -C $Work lfs pull }

# Verify LFS actually downloaded (main kn5 must be ~240 MB, not ~130 bytes)
$kn5 = Get-Item "$Work\zw_rpm\zw_rpm.kn5"
if ($kn5.Length -lt 10MB) { throw "LFS files not downloaded; run git lfs pull" }

# Back up any existing install, then copy
$Dest = "$AC\content\tracks\zw_rpm"
if (Test-Path $Dest) { Rename-Item $Dest "zw_rpm.bak_$(Get-Date -Format yyyyMMdd_HHmmss)" }
Copy-Item "$Work\zw_rpm" $Dest -Recurse
```

## Verify
- `$Dest\models_main.ini` and `models_short.ini` exist, and `zw_rpm_own.kn5` is present.
- `$Dest\ui\main\ui_track.json` and `$Dest\ui\short\ui_track.json` exist.
- In Content Manager → Drive → Track, "Raceway Park of the Midlands" shows two layouts: main (3.590 km) and D Course (2.380 km). If it doesn't appear, restart Content Manager.

## Update later
Re-run the Install block; it pulls the latest branch and replaces the track (old copy kept as `zw_rpm.bak_*`).

## Uninstall / roll back
Delete `$AC\content\tracks\zw_rpm` and rename the newest `zw_rpm.bak_*` back to `zw_rpm` if desired.

## Hand-off to the user (what to test)
1. Load each layout once in practice (VR).
2. Curbs should NOT trigger cuts; four wheels on grass SHOULD (server race).
3. Short layout: sector 1/2 and lap timing work.
4. VR2 surfaces: tent paddock feels gravel (slow, dusty, no flag); access roads outside the track look like jointed concrete; grass runs to the track edge at corners (no brick/cobble look).
5. Visual check: larger timing tower (~15x10 m), brake boards 3/2/1, marshal hut, grandstands with closed risers, flagpole, Poly Haven tree billboards, armco/tire/tent specular, ground blending, water, props.
6. Short-course main straight vs. real drag strip position.
Report any issue back to the user's Grok Bot.

## Credits / license
See README.md, CREDITS.md, LICENSE. Base: zwiss "Raceway Park of the Midlands" v0.9 (used with permission, open-source condition); sections/logo Fanapryde. Replacement textures CC0 / public domain (ambientCG, USDA NAIP) or made for this project.
