# PC-Action 商业化发布执行文档

> 目标：明天面向公众发布，99 元/月订阅制
> 生成时间：2026-09-04 晚 | 执行窗口：今晚 → 明早
> 依据：2026-09-04 对代码库的实际勘察 + 已确认决策（PayPro 收款 / Supabase 已建项目 / Inno Setup 安装包 / 仅 99 元月付单档）

---

## 〇、现状盘点（勘察结论）

### 已就绪（直接复用）
| 模块 | 文件 | 状态 |
|---|---|---|
| 登录注册（本地+云端混合+邮箱验证） | login_ui.py / login_manager.py / hybrid_db.py | ✅ 完整 |
| 管理后台（用户/VIP/反馈管理） | admin_manager.py（2074 行） | ✅ 完整 |
| 权益引擎（卡密激活+7天试用+到期判定） | entitlement.py | ✅ 代码完整，**但未接线** |
| VIP 时长管理/充值记录 | database_helper.py `manage_vip_license` | ✅ 完整 |
| 崩溃日志 | crash_logger.py（主入口已装） | ✅ 完整 |
| 打包配置 | PC-Action.spec | ⚠️ 存在但 datas 为空 |

### 阻断性缺口（P0，全部要今晚→明早解决）
1. **Supabase 未配置**：无 .env，URL/KEY 均为占位符 → 云登录/权益/激活码全部不可用
2. **付费闸未接入**：`entitlement.has_full_access` 在主程序 **0 处调用** → 不付费也能永久用
3. **激活码无 UI 入口**：`activate_code` 无任何界面调用 → 用户买码没地方输
4. **定价不符**：pricing.json 是 9.9/月 + 100/年占位，需改 99/月单档
5. **支付未通**：PayPro 未部署，channel_url 是 your_id 占位
6. **打包未验证**：spec 的 datas 为空（icons/ 与 pricing.json 不会进包），从未产出过安装包

---

## 一、To-do List（按优先级，T1→T8 顺序执行）

### 【P0 · 今晚必须完成】
| # | 任务 | 预估 | 依赖 |
|---|---|---|---|
| T1 | Supabase 配置 + 建表 + RLS | 40min | 无 |
| T2 | 定价改 99/月单档（4 处一致性） | 15min | T1 |
| T3 | 激活码 UI 入口（程序内输码激活） | 45min | T1 |
| T4 | 付费闸接入主程序（试用/VIP 到期锁功能） | 60min | T3 |
| T5 | PayPro 部署 + 99 元商品 + 支付成功发卡 | 90min | T1 |
| T6 | 打包：补 spec → PyInstaller → Inno Setup | 90min | T2,T3,T4 |
| T7 | 全流程冒烟回归（干净环境安装实测） | 45min | T6 |
| T8 | 用户协议 + 隐私声明打包进安装包 | 30min | 与 T6 并行 |

### 【P1 · 发布当天上午】
| # | 任务 | 预估 |
|---|---|---|
| T9 | 下载/购买落地页（改造 PayPro 首页即可：介绍+下载+购买按钮） | 60min |
| T10 | 客服渠道就位（QQ 群 or 邮箱，写进「关于」页与协议） | 20min |
| T11 | 杀软误报预案（本地实测各杀软扫描结果 + 写用户加白教程） | 40min |
| T12 | 发布总 Checkpoint（CP1~CP8 复走一遍 + 首批用户监控值班） | 30min |

### 【P2 · 发布后一周内（不阻断发布）】
| # | 任务 |
|---|---|
| T13 | 自动更新：启动时请求版本接口 `/version.json`，提示新版本 |
| T14 | Supabase 每日自动导出备份（users + activation_codes + 订单） |
| T15 | 续费提醒：VIP 到期前 3 天弹窗引导再购 |
| T16 | 基础防逆向（PyInstaller 解包门槛：`--key` 已废，改 pyc 混淆 pyarmor） |
| T17 | 埋点统计：注册数/激活数/崩溃率日报（为调价和迭代做依据） |

---

## 二、Checklist（每个 To-do 的硬性自检指标）+ Checkpoint（通过/不通过闸门）

> 规则：**每完成一个 To-do，立即跑对应 Checklist；Checkpoint 显示 ✅ 才允许开始下一个 To-do。**
> 任何 CP 不通过 → 当场修复重跑，不得带病进入下一项。

---

### T1 Supabase 配置 + 建表 + RLS

**操作**：
1. Supabase 控制台 → Project Settings → API：复制 `Project URL` 和 `anon public key`
2. 项目根目录建 `.env`（**此文件必须加入 .gitignore，绝不入库**）：
   ```
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_KEY=eyJhbGciOi...（anon key）
   ```
