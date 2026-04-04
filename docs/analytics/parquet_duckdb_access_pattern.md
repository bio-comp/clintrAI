# Parquet Analytics Marts + DuckDB Access Pattern

This document defines the analytics marts for issue #7 and the expected query/benchmark workflow.

## Fact Marts
The export pipeline defines five fact-table outputs:
- `trial_fact`
- `arm_fact`
- `endpoint_fact`
- `site_fact`
- `publication_fact`

Each mart is exported as partitioned Parquet under:
- `<output_root>/<fact_table>/source_snapshot_id=<snapshot_id>/*.parquet`

## Canonical to Mart Mapping
| Fact Mart | Canonical Source Table |
|---|---|
| `trial_fact` | `trial` |
| `arm_fact` | `arm` |
| `endpoint_fact` | `endpoint` |
| `site_fact` | `site` |
| `publication_fact` | `publication` |

The export pipeline also writes `mart_lineage_map.json` to preserve table-level lineage mapping.

## Export Pipeline
Use the CLI wrapper:

```bash
python scripts/export_analytics_marts.py \
  --canonical-dir ./canonical_parquet \
  --output-dir ./analytics_marts \
  --snapshot-id snapshot-2026-04-03 \
  --benchmark-runs 5
```

This writes:
- partitioned mart parquet datasets,
- `mart_lineage_map.json`,
- `mart_export_benchmarks.json`.

## DuckDB Query Examples
```sql
-- Total rows in a mart snapshot
select count(*)
from read_parquet('analytics_marts/trial_fact/source_snapshot_id=snapshot-2026-04-03/*.parquet');

-- Trial status trend slice
select overall_status, count(*) as trials
from read_parquet('analytics_marts/trial_fact/source_snapshot_id=snapshot-2026-04-03/*.parquet')
group by overall_status
order by trials desc;

-- Publication counts by journal
select journal, count(*) as publications
from read_parquet('analytics_marts/publication_fact/source_snapshot_id=snapshot-2026-04-03/*.parquet')
group by journal
order by publications desc
limit 20;
```

## Benchmark Notes
`mart_export_benchmarks.json` includes per-mart metrics:
- `export_seconds`
- `median_query_seconds`
- `row_count`
- `benchmark_runs`

Use these metrics as baseline benchmarks and compare deltas by snapshot/version.
