# I-29 Speedway v1.0.2

Server fix release on top of v1.0.1. Install exactly as before (unzip into the Assetto Corsa root or drag onto Content Manager).

## Changes
- **Dedicated server / Content Manager server fix:** servers crashed with `No track params found for vf_i29_speedway` (the entry was lost with the rename from `zw_rpm`). The zip now contains `server/data_track_params_vf_i29_speedway.ini`. Append it to `<server>/system/data/data_track_params.ini` and, for local CM hosting, to `<Assetto Corsa>/system/data/data_track_params.ini` (AssettoServer: `cfg/data_track_params.ini`). Do not replace the whole file. `server/add_track_params.py <file>` appends it only if missing.

```ini
[vf_i29_speedway]
NAME=I-29 Speedway
LATITUDE=41.024167
LONGITUDE=-95.832778
TIMEZONE=America/Chicago
```

- Version bumped to 1.0.2 in both layouts. Track content is otherwise unchanged from v1.0.1.
