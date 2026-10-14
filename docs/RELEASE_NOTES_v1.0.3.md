# I-29 Speedway v1.0.3

Documentation/tooling fix on top of v1.0.2. Track geometry and checksummed files (`*.kn5`, `surfaces.ini`, `models*.ini`) are byte-identical to v1.0.2.

## Changes
- **Server setup corrected:** do not edit `system/data/data_track_params.ini` (server or game). Vanilla acServer needs no track params. AssettoServer reads only `<server root>/cfg/data_track_params.ini`; append `server/data_track_params_vf_i29_speedway.ini` there, or run `python server/add_track_params.py "<server root>"` (idempotent, `.bak`, refuses `system/data`). Alternative: `extra_cfg.yml` → `IgnoreConfigurationErrors: MissingTrackParams: true` (UTC; not with LiveWeatherPlugin).
- **Checksum failed?** Install the identical release on server and clients, delete old `zw_rpm`/stale `vf_i29_speedway` folders, restart the server.
- Version bumped to 1.0.3 in both layouts.
