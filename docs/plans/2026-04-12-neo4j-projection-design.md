# Neo4j Projection Design for Relationship-Centric Exploration

Date: 2026-04-12  
Issue: #5  
Branch: `issue/5-neo4j-projection-relationship-centric-exploration`

## Goal
Define a derived Neo4j projection for multi-hop exploration workloads while keeping Postgres as the single authoritative source of truth.

## Authority Boundary (Required)
- Canonical authority remains in Postgres.
- Neo4j is a read-optimized projection only.
- No writes originate from Neo4j back into canonical entities.
- If projection and canonical data disagree, Postgres wins and projection is rebuilt/replayed.

## Graph Schema as a Projection from Canonical Postgres

### Node Labels and Source Mapping
| Node Label | Canonical Source |
|---|---|
| `Trial` | `trial` |
| `Sponsor` | `sponsor` |
| `Arm` | `arm` |
| `Intervention` | `intervention` |
| `Condition` | `condition` |
| `Biomarker` | `biomarker` |
| `Endpoint` | `endpoint` |
| `Publication` | `publication` |
| `Site` | `site` |

### Relationship Types and Source Mapping
| Relationship | Canonical Derivation |
|---|---|
| `(:Sponsor)-[:SPONSORS]->(:Trial)` | `trial.sponsor_id -> sponsor.sponsor_id` |
| `(:Trial)-[:HAS_ARM]->(:Arm)` | `arm.trial_id -> trial.trial_id` |
| `(:Trial)-[:HAS_INTERVENTION]->(:Intervention)` | `intervention.trial_id -> trial.trial_id` |
| `(:Trial)-[:STUDIES]->(:Condition)` | `condition.trial_id -> trial.trial_id` |
| `(:Trial)-[:MEASURES]->(:Endpoint)` | `endpoint.trial_id -> trial.trial_id` |
| `(:Trial)-[:HAS_BIOMARKER]->(:Biomarker)` | `biomarker.trial_id -> trial.trial_id` |
| `(:Trial)-[:HAS_PUBLICATION]->(:Publication)` | `publication.trial_id -> trial.trial_id` |
| `(:Trial)-[:HAS_SITE]->(:Site)` | `site.trial_id -> trial.trial_id` |

### Required Node Identity Keys
- `Trial.trial_id` and `Trial.nct_id`
- `{Entity}.<table>_id` for each projected entity
- `source_snapshot_id` on every projected node and relationship for lineage

### Required Constraints and Indexes (Neo4j)
```cypher
CREATE CONSTRAINT trial_id_unique IF NOT EXISTS
FOR (t:Trial) REQUIRE t.trial_id IS UNIQUE;

CREATE CONSTRAINT sponsor_id_unique IF NOT EXISTS
FOR (s:Sponsor) REQUIRE s.sponsor_id IS UNIQUE;

CREATE CONSTRAINT arm_id_unique IF NOT EXISTS
FOR (a:Arm) REQUIRE a.arm_id IS UNIQUE;

CREATE CONSTRAINT intervention_id_unique IF NOT EXISTS
FOR (i:Intervention) REQUIRE i.intervention_id IS UNIQUE;

CREATE CONSTRAINT condition_id_unique IF NOT EXISTS
FOR (c:Condition) REQUIRE c.condition_id IS UNIQUE;

CREATE CONSTRAINT biomarker_id_unique IF NOT EXISTS
FOR (b:Biomarker) REQUIRE b.biomarker_id IS UNIQUE;

CREATE CONSTRAINT endpoint_id_unique IF NOT EXISTS
FOR (e:Endpoint) REQUIRE e.endpoint_id IS UNIQUE;

CREATE CONSTRAINT publication_id_unique IF NOT EXISTS
FOR (p:Publication) REQUIRE p.publication_id IS UNIQUE;

CREATE CONSTRAINT site_id_unique IF NOT EXISTS
FOR (s:Site) REQUIRE s.site_id IS UNIQUE;

CREATE INDEX trial_nct_id IF NOT EXISTS
FOR (t:Trial) ON (t.nct_id);
```

## ETL Sync Strategy (Incremental + Replay)

### Bootstrap (Initial Full Load)
1. Export canonical entities from Postgres in deterministic entity order.
2. Load nodes via `MERGE` on immutable IDs.
3. Load relationships via `MERGE` on node IDs and relationship type.
4. Stamp `source_snapshot_id` and `projected_at`.

### Incremental Sync
- Watermark input: `updated_at` + `source_snapshot_id` from canonical tables.
- Pull changed rows since last successful watermark.
- Upsert nodes and relationships with `MERGE`.
- Soft deletes represented with `is_active=false` on nodes/relationships when canonical row is no longer valid.
- Persist sync checkpoints in a Postgres table (`graph_projection_checkpoint`) to keep auditability near canonical lineage.

### Replay / Backfill
- Triggered by explicit snapshot range or lineage replay request.
- Delete+rebuild scope:
  - per `source_snapshot_id`, or
  - per entity family (for targeted repair).
- Replay is idempotent because `MERGE` keys are canonical IDs and relationship identities.

### Consistency Guardrails
- Projection job must fail closed if source extract contains referential breaks.
- Daily reconciliation checks:
  - node count parity by entity label vs canonical tables,
  - edge count parity by relationship type,
  - sample key consistency checks (`trial_id`, `nct_id`, `source_snapshot_id`).

## Core Traversal Queries Validated Against Product Use Cases
Query catalog: `docs/analytics/neo4j_projection_query_catalog.cypher`

### Use Case 1: Competitive landscape by mechanism
- Need: trials connected to specific biomarker + intervention pattern.
- Validation: query returns `Trial`, linked `Biomarker`, and `Intervention` nodes with source IDs.

### Use Case 2: Sponsor portfolio exploration across disease areas
- Need: sponsor-to-trial-to-condition multi-hop traversal with aggregation.
- Validation: query groups trials by sponsor and condition, returns top portfolios.

### Use Case 3: Endpoint strategy discovery
- Need: identify trials measuring endpoint families across conditions.
- Validation: query traverses `Trial -> Endpoint` and `Trial -> Condition` and returns explainable paths.

### Use Case 4: Evidence graph drill-down
- Need: from trial to publications and supporting context.
- Validation: query returns `Trial -> Publication` paths with provenance properties.

## Operational Note
- This projection is intentionally non-authoritative and can be rebuilt from canonical Postgres + lineage snapshots.
- Consumer services must treat Neo4j as a query accelerator, not as a transactional source of truth.
