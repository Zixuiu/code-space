# -*- coding: utf-8 -*-
p = r'D:\codespace\.workbuddy\memory\2026-08-26.md'
note = '''
## 主 bat 不自动开浏览器 + harness key 同步修复（2026-08-26 凌晨）
- 现象：双击打开DeepSeekHarness.bat 后日志停在「后端未起，调用 recover」，浏览器不弹。
- 根因1：主 bat 第16行用 `call recover_freellmapi.bat` 同步调用，而 recover 结尾有 `pause`（"请按任意键继续"），导致主 bat 卡在 recover 的 pause 上，后面「启动 harness + 开浏览器」整段没执行。
- 根因2：harness `settings.yaml` 用 `apiKeyEnv: FREELLMAPI_API_KEY` 从环境变量取 key；`start_dsh.bat` 未设该变量；且 recover 每次都重置数据库、生成**新 key**（旧 key 失效），所以 harness 即使起来也会 401。
- 修复：
  1. `recover_freellmapi.bat` 去掉结尾 `pause`（保留其它全部逻辑），`call` 现在能干净返回。
  2. 新增 `get_key.py`：从 `freellmapi_server.log` 正则提取最新 `unified API key: freellmapi-...`（取最后一次出现，兼容多次 recover）。
  3. `start_dsh.bat` 启动 `dsh web` 前用 `for /f` 调用 `get_key.py` 把当前 key 注入 `FREELLMAPI_API_KEY`，harness 永远用活 key，不受 recover 换 key 影响。
- 三个文件均用 Python 字节法生成（GBK+CRLF+无BOM），已校验。生成脚本 `fix_bats.py` 保留可复跑。
- 当前有效 key（recover 重置后）：`freellmapi-589ad72ea17305b5d6b52e89bc8bb95c875393e9a96565ff`（旧 `freellmapi-1aace98d...` 已失效）。管理后台登录仍用 `1399972370@qq.com` / `freellmapi123`。
- 用户对"双击bat不自动跳浏览器"的诉求：已通过去 pause + 动态 key 解决；主 bat 末尾 `start "" "http://127.0.0.1:3080"` 在 3001+3080 都就绪后自动开浏览器。
'''
with open(p, 'a', encoding='utf-8') as f:
    f.write(note)
print("appended; exists:", __import__('os').path.exists(p))
