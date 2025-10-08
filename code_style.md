# ClinTrAI Code Style Guide

## Overview

This document defines coding standards and best practices for the ClinTrAI clinical trials data processing pipeline. The goal is to maintain consistent, readable, performant, and maintainable code that follows modern Python conventions.

## Core Principles

### 1. Python Version & Modern Syntax
- **Target Python 3.12+**
- Use modern type hints with built-in types
- Leverage new language features for cleaner code

### 2. The Zen of Python
Follow PEP 20 principles:
- Beautiful is better than ugly
- Explicit is better than implicit
- Simple is better than complex
- Readability counts
- There should be one obvious way to do it

## Type Annotations

### ✅ Preferred (Modern Python 3.10+)
```python
from typing import TypeAlias

# Use built-in types
def process_data(studies: list[dict]) -> dict[str, int]:
    """Process clinical trials data."""
    return {"count": len(studies)}

# Use union operator for optional types
def get_study(nct_id: str) -> Study | None:
    """Retrieve study by NCT ID."""
    return database.get(nct_id)

# Use TypeAlias for complex, reusable types to improve readability
StudyData: TypeAlias = dict[str, str | int | list[str]]
ProcessingResult: TypeAlias = dict[str, list[str] | int]
EmbeddingVector: TypeAlias = list[float]

def combine_results(results: list[StudyData]) -> ProcessingResult:
    """Combine processing results using clear type aliases."""
    pass

def generate_embeddings(texts: list[str]) -> list[EmbeddingVector]:
    """Generate embeddings with clear return type."""
    pass
```

### ❌ Avoid (Legacy typing module)
```python
from typing import List, Dict, Optional, Union

# Don't use these legacy forms
def process_data(studies: List[Dict]) -> Dict[str, int]:
    pass

def get_study(nct_id: str) -> Optional[Study]:
    pass
```

## Dependency Injection

### ✅ Preferred Pattern
```python
# Pure functions with injected dependencies
def harmonize_data(
    csv_path: Path,
    json_dir: Path,
    strategy: DeduplicationStrategy,
    csv_processor: Callable,
    json_processor: Callable,
) -> tuple[pl.DataFrame, dict]:
    """Harmonize data using injected processors."""
    csv_df = csv_processor(csv_path)
    json_df = json_processor(json_dir)
    return merge_data(csv_df, json_df, strategy)

# Testable and flexible
class NLPProcessor:
    def __init__(
        self,
        model_loader: Callable[[str], spacy.Language],
        tokenizer: Callable[[str], list[str]],
    ):
        self.model_loader = model_loader
        self.tokenizer = tokenizer
```

### ❌ Avoid (Hard Dependencies)
```python
# Don't hardcode dependencies
def harmonize_data(csv_path: Path, json_dir: Path):
    # Hard to test and inflexible
    csv_df = prepare_csv_df(csv_path)  # Hardcoded function
    json_df = prepare_json_df(json_dir)  # Hardcoded function
```

## Enum Usage

### ✅ Use Centralized Enums from API Documentation
```python
# Reference: docs/apis/clinical_trials_dot_gov/enums.md
from clintrai.models.types import (
    StudyStatus,
    StudyPhase,
    CSVFieldName,
    DeduplicationStrategy,
)

# Use enum values consistently
def filter_studies(status: StudyStatus) -> pl.DataFrame:
    return df.filter(pl.col("status") == status.value)

# API-aligned enums
class OverallStatus(str, Enum):
    """From ClinicalTrials.gov API enums endpoint."""
    RECRUITING = "RECRUITING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
```

### ❌ Avoid Magic Strings
```python
# Don't use hardcoded strings
def filter_studies(df):
    return df.filter(pl.col("status") == "recruiting")  # Error-prone
```

## Async Programming

