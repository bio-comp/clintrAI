"""Contract tests for canonical PostgreSQL schema migration."""

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = Path("database/migrations/0001_canonical_schema.sql")


def _load_migration_sql() -> str:
    assert MIGRATION_PATH.exists(), f"Expected migration file at {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8").lower()


def test_canonical_migration_file_exists():
    """Initial canonical schema migration must exist."""
    assert MIGRATION_PATH.exists()


def test_canonical_schema_includes_required_core_tables():
    """Core canonical entities should be defined in the migration."""
    sql = _load_migration_sql()

    required_tables = [
        "trial",
        "trial_version",
        "arm",
        "intervention",
        "condition",
        "biomarker",
        "endpoint",
        "outcome_measure",
        "adverse_event",
        "site",
        "sponsor",
        "publication",
    ]

    for table_name in required_tables:
        assert f"create table if not exists {table_name}" in sql


def test_canonical_schema_uses_jsonb_for_irregular_fields():
    """Canonical entities should keep irregular fields in jsonb columns."""
    sql = _load_migration_sql()

    for table_name in ["trial", "arm", "intervention", "condition", "endpoint", "site", "publication"]:
        table_block_start = sql.index(f"create table if not exists {table_name}")
        table_block_end = sql.index(");", table_block_start)
        table_sql = sql[table_block_start:table_block_end]
        assert "jsonb" in table_sql


def test_canonical_schema_includes_provenance_columns():
    """Canonical entities should include snapshot-level provenance keys."""
    sql = _load_migration_sql()

    provenance_columns = [
        "source_snapshot_id",
        "source_system",
        "source_record_id",
    ]

    for table_name in ["trial", "trial_version", "arm", "intervention", "condition", "endpoint", "outcome_measure", "adverse_event", "site", "publication"]:
        table_block_start = sql.index(f"create table if not exists {table_name}")
        table_block_end = sql.index(");", table_block_start)
        table_sql = sql[table_block_start:table_block_end]

        for column in provenance_columns:
            assert column in table_sql
