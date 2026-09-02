@echo off
REM ============================================================
REM  scrcpy quick launcher
REM  scrcpy is the most fluid open-source phone mirroring tool
REM  (lowest latency, best quality). This just launches it.
REM
REM  Before mirroring, the phone must be connected to this PC:
REM   - USB: enable "USB debugging" on the phone, plug in, run scrcpy
REM   - WiFi: on the phone enable Developer options -> Wireless debugging,
REM           pair with "adb pair IP:PORT" + code, then "adb connect IP:PORT"
REM ============================================================
cd /d "%~dp0"
echo.
echo scrcpy launcher
echo (phone must be connected via USB debugging or Wireless debugging)
echo.
scrcpy.exe %*
