import os
NL = b"\r\n"
lines = [
    b"@echo off",
    b"setlocal",
    b'set "ROOT=%~dp0"',
    b'set "WB_NODE_DIR=C:\\Users\\stk_gb\\.workbuddy\\binaries\\node\\versions\\22.22.2"',
    b'set "PATH=%WB_NODE_DIR%;%PATH%"',
    b"echo === fix_ajv4.bat ===",
    b"echo.",
    b"echo [1/3] closing any leftover node processes (tsx watch)...",
    b"taskkill /IM node.exe /F",
    b"echo.",
    b"echo [2/3] removing broken server\\node_modules\\ajv folder...",
    b'if exist "%ROOT%server\\node_modules\\ajv" goto :do_rmdir',
    b"goto :after_rmdir",
    b":do_rmdir",
    b'rmdir /s /q "%ROOT%server\\node_modules\\ajv"',
    b":after_rmdir",
    b"echo.",
    b"echo [3/3] reinstalling ajv in server/ (fresh download, ~30s)...",
    b'cd /d "%ROOT%server"',
    b"call npm install ajv --no-audit --no-fund",
    b"echo.",
    b"echo === done. now close this window and re-run run_freellmapi2.bat ===",
    b"pause",
]
content = NL.join(lines) + NL
out = r"D:\codespace\freellmapi\fix_ajv4.bat"
with open(out, "wb") as f:
    f.write(content)
data = open(out, "rb").read()
print("size:", len(data), "CRLF:", data.count(b"\r\n"), "BOM:", data[:3] == b"\xef\xbb\xbf")
print("has C:\\Users:", b"C:\\Users" in data)
print("bad /r/n:", b"/r/n" in data)
print("bad C://:", b"C://" in data)
print("has set PATH line:", b'set "PATH=' in data)
