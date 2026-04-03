-- 0003_data_lineage_reprocessing_controls.sql
-- Lineage, deterministic versioning, replay controls, and promotion quality gates.

begin;

create type data_layer as enum ('bronze', 'silver', 'gold');

create table if not exists pipeline_run (
    pipeline_run_id bigserial primary key,
    run_version_id text not null unique,
    source_snapshot_id text not null,
    input_fingerprint text not null,
    transform_version text not null,
    started_at timestamptz not null default now(),
    completed_at timestamptz,
    status text not null check (status in ('running', 'succeeded', 'failed')),
    metadata jsonb not null default '{}'::jsonb,
    unique (source_snapshot_id, input_fingerprint, transform_version)
);

create table if not exists dataset_version (
    dataset_version_id bigserial primary key,
    layer data_layer not null,
    dataset_key text not null,
    source_snapshot_id text not null,
    input_fingerprint text not null,
    transform_version text not null,
    version_id text generated always as (
        md5(
            layer::text || ':' || dataset_key || ':' || source_snapshot_id || ':' ||
            input_fingerprint || ':' || transform_version
        )
    ) stored,
    pipeline_run_id bigint references pipeline_run(pipeline_run_id) on delete set null,
    created_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb,
    unique (layer, dataset_key, source_snapshot_id, input_fingerprint, transform_version),
    unique (version_id)
);

create table if not exists lineage_edge (
    lineage_edge_id bigserial primary key,
    parent_dataset_version_id bigint not null references dataset_version(dataset_version_id) on delete cascade,
    child_dataset_version_id bigint not null references dataset_version(dataset_version_id) on delete cascade,
    created_at timestamptz not null default now(),
    check (parent_dataset_version_id <> child_dataset_version_id),
    unique (parent_dataset_version_id, child_dataset_version_id)
);

create table if not exists reprocessing_request (
    reprocessing_request_id bigserial primary key,
    request_type text not null,
    idempotency_key text not null unique,
    source_snapshot_id text,
    target_layer data_layer,
    target_dataset_key text,
    requested_by text,
    requested_at timestamptz not null default now(),
    status text not null check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
    metadata jsonb not null default '{}'::jsonb,
    check (request_type in ('backfill', 'replay'))
);

create table if not exists quality_check_result (
    quality_check_result_id bigserial primary key,
    dataset_version_id bigint not null references dataset_version(dataset_version_id) on delete cascade,
    check_suite text not null,
    gate_status text not null check (gate_status in ('passed', 'failed')),
    issues jsonb not null default '[]'::jsonb,
    checked_at timestamptz not null default now(),
    unique (dataset_version_id, check_suite)
);

create table if not exists layer_promotion (
    layer_promotion_id bigserial primary key,
    source_dataset_version_id bigint not null references dataset_version(dataset_version_id) on delete cascade,
    target_layer data_layer not null,
    promoted_by text,
    promoted_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb
);

create or replace function enforce_quality_gate_before_promotion()
returns trigger
language plpgsql
as $$
declare
    has_passed_gate boolean;
begin
    select exists (
        select 1
        from quality_check_result q
        where q.dataset_version_id = new.source_dataset_version_id
          and q.gate_status = 'passed'
    ) into has_passed_gate;

    if not has_passed_gate then
        raise exception 'quality gate failed or missing for dataset_version_id=%', new.source_dataset_version_id;
    end if;

    return new;
end;
$$;

create trigger trg_enforce_quality_gate_before_promotion
before insert on layer_promotion
for each row
execute function enforce_quality_gate_before_promotion();

create index if not exists idx_dataset_version_layer_key
    on dataset_version (layer, dataset_key);

create index if not exists idx_dataset_version_snapshot
    on dataset_version (source_snapshot_id);

create index if not exists idx_lineage_edge_parent
    on lineage_edge (parent_dataset_version_id);

create index if not exists idx_lineage_edge_child
    on lineage_edge (child_dataset_version_id);

create index if not exists idx_reprocessing_request_target
    on reprocessing_request (target_layer, target_dataset_key, status);

create index if not exists idx_quality_check_dataset_version
    on quality_check_result (dataset_version_id, gate_status);

commit;
