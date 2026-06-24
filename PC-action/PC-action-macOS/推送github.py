import subprocess
import os

root = "D:\\code空间"
os.chdir(root)

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
nul
recordings/
trash/
"""

with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as f:
    f.write(safe_gitignore)
print("✅ .gitignore 已精简，不再排除关键目录")

# 设置远程仓库地址为 GitHub
subprocess.run("git remote set-url origin https://github.com/Zixuiu/code-space.git", shell=True)
print("✅ 远程仓库已切换到 GitHub: https://github.com/Zixuiu/code-space.git")

subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "auto_update: add all key files"', shell=True)
subprocess.run("git push -u origin main --force", shell=True)
print("✅ 全部关键文件已推送完成！")