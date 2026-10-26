# I-29 Speedway (`vf_i29_speedway`) — install guide for automation agents

Current release: **v1.1.4** (exit soft-cut flush with the remaining exit cone; checksum changed: `vf_chicane.kn5`) · Repo: https://github.com/vybesforge/trackupdates_forge · Track folder id: `vf_i29_speedway` (was `zw_rpm` before the rename).

## HARD RULES (read first)
1. **Never modify, create or delete anything under the game's or the server's `system/` folder** — this includes `system/data/*`, `system/data/data_track_params.ini` and the global `system/data/surfaces.ini`. These files are shared by all tracks.
2. **Write only to these targets:**
   - Client: `<AC>/content/tracks/vf_i29_speedway`, `<AC>/apps/python/i29_dragtree`, and removing an old `<AC>/content/tracks/zw_rpm` (back it up first).
   - Server: `<server>/content/tracks/vf_i29_speedway`; and **AssettoServer only**: `<server>/cfg/data_track_params.ini` (append our section) **or** `<server>/cfg/extra_cfg.yml` (`MissingTrackParams`).
   - Your own work/download folder (e.g. `%TEMP%`, `$HOME/i29_install`).
3. Backups go next to the target as `<name>.bak_<timestamp>`. Never merge a new track over an old one — always clean-replace (checksums must match).
4. If anything seems to require a change outside the list above (system files, other tracks, CM/CSP settings files), **stop and report to the user** instead of doing it.

## Source (prefer the release zip)
- **Preferred:** GitHub Release v1.1.4 — https://github.com/vybesforge/trackupdates_forge/releases/tag/v1.1.4
  - Asset: `I-29_Speedway_v1.1.4.zip` (~214 MB)
  - SHA-256: `0e08b04cd74f202402456919ba30c98daca94af5d1a7f1cd455c8557a90b4a79` — **verify before installing; abort on mismatch.** Do not reuse the v1.1.3 hash `967ae33a41a6e6db39f0c978220f09e3a6a46af20544b6eeb92ca8bb90f3fe27` or the v1.1.2 hash `b57716140e1c2a11798a69889655723f166868c32b2534b272480750e4c8d59c`.
  - Zip layout: `content/tracks/vf_i29_speedway/`, `apps/python/i29_dragtree/`, `server/` (track-params snippet + `add_track_params.py`), `I-29_Speedway_docs/`.
- **Alternative:** git + Git LFS from `main` or tag `v1.1.4` (not old feature branches). GitHub's "Download ZIP" of the repo contains LFS pointer files, not real data — do not use it.
  ```
  git lfs install
  git clone --branch v1.1.4 https://github.com/vybesforge/trackupdates_forge.git && cd trackupdates_forge && git lfs pull
  ```
  Then use `vf_i29_speedway/`, `apps/python/i29_dragtree/` and `server/` from the clone in place of the zip folders below. Sanity check: `vf_i29_speedway/vf_i29_speedway.kn5` must be > 10 MB (not a ~130-byte pointer).

## Byte-exact files and checksums (v1.1.4)
AC compares `*.kn5`, `surfaces.ini` and `models*.ini` byte-for-byte between server and client. **Install only from the release zip.** If you must copy from a git worktree, it must be a fresh clone made after the `.gitattributes` fix (main ≥ v1.0.4, all shipped files `-text`) or a clone with `git config core.autocrlf false`; older Windows checkouts with `core.autocrlf=true` turned `.ini` files into CRLF and caused "checksum failed". v1.1.4 files (the old `zw_*.kn5` were renamed `vf_*.kn5`; delete any `zw_*.kn5` left in an install):

