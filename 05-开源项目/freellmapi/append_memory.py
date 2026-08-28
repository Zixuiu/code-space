import os

p = r'D:\codespace\.workbuddy\memory\2026-08-26.md'
note = r'''
## DeepSeek Harness (dsh) 启动假死根因与修复（2026-08-26 凌晨）
- 现象：双击打开DeepSeekHarness.bat 后 harness 一直起不来，dsh_web.log 空白，node 进程常驻十几分钟无输出（看似卡死）。
- 根因：dsh 启动时 healProfilesModuleFallback 把 dsh 主包的整个依赖闭包（几百个包）写入 ~/.dsh/profiles/node_modules。ensureSymlink 在 Windows 上对每包执行 rmSync + 递归 copyFileSync（源码注释：Windows junction 不可靠故用 copy），导致启动时递归复制几百个目录——极慢（假死），且 heal 不打印任何进度。
- 修复：改 C:\Users\stk_gb\dsh-deploy\node_modules\@deepseek-ai\dsh-app-boot\lib\index.js 的 ensureSymlink，Windows 分支用 fsApp.symlinkSync(target, link, "junction")（O(1) 创建，普通用户无需特权）替代递归复制。原文件备份为 index.js.bak_heal。
- 效果：heal 从几十分钟复制变秒过，harness 启动剩余时间主要是前端编译（约 2.5 分钟），日志出现 dsh web: http://127.0.0.1:3080，3080 返回 200 HTML。
- bat 配套修复：桌面 打开DeepSeekHarness.bat 端口检测从不可靠的 powershell -Command ... || 改为 bat 原生 netstat -ano | findstr（避免 || 因 PowerShell 返回对象而永不触发）；拆出 start_dsh.bat 自包含 PATH。已验证 GBK+CRLF。
- 关键机制：web profile 的 bundle（dsh-web-app/dsh-base）来自 dsh 安装目录（installAnchor=dsh-deploy），由 heal 写入 ~/.dsh/profiles/node_modules（顶层）。曾误建 web/node_modules 的 junction 不在 heal 路径且干扰，已删。
- 提醒：此 dsh 源码修改为本地改动，dsh 重装/更新会丢失，需重打补丁（ensureSymlink 加 win32 junction 分支）。
'''

with open(p, 'a', encoding='utf-8') as f:
    f.write(note)
print('appended', os.path.exists(p))
