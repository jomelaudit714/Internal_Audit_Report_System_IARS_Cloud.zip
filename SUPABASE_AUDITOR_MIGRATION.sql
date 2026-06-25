-- IARS v3.1 - one-time migration for the Add New Auditor feature
-- Run in Supabase Dashboard > SQL Editor after the original archive setup.

create extension if not exists pgcrypto;

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
grant select, insert, update, delete on table public.auditors_master to service_role;
