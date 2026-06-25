import subprocess, os, sys, socket
from datetime import datetime

root = r"D:\code空间"
os.chdir(root)

GITHUB_URL = "git@github.com:Zixuiu/code-space.git"
GITCODE_URL = "git@gitcode.com:weixin_58844486/codespace.git"

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

def git_push(remote="origin", branch="main", retries=2):
    for attempt in range(1, retries + 1):
        result = subprocess.run(["git", "push", remote, branch], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(result.stdout)
            return True
        print(f"❌ 推送到 {remote} 失败(第{attempt}次): {result.stderr.strip()}")
        if attempt < retries:
            print(f"⏳ {2}s 后重试...")
            import time
            time.sleep(2)
    return False

# 1. SSH 方式不需要代理检测，已跳过

# 2. 写 .gitignore
with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as f:
    f.write(safe_gitignore)
print("✅ .gitignore 已精简")

# 3. 设置远程仓库（SSH）
subprocess.run(["git", "remote", "set-url", "origin", GITHUB_URL])
subprocess.run(["git", "remote", "rm", "gitcode"], capture_output=True)
subprocess.run(["git", "remote", "add", "gitcode", GITCODE_URL])
print(f"✅ 远程仓库(GitHub - SSH): {GITHUB_URL}")
print(f"✅ 远程仓库(GitCode - SSH): {GITCODE_URL}")

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

# 6. 推送（自动重试到两个远程仓库）
all_ok = True
for rmt, lbl in [("origin", "GitHub"), ("gitcode", "GitCode")]:
    print(f"⏳ 正在推送到 {lbl}...")
    if not git_push(remote=rmt, retries=2):
        all_ok = False
if all_ok:
    print("✅ 全部推送完成！")
else:
    print("💡 部分推送失败，请检查网络或代理设置后重试")

input("按 Enter 退出...")
