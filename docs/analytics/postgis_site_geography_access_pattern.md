# PostGIS Site Geography Access Pattern

This document defines the geospatial model and baseline query surfaces added for issue #3.

## Schema Additions
Migration `0005_postgis_site_geography.sql` extends canonical `site` with:
- `site_point geometry(point, 4326)` for planar geometry operations and map projection compatibility.
- `site_geog geography(point, 4326)` for meter-accurate distance/radius filtering.

Both columns are generated from canonical `longitude` + `latitude` using:
- `st_setsrid(st_makepoint(longitude, latitude), 4326)`

## Indexing Strategy
Implemented indexes:
- `idx_site_site_point_gist` on `site_point` for geometry predicates.
- `idx_site_site_geog_gist` on `site_geog` for radius/distance filters (`st_dwithin`).
- `idx_site_country_state` on `(country, state)` for region coverage grouping/filtering.
- `idx_site_trial_country` on `(trial_id, country)` for trial-scoped geography slices.

This mix supports both spatial filtering and relational drill-down paths.

## Canonical Integration Surface
`site_trial_geography` view joins canonical trial + site records and keeps:
- trial keys: `trial_id`, `nct_id`, `overall_status`
- site location fields and PostGIS points
- lineage fields: `source_snapshot_id`, `source_system`, `source_record_id`, `source_content_sha256`

## Baseline Query Surfaces
Migration-provided SQL interfaces:
- `sites_within_radius_km(center_lat, center_lon, radius_km, max_results)`
- `site_catchment_summary(radius_km)`
- `region_site_coverage` view

### Radius Search
```sql
select *
from sites_within_radius_km(39.7392, -104.9903, 75.0, 200);
```

### Catchment Summary
```sql
select *
from site_catchment_summary(100.0)
order by nearby_trial_count desc, nearby_site_count desc
limit 50;
```

### Regional Coverage
```sql
select country, state, site_count, trial_count, sponsor_count
from region_site_coverage
order by site_count desc, trial_count desc;
```
