import os, time
bat = r'd:\codespace\01-开发项目\PC-action\PC-action-macOS\_safe_merge.bat'
log = r'd:\codespace\01-开发项目\PC-action\PC-action-macOS\_merge_result.txt'

# 先清空旧日志
try: open(log, 'w').close()
except: pass

print("Starting merge via BAT... (no console output, results written to file)")
print(f"Executing: {bat}")
ret = os.system(f'""{bat}" >nul 2>&1"')
print(f"BAT process exit code: {ret}")
print(f"Waiting for log file...")

# 等待日志出现
for i in range(30):
    if os.path.exists(log) and os.path.getsize(log) > 500:
        break
    time.sleep(1)

if os.path.exists(log):
    print("\n=== MERGE RESULT (from log) ===")
    with open(log, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
        print(content[-3000:] if len(content) > 3000 else content)
else:
    print("ERROR: Log file was not generated.")