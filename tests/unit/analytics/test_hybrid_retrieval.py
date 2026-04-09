"""Tests for hybrid retrieval (metadata filters + lexical + vector)."""

from __future__ import annotations

import time

from clintrai.analytics.retrieval import HybridRetrievalQuery, hybrid_retrieve


def _sample_records() -> list[dict[str, object]]:
    return [
        {
            "document_chunk_id": 1,
            "nct_id": "NCT1001",
            "chunk_text": "Eligibility includes EGFR mutation positive NSCLC patients.",
            "source_snapshot_id": "snapshot-a",
            "source_content_sha256": "hash-a",
            "source_document_path": "docs/protocol_a.pdf",
            "country": "US",
            "study_phase": "PHASE2",
            "embedding": [0.10, 0.20, 0.30],
        },
        {
            "document_chunk_id": 2,
            "nct_id": "NCT1002",
            "chunk_text": "Exclusion criteria include uncontrolled hypertension and renal failure.",
            "source_snapshot_id": "snapshot-b",
            "source_content_sha256": "hash-b",
            "source_document_path": "docs/protocol_b.pdf",
            "country": "US",
            "study_phase": "PHASE2",
            "embedding": [0.90, 0.10, 0.10],
        },
        {
            "document_chunk_id": 3,
            "nct_id": "NCT2001",
            "chunk_text": "Inclusion requires prior PD-1 exposure and measurable disease.",
            "source_snapshot_id": "snapshot-c",
            "source_content_sha256": "hash-c",
            "source_document_path": "docs/protocol_c.pdf",
            "country": "CA",
            "study_phase": "PHASE3",
            "embedding": [0.95, 0.05, 0.05],
        },
    ]


def test_hybrid_retrieve_supports_metadata_filters_and_vector_similarity():
    """Metadata filters should constrain rows before semantic ranking."""
    query = HybridRetrievalQuery(
        query_text="EGFR mutation positive",
        query_embedding=[0.10, 0.20, 0.30],
        metadata_filters={"country": "US", "study_phase": "PHASE2"},
        top_k=2,
    )

    results = hybrid_retrieve(_sample_records(), query)

    assert len(results) == 2
    assert {r["document_chunk_id"] for r in results} == {1, 2}
    assert results[0]["document_chunk_id"] == 1


def test_hybrid_retrieve_uses_lexical_fallback_when_query_embedding_missing():
    """Lexical ranking should still return good candidates when embedding is absent."""
    query = HybridRetrievalQuery(
        query_text="uncontrolled hypertension",
        query_embedding=None,
        metadata_filters={"country": "US"},
        top_k=2,
    )

    results = hybrid_retrieve(_sample_records(), query)

    assert results
    assert results[0]["document_chunk_id"] == 2
    assert results[0]["lexical_score"] > 0.0
    assert results[0]["combined_score"] > 0.0


def test_hybrid_retrieve_returns_source_provenance_fields():
    """Returned hits should include source/provenance identifiers."""
    query = HybridRetrievalQuery(
        query_text="pd-1 measurable disease",
        query_embedding=[0.95, 0.05, 0.05],
        metadata_filters={"country": "CA"},
        top_k=1,
    )

    result = hybrid_retrieve(_sample_records(), query)[0]

    assert result["nct_id"] == "NCT2001"
    assert result["source_snapshot_id"] == "snapshot-c"
    assert result["source_content_sha256"] == "hash-c"
    assert result["source_document_path"] == "docs/protocol_c.pdf"


def test_hybrid_retrieve_smoke_precision_and_latency():
    """Smoke test: relevant top hit and bounded runtime for moderate candidate set."""
    records = []
    for idx in range(500):
        records.append(
            {
                "document_chunk_id": idx + 100,
                "nct_id": f"NCT{idx:04d}",
                "chunk_text": f"background sentence {idx}",
                "source_snapshot_id": "snapshot-z",
                "source_content_sha256": f"hash-{idx}",
                "source_document_path": f"docs/{idx}.pdf",
                "country": "US",
                "study_phase": "PHASE2",
                "embedding": [0.0, 1.0, 0.0],
            }
        )

    records.append(
        {
            "document_chunk_id": 42,
            "nct_id": "NCTBEST",
            "chunk_text": "Eligibility requires EGFR exon 19 deletion and measurable disease.",
            "source_snapshot_id": "snapshot-best",
            "source_content_sha256": "hash-best",
            "source_document_path": "docs/best.pdf",
            "country": "US",
            "study_phase": "PHASE2",
            "embedding": [1.0, 0.0, 0.0],
        }
    )

    query = HybridRetrievalQuery(
        query_text="egfr exon 19 deletion measurable disease",
        query_embedding=[1.0, 0.0, 0.0],
        metadata_filters={"country": "US", "study_phase": "PHASE2"},
        top_k=5,
    )

    start = time.perf_counter()
    results = hybrid_retrieve(records, query)
    elapsed = time.perf_counter() - start

    assert results[0]["document_chunk_id"] == 42
    assert elapsed < 1.0
