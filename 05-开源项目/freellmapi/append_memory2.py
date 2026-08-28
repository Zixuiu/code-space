note = '''
## 打开DeepSeekHarness.bat 端口检测再修复（2026-08-26 凌晨）
- 现象：双击 bat 后窗口停在"检查 3080"后整段不再执行，浏览器不弹出，dsh_web.log 无新内容（start_dsh.bat 未被调用）。
- 根因：bat 用 `netstat -ano | findstr ":3080" | findstr "LISTENING"` 做端口检测，该 findstr 管道在中文 cmd 下偶发卡死/提前结束，导致后续 `if errorlevel` 分支未执行、bat 静默退出（非逻辑错误）。
- 修复：端口检测改用 `powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort X -State Listen -ErrorAction SilentlyContinue; if($c -ne $null){exit 0}else{exit 1}"`，返回明确 exit code，`if errorlevel 1` 正确分支。已验证 GBK+CRLF、无 netstat、引用 start_dsh.bat、末尾 pause。
- 注：AI 侧 `node bin.js web` 直接拉 harness 在沙箱环境不稳定（偶发静默卡在 heal 阶段），应以用户本机双击 bat（走 dsh.cmd）为准；junction 修复后用户本机 dsh web 可正常起（heal 秒过）。
'''
p = r'D:\codespace\.workbuddy\memory\2026-08-26.md'
with open(p, 'a', encoding='utf-8') as f:
    f.write(note)
print('appended')
