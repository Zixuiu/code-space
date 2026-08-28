out = r"C:\Users\stk_gb\Desktop\打开DeepSeekHarness.bat"
lines = [
    "@echo off",
    "setlocal",
    'set "WB_NODE_DIR=C:\\Users\\stk_gb\\.workbuddy\\binaries\\node\\versions\\22.22.2"',
    'set "PATH=%WB_NODE_DIR%;%PATH%"',
    'set "DST_DIR=C:\\Users\\stk_gb\\dsh-deploy"',
    'set "DSH=%DST_DIR%\\node_modules\\.bin\\dsh.cmd"',
    "echo [FreeHarness] checking port 3080 ...",
    'netstat -ano 2>nul | findstr /C:":3080 " >nul',
    "if %errorlevel%==0 goto :open",
    "echo [FreeHarness] starting DeepSeek Harness (dsh web) ...",
    'start "" /min cmd /c "%DSH% web --no-open > %DST_DIR%\\dsh_web.log 2>&1"',
    "echo [FreeHarness] waiting for server on :3080 (first boot installs deps, ~1-2 min) ...",
    "set \"TRIES=0\"",
    ":wait",
    "set /a TRIES+=1",
    "if %TRIES% GTR 40 goto :open",
    'netstat -ano 2>nul | findstr /C:":3080 " >nul',
    "if %errorlevel%==0 goto :open",
    "timeout /t 3 >nul",
    "goto :wait",
    ":open",
    "echo [FreeHarness] server is up. opening http://127.0.0.1:3080 ...",
    'start "" "http://127.0.0.1:3080"',
    "exit",
]
data = ("\r\n".join(lines) + "\r\n").encode("utf-8")
with open(out, "wb") as f:
    f.write(data)
print("wrote", out, len(data), "bytes")
