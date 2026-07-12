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

    snapshot_dir = tmp_path / "snapshots" / "snapshot-001"
    metadata_df = pl.read_parquet(snapshot_dir / "document_metadata.parquet")
    assert "source_snapshot_id" in metadata_df.columns
    assert "source_content_sha256" in metadata_df.columns
    assert "url" in metadata_df.columns
    assert "source_fetched_at" in metadata_df.columns
    assert "raw_artifact_path" in metadata_df.columns
    assert metadata_df[0, "source_snapshot_id"] == "snapshot-001"
    assert metadata_df[0, "source_content_sha256"] == expected_hash

    snapshot_df = pl.read_parquet(snapshot_dir / "source_snapshot.parquet")
    assert snapshot_df[0, "snapshot_id"] == "snapshot-001"
    assert snapshot_df[0, "status"] == "completed"
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


def test_persist_raw_artifact_rejects_corrupt_existing_content(tmp_path):
    """An existing artifact must match the hash encoded in its path."""
    raw_artifacts_dir = tmp_path / "raw_artifacts"
    content = b"expected-content"
    content_hash = hashlib.sha256(content).hexdigest()
    artifact_path = raw_artifacts_dir / content_hash[:2] / f"{content_hash}.pdf"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"corrupt")

    with pytest.raises(RuntimeError, match="integrity check failed"):
        documents_module._persist_raw_artifact(
            raw_artifacts_dir,
            content,
            "protocol.pdf",
        )


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

    snapshot_path = output_dir / "snapshots" / "snapshot-empty" / "source_snapshot.parquet"
    assert snapshot_path.exists()

    snapshot_df = pl.read_parquet(snapshot_path)
    assert snapshot_df[0, "snapshot_id"] == "snapshot-empty"
    assert snapshot_df[0, "status"] == "completed"
    assert snapshot_df[0, "document_count"] == 0
    assert snapshot_df[0, "downloaded_count"] == 0


@pytest.mark.asyncio
async def test_unchanged_documents_are_refetched_and_reuse_artifact(tmp_path, monkeypatch):
    """Unchanged documents should be revalidated and reuse their content-addressed artifact."""
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

    request_count = 0

    def _mock_client_factory() -> httpx.AsyncClient:
        def _handler(_request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            return httpx.Response(200, content=content)

        transport = httpx.MockTransport(_handler)
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
    unchanged_record = second_records[0]

    assert request_count == 2
    assert unchanged_record["status"] == "downloaded"
    assert unchanged_record["source_snapshot_id"] == "snapshot-second"
    assert unchanged_record["source_content_sha256"] == expected_hash
    assert unchanged_record["source_fetched_at"] is not None
    assert unchanged_record["raw_artifact_path"] is not None
    assert Path(unchanged_record["raw_artifact_path"]).exists()
    assert unchanged_record["raw_artifact_path"] == first_records[0]["raw_artifact_path"]
    assert unchanged_record["local_path"] != first_records[0]["local_path"]

    assert (output_dir / "snapshots" / "snapshot-first" / "document_metadata.parquet").exists()
    assert (output_dir / "snapshots" / "snapshot-second" / "document_metadata.parquet").exists()


@pytest.mark.asyncio
async def test_changed_document_at_same_url_creates_new_artifact(tmp_path, monkeypatch):
    """Changed bytes at a stable URL should create a new immutable artifact."""
    contents = iter([b"%PDF-1.7 version one", b"%PDF-1.7 version two"])
    output_dir = tmp_path / "output"
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000004"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [
                ["Protocol, https://example.com/protocol.pdf"],
            ],
        }
    )

    def _mock_client_factory() -> httpx.AsyncClient:
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(200, content=next(contents))
        )
        return httpx.AsyncClient(transport=transport)

    monkeypatch.setattr(documents_module, "create_httpx_client", _mock_client_factory)

    first_records, _ = await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=output_dir,
        snapshot_id="snapshot-change-1",
    )
    second_records, _ = await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=output_dir,
        snapshot_id="snapshot-change-2",
    )

    first_record = first_records[0]
    second_record = second_records[0]

    assert first_record["status"] == "downloaded"
    assert second_record["status"] == "downloaded"
    assert first_record["source_content_sha256"] != second_record["source_content_sha256"]
    assert first_record["raw_artifact_path"] != second_record["raw_artifact_path"]
    assert Path(first_record["raw_artifact_path"]).exists()
    assert Path(second_record["raw_artifact_path"]).exists()
    assert first_record["local_path"] != second_record["local_path"]
    assert Path(first_record["local_path"]).read_bytes() == b"%PDF-1.7 version one"
    assert Path(second_record["local_path"]).read_bytes() == b"%PDF-1.7 version two"


