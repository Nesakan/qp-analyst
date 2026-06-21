-- QP Analyst — Supabase schema
-- Run this in the Supabase SQL editor (Project -> SQL Editor -> New query)

create table papers (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  subject_name text not null,
  exam_type text not null check (exam_type in ('CIA-1', 'CIA-2', 'CIA-3', 'End Semester', 'Model Exam')),
  department text,
  year integer,
  raw_text text not null,
  uploaded_at timestamptz not null default now()
);

create table questions (
  id uuid primary key default gen_random_uuid(),
  paper_id uuid not null references papers(id) on delete cascade,
  question_number text not null,
  question_text text not null,
  unit integer not null check (unit between 1 and 5),
  topic text not null,
  marks integer not null,
  question_type text not null check (
    question_type in ('Theory', 'Numerical', 'Diagram', 'Derivation', 'Programming')
  ),
  has_diagram boolean not null default false,
  diagram_url text
);

-- Speeds up the most common query: "all questions for paper X"
create index idx_questions_paper_id on questions(paper_id);

-- Speeds up future cross-paper analytics (Phase 2): "all Unit 3 questions across all papers"
create index idx_questions_unit on questions(unit);

-- ── Diagram storage ──
-- Run this separately: Supabase Dashboard -> Storage -> New bucket
--   Name: diagrams
--   Public bucket: ON  (so cropped images can be displayed directly via URL)
-- No SQL needed for bucket creation itself, but this policy allows the
-- backend's anon/publishable key to upload into it:
insert into storage.buckets (id, name, public)
values ('diagrams', 'diagrams', true)
on conflict (id) do nothing;

create policy "Allow public uploads to diagrams bucket"
on storage.objects for insert
to public
with check (bucket_id = 'diagrams');

create policy "Allow public read of diagrams bucket"
on storage.objects for select
to public
using (bucket_id = 'diagrams');
