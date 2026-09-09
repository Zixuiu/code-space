# Code Space 工作区

> 最后更新：2026-09-09

统一的本地开发工作区。按 `01`~`05` 编号分类，编号只用于排序，不代表优先级。
（`03` 目前空缺，原移动应用项目已移除。）

## 目录结构

```
codespace/
├── 01-space/                    # 桌面 / 服务端项目
│   ├── PC-action/               # ⭐ 桌面自动化工具（应用名已改为 Action）
│   │   └── PC-action-macOS/     #    Python + PyQt5 主工程
│   └── PayPro/                  # 支付充值服务（Java + Docker）
│       ├── PayPro-master/       #    服务端主工程（Spring Boot）
│       ├── tools/               #    激活码生成、端口代理、充值页样式稿
│       ├── qr_processed/        #    已处理的收款二维码
│       ├── qr_src/              #    二维码原始素材
│       └── paypro-config.json   #    充值页配置（推送到远端供客户端拉取）
│
├── 02-Web应用/                  # 纯前端 / 网页
│   ├── 各种速成html/
│   │   ├── fde/
│   │   └── langchain/
│   └── 清单/                    # 清单管理（含 txt 版本说明）
│
├── 04-工具脚本/                 # 本机常用脚本
│   ├── git工具/                 # 一键推送 / 一键拉取
│   ├── 系统工具/                # IP 切换、预设、禁用自带键盘
│   └── open_deepharness.bat
│
├── 05-开源项目/                 # 第三方 / 独立仓库
│   └── freellmapi/              # LLM 代理网关（自带独立 git 仓库）
│
├── README.md
└── .gitignore
```

## 项目速览

| 项目 | 位置 | 类型 | 说明 |
|---|---|---|---|
| **Action**（原 PC-Action） | `01-space/PC-action/PC-action-macOS/` | Python + PyQt5 | 桌面自动化：录制操作流程后一键重复执行。含激活码授权、组合技能、图像识别 |
| **PayPro** | `01-space/PayPro/` | Java + Docker | 支付/充值服务端，搭配 `tools/` 下的发码与代理脚本，为 Action 提供会员支付能力 |
| 各种速成 html | `02-Web应用/各种速成html/` | HTML | fde、langchain 等单页演示 |
| 清单 | `02-Web应用/清单/` | HTML + JS | 清单管理工具 |
| git 工具 | `04-工具脚本/git工具/` | Python | 一键推送/拉取，SSH 失败自动回退 HTTPS |
| freellmapi | `05-开源项目/freellmapi/` | Node.js | LLM 代理网关，独立仓库，需自行 `npm install` |

## 常用操作

启动 Action（开发模式）：

```bash
cd 01-space/PC-action/PC-action-macOS
python main.py
```

打包 Action 为 Windows 安装包：见
[`01-space/PC-action/PC-action-macOS/installer/BUILD.md`](01-space/PC-action/PC-action-macOS/installer/BUILD.md)，
流程是「装依赖 → PyInstaller 出 `dist/Action` → NSIS 编译成安装包」，NSIS 便携版已随仓库提供，无需额外安装。

Git 推送：

```bash
python 04-工具脚本/git工具/一键推送.py
```

## 约定

- **编号前缀**：`01-`~`05-`，便于排序
- **中文目录名**：描述清楚即可
- **新增项目**：放进对应编号目录后更新本文档
- **脚本里不要写死 `D:/codespace/...` 绝对路径**，用 `Path(__file__)` 相对定位，否则移动目录就失效

## 已知问题

- `02-Web应用/各种速成html/fde/gen_fde.py` 里 `BASE` 仍写死 `D:/codespace/各种速成html/fde`，
  与该文件的实际位置不符，跑之前需改成相对路径。
- `01-space/PC-action/PC-action-macOS/build/` 与 `dist/` 都是 PyInstaller 生成物，已被 `.gitignore` 忽略。
- `05-开源项目/` 根部的 `package.json` / `package-lock.json` 属于 `freellmapi` 之外的一层，
  确认无用后可清理（`freellmapi` 自己目录下也有一套）。

## 注意

- `.gitignore` 里忽略了 `dist/`、`installer/output/`、`.venv/`，这些都是生成物，不要手动加进仓库。
- 移动目录后务必回到本文档更新路径，并检查脚本内的路径引用。
