"""Parquet analytics marts export using DuckDB."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
import statistics
import time

import duckdb

FACT_TABLE_SOURCE_MAP: dict[str, str] = {
    "trial_fact": "trial",
    "arm_fact": "arm",
    "endpoint_fact": "endpoint",
    "site_fact": "site",
    "publication_fact": "publication",
}


@dataclass(frozen=True)
class MartExportResult:
    """Summary of a single mart export."""

    source_table: str
    row_count: int
    benchmark_runs: int
    export_seconds: float
    median_query_seconds: float
    partition_path: str


def _sql_quote(value: str) -> str:
    return value.replace("'", "''")


def _source_path(canonical_dir: Path, source_table: str) -> Path:
    return canonical_dir / f"{source_table}.parquet"


def _export_mart(
    connection: duckdb.DuckDBPyConnection,
    source_path: Path,
    fact_output_dir: Path,
    source_snapshot_id: str,
) -> tuple[int, float, Path]:
    fact_output_dir.mkdir(parents=True, exist_ok=True)

    source_path_sql = _sql_quote(str(source_path))
    fact_output_dir_sql = _sql_quote(str(fact_output_dir))
    snapshot_sql = _sql_quote(source_snapshot_id)

    start = time.perf_counter()
    connection.execute(
        f"""
        copy (
            select
                src.*,
                '{snapshot_sql}' as source_snapshot_id,
                now()::timestamptz as exported_at
            from read_parquet('{source_path_sql}') as src
        )
        to '{fact_output_dir_sql}'
        (format parquet, partition_by (source_snapshot_id), overwrite_or_ignore true);
        """
    )
    export_seconds = time.perf_counter() - start

    partition_path = fact_output_dir / f"source_snapshot_id={source_snapshot_id}"

    row_count = connection.execute(
        f"""
        select count(*)
        from read_parquet('{_sql_quote(str(partition_path / "*.parquet"))}')
        """
    ).fetchone()[0]

    return int(row_count), export_seconds, partition_path


def _benchmark_query(
    connection: duckdb.DuckDBPyConnection,
    partition_path: Path,
    benchmark_runs: int,
) -> float:
    durations: list[float] = []
    partition_glob_sql = _sql_quote(str(partition_path / "*.parquet"))

    for _ in range(max(1, benchmark_runs)):
        start = time.perf_counter()
        connection.execute(
            f"""
            select count(*)
            from read_parquet('{partition_glob_sql}')
            """
        ).fetchone()
        durations.append(time.perf_counter() - start)

    return float(statistics.median(durations))


def export_analytics_marts(
    canonical_dir: Path,
    output_dir: Path,
    source_snapshot_id: str,
    benchmark_runs: int = 3,
    fact_table_source_map: Mapping[str, str] | None = None,
) -> dict[str, dict[str, int | float | str]]:
    """
    Export canonical tables to partitioned Parquet fact marts with benchmark metadata.

    Args:
        canonical_dir: Directory containing canonical source parquet files.
        output_dir: Root output directory for fact marts.
        source_snapshot_id: Snapshot identifier used as parquet partition key.
        benchmark_runs: Number of DuckDB query benchmark runs per mart.
        fact_table_source_map: Optional override of fact->source table mapping.

    Returns:
        Dictionary keyed by fact table with export and benchmark metadata.
    """
    mapping = dict(fact_table_source_map or FACT_TABLE_SOURCE_MAP)

    missing_sources = [
        source_table
        for source_table in mapping.values()
        if not _source_path(canonical_dir, source_table).exists()
    ]
    if missing_sources:
        raise FileNotFoundError(
            "Missing canonical parquet source files for: " + ", ".join(sorted(missing_sources))
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, MartExportResult] = {}
    lineage_map: dict[str, dict[str, str]] = {}
    benchmark_summary: dict[str, dict[str, int | float | str]] = {}

    connection = duckdb.connect()
    try:
        for fact_table, source_table in mapping.items():
            source_path = _source_path(canonical_dir, source_table)
            fact_output_dir = output_dir / fact_table

            row_count, export_seconds, partition_path = _export_mart(
                connection=connection,
                source_path=source_path,
                fact_output_dir=fact_output_dir,
                source_snapshot_id=source_snapshot_id,
            )
            median_query_seconds = _benchmark_query(
                connection=connection,
                partition_path=partition_path,
                benchmark_runs=benchmark_runs,
            )

            result = MartExportResult(
                source_table=source_table,
                row_count=row_count,
                benchmark_runs=benchmark_runs,
                export_seconds=float(export_seconds),
                median_query_seconds=median_query_seconds,
                partition_path=str(partition_path),
            )
            results[fact_table] = result

            lineage_map[fact_table] = {
                "source_table": source_table,
                "source_parquet": str(source_path),
                "fact_parquet_dir": str(fact_output_dir),
                "partition_key": "source_snapshot_id",
            }
            benchmark_summary[fact_table] = {
                "benchmark_runs": benchmark_runs,
                "export_seconds": result.export_seconds,
                "median_export_seconds": result.export_seconds,
                "median_query_seconds": result.median_query_seconds,
                "row_count": result.row_count,
            }
    finally:
        connection.close()

    (output_dir / "mart_lineage_map.json").write_text(
        json.dumps(lineage_map, indent=2),
        encoding="utf-8",
    )
    (output_dir / "mart_export_benchmarks.json").write_text(
        json.dumps(benchmark_summary, indent=2),
        encoding="utf-8",
    )

    return {
        fact_table: {
            "source_table": result.source_table,
            "row_count": result.row_count,
            "benchmark_runs": result.benchmark_runs,
            "export_seconds": result.export_seconds,
            "median_query_seconds": result.median_query_seconds,
            "partition_path": result.partition_path,
        }
        for fact_table, result in results.items()
    }
