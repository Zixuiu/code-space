-- ============================================================
-- T1 补丁2：重建 licenses 表（旧表 FK 引用了错误的 users 表，且为空表，零数据损失）
-- 用法：Supabase 控制台 → SQL Editor → 粘贴全文 → Run
-- ============================================================

-- ① 存档根因：看旧 FK 到底引用哪张表（应在结果里看到带 schema 的全名）
select conname, confrelid::regclass as 引用的表
from pg_constraint where conname = 'licenses_user_id_fkey';

-- ② 删掉引用错乱的旧表（空表，安全）
drop table if exists public.licenses cascade;

-- ③ 重建：FK 明确指向 public.users，用户删除时级联清 license
create table public.licenses (
  id          bigint generated always as identity primary key,
  user_id     bigint references public.users(id) on delete cascade,
  license_key text,
  product_name text,
  expiry_date text,
  created_at  text
);

create index if not exists idx_licenses_user_id on public.licenses(user_id);

-- ④ RLS + anon 放行策略（与其它 5 表一致）
alter table public.licenses enable row level security;
drop policy if exists "anon_full_access" on public.licenses;
create policy "anon_full_access" on public.licenses
  for all to anon, authenticated using (true) with check (true);

-- ⑤ 验证：新 FK 应显示引用 public.users
select conname, confrelid::regclass as 引用的表
from pg_constraint where conname like 'licenses%';
