"""Contract tests for document chunk FTS + pgvector migration."""

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = Path("database/migrations/0002_document_chunk_pipeline.sql")


def _load_sql() -> str:
    assert MIGRATION_PATH.exists(), f"Expected migration file at {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8").lower()


def test_document_chunk_migration_exists():
    """Document chunk pipeline migration should exist."""
    assert MIGRATION_PATH.exists()


def test_document_chunk_table_includes_required_columns():
    """Document chunk table should include text, offsets, section path, metadata, and provenance fields."""
    sql = _load_sql()
    assert "create table if not exists document_chunk" in sql

    required_columns = [
        "trial_id",
        "nct_id",
        "chunk_index",
        "chunk_text",
        "section_path",
        "char_start",
        "char_end",
        "metadata jsonb",
        "search_text_tsv tsvector",
        "embedding vector",
        "source_snapshot_id",
        "source_content_sha256",
        "source_document_path",
    ]

    table_start = sql.index("create table if not exists document_chunk")
    table_end = sql.index(");", table_start)
    table_sql = sql[table_start:table_end]

    for column in required_columns:
        assert column in table_sql


def test_document_chunk_table_links_to_trial_and_enforces_offsets():
    """Migration should enforce trial linkage and basic offset validity constraints."""
    sql = _load_sql()
    table_start = sql.index("create table if not exists document_chunk")
    table_end = sql.index(");", table_start)
    table_sql = sql[table_start:table_end]

    assert "references trial(trial_id)" in table_sql
    assert "check (char_start >= 0)" in table_sql
    assert "check (char_end >= char_start)" in table_sql


def test_document_chunk_migration_creates_fts_and_vector_indexes():
    """Migration should add full-text and vector similarity indexes."""
    sql = _load_sql()

    assert "create index if not exists idx_document_chunk_fts" in sql
    assert "using gin (search_text_tsv)" in sql

    assert "create index if not exists idx_document_chunk_embedding_hnsw" in sql
    assert "using hnsw (embedding vector_cosine_ops)" in sql


def test_document_chunk_migration_adds_provenance_lookup_indexes():
    """Migration should support chunk-to-source provenance lookup queries."""
    sql = _load_sql()

    assert "create index if not exists idx_document_chunk_snapshot" in sql
    assert "(source_snapshot_id)" in sql

    assert "create index if not exists idx_document_chunk_source_hash" in sql
    assert "(source_content_sha256)" in sql