3. SQL Editor 建三张表（如未建）：
   ```sql
   create table if not exists users (
     id bigint generated always as identity primary key,
     username text unique not null,
     password_hash text not null,
     is_vip int default 0,
     vip_end_date text,
     is_admin int default 0,
     created_at text default (now()::text)
   );
   create table if not exists activation_codes (
     id bigint generated always as identity primary key,
     code text unique not null,
     plan text default 'plan_1',
     months int default 1,
     used int default 0,
     used_by text, used_at text, note text,
     created_at text
   );
   create table if not exists feedback (
     id bigint generated always as identity primary key,
     username text, content text, contact_info text,
     created_at text
   );
   ```
   （字段名以 supabase_db.py / hybrid_db.py 实际读写为准，建表前先对一遍代码）
4. RLS：开启表级 RLS；anon 角色按代码实际访问面放行 select/insert/update 所需最小权限

**Checklist C1**：
- [ ] .env 存在且已在 .gitignore 中（`git check-ignore .env` 有输出）
- [ ] 写 10 行测试脚本 `python -c` 连库：insert 测试用户 → 查回 → 删除，全程无异常
- [ ] activation_codes 表手动插一条测试码能查到
- [ ] git status 确认 .env 未被跟踪

**Checkpoint CP1**：`[通过/不通过]` 测试脚本连库+增删查全通，且 .env 未进版本库。不通过 → 禁止做 T2。

---

### T2 定价 99/月单档（四处一致）

**操作**：pricing.json 改为：
```json
{
  "plan_1": {"name": "PC-Action 会员", "price": 99.0, "months": 1, "desc": "包月 · 全功能"},
  "trial_days": 7,
  "channel_name": "PayPro",
  "channel_url": "（T5 部署后填购买页地址）"
}
```
同时检查 admin_manager 后台定价编辑页、登录窗会员页（若有）展示价格是否读同一配置。

**Checklist C2**：
- [ ] pricing.json = 99.0 / months=1 / 单档（删除 plan_2 或留空不展示）
- [ ] 程序内所有展示价格的位置（会员弹窗/购买引导/后台）显示 ¥99/月，无 9.9/100 残留（全局搜 `9.9`、`100.0`）
- [ ] 激活码 months=1 与商品一致

**Checkpoint CP2**：`[通过/不通过]` 全局搜无旧价格残留，程序内显示 ¥99。

---

### T3 激活码 UI 入口

**操作**：
1. 新建 `activation_dialog.py`：输入框 + 「激活」按钮 + 跳转购买页链接
2. 接 `entitlement.activate_code(code, username)`，成功后刷新权益状态显示
3. 入口挂三处：① 登录后主窗「会员/关于」菜单 ② 试用期到期弹窗的「输入激活码」按钮 ③ admin 后台「批量生成激活码」确认能产出码

**Checklist C3**：
- [ ] 后台 `generate_activation_codes(5, 1)` 生成 5 个码，Supabase 表可见 used=0
- [ ] 用测试码在 UI 激活：提示「激活成功，已开通 1 个月会员」，表内 used=1、used_by=测试账号
- [ ] 同一码再次激活 → 提示「已被使用」；乱码 → 「激活码无效」
- [ ] 断网状态激活 → 提示「服务未连接」，不崩

**Checkpoint CP3**：`[通过/不通过]` 从生成→激活→重复激活→无效码→断网，5 条路径行为全部正确。

---

### T4 付费闸接入主程序（核心，最容易被漏）

**操作**：
1. 登录成功后调用 `entitlement.get_entitlement(username)`，缓存权益状态
2. 主窗启动与每次关键功能入口（动作录制/回放/组合技执行）检查 `has_access`
3. 无权限时：弹出「试用已结束」引导窗（含：剩余天数 / 购买页链接 / 输码激活按钮），阻断功能执行
4. **离线宽限策略**：Supabase 不可达时放行（代码 fallback 已是放行，保持），避免误伤付费用户；但连续 72h 离线且从未验证过 VIP 的账号下次联网时强制重校
5. 试用期 UI：主窗角标显示「试用剩余 X 天」；VIP 显示「会员至 yyyy-mm-dd」

**Checklist C4**：
- [ ] 新注册账号 → 主窗显示试用剩余 7 天，全功能可用
- [ ] 在 Supabase 手动把该用户 created_at 改为 8 天前 → 重启 → 功能被锁 + 购买引导窗弹出
- [ ] 激活 1 个月 → 锁解除，显示会员到期日（=今天+31 天左右，核对 manage_vip_license 的加月逻辑）
- [ ] 断网启动（付费账号）→ 不锁、不崩
- [ ] 断网启动（试用过期账号）→ 按 fallback 放行（可接受的宽松项，记录为已知行为）

