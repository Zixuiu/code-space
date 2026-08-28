# -*- coding: utf-8 -*-
import os

WB = r'C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2'
FL = r'D:\codespace\05-开源项目\freellmapi'
DSH = r'C:\Users\stk_gb\dsh-deploy'

# ---------- recover_freellmapi.bat (放在 05-开源项目\freellmapi) ----------
recover = (
    '@echo off\r\n'
    'setlocal\r\n'
    f'set "WB_NODE_DIR={WB}"\r\n'
    'set "PATH=%WB_NODE_DIR%;%PATH%"\r\n'
    'set "ROOT=%~dp0"\r\n'
    'echo === recover_freellmapi.bat : 恢复免费 API 后端 ===\r\n'
    'echo.\r\n'
    'echo [1/5] 生成 server/.env (ENCRYPTION_KEY) ...\r\n'
    'if exist "%ROOT%server\\.env" goto :have_env\r\n'
    'powershell -NoProfile -Command "$k=([BitConverter]::ToString((1..32|%%{Get-Random -Maximum 256})) -replace \'-\',\'\'); Set-Content -Path \'%ROOT%server\\.env\' -Value \"ENCRYPTION_KEY=$k`nPORT=3001`nNODE_ENV=production\" -Encoding utf8"\r\n'
    'goto :after_env\r\n'
    ':have_env\r\n'
    'echo .env 已存在，跳过生成\r\n'
    ':after_env\r\n'
    'echo.\r\n'
    'echo [2/5] npm install (重建 better-sqlite3 原生模块，约 5-10 分钟) ...\r\n'
    'cd /d "%ROOT%server"\r\n'
    'call npm install --no-audit --no-fund\r\n'
    'echo.\r\n'
    'echo [3/5] npm run build (tsc -> dist) ...\r\n'
    'call npm run build\r\n'
    'echo.\r\n'
    'echo [4/5] 重置数据库以便重新引导 (旧 key 将失效，会生成新 key) ...\r\n'
    'if exist "%ROOT%server\\data\\freeapi.db" del "%ROOT%server\\data\\freeapi.db"\r\n'
    'echo.\r\n'
    'echo [5/5] 启动服务 (后台隐藏运行) ...\r\n'
    'taskkill /IM node.exe /F\r\n'
    'timeout /t 2 /nobreak >nul\r\n'
    'powershell -NoProfile -Command "Start-Process -FilePath \'%WB_NODE_DIR%\\node.exe\' -ArgumentList \'dist/index.js\' -WorkingDirectory \'%ROOT%server\' -WindowStyle Hidden -RedirectStandardOutput \'%ROOT%freellmapi_server.log\' -RedirectStandardError \'%ROOT%freellmapi_server.err\'"\r\n'
    'timeout /t 15 /nobreak >nul\r\n'
    'cd /d "%ROOT%"\r\n'
    'node bootstrap.mjs\r\n'
    'echo.\r\n'
    'echo === 完成。服务日志: %ROOT%freellmapi_server.log ===\r\n'
    'echo === 上面的 Unified API Key 就是新的免费端点密钥 ===\r\n'
    'pause\r\n'
)

# ---------- 打开DeepSeekHarness.bat (放在桌面) ----------
desktop = (
    '@echo off\r\n'
    'setlocal\r\n'
    f'set "WB_NODE_DIR={WB}"\r\n'
    'set "PATH=%WB_NODE_DIR%;%PATH%"\r\n'
    f'set "FL={FL}"\r\n'
    f'set "DSH={DSH}"\r\n'
    'echo [FreeHarness] 检查端口 3001 (freellmapi 后端) ...\r\n'
    'powershell -NoProfile -Command "if(-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 3001 -WarningAction SilentlyContinue -InformationLevel Quiet)){ exit 1 }" || (\r\n'
    '  echo [FreeHarness] 后端未运行，正在恢复并启动 freellmapi ...\r\n'
    '  start "" "%FL%\\recover_freellmapi.bat"\r\n'
    ')\r\n'
    'echo [FreeHarness] 检查端口 3080 (harness 界面) ...\r\n'
    'powershell -NoProfile -Command "if(-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 3080 -WarningAction SilentlyContinue -InformationLevel Quiet)){ exit 1 }" || (\r\n'
    '  echo [FreeHarness] 正在启动 DeepSeek Harness (dsh web) ...\r\n'
    '  start "" /min cmd /c "cd /d \\"%DSH%\\" && node node_modules\\.bin\\dsh web --no-open"\r\n'
    ')\r\n'
    'echo [FreeHarness] 等待服务就绪 (最多约 5 分钟，首次需装依赖) ...\r\n'
    'set "OK=0"\r\n'
    'for /l %%i in (1,1,100) do (\r\n'
    '  powershell -NoProfile -Command "if((Test-NetConnection -ComputerName 127.0.0.1 -Port 3001 -WarningAction SilentlyContinue -InformationLevel Quiet) -and (Test-NetConnection -ComputerName 127.0.0.1 -Port 3080 -WarningAction SilentlyContinue -InformationLevel Quiet)){ exit 0 } else { exit 1 }" && set "OK=1" && goto :open\r\n'
    '  timeout /t 3 /nobreak >nul\r\n'
    ')\r\n'
    ':open\r\n'
    'if "%OK%"=="1" (\r\n'
    '  echo [FreeHarness] 服务已就绪，打开浏览器 ...\r\n'
    ') else (\r\n'
    '  echo [FreeHarness] 等待超时，请查看后台恢复窗口的日志\r\n'
    ')\r\n'
    'start "" "http://127.0.0.1:3080"\r\n'
    'exit\r\n'
)

def write_gbk(path, content):
    with open(path, 'wb') as f:
        f.write(content.encode('gb18030'))

write_gbk(os.path.join(FL, 'recover_freellmapi.bat'), recover)
write_gbk(r'C:\Users\stk_gb\Desktop\打开DeepSeekHarness.bat', desktop)

print('written recover ->', os.path.join(FL, 'recover_freellmapi.bat'), len(recover), 'chars')
print('written desktop ->', r'C:\Users\stk_gb\Desktop\打开DeepSeekHarness.bat', len(desktop), 'chars')