@pytest.mark.asyncio
async def test_same_filename_from_different_urls_has_distinct_local_identity(tmp_path, monkeypatch):
    """Different source URLs must not collide when their filenames match."""
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000005"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [
                [
                    "Protocol, https://primary.example.com/files/protocol.pdf",
                    "Protocol, https://mirror.example.com/files/protocol.pdf",
                ],
            ],
        }
    )

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=str(request.url).encode())

    def _mock_client_factory() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(_handler))

    monkeypatch.setattr(documents_module, "create_httpx_client", _mock_client_factory)

    records, stats = await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=tmp_path,
        snapshot_id="snapshot-collision",
    )

    local_paths = {record["local_path"] for record in records}
    assert stats["downloaded"] == 2
    assert len(local_paths) == 2
    assert all(Path(path).exists() for path in local_paths)


@pytest.mark.asyncio
async def test_snapshot_identifier_cannot_be_reused(tmp_path):
    """Snapshot directories should be append-only and reject duplicate identifiers."""
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000006"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [[]],
        }
    )

    await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=tmp_path,
        snapshot_id="snapshot-immutable",
    )

    with pytest.raises(FileExistsError):
        await documents_module.process_document_downloads(
            harmonized_df=harmonized_df,
            output_dir=tmp_path,
            snapshot_id="snapshot-immutable",
        )


@pytest.mark.asyncio
async def test_failed_run_persists_failure_manifest(tmp_path, monkeypatch):
    """A reserved snapshot should record an unexpected processing failure."""
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000007"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [[]],
        }
    )

    def _raise_extraction_error(*_args, **_kwargs):
        raise RuntimeError("extraction failed")

    monkeypatch.setattr(
        documents_module,
        "extract_document_info",
        _raise_extraction_error,
    )

    with pytest.raises(RuntimeError, match="extraction failed"):
        await documents_module.process_document_downloads(
            harmonized_df=harmonized_df,
            output_dir=tmp_path,
            snapshot_id="snapshot-failed",
        )

    snapshot_df = pl.read_parquet(
        tmp_path / "snapshots" / "snapshot-failed" / "source_snapshot.parquet"
    )
    assert snapshot_df[0, "status"] == "failed"
    assert snapshot_df[0, "error"] == "extraction failed"


@pytest.mark.asyncio
async def test_oversized_response_preserves_fetch_provenance(tmp_path, monkeypatch):
    """Fetched bytes should remain auditable even when materialization is rejected."""
    content = b"oversized"
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000008"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [
                ["Protocol, https://example.com/oversized.pdf"],
            ],
        }
    )

    def _mock_client_factory() -> httpx.AsyncClient:
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(200, content=content)
        )
        return httpx.AsyncClient(transport=transport)

    monkeypatch.setattr(documents_module, "create_httpx_client", _mock_client_factory)

    records, stats = await documents_module.process_document_downloads(
        harmonized_df=harmonized_df,
        output_dir=tmp_path,
        max_size_mb=0,
        snapshot_id="snapshot-oversized",
    )

    record = records[0]
    assert stats["failed"] == 1
    assert record["status"] == "failed"
    assert record["source_fetched_at"] is not None
    assert record["source_content_sha256"] == hashlib.sha256(content).hexdigest()
    assert Path(record["raw_artifact_path"]).read_bytes() == content


@pytest.mark.asyncio
async def test_empty_snapshot_identifier_is_rejected(tmp_path):
    """An explicitly empty snapshot identifier should not be silently replaced."""
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00000009"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [[]],
        }
    )

    with pytest.raises(ValueError, match="Invalid snapshot identifier"):
        await documents_module.process_document_downloads(
            harmonized_df=harmonized_df,
            output_dir=tmp_path,
            snapshot_id="",
        )
