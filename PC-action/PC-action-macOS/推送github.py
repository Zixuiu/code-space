import subprocess
import os
import sys
import socket
from datetime import datetime

root = r"D:\code空间"
os.chdir(root)

GITHUB_URL = "https://github.com/Zixuiu/code-space.git"

safe_gitignore = """__pycache__/
*.pyc
*.pyo
*.egg-info/
/dist/
/build/
*.log
*.db
.DS_Store
Thumbs.db
.trae/
.vscode/
_fix_*.py
_apply_*.py
_patch_*.py
_tmp*
debug.log
*.bak
*.bak2
*.old
recordings/
trash/
"""

def detect_proxy():
    common_ports = [7890, 7891, 7897, 10808, 10809, 1080, 1081, 8080, 8118, 2080, 33210]
    for port in common_ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            s.close()
            return port
        s.close()
    return None

def git_push(retries=2):
    for attempt in range(1, retries + 1):
        result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(result.stdout)
            return True
        print(f"❌ 推送失败(第{attempt}次): {result.stderr.strip()}")
        if attempt < retries:
            print(f"⏳ {2}s 后重试...")
            import time
            time.sleep(2)
    return False

# 1. 代理检测
proxy_port = detect_proxy()
if proxy_port:
    proxy_url = f"http://127.0.0.1:{proxy_port}"
    subprocess.run(["git", "config", "--global", "http.proxy", proxy_url])
    subprocess.run(["git", "config", "--global", "https.proxy", proxy_url])
    print(f"✅ 检测到代理端口: {proxy_port}，已设置 git 代理")
else:
    subprocess.run(["git", "config", "--global", "--unset", "http.proxy"], capture_output=True)
    subprocess.run(["git", "config", "--global", "--unset", "https.proxy"], capture_output=True)
    print("⚠️ 未检测到代理，将尝试直连")

# 2. 写 .gitignore
with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as f:
    f.write(safe_gitignore)
print("✅ .gitignore 已精简")

# 3. 设置远程仓库
subprocess.run(["git", "remote", "set-url", "origin", GITHUB_URL])
print(f"✅ 远程仓库: {GITHUB_URL}")

# 4. 检查是否有变更
subprocess.run(["git", "config", "--global", "credential.helper", "store"])
status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)

if not status.stdout.strip():
    print("📝 没有新文件变更，直接推送...")
else:
    # 5. 有变更，提交（commit 信息带时间）
    subprocess.run(["git", "add", "-A"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit = subprocess.run(["git", "commit", "-m", f"auto_update {now}"], capture_output=True, text=True)
    if commit.returncode != 0:
        print(f"⚠️ 提交跳过: {commit.stderr.strip()}")
    else:
        print("✅ 提交成功")

# 6. 推送（自动重试）
print("⏳ 正在推送到 GitHub...")
if git_push(retries=2):
    print("✅ 推送完成！")
else:
    print("💡 推送失败，请检查网络或代理设置后重试")

input("按 Enter 退出...")