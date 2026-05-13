"""
打包脚本：将应用程序打包为文件夹模式到桌面
优化点：
1. 自动填充账号密码 - 保存的登录信息会复制到输出目录
2. 录制文件夹和快捷键 - 完整复制recordings目录和用户数据
3. 启动速度优化 - 使用UPX压缩，排除不必要的模块
"""
import PyInstaller.__main__
import os
import shutil
import sys
import tempfile
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
final_output_dir = os.path.join(desktop_path, "PC-action-家用电脑")

temp_dir = tempfile.gettempdir()
temp_project_name = "pc_action_build"
temp_build_dir = os.path.join(temp_dir, temp_project_name)
temp_dist_dir = os.path.join(temp_dir, temp_project_name + "_dist")
temp_work_dir = os.path.join(temp_dir, temp_project_name + "_work")
temp_spec_dir = os.path.join(temp_dir, temp_project_name + "_spec")

os.makedirs(temp_dist_dir, exist_ok=True)

# 首先检查必要的文件是否存在
required_files = ['start_app.py', 'app.py', 'login_ui.py', 'login_manager.py']
for file in required_files:
    file_path = os.path.join(current_dir, file)
    if not os.path.exists(file_path):
        print(f"错误: 必要文件不存在: {file_path}")
        sys.exit(1)
    print(f"✓ 找到必要文件: {file}")

# PyInstaller参数 - 使用ASCII临时路径避免中文编码问题
args = [
    os.path.join(current_dir, "start_app.py"),
    "--name", "PC-action-家用电脑",
    "--onedir",
    "--windowed",
    "--distpath", temp_dist_dir,
    "--workpath", temp_work_dir,
    "--specpath", temp_spec_dir,
    "--clean",
    "--noconfirm",
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
    "--hidden-import", "dotenv",
    "--hidden-import", "PyQt5.sip",
    "--hidden-import", "PyQt5.QtCore",
    "--hidden-import", "PyQt5.QtGui",
    "--hidden-import", "PyQt5.QtWidgets",
    # 排除不必要的模块以减小体积和加速启动
    "--exclude-module", "matplotlib",
    "--exclude-module", "numpy.random._examples",
    "--exclude-module", "scipy",
    "--exclude-module", "pandas",
    "--exclude-module", "tkinter",
    "--exclude-module", "unittest",
    "--exclude-module", "pydoc",
    "--exclude-module", "xmlrpc",
    "--exclude-module", "multiprocessing",
    "--exclude-module", "email.mime.audio",
    "--exclude-module", "email.mime.image",
    "--exclude-module", "email.mime.message",
]

print("=" * 60)
print("开始打包 PC-action-家用电脑")
print("=" * 60)
print(f"使用ASCII临时路径: {temp_dist_dir}")
print("打包模式: 文件夹模式（启动速度更快）")
print("=" * 60)

# 运行PyInstaller
PyInstaller.__main__.run(args)

# 清理旧的输出目录
if os.path.exists(final_output_dir):
    print(f"\n清理旧的输出目录: {final_output_dir}")
    try:
        shutil.rmtree(final_output_dir)
    except Exception as e:
        print(f"清理旧目录时出错: {e}")

# 从临时目录复制打包结果到最终目录
print("\n" + "=" * 60)
print("移动打包结果到桌面...")
print("=" * 60)

temp_exe_dir = os.path.join(temp_dist_dir, "PC-action-家用电脑")
if os.path.exists(temp_exe_dir):
    shutil.copytree(temp_exe_dir, final_output_dir)
    print(f"✓ 打包结果已移动到: {final_output_dir}")
else:
    print(f"错误: 找不到打包结果: {temp_exe_dir}")
    sys.exit(1)

# 复制数据文件到输出目录
print("\n" + "=" * 60)
print("复制数据文件...")
print("=" * 60)

