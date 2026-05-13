import sys
import os

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
app_path = os.path.join(current_dir, "app.py")

# 直接运行主程序，不使用subprocess
# 这样可以确保窗口正常显示
sys.path.insert(0, current_dir)

# 导入并运行主应用
from app import start_app

if __name__ == "__main__":
    start_app()
