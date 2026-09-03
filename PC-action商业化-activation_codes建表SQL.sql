-- PC-action 商业化：激活码表（卡密激活模式）
-- 在 Supabase 控制台的 SQL Editor 执行此脚本。
-- 客户端使用 anon key 直连 Supabase，因此关闭 RLS（与现有 users / licenses 表处理方式一致）。
-- 对应代码：entitlement.py 的 generate_activation_codes() / activate_code()

create table if not exists public.activation_codes (
  id bigint generated always as identity primary key,
  code text not null unique,
  plan text not null default 'plan_1',
  months integer not null default 1,
  used integer not null default 0,
  used_by text,
  note text default '',
  created_at timestamptz default now(),
  used_at timestamptz
);

alter table public.activation_codes disable row level security;
