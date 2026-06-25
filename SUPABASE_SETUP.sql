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


-- Additional auditors added from IARS. Existing auditors remain in Master_Data.xlsx.
create table if not exists public.auditors_master (
    id uuid primary key default gen_random_uuid(),
    auditor_name text not null,
    designation text not null default '',
    user_display text not null default '',
    email text not null default '',
    status text not null default 'Active' check (status in ('Active', 'Inactive')),
    created_at timestamptz not null default now(),
    created_by text not null default ''
);

create unique index if not exists auditors_master_name_ci_uidx
    on public.auditors_master (lower(auditor_name));

create index if not exists auditors_master_status_idx
    on public.auditors_master (status);

alter table public.auditors_master enable row level security;

grant usage on schema public to service_role;
grant select, insert, update, delete on table public.pdf_archive to service_role;
grant select, insert, update, delete on table public.auditors_master to service_role;
