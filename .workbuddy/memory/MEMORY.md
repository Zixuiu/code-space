# 长期约定（MEMORY）

## 代码修改后自动推送
- **用户要求**：每次修改代码之后，都运行 `一键推送.py` 把改动推送到 GitCode（`git@gitcode.com:weixin_58844486/codespace.git`）。
- **推送方式**：在 `D:\codespace` 下执行 `printf '\n\n' | "C:/Users/INK/.workbuddy/binaries/python/versions/3.13.12/python.exe" 一键推送.py`（脚本内的 input 用换行喂入）。
- **若 push 被拒（remote 有新提交）**：先 `git fetch origin && git rebase origin/main`，再跑脚本。
- **注意**：脚本用 `git add .`，会把 `.workbuddy/` 私人目录（工作记忆、本地配置）一并提交。如不想同步该目录，需将其加入 `.gitignore`（曾提醒用户，尚未执行）。
- 推送脚本日志中"工作区干净，无需提交"为描述顺序误报；实际已 commit 并 push（以 `git log` / `git status` 为准）。
