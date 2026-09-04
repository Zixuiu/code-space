"""
按键捕获增强模块

背景：Alt+Tab / Alt+Shift+Tab 是 Windows 的系统级窗口切换热键，Qt 窗口收不到
（系统在 shell 层就把事件吞掉了），所以在「记录按键」的对话框里按 Alt+Tab 时
要么没反应，要么直接把窗口切走、录制流程被打断。

本模块提供两块能力：
  1. install_alt_tab_capture(callback)  —— 安装 WH_KEYBOARD_LL 低级键盘钩子，
     在对话框存活期间拦截 Alt+Tab（不会被系统切走），识别为 "alt+tab" /
     "alt+shift+tab" 并回调给调用方。
  2. send_alt_tab()                     —— 用底层 keybd_event 可靠地真正执行一次
     Alt+Tab（用于录制时执行、以及回放时执行，比 pyautogui.hotkey 稳）。

只在 Windows 上生效；非 Windows 环境的接口调用全部安全降级（返回 False）。
"""

import os
import sys
import time

IS_WINDOWS = (os.name == 'nt') or (sys.platform.startswith('win'))

# ── Win32 常量 ────────────────────────────────────────────────────────────────
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

VK_SHIFT = 0x10
VK_MENU = 0x12       # Alt
VK_TAB = 0x09

LLKHF_ALTDOWN = 0x0020   # KBDLLHOOKSTRUCT.flags：Alt 处于按下状态
KEYEVENTF_KEYUP = 0x0002

# ── 模块级状态 ────────────────────────────────────────────────────────────────
_user32 = None
_hook_handle = None
_hook_proc_ref = None      # 必须持有引用，否则被 GC 后钩子回调直接崩
_alt_tab_callback = None
_alt_down = False
_install_depth = 0         # 支持嵌套安装（多个对话框）

if IS_WINDOWS:
    try:
        import ctypes
        from ctypes import wintypes, CFUNCTYPE, POINTER

        # use_last_error=True：失败时能拿到真实的 GetLastError，方便排障
        _user32 = ctypes.WinDLL('user32', use_last_error=True)
        _kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

        class _KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_ulonglong),
            ]

        _HOOKPROC = CFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

        _user32.SetWindowsHookExW.argtypes = [ctypes.c_int, _HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        _user32.SetWindowsHookExW.restype = wintypes.HHOOK
        _user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        _user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        _user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        _user32.CallNextHookEx.restype = ctypes.c_longlong
        _user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        _user32.GetAsyncKeyState.restype = ctypes.c_short
        _user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p]
        _user32.keybd_event.restype = None
        # ★ 必须显式声明 restype：不声明时 ctypes 默认按 c_int 返回，
        #   64 位进程里 HMODULE 会被截断成 32 位，SetWindowsHookExW 直接失败
        _kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        _kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    except Exception:
        _user32 = None


# ── Alt+Tab 识别 ──────────────────────────────────────────────────────────────
def normalize_key(key_str):
    """把 'ALT + Tab' 这类写法归一成 'alt+tab'"""
    if not key_str:
        return ''
    return '+'.join(p.strip().lower() for p in str(key_str).split('+') if p.strip())


def is_alt_tab_key(key_str):
    """判断某个 key 字符串是否是 Alt+Tab 系列（alt+tab / alt+shift+tab）"""
    return normalize_key(key_str) in ('alt+tab', 'alt+shift+tab', 'shift+alt+tab')


# ── 低级键盘钩子 ──────────────────────────────────────────────────────────────
def _fire_callback_async(key_str):
    """钩子回调里不要做重活：丢到 Qt 事件循环的下一个 tick 再执行，避免阻塞钩子"""
    cb = _alt_tab_callback
    if cb is None:
        return
    try:
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: _safe_call(cb, key_str))
    except Exception:
        _safe_call(cb, key_str)


def _safe_call(cb, key_str):
    try:
        cb(key_str)
    except Exception:
        pass


