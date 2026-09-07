-- ============================================================
-- T1 补丁：对齐已有旧表结构（幂等，可重复执行，不动已有数据）
-- 用法：Supabase 控制台 → SQL Editor → 粘贴全文 → Run
-- ============================================================

-- 1) users 表补缺列（现有: id/username/email/password_hash/is_active/is_admin/replay_count/created_at）
alter table public.users add column if not exists is_vip       int default 0;
alter table public.users add column if not exists vip_end_date text;
alter table public.users add column if not exists can_replay   int default 1;

-- 2) licenses 表补缺列（现有 user_id 带 FK；补齐 VIP 时长字段）
alter table public.licenses add column if not exists license_key  text;
alter table public.licenses add column if not exists product_name text;
alter table public.licenses add column if not exists expiry_date  text;
alter table public.licenses add column if not exists created_at   text;
create index if not exists idx_licenses_user_id on public.licenses(user_id);

-- 3) 兜底：确保全部 6 张表 RLS 开启 + anon 放行策略（幂等）
alter table public.users            enable row level security;
alter table public.licenses         enable row level security;
alter table public.activation_codes enable row level security;
alter table public.recharge_records enable row level security;
alter table public.feedback         enable row level security;
alter table public.login_records    enable row level security;

do $$
declare t text;
begin
  foreach t in array array['users','licenses','activation_codes','recharge_records','feedback','login_records']
  loop
    execute format('drop policy if exists "anon_full_access" on public.%I', t);
    execute format('create policy "anon_full_access" on public.%I for all to anon, authenticated using (true) with check (true)', t);
  end loop;
end $$;

-- 验证：users 应含 is_vip/vip_end_date/can_replay
select column_name from information_schema.columns
where table_schema='public' and table_name='users'
order by ordinal_position;