**Checkpoint CP4**：`[通过/不通过]` 「试用内可用 / 过期被锁 / 激活解锁 / 断网不崩」四态全部符合。

---

### T5 PayPro 部署 + 99 元商品 + 发卡闭环

**操作**：
1. 克隆 `github.com/codewendao/PayPro`，按 README 部署（本机或你的服务器；需 Python Web 环境）
2. 配置你的微信/支付宝收款码；支付方式选「备注对账 + 邮件审批」模式起步
3. 上架单一商品：「PC-Action 会员月卡 ¥99」；**订单成功页/邮件中自动附带一个激活码**（改 PayPro 的 order-success 流程：从 Supabase `activation_codes` 取一条 used=0 的码标记预留并展示；改造前先跑通「人工发码」兜底路径）
4. 每天早上检查卡密池：后台预生成 ≥30 个未用码（`generate_activation_codes(30, 1)`），低于 10 个及时补
5. channel_url 填 PayPro 购买页地址，回填 pricing.json（完成 CP2 复验）

**Checklist C5**：
- [ ] 购买页公网可访问（手机流量打开不依赖你的局域网）
- [ ] 真实支付 1 笔 ¥99（或先建 ¥1 测试商品走全流程再删）：下单→付款→到账确认→拿到激活码
- [ ] 拿到的码在程序内激活成功（与 T3 闭环）
- [ ] 收款进你的微信/支付宝个人账户（核对无中间托管）
- [ ] 卡密池余量 ≥30，补货流程自己能 1 分钟完成

**Checkpoint CP5**：`[通过/不通过]` 真·付一笔钱→真·拿到码→真·激活成功，全链路无人工干预环节卡死（人工兜底不算卡死）。

---

### T6 打包（PyInstaller → Inno Setup）

**操作**：
1. 修 PC-Action.spec：`datas` 补 `('icons', 'icons'), ('pricing.json', '.')`；hiddenimports 视打包报错补；确认 onefile（现状）或改 onedir（启动更快，推荐 onedir + 安装包包裹）
2. 干净构建：`pyinstaller PC-Action.spec`（在 .venv 内装好 pyinstaller/inno 依赖）
3. 图标：exe 与安装包用同一 ico（从 icons 里选或新做 256px 多尺寸）
4. 版本信息：exe 加 VERSIONINFO（1.0.0，公司名/产品名——写你自己的）
5. Inno Setup 脚本：装后建桌面/开始菜单快捷方式、默认装 Program Files、卸载清理 data 目录可选、**安装时请求 administrator 权限**（manifest requireAdministrator，与主程序 UAC 逻辑一致）
6. 产出 `PC-Action_Setup_1.0.0.exe`

**Checklist C6**：
- [ ] 打包产物在**未装 Python 的目录**直接双击能启动（或经安装包安装后启动）
- [ ] 程序内 28 个 SVG 图标全部正常显示（icons 打进包了）
- [ ] 登录→试用→激活→录制→回放 五项在打包版全部可用
- [ ] exe 右键属性有版本号 1.0.0 与产品名
- [ ] 安装包卸载后开始菜单/桌面项清除
- [ ] `.env` **没有**被打进包（密钥走安装后首次配置或编译期注入方案二选一——见下「密钥分发」）

**⚠ 密钥分发决策（CP6 前必须定）**：打包版无 .env 时 Supabase 连不上。两个方案：
- 方案 A（快）：编译期把 URL/anon key 注入 spec 或环境变量读取逻辑，打进 exe（anon key 本就是前端可见级别，RLS 是真正防线——**确认 RLS 规则正确即可接受**）
- 方案 B（稳）：首次启动向导让用户不填，密钥由你内置但混淆存放
**默认走方案 A + RLS 收紧。**

**Checkpoint CP6**：`[通过/不通过]` 干净机器安装→五项功能全通→图标版本信息齐全→密钥方案落地且 RLS 生效。

---

### T7 全流程冒烟回归

**操作**：用 T6 的安装包，在一台**干净 Windows**（或新建虚拟机）完整走一遍用户旅程。

**Checklist C7（= 用户旅程剧本）**：
- [ ] 安装（UAC 弹窗正常）→ 启动 → 注册（收验证邮件）→ 登录
- [ ] 主窗显示「试用剩余 7 天」，28 个图标正常
- [ ] WiFi 手机控制器连接一次（若有真机条件）
- [ ] 录制一段动作（Esc 退出正常）→ 回放成功 → turbo 模式正常
- [ ] 崩溃日志文件 `PC-Action运行日志.txt` 正常生成于预期位置
- [ ] 制造一次试用过期 → 锁定+引导窗 → 输码激活 → 解锁
- [ ] 反馈入口提交一条 → admin 后台能看到
- [ ] 全程无未捕获崩溃弹窗

