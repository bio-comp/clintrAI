"""Contract tests for lineage and reprocessing control migration."""

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = Path("database/migrations/0003_data_lineage_reprocessing_controls.sql")


def _load_sql() -> str:
    assert MIGRATION_PATH.exists(), f"Expected migration file at {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8").lower()


def test_lineage_migration_exists():
    """Lineage/reprocessing migration should exist."""
    assert MIGRATION_PATH.exists()


def test_lineage_migration_defines_bronze_silver_gold_layers():
    """Migration should define explicit bronze/silver/gold layer typing."""
    sql = _load_sql()

    assert "create type data_layer as enum" in sql
    assert "'bronze'" in sql
    assert "'silver'" in sql
    assert "'gold'" in sql


def test_lineage_migration_adds_reproducible_dataset_versions():
    """Migration should include deterministic version identifier generation."""
    sql = _load_sql()

    assert "create table if not exists dataset_version" in sql
    assert "version_id text generated always as" in sql
    assert "md5(" in sql
    assert "unique (layer, dataset_key, source_snapshot_id, input_fingerprint, transform_version)" in sql


def test_lineage_migration_adds_idempotent_reprocessing_requests():
    """Migration should enforce idempotency for replay/backfill requests."""
    sql = _load_sql()

    assert "create table if not exists reprocessing_request" in sql
    assert "idempotency_key text not null unique" in sql
    assert "request_type text not null" in sql
    assert "check (request_type in ('backfill', 'replay'))" in sql


def test_lineage_migration_blocks_invalid_promotions_with_quality_gate():
    """Promotion to higher layers should be blocked unless quality checks passed."""
    sql = _load_sql()

    assert "create table if not exists quality_check_result" in sql
    assert "create table if not exists layer_promotion" in sql
    assert (
        "create function enforce_quality_gate_before_promotion()" in sql
        or "create or replace function enforce_quality_gate_before_promotion()" in sql
    )
    assert "create trigger trg_enforce_quality_gate_before_promotion" in sql
