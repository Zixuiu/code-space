@echo off
setlocal
"%~dp0adb.exe" kill-server >nul 2>&1
"%~dp0adb.exe" start-server
echo ===== adb devices =====
"%~dp0adb.exe" devices
echo.
echo If list is EMPTY: connect phone via USB with USB debugging ON, or run adb_wifi_connect.bat
echo If status is "device": connected OK
echo If status is "offline": phone is HarmonyOS NEXT, adb not supported, need hdc
echo.
pause
