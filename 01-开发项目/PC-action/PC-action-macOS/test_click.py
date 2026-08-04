# -*- coding: utf-8 -*-
"""
双击诊断脚本 — 固定在流程最后一步坐标 (327, 421) 测试不同双击方法
用法:
  1. 打开目标应用，定位到双击前的状态
  2. python test_click.py
  3. 按数字键 1-8 测试不同方法, 观察目标应用是否产生跳转/响应
  4. 按 q 退出
"""
import ctypes
import sys
import time
from ctypes import wintypes

user32 = ctypes.windll.user32

# ★★★ 关键：声明 DPI Awareness，让进程使用物理坐标（否则 GetCursorPos 返回逻辑坐标，点击位置偏移）
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    _DPI_MODE = "PER_MONITOR_AWARE_V2"
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        _DPI_MODE = "PER_MONITOR_AWARE"
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            _DPI_MODE = "SYSTEM_AWARE"
        except Exception:
            _DPI_MODE = "UNAWARE (DPI虚拟化，坐标会偏移!)"

# ---- 常量 ----
MOUSEEVENTF_LEFTDOWN  = 0x0002
MOUSEEVENTF_LEFTUP    = 0x0004
MOUSEEVENTF_ABSOLUTE  = 0x8000
INPUT_MOUSE           = 0
WM_LBUTTONDOWN        = 0x0201
WM_LBUTTONUP          = 0x0202
WM_LBUTTONDBLCLK      = 0x0203
WPARAM_MK_LBUTTON     = 0x0001

# ---- SendInput 结构体 ----
class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG), ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_void_p),
    ]

class _INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", _MOUSEINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
user32.SendInput.restype  = wintypes.UINT

# ---- 辅助函数 ----
def get_screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def get_window_at(x, y):
    """获取屏幕坐标 (x,y) 处的顶层窗口"""
    pt = wintypes.POINT(x, y)
    hwnd = user32.WindowFromPoint(pt)
    root = user32.GetAncestor(hwnd, 2)  # GA_ROOT = 2
    if root:
        hwnd = root
    return hwnd

def get_window_title(hwnd):
    if not hwnd:
        return "(无)"
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value or "(无标题)"

def get_window_pid(hwnd):
    if not hwnd:
        return 0
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def make_lparam(x, y):
    return (y << 16) | (x & 0xFFFF)

def _bring_to_front(hwnd):
    """把窗口激活到前台（用 AttachThreadInput 绕过 SetForegroundWindow 限制）"""
    if not hwnd:
        return False
    fg = user32.GetForegroundWindow()
    if fg == hwnd:
        return True
    tid_fg = user32.GetWindowThreadProcessId(fg, None)
    tid_target = user32.GetWindowThreadProcessId(hwnd, None)
    attached = False
    if tid_fg and tid_target and tid_fg != tid_target:
        if user32.AttachThreadInput(tid_fg, tid_target, True):
            attached = True
    try:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        result = user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(tid_fg, tid_target, False)
    return bool(result)

# ---- 测试方法 ----
def method1_mouse_event_relative(x, y):
    """方法1: SetCursorPos + mouse_event 相对点击"""
    user32.SetCursorPos(x, y)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def method2_absolute(x, y):
    """方法2: MOUSEEVENTF_ABSOLUTE 绝对坐标"""
    sw, sh = get_screen_size()
    ax = int(x * 65536 / sw) if sw > 0 else 0
    ay = int(y * 65536 / sh) if sh > 0 else 0
    user32.mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTDOWN, ax, ay, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTUP, ax, ay, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTDOWN, ax, ay, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTUP, ax, ay, 0, 0)

def method3_sendinput(x, y):
    """方法3: SendInput 绝对坐标"""
    sw, sh = get_screen_size()
    ax = int(x * 65536 / sw) if sw > 0 else 0
    ay = int(y * 65536 / sh) if sh > 0 else 0
    def _send(flags):
        inp = _INPUT()
        inp.type = INPUT_MOUSE
        inp.mi.dx = ax
        inp.mi.dy = ay
        inp.mi.dwFlags = flags | MOUSEEVENTF_ABSOLUTE
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))
    _send(MOUSEEVENTF_LEFTDOWN)
    time.sleep(0.01)
    _send(MOUSEEVENTF_LEFTUP)
    time.sleep(0.05)
    _send(MOUSEEVENTF_LEFTDOWN)
    time.sleep(0.01)
    _send(MOUSEEVENTF_LEFTUP)

def method4_pyautogui_double(x, y):
    """方法4: pyautogui.doubleClick"""
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    pyautogui.doubleClick(x, y)

def method5_pyautogui_clicks(x, y):
    """方法5: pyautogui.click 两次（带间隔）"""
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    pyautogui.click(x, y)
    time.sleep(0.1)
    pyautogui.click(x, y)

def method6_postmessage(x, y, hwnd):
    """方法6: PostMessage 直接向窗口发送双击消息（不移动鼠标）"""
    lp = make_lparam(x, y)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, WPARAM_MK_LBUTTON, lp)
    time.sleep(0.01)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, WPARAM_MK_LBUTTON, lp)
    time.sleep(0.01)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(0.01)
    user32.PostMessageW(hwnd, WM_LBUTTONDBLCLK, WPARAM_MK_LBUTTON, lp)

