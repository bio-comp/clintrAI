"""Contract tests for eligibility dual representation migration."""

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = Path("database/migrations/0004_eligibility_dual_representation.sql")


def _load_sql() -> str:
    assert MIGRATION_PATH.exists(), f"Expected migration file at {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8").lower()


def test_eligibility_migration_exists():
    """Eligibility dual-representation migration should exist."""
    assert MIGRATION_PATH.exists()


def test_eligibility_clause_table_contains_dual_representation_fields():
    """Eligibility clause table should retain raw text plus normalized structure and optional AST."""
    sql = _load_sql()
    assert "create table if not exists eligibility_clause" in sql

    table_start = sql.index("create table if not exists eligibility_clause")
    table_end = sql.index(");", table_start)
    table_sql = sql[table_start:table_end]

    required_columns = [
        "trial_id",
        "nct_id",
        "raw_text",
        "normalized_clause jsonb",
        "logical_ast jsonb",
        "char_start",
        "char_end",
        "source_document_path",
        "document_chunk_id",
        "source_snapshot_id",
        "source_content_sha256",
    ]

    for column in required_columns:
        assert column in table_sql


def test_eligibility_clause_table_enforces_traceability_constraints():
    """Eligibility clause rows should preserve offset validity and chunk-level provenance linkage."""
    sql = _load_sql()
    table_start = sql.index("create table if not exists eligibility_clause")
    table_end = sql.index(");", table_start)
    table_sql = sql[table_start:table_end]

    assert "references trial(trial_id)" in table_sql
    assert "references document_chunk(document_chunk_id)" in table_sql
    assert "check (char_start >= 0)" in table_sql
    assert "check (char_end >= char_start)" in table_sql


def test_eligibility_tree_table_exists_for_optional_ast_views():
    """Migration should include tree table for optional logical-tree representations."""
    sql = _load_sql()

    assert "create table if not exists eligibility_tree" in sql
    assert "tree_json jsonb" in sql
    assert "root_clause_id" in sql


def test_concept_link_table_captures_required_concept_types():
    """Concept link table should support disease/biomarker/lab/treatment mappings."""
    sql = _load_sql()

    assert "create table if not exists criterion_concept_link" in sql
    assert "concept_type text not null" in sql
    assert "check (concept_type in ('disease', 'biomarker', 'lab', 'treatment'))" in sql


def test_eligibility_migration_adds_indexes_for_queryability():
    """Migration should include indexes for JSON lookups, concept links, and text-offset traceability."""
    sql = _load_sql()

    assert "create index if not exists idx_eligibility_clause_trial" in sql
    assert "create index if not exists idx_eligibility_clause_normalized_json" in sql
    assert "using gin (normalized_clause)" in sql
    assert "create index if not exists idx_eligibility_clause_offsets" in sql
    assert "create index if not exists idx_criterion_concept_link_type_value" in sql