| File (in `content/tracks/vf_i29_speedway/`) | Bytes | MD5 |
|---|---|---|
| `chicane/data/surfaces.ini` | 3941 | `12434e5cc5ef0421f1d0822a0bfda332` |
| `main/data/surfaces.ini` | 3800 | `a218d5ec21d093db03f2aec901ccd9b0` |
| `models_chicane.ini` | 1159 | `df274993df614c2f766d3cfde91a2c14` |
| `models_main.ini` | 1097 | `887cb7057faa89dc90e1a2612e0ee8ad` |
| `models_short.ini` | 1031 | `488a75318f91e797a72952bd983cc309` |
| `short/data/surfaces.ini` | 3437 | `4cf76a43508412ec49498cca1404c0dd` |
| `vf_chicane.kn5` | 109772 | `aa17ec5a2c2445c2af679c2ebed9d1f1` |
| `vf_dragcol.kn5` | 244144 | `7094d086db4c3c9632931b1077098645` |
| `vf_dragexit.kn5` | 14370948 | `532c29b2a07b0cf431c02ef3118330f9` |
| `vf_draglaunch.kn5` | 14070895 | `40e0dbe54c1982fa6638f214e978327b` |
| `vf_dragtents.kn5` | 885449 | `b8a0890e0984c1d4acb7828e69578547` |
| `vf_ext.kn5` | 43526931 | `45407bd30f22529814b219bd63636633` |
| `vf_i29_speedway.kn5` | 257020369 | `d35162d917c35c6c2544973c216fa382` |
| `vf_i29_speedway_gp.kn5` | 11964180 | `11e896b8a4dec8555f14389593144c38` |
| `vf_i29_speedway_own.kn5` | 18682981 | `0972422525b33967ca3ad880048f8bc2` |
| `vf_i29_speedway_physical.kn5` | 24309908 | `e48d024b0e9dedb7b08506e57a8978ad` |
| `vf_i29_speedway_sh.kn5` | 1044980 | `311c2d8d5618bd82d2a19632ddbcca86` |
| `vf_roads.kn5` | 7500370 | `fb8b932368f4d0e0f0c36b3a39fe36f2` |
| `vf_ruts.kn5` | 99292 | `5938ed345eaf34ad7eeb120f09c91b51` |
| `vf_tents.kn5` | 12511265 | `e65c08493c2c8d10d2100fd0eae25f7c` |
| `vf_vegetation.kn5` | 48601289 | `187a2519fece1ae0be0afe087d62ee6f` |
| `vf_vr5.kn5` | 2798509 | `c95cf9de26f7ee0b9dae012dc9f00450` |
| `vf_vr6.kn5` | 4410323 | `9599c678dc7e811caa9fa919cec75b3a` |
| `vf_vr7_longcut.kn5` | 533884 | `de5e7a3b23eef128df59a091580fefa2` |
| `vf_westlot.kn5` | 6923075 | `3323fa8da2b5ca2cde061dfbedc3a5f6` |

Verify (PowerShell): `Get-FileHash -Algorithm MD5 <file>`; (Linux): `md5sum <file>`. Any mismatch → clean-reinstall from the zip.

## Client install (Windows, PowerShell)
Find AC: default `C:\Program Files (x86)\Steam\steamapps\common\assettocorsa`; otherwise search the paths in `C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf` for `steamapps\common\assettocorsa`.
```powershell
$ErrorActionPreference = "Stop"
$AC   = "C:\Program Files (x86)\Steam\steamapps\common\assettocorsa"   # adjust
$Ver  = "v1.1.4"
$Sha  = "0e08b04cd74f202402456919ba30c98daca94af5d1a7f1cd455c8557a90b4a79"
$Work = Join-Path $env:TEMP "i29_$Ver"; New-Item -ItemType Directory -Force $Work | Out-Null
$Zip  = Join-Path $Work "I-29_Speedway_$Ver.zip"
Invoke-WebRequest "https://github.com/vybesforge/trackupdates_forge/releases/download/$Ver/I-29_Speedway_$Ver.zip" -OutFile $Zip
if ((Get-FileHash $Zip -Algorithm SHA256).Hash.ToLower() -ne $Sha) { throw "SHA-256 mismatch - aborting" }
Expand-Archive $Zip -DestinationPath "$Work\x" -Force

$TS     = Get-Date -Format yyyyMMdd_HHmmss
$Tracks = "$AC\content\tracks"
# old zw_rpm folder -> backup (moved out of the way, not merged)
if (Test-Path "$Tracks\zw_rpm") { Rename-Item "$Tracks\zw_rpm" "zw_rpm.bak_$TS" }
# clean replace: back up existing track, then copy fresh
if (Test-Path "$Tracks\vf_i29_speedway") { Rename-Item "$Tracks\vf_i29_speedway" "vf_i29_speedway.bak_$TS" }
Copy-Item "$Work\x\content\tracks\vf_i29_speedway" "$Tracks\vf_i29_speedway" -Recurse
# optional vanilla drag-tree app
$App = "$AC\apps\python\i29_dragtree"
if (Test-Path $App) { Rename-Item $App "i29_dragtree.bak_$TS" }
Copy-Item "$Work\x\apps\python\i29_dragtree" $App -Recurse
```
Note: AC/CM list every folder in `content/tracks`, so a `*.bak_*` folder may appear as an extra track. After the user confirms the new install works, the backups can be deleted (ask first).

Verify:
- `$Tracks\vf_i29_speedway\vf_i29_speedway.kn5` > 10 MB; `models_main.ini`, `models_short.ini`, `models_chicane.ini`, `ui\main\ui_track.json`, `ui\short\ui_track.json`, `ui\chicane\ui_track.json` exist; each `ui_track.json` `"version"` = `1.1.4`.
- Content Manager shows three layouts: "I-29 Speedway Long Course" (`main`), "I-29 Speedway Short Course" (`short`), and "I-29 Speedway Long Course Chicane" (`chicane`).
- Recommended: Content Manager + CSP 0.2.x (lights, grass, reactive drag tree on the pole). Without CSP, enable the "I-29 Drag Tree" app.

