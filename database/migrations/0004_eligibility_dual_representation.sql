-- 0004_eligibility_dual_representation.sql
-- Eligibility dual representation: raw text + normalized structure + optional logical tree.

begin;

create table if not exists eligibility_clause (
    eligibility_clause_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    document_chunk_id bigint references document_chunk(document_chunk_id) on delete set null,
    nct_id text not null,
    criterion_type text not null check (criterion_type in ('inclusion', 'exclusion')),
    raw_text text not null,
    normalized_clause jsonb not null default '{}'::jsonb,
    logical_ast jsonb,
    source_document_path text,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text not null,
    char_start integer not null check (char_start >= 0),
    char_end integer not null check (char_end >= char_start),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists eligibility_tree (
    eligibility_tree_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    root_clause_id bigint references eligibility_clause(eligibility_clause_id) on delete set null,
    tree_json jsonb not null,
    tree_version text,
    source_snapshot_id text not null,
    source_content_sha256 text,
    created_at timestamptz not null default now()
);

create table if not exists criterion_concept_link (
    criterion_concept_link_id bigserial primary key,
    eligibility_clause_id bigint not null references eligibility_clause(eligibility_clause_id) on delete cascade,
    concept_type text not null,
    concept_id text,
    concept_label text not null,
    normalized_value text,
    char_start integer not null check (char_start >= 0),
    char_end integer not null check (char_end >= char_start),
    confidence numeric,
    source_snapshot_id text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    check (concept_type in ('disease', 'biomarker', 'lab', 'treatment')),
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create index if not exists idx_eligibility_clause_trial
    on eligibility_clause (trial_id, criterion_type);

create index if not exists idx_eligibility_clause_nct_id
    on eligibility_clause (nct_id);

create index if not exists idx_eligibility_clause_snapshot
    on eligibility_clause (source_snapshot_id);

create index if not exists idx_eligibility_clause_normalized_json
    on eligibility_clause using gin (normalized_clause);

create index if not exists idx_eligibility_clause_logical_ast
    on eligibility_clause using gin (logical_ast);

create index if not exists idx_eligibility_clause_offsets
    on eligibility_clause (source_document_path, char_start, char_end);

create index if not exists idx_criterion_concept_link_clause
    on criterion_concept_link (eligibility_clause_id);

create index if not exists idx_criterion_concept_link_type_value
    on criterion_concept_link (concept_type, normalized_value);

commit;