### ✅ Use Async for I/O-Bound Operations
```python
import asyncio
import httpx

async def fetch_study(client: httpx.AsyncClient, nct_id: str) -> dict:
    """Fetch single study asynchronously."""
    response = await client.get(f"/studies/{nct_id}")
    return response.json()

async def fetch_multiple_studies(nct_ids: list[str]) -> list[dict]:
    """Fetch multiple studies concurrently using async client."""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"/studies/{nct_id}") for nct_id in nct_ids
        ]
        responses = await asyncio.gather(*tasks)
    return [resp.json() for resp in responses]

# Use in Metaflow steps where the primary work is network I/O
@step
async def download_documents(self):
    """Download documents asynchronously."""
    urls = self.document_urls
    async with httpx.AsyncClient() as client:
        documents = await asyncio.gather(*[
            download_document(client, url) for url in urls
        ])
    self.documents = documents
```

### ❌ Avoid Using Async for CPU-Bound Work
```python
import time
import asyncio

# This function does heavy computation, not I/O
def cpu_bound_task(data: list[int]) -> int:
    """Simulates heavy, blocking computation."""
    time.sleep(2)  # Simulates CPU work
    return sum(data)

async def process_data_incorrectly(data_list: list[list[int]]) -> list[int]:
    """❌ Incorrect: Using async for CPU-bound work blocks the event loop."""
    # This will run sequentially, not concurrently!
    # Each cpu_bound_task blocks the entire event loop
    tasks = [cpu_bound_task(data) for data in data_list]
    results = await asyncio.gather(*tasks)  # Incorrect use of gather
    return results

# ✅ Correct approach for CPU-bound work
from concurrent.futures import ProcessPoolExecutor

def process_data_correctly(data_list: list[list[int]]) -> list[int]:
    """✅ Correct: Use ProcessPoolExecutor for CPU-bound work."""
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(cpu_bound_task, data_list))
    return results
```

## Vectorization with Polars

### ✅ Preferred (Vectorized Operations)
```python
# Use Polars expressions for data processing
def process_clinical_data(df: pl.DataFrame) -> pl.DataFrame:
    """Process clinical trials data using vectorized operations."""
    return (
        df.with_columns([
            # Combine text fields vectorially
            pl.concat_str([
                pl.col("title").fill_null(""),
                pl.col("brief_summary").fill_null(""),
            ], separator=" ").alias("combined_text"),
            
            # Extract year from date
            pl.col("start_date").str.strptime(pl.Date).dt.year().alias("start_year"),
            
            # Calculate text metrics
            pl.col("title").str.len_chars().alias("title_length"),
        ])
        .filter(pl.col("combined_text").str.len_chars() > 0)
        .with_columns(
            # Assign shards using hash
            (pl.col("nct_id").hash() % 256).alias("shard_id")
        )
    )
```

### ❌ Avoid (Row-by-Row Processing)
```python
# Don't iterate through rows
def process_clinical_data(df: pl.DataFrame) -> pl.DataFrame:
    processed_rows = []
    for row in df.iter_rows(named=True):  # Slow!
        # Process each row individually
        processed_rows.append(process_row(row))
    return pl.DataFrame(processed_rows)
```

## NLP with spaCy

### ✅ Modern NLP Patterns
```python
import spacy
from spacy.lang.en import English

def create_nlp_pipeline(
    model_name: str = "en_core_web_sm",
    disable_components: list[str] | None = None,
) -> spacy.Language:
    """Create optimized spaCy pipeline."""
    if disable_components is None:
        disable_components = ["parser", "ner"]  # Disable if not needed
    
    nlp = spacy.load(model_name, disable=disable_components)
    
    # Add custom components if needed
    if "custom_tokenizer" not in nlp.pipe_names:
        nlp.add_pipe("custom_tokenizer", first=True)
    
    return nlp

def extract_features_batch(
    texts: list[str],
    nlp: spacy.Language,
    batch_size: int = 1000,
) -> list[dict]:
    """Extract NLP features in batches for efficiency."""
    features = []
    
    for doc in nlp.pipe(texts, batch_size=batch_size):
        features.append({
            "token_count": len([t for t in doc if not t.is_stop]),
            "entities": [(ent.text, ent.label_) for ent in doc.ents],
            "sentences": len(list(doc.sents)),
        })
    
    return features
```

