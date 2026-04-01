-- 0002_document_chunk_pipeline.sql
-- Document chunk layer with lexical + vector retrieval primitives.

begin;

create extension if not exists vector;

create table if not exists document_chunk (
    document_chunk_id bigserial primary key,
    trial_id bigint not null references trial(trial_id) on delete cascade,
    nct_id text not null,
    source_snapshot_id text not null,
    source_system text not null,
    source_record_id text,
    source_content_sha256 text not null,
    source_document_path text,
    source_document_type text,
    section_path text not null,
    chunk_index integer not null,
    chunk_text text not null,
    char_start integer not null check (char_start >= 0),
    char_end integer not null check (char_end >= char_start),
    metadata jsonb not null default '{}'::jsonb,
    search_text_tsv tsvector generated always as (
        to_tsvector('english', coalesce(chunk_text, ''))
    ) stored,
    embedding vector(384),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (source_snapshot_id, source_content_sha256, chunk_index)
);

create index if not exists idx_document_chunk_trial_id
    on document_chunk (trial_id);

create index if not exists idx_document_chunk_nct_id
    on document_chunk (nct_id);

create index if not exists idx_document_chunk_snapshot
    on document_chunk (source_snapshot_id);

create index if not exists idx_document_chunk_source_hash
    on document_chunk (source_content_sha256);

create index if not exists idx_document_chunk_source_record
    on document_chunk (source_system, source_record_id);

create index if not exists idx_document_chunk_fts
    on document_chunk using gin (search_text_tsv);

create index if not exists idx_document_chunk_embedding_hnsw
    on document_chunk using hnsw (embedding vector_cosine_ops);

commit;
