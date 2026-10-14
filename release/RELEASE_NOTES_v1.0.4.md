# I-29 Speedway v1.0.4

Tooling/packaging fix on top of v1.0.3. Checksummed track files (`*.kn5`, `surfaces.ini`, `models*.ini`) are byte-identical to v1.0.3, so v1.0.3 and v1.0.4 clients/servers are checksum-compatible.

## Changes
- **Git checkouts now byte-identical to the zip:** `.gitattributes` disables line-ending conversion for all shipped files. Windows clones with `core.autocrlf=true` previously turned `.ini` files into CRLF, causing "checksum failed" online. Install from this zip, or from a fresh clone of v1.0.4.
- **`server/add_track_params.py` hardened:** append-only (never rewrites or truncates), keeps a `.bak`, refuses a missing or empty target unless `--create`, refuses `system/data`. Note: the v1.0.2 script created a 109-byte file containing only the `[vf_i29_speedway]` section when pointed at a missing or empty file — if your `system/data/data_track_params.ini` looks like that, restore it (Steam "Verify integrity of game files" for the game; original server files for a server).
- MD5 list of checksummed files in `INSTALL_AGENT.md`.
- Version 1.0.4 in both layouts.
