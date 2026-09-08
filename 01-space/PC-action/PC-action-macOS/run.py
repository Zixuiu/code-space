"""
PC-action 启动脚本 (Windows)
自动设置 Qt 插件路径，避免 "no Qt platform plugin" 错误。
用法: python run.py
"""
import os
import sys


def _is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return True  # 检测失败时保守按"已管理员"处理，不阻塞启动


def _ensure_admin():
    """
    默认以管理员身份运行：非管理员时自动弹一次 UAC 提权重启自己。
    可设环境变量 PC_ACTION_NO_ELEVATE=1 跳过提权（用于免打扰/自动化后台启动）。
    """
    if os.environ.get('PC_ACTION_NO_ELEVATE') == '1':
        return
    if sys.platform != 'win32':
        return
    if _is_admin():
        return
    import subprocess
    _exe = sys.executable
    _script = os.path.abspath(__file__)
    _cwd = os.getcwd()
    _esc = lambda s: str(s).replace("'", "''")
    _extra = ' '.join('"' + str(a) + '"' for a in sys.argv[1:])
    _ps = (
        "Start-Process -FilePath '{exe}' -ArgumentList '\"{script}\" {extra}' "
        "-WorkingDirectory '{cwd}' -Verb RunAs"
    ).format(exe=_esc(_exe), script=_esc(_script), extra=_extra, cwd=_esc(_cwd))
    try:
        subprocess.Popen(
            ['powershell', '-NoProfile', '-Command', _ps],
            cwd=_cwd, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    except Exception:
        # 提权被取消/失败：降到普通权限继续运行，不把程序"弄没"
        try:
            sys.stderr.write("[PC-action] 请求管理员权限失败，将以普通权限运行\n")
        except Exception:
            pass
        return
    sys.exit(0)  # 交给提权后的新进程继续，本进程退出

# 确保 Qt 能找到平台插件（qwindows.dll）
import PyQt5
_plugin = os.path.join(PyQt5.__path__[0], 'Qt5', 'plugins')
os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', _plugin)
os.environ.setdefault('QT_PLUGIN_PATH', _plugin)

# DPI 感知
if sys.platform == 'win32':
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# 桌面运行/崩溃日志：Action运行日志.txt（未捕获异常、Qt 事件异常、atexit 都会落盘）
try:
    from crash_logger import install_crash_logger
    install_crash_logger()
except Exception:
    pass

from app_macos import start_macos_app

if __name__ == '__main__':
    _ensure_admin()
    start_macos_app()
