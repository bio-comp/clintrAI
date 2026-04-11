-- 0005_postgis_site_geography.sql
-- PostGIS support for site selection and recruitment geography analysis.

begin;

create extension if not exists postgis;

alter table site
    add column if not exists site_point geometry(point, 4326)
    generated always as (
        case
            when latitude is not null and longitude is not null
                then st_setsrid(st_makepoint(longitude, latitude), 4326)
            else null
        end
    ) stored;

alter table site
    add column if not exists site_geog geography(point, 4326)
    generated always as (
        case
            when latitude is not null and longitude is not null
                then st_setsrid(st_makepoint(longitude, latitude), 4326)::geography
            else null
        end
    ) stored;

create index if not exists idx_site_site_point_gist
    on site using gist (site_point);

create index if not exists idx_site_site_geog_gist
    on site using gist (site_geog);

create index if not exists idx_site_country_state
    on site (country, state);

create index if not exists idx_site_trial_country
    on site (trial_id, country);

create or replace view site_trial_geography as
select
    s.site_id,
    s.trial_id,
    t.nct_id,
    t.overall_status,
    s.facility_name,
    s.city,
    s.state,
    s.country,
    s.postal_code,
    s.latitude,
    s.longitude,
    s.site_point,
    s.site_geog,
    s.source_snapshot_id,
    s.source_system,
    s.source_record_id,
    s.source_content_sha256
from site s
join trial t on t.trial_id = s.trial_id;

create or replace function sites_within_radius_km(
    center_lat double precision,
    center_lon double precision,
    radius_km double precision default 50.0,
    max_results integer default 500
)
returns table (
    site_id bigint,
    trial_id bigint,
    nct_id text,
    facility_name text,
    city text,
    state text,
    country text,
    distance_km double precision
)
language sql
stable
as $$
    select
        s.site_id,
        s.trial_id,
        t.nct_id,
        s.facility_name,
        s.city,
        s.state,
        s.country,
        st_distance(
            s.site_geog,
            st_setsrid(st_makepoint(center_lon, center_lat), 4326)::geography
        ) / 1000.0 as distance_km
    from site s
    join trial t on t.trial_id = s.trial_id
    where s.site_geog is not null
      and st_dwithin(
          s.site_geog,
          st_setsrid(st_makepoint(center_lon, center_lat), 4326)::geography,
          radius_km * 1000.0
      )
    order by distance_km asc
    limit greatest(max_results, 1);
$$;

create or replace function site_catchment_summary(
    radius_km double precision default 50.0
)
returns table (
    site_id bigint,
    trial_id bigint,
    nct_id text,
    nearby_site_count bigint,
    nearby_trial_count bigint
)
language sql
stable
as $$
    select
        anchor.site_id,
        anchor.trial_id,
        t.nct_id,
        count(neighbor.site_id) filter (
            where neighbor.site_id is not null and neighbor.site_id <> anchor.site_id
        ) as nearby_site_count,
        count(distinct neighbor.trial_id) filter (
            where neighbor.site_id is not null and neighbor.site_id <> anchor.site_id
        ) as nearby_trial_count
    from site anchor
    join trial t on t.trial_id = anchor.trial_id
    left join site neighbor
        on anchor.site_geog is not null
       and neighbor.site_geog is not null
       and st_dwithin(anchor.site_geog, neighbor.site_geog, radius_km * 1000.0)
    group by anchor.site_id, anchor.trial_id, t.nct_id;
$$;

create or replace view region_site_coverage as
select
    coalesce(s.country, 'unknown') as country,
    coalesce(s.state, 'unknown') as state,
    count(*) as site_count,
    count(distinct s.trial_id) as trial_count,
    count(distinct t.sponsor_id) as sponsor_count,
    st_centroid(st_collect(s.site_point))::geometry(point, 4326) as coverage_centroid
from site s
join trial t on t.trial_id = s.trial_id
where s.site_point is not null
group by 1, 2;

commit;
