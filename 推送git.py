import subprocess, os
from datetime import datetime

root = r"D:\codespace"
os.chdir(root)

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

def git_push(remote="origin", branch="main", retries=3):
    # 关键：设置 SSH 自动接受新主机密钥，防止交互式提示卡死
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"
    for attempt in range(1, retries + 1):
        try:
            result = subprocess.run(
                ["git", "push", remote, branch],
                capture_output=True, text=True, timeout=45, env=env,
                # 标准输入重定向到 DEVNULL，防止 SSH 等待输入
                stdin=subprocess.DEVNULL
            )
        except subprocess.TimeoutExpired:
            print(f"⏱️ 推送到 {remote} 超时(第{attempt}次)")
            if attempt < retries:
                print(f"⏳ {attempt * 2}s 后重试...")
                import time
                time.sleep(attempt * 2)
            continue
        if result.returncode == 0:
            return True
        err = result.stderr.strip()
        print(f"❌ 推送到 {remote} 失败(第{attempt}次): {err}")
        if attempt < retries:
            wait = attempt * 2
            print(f"⏳ {wait}s 后重试...")
            import time
            time.sleep(wait)
    return False

# 1. 自动添加 known_hosts（带超时保护）
known_hosts = os.path.expanduser("~/.ssh/known_hosts")
for host in ["gitcode.com"]:
    try:
        r = subprocess.run(["ssh-keygen", "-F", host], capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        print(f"⏱️ ssh-keygen 查询 {host} 超时，跳过 known_hosts 检查")
        continue
    if r.returncode != 0:
        print(f"🔑 正在添加 {host} 到 known_hosts...")
        try:
            subprocess.run(f'ssh-keyscan -H {host} >> "{known_hosts}"', shell=True, timeout=15)
        except subprocess.TimeoutExpired:
            print(f"⏱️ ssh-keyscan 连接 {host} 超时，已跳过（可稍后手动添加）")

# 2. 写 .gitignore
with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as f:
    f.write(safe_gitignore)
print("✅ .gitignore 已精简")

# 3. 设置远程仓库
subprocess.run(["git", "remote", "set-url", "origin", GITCODE_URL], timeout=15)
print(f"✅ 远程仓库(GitCode): {GITCODE_URL}")

# 4. 检查是否有变更
status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=15)

if not status.stdout.strip():
    print("📝 没有新文件变更，直接推送...")
else:
    subprocess.run(["git", "add", "-A"], timeout=30)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit = subprocess.run(["git", "commit", "-m", f"auto_update {now}"], capture_output=True, text=True, timeout=30)
    if commit.returncode != 0:
        err = commit.stderr.strip()
        if "nothing to commit" in err:
            print("📝 没有新变更，跳过提交")
        elif "LF will be replaced" not in err and "CRLF" not in err:
            print(f"⚠️ 提交跳过: {err}")
    else:
        print("✅ 提交成功")

# 5. 推送（自动重试）
print(f"⏳ 正在推送到 GitCode...")
all_ok = git_push(retries=3)
if all_ok:
    print("✅ 推送完成！")
else:
    print("💡 推送失败，请检查网络后重试")

print("\n⏹️  按 Enter 键退出...")
input()