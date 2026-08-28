bat = r'''@echo off
setlocal
echo [停止] 停止 DeepSeek Harness (端口 3080) ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3080" ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
echo [停止] 停止 freellmapi 后端 (端口 3001) ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001" ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
echo [完成] 已停止两项服务（端口本就未占用则无操作）
pause
'''
with open(r'C:\Users\stk_gb\Desktop\停止DeepSeekHarness.bat', 'wb') as f:
    f.write(bat.replace('\n', '\r\n').encode('gbk'))
print("written: C:\\Users\\stk_gb\\Desktop\\停止DeepSeekHarness.bat")
