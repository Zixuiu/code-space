import os
import subprocess
import sys
from datetime import datetime

# ====== 切换到项目目录 ======
project_dir = r"d:\code空间\PC-action\PC-action-macOS"
os.chdir(project_dir)
print(f"📂 切换到: {project_dir}")

# ====== 1. git add . ======
print("📦 git add .")
r = subprocess.run(["git", "add", "."], capture_output=True, text=True)
if r.returncode != 0:
    print(f"❌ {r.stderr}")
    sys.exit(1)
print("✅ 暂存完成")

# ====== 2. git commit（有变更才提交）====== 
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
commit_msg = f"update {timestamp}"
print(f"💾 git commit -m \"{commit_msg}\"")
r = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode != 0:
    if "nothing to commit" in r.stdout or "nothing to commit" in r.stderr:
        print("⚠️  没有新变更，跳过提交")
    else:
        print(f"⚠️  {r.stderr}")

# ====== 3. git push ======
print("🚀 git push")
r = subprocess.run(["git", "push"], capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode != 0:
    print(f"❌ 推送失败: {r.stderr}")
    sys.exit(1)
print("✅ 推送成功！🎉")