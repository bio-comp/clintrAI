"""Shared types and enums for clinical trial data models."""

from __future__ import annotations

from enum import Enum


class DeduplicationStrategy(str, Enum):
    """Strategy for handling duplicate records between CSV and JSON sources."""
    
    JSON_PRIORITY = "json_priority"
    CSV_PRIORITY = "csv_priority"
    MERGE_ALL = "merge_all"


class DataSource(str, Enum):
    """Source of clinical trial data."""
    
    CSV_ONLY = "csv_only"
    JSON_ONLY = "json_only"
    JSON_PRIORITY = "json_priority"
    CSV_FALLBACK = "csv_fallback"
    MERGED = "merged"


class DocumentSource(str, Enum):
    """Source of document reference."""
    
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
    EXTERNAL = "external"


class DocumentType(str, Enum):
    """Type of clinical trial document."""
    
    PROTOCOL = "protocol"
    SAP = "sap"  # Statistical Analysis Plan
    ICF = "icf"  # Informed Consent Form
    CSR = "csr"  # Clinical Study Report
    RESULTS = "results"
    SUMMARY = "summary"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Status of data processing."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FileFormat(str, Enum):
    """Supported file formats."""
    
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    PDF = "pdf"
    TXT = "txt"
    XML = "xml"