## Database Integration (PostgreSQL + pgvector)

### ✅ Async Database Operations
```python
import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector

async def store_embeddings(
    embeddings_df: pl.DataFrame,
    connection_string: str,
) -> None:
    """Store embeddings in PostgreSQL efficiently using vectorized operations."""
    conn = await asyncpg.connect(connection_string)
    await register_vector(conn)
    
    # ✅ Vectorized approach: prepare data without row-by-row iteration
    records = (
        embeddings_df
        .select([
            "nct_id",
            pl.col("embedding").map_elements(
                lambda x: np.array(x), 
                return_dtype=pl.Object
            ).alias("embedding_array")
        ])
        .rows()
    )
    
    await conn.executemany(
        """
        INSERT INTO clinical_trial_embeddings (nct_id, embedding) 
        VALUES ($1, $2) 
        ON CONFLICT (nct_id) DO UPDATE SET embedding = EXCLUDED.embedding
        """,
        records
    )
    
    await conn.close()

async def search_similar_studies(
    query_embedding: np.ndarray,
    limit: int = 10,
    connection_string: str,
) -> list[dict]:
    """Search for similar studies using vector similarity."""
    conn = await asyncpg.connect(connection_string)
    await register_vector(conn)
    
    rows = await conn.fetch(
        """
        SELECT nct_id, embedding <-> $1 as distance
        FROM clinical_trial_embeddings
        ORDER BY distance
        LIMIT $2
        """,
        query_embedding,
        limit
    )
    
    await conn.close()
    return [dict(row) for row in rows]
```

## Container & Kubernetes Readiness

### ✅ Docker Best Practices
```dockerfile
# Use multi-stage Dockerfile for smaller, more secure production images
FROM python:3.12-slim as builder

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && poetry install --no-dev --no-interaction --no-ansi

# Final, smaller production image
FROM python:3.12-slim as production
WORKDIR /app
COPY --from=builder /app/.venv /.venv
COPY clintrai/ ./clintrai/

# The CMD should run the application service (e.g., an API),
# not the Metaflow pipeline itself. Metaflow's runtime handles pipeline execution.
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "clintrai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```python
# Environment-aware configuration
import os
from pathlib import Path

def get_config() -> dict:
    """Get configuration from environment variables."""
    return {
        "database_url": os.getenv("DATABASE_URL", "postgresql://localhost:5432/clintrai"),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "model_cache_dir": Path(os.getenv("MODEL_CACHE_DIR", "/tmp/models")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }
```

### ✅ Kubernetes Health Checks
```python
# clintrai/api/main.py
from fastapi import FastAPI, HTTPException
import asyncpg
import os

app = FastAPI()

@app.get("/healthz", status_code=200)
async def health_check():
    """Kubernetes liveness probe: checks if the service is running."""
    return {"status": "ok"}

@app.get("/readyz", status_code=200)
async def readiness_check():
    """Kubernetes readiness probe: checks if the service can handle requests."""
    try:
        # Check critical dependencies like the database
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"), timeout=5)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return {"status": "ready"}
    except Exception as e:
        # Service is running but not ready for traffic
        raise HTTPException(
            status_code=503, 
            detail=f"Database connection failed: {e}"
        )
```

## Error Handling

### ✅ Specific Exception Handling
```python
from loguru import logger

async def robust_api_call(url: str, max_retries: int = 3) -> dict:
    """Make API call with proper error handling."""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                await asyncio.sleep(60)  # Wait before retry
                continue
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error calling {url}: {e}")
            raise
```

## Logging

### ✅ Structured Logging with Loguru
```python
from loguru import logger
import sys

# Configure structured logging
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level="INFO",
    serialize=True,  # JSON output for production
)