def method7_postmessage_child(x, y):
    """方法7: PostMessage 发送到 (x,y) 处的子窗口（精确控件）"""
    pt = wintypes.POINT(x, y)
    hwnd = user32.WindowFromPoint(pt)
    if not hwnd:
        print("  [错误] 找不到窗口")
        return
    client_pt = wintypes.POINT(x, y)
    user32.ScreenToClient(hwnd, ctypes.byref(client_pt))
    lp = make_lparam(client_pt.x, client_pt.y)
    print(f"  目标子窗口 hwnd={hwnd}, 客户区坐标=({client_pt.x},{client_pt.y})")
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, WPARAM_MK_LBUTTON, lp)
    time.sleep(0.01)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, WPARAM_MK_LBUTTON, lp)
    time.sleep(0.01)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(0.01)
    user32.PostMessageW(hwnd, WM_LBUTTONDBLCLK, WPARAM_MK_LBUTTON, lp)

def method8_activate_and_click(x, y, hwnd):
    """方法8: ★激活窗口到前台 + 移动鼠标 + hover + 双击（最接近手动操作）"""
    if hwnd:
        ok = _bring_to_front(hwnd)
        print(f"  激活窗口 hwnd={hwnd} 结果={ok}")
        time.sleep(0.15)  # 等待窗口前置完成
    # 移动鼠标到目标位置
    user32.SetCursorPos(x, y)
    time.sleep(0.15)  # hover 停留，让 UI 响应
    # 双击
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.05)  # 双击间隔
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# ---- 主程序 ----
if __name__ == '__main__':
    # ★ 固定测试坐标：流程_20260804_200155_319 最后一步双击位置
    TARGET_X, TARGET_Y = 327, 421

    sw, sh = get_screen_size()
    print("=" * 64)
    print("           双击诊断脚本 (已启用 DPI Awareness)")
    print("=" * 64)
    print(f"  DPI 模式   : {_DPI_MODE}")
    print(f"  屏幕分辨率 : {sw} x {sh}  (GetSystemMetrics)")
    try:
        dpi = user32.GetDpiForSystem()
        print(f"  系统 DPI   : {dpi} ({dpi/96*100:.0f}%)")
    except Exception:
        print("  系统 DPI   : N/A")
    print(f"  管理员权限 : {'是' if is_admin() else '否（可能无法操作高权限窗口）'}")
    print(f"  目标坐标   : ({TARGET_X}, {TARGET_Y})  ← 流程最后一步双击位置")
    print()
    print("  测试方法:")
    print("    1 - mouse_event 相对点击")
    print("    2 - MOUSEEVENTF_ABSOLUTE 绝对坐标")
    print("    3 - SendInput 绝对坐标")
    print("    4 - pyautogui.doubleClick")
    print("    5 - pyautogui.click x2")
    print("    6 - PostMessage 发送到顶层窗口")
    print("    7 - PostMessage 发送到子窗口（精确控件）")
    print("    8 - ★激活窗口+移动+hover+双击 (最接近手动操作)")
    print("    q - 退出")
    print()
    print("  >> 请先打开目标应用并定位到双击前的状态，再按数字键测试 <<")
    print("  >> 重点测试方法 8 <<")
    print("=" * 64)

    import keyboard

    while True:
        # 显示当前目标坐标处所属窗口信息
        hwnd_at = get_window_at(TARGET_X, TARGET_Y)
        title = get_window_title(hwnd_at)
        pid = get_window_pid(hwnd_at)
        print(f"\r  目标({TARGET_X},{TARGET_Y}) | 窗口: {title[:30]:<30s} PID={pid}   ", end='', flush=True)

        key = keyboard.read_key()
        time.sleep(0.15)  # 去抖

        if key == 'q':
            print("\n退出。")
            break
        elif key in ('1', '2', '3', '4', '5', '6', '7', '8'):
            x, y = TARGET_X, TARGET_Y
            hwnd = get_window_at(x, y)
            title = get_window_title(hwnd)
            print(f"\n  >>> 方法 {key} @ ({x},{y}) 窗口='{title}' <<<")
            try:
                if key == '1':
                    method1_mouse_event_relative(x, y)
                elif key == '2':
                    method2_absolute(x, y)
                elif key == '3':
                    method3_sendinput(x, y)
                elif key == '4':
                    method4_pyautogui_double(x, y)
                elif key == '5':
                    method5_pyautogui_clicks(x, y)
                elif key == '6':
                    method6_postmessage(x, y, hwnd)
                elif key == '7':
                    method7_postmessage_child(x, y)
                elif key == '8':
                    method8_activate_and_click(x, y, hwnd)
                print(f"  >>> 方法 {key} 执行完成，请观察目标应用是否响应 <<<")
            except Exception as e:
                print(f"  >>> 方法 {key} 执行失败: {e} <<<")
            time.sleep(0.5)
