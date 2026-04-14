"""Contract tests for Neo4j projection design documentation."""

from __future__ import annotations

from pathlib import Path

DESIGN_DOC_PATH = Path("docs/plans/2026-04-12-neo4j-projection-design.md")
QUERY_CATALOG_PATH = Path("docs/analytics/neo4j_projection_query_catalog.cypher")


def _load_design_doc() -> str:
    assert DESIGN_DOC_PATH.exists(), f"Expected design doc at {DESIGN_DOC_PATH}"
    return DESIGN_DOC_PATH.read_text(encoding="utf-8").lower()


def _load_query_catalog() -> str:
    assert QUERY_CATALOG_PATH.exists(), f"Expected query catalog at {QUERY_CATALOG_PATH}"
    return QUERY_CATALOG_PATH.read_text(encoding="utf-8").lower()


def test_design_doc_and_query_catalog_exist():
    """Neo4j projection design artifacts should exist."""
    assert DESIGN_DOC_PATH.exists()
    assert QUERY_CATALOG_PATH.exists()


def test_design_doc_defines_projection_schema_from_canonical():
    """Design doc should define graph schema as a canonical projection."""
    content = _load_design_doc()

    assert "graph schema as a projection from canonical postgres" in content
    assert "node labels and source mapping" in content
    assert "relationship types and source mapping" in content
    assert "trial" in content
    assert "sponsor" in content


def test_design_doc_documents_incremental_and_replay_sync_strategy():
    """ETL strategy should include bootstrap, incremental sync, and replay/backfill."""
    content = _load_design_doc()

    assert "etl sync strategy (incremental + replay)" in content
    assert "bootstrap (initial full load)" in content
    assert "incremental sync" in content
    assert "replay / backfill" in content
    assert "merge" in content


def test_query_catalog_covers_core_traversal_use_cases():
    """Core traversal query use cases should be represented in the query catalog."""
    content = _load_query_catalog()

    assert "use case 1" in content
    assert "use case 2" in content
    assert "use case 3" in content
    assert "use case 4" in content
    assert "match (s:sponsor)-[:sponsors]->(t:trial)-[:studies]->(c:condition)" in content


def test_design_doc_marks_graph_layer_non_authoritative():
    """Design doc must explicitly mark Neo4j as non-authoritative."""
    content = _load_design_doc()

    assert "non-authoritative" in content
    assert "postgres wins" in content
    assert "query accelerator" in content
