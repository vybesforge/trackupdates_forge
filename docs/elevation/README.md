# Elevation / georeference
- DEM: USGS 3DEP 1 m, project IA_WesternIA_2020_D21, tile USGS_1M_15_x26y455 (public domain): https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/IA_WesternIA_2020_D21/TIFF/USGS_1M_15_x26y455_IA_WesternIA_2020_D21.tif
- `dem_crop_1m.tif`: crop E 261600–264400, N 4544200–4547700, EPSG:26915 (UTM 15N), NAVD88 m. Range 288.27–303.12 m (high values = I-29 embankment/overpass).
- `heightmap_16bit.png`: same crop, 0–65535 linear = 288.27–303.12 m (14.85 m span), 1 px = 1 m, north up. Blender: Displace strength 14.85 m.
- Georeference AC (x, z) → UTM 15N (E, N): E = 0.97902·x − 0.03574·z + 263012.19 ; N = −0.02284·x − 0.98587·z + 4545027.63.
  Derived chain: kn5 ground mesh (material `google`, mesh 1GRASS) UV fit (3063/3153 inliers, sub-px) → google2 image → NAIP 2021 (SIFT+ECC). OSM Overpass was unavailable (406/HTML errors), so OSM was not used; overlay `ai_lines_on_naip.png` shows the fit (red main, yellow short).
  Note: implied model scale 0.976–0.990 vs real → zwiss's model is ~1–2.5 % small / slightly sheared; check during mesh rework.
- `../elevation_profile.csv`: per AI point: layout, dist_m, UTM E/N, DEM raw, smoothed (σ≈3 pts), relative-to-min, AC AI y.
