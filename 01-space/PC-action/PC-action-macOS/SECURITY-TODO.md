# 商业化安全待办清单

> 由 2026-09-08 的安全审计产生。客户端能修的已修，剩下这些**必须动服务端**，无法靠改客户端解决。
> 本文件只记录待办与操作步骤，不含任何密钥、令牌或可利用细节。

---

## P0-1 · 收回数据库的公网写权限 ⚠️ 最高优先级

**现状**：anon key 硬编码在 `supabase_db.py`（role=anon，有效期到 2076 年），
且 `supabase_setup.sql` 里的 RLS 策略对 anon 是 `for all ... using (true) with check (true)`。
两者叠加 = `users` 表对任何拿到 key 的人完全可读写，而 key 就打在发行包里。

**风险**：一条 REST 请求即可把自己改成永久 VIP；同时可读走全表用户数据、可删库。

**操作步骤**（在 Supabase 后台 + SQL Editor 完成）：

1. **先备份** `users`、`recharge_records` 两张表（Dashboard → Table Editor → 导出 CSV）。
2. 删除现有的 `anon_full_access` 策略（对所有业务表）：
   ```sql
   drop policy if exists "anon_full_access" on public.users;
   drop policy if exists "anon_full_access" on public.recharge_records;
   drop policy if exists "anon_full_access" on public.activation_codes;
   drop policy if exists "anon_full_access" on public.login_records;
   drop policy if exists "anon_full_access" on public.feedback;
   ```
3. 为 `users` 表建**只读自己那行**的策略（需先接入 Supabase Auth，见下条）。
   过渡期若暂时接不了 Auth，至少先改成**只读**：
   ```sql
   create policy "anon_select_only" on public.users for select to anon using (true);
   ```
   ——注意：只给 select 会让注册/登录/写充值记录失效，所以必须同步完成第 4 步再上线。
4. 把所有**写操作**迁到 Edge Function（service_role key 只存在于服务端，不下发客户端）：
   - `register_user` / `login`（写 `users`）
   - `add_recharge_record`（写 `recharge_records`）
   - `activate_code` / `manage_vip_license`（写 `users.is_vip`）
   - `add_login_record`、`submit_feedback`
5. 客户端 `supabase_db.py` 里对应的写方法改为调用 Edge Function，不再直连表。
6. **轮换 key**：在 Supabase 后台 Settings → API 重置 anon key，并更新客户端内置值。

**验收**：用发行包里的 key 直接 PATCH `users` 表应返回 401/403；客户端全流程（注册、登录、充值提交、审核开通）功能正常。

---

## P1 · 把付费判定搬到服务端（根治 P1-3 / P1-4）

**现状**：客户端拿到 `is_vip`、`vip_end_date`、`created_at` 等原始字段自行计算结论。
只要判定在本地，本地能改的东西就注定防得住一时、防不住根本。

**目标架构**：服务端算好 `has_access: true/false` + `vip_end` 直接下发，客户端只做展示、不做判定。

**操作步骤**：

1. 新增 Edge Function `get_entitlement(username)`：
   - 服务端读库、取服务器时间、算 VIP 有效期与试用期
   - 返回 `{ has_access, is_vip, vip_end, trial_end, server_now }`
2. 客户端 `entitlement.get_entitlement` 改为请求该接口，删掉本地的 VIP/试用期计算逻辑。
3. 顺带解决（改造完成后这些不再需要）：
   - `MAX_TRIAL_DAYS` 本地夹取（试用期天数由服务端下发）
   - 离线签名缓存与 `_ENT_SIGN_SECRET`（服务端判定，本地缓存不再承载授权语义）
4. 保留离线宽限，但改为**服务端签发短期票据**（带服务端时间戳与签名），客户端只在票据有效期内放行。

**验收**：本地改 `pricing.json`、改系统时间、伪造缓存文件，三者都无法获得权限。

---

## P2 · 其他

- [ ] 闸门覆盖面复查：确认所有"执行类"入口都过了 `check_entitlement_gate`
      （当前 5 处：app.py 7097/7271、app_macos.py 1048/1159/3492）。
      新增功能入口时记得补闸，建议抽成装饰器统一处理。
- [ ] `_cached_server_now` 失败时回退本地系统时间，可考虑改为回退"上次已知服务器时间 + 已流逝的单调时间"。
- [ ] 定期（建议每季度）复查 Supabase 的策略列表，确认没有残留 `using (true)` 的写策略。

---

## 已完成（2026-09-08）

- [x] P0-2 闸门 fail-closed：`app.py` `check_entitlement_gate` 异常与缺键不再放行
- [x] P1-3 试用期天数上限：`entitlement.py` 新增 `MAX_TRIAL_DAYS = 7`
- [x] P1-4 离线宽限加固：系统时间回拨检测 + 离线放行次数上限（5 次）+ 时间上限（1 天）
- [x] P2 补闸：`app_macos.py` `run_selected_combo_skills` 批量运行组合技原先无闸门
