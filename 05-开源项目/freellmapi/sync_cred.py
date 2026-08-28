"""每次启动 harness 前，把 freeapi.db 里当前的 unified key 同步进 dsh 凭据库
~/.dsh/.credentials.yaml，覆盖可能过期的旧缓存，避免 harness 用旧 key 打后端报 AUTH。
db 读不到时回退到已知正确 key，保证万无一失。
"""
import sqlite3
import os

DB = r"D:\codespace\05-开源项目\freellmapi\server\data\freeapi.db"
CRED = os.path.expanduser(r"~\.dsh\.credentials.yaml")
FALLBACK = "freellmapi-86554f302d377a210b3a094ff8f1ad820549406aa7cd4f0d"

key = None
try:
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=8)
    row = c.execute("SELECT value FROM settings WHERE key='unified_api_key'").fetchone()
    c.close()
    if row and row[0]:
        key = row[0]
except Exception as e:
    print("read db failed:", e)

if not key:
    key = FALLBACK
    print("use fallback key")

yaml = f"version: 1\n\nrefs:\n  FREELLMAPI_API_KEY: {key}\n"
with open(CRED, "w", encoding="utf-8") as f:
    f.write(yaml)
print("synced credential:", key[:16] + "...")
