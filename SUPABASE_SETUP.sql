-- IARS PDF Archive - one-time Supabase setup
-- Run this in Supabase Dashboard > SQL Editor.

create extension if not exists pgcrypto;

insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
values (
    'audit-pdf-archive',
    'audit-pdf-archive',
    false,
    52428800,
    array['application/pdf']
)
on conflict (id) do update set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create table if not exists public.pdf_archive (
    id uuid primary key default gen_random_uuid(),
    audit_reference text not null default '',
    auditee_name text not null default '',
    original_filename text not null,
    storage_bucket text not null default 'audit-pdf-archive',
    storage_path text not null unique,
    document_type text not null check (document_type in ('Original', 'Tagged')),
    uploaded_at timestamptz not null default now(),
    uploaded_by text not null default '',
    file_size bigint not null check (file_size >= 0),
    sha256 text not null unique,
    created_at timestamptz not null default now()
);

create index if not exists pdf_archive_reference_idx
    on public.pdf_archive (audit_reference);

create index if not exists pdf_archive_auditee_idx
    on public.pdf_archive (auditee_name);

create index if not exists pdf_archive_uploaded_at_idx
    on public.pdf_archive (uploaded_at desc);

alter table public.pdf_archive enable row level security;

-- No public RLS policies are intentionally created.
-- IARS accesses this private archive from the Streamlit server using the
-- Supabase service-role key stored only in Streamlit Secrets.
