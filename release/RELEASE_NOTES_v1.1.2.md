# I-29 Speedway v1.1.2

Drag-area ad tent fix. **Checksummed files changed** (`vf_dragtents.kn5`, `vf_dragcol.kn5`, `vf_westlot.kn5`): install v1.1.2 on the server and on every client.

## Changes
- Ad tent `vftent_slot20` moved from the south staging spot to the old back-tent spot (west of slot 19), opening south towards the apron. The south spot is now empty. Still 20 tent slots; `skins/default/tent_slot20.dds` is unchanged.
- Collision (`1WALL_DRAG_VFTENT` leg posts) moved with the tent; old staging-tent geometry stays fully hidden with no collision.
- West-lot gravel re-cut around the tents (kept off objects; the freed spot is gravel like its surroundings).
- Version 1.1.2 in both layouts.

## Upgrading
1. Install the v1.1.2 zip over v1.1.1 on the server and all clients (or copy the 3 kn5s above).
2. Restart the server.
