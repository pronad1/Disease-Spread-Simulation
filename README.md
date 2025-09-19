# Supabase Keepalive (Next.js + Vercel Cron)

Keeps your Supabase **database** active by upserting a single row twice a week.

## 1) Create the table & policies in Supabase

Run this once in **Supabase → SQL Editor**:

```sql
create table if not exists public.keepalive (
  id int primary key,
  last_ping timestamptz not null default now()
);

insert into public.keepalive (id) values (1)
on conflict (id) do nothing;

alter table public.keepalive enable row level security;

create policy "ka_select_anon"
on public.keepalive
for select
to anon
using (id = 1);

create policy "ka_insert_anon"
on public.keepalive
for insert
to anon
with check (id = 1);

create policy "ka_update_anon"
on public.keepalive
for update
to anon
using (id = 1)
with check (id = 1);

grant select, insert, update on public.keepalive to anon, authenticated;
