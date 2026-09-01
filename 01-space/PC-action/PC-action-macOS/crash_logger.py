# -*- coding: utf-8 -*-
"""
桌面运行日志 / 崩溃诊断模块

问题背景：
    PC-action 打包成 exe 后没有控制台，运行一段时间"卡退退出"时，
    stdout/stderr、traceback.print_exc() 以及 Qt 事件处理器(timer/slot)里
    抛出的异常都会无声消失，无法定位原因。

做法：
    每次启动 PC-action（通过 start_macos_app 调用 install_crash_logger）：
      1. 把 stdout / stderr 同时镜像写入桌面 txt（带时间戳）。
      2. 接管 sys.excepthook / threading.excepthook / sys.unraisablehook，
         未捕获异常完整 traceback 写入 txt。
      3. 用一个 QApplication 子类重写 notify()，捕获 Qt 事件处理器里被
         Qt 吞掉的异常（这是"卡退"最常见的原因之一）。
      4. 接管 Qt C++ 消息（qInstallMessageHandler），把 WARN/CRITICAL/FATAL
         级消息（如跨线程 startTimer、对象已销毁等）写入 txt。
      5. 额外把 pc_action logger 的日志也桥接到桌面 txt，提供运行上下文。

日志文件：桌面 / PC-Action运行日志.txt（每次启动覆盖重写，仅保留本次会话）。
"""
import os
import sys
import io
import time
import faulthandler
import traceback
import threading
import atexit

_LOG_FILE = None
_LOG_LOCK = threading.Lock()
_INSTALLED = False
_LOG_PATH = None

import re as _re
# logging 通过 _LogBridge 已经把记录写进桌面日志；console_handler 把同样的
# 格式化行输出到 stderr，会被 _Tee 再镜像一遍造成重复。用这个正则识别并跳过。
_LOG_LINE_RE = _re.compile(
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL)\]'
)


# --------------------------------------------------------------------------
# 路径
# --------------------------------------------------------------------------
def _get_desktop_path():
    """取得当前用户桌面目录，失败回退到 ~/Desktop 或用户主目录。"""
    try:
        import ctypes
        from ctypes import wintypes
        shell32 = ctypes.windll.shell32
        SHGFP_TYPE_CURRENT = 0
        CSIDL_DESKTOPDIRECTORY = 0x10
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        shell32.SHGetFolderPathW.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
            ctypes.c_int, ctypes.c_wchar_p
        ]
        shell32.SHGetFolderPathW.restype = ctypes.c_int
        if shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None,
                                    SHGFP_TYPE_CURRENT, buf) == 0:
            p = buf.value
            if p and os.path.isdir(p):
                return p
    except Exception:
        pass
    try:
        p = os.path.join(os.path.expanduser('~'), 'Desktop')
        if os.path.isdir(p):
            return p
    except Exception:
        pass
    return os.path.expanduser('~')


def _open_log_file():
    """打开桌面日志文件（每次启动覆盖重写），返回路径。"""
    global _LOG_FILE, _LOG_PATH
    desktop = _get_desktop_path()
    path = os.path.join(desktop, 'PC-Action运行日志.txt')
    # 每次启动重新写入：用 'w' 覆盖打开，旧日志清空。
    # 用默认块缓冲即可：_write 每次写完都会 flush()，崩溃也不丢最后一行。
    _LOG_FILE = open(path, 'w', encoding='utf-8')
    _LOG_PATH = path
    return path


# --------------------------------------------------------------------------
# 写入
# --------------------------------------------------------------------------
def _write(text):
    if _LOG_FILE is None:
        return
    try:
        with _LOG_LOCK:
            _LOG_FILE.write(text)
            _LOG_FILE.flush()
    except Exception:
        pass


def _now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


