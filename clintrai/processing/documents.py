"""Document download and processing for clinical trials data."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
import re
from typing import Any, TypeAlias
from urllib.parse import urlparse

import httpx
from loguru import logger
import polars as pl

from clintrai.models.types import HarmonizedFieldName

# Type aliases for better readability
DocumentInfo: TypeAlias = dict[str, Any]
DownloadStats: TypeAlias = dict[str, Any]
HttpClient: TypeAlias = httpx.AsyncClient


def extract_document_info(df: pl.DataFrame) -> list[DocumentInfo]:
    """
    Extract document download information from harmonized DataFrame.
    
    Args:
        df: Harmonized DataFrame with document_urls column
        
    Returns:
        List of document info dictionaries
    """
    documents = []

    # Filter to studies with documents using vectorized operations
    studies_with_docs = df.filter(
        pl.col(HarmonizedFieldName.DOCUMENT_URLS.value).list.len() > 0
    ).select([
        HarmonizedFieldName.NCT_ID.value,
        HarmonizedFieldName.DOCUMENT_URLS.value
    ])

    for row in studies_with_docs.iter_rows(named=True):
        nct_id = row[HarmonizedFieldName.NCT_ID.value]
        document_urls = row[HarmonizedFieldName.DOCUMENT_URLS.value]

        for doc_string in document_urls:
            doc_type, url = _parse_document_url(doc_string)
            filename = _extract_filename(url)

            documents.append({
                "nct_id": nct_id,
                "document_type": doc_type,
                "url": url,
                "filename": filename,
                "local_path": None,
                "file_size": None,
                "status": "pending",
                "error": None
            })

    logger.info(f"Found {len(documents)} documents to download from {studies_with_docs.height} studies")
    return documents


def _parse_document_url(doc_string: str) -> tuple[str, str]:
    """Parse document URL string into (type, url) tuple."""
    if ", http" in doc_string:
        parts = doc_string.split(", http", 1)
        if len(parts) == 2:
            return parts[0].strip(), "http" + parts[1].strip()

    return "Unknown Document", doc_string.strip()


def _extract_filename(url: str) -> str:
    """Extract filename from URL."""
    parsed_url = urlparse(url)
    filename = Path(parsed_url.path).name
    return filename if filename else "unknown_document.pdf"


def _create_safe_path(output_dir: Path, nct_id: str, filename: str) -> Path:
    """Create safe local file path for document."""
    study_dir = output_dir / nct_id
    study_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_filename = re.sub(r"[^\w\-_\.]", "_", filename)
    return study_dir / safe_filename


async def _download_single_document(
    client: HttpClient,
    doc_info: DocumentInfo,
    output_dir: Path,
    max_size_mb: int = 50
) -> DocumentInfo:
    """
    Download a single document with error handling.
    
    Args:
        client: HTTP client (injected dependency)
        doc_info: Document information dictionary
        output_dir: Output directory for downloads
        max_size_mb: Maximum file size in MB
        
    Returns:
        Updated document info with download status
    """
    try:
        local_path = _create_safe_path(output_dir, doc_info["nct_id"], doc_info["filename"])

        # Skip if already exists
        if local_path.exists():
            doc_info["local_path"] = str(local_path)
            doc_info["file_size"] = local_path.stat().st_size
            doc_info["status"] = "skipped"
            return doc_info

        # Download with timeout and size limits
        response = await client.get(doc_info["url"], timeout=60.0)
        response.raise_for_status()

        content = response.content

        # Check file size
        if len(content) > max_size_mb * 1024 * 1024:
            doc_info["status"] = "failed"
            doc_info["error"] = f"File too large: {len(content) / 1024 / 1024:.1f}MB"
            return doc_info

        # Save file
        local_path.write_bytes(content)

        # Update document info
        doc_info["local_path"] = str(local_path)
        doc_info["file_size"] = len(content)
        doc_info["status"] = "downloaded"

        logger.debug(f"Downloaded {doc_info['nct_id']}/{doc_info['filename']} ({len(content) / 1024:.1f}KB)")

    except httpx.TimeoutException:
        doc_info["status"] = "failed"
        doc_info["error"] = "Download timeout"
    except httpx.HTTPStatusError as e:
        doc_info["status"] = "failed"
        doc_info["error"] = f"HTTP {e.response.status_code}"
    except Exception as e:
        doc_info["status"] = "failed"
        doc_info["error"] = str(e)
        logger.warning(f"Failed to download {doc_info['url']}: {e}")

    return doc_info


async def download_documents(
    documents: list[DocumentInfo],
    output_dir: Path,
    client_factory: Callable[[], HttpClient],
    max_concurrent: int = 10,
    max_size_mb: int = 50
) -> tuple[list[DocumentInfo], DownloadStats]:
    """
    Download documents with injected HTTP client factory.
    
    Args:
        documents: List of document info dictionaries
        output_dir: Directory to save documents
        client_factory: Function that creates HTTP client (dependency injection)
        max_concurrent: Maximum concurrent downloads
        max_size_mb: Maximum file size per document in MB
        
    Returns:
        Tuple of (updated_documents, download_stats)
    """
    if not documents:
        return [], _create_empty_stats()

    output_dir.mkdir(parents=True, exist_ok=True)

    # Use semaphore to limit concurrent downloads
    semaphore = asyncio.Semaphore(max_concurrent)

    async def download_with_limit(doc_info: DocumentInfo) -> DocumentInfo:
        async with semaphore:
            async with client_factory() as client:
                return await _download_single_document(client, doc_info, output_dir, max_size_mb)

    logger.info(f"Starting download of {len(documents)} documents with {max_concurrent} concurrent connections")

    # Download all documents
    updated_documents = await asyncio.gather(
        *[download_with_limit(doc) for doc in documents],
        return_exceptions=True
    )

    # Handle any exceptions from gather
    results = []
    for i, result in enumerate(updated_documents):
        if isinstance(result, Exception):
            doc_info = documents[i].copy()
            doc_info["status"] = "failed"
            doc_info["error"] = str(result)
            results.append(doc_info)
        else:
            results.append(result)

    # Calculate statistics
    stats = _calculate_download_stats(results)

    logger.info(
        f"Document download complete: {stats['downloaded']} downloaded, "
        f"{stats['failed']} failed, {stats['skipped']} skipped"
    )

    return results, stats


def _create_empty_stats() -> DownloadStats:
    """Create empty download statistics."""
    return {
        "total_documents": 0,
        "downloaded": 0,
        "failed": 0,
        "skipped": 0,
        "total_size_mb": 0.0,
        "studies_with_documents": 0
    }


def _calculate_download_stats(documents: list[DocumentInfo]) -> DownloadStats:
    """Calculate download statistics from document results."""
    stats = _create_empty_stats()
    stats["total_documents"] = len(documents)
    stats["studies_with_documents"] = len(set(doc["nct_id"] for doc in documents))

    for doc in documents:
        if doc["status"] == "downloaded":
            stats["downloaded"] += 1
            if doc["file_size"]:
                stats["total_size_mb"] += doc["file_size"] / (1024 * 1024)
        elif doc["status"] == "failed":
            stats["failed"] += 1
        elif doc["status"] == "skipped":
            stats["skipped"] += 1

    return stats


def save_document_metadata(documents: list[DocumentInfo], output_path: Path) -> None:
    """
    Save document metadata to parquet file.
    
    Args:
        documents: List of document information
        output_path: Path to save metadata parquet file
    """
    if not documents:
        logger.warning("No document metadata to save")
        return

    df = pl.DataFrame(documents)
    df.write_parquet(output_path)
    logger.info(f"Saved document metadata for {len(documents)} documents to {output_path}")


def create_httpx_client() -> HttpClient:
    """
    Create HTTP client with appropriate settings for document downloads.
    
    Returns:
        Configured httpx.AsyncClient
    """
    return httpx.AsyncClient(
        timeout=httpx.Timeout(60.0),
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
        headers={"User-Agent": "ClintrAI Document Downloader 1.0"}
    )


async def process_document_downloads(
    harmonized_df: pl.DataFrame,
    output_dir: Path,
    max_concurrent: int = 10,
    max_size_mb: int = 50
) -> tuple[list[DocumentInfo], DownloadStats]:
    """
    Main function to process document downloads from harmonized data.
    
    Args:
        harmonized_df: DataFrame with document URLs
        output_dir: Directory to save documents and metadata
        max_concurrent: Maximum concurrent downloads
        max_size_mb: Maximum file size per document in MB
        
    Returns:
        Tuple of (document_records, download_stats)
    """
    logger.info("Starting document download process")

    # Extract document information
    documents = extract_document_info(harmonized_df)

    if not documents:
        logger.warning("No documents found to download")
        return [], _create_empty_stats()

    # Download documents with dependency injection
    updated_documents, stats = await download_documents(
        documents,
        output_dir / "documents",
        create_httpx_client,  # Injected client factory
        max_concurrent,
        max_size_mb
    )

    # Save metadata
    metadata_path = output_dir / "document_metadata.parquet"
    save_document_metadata(updated_documents, metadata_path)

    # Log summary
    logger.info("Document download summary:")
    logger.info(f"  Studies with documents: {stats['studies_with_documents']:,}")
    logger.info(f"  Total documents: {stats['total_documents']:,}")
    logger.info(f"  Downloaded: {stats['downloaded']:,}")
    logger.info(f"  Failed: {stats['failed']:,}")
    logger.info(f"  Skipped: {stats['skipped']:,}")
    logger.info(f"  Total size: {stats['total_size_mb']:.1f} MB")

    return updated_documents, stats
