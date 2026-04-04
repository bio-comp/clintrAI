"""Tests for Parquet analytics mart export and DuckDB access pattern."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from clintrai.analytics.marts import export_analytics_marts


def _write_canonical_sources(canonical_dir: Path) -> None:
    canonical_dir.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        {
            "trial_id": [1, 2],
            "nct_id": ["NCT0001", "NCT0002"],
            "overall_status": ["COMPLETED", "RECRUITING"],
        }
    ).write_parquet(canonical_dir / "trial.parquet")

    pl.DataFrame(
        {
            "arm_id": [10, 11],
            "trial_id": [1, 2],
            "arm_label": ["Control", "Treatment"],
        }
    ).write_parquet(canonical_dir / "arm.parquet")

    pl.DataFrame(
        {
            "endpoint_id": [100, 101],
            "trial_id": [1, 2],
            "endpoint_name": ["OS", "PFS"],
        }
    ).write_parquet(canonical_dir / "endpoint.parquet")

    pl.DataFrame(
        {
            "site_id": [200, 201],
            "trial_id": [1, 2],
            "country": ["US", "CA"],
        }
    ).write_parquet(canonical_dir / "site.parquet")

    pl.DataFrame(
        {
            "publication_id": [300, 301],
            "trial_id": [1, 2],
            "journal": ["NEJM", "JAMA"],
        }
    ).write_parquet(canonical_dir / "publication.parquet")


def test_export_analytics_marts_writes_partitioned_parquet_and_lineage_map(tmp_path):
    """Export should create required fact marts partitioned by snapshot with lineage map."""
    canonical_dir = tmp_path / "canonical"
    output_dir = tmp_path / "analytics_marts"
    snapshot_id = "snapshot-analytics-001"

    _write_canonical_sources(canonical_dir)

    results = export_analytics_marts(
        canonical_dir=canonical_dir,
        output_dir=output_dir,
        source_snapshot_id=snapshot_id,
        benchmark_runs=2,
    )

    required_facts = {
        "trial_fact": "trial",
        "arm_fact": "arm",
        "endpoint_fact": "endpoint",
        "site_fact": "site",
        "publication_fact": "publication",
    }

    assert set(results.keys()) == set(required_facts.keys())

    for fact_table, source_table in required_facts.items():
        partition_dir = output_dir / fact_table / f"source_snapshot_id={snapshot_id}"
        parquet_files = list(partition_dir.glob("*.parquet"))

        assert partition_dir.exists()
        assert parquet_files

        assert results[fact_table]["source_table"] == source_table
        assert results[fact_table]["row_count"] == 2
        assert results[fact_table]["benchmark_runs"] == 2

    lineage_map_path = output_dir / "mart_lineage_map.json"
    assert lineage_map_path.exists()

    lineage_map = json.loads(lineage_map_path.read_text(encoding="utf-8"))
    assert lineage_map["trial_fact"]["source_table"] == "trial"
    assert lineage_map["publication_fact"]["source_table"] == "publication"


def test_export_analytics_marts_writes_benchmark_summary(tmp_path):
    """Export should persist benchmark metrics for each mart."""
    canonical_dir = tmp_path / "canonical"
    output_dir = tmp_path / "analytics_marts"

    _write_canonical_sources(canonical_dir)

    export_analytics_marts(
        canonical_dir=canonical_dir,
        output_dir=output_dir,
        source_snapshot_id="snapshot-analytics-002",
        benchmark_runs=3,
    )

    benchmark_path = output_dir / "mart_export_benchmarks.json"
    assert benchmark_path.exists()

    benchmark_summary = json.loads(benchmark_path.read_text(encoding="utf-8"))
    assert set(benchmark_summary.keys()) == {
        "trial_fact",
        "arm_fact",
        "endpoint_fact",
        "site_fact",
        "publication_fact",
    }

    assert benchmark_summary["trial_fact"]["benchmark_runs"] == 3
    assert benchmark_summary["trial_fact"]["median_export_seconds"] >= 0.0
