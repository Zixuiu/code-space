"""
PC-action应用程序打包脚本
用于将Python项目打包成exe可执行文件
"""

import os
import sys
import subprocess
from pathlib import Path

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在检查PyInstaller...")
    try:
        import PyInstaller
        print("PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller安装完成")

def run_build():
    """执行打包命令"""
    print("开始打包PC-action应用程序...")
    
    # 获取项目路径
    project_dir = Path(__file__).parent
    spec_file = project_dir / "resent" / "PC-action.spec"
    
    if not spec_file.exists():
        print(f"错误: 找不到spec文件 {spec_file}")
        return False
    
    print(f"使用spec文件: {spec_file}")
    
    try:
        # 执行pyinstaller命令
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            str(spec_file)
        ], cwd=project_dir / "resent", check=True, capture_output=True, text=True)
        
        print("打包成功完成!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"打包过程中出现错误: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"打包过程中出现异常: {e}")
        return False

def copy_to_desktop():
    """将生成的exe文件复制到桌面"""
    project_dir = Path(__file__).parent
    exe_source = project_dir / "resent" / "dist" / "PC-action.exe"
    exe_dest = Path.home() / "Desktop" / "PC-action.exe"
    
    if exe_source.exists():
        try:
            import shutil
            # 确保桌面目录存在
            exe_dest.parent.mkdir(exist_ok=True)
            # 复制文件
            shutil.copy2(exe_source, exe_dest)
            print(f"已将可执行文件复制到桌面: {exe_dest}")
            return True
        except Exception as e:
            print(f"复制到桌面时出现错误: {e}")
            return False
    else:
        print(f"找不到可执行文件: {exe_source}")
        return False

def main():
    print("="*50)
    print("PC-action应用程序打包工具")
    print("="*50)
    
    # 安装PyInstaller
    install_pyinstaller()
    
    # 执行打包
    if run_build():
        print("\n" + "="*50)
        print("打包成功完成!")
        
        # 尝试复制到桌面
        copy_to_desktop()
        
        print("\n打包的文件位置:")
        print(f"  源文件: {Path(__file__).parent / 'resent' / 'dist' / 'PC-action.exe'}")
        print(f"  桌面副本: {Path.home() / 'Desktop' / 'PC-action.exe'}")
        print("="*50)
    else:
        print("\n打包失败，请检查错误信息。")

if __name__ == "__main__":
    main()