# Use context in logs
def process_study(nct_id: str) -> dict:
    """Process a single study with contextual logging."""
    with logger.contextualize(nct_id=nct_id):
        logger.info("Starting study processing")
        
        try:
            result = expensive_operation(nct_id)
            logger.info("Study processing completed", records_processed=len(result))
            return result
            
        except Exception as e:
            logger.error("Study processing failed", error=str(e))
            raise
```

## Testing Patterns

### ✅ Dependency Injection for Testing
```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
async def mock_http_client():
    """Mock HTTP client for testing."""
    client = AsyncMock()
    client.get.return_value.json.return_value = {"nct_id": "NCT12345"}
    return client

async def test_study_fetcher(mock_http_client):
    """Test study fetching with mocked dependencies."""
    fetcher = StudyFetcher(http_client=mock_http_client)
    result = await fetcher.get_study("NCT12345")
    
    assert result["nct_id"] == "NCT12345"
    mock_http_client.get.assert_called_once()
```

## Performance Guidelines

### ✅ Optimization Patterns
```python
# Use appropriate data structures
from collections import defaultdict, Counter
import polars as pl

def efficient_grouping(df: pl.DataFrame) -> dict[str, int]:
    """Efficient grouping using Polars."""
    return (
        df.group_by("study_type")
        .agg(pl.count().alias("count"))
        .to_dict(as_series=False)
    )

# Lazy evaluation
def lazy_data_pipeline(file_path: str) -> pl.LazyFrame:
    """Use lazy evaluation for large datasets."""
    return (
        pl.scan_csv(file_path)
        .filter(pl.col("status") == "RECRUITING")
        .select(["nct_id", "title", "brief_summary"])
        .with_columns(
            pl.col("title").str.len_chars().alias("title_length")
        )
    )  # Not executed until .collect() is called
```

## File Organization

```
clintrai/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── client.py          # HTTP client with dependency injection
│   ├── studies.py         # API functions
│   └── exceptions.py      # Custom exceptions
├── metaflow/
│   ├── __init__.py
│   ├── clinical_trials_flow.py    # Main pipeline
│   ├── harmonization.py           # Data harmonization logic
│   ├── nlp_processing.py         # NLP functions
│   └── embeddings.py             # Embedding generation
├── models/
│   ├── __init__.py
│   ├── types.py           # Enums and type definitions
│   ├── api_models.py      # API response models
│   └── database.py        # Database models
└── utils/
    ├── __init__.py
    ├── config.py          # Configuration management
    └── logging.py         # Logging setup
```

## Code Quality Tools

### Required Tools
- **Formatter**: `ruff format` (replaces black)
- **Linter**: `ruff check` (replaces flake8, isort, etc.)
- **Type Checker**: `mypy`
- **Security**: `bandit`

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
```

## Documentation

### ✅ Docstring Format
```python
def harmonize_clinical_data(
    csv_path: Path,
    json_dir: Path,
    strategy: DeduplicationStrategy,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """
    Harmonize clinical trials data from multiple sources.
    
    Combines CSV and JSON data sources using the specified deduplication
    strategy. Handles schema validation and field mapping according to
    ClinicalTrials.gov API specifications.
    
    Args:
        csv_path: Path to the CSV file containing clinical trials data
        json_dir: Directory containing individual JSON study files
        strategy: Strategy for handling overlapping records
        
    Returns:
        Tuple containing:
            - Harmonized DataFrame with standardized schema
            - Statistics dictionary with processing metrics
            
    Raises:
        FileNotFoundError: If CSV file or JSON directory doesn't exist
        ValidationError: If data doesn't match expected schema
        
    Example:
        >>> df, stats = harmonize_clinical_data(
        ...     Path("studies.csv"),
        ...     Path("json_studies/"),
        ...     DeduplicationStrategy.JSON_PRIORITY
        ... )
        >>> print(f"Processed {stats['total_records']} records")
    """
```

This style guide ensures code is modern, performant, testable, and maintainable while following Python best practices and being optimized for clinical trials data processing workflows.