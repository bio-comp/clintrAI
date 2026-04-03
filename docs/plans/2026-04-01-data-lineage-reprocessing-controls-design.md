# Data Lineage + Reprocessing Controls Design

Date: 2026-04-01  
Issue: #4  
Branch: `issue/4-data-lineage-reprocessing-controls`

## Goal
Guarantee deterministic reprocessing and auditable lineage across Bronze/Silver/Gold layers with enforced quality gates on promotions.

## Problem Statement
We now have canonical schema and document chunk schema, but no first-class lineage model that can:
- deterministically identify dataset versions,
- encode parent/child lineage between layer outputs,
- guarantee idempotent replay/backfill requests,
- block promotions when quality checks fail.

Without this layer, reproducibility and auditability remain procedural instead of enforced by schema-level controls.

## Alternatives Considered
1. Application-only lineage ledger (no DB constraints)
- Pros: fastest to build, flexible.
- Cons: weak guarantees; idempotency and promotion gates rely on app discipline.

2. Database-enforced lineage core (chosen)
- Pros: deterministic version IDs, unique idempotency keys, trigger-enforced quality gate.
- Cons: adds SQL complexity and migration ownership.

3. Event-sourcing only in object storage/logs
- Pros: append-only history and cheap storage.
- Cons: weak transactional joins to canonical entities; harder blocking guarantees.

## Chosen Design
Implement a SQL migration that adds lineage primitives and guardrails:
- `data_layer` enum: `bronze`, `silver`, `gold`
- `pipeline_run`: immutable run identity and run-level reproducibility inputs
- `dataset_version`: deterministic `version_id` generated from layer + dataset + snapshot + fingerprints
- `lineage_edge`: DAG edges between dataset versions
- `reprocessing_request`: idempotent replay/backfill requests via unique `idempotency_key`
- `quality_check_result`: persisted gate outputs
- `layer_promotion`: promotion attempts
- `enforce_quality_gate_before_promotion` trigger: blocks promotion unless a passed quality result exists

## Data Flow
1. Pipeline run starts and records `pipeline_run` with deterministic inputs.
2. Outputs create `dataset_version` rows in Bronze/Silver/Gold.
3. Transform dependencies are linked via `lineage_edge`.
4. Replay/backfill is requested with `idempotency_key`; duplicates collapse at DB layer.
5. Quality checks write `quality_check_result`.
6. Promotion insert into `layer_promotion` succeeds only if the quality gate is passed.

## Determinism and Idempotency Model
- Deterministic versioning: `version_id` is generated using an MD5 expression of stable inputs.
- Replay/backfill idempotency: unique `idempotency_key` prevents duplicate logical requests.
- Promotion safety: trigger blocks invalid promotions even if application logic misbehaves.

## Testing Strategy
Use SQL contract tests (file-content assertions) to verify:
- Bronze/Silver/Gold layer typing,
- deterministic `dataset_version.version_id` generation,
- idempotent reprocessing controls,
- trigger-based quality gate enforcement artifacts.

## Out of Scope
- Runtime orchestration integration with Metaflow steps.
- Population logic for quality check suites.
- UI/reporting layer for lineage visualization.

## Rollout
1. Apply migration `0003_data_lineage_reprocessing_controls.sql`.
2. Validate schema contracts in CI.
3. In follow-up issue(s), connect pipeline execution to these tables.
