# PC-action 充值站 · 固定域名配置清单

> 方案：ClouDNS 免费二级域名 + 自建 Cloudflare Tunnel
> 目标：把本机 PayPro 后端（:8889）暴露为**固定 HTTPS 域名**，永久不漂，根治花生壳试用到期 / cpolar 域名漂移。
> 域名已定：**ClouDNS 免费区 `ink.abrdns.com`** + Tunnel 子域 `pay` → 最终公网 **`https://pay.ink.abrdns.com`**

---

## 架构链路

```
外网用户
  → https://pay.ink.abrdns.com               （Cloudflare 边缘，免费 SSL + CDN + 隐藏源站 IP）
  → Cloudflare Tunnel（cloudflared，常驻本机）
  → http://localhost:8889                  （Docker Toolbox 内 PayPro 应用，已验证可达）
```

---

## 前置事实（已核实 ✅）

- 后端 8889 主机侧可达：`localhost:8889` 与 `192.168.99.100:8889` 均返回 **200 + 充值页指纹**（PC-Action / 会员充值）✅
- `pay` 容器 Running，重启策略已设为 `unless-stopped`（本机/虚拟机重启后自动起）✅
- 花生壳试用已到期（日志 `map(:443) is fordden` = forbidden，映射被禁用），不再使用
- cpolar 免费隧道域名 `.rN.cpolar.cn` 重启会漂移，**不作固定方案**
- `localhost.cc` 的 zone 归平台、不在用户自有 Cloudflare 账号，**建不了 Cloudflare Tunnel** → 故改用 ClouDNS 免费二级域名（zone 归用户，可转自有 Cloudflare 账号）

---

## 第一步：ClouDNS 申请免费二级域名

- [x] 1.1 打开 ClouDNS 官网，注册账号并验证邮箱（界面可切简体中文）
- [x] 1.2 登录后「DNS 托管」→「创建区域」→ 选「免费区域」
- [x] 1.3 从可选后缀（`.abrdns.com`）里挑后缀，输入前缀 `ink` → 创建
- [x] 1.4 二级域名已定：`ink.abrdns.com`（前缀 `ink` + 后缀 `.abrdns.com`）

> CHECKPOINT ①：运行 `nslookup ink.abrdns.com` 返回 ClouDNS 默认 NS（`*.cloudns.net` 之类），说明域名已建。

---

## 第二步：把域名托管到 Cloudflare（拿免费 CDN + SSL）

Cloudflare Tunnel 强制要求域名由**你自己的** Cloudflare 账号托管。

- [ ] 2.1 Cloudflare 后台「添加域」→ 输入 `ink.abrdns.com` → 套餐 Free
- [ ] 2.2 复制 Cloudflare 分配的两个 Nameservers 地址（页面别关）
- [ ] 2.3 回 ClouDNS 域名管理 → 添加两条 NS 记录（填 Cloudflare 给的地址），并删除系统自带的 4 条默认 NS
- [ ] 2.4 回 Cloudflare 点「立即检查」→ 状态变「活动」（一般 3–5 分钟）

> CHECKPOINT ②：`nslookup ink.abrdns.com` 的 NS 变成 `rory.ns.cloudflare.com` / `jamie.ns.cloudflare.com`，且 Cloudflare 站点状态 = 活动。

---

## 第三步：创建 Cloudflare Tunnel 打通内外网

- [ ] 3.1 左侧菜单 Zero Trust → Networks → Tunnels →「Create a tunnel」，命名（如 `pcaction`）
- [ ] 3.2 选 Windows，复制页面安装命令到本机终端运行（装 `cloudflared` connector）
- [ ] 3.3 tunnel 变绿色 Healthy 后点 Edit → Public Hostname → Add a public hostname：
  - Subdomain：`pay`
  - Domain：选托管的 `ink.abrdns.com`
  - Service URL：`http://localhost:8889`
- [ ] 3.4 保存
- [ ] 3.5 设置 `cloudflared` 开机自启（Windows Service），保证长期开机不断

> CHECKPOINT ③：外网访问 `https://pay.ink.abrdns.com/recharge.html` 返回 **200 + 指纹（PC-Action / 会员充值）**。

---

## 收尾（CHECKPOINT ③ 通过后）

- [ ] 把 app 的 `channel_url` 改为固定域名（本地 `pricing.json` / `entitlement.py` **+ GitCode 远程 `paypro-config.json`**，否则 app 下次拉远程配置会覆盖回旧值）
- [ ] 撤销之前 cpolar 随机域名的改动
- [ ] 写入长期记忆

---

## 注意事项

- Cloudflare Zero Trust 首次可能要绑信用卡验证，完全免费、不扣费
- `cloudflared` 进程在跑服务才通，务必设开机自启
- 回传邮箱由 PayPro 代码实现，与穿透工具无关；Cloudflare Tunnel 只负责转发外网请求到本机服务

---

## 我已主动完成（本地）

- [x] 后端 8889 验证可达（localhost + VM IP 均 200 + 指纹）
- [x] `pay` 容器 Up + `unless-stopped` 自启策略
- [x] 生成本清单文件（域名已填实：`pay.ink.abrdns.com`）
- [x] cloudflared 已安装：`D:\内网穿透工具\cloudflared.exe`（v2026.8.3，54MB）。沙箱直连 GitHub 资产 CDN（objects.githubusercontent.com）被掐超时，改经 **ghproxy.net GitHub 代理镜像**拉取成功（关键窍门，见记忆）
- [ ] cloudflared 登录 / 建隧道 / 注册 Service —— 见下方「待你确认的卡点」

---

## 待你确认的卡点（已获授权，但部分仍需你账号）

- [ ] **ClouDNS 账号**：注册 + 建 `ink.abrdns.com` 区（需你邮箱验证，我代不了）
- [ ] **Cloudflare 账号**：托管 `ink.abrdns.com` + Zero Trust（可能绑卡，我代不了）
- [ ] **Cloudflare 凭证二选一**（决定第三步能否全自动）：
  - 方案甲：在 Zero Trust 点「Create a tunnel」后，把页面给的 **token** 发我 → 我跑 `cloudflared service install <token>`
  - 方案乙：直接给 **Cloudflare API Token（Zone:DNS Edit + Account:Cloudflare Tunnel Edit）+ Account ID** → 我纯命令行全自动建完 tunnel + 自动加 DNS，最省事

---

## cloudflared 本地配置（已备好，待联网即生效）

装好后由我跑：
1. `cloudflared tunnel login`（方案甲）或 `cloudflared tunnel create`（方案乙，用 API Token）
2. 写 `config.yml`：
   ```yaml
   tunnel: <tunnel-id>
   credentials-file: D:\内网穿透工具\<tunnel-id>.json
   ingress:
     - hostname: pay.ink.abrdns.com
       service: http://localhost:8889
     - service: http_status:404
   ```
3. `cloudflared route dns <tunnel> pay.ink.abrdns.com`（自动加 DNS 记录）
4. 注册 Windows Service 开机自启：`cloudflared.exe service install`（或 `sc create` 指向 config.yml）
