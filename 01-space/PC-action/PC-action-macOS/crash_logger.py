# -*- coding: utf-8 -*-
"""
运行日志 / 崩溃诊断模块

问题背景：
    PC-action 打包成 exe 后没有控制台，运行一段时间"卡退退出"时，
    stdout/stderr、traceback.print_exc() 以及 Qt 事件处理器(timer/slot)里
    抛出的异常都会无声消失，无法定位原因。

做法：
    每次启动 PC-action（通过 start_macos_app 调用 install_crash_logger）：
      1. 把 stdout / stderr 同时镜像写入日志 txt（带时间戳）。
      2. 接管 sys.excepthook / threading.excepthook / sys.unraisablehook，
         未捕获异常完整 traceback 写入 txt。
      3. 用一个 QApplication 子类重写 notify()，捕获 Qt 事件处理器里被
         Qt 吞掉的异常（这是"卡退"最常见的原因之一）。
      4. 接管 Qt C++ 消息（qInstallMessageHandler），把 WARN/CRITICAL/FATAL
         级消息（如跨线程 startTimer、对象已销毁等）写入 txt。
      5. 额外把 pc_action logger 的日志也桥接到 txt，提供运行上下文。

日志文件：应用目录的上级文件夹 / Action运行日志.txt
        （每次启动覆盖重写，仅保留本次会话；桌面不再生成，可用环境变量
          PC_ACTION_LOG_DIR 覆盖目录）
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
# logging 通过 _LogBridge 已经把记录写进日志文件；console_handler 把同样的
# 格式化行输出到 stderr，会被 _Tee 再镜像一遍造成重复。用这个正则识别并跳过。
_LOG_LINE_RE = _re.compile(
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL)\]'
)


# --------------------------------------------------------------------------
# 路径
# --------------------------------------------------------------------------
def _app_base_dir():
    """应用所在目录：打包后 = exe 所在目录；开发环境 = 本文件所在目录。"""
    try:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(os.path.abspath(sys.executable))
    except Exception:
        pass
    return os.path.dirname(os.path.abspath(__file__))


def _is_writable(d):
    try:
        os.makedirs(d, exist_ok=True)
        t = os.path.join(d, '.~action_log_write_test')
        with open(t, 'w', encoding='utf-8') as f:
            f.write('')
        os.remove(t)
        return True
    except Exception:
        return False


def _is_drive_root(p):
    """是否盘符根目录（D:\\ / C:\\ ...），根目录不能当日志目录"""
    try:
        drive, tail = os.path.splitdrive(os.path.abspath(p))
        return bool(drive) and tail in ('\\', '/', '')
    except Exception:
        return False


def get_log_dir():
    """日志目录：默认写在**应用目录的上级文件夹**里（不再写桌面）。

    优先级：环境变量 PC_ACTION_LOG_DIR → 应用目录的上级 → 应用目录本身 → user_data。
    - 上级是盘符根目录（如安装版 exe 在 D:\\PC-Action，上级是 D:\\）时跳过上级，
      否则日志会撒到盘根。
    - 统一做可写探测，避免装到 Program Files 之类只读位置时静默失败。
    """
    cands = []
    env_dir = os.environ.get('PC_ACTION_LOG_DIR')
    if env_dir:
        cands.append(env_dir)
    base = os.path.normpath(_app_base_dir())
    parent = os.path.dirname(base)
    if parent and os.path.normcase(parent) != os.path.normcase(base) \
            and not _is_drive_root(parent):
        cands.append(parent)
    cands.append(base)
    try:
        from utils import get_user_data_path
        cands.append(get_user_data_path())
    except Exception:
        pass
    for d in cands:
        if d and _is_writable(d):
            return d
    return cands[0] if cands else os.getcwd()


def _open_log_file():
    """打开运行日志文件（每次启动覆盖重写），返回路径。"""
    global _LOG_FILE, _LOG_PATH
    log_dir = get_log_dir()
    path = os.path.join(log_dir, 'Action运行日志.txt')
    # 每次启动重新写入：用 'w' 覆盖打开，旧日志清空。
    # 用默认块缓冲即可：_write 每次写完都会 flush()，崩溃也不丢最后一行。
    _LOG_FILE = open(path, 'w', encoding='utf-8')
    _LOG_PATH = path
    return path


def _get_desktop_dir():
    """桌面目录（仅用于清理历史遗留的桌面日志）"""
    try:
        import ctypes
        from ctypes import wintypes
        shell32 = ctypes.windll.shell32
        CSIDL_DESKTOPDIRECTORY = 0x10
        SHGFP_TYPE_CURRENT = 0
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
    return None


def _looks_like_action_log(path):
    """指纹校验：确认是本程序写的日志（首部有启动横幅），避免误删同名文件"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            head = f.read(400)
        return ('启动' in head) and ('Action' in head or 'action' in head) \
            and ('PID:' in head or '管理员' in head)
    except Exception:
        return False