**Checkpoint CP7**：`[通过/不通过]` 剧本 8 项全绿。任何一项红 → 修复 → **重跑整个 C7**（不是只跑那一项）。

---

### T8 用户协议 + 隐私声明

**操作**：写 `EULA.txt` + `PRIVACY.txt` 随安装包发布，关键条款：
1. 本软件提供键鼠自动化与图像识别能力，**用户须对使用行为负责**；不得用于破坏计算机系统、外挂作弊、批量注册等违法违规场景，违者责任自负、账号可被终止
2. 数据说明：账号信息与权益存于云端（Supabase）；**录制的脚本/截图模板仅保存在用户本地**，软件不上传
3. 付费说明：99 元/月，按月开通不自动续费，到期需重新购买；已激活时长不因卸载/重装丢失（绑定账号）
4. 免责：因杀软误报、系统差异导致的自动化执行失败，提供技术支持但不承诺在所有环境 100% 可用

**Checklist C8**：
- [ ] 两份文档随安装包安装（开始菜单/安装目录可打开）
- [ ] 首次启动弹一次「同意协议」勾选框，不同意则退出
- [ ] 协议内含客服联系方式（与 T10 一致）

**Checkpoint CP8**：`[通过/不通过]` 新装首启必见协议弹窗，勾选才可进入。

---

### P1 项的轻量 Checklist（发布当天上午）
- **T9 落地页**：手机流量可打开；下载按钮指向最新安装包；购买按钮指向 PayPro；页面有 99/月 明示与客服方式
- **T10 客服**：QQ 群/邮箱在程序「关于」、协议、落地页三处一致；你本人能收到消息
- **T11 杀软**：把安装包上传 VirusTotal 留档；若主流杀软报毒 → 准备「加白教程」图文（Windows Defender 简单路径）；**不要**为此推迟发布，但要准备好客服话术
- **T12 发布总闸**：CP1~CP8 重走一遍全 ✅ + 你手机能收到首笔支付通知 + 卡密池满仓 → **发布**

---

## 三、付费方案总览（今晚落地版）

```
用户旅程：
下载安装包 → 安装(需管理员) → 注册/登录 → 7天全功能试用(角标倒计时)
   → 试用到期 → 锁定+购买引导窗
   → 跳转 PayPro 购买页 → 扫码付 ¥99(备注用户名)
   → PayPro 到账确认(备注对账/邮件审批) → 自动展示激活码 + 邮件发送
   → 程序内「输入激活码」 → Supabase 校验 → VIP +31天 → 解锁全功能
   → 到期前3天弹续费提醒 → 再购一码叠加时长
```

| 环节 | 方案 | 备注 |
|---|---|---|
| 收款 | PayPro（个人收款码+备注对账） | 零手续费；全自动识别不稳时切「邮件审批/手动确认」 |
| 发码 | activation_codes 表（后台预生成≥30） | PayPro 成功页自动带码为最优；人工发码兜底 |
| 校验 | entitlement.activate_code → Supabase 一次性核销 | 离线宽限放行，联网强校 |
| 续费 | 重购激活码叠加 months | 个人渠道做不了自动扣款，P2 用提醒+一键跳购买页弥补 |
| 防刷 | 一码一用+used_by 记录 | P2 加同账号 24h 激活次数上限 |

**明晚就要上线，所以接受这两个已知妥协**（记录在案，P2 改进）：
1. 支付到自动化程度取决于 PayPro 对账模式，首日可能需要你盯单人工确认几笔
2. 无代码签名证书 → 杀软大概率误报，靠加白教程+客服兜住（签名证书约几百至千元/年，P2 采购）

---

## 四、明日发布倒排时刻表（建议）

| 时间 | 动作 |
|---|---|
| 今晚 20:00-24:00 | T1→T2→T3→T4（Supabase/定价/激活UI/付费闸） |
| 今晚 24:00-01:00 | T5 PayPro 部署+测试支付 |
| 明早 08:00-09:30 | T6 打包 + T8 协议 |
| 明早 09:30-10:15 | T7 干净机全流程回归 |
| 明早 10:15-11:30 | T9 落地页 + T10 客服 + T11 杀软预案 |
| 明早 11:30 | T12 发布总 Checkpoint → 开闸发布 |

> 执行原则：**每晚一个 CP 闸门就当场修，不攒到明天。** T7 冒烟发现问题优先级高于一切新功能念头。
