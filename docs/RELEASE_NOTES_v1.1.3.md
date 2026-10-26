# I-29 Speedway v1.1.3

Long Course Chicane. **Checksummed files added** (`vf_chicane.kn5`, `models_chicane.ini`, `chicane/data/surfaces.ini`): install v1.1.3 on the server and on every client.

## Changes
- New layout **Long Course Chicane** (`chicane`): the long course with two soft-cut cone chicanes on the west double-straight, aligned across from each other.
- Southbound main straight: entrance driver's right, exit driver's left. Northbound return: entrance driver's left, exit driver's right.
- AI `fast_lane` and `ideal_line` follow the weaves. Driving through a chicane is off-track (invisible SCUT, no hard walls). The cone line stays valid. The short-course T1 hairpin stays closed.
- `main` and `short` are unchanged apart from the version string.
- Version 1.1.3 in all three layouts. Apache-2.0, author Vybes Forge.

## Upgrading
1. Install the v1.1.3 zip over v1.1.2 on the server and all clients.
2. Restart the server. Content Manager shows three layouts.
