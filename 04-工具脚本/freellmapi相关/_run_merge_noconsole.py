import os, sys, io, datetime

# === 重定向所有输出到日志文件 ===
PROJECT_DIR = r'd:\codespace\01-开发项目\PC-action\PC-action-macOS'
LOG_FILE = os.path.join(PROJECT_DIR, f"_merge_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

class Tee:
    def __init__(self, stream, log_fp):
        self.stream = stream
        self.log_fp = log_fp
    def write(self, data):
        try: self.stream.write(data)
        except Exception: pass
        try: self.log_fp.write(data)
        except Exception: pass
    def flush(self):
        try: self.stream.flush()
        except Exception: pass
        try: self.log_fp.flush()
        except Exception: pass

_log_fp = open(LOG_FILE, 'a', encoding='utf-8')
sys.stdout = Tee(sys.stdout, _log_fp)
sys.stderr = Tee(sys.stderr, _log_fp)

# === 执行合并 ===
exec(open(os.path.join(PROJECT_DIR, '_safe_merge.py'), encoding='utf-8').read())

_log_fp.close()
print(f"\nLOG WRITTEN TO: {LOG_FILE}", file=open(os.path.join(PROJECT_DIR, '_last_merge_result.txt'), 'w', encoding='utf-8'))