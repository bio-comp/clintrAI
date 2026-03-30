"""Tests for document provenance and immutable raw artifact storage."""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import polars as pl
import pytest

from clintrai.models.types import HarmonizedFieldName
from clintrai.processing import documents as documents_module


@pytest.mark.asyncio
async def test_process_document_downloads_writes_snapshot_and_provenance(tmp_path, monkeypatch):
    """Downloaded records should carry snapshot + hash provenance, and snapshot metadata should be persisted."""
    content = b"%PDF-1.7 sample protocol content"

    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000001"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [
                ["Protocol, https://example.com/protocol_v1.pdf"],
            ],
        }
    )

    def _mock_client_factory() -> httpx.AsyncClient:
        transport = httpx.MockTransport(lambda request: httpx.Response(200, content=content))
        return httpx.AsyncClient(transport=transport)

    monkeypatch.setattr(documents_module, "create_httpx_client", _mock_client_factory)

    records, stats = await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=tmp_path,
        max_concurrent=1,
        max_size_mb=5,
        snapshot_id="snapshot-001",
    )

    assert stats["total_documents"] == 1
    assert stats["downloaded"] == 1
    assert len(records) == 1

    record = records[0]
    expected_hash = hashlib.sha256(content).hexdigest()

    assert record["source_snapshot_id"] == "snapshot-001"
    assert record["source_content_sha256"] == expected_hash
    assert record["raw_artifact_path"] is not None
    assert Path(record["raw_artifact_path"]).exists()
    assert record["source_fetched_at"] is not None

    metadata_df = pl.read_parquet(tmp_path / "document_metadata.parquet")
    assert "source_snapshot_id" in metadata_df.columns
    assert "source_content_sha256" in metadata_df.columns
    assert metadata_df[0, "source_snapshot_id"] == "snapshot-001"
    assert metadata_df[0, "source_content_sha256"] == expected_hash

    snapshot_df = pl.read_parquet(tmp_path / "source_snapshot.parquet")
    assert snapshot_df[0, "snapshot_id"] == "snapshot-001"
    assert snapshot_df[0, "document_count"] == 1
    assert snapshot_df[0, "downloaded_count"] == 1


def test_persist_raw_artifact_is_content_addressed_and_idempotent(tmp_path):
    """Persisting the same bytes twice should reuse one immutable artifact path."""
    raw_artifacts_dir = tmp_path / "raw_artifacts"

    first_path, first_hash = documents_module._persist_raw_artifact(
        raw_artifacts_dir,
        b"same-content",
        "protocol_v1.pdf",
    )
    second_path, second_hash = documents_module._persist_raw_artifact(
        raw_artifacts_dir,
        b"same-content",
        "protocol_v1.pdf",
    )

    assert first_hash == second_hash
    assert first_path == second_path
    assert first_path.exists()

    artifact_files = [path for path in raw_artifacts_dir.rglob("*") if path.is_file()]
    assert len(artifact_files) == 1


@pytest.mark.asyncio
async def test_process_document_downloads_no_docs_writes_snapshot(tmp_path):
    """No-document runs should still persist source snapshot metadata."""
    output_dir = tmp_path / "missing_output_dir"
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000002"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [[]],
        }
    )

    records, stats = await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=output_dir,
        snapshot_id="snapshot-empty",
    )

    assert records == []
    assert stats["total_documents"] == 0

    snapshot_path = output_dir / "source_snapshot.parquet"
    assert snapshot_path.exists()

    snapshot_df = pl.read_parquet(snapshot_path)
    assert snapshot_df[0, "snapshot_id"] == "snapshot-empty"
    assert snapshot_df[0, "document_count"] == 0
    assert snapshot_df[0, "downloaded_count"] == 0


@pytest.mark.asyncio
async def test_skipped_documents_keep_hash_without_new_fetch_timestamp(tmp_path, monkeypatch):
    """Skipped documents should keep content hash provenance without recording a fresh fetch timestamp."""
    content = b"%PDF-1.7 stable content"
    output_dir = tmp_path / "output"
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000003"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [
                ["Protocol, https://example.com/protocol_v2.pdf"],
            ],
        }
    )

    def _mock_client_factory() -> httpx.AsyncClient:
        transport = httpx.MockTransport(lambda request: httpx.Response(200, content=content))
        return httpx.AsyncClient(transport=transport)

    monkeypatch.setattr(documents_module, "create_httpx_client", _mock_client_factory)

    first_records, _ = await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=output_dir,
        snapshot_id="snapshot-first",
    )
    assert first_records[0]["status"] == "downloaded"

    second_records, _ = await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=output_dir,
        snapshot_id="snapshot-second",
    )

    expected_hash = hashlib.sha256(content).hexdigest()
    skipped_record = second_records[0]

    assert skipped_record["status"] == "skipped"
    assert skipped_record["source_snapshot_id"] == "snapshot-second"
    assert skipped_record["source_content_sha256"] == expected_hash
    assert skipped_record["source_fetched_at"] is None
    assert skipped_record["raw_artifact_path"] is not None
    assert Path(skipped_record["raw_artifact_path"]).exists()
