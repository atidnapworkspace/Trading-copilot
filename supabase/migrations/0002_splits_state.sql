-- Trading Copilot — Phase 1.2: splits, ingestion state, db size probe.
-- Run ONCE in the Supabase SQL editor (choose "Run and enable RLS" if asked).

-- Raw prices are stored unadjusted; splits are applied by code at metric time.
create table splits (
  instrument_id bigint not null references instruments(id) on delete cascade,
  ex_date       date not null,
  split_from    numeric not null,
  split_to      numeric not null,        -- 2-for-1: from=1, to=2 (price before ex_date / (to/from))
  source        text not null default 'polygon',
  primary key (instrument_id, ex_date)
);

-- Small key/value state for resumable jobs (e.g. which EOD dates are already loaded).
create table ingest_state (
  key        text primary key,
  value      jsonb not null,
  updated_at timestamptz not null default now()
);

insert into app_settings(key, value)
values ('storage_filters', '{"min_close": 1, "min_dollar_volume": 250000}')
on conflict (key) do nothing;

-- Free tier is 500 MB: lets the pipeline report database size on every run.
create or replace function db_size_mb() returns numeric
language sql security definer set search_path = public as $$
  select round(pg_database_size(current_database()) / 1024.0 / 1024.0, 1)
$$;
revoke all on function db_size_mb() from public, anon, authenticated;
grant execute on function db_size_mb() to service_role;

alter table splits       enable row level security;
alter table ingest_state enable row level security;