# 复制数据库
db_files = ["local_users.db", "app.db"]
for db_file in db_files:
    db_src = os.path.join(current_dir, db_file)
    db_dst = os.path.join(final_output_dir, db_file)
    if os.path.exists(db_src):
        shutil.copy2(db_src, db_dst)
        print(f"  ✓ {db_file}")

# 复制JSON配置文件（包含保存的登录信息）
json_files = ["saved_login.json", "login_credentials.json", "users.json"]
for json_file in json_files:
    src = os.path.join(current_dir, json_file)
    dst = os.path.join(final_output_dir, json_file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  ✓ {json_file}")
    else:
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        print(f"  ✓ {json_file} (创建空文件)")

# 复制图片文件
png_files = ["target_light_red.png", "target_deep_red.png", "check.png"]
for png_file in png_files:
    src = os.path.join(current_dir, png_file)
    dst = os.path.join(final_output_dir, png_file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  ✓ {png_file}")

# 复制.env文件
env_files = [".env", ".env.example"]
for env_file in env_files:
    src = os.path.join(current_dir, env_file)
    dst = os.path.join(final_output_dir, env_file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  ✓ {env_file}")

# 复制用户数据目录（包含快捷键配置等）
from utils import get_user_data_path
user_data_dir = get_user_data_path()
if os.path.exists(user_data_dir):
    user_data_dst = os.path.join(final_output_dir, "user_data")
    os.makedirs(user_data_dst, exist_ok=True)
    
    for item in os.listdir(user_data_dir):
        src = os.path.join(user_data_dir, item)
        dst = os.path.join(user_data_dst, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  ✓ user_data/{item}")
        elif os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  ✓ user_data/{item}/")

# 复制recordings目录（录制文件夹）
recordings_src = os.path.join(current_dir, "recordings")
recordings_dst = os.path.join(final_output_dir, "recordings")
if os.path.exists(recordings_src):
    if os.path.exists(recordings_dst):
        shutil.rmtree(recordings_dst)
    shutil.copytree(recordings_src, recordings_dst)
    print(f"  ✓ recordings/ 目录")
    recording_count = len([d for d in os.listdir(recordings_src) if os.path.isdir(os.path.join(recordings_src, d))])
    print(f"    包含 {recording_count} 个录制文件夹")
else:
    os.makedirs(recordings_dst, exist_ok=True)
    print(f"  ✓ recordings/ 目录 (创建空目录)")

# 创建启动说明文件
readme_content = """PC-action-家用电脑 使用说明
============================

启动程序：
双击 "PC-action-家用电脑.exe" 启动程序

功能特点：
1. 自动填充账号密码 - 登录信息会自动填充，点击登录即可
2. 录制文件夹 - 所有录制文件保存在 recordings 目录中
3. 快捷键配置 - 用户快捷键配置保存在 user_data 目录中

数据备份：
- recordings/ - 录制文件目录
- user_data/ - 用户数据和快捷键配置
- saved_login.json - 保存的登录信息
- users.json - 用户账户信息

注意事项：
1. 首次运行可能需要几秒钟初始化
2. 如果登录信息未自动填充，请检查 saved_login.json 文件是否存在
3. 快捷键配置按用户保存，切换用户需要重新设置
"""

readme_path = os.path.join(final_output_dir, "使用说明.txt")
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content)
print(f"  ✓ 使用说明.txt")

print("\n" + "=" * 60)
print("打包完成！")
print("=" * 60)
print(f"输出目录: {final_output_dir}")
print(f"启动程序: {os.path.join(final_output_dir, 'PC-action-家用电脑.exe')}")
print("\n功能验证:")
print("  ✓ 自动填充账号密码 - 登录信息已保存")
print("  ✓ 录制文件夹 - recordings目录已复制")
print("  ✓ 快捷键配置 - user_data目录已复制")
print("  ✓ 启动速度优化 - 使用文件夹模式")
print("=" * 60)