def _send_to_recycle_bin(path):
    """把文件移入回收站（可恢复）。失败返回 False——不做永久删除兜底。"""
    try:
        import ctypes
        from ctypes import wintypes

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [
                ('hwnd', wintypes.HWND),
                ('wFunc', wintypes.UINT),
                ('pFrom', ctypes.c_wchar_p),
                ('pTo', ctypes.c_wchar_p),
                ('fFlags', ctypes.c_uint16),
                ('fAnyOperationsAborted', wintypes.BOOL),
                ('hNameMappings', ctypes.c_void_p),
                ('lpszProgressTitle', ctypes.c_wchar_p),
            ]

        FO_DELETE = 3
        FOF_SILENT = 0x0004
        FOF_NOCONFIRMATION = 0x0010
        FOF_ALLOWUNDO = 0x0040          # 关键：进回收站而不是永久删除
        FOF_NOERRORUI = 0x0400

        op = SHFILEOPSTRUCTW()
        op.hwnd = None
        op.wFunc = FO_DELETE
        op.pFrom = str(path) + '\0\0'   # 必须双 null 结尾
        op.pTo = None
        op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
        res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        # 桌面这种 shell 特殊目录有时返回非 0 但文件已被移走，这里以实际结果为准
        return res == 0 or not os.path.exists(path)
    except Exception:
        return False


# 历史版本用过的桌面日志名（都要清掉）
_LEGACY_LOG_NAMES = ('Action运行日志.txt', 'PC-Action运行日志.txt')


def cleanup_legacy_desktop_log(log_dir):
    """启动时清理历史遗留的桌面日志（老版本写在桌面，现已改到上级文件夹）。

    只处理「同名 + 带本程序指纹」的文件，且只移入回收站（可恢复），
    不做永久删除；任何异常都静默跳过。返回被清理的路径列表。
    """
    moved = []
    try:
        desk = _get_desktop_dir()
        if not desk:
            return moved
        if os.path.normcase(os.path.normpath(desk)) == \
                os.path.normcase(os.path.normpath(log_dir or '')):
            return moved   # 日志本来就写在桌面，别动它
        for name in _LEGACY_LOG_NAMES:
            old = os.path.join(desk, name)
            if not os.path.isfile(old) or not _looks_like_action_log(old):
                continue
            if _send_to_recycle_bin(old):
                moved.append(old)
    except Exception:
        return moved
    return moved


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
    """把写入内容同时落到原 stdout/stderr 和日志文件。"""

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
    抛出的异常会被捕获并写入日志文件，而不是被 Qt 静默吞掉。
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
# logging 桥接（把 pc_action logger 的日志也写入日志 txt）
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
        # 指向 sys.stderr，会被 _Tee 再镜像一次，造成日志里 [INFO] 行被 [ERR]
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
    """在程序最早期调用：打开运行日志文件并安装全部钩子。"""
    global _INSTALLED, _LOG_FILE, _LOG_PATH
    if _INSTALLED:
        return
    _INSTALLED = True

    # 1) 打开日志文件（上级文件夹 → 应用目录 → user_data 逐级兜底）
    try:
        path = _open_log_file()
    except Exception:
        try:
            from utils import get_user_data_path
            path = os.path.join(get_user_data_path(), 'Action运行日志.txt')
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
        "========== Action 启动 ==========\n"
        f"时间: {_now()}\n"
        f"Python: {sys.version.split()[0]}  模式: "
        f"{'打包exe' if getattr(sys, 'frozen', False) else '开发'}\n"
        f"PID: {os.getpid()}\n"
        f"管理员: {admin}\n"
        f"日志文件: {_LOG_PATH}\n"
        "=====================================\n"
    )
    _write(banner)

    # 3.5) 清理历史遗留的桌面日志：老版本把日志写在桌面，改成"应用目录的上级
    #      文件夹"后，桌面那份残留会让人误以为还在往桌面写。这里把它移入回收站
    #      （可恢复，只认同名 + 带启动横幅指纹的文件）。
    try:
        _legacy = cleanup_legacy_desktop_log(os.path.dirname(_LOG_PATH) if _LOG_PATH else '')
        for _p in (_legacy or []):
            _write(f"{_now()} [INFO] 已清理桌面的历史日志（进回收站，可恢复）: {_p}\n")
    except Exception:
        pass

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
    print("crash_logger 自测：这条会同时出现在控制台和日志文件里")
    raise RuntimeError("自测未捕获异常（应被写入日志文件）")
