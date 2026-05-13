"""
打包脚本：将应用程序打包为单个exe文件
包含所有数据文件和数据库
"""
import PyInstaller.__main__
import os
import shutil

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 桌面路径
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
output_dir = os.path.join(desktop_path, "PC-action-家用电脑")

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 构建 --add-data 参数
add_data_args = []

# 添加数据文件到user_data目录
# 注意：在单文件模式下，数据文件会被解压到临时目录
# 我们需要在代码中处理这种情况

# 添加JSON配置文件
data_files = [
    ("users.json", "user_data"),
    ("login_credentials.json", "user_data"),
    ("saved_login.json", "user_data"),
    ("local_users.db", "user_data"),
    ("target_light_red.png", "."),
    ("target_deep_red.png", "."),
    ("check.png", "."),
    (".env.example", "."),
]

for filename, dest_dir in data_files:
    filepath = os.path.join(current_dir, filename)
    if os.path.exists(filepath):
        add_data_args.extend(["--add-data", f"{filename};{dest_dir}"])

# 添加recordings目录
if os.path.exists(os.path.join(current_dir, "recordings")):
    add_data_args.extend(["--add-data", "recordings;recordings"])

# PyInstaller参数 - 单文件模式
args = [
    "main.py",  # 入口文件
    "--name", "PC-action-家用电脑",  # 输出文件名
    "--onefile",  # 打包成单个exe文件
    "--windowed",  # 不显示控制台窗口
    "--distpath", output_dir,  # 输出目录
    "--workpath", os.path.join(current_dir, "build"),  # 临时文件目录
    "--specpath", current_dir,  # spec文件目录
    "--clean",  # 清理临时文件
    "--noconfirm",  # 不询问确认
    # 隐藏导入
    "--hidden-import", "keyboard",
    "--hidden-import", "PIL.ImageGrab",
    "--hidden-import", "sqlite3",
    "--hidden-import", "supabase_db",
    "--hidden-import", "database_helper",
    "--hidden-import", "hybrid_db",
    "--hidden-import", "login_manager",
    "--hidden-import", "login_ui",
    "--hidden-import", "selection_overlay",
    "--hidden-import", "styles",
    "--hidden-import", "utils",
    "--hidden-import", "admin_manager",
    "--hidden-import", "image_recognition",
    # 排除不必要的模块以减小体积
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy",
    "--exclude-module", "pandas",
    "--exclude-module", "tkinter",
    "--exclude-module", "unittest",
]

# 添加数据文件参数
args.extend(add_data_args)

print("开始打包为单文件exe...")
print(f"输出目录: {output_dir}")
print(f"数据文件: {[a for a in add_data_args if not a.startswith('--')]}")

# 运行PyInstaller
PyInstaller.__main__.run(args)

print(f"\n打包完成！")
print(f"输出文件: {os.path.join(output_dir, 'PC-action-家用电脑.exe')}")
