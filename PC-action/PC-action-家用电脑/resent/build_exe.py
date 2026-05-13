"""
打包脚本：将应用程序打包为文件夹模式
数据文件放在外部，便于修改
"""
import PyInstaller.__main__
import os
import shutil

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 桌面路径
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
output_dir = os.path.join(desktop_path, "PC-action-家用电脑")

# 确保输出目录存在（如果存在则保留，避免权限问题）
os.makedirs(output_dir, exist_ok=True)

# PyInstaller参数 - 使用文件夹模式
args = [
    "start_app.py",  # 入口文件
    "--name", "PC-action-家用电脑",  # 输出文件名
    "--onedir",  # 打包成文件夹模式（不是单文件）
    "--windowed",  # 不显示控制台窗口
    "--distpath", desktop_path,  # 输出目录（桌面）
    "--workpath", os.path.join(current_dir, "build"),  # 临时文件目录
    "--specpath", current_dir,  # spec文件目录
    "--clean",  # 清理临时文件
    "--noconfirm",  # 不询问确认
    # 只包含必要的隐藏导入
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
    "--exclude-module", "numpy.random._examples",
    "--exclude-module", "scipy",
    "--exclude-module", "pandas",
    "--exclude-module", "tkinter",
    "--exclude-module", "unittest",
    "--exclude-module", "pydoc",
    "--exclude-module", "xmlrpc",
    "--exclude-module", "multiprocessing",
]

print("开始打包...")
print(f"输出目录: {output_dir}")
print("使用文件夹模式，数据文件将放在外部")

# 运行PyInstaller
PyInstaller.__main__.run(args)

# 复制数据文件到输出目录（外部，便于修改）
print("\n复制数据文件...")

# 复制数据库
db_src = os.path.join(current_dir, "local_users.db")
db_dst = os.path.join(output_dir, "local_users.db")
if os.path.exists(db_src):
    shutil.copy2(db_src, db_dst)
    print(f"  - local_users.db")

# 复制JSON配置文件
json_files = ["saved_login.json", "login_credentials.json", "users.json"]
for json_file in json_files:
    src = os.path.join(current_dir, json_file)
    dst = os.path.join(output_dir, json_file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  - {json_file}")

# 复制图片文件
png_files = ["target_light_red.png", "target_deep_red.png", "check.png"]
for png_file in png_files:
    src = os.path.join(current_dir, png_file)
    dst = os.path.join(output_dir, png_file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  - {png_file}")

# 复制.env.example
env_src = os.path.join(current_dir, ".env.example")
env_dst = os.path.join(output_dir, ".env.example")
if os.path.exists(env_src):
    shutil.copy2(env_src, env_dst)
    print(f"  - .env.example")

# 复制recordings目录
recordings_src = os.path.join(current_dir, "recordings")
recordings_dst = os.path.join(output_dir, "recordings")
if os.path.exists(recordings_src):
    if os.path.exists(recordings_dst):
        shutil.rmtree(recordings_dst)
    shutil.copytree(recordings_src, recordings_dst)
    print(f"  - recordings/ 目录")

print(f"\n打包完成！")
print(f"输出目录: {output_dir}")
print(f"启动程序: {os.path.join(output_dir, 'PC-action-家用电脑.exe')}")