# --------------------------------------------------------------------------
# stdout / stderr 镜像
# --------------------------------------------------------------------------
class _Tee(io.TextIOBase):
    """把写入内容同时落到原 stdout/stderr 和桌面日志文件。"""

    def __init__(self, prefix, original):
        self._prefix = prefix
        self._original = original
        self._buf = ''

    @property
    def encoding(self):
        return 'utf-8'

    @property
    def errors(self):
        return 'replace'

    def write(self, data):
        # 1) 原输出（开发期控制台可见）
        try:
            if self._original is not None:
                self._original.write(data)
                self._original.flush()
        except Exception:
            pass
        # 2) 按行镜像到日志文件，加时间戳前缀
        self._buf += data
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            # stderr 中来自 logging 的已通过 _LogBridge 写入日志，跳过避免重复
            if self._prefix == '[ERR]' and _LOG_LINE_RE.match(line):
                continue
            _write(f"{_now()} {self._prefix} {line}\n")
        return len(data)

    def flush(self):
        if self._buf:
            if not (self._prefix == '[ERR]' and _LOG_LINE_RE.match(self._buf)):
                _write(f"{_now()} {self._prefix} {self._buf}\n")
            self._buf = ''
        try:
            if self._original is not None:
                self._original.flush()
        except Exception:
            pass

    def isatty(self):
        return False

    def writable(self):
        return True


# --------------------------------------------------------------------------
# 异常钩子
# --------------------------------------------------------------------------
def _excepthook(exc_type, exc_value, exc_tb):
    banner = ("\n" + "=" * 64 + "\n"
              "!!! 未捕获异常 (sys.excepthook) !!!\n"
              f"时间: {_now()}\n"
              + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
              + "=" * 64 + "\n")
    _write(banner)
    try:
        sys.__stderr__.write(banner)
    except Exception:
        pass


def _threading_excepthook(args):
    banner = ("\n" + "=" * 64 + "\n"
              "!!! 线程未捕获异常 (threading.excepthook) !!!\n"
              f"线程: {getattr(args, 'thread', None)}\n"
              + "".join(traceback.format_exception(
                  args.exc_type, args.exc_value, args.exc_traceback))
              + "=" * 64 + "\n")
    _write(banner)


def _unraisablehook(unraisable):
    banner = ("\n" + "=" * 64 + "\n"
              "!!! 无法抛出的异常 (unraisable) !!!\n"
              f"对象: {getattr(unraisable, 'object', None)}\n"
              f"{getattr(unraisable, 'err_msg', '')}\n"
              + "".join(traceback.format_exception(
                  unraisable.exc_type, unraisable.exc_value,
                  unraisable.exc_traceback))
              + "=" * 64 + "\n")
    _write(banner)


# --------------------------------------------------------------------------
# Qt 消息 & 事件异常捕获
# --------------------------------------------------------------------------
def _install_qt_message_handler():
    try:
        from PyQt5.QtCore import qInstallMessageHandler, QtMsgType
    except Exception:
        return

    _type_map = {
        QtMsgType.QtDebugMsg: 'DEBUG',
        QtMsgType.QtInfoMsg: 'INFO',
        QtMsgType.QtWarningMsg: 'WARN',
        QtMsgType.QtCriticalMsg: 'CRITICAL',
        QtMsgType.QtFatalMsg: 'FATAL',
    }

    def _handler(msg_type, context, message):
        level = _type_map.get(msg_type, 'UNKNOWN')
        # 只记录 WARN/CRITICAL/FATAL，过滤 Qt 常规 INFO/DEBUG 噪声
        if level in ('WARN', 'CRITICAL', 'FATAL'):
            loc = ''
            if context is not None:
                loc = f"  [{context.file}:{context.line} {context.function}]"
            _write(f"{_now()} [Qt {level}] {message}{loc}\n")

    qInstallMessageHandler(_handler)


def make_application(*args, **kwargs):
    """创建带异常捕获的 QApplication 子类实例。

    notify() 重写后，Qt 事件处理器（slot / QTimer 回调 / 事件过滤器）里
    抛出的异常会被捕获并写入桌面日志，而不是被 Qt 静默吞掉。
    """
    from PyQt5.QtWidgets import QApplication

    class _CrashAwareApp(QApplication):
        def notify(self, receiver, event):
            try:
                return super().notify(receiver, event)
            except Exception:
                tb = traceback.format_exc()
                _write(
                    "\n" + "=" * 64 + "\n"
                    "!!! Qt 事件处理器异常 (notify) !!!\n"
                    f"时间: {_now()}\n"
                    f"接收者: {receiver}\n事件: {event}\n"
                    + tb + "=" * 64 + "\n"
                )
                return False

    return _CrashAwareApp(*args, **kwargs)