## Server install (Linux and Windows)
The server needs the **same** track folder as the clients (it checksums `*.kn5`, `surfaces.ini`, `models*.ini`).
1. Download and verify the v1.1.4 zip exactly as above (Linux: `curl -LO <url> && sha256sum I-29_Speedway_v1.1.4.zip`; compare with the hash above).
2. Stop the server.
3. Clean replace the track:
   - Linux: `TS=$(date +%Y%m%d_%H%M%S); cd <server>/content/tracks && { [ -d vf_i29_speedway ] && mv vf_i29_speedway vf_i29_speedway.bak_$TS; true; } && cp -r <unzipped>/content/tracks/vf_i29_speedway .`
   - Windows: same as the client block, with `$Tracks = "<server>\content\tracks"` (no app copy needed).
   - If an old `zw_rpm` folder exists there, move it to `zw_rpm.bak_<ts>` too; point the server config (`TRACK=vf_i29_speedway`, `CONFIG_TRACK=main` or `short`) at the new id.
4. Track params:
   - **Vanilla acServer:** nothing to do.
   - **AssettoServer:** it reads only `<server>/cfg/data_track_params.ini`. Run `python <unzipped>/server/add_track_params.py "<server root>"` (appends `[vf_i29_speedway]` only if missing, keeps a `.bak`, refuses `system/data`). **Or** in `<server>/cfg/extra_cfg.yml` set
     ```yaml
     IgnoreConfigurationErrors:
       MissingTrackParams: true
     ```
     (time then runs in UTC; not compatible with LiveWeatherPlugin.)
5. Start the server. Verify: the log has no `No track params found for vf_i29_speedway`/missing-track-params error, and a client joins without "checksum failed".
6. Ensure server and clients have identical files — compare MD5 on both machines:
   - Linux: `cd <server>/content/tracks/vf_i29_speedway && md5sum *.kn5 main/data/surfaces.ini short/data/surfaces.ini models_*.ini`
   - Windows: `Get-ChildItem "$Tracks\vf_i29_speedway\*.kn5","$Tracks\vf_i29_speedway\models_*.ini","$Tracks\vf_i29_speedway\*\data\surfaces.ini" | Get-FileHash -Algorithm MD5`
   Any difference → clean-reinstall v1.1.4 on the side that differs, restart the server.

## Repair a previously modified install
If an earlier agent (or older instructions, v1.0.2) edited shared system files:
1. `<AC or server>/system/data/data_track_params.ini`: if a `.bak` from that edit exists, restore it (`data_track_params.ini.bak` → `data_track_params.ini`). Otherwise remove **only** the `[vf_i29_speedway]` section (its header and the following `NAME/LATITUDE/LONGITUDE/TIMEZONE` lines) and change nothing else.
2. Game installs: if other `system/` files may have been touched, suggest the user run Steam → Assetto Corsa → Properties → Installed Files → **Verify integrity of game files** (do not do it unasked).
3. Then do a clean client/server install as above.
4. Git checkouts made before v1.0.4 (or with `core.autocrlf=true`, the Windows default) can have CRLF-converted files that fail AC/server checksums. One-time fix inside the existing checkout:
   ```
   git config core.autocrlf false
   git rm --cached -r -q .
   git reset --hard
   ```
   Then verify the files against the release zip. Prefer installing from the release zip; do not copy a git worktree/checkout (with `.git`, `assets_src/`, `tools/`, etc.) into the AC folder.

## Update / uninstall
- Update: repeat the install with the new release tag and its published SHA-256.
- Uninstall: delete `content/tracks/vf_i29_speedway` (and `apps/python/i29_dragtree`); optionally rename the newest `*.bak_*` back. On AssettoServer, optionally remove our section from `cfg/data_track_params.ini`.

## Hand-off: what the user should test
1. Load both layouts in practice (VR frame rate OK, no falling through the world on grass, pit exit, north roads, ponds).
2. Cuts: curbs do not trigger cuts; four wheels on grass do (server race).
3. Short layout: sector and lap timing work.
4. Replay cameras: 3 camera sets per layout cycle correctly.
5. Dirt/gravel: tent paddock and dirt areas look and feel like gravel/dirt.
6. Drag strip: CSP pole tree (pre-stage/stage at the white line, ambers, green, red on jump, timeslip); without CSP the "I-29 Drag Tree" app does the same.
7. North extension: 190th/188th St, fuel stations, US-34 stop drivable without flags or steps.
8. Night (CSP): pit, paddock and drag-strip lights.
9. Online: server starts without track-params errors and clients join without checksum failure.
10. Long Course Chicane: both cone chicanes are across from each other on the west double-straight; driving the shortcut is off-track and the cone line is valid. On each exit the soft-cut edge sits on the innermost remaining cone.
Report issues back to the user.

## License
Apache License 2.0 (Copyright 2026 vybesforge); see `LICENSE`, `NOTICE`, `README.md`, `CREDITS.md`.
