-- ============================================================
-- PC-Action 商业化 · Supabase 建表脚本（T1）
-- 用法：Supabase 控制台 → SQL Editor → New query → 全文粘贴 → Run
-- 与代码对齐：supabase_db.py / hybrid_db.py / database_helper.py / entitlement.py
-- ============================================================

-- 1) 用户表（hybrid_db.create_user 最小字段 + supabase_db.create_user 完整字段）
create table if not exists public.users (
  id            bigint generated always as identity primary key,
  username      text unique not null,
  email         text,
  password_hash text not null default '',
  is_active     int  default 1,
  is_admin      int  default 0,
  is_vip        int  default 0,
  vip_end_date  text,
  can_replay    int  default 1,
  replay_count  int  default 0,
  created_at    text
);

-- 2) VIP 许可证表（VIP 时长真源：manage_vip_license / check_vip_status 读写）
create table if not exists public.licenses (
  id           bigint generated always as identity primary key,
  user_id      bigint,
  license_key  text,
  product_name text,
  expiry_date  text,
  created_at   text
);
create index if not exists idx_licenses_user_id on public.licenses(user_id);

-- 3) 激活码表（entitlement.generate_activation_codes / activate_code 读写）
create table if not exists public.activation_codes (
  id         bigint generated always as identity primary key,
  code       text unique not null,
  plan       text default 'plan_1',
  months     int  default 1,
  used       int  default 0,
  used_by    text,
  used_at    text,
  note       text,
  created_at text
);
create index if not exists idx_activation_codes_code on public.activation_codes(code);

-- 4) 充值记录表
create table if not exists public.recharge_records (
  id             bigint generated always as identity primary key,
  username       text,
  amount         numeric,
  payment_method text,
  created_at     text
);

-- 5) 反馈表（database_helper.submit_feedback：username/content/contact_info/created_at）
create table if not exists public.feedback (
  id           bigint generated always as identity primary key,
  username     text,
  content      text,
  contact_info text,
  created_at   text
);

-- 6) 登录记录表（supabase_db.create_login_record 预留，字段宽松）
create table if not exists public.login_records (
  id         bigint generated always as identity primary key,
  username   text,
  login_time text,
  ip         text,
  user_agent text,
  created_at text
);

-- ============================================================
-- RLS：P0 务实方案——anon 全放行（客户端用 anon key 直连，无 Supabase Auth）
-- ⚠ 已知风险：anon key 会打进 exe，拿到 key 者可任意读写这些表。
-- P2 改进项：改 service_role + 自建 API / Edge Function，收紧策略。
-- ============================================================
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

-- 验证：应返回 6 行且每行策略存在
select tablename, policyname from pg_policies where schemaname = 'public';