# --------------------------------------------------------------------------
# logging 桥接（把 pc_action logger 的日志也写入桌面 txt）
# --------------------------------------------------------------------------
class _LogBridge(io.TextIOBase):
    def write(self, data):
        _write(data)
        return len(data)

    def flush(self):
        pass

    def writable(self):
        return True


def _install_logging_bridge():
    try:
        import logging
        logger = logging.getLogger('pc_action')
        logger.propagate = False
        # 移除已有的「控制台型」handler（utils.py 给 pc_action 挂的 StreamHandler
        # 指向 sys.stderr，会被 _Tee 再镜像一次，造成桌面日志里 [INFO] 行被 [ERR]
        # 重复写一遍）。保留 FileHandler（写应用日志文件），只留本 bridge 一行输出。
        for h in list(logger.handlers):
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler):
                if not isinstance(getattr(h, 'stream', None), _LogBridge):
                    logger.removeHandler(h)
        handler = logging.StreamHandler(_LogBridge())
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
    except Exception:
        pass


# --------------------------------------------------------------------------
# 退出记录
# --------------------------------------------------------------------------
def _on_exit():
    _write(f"\n{_now()} [INFO] 程序退出 (atexit 触发)\n")
    try:
        if _LOG_FILE is not None:
            _LOG_FILE.flush()
            _LOG_FILE.close()
    except Exception:
        pass


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def install_crash_logger():
    """在程序最早期调用：打开桌面日志文件并安装全部钩子。"""
    global _INSTALLED, _LOG_FILE, _LOG_PATH
    if _INSTALLED:
        return
    _INSTALLED = True

    # 1) 打开日志文件（桌面不可用则回退到 user_data）
    try:
        path = _open_log_file()
    except Exception:
        try:
            from utils import get_user_data_path
            path = os.path.join(get_user_data_path(), 'PC-Action运行日志.txt')
            _LOG_FILE = open(path, 'w', encoding='utf-8')
            _LOG_PATH = path
        except Exception:
            _LOG_FILE = None
            return

    # 2) 启动 faulthandler（段错误 / C 扩展崩溃也能把 traceback 写进日志）
    try:
        if _LOG_FILE is not None:
            faulthandler.enable(_LOG_FILE)
    except Exception:
        pass

    # 3) 启动会话横幅
    try:
        import ctypes
        try:
            admin = (ctypes.windll.shell32.IsUserAnAdmin() != 0)
        except Exception:
            admin = '?'
    except Exception:
        admin = '?'

    banner = (
        "========== PC-action 启动 ==========\n"
        f"时间: {_now()}\n"
        f"Python: {sys.version.split()[0]}  模式: "
        f"{'打包exe' if getattr(sys, 'frozen', False) else '开发'}\n"
        f"PID: {os.getpid()}\n"
        f"管理员: {admin}\n"
        f"日志文件: {_LOG_PATH}\n"
        "=====================================\n"
    )
    _write(banner)

    # 3) 镜像 stdout / stderr
    if not isinstance(sys.stdout, _Tee):
        sys.stdout = _Tee('[OUT]', sys.stdout)
    if not isinstance(sys.stderr, _Tee):
        sys.stderr = _Tee('[ERR]', sys.stderr)

    # 4) 异常钩子
    sys.excepthook = _excepthook
    try:
        sys.unraisablehook = _unraisablehook
    except Exception:
        pass
    try:
        threading.excepthook = _threading_excepthook
    except Exception:
        pass

    # 5) Qt 消息 + 事件异常
    _install_qt_message_handler()
    _install_logging_bridge()

    # 6) 退出记录
    atexit.register(_on_exit)


if __name__ == '__main__':
    install_crash_logger()
    print("crash_logger 自测：这条会同时出现在控制台和桌面日志里")
    raise RuntimeError("自测未捕获异常（应被写入桌面日志）")
