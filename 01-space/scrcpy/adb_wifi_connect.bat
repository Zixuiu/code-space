@echo off
setlocal
"%~dp0adb.exe" kill-server >nul 2>&1
"%~dp0adb.exe" start-server
set /p IP="Enter phone IP (e.g. 192.168.1.187): "
set /p PAIRPORT="Enter PAIRING port (the 37xxx one from phone, NOT the connect port): "
echo.
echo adb will now ask for the 6-digit pairing code. Type it and press Enter.
echo.
"%~dp0adb.exe" pair %IP%:%PAIRPORT%
set /p CONNPORT="Enter CONNECT port (e.g. 43961): "
"%~dp0adb.exe" connect %IP%:%CONNPORT%
echo.
echo ===== devices =====
"%~dp0adb.exe" devices
echo.
echo If status is "device": success.
echo If "offline": phone is HarmonyOS NEXT, adb unsupported, need hdc.
echo.
pause
