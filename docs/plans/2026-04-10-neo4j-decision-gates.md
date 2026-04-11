# Decision Gates: When to Introduce Neo4j

Date: 2026-04-10  
Issue: #2  
Branch: `issue/2-decision-gates-neo4j-introduction`

## Goal
Define objective, measurable criteria for when to introduce Neo4j as a graph projection layer beyond the existing Postgres + pgvector architecture.

## Decision Policy
- Postgres remains the canonical system of record for structured entities and provenance.
- Neo4j is an optional projection layer for relationship-centric workloads only.
- Issue #5 ("Neo4j Projection for Relationship-Centric Exploration") should be started only when the gates below are met.

## Decision Matrix (Objective Thresholds)
All metrics are measured over a rolling 30-day window from production query logs and workload telemetry.

| Decision Signal | Metric | Stay on Postgres + pgvector | Introduce Neo4j (Gate Pass) |
|---|---|---|---|
| Multi-hop workload prevalence | Share of read queries requiring >= 4 relationship hops | < 15% | >= 25% |
| Path-query latency | p95 latency for multi-hop path queries with clinical filters | <= 1.5s | > 2.5s for 2 consecutive weeks |
| Query complexity debt | Number of recurring analyst/product queries requiring > 3 CTE layers or recursive SQL | < 10 | >= 20 |
| Product dependence on graph UX | Share of roadmap features blocked by neighborhood/path exploration | < 2 features/quarter | >= 4 features/quarter |
| Explainability requirement | Share of priority user stories requiring explicit path evidence (node/edge trails) | < 20% | >= 40% |
| Retrieval quality delta | Improvement in path-constrained evidence retrieval vs SQL baseline | < 10% lift | >= 20% lift in offline eval |

Interpretation:
- Default is `No-Go`.
- `Go` requires meeting at least 4 of 6 Neo4j gate-pass thresholds, including either latency or product-dependence gate.

## Cost and Operations Tradeoff

### Option A: Postgres + pgvector only (default)
Benefits:
- Single operational datastore for canonical entities, provenance, filtering, and vectors.
- Lower operational complexity (one persistence stack, one backup/restore policy, one on-call runbook).
- Simpler consistency model; no projection lag risk.

Costs/Limitations:
- Complex multi-hop and neighborhood exploration queries become harder to maintain.
- Recursive/CTE-heavy SQL can degrade readability and performance at scale.
- Explainable path-centric UX requires custom join logic and post-processing.

### Option B: Add Neo4j projection layer
Benefits:
- Native graph traversal for path, neighborhood, and relationship-centrality use cases.
- Cleaner modeling for sponsor -> trial -> arm -> intervention -> target -> biomarker -> endpoint networks.
- Better fit for graph-first product capabilities and explainable path outputs.

Costs/Risks:
- Additional infrastructure and licensing cost (managed graph service + backup + monitoring).
- New ETL/projection pipeline with lag and reconciliation risk.
- Increased operational load: schema governance in two systems, graph index tuning, incident response.
- Data consistency risk between canonical Postgres and graph projection if sync fails.

Operational expectation if adopted:
- One additional production service with explicit SLOs.
- Dedicated projection pipeline ownership and reconciliation checks.
- Added runbooks for graph restore, index rebuild, and projection backfill.

## Fallback Plan if Graph Projection Is Deferred
If gates are not met:
1. Keep Neo4j as `deferred`.
2. Continue optimizing graph-like queries in Postgres:
   - materialized relationship views,
   - targeted indexes,
   - precomputed path helper tables for highest-value use cases.
3. Instrument and store gate metrics monthly (query mix, latency, feature demand, retrieval lift).
4. Re-run this decision matrix at each quarterly architecture review.
5. Keep issue #5 open in backlog with explicit dependencies on gate metrics.

## Team Sign-Off Criteria (Go/No-Go)
A decision review is valid only when all artifacts below exist:
- 30-day workload report with gate metrics and raw query evidence.
- Cost estimate covering dev/staging/prod plus projected on-call/support impact.
- Projection design draft (source tables, edge/node schema, sync cadence, failure handling).
- Rollback plan describing how to disable graph reads without data loss.
- Named owners for data projection, operations, and incident response.

Approval rules:
- `Go` requires approval from Engineering Lead + Data Platform Owner + Product Lead.
- `No-Go` requires documenting the top two blocking gates and a remediation plan.

## Current Decision (As of 2026-04-10)
- Status: `No-Go` (defer Neo4j projection).
- Reason: Gate metrics not yet collected/validated in production telemetry.
- Next review: First quarterly architecture review after telemetry baseline is available.
