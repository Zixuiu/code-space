@echo off
chcp 65001 >nul
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在请求管理员权限...
    powershell start -verb runas '%0'
    exit
)

reg query "HKLM\SYSTEM\CurrentControlSet\Services\i8042prt" /v DisableDevice | find "0x1" >nul
if %errorlevel% equ 0 (
    :: 当前已禁用，恢复自带键盘
    reg add "HKLM\SYSTEM\CurrentControlSet\Services\i8042prt" /v DisableDevice /t REG_DWORD /d 0 /f
    sc config i8042prt start= auto
    echo 自带键盘已恢复开启
) else (
    :: 实时屏蔽内置键盘（真正禁用）
    reg add "HKLM\SYSTEM\CurrentControlSet\Services\i8042prt" /v DisableDevice /t REG_DWORD /d 1 /f
    sc config i8042prt start= disabled
    echo 自带键盘已成功禁用
)

echo.
echo 请重启电脑生效！
pause
exit