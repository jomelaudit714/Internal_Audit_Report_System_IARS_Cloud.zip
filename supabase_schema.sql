-- Supabase SQL Schema for Internal Audit Report System

create extension if not exists "uuid-ossp";

create table if not exists audit_reports (
    id uuid primary key default uuid_generate_v4(),
    created_at timestamp with time zone default now(),
    encoded_date date,
    audit_reference text,
    date_reported text,
    auditee_name text,
    scope_date text,
    year text,
    pdf_bucket text,
    pdf_path text
);

create table if not exists audit_findings (
    id uuid primary key default uuid_generate_v4(),
    created_at timestamp with time zone default now(),
    report_id uuid references audit_reports(id) on delete cascade,
    row_no text,
    encoded_date text,
    type text,
    date_reported text,
    audit_reference text,
    id_no text,
    name text,
    task_id text,
    scope_date text,
    year text,
    findings text,
    issue_detail_issue text,
    explanation text,
    recommendation1 text,
    recommendation2 text,
    audited_by1 text,
    audited_by2 text,
    reaction text,
    frequency text,
    correction text,
    sanction text,
    case_status text,
    score numeric,
    improve_score numeric,
    net_score numeric,
    audit_unit text,
    user_name text
);

create table if not exists employee_masterlist (
    id uuid primary key default uuid_generate_v4(),
    employee_id text unique,
    full_name text,
    company text,
    department text,
    position text,
    status text default 'Active',
    created_at timestamp with time zone default now()
);

-- Create a private storage bucket named audit-pdfs in Supabase Storage.
-- In Supabase Dashboard: Storage > New bucket > audit-pdfs > Private.