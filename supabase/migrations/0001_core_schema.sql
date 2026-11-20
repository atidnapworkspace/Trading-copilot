-- Trading Copilot — core schema (Phase 1.1)
-- Single-user app. RLS is ENABLED on every table with NO policies: the anon key can read nothing.
-- Access only via service role (pipeline, Edge Functions after PIN check).

create type market_t     as enum ('US', 'AR', 'CRYPTO');
create type asset_type_t as enum ('stock', 'etf', 'cedear', 'bond', 'on', 'crypto');
create type quality_t    as enum ('OK', 'STALE', 'SUSPECT', 'MISSING', 'NOT_MEANINGFUL');
create type freshness_t  as enum ('realtime', 'delayed_15m', 'delayed_20m', 'eod');

-- ---------- Instruments ----------
create table instruments (
  id            bigint generated always as identity primary key,
  symbol        text not null,
  market        market_t not null,
  asset_type    asset_type_t not null,
  name          text,
  exchange      text,
  currency      text,                 -- native trading currency (USD, ARS, ...)
  isin          text,
  cik           text,                 -- SEC CIK (US only), zero-padded 10 digits
  underlying_id bigint references instruments(id),  -- cedear -> US underlying
  cedear_ratio  numeric,
  is_watchlist  boolean not null default false,
  active        boolean not null default true,
  updated_at    timestamptz not null default now(),
  unique (market, symbol, currency)
);
create index on instruments (market, asset_type) where active;

create table instrument_aliases (      -- provider-specific symbols
  instrument_id bigint not null references instruments(id) on delete cascade,
  provider      text not null,         -- yahoo | data912 | okx | coingecko | polygon | finnhub
  provider_symbol text not null,
  primary key (instrument_id, provider)
);

-- Sector / custom groups (N:M so a ticker can live in several groups)
create table groups (
  id     bigint generated always as identity primary key,
  name   text not null unique,
  market market_t,
  kind   text not null default 'custom'   -- custom | sector_auto
);
create table group_members (
  group_id      bigint not null references groups(id) on delete cascade,
  instrument_id bigint not null references instruments(id) on delete cascade,
  sort_order    int,
  primary key (group_id, instrument_id)
);

create table user_labels (
  instrument_id bigint primary key references instruments(id) on delete cascade,
  label         text,                  -- Mirar | En zona de compra | Descartar | free text
  note          text,
  updated_at    timestamptz not null default now()
);

-- ---------- Market data ----------
create table prices_daily (
  instrument_id bigint not null references instruments(id) on delete cascade,
  d             date not null,
  open numeric, high numeric, low numeric,
  close_raw     numeric,
  close_adj     numeric,               -- adjusted for splits+dividends
  volume        numeric,
  source        text not null,
  quality       quality_t not null default 'OK',
  primary key (instrument_id, d)
);

create table quotes_latest (
  instrument_id bigint primary key references instruments(id) on delete cascade,
  price         numeric,
  day_volume    numeric,
  ts_market     timestamptz,           -- timestamp of the quote itself
  ts_ingested   timestamptz not null default now(),
  freshness     freshness_t not null,
  source        text not null,
  quality       quality_t not null default 'OK'
);

create table fx_rates (
  ts     timestamptz not null,
  kind   text not null,                -- oficial | mep | ccl | blue
  value  numeric not null,
  source text not null,
  primary key (ts, kind)
);

-- ---------- Computed metrics (written ONLY by pipeline code) ----------
create table metrics_snapshot (
  instrument_id bigint primary key references instruments(id) on delete cascade,
  as_of         date not null,
  last_close    numeric,
  low_52w       numeric,
  high_52w      numeric,
  pct_to_high   numeric,               -- (last/high_52w - 1)*100
  vol_avg_30d   numeric,
  vol_last      numeric,
  vol_rel       numeric,               -- vol_last/vol_avg_30d
  rsi_14        numeric,
  sma_50        numeric,
  sma_200       numeric,
  flags         jsonb not null default '{}'::jsonb,   -- per-metric quality, e.g. {"pct_to_high":"OK"}
  computed_at   timestamptz not null default now()
);

create table fundamentals (
  instrument_id bigint primary key references instruments(id) on delete cascade,
  as_of         date not null,
  period_end    date,                  -- last fiscal period used
  eps_ttm       numeric,
  pe            numeric,
  fwd_pe        numeric,               -- watchlist only, external source
  pb            numeric,
  roe           numeric,
  sources       jsonb not null default '{}'::jsonb,   -- per-field source
  flags         jsonb not null default '{}'::jsonb,   -- per-field OK|NOT_MEANINGFUL|MISSING|SUSPECT
  computed_at   timestamptz not null default now()
);

