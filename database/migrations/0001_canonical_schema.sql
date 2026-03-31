-- 0001_canonical_schema.sql
-- Initial canonical relational schema for trial intelligence.

begin;

create extension if not exists vector;

create table if not exists sponsor (
    sponsor_id bigserial primary key,
    sponsor_name text not null,
    sponsor_type text,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists trial (
    trial_id bigserial primary key,
    nct_id text not null unique,
    sponsor_id bigint references sponsor(sponsor_id),
    official_title text,
    brief_title text,
    overall_status text,
    study_type text,
    phase text,
    enrollment integer,
    first_posted date,
    last_update_posted date,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    validity_range tstzrange not null default tstzrange(now(), null, '[)'),
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists trial_version (
    trial_version_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    version_number integer not null,
    is_current boolean not null default true,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    changed_fields jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (trial_id, version_number)
);

create table if not exists condition (
    condition_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    condition_name text not null,
    mesh_id text,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists intervention (
    intervention_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    intervention_type text,
    intervention_name text not null,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists arm (
    arm_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    arm_label text not null,
    arm_type text,
    description text,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists biomarker (
    biomarker_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    biomarker_name text not null,
    biomarker_type text,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists endpoint (
    endpoint_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    endpoint_type text not null,
    endpoint_name text not null,
    endpoint_timeframe text,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists outcome_measure (
    outcome_measure_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    endpoint_id bigint references endpoint(endpoint_id) on delete set null,
    measure_name text not null,
    measure_value numeric,
    measure_unit text,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists adverse_event (
    adverse_event_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    event_name text not null,
    event_severity text,
    event_frequency numeric,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists site (
    site_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    facility_name text,
    city text,
    state text,
    country text,
    postal_code text,
    latitude double precision,
    longitude double precision,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists publication (
    publication_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    pmid text,
    doi text,
    title text,
    published_at date,
    journal text,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_trial_nct_id on trial (nct_id);
create index if not exists idx_trial_sponsor on trial (sponsor_id);
create index if not exists idx_trial_snapshot on trial (source_snapshot_id);
create index if not exists idx_trial_validity_range on trial using gist (validity_range);
create index if not exists idx_trial_attributes on trial using gin (attributes);

create index if not exists idx_condition_trial on condition (trial_id);
create index if not exists idx_intervention_trial on intervention (trial_id);
create index if not exists idx_arm_trial on arm (trial_id);
create index if not exists idx_biomarker_trial on biomarker (trial_id);
create index if not exists idx_endpoint_trial on endpoint (trial_id);
create index if not exists idx_outcome_trial on outcome_measure (trial_id);
create index if not exists idx_adverse_event_trial on adverse_event (trial_id);
create index if not exists idx_site_trial on site (trial_id);
create index if not exists idx_publication_trial on publication (trial_id);

commit;
