# 长期约定（MEMORY）

## 代码修改后自动推送
- **用户要求**：每次修改代码之后，都运行 `一键推送.py` 把改动推送到 GitCode（`git@gitcode.com:weixin_58844486/codespace.git`）。
- **推送方式**：在 `D:\codespace` 下执行 `printf '\n\n' | "C:/Users/INK/.workbuddy/binaries/python/versions/3.13.12/python.exe" 一键推送.py`（脚本内的 input 用换行喂入）。
- **若 push 被拒（remote 有新提交）**：先 `git fetch origin && git rebase origin/main`，再跑脚本。
- **注意**：脚本用 `git add .`，会把 `.workbuddy/` 私人目录（工作记忆、本地配置）一并提交。如不想同步该目录，需将其加入 `.gitignore`（曾提醒用户，尚未执行）。
- 推送脚本日志中"工作区干净，无需提交"为描述顺序误报；实际已 commit 并 push（以 `git log` / `git status` 为准）。

## 运行环境
- **PC-action 在公司电脑上需以管理员身份运行**：`keyboard` 库的全局钩子在非管理员权限下不稳定，回放（高频模拟按键）后热键容易"按了没反应"。家用电脑同样代码没问题，说明是环境权限差异，不是代码 bug。
- 已确认回放后热键恢复逻辑干净（只清 `_hotkeys_temporarily_disabled` 标志位，不再调 `unhook_all`），因此失效根因在公司电脑环境（管理员权限/杀软干扰），不在代码。
- 后续若反复遇到"回放后快捷键失效"，第一排查点：是否以管理员身份运行程序；其次为公司杀软/EDR 是否拦截全局键盘钩子。

## 热键失效的代码根因审计（2026-08-06）
- **核心链路**：注册 `update_shortcuts()`(10157)/`register_record_hotkey`(9703)/`register_stop_replay_hotkey`(9723) → `keyboard.add_hotkey` → 回调里查 `_hotkeys_temporarily_disabled`(10188等) 与 `replay_enabled`(10193) → 触发 `_safe_replay_folder`(10221 起线程)。
- **回放后失效的真正代码原因（用户当前症状）**：keyboard 库 `listening_thread`/`processing_thread` 可能因回放高频模拟按键崩溃，但 `_listener.listening` 仍是 True，导致热键"注册了却不被处理"。定时健康检查 `_check_and_restore_hotkeys`(9770起, 每1秒) **已同时检查线程存活**（9783-9817：检测 `listening_thread.is_alive()`/`processing_thread.is_alive()`，线程死了即触发 `_reinitialize_all_hotkeys` 恢复）——但回放刚结束那一瞬线程可能正崩溃、1秒轮询有延迟；且若线程"卡死但未判定死亡"（alive=True 却不处理事件），健康检查也查不出。
- **之前"删回放后重新初始化"的副作用**：原回放 finally 会调 `_reinitialize_all_hotkeys()`（含线程死亡检测 9929-9951: 线程死则 `listening=False`），删掉后回放后无及时修复，只能等不健全的健康检查。但现已可安全加回——`_cleanup_all_hotkeys`(9990)/`_reinitialize_all_hotkeys`(9874) **已不含 `unhook_all`**（10002/9988注释确认），不会杀线程。
- **其它失效路径**：①`_hotkeys_temporarily_disabled` 卡 True（正常回放 finally/stop_replay 都清，风险低）；②`_replay_lock` 死锁（7179非阻塞获取, finally 7286释放, 超时强制释放 9832-9841, 会导致"按了不回放"而非"完全无反应"）；③`replay_enabled=False`(10193/7419)；④快捷键字符串 keyboard 不支持（如 F1+F2 系统键, 10237）；⑤多实例重复注册残留。
- **已实施修复（commit 2c6a270, 2026-08-06）**：A) 健康检查 `_check_and_restore_hotkeys` 已含线程存活检测（无需再改）；B) **回放 finally 块加回主动自愈**：清 `_hotkeys_temporarily_disabled` 标志位后，立即 `threading.Thread(target=self._check_and_restore_hotkeys, daemon=True).start()`，回放一结束就跑健康检查（线程若已死立刻触发 `_reinitialize_all_hotkeys` 恢复，健康时零副作用），不再干等那 1 秒；C) 新增 `_check_admin_and_warn()`：程序启动时检测 Windows 管理员权限，非管理员弹窗提醒"建议以管理员身份运行"，直接验证环境假设。三处均 `py_compile` 通过并推送。
