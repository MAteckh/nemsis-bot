-- NEMSIS v2 — Supabase Schema
-- Run this in Supabase → SQL Editor → New Query → Run

-- Signals table
create table if not exists signals (
  id          bigserial primary key,
  created_at  timestamptz default now(),
  direction   text,
  entry       numeric,
  sl          numeric,
  tp          numeric,
  rr          numeric,
  score       int,
  rsi         numeric,
  adx         numeric,
  atr         numeric,
  regime      text,
  session     text,
  smc_bonus   int,
  mtf_detail  jsonb,
  score_reasons jsonb,
  executed    boolean default false
);

-- Trades table
create table if not exists trades (
  id          bigserial primary key,
  created_at  timestamptz default now(),
  ticket      text,
  direction   text,
  entry       numeric,
  sl          numeric,
  tp          numeric,
  lot_size    numeric,
  open_time   timestamptz,
  close_time  timestamptz,
  close_price numeric,
  pnl         numeric,
  result      text,
  rr          numeric,
  score       int,
  regime      text,
  session     text
);

-- Bot state table (single row, updated every scan)
create table if not exists bot_state (
  id          int primary key default 1,
  updated_at  timestamptz default now(),
  price       numeric,
  spread      numeric,
  last_scan   text,
  regime      text,
  session     text,
  scanning    boolean default false,
  risk        jsonb,
  stats       jsonb,
  log         jsonb
);

-- Insert initial bot_state row
insert into bot_state (id) values (1) on conflict (id) do nothing;

-- Enable realtime for live updates
alter publication supabase_realtime add table signals;
alter publication supabase_realtime add table bot_state;

-- Allow public read (dashboard needs this)
alter table signals   enable row level security;
alter table trades    enable row level security;
alter table bot_state enable row level security;

create policy "Public read signals"   on signals   for select using (true);
create policy "Public read trades"    on trades    for select using (true);
create policy "Public read bot_state" on bot_state for select using (true);

create policy "Service insert signals"   on signals   for insert with check (true);
create policy "Service insert trades"    on trades    for insert with check (true);
create policy "Service update bot_state" on bot_state for update using (true);
create policy "Service insert bot_state" on bot_state for insert with check (true);
