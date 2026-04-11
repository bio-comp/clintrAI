"""Contract tests for PostGIS site geography migration."""

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = Path("database/migrations/0005_postgis_site_geography.sql")


def _load_sql() -> str:
    assert MIGRATION_PATH.exists(), f"Expected migration file at {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8").lower()


def test_postgis_site_geography_migration_exists():
    """PostGIS site geography migration should exist."""
    assert MIGRATION_PATH.exists()


def test_site_table_adds_geometry_and_geography_columns_with_srid():
    """Site schema should include geometry/geography point columns with SRID 4326."""
    sql = _load_sql()

    assert "create extension if not exists postgis" in sql
    assert "add column if not exists site_point geometry(point, 4326)" in sql
    assert "add column if not exists site_geog geography(point, 4326)" in sql
    assert "st_setsrid(st_makepoint(longitude, latitude), 4326)" in sql


def test_postgis_indexing_strategy_is_implemented():
    """Migration should include spatial and regional indexes for distance/coverage workloads."""
    sql = _load_sql()

    assert "create index if not exists idx_site_site_point_gist" in sql
    assert "on site using gist (site_point)" in sql
    assert "create index if not exists idx_site_site_geog_gist" in sql
    assert "on site using gist (site_geog)" in sql
    assert "create index if not exists idx_site_country_state" in sql
    assert "create index if not exists idx_site_trial_country" in sql


def test_baseline_geospatial_query_surfaces_exist():
    """Radius, catchment, and region coverage query surfaces should be present."""
    sql = _load_sql()

    assert "create or replace function sites_within_radius_km" in sql
    assert "st_dwithin" in sql
    assert "create or replace function site_catchment_summary" in sql
    assert "count(distinct neighbor.trial_id)" in sql
    assert "create or replace view region_site_coverage" in sql


def test_geospatial_outputs_are_joined_to_canonical_trial_site_entities():
    """Geospatial outputs should be linked to canonical trial and site entities."""
    sql = _load_sql()

    assert "create or replace view site_trial_geography" in sql
    assert "from site s" in sql
    assert "join trial t on t.trial_id = s.trial_id" in sql
    assert "t.nct_id" in sql
