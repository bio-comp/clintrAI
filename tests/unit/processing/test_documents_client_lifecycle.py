"""Tests for document downloader HTTP client lifecycle behavior."""

from __future__ import annotations

import httpx
import polars as pl
import pytest

from clintrai.models.types import HarmonizedFieldName
from clintrai.processing import documents as documents_module


@pytest.mark.asyncio
async def test_download_documents_uses_single_shared_client_per_run(tmp_path):
    """Downloader should create one client per run and reuse it across documents."""
    harmonized_df = pl.DataFrame(
        {
            HarmonizedFieldName.NCT_ID.value: ["NCT00010001"],
            HarmonizedFieldName.DOCUMENT_URLS.value: [
                [
                    "Protocol, https://example.com/protocol_v1.pdf",
                    "SAP, https://example.com/sap_v1.pdf",
                ],
            ],
        }
    )
    documents = documents_module.extract_document_info(harmonized_df, snapshot_id="snapshot-client")

    factory_calls = 0

    def _client_factory() -> httpx.AsyncClient:
        nonlocal factory_calls
        factory_calls += 1
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(200, content=b"%PDF-1.7 sample content")
        )
        return httpx.AsyncClient(transport=transport)

    records, stats = await documents_module.download_documents(
        documents=documents,
        output_dir=tmp_path / "documents",
        client_factory=_client_factory,
        max_concurrent=2,
        max_size_mb=5,
        raw_artifacts_dir=tmp_path / "raw_artifacts",
    )

    assert factory_calls == 1
    assert len(records) == 2
    assert stats["downloaded"] == 2
    assert stats["failed"] == 0
    assert stats["skipped"] == 0
    assert all(record["status"] == "downloaded" for record in records)
