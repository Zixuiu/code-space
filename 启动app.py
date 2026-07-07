"""启动脚本：运行 PC-action macOS 应用"""
import os
import sys
import subprocess

# 当前目录（d:\codespace）
root = os.path.dirname(os.path.abspath(__file__))

# app.py 的路径
app_dir = os.path.join(root, "01-开发项目", "PC-action", "PC-action-macOS")
app_path = os.path.join(app_dir, "app.py")

if not os.path.exists(app_path):
    print(f"错误：找不到 app.py\n路径：{app_path}")
    print("请确保项目结构完整。")
    input("按 Enter 键退出...")
    sys.exit(1)

print(f"正在启动 PC-action 应用...")
print(f"路径：{app_path}")

# 切换到 app.py 所在目录并运行
os.chdir(app_dir)
subprocess.run([sys.executable, app_path])