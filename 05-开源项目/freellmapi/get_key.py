# -*- coding: utf-8 -*-
import re, os, sqlite3

def from_db():
    """从 freeapi.db 的 settings.unified_api_key 读取明文 key（权威来源，实时）。"""
    db = r"D:\codespace\05-开源项目\freellmapi\server\data\freeapi.db"
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        c.execute("PRAGMA busy_timeout=5000")
        row = c.execute("SELECT value FROM settings WHERE key='unified_api_key'").fetchone()
        c.close()
        if row and row[0]:
            return row[0].strip()
    except Exception:
        return None
    return None

def from_log():
    """兼容旧方式：从启动日志正则提取 unified API key。"""
    log = r"D:\codespace\05-开源项目\freellmapi\freellmapi_server.log"
    if os.path.exists(log):
        try:
            text = open(log, encoding="utf-8", errors="replace").read()
            m = list(re.finditer(r"unified API key\s*:\s*(freellmapi-[\w]+)", text, re.IGNORECASE))
            if m:
                return m[-1].group(1).strip()
        except Exception:
            pass
    return None

key = from_db() or from_log()
if key:
    print(key)
