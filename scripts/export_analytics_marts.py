"""CLI for exporting analytics marts to partitioned Parquet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from clintrai.analytics.marts import export_analytics_marts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export analytics marts from canonical parquet sources")
    parser.add_argument("--canonical-dir", required=True, type=Path, help="Directory with canonical parquet tables")
    parser.add_argument("--output-dir", required=True, type=Path, help="Output root for analytics marts")
    parser.add_argument("--snapshot-id", required=True, help="Snapshot id for parquet partitioning")
    parser.add_argument("--benchmark-runs", type=int, default=3, help="Number of benchmark query runs per mart")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = export_analytics_marts(
        canonical_dir=args.canonical_dir,
        output_dir=args.output_dir,
        source_snapshot_id=args.snapshot_id,
        benchmark_runs=args.benchmark_runs,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
