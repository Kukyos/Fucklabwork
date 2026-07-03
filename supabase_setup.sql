-- AutoLAB billing schema. Paste the whole file into
-- Supabase dashboard -> SQL Editor -> New query -> Run. Safe to re-run.

create table if not exists public.wallets (
  user_id uuid primary key references auth.users(id) on delete cascade,
  balance int not null default 0 check (balance >= 0)
);

create table if not exists public.ledger (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  delta int not null,
  reason text not null,
  ref text unique,          -- razorpay payment id; makes crediting idempotent
  created_at timestamptz not null default now()
);

alter table public.wallets enable row level security;
alter table public.ledger enable row level security;

drop policy if exists "read own wallet" on public.wallets;
create policy "read own wallet" on public.wallets
  for select using (auth.uid() = user_id);

drop policy if exists "read own ledger" on public.ledger;
create policy "read own ledger" on public.ledger
  for select using (auth.uid() = user_id);

-- Atomic spend: decrements only when the balance covers the cost.
-- Returns the new balance, or -1 when there isn't enough.
create or replace function public.spend_credits(uid uuid, cost int, why text)
returns int language plpgsql security definer set search_path = public as $$
declare new_balance int;
begin
  insert into wallets (user_id) values (uid) on conflict do nothing;
  update wallets set balance = balance - cost
    where user_id = uid and balance >= cost
    returning balance into new_balance;
  if new_balance is null then
    return -1;
  end if;
  insert into ledger (user_id, delta, reason) values (uid, -cost, why);
  return new_balance;
end $$;

-- Add credits. When pay_ref is set (a Razorpay payment id) the call is
-- idempotent: a second webhook/verify for the same payment adds nothing.
create or replace function public.add_credits(uid uuid, amount int, why text,
                                              pay_ref text default null)
returns int language plpgsql security definer set search_path = public as $$
declare new_balance int;
begin
  if pay_ref is not null and exists (select 1 from ledger where ref = pay_ref) then
    select balance into new_balance from wallets where user_id = uid;
    return coalesce(new_balance, 0);
  end if;
  insert into wallets (user_id, balance) values (uid, amount)
    on conflict (user_id) do update set balance = wallets.balance + excluded.balance
    returning balance into new_balance;
  insert into ledger (user_id, delta, reason, ref) values (uid, amount, why, pay_ref);
  return new_balance;
end $$;

-- Only the server (service_role key) may move money.
revoke execute on function public.spend_credits(uuid, int, text) from public, anon, authenticated;
revoke execute on function public.add_credits(uuid, int, text, text) from public, anon, authenticated;