create table crypto_metrics (
  instrument_id bigint primary key references instruments(id) on delete cascade,
  ts            timestamptz not null,
  mcap          numeric,
  rank          int,
  ath           numeric,
  pct_from_ath  numeric,
  high_52w      numeric,
  pct_to_high   numeric,
  vol_24h       numeric,
  vol_7d_avg    numeric,
  open_interest_usd numeric,           -- single exchange (OKX) unless stated in oi_source
  oi_source     text,
  funding_rate  numeric,
  flags         jsonb not null default '{}'::jsonb
);
create table crypto_global (
  ts timestamptz primary key,
  btc_dominance numeric,
  total_mcap numeric
);

-- ---------- Bonds / ONs ----------
create table bonds (
  instrument_id bigint primary key references instruments(id) on delete cascade,
  issuer        text,
  bond_kind     text,                  -- soberano | lecap | cer | ON | provincial ...
  currency      text,
  maturity      date,
  coupon_pct    numeric,
  rating_national text,                -- e.g. AA(arg); curated
  rating_agency text,
  rating_date   date,
  rating_source_url text,
  cashflows     jsonb,                 -- curated schedule [{date, amount}] for YTM/duration
  notes         text
);
create table bond_metrics (
  instrument_id bigint primary key references instruments(id) on delete cascade,
  as_of         timestamptz not null,
  price         numeric,
  ytm_pct       numeric,
  parity_pct    numeric,
  duration_mod  numeric,
  flags         jsonb not null default '{}'::jsonb
);

-- ---------- Seasonality (cached, computed by code) ----------
create table seasonality_monthly (
  instrument_id bigint not null references instruments(id) on delete cascade,
  basis         text not null,         -- native | ars | usd_ccl
  y             int not null,
  m             int not null check (m between 1 and 12),
  ret_pct       numeric,
  n_days        int,
  quality       quality_t not null default 'OK',
  primary key (instrument_id, basis, y, m)
);
create table seasonality_summary (
  instrument_id bigint not null references instruments(id) on delete cascade,
  basis         text not null,
  window_years  int not null,          -- 10 | 5 | all
  m             int not null check (m between 1 and 12),
  avg_pct       numeric, median_pct numeric, win_rate numeric, n int,
  computed_at   timestamptz not null default now(),
  primary key (instrument_id, basis, window_years, m)
);

-- ---------- Agent / TradingView ----------
create table news_items (
  id            bigint generated always as identity primary key,
  instrument_id bigint references instruments(id) on delete cascade,
  url           text not null,
  title         text,
  published_at  timestamptz,
  source_domain text,
  source_tier   int check (source_tier between 1 and 3),
  fetched_at    timestamptz not null default now(),
  url_hash      text not null unique
);

create table briefing_requests (
  id            bigint generated always as identity primary key,
  instrument_id bigint not null references instruments(id) on delete cascade,
  requested_at  timestamptz not null default now(),
  status        text not null default 'pending'
                check (status in ('pending','running','done','failed','rejected')),
  input_json    jsonb,                 -- computed metrics snapshot given to the agent
  input_hash    text,
  output_json   jsonb,                 -- {sections..., citations:[{url,date,tier}]}
  validation    jsonb,                 -- result of citation/number validator
  model         text,
  finished_at   timestamptz
);
create index on briefing_requests (status, requested_at);

create table alerts_inbox (
  id            bigint generated always as identity primary key,
  received_at   timestamptz not null default now(),
  idempotency_key text unique,
  signature_ok  boolean not null,
  raw_payload   jsonb not null,
  ticker        text,
  instrument_id bigint references instruments(id),
  timeframe     text,
  condition     text,
  price         numeric,
  enrichment    jsonb,                 -- code-computed context at receive time
  status        text not null default 'new' check (status in ('new','queued','evaluated','dismissed'))
);

create table setups (
  id            bigint generated always as identity primary key,
  instrument_id bigint not null references instruments(id) on delete cascade,
  side          text not null check (side in ('long','short')),
  entry numeric not null, stop numeric not null,
  targets       numeric[] not null,
  rr            numeric,               -- computed by code, never by LLM
  pine_script   text,
  tv_link       text,
  created_by    text not null check (created_by in ('agent','user')),
  status        text not null default 'draft',
  created_at    timestamptz not null default now()
);

-- ---------- Config & observability ----------
create table app_settings (
  key   text primary key,
  value jsonb not null
);
insert into app_settings(key, value) values
  ('screener_filters', '{"min_price": 2, "min_dollar_volume": 1000000, "etfs_separate": true}');

create table provider_runs (
  id          bigint generated always as identity primary key,
  job         text not null,
  provider    text,
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  n_ok int default 0, n_suspect int default 0, n_missing int default 0,
  quota_used  int,                     -- calls consumed (rate-limit accounting)
  error       text
);
create table data_quality_log (
  id            bigint generated always as identity primary key,
  run_id        bigint references provider_runs(id) on delete cascade,
  ts            timestamptz not null default now(),
  instrument_id bigint references instruments(id) on delete cascade,
  rule          text not null,
  severity      text not null check (severity in ('info','warn','error')),
  detail        text
);

-- ---------- Lock everything down ----------
do $$
declare t text;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('alter table public.%I enable row level security', t);
  end loop;
end $$;
