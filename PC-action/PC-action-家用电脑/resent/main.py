"""
主入口文件 - 直接运行应用程序
"""
import sys
import os

# 获取当前目录（支持打包后的环境）
if getattr(sys, 'frozen', False):
    # 打包后的环境
    current_dir = os.path.dirname(sys.executable)
else:
    # 开发环境
    current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加当前目录到路径
sys.path.insert(0, current_dir)

# 导入并运行主应用
from app import start_app

if __name__ == "__main__":
    start_app()
