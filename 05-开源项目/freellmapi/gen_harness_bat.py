bat = r'''@echo off
setlocal
set "WB_NODE_DIR=C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2"
set "PATH=%WB_NODE_DIR%;%PATH%"
set "FL=D:\codespace\05-开源项目\freellmapi"
set "DSH=C:\Users\stk_gb\dsh-deploy"
set "LOG=D:\codespace\05-开源项目\freellmapi\harness_launcher.log"

echo [%time%] === FreeHarness 启动 === > "%LOG%"
echo [FreeHarness] 检查端口 3001 (freellmapi 后端) ...
echo [%time%] 检查 3001 >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=Get-NetTCPConnection -LocalPort 3001 -State Listen -ErrorAction SilentlyContinue; if($c -ne $null){exit 0}else{exit 1}"
if errorlevel 1 (
  echo [FreeHarness] 后端未运行，正在恢复并启动 freellmapi ...
  echo [%time%] 后端未起，调用 recover >> "%LOG%"
  call "%FL%\recover_freellmapi.bat"
) else (
  echo [%time%] 3001 已在运行 >> "%LOG%"
)

echo [FreeHarness] 检查端口 3080 (harness 界面) ...
echo [%time%] 检查 3080 >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=Get-NetTCPConnection -LocalPort 3080 -State Listen -ErrorAction SilentlyContinue; if($c -ne $null){exit 0}else{exit 1}"
if errorlevel 1 (
  echo [FreeHarness] 正在启动 DeepSeek Harness (dsh web) ...
  echo [%time%] 启动 dsh web >> "%LOG%"
  start "" /min "%FL%\start_dsh.bat"
) else (
  echo [%time%] 3080 已在运行 >> "%LOG%"
)

echo [FreeHarness] 等待服务就绪 (最多约 10 分钟) ...
echo [%time%] 进入等待循环 >> "%LOG%"
set "OK=0"
for /l %%i in (1,1,200) do (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$a=Get-NetTCPConnection -LocalPort 3001 -State Listen -EA SilentlyContinue; $b=Get-NetTCPConnection -LocalPort 3080 -State Listen -EA SilentlyContinue; if(($a -ne $null) -and ($b -ne $null)){exit 0}else{exit 1}"
  if not errorlevel 1 (
    set "OK=1"
    goto :open
  )
  timeout /t 3 /nobreak >nul
)
:open
if "%OK%"=="1" (
  echo [FreeHarness] 服务已就绪，打开浏览器 ...
  echo [%time%] 就绪，打开浏览器 >> "%LOG%"
) else (
  echo [FreeHarness] 等待超时！harness 未启动，详见 dsh_web.log
  echo [%time%] 超时 >> "%LOG%"
)
start "" "http://127.0.0.1:3080"
echo [%time%] 完成(已尝试打开浏览器) >> "%LOG%"
pause
'''
with open(r'C:\Users\stk_gb\Desktop\打开DeepSeekHarness.bat', 'wb') as f:
    f.write(bat.replace('\n', '\r\n').encode('gbk'))
print("written: C:\\Users\\stk_gb\\Desktop\\打开DeepSeekHarness.bat")