def _hook_callback(nCode, wParam, lParam):
    """WH_KEYBOARD_LL 回调：拦下 Alt+Tab，其余按键原样放行"""
    global _alt_down
    try:
        if nCode >= 0:
            kb = ctypes.cast(lParam, POINTER(_KBDLLHOOKSTRUCT)).contents
            vk = kb.vkCode
            is_down = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)
            is_up = wParam in (WM_KEYUP, WM_SYSKEYUP)

            if vk in (VK_MENU, 0xA4, 0xA5):      # Alt / LAlt / RAlt
                _alt_down = is_down

            # Alt+Tab：flags 里带 LLKHF_ALTDOWN 最可靠，_alt_down 作为兜底
            # 按下/抬起都要吞掉，否则系统只收到 Tab 的 up，切换器状态会错乱
            if vk == VK_TAB and (kb.flags & LLKHF_ALTDOWN or _alt_down):
                if is_down:
                    shift_down = False
                    try:
                        shift_down = bool(_user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
                    except Exception:
                        pass
                    _fire_callback_async('alt+shift+tab' if shift_down else 'alt+tab')
                return 1        # 吞掉事件：不让系统真的切走窗口
    except Exception:
        pass
    try:
        return _user32.CallNextHookEx(_hook_handle, nCode, wParam, lParam)
    except Exception:
        return 0


def install_alt_tab_capture(callback):
    """
    安装 Alt+Tab 捕获钩子（可重入，内部计数）。

    callback(key_str) 会在 Qt 主线程被异步调用，key_str ∈ {'alt+tab', 'alt+shift+tab'}。
    返回 True 表示钩子安装成功（非 Windows 或失败时返回 False）。
    """
    global _hook_handle, _hook_proc_ref, _alt_tab_callback, _install_depth

    if not IS_WINDOWS or _user32 is None:
        return False

    _install_depth += 1
    _alt_tab_callback = callback
    if _hook_handle is not None:
        return True                      # 已安装，只换回调

    try:
        _hook_proc_ref = _HOOKPROC(_hook_callback)
        # WH_KEYBOARD_LL 是全局钩子，hMod 传 NULL 即可（不需要模块句柄）
        _hook_handle = _user32.SetWindowsHookExW(WH_KEYBOARD_LL, _hook_proc_ref, None, 0)
        if not _hook_handle:
            print(f"[key_capture] SetWindowsHookExW 返回 NULL，last_error={ctypes.get_last_error()}")
            _hook_handle = None
            _hook_proc_ref = None
            return False
        return True
    except Exception as _e:
        import traceback
        traceback.print_exc()
        print(f"[key_capture] Alt+Tab 钩子安装失败: {_e}")
        _hook_handle = None
        _hook_proc_ref = None
        return False


def uninstall_alt_tab_capture(force=False):
    """卸载钩子；嵌套安装时只有最后一层才真正卸载"""
    global _hook_handle, _hook_proc_ref, _alt_tab_callback, _install_depth, _alt_down

    _install_depth = max(0, _install_depth - 1)
    if _install_depth > 0 and not force:
        return

    _alt_tab_callback = None
    _alt_down = False
    if _hook_handle is not None:
        try:
            _user32.UnhookWindowsHookEx(_hook_handle)
        except Exception:
            pass
    _hook_handle = None
    _hook_proc_ref = None
    _install_depth = 0


def is_capture_installed():
    return _hook_handle is not None


# ── 真正执行一次 Alt+Tab（录制时执行 / 回放时执行）────────────────────────────
def send_alt_tab(shift=False, pre_hold=0.15, post_hold=0.15):
    """
    用 keybd_event 发送 Alt(+Shift)+Tab。

    流程：Alt 按下 → (Shift 按下) → 停顿 → Tab 按下 → 停顿 → Tab 抬起 → 停顿 → 抬起 Shift/Alt。
    停顿很关键：Alt 按下后系统需要时间弹出切换器（实测 0.06s 太快，会整个被忽略），
    松开 Alt 才是"提交切换"的时机。
    """
    if not IS_WINDOWS or _user32 is None:
        return False
    try:
        _user32.keybd_event(VK_MENU, 0, 0, None)                 # Alt down
        if shift:
            _user32.keybd_event(VK_SHIFT, 0, 0, None)           # Shift down
        time.sleep(pre_hold)                                     # 等切换器弹出来

        _user32.keybd_event(VK_TAB, 0, 0, None)                  # Tab down
        time.sleep(0.05)
        _user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, None)    # Tab up
        time.sleep(post_hold)

        if shift:
            _user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, None)
        time.sleep(0.02)
        _user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, None)   # Alt up（提交切换）
        return True
    except Exception:
        return False


def send_key_combo(key_str):
    """
    通用按键执行：Alt+Tab 系列走底层可靠实现，其余交给 pyautogui。
    返回 True 表示已执行。
    """
    import pyautogui
    if is_alt_tab_key(key_str):
        shift = 'shift' in normalize_key(key_str).split('+')
        return send_alt_tab(shift=shift)
    try:
        parts = [p.strip().lower() for p in str(key_str).split('+') if p.strip()]
        if not parts:
            return False
        if len(parts) == 1:
            pyautogui.press(parts[0])
        else:
            pyautogui.hotkey(*parts)
        return True
    except Exception:
        return False
