# -*- coding: utf-8 -*-
"""
临时校验脚本：启动安装向导，逐页抓取界面文本，
确认中文没有乱码、默认安装路径正确。验证完即删除。
"""
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)

WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
WM_CLOSE = 0x0010
BM_CLICK = 0x00F5

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


EM_GETTEXTEX = 0x045E          # WM_USER + 94


class GETTEXTEX(ctypes.Structure):
    _fields_ = [('cb', ctypes.c_uint32),
                ('flags', ctypes.c_uint32),
                ('codepage', ctypes.c_uint),
                ('lpDefaultChar', ctypes.c_void_p),
                ('lpUsedDefChar', ctypes.c_void_p)]


def rich_edit_text(h):
    """RichEdit 的 WM_GETTEXT 会被截断，改用 EM_GETTEXTEX 取全文（UTF-16LE）。"""
    buf = ctypes.create_unicode_buffer(200000)
    gt = GETTEXTEX(ctypes.sizeof(buf), 0, 1200, None, None)
    got = user32.SendMessageW(h, EM_GETTEXTEX, ctypes.byref(gt), buf)
    if got:
        return buf.value
    return None


def win_text(h):
    n = user32.SendMessageW(h, WM_GETTEXTLENGTH, 0, 0)
    n = int(n)
    if n <= 0:
        return ''
    buf = ctypes.create_unicode_buffer(n + 2)
    user32.SendMessageW(h, WM_GETTEXT, n + 1, buf)
    return buf.value


def class_name(h):
    b = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(h, b, 256)
    return b.value


def find_main(pid):
    found = []

    def cb(h, l):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(h):
            t = win_text(h)
            if t:
                found.append((h, class_name(h), t))
        return True

    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found


def dump_children(hwnd):
    items = []

    def cb(h, l):
        cn = class_name(h)
        if cn in ('Static', 'Button', 'Edit', 'RichEdit20W', 'RichEdit20A', 'SysLink'):
            txt = win_text(h)
            if txt.strip():
                # 许可协议正文在 RichEdit 里，截断会看不到价格条款，故对 RichEdit 不截断
                limit = 100000 if cn.startswith('RichEdit') else 220
                items.append((cn, txt.replace('\r', '').replace('\n', ' ⏎ ')[:limit]))
        return True

    user32.EnumChildWindows(hwnd, EnumChildWindowsProc(cb), 0)
    return items


def click_button(hwnd, keywords):
    """keywords: 依次尝试的按钮文字关键词，返回实际点击的按钮文字"""
    buttons = []

    def cb(h, l):
        if class_name(h) == 'Button':
            buttons.append((h, win_text(h)))
        return True

    user32.EnumChildWindows(hwnd, EnumChildWindowsProc(cb), 0)
    for kw in keywords:
        for h, t in buttons:
            if kw in t:
                user32.SendMessageW(h, BM_CLICK, 0, 0)
                return t
    return ''


def main():
    setup = sys.argv[1]
    out = []
    p = subprocess.Popen([setup])
    time.sleep(3.5)
    wins = find_main(p.pid)
    out.append('=== 窗口列表 ===')
    for h, cn, t in wins:
        out.append(f'[{cn}] {t}')

    # (页面名, 用于进入下一页的按钮关键词)
    pages = [
        ('欢迎页', ['下一步']),
        ('许可协议页', ['我接受', '我同意', '下一步']),
        ('选择安装位置页', ['下一步']),
        ('附加选项页', ['安装', '下一步']),
    ]
    for i, (name, kws) in enumerate(pages):
        wins = find_main(p.pid)
        if not wins:
            out.append(f'--- {name}: 未找到窗口')
            break
        hwnd = wins[0][0]
        out.append(f'--- {name} (标题: {wins[0][2]}) ---')
        for cn, txt in dump_children(hwnd):
            out.append(f'  <{cn}> {txt}')
        if i < len(pages) - 1:
            clicked = click_button(hwnd, kws)
            out.append(f'  [点击按钮: "{clicked}"]')
            time.sleep(2.0)

    time.sleep(0.5)
    subprocess.run(['taskkill', '/PID', str(p.pid), '/F'],
                   capture_output=True)
    open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(out))
    print('written', sys.argv[2])


if __name__ == '__main__':
    main()
