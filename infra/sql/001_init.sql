create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

create table if not exists org(
  id uuid primary key default gen_random_uuid(),
  name text not null
);

create table if not exists "user"(
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  name text
);

create table if not exists org_user(
  org_id uuid references org(id) on delete cascade,
  user_id uuid references "user"(id) on delete cascade,
  role text check (role in ('owner','admin','member','viewer')) not null,
  primary key (org_id, user_id)
);

create table if not exists project(
  id uuid primary key default gen_random_uuid(),
  org_id uuid references org(id) on delete cascade,
  name text not null,
  competition text,
  metric text not null,   -- 'auc'|'f1'|'rmse'|'mae'
  created_by uuid references "user"(id),
  created_at timestamptz default now()
);

create table if not exists dataset(
  id uuid primary key default gen_random_uuid(),
  project_id uuid references project(id) on delete cascade,
  version text not null,
  uri text not null,               -- s3/r2/minio prefix
  schema_json jsonb not null,
  created_by uuid references "user"(id),
  created_at timestamptz default now()
);

create table if not exists pipeline(
  id uuid primary key default gen_random_uuid(),
  project_id uuid references project(id) on delete cascade,
  type text not null,              -- 'tabular'|'image'|'nlp'|'timeseries'
  spec_json jsonb not null,
  created_by uuid references "user"(id),
  created_at timestamptz default now()
);

create table if not exists run(
  id uuid primary key default gen_random_uuid(),
  project_id uuid references project(id) on delete cascade,
  pipeline_id uuid references pipeline(id),
  params_json jsonb not null,      -- RunConfig
  status text not null default 'pending', -- pending|running|finished|failed
  score double precision,
  cv_json jsonb,
  seed int not null,
  runner text,                     -- 'kaggle'|'hf_spaces'
  started_at timestamptz,
  finished_at timestamptz,
  created_by uuid references "user"(id),
  created_at timestamptz default now()
);

create table if not exists artifact(
  id uuid primary key default gen_random_uuid(),
  run_id uuid references run(id) on delete cascade,
  type text not null,              -- 'oof'|'submission'|'model'|'metrics'|'plot'|'log'
  uri text not null,
  meta_json jsonb,
  created_at timestamptz default now()
);

create table if not exists comment(
  id uuid primary key default gen_random_uuid(),
  target_type text not null,       -- 'project'|'run'|'dataset'
  target_id uuid not null,
  author_id uuid references "user"(id),
  body text not null,
  created_at timestamptz default now()
);

create table if not exists audit_log(
  id bigserial primary key,
  actor_id uuid references "user"(id),
  action text not null,            -- 'create_run'|'view_artifact'...
  target text,
  payload jsonb,
  ts timestamptz default now()
);
