import subprocess
import os
import sys

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

with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as f:
    f.write(safe_gitignore)
print("✅ .gitignore 已精简")

subprocess.run(f'git remote set-url origin "{GITHUB_URL}"', shell=True)
print(f"✅ 远程仓库已切换到: {GITHUB_URL}")

result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
if not result.stdout.strip():
    print("📝 没有新文件变更，直接推送...")
    result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ 推送失败: {result.stderr}")
        subprocess.run("git config --global credential.helper store", shell=True)
        print("💡 已设置 credential.helper=store，请重新运行脚本")
    else:
        print("✅ 推送完成！")
    input("按 Enter 退出...")
    sys.exit(0)

subprocess.run("git add -A", shell=True)
commit = subprocess.run('git commit -m "auto_update: add all key files"', shell=True, capture_output=True, text=True)
if commit.returncode != 0:
    print(f"⚠️ 提交跳过: {commit.stderr.strip()}")
else:
    print("✅ 提交成功")

print("⏳ 正在推送到 GitHub...")
result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"❌ 推送失败: {result.stderr}")
    subprocess.run("git config --global credential.helper store", shell=True)
    print("💡 已设置 credential.helper=store，请重新运行脚本")
else:
    print("✅ 全部关键文件已推送完成！")

input("按 Enter 退出...")