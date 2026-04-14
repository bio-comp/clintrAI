// Neo4j projection query catalog for issue #5.
// Graph is a non-authoritative projection from canonical Postgres.

// Use Case 1: Competitive landscape by mechanism
// Example: PD-1 trials in GI cancers with biomarker-linked evidence.
MATCH (t:Trial)-[:HAS_INTERVENTION]->(i:Intervention)
MATCH (t)-[:STUDIES]->(c:Condition)
OPTIONAL MATCH (t)-[:HAS_BIOMARKER]->(b:Biomarker)
WHERE toLower(i.intervention_name) CONTAINS "pd-1"
  AND toLower(c.condition_name) CONTAINS "gastro"
RETURN t.trial_id, t.nct_id, i.intervention_name, c.condition_name,
       collect(distinct b.biomarker_name) AS biomarkers
ORDER BY t.nct_id
LIMIT 100;

// Use Case 2: Sponsor portfolio exploration across disease areas
MATCH (s:Sponsor)-[:SPONSORS]->(t:Trial)-[:STUDIES]->(c:Condition)
RETURN s.sponsor_name, c.condition_name, count(distinct t) AS trial_count
ORDER BY trial_count DESC
LIMIT 50;

// Use Case 3: Endpoint strategy discovery by condition
MATCH (t:Trial)-[:MEASURES]->(e:Endpoint)
MATCH (t)-[:STUDIES]->(c:Condition)
RETURN c.condition_name, e.endpoint_type, e.endpoint_name, count(distinct t) AS trials
ORDER BY trials DESC
LIMIT 100;

// Use Case 4: Evidence graph drill-down
MATCH (t:Trial {nct_id: $nct_id})-[:HAS_PUBLICATION]->(p:Publication)
RETURN t.nct_id, p.publication_id, p.title, p.journal, p.published_at,
       p.source_snapshot_id
ORDER BY p.published_at DESC
LIMIT 25;

