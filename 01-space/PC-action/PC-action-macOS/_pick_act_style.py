# -*- coding: utf-8 -*-
"""临时：激活弹窗 10 套「不同排版结构」方案 → 一张对比 PNG（选定后删除）"""
import sys

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QColor, QFont, QImage, QPainter
from PyQt5.QtWidgets import (
    QApplication, QFrame, QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QVBoxLayout, QWidget,
)

from beautiful_dialog import load_svg_icon, ICON_SCALE

OUT = r'C:\Users\stk_gb\AppData\Local\Temp\activation_10_styles.png'

INK, SUB, LINE, CHIP, BLUE, GREEN, RED = (
    "#111114", "#86868B", "#D1D1D6", "#F5F5F7", "#0A84FF", "#34C759", "#FF3B30")
W = 460


def lbl(text, size, color, bold=False, align=None, ls=0, wrap=True):
    l = QLabel(text)
    w = "700" if bold else "500"
    qss = (f"color:{color};font-size:{size}px;font-weight:{w};"
           'font-family:"Microsoft YaHei";background:transparent;border:none;')
    if ls:
        qss += f"letter-spacing:{ls}px;"
    l.setStyleSheet(qss)
    l.setWordWrap(wrap)
    if align is not None:
        l.setAlignment(align)
    return l


def dot():
    d = QLabel()
    d.setFixedSize(16, 16)
    d.setStyleSheet(f"background:{RED};border:none;border-radius:8px;")
    d.setAlignment(Qt.AlignCenter)
    return d


def icon_sq(size=40, radius=10, bg=CHIP, border=""):
    b = f"border:1px solid {border};" if border else "border:none;"
    w = QLabel()
    w.setFixedSize(size, size)
    w.setAlignment(Qt.AlignCenter)
    w.setStyleSheet(f"background:{bg};{b}border-radius:{radius}px;")
    pm = load_svg_icon("member", int(size * 0.5)).pixmap(
        int(round(size * 0.5 * ICON_SCALE)), int(round(size * 0.5 * ICON_SCALE)))
    w.setPixmap(pm)
    return w


def line_input(ph, qss):
    e = QLineEdit()
    e.setPlaceholderText(ph)
    e.setFixedHeight(42)
    e.setAlignment(Qt.AlignCenter if "AlignCenter" in qss else Qt.AlignLeft)
    e.setStyleSheet(qss)
    return e


def btn(text, qss):
    b = QPushButton(text)
    b.setFixedHeight(42)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(qss)
    return b


INK_BTN = ("QPushButton{{background:%s;color:#fff;border:none;border-radius:{r};"
           "font-size:15px;font-weight:700;min-height:0px;padding:0px;}}"
           "QPushButton:hover{{background:#2C2C31;}}" % INK)
BLUE_BTN = ("QPushButton{{background:%s;color:#fff;border:none;border-radius:{r};"
            "font-size:15px;font-weight:700;min-height:0px;padding:0px;}}"
            "QPushButton:hover{{background:#2A95FF;}}" % BLUE)
GREEN_BTN = ("QPushButton{{background:%s;color:#fff;border:none;border-radius:{r};"
             "font-size:15px;font-weight:700;min-height:0px;padding:0px;}}"
             "QPushButton:hover{{background:#2DB84F;}}" % GREEN)
ORANGE_BTN = ("QPushButton{{background:#FF9500;color:#fff;border:none;border-radius:{r};"
              "font-size:15px;font-weight:700;min-height:0px;padding:0px;}}"
              "QPushButton:hover{{background:#FFA526;}}")

STATUS_TXT = "当前为全功能访问（离线模式）"
ACCOUNT = "当前账户：tester"
TIP = "输入激活码开通 / 续费 VIP 会员（每码 1 个月起）"
PH = "请输入激活码，如 A1B2C3D4E5F6"
LINK = "没有激活码？去 PayPro 购买（¥9.9/30天）→"


def card(radius, bg="#FFFFFF", border=LINE):
    f = QFrame()
    f.setFixedWidth(W)
    f.setStyleSheet(f"QFrame{{background:{bg};border:1px solid {border};"
                    f"border-radius:{radius}px;}}")
    return f


# ── 1 · 居中英雄：全部居中，大圆角 22 ──
def v1():
    f = card(22)
    v = QVBoxLayout(f)
    v.setContentsMargins(28, 22, 28, 24)
    v.setSpacing(12)
    row = QHBoxLayout()
    row.addStretch()
    row.addWidget(dot())
    v.addLayout(row)
    icon = icon_sq(56, 16)
    icon.setAlignment(Qt.AlignCenter)
    v.addWidget(icon, 0, Qt.AlignHCenter)
    t = lbl("账户与激活", 19, "#1A1A2E", bold=True, align=Qt.AlignHCenter)
    v.addWidget(t)
    a = lbl(ACCOUNT, 12, SUB, align=Qt.AlignHCenter)
    v.addWidget(a)
    s = lbl("✓  " + STATUS_TXT, 14, "#248A3D", bold=True, align=Qt.AlignHCenter)
    s.setMinimumHeight(56)
    s.setStyleSheet(f"background:{CHIP};border-radius:14px;padding:8px 14px;")
    v.addWidget(s)
    v.addWidget(lbl(TIP, 11, SUB, align=Qt.AlignHCenter))
    v.addWidget(line_input(PH, (
        "QLineEdit{background:#FFFFFF;border:2px solid #E0E0E4;border-radius:14px;"
        "padding:0 14px;font-size:14px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-color:%s;}" % INK)))
    v.addWidget(btn("立即激活", INK_BTN.format(r=14)))
    l = lbl(f'<a href="#" style="color:{BLUE};text-decoration:none;">{LINK}</a>', 12, BLUE,
            align=Qt.AlignHCenter)
    l.setOpenExternalLinks(False)
    v.addWidget(l, 0, Qt.AlignHCenter)
    return f


# ── 2 · 浅灰横幅：头部横幅带 + 白色正文 ──
def v2():
    f = card(18)
    v = QVBoxLayout(f)
    v.setContentsMargins(0, 0, 0, 22)
    v.setSpacing(12)
    head = QFrame()
    head.setFixedHeight(58)
    head.setStyleSheet(f"QFrame{{background:{CHIP};border:none;"
                       "border-top-left-radius:17px;border-top-right-radius:17px;}")
    h = QHBoxLayout(head)
    h.setContentsMargins(20, 0, 16, 0)
    h.addWidget(icon_sq(36, 9, "#FFFFFF", LINE))
    h.addSpacing(10)
    h.addWidget(lbl("账户与激活", 17, "#1A1A2E", bold=True))
    h.addStretch()
    h.addWidget(dot())
    v.addWidget(head)
    body = QVBoxLayout()
    body.setContentsMargins(22, 4, 22, 0)
    body.setSpacing(12)
    body.addWidget(lbl(ACCOUNT, 12, SUB))
    st = lbl("✓  " + STATUS_TXT, 13, "#248A3D", bold=True)
    st.setMinimumHeight(48)
    st.setStyleSheet(f"background:rgba(52,199,89,0.10);border-radius:12px;padding:6px 14px;")
    body.addWidget(st)
    body.addWidget(line_input(PH, (
        "QLineEdit{background:#FFFFFF;border:2px solid #E0E0E4;border-radius:12px;"
        "padding:0 14px;font-size:14px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-color:%s;}" % BLUE)))
    body.addWidget(btn("立即激活", BLUE_BTN.format(r=12)))
    lk = lbl(f'<a href="#" style="color:{BLUE};text-decoration:none;">{LINK}</a>', 12, BLUE)
    lk.setOpenExternalLinks(False)
    body.addWidget(lk)
    v.addLayout(body)
    return f


# ── 3 · 圆徽章：大圆头像 + 无框状态 ──
def v3():
    f = card(24, border="#E5E5EA")
    v = QVBoxLayout(f)
    v.setContentsMargins(30, 26, 30, 24)
    v.setSpacing(10)
    row = QHBoxLayout()
    row.addStretch()
    row.addWidget(dot())
    v.addLayout(row)
    badge = QLabel()
    badge.setFixedSize(72, 72)
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(f"background:{CHIP};border:1px solid #E5E5EA;border-radius:36px;")
    pm = load_svg_icon("member", 34).pixmap(int(34 * ICON_SCALE), int(34 * ICON_SCALE))
    badge.setPixmap(pm)
    v.addWidget(badge, 0, Qt.AlignHCenter)
    v.addWidget(lbl("账户与激活", 19, "#1A1A2E", bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl(ACCOUNT, 12, SUB, align=Qt.AlignHCenter))
    v.addSpacing(4)
    st = QHBoxLayout()
    st.addStretch()
    st.addWidget(QLabel("●"), 0, Qt.AlignVCenter)
    st.addWidget(lbl("  " + STATUS_TXT, 14, "#1A1A2E", bold=True), 0, Qt.AlignVCenter)
    st.addStretch()
    v.addLayout(st)
    v.addSpacing(6)
    v.addWidget(line_input(PH, (
        "QLineEdit{background:%s;border:1px solid #E5E5EA;border-radius:16px;"
        "padding:0 16px;font-size:14px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}" % CHIP)))
    v.addWidget(btn("立即激活", INK_BTN.format(r=16)))
    l = lbl(f'<a href="#" style="color:{SUB};text-decoration:none;">{LINK}</a>', 11, SUB,
            align=Qt.AlignHCenter)
    l.setOpenExternalLinks(False)
    v.addWidget(l, 0, Qt.AlignHCenter)
    return f


# ── 4 · 状态英雄：大状态块为视觉中心 ──
def v4():
    f = card(18)
    v = QVBoxLayout(f)
    v.setContentsMargins(24, 20, 24, 24)
    v.setSpacing(12)
    row = QHBoxLayout()
    row.addWidget(lbl("账户与激活", 15, "#1A1A2E", bold=True))
    row.addStretch()
    row.addWidget(dot())
    v.addLayout(row)
    hero = lbl("✓\n" + STATUS_TXT, 17, "#248A3D", bold=True, align=Qt.AlignHCenter)
    hero.setMinimumHeight(96)
    hero.setStyleSheet(
        "background:rgba(52,199,89,0.10);border:1px solid rgba(52,199,89,0.35);"
        "border-radius:18px;padding:10px;")
    v.addWidget(hero)
    v.addWidget(lbl(ACCOUNT, 12, SUB))
    v.addWidget(lbl(TIP, 11, SUB))
    v.addWidget(line_input(PH, (
        "QLineEdit{background:#FFFFFF;border:2px solid #E0E0E4;border-radius:12px;"
        "padding:0 14px;font-size:14px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-color:#248A3D;}")))
    v.addWidget(btn("立即激活", GREEN_BTN.format(r=12)))
    lk = lbl(f'<a href="#" style="color:#248A3D;text-decoration:none;">{LINK}</a>', 11, "#248A3D")
    lk.setOpenExternalLinks(False)
    v.addWidget(lk)
    return f


# ── 5 · 双列：左身份 / 右操作 ──
def v5():
    f = card(18)
    v = QVBoxLayout(f)
    v.setContentsMargins(22, 20, 22, 22)
    v.setSpacing(14)
    top = QHBoxLayout()
    top.addWidget(lbl("账户与激活", 15, "#1A1A2E", bold=True))
    top.addStretch()
    top.addWidget(dot())
    v.addLayout(top)
    body = QHBoxLayout()
    body.setSpacing(18)
    left = QVBoxLayout()
    left.setSpacing(8)
    left.addWidget(icon_sq(52, 14), 0, Qt.AlignHCenter)
    left.addWidget(lbl("tester", 15, "#1A1A2E", bold=True, align=Qt.AlignHCenter))
    left.addWidget(lbl("未登录 · 可激活", 11, SUB, align=Qt.AlignHCenter))
    left.addStretch()
    body.addLayout(left, 5)
    ln = QFrame()
    ln.setFixedWidth(1)
    ln.setStyleSheet(f"background:{LINE};border:none;")
    body.addWidget(ln)
    right = QVBoxLayout()
    right.setSpacing(10)
    st = lbl("✓  " + STATUS_TXT, 12, "#248A3D", bold=True)
    st.setMinimumHeight(52)
    st.setWordWrap(True)
    st.setStyleSheet(f"background:{CHIP};border-radius:12px;padding:6px 12px;")
    right.addWidget(st)
    right.addWidget(line_input(PH, (
        "QLineEdit{background:#FFFFFF;border:2px solid #E0E0E4;border-radius:12px;"
        "padding:0 12px;font-size:13px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-color:%s;}" % INK)))
    right.addWidget(btn("立即激活", INK_BTN.format(r=12)))
    lk = lbl(f'<a href="#" style="color:{BLUE};text-decoration:none;">{LINK}</a>', 10, BLUE)
    lk.setWordWrap(True)
    lk.setOpenExternalLinks(False)
    right.addWidget(lk)
    body.addLayout(right, 9)
    v.addLayout(body)
    return f


# ── 6 · 嵌套面板：灰面板包住状态+输入 ──
def v6():
    f = card(18)
    v = QVBoxLayout(f)
    v.setContentsMargins(22, 20, 22, 22)
    v.setSpacing(12)
    row = QHBoxLayout()
    row.addWidget(icon_sq(36, 9))
    row.addSpacing(10)
    row.addWidget(lbl("账户与激活", 17, "#1A1A2E", bold=True))
    row.addStretch()
    row.addWidget(dot())
    v.addLayout(row)
    panel = QFrame()
    panel.setStyleSheet(f"QFrame{{background:{CHIP};border:none;border-radius:14px;}}")
    pv = QVBoxLayout(panel)
    pv.setContentsMargins(14, 14, 14, 14)
    pv.setSpacing(10)
    pv.addWidget(lbl(ACCOUNT, 11, SUB))
    pv.addWidget(lbl("✓  " + STATUS_TXT, 13, "#248A3D", bold=True))
    pv.addWidget(line_input(PH, (
        "QLineEdit{background:#FFFFFF;border:1px solid #E5E5EA;border-radius:10px;"
        "padding:0 12px;font-size:14px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-color:%s;}" % INK)))
    pv.addWidget(lbl(TIP, 10, SUB))
    v.addWidget(panel)
    v.addWidget(btn("立即激活", INK_BTN.format(r=12)))
    lk = lbl(f'<a href="#" style="color:{BLUE};text-decoration:none;">{LINK}</a>', 11, BLUE)
    lk.setOpenExternalLinks(False)
    v.addWidget(lk)
    return f


# ── 7 · 极简线：分隔线 + 描边按钮 ──
def v7():
    f = card(16, border="#E5E5EA")
    v = QVBoxLayout(f)
    v.setContentsMargins(26, 22, 26, 24)
    v.setSpacing(14)
    row = QHBoxLayout()
    row.addWidget(lbl("账户与激活", 15, "#1A1A2E", bold=True))
    row.addStretch()
    row.addWidget(dot())
    v.addLayout(row)
    ln = QFrame()
    ln.setFixedHeight(1)
    ln.setStyleSheet(f"background:#ECECEF;border:none;")
    v.addWidget(ln)
    v.addSpacing(2)
    v.addWidget(lbl("✓  " + STATUS_TXT, 15, "#248A3D", bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl(ACCOUNT, 11, SUB, align=Qt.AlignHCenter))
    v.addWidget(ln)
    u = line_input(PH, (
        "QLineEdit{background:transparent;border:none;border-bottom:2px solid #C7C7CC;"
        "border-radius:0px;padding:0 4px;font-size:14px;font-weight:600;"
        "letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-bottom-color:%s;}" % INK))
    v.addWidget(u)
    ob = btn("立即激活", (
        "QPushButton{background:#FFFFFF;color:%s;border:1.5px solid %s;border-radius:12px;"
        "font-size:15px;font-weight:700;min-height:0px;padding:0px;}"
        "QPushButton:hover{background:%s;color:#FFFFFF;}" % (INK, INK, INK)))
    v.addWidget(ob)
    lk = lbl(f'<a href="#" style="color:{SUB};text-decoration:none;">{LINK}</a>', 11, SUB,
             align=Qt.AlignHCenter)
    lk.setOpenExternalLinks(False)
    v.addWidget(lk, 0, Qt.AlignHCenter)
    return f


# ── 8 · 绿色确认：绿徽章 + 绿按钮 ──
def v8():
    f = card(20)
    v = QVBoxLayout(f)
    v.setContentsMargins(28, 24, 28, 24)
    v.setSpacing(12)
    row = QHBoxLayout()
    row.addStretch()
    row.addWidget(dot())
    v.addLayout(row)
    badge = QLabel("✓")
    badge.setFixedSize(60, 60)
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(
        "background:rgba(52,199,89,0.12);border:none;border-radius:30px;"
        "font-size:26px;font-weight:700;color:#248A3D;")
    v.addWidget(badge, 0, Qt.AlignHCenter)
    v.addWidget(lbl("账户与激活", 18, "#1A1A2E", bold=True, align=Qt.AlignHCenter))
    chip = lbl(STATUS_TXT, 12, "#248A3D", bold=True, align=Qt.AlignHCenter)
    chip.setMinimumHeight(40)
    chip.setStyleSheet("background:rgba(52,199,89,0.10);border-radius:20px;padding:4px 16px;")
    v.addWidget(chip, 0, Qt.AlignHCenter)
    v.addWidget(lbl(ACCOUNT, 11, SUB, align=Qt.AlignHCenter))
    v.addWidget(line_input(PH, (
        "QLineEdit{background:#FFFFFF;border:2px solid rgba(52,199,89,0.45);border-radius:12px;"
        "padding:0 14px;font-size:14px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-color:%s;}" % GREEN)))
    v.addWidget(btn("立即激活", GREEN_BTN.format(r=12)))
    lk = lbl(f'<a href="#" style="color:#248A3D;text-decoration:none;">{LINK}</a>', 11, "#248A3D",
             align=Qt.AlignHCenter)
    lk.setOpenExternalLinks(False)
    v.addWidget(lk, 0, Qt.AlignHCenter)
    return f


# ── 9 · 深色头部：墨黑横幅 + 白正文 + 蓝按钮 ──
def v9():
    f = card(18)
    v = QVBoxLayout(f)
    v.setContentsMargins(0, 0, 0, 22)
    v.setSpacing(12)
    head = QFrame()
    head.setFixedHeight(64)
    head.setStyleSheet("QFrame{background:#1E1F24;border:none;"
                       "border-top-left-radius:17px;border-top-right-radius:17px;}")
    h = QHBoxLayout(head)
    h.setContentsMargins(22, 0, 16, 0)
    h.addWidget(lbl("账户与激活", 17, "#F2F2F7", bold=True))
    h.addStretch()
    h.addWidget(dot())
    v.addWidget(head)
    body = QVBoxLayout()
    body.setContentsMargins(22, 6, 22, 0)
    body.setSpacing(12)
    body.addWidget(lbl(ACCOUNT, 12, SUB))
    st = lbl("✓  " + STATUS_TXT, 13, "#248A3D", bold=True)
    st.setMinimumHeight(48)
    st.setStyleSheet("background:rgba(52,199,89,0.10);border-radius:12px;padding:6px 14px;")
    body.addWidget(st)
    body.addWidget(line_input(PH, (
        "QLineEdit{background:#FFFFFF;border:2px solid #E0E0E4;border-radius:12px;"
        "padding:0 14px;font-size:14px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-color:%s;}" % BLUE)))
    body.addWidget(btn("立即激活", BLUE_BTN.format(r=12)))
    lk = lbl(f'<a href="#" style="color:{BLUE};text-decoration:none;">{LINK}</a>', 12, BLUE)
    lk.setOpenExternalLinks(False)
    body.addWidget(lk)
    v.addLayout(body)
    return f


# ── 10 · 分步引导：步骤条 + 表单 ──
def v10():
    f = card(18)
    v = QVBoxLayout(f)
    v.setContentsMargins(24, 20, 24, 24)
    v.setSpacing(14)
    row = QHBoxLayout()
    row.addWidget(lbl("账户与激活", 15, "#1A1A2E", bold=True))
    row.addStretch()
    row.addWidget(dot())
    v.addLayout(row)
    steps = QHBoxLayout()
    steps.setSpacing(8)
    for i, s in enumerate(("输入激活码", "立即激活", "解锁全部")):
        n = QLabel(str(i + 1))
        n.setFixedSize(22, 22)
        n.setAlignment(Qt.AlignCenter)
        n.setStyleSheet(f"background:{INK};color:#FFFFFF;border:none;border-radius:11px;"
                        'font-size:12px;font-weight:700;font-family:"Microsoft YaHei";')
        steps.addWidget(n)
        steps.addWidget(lbl(s, 12, "#1A1A2E" if i == 0 else SUB, bold=(i == 0)))
        if i < 2:
            steps.addWidget(lbl("→", 12, SUB))
        steps.addStretch()
    v.addLayout(steps)
    st = lbl("✓  " + STATUS_TXT, 13, "#248A3D", bold=True)
    st.setMinimumHeight(48)
    st.setStyleSheet(f"background:{CHIP};border-radius:12px;padding:6px 14px;")
    v.addWidget(st)
    v.addWidget(lbl(ACCOUNT, 11, SUB))
    v.addWidget(line_input(PH, (
        "QLineEdit{background:#FFFFFF;border:2px solid #E0E0E4;border-radius:12px;"
        "padding:0 14px;font-size:14px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}"
        "QLineEdit:focus{border-color:%s;}" % ORANGE_BTN.split("background:")[1][:7])))
    v.addWidget(btn("立即激活", ORANGE_BTN.format(r=12)))
    lk = lbl(f'<a href="#" style="color:#E07C00;text-decoration:none;">{LINK}</a>', 11, "#E07C00")
    lk.setOpenExternalLinks(False)
    v.addWidget(lk)
    return f


VARIANTS = [
    ("1 · 居中英雄", v1), ("2 · 浅灰横幅", v2), ("3 · 圆徽章", v3),
    ("4 · 状态英雄", v4), ("5 · 双列", v5), ("6 · 嵌套面板", v6),
    ("7 · 极简线", v7), ("8 · 绿色确认", v8), ("9 · 深色头部", v9),
    ("10 · 分步引导", v10),
]


def main():
    app = QApplication(sys.argv)
    shots = []
    for name, fn in VARIANTS:
        w = fn()
        w.show()
        for _ in range(16):
            app.processEvents()
            QThread.msleep(12)
        shots.append((name, w.grab()))
        w.close()
        app.processEvents()

    PAD, LABEL_H, GAP = 28, 52, 26
    cw = max(p.width() for _, p in shots) + PAD * 2
    ch = max(p.height() for _, p in shots) + PAD + LABEL_H
    cols, rows = 2, 5
    Wd, H = cols * cw + (cols + 1) * GAP, rows * ch + (rows + 1) * GAP
    img = QImage(Wd, H, QImage.Format_RGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(img.rect(), QColor("#B8B8BE"))
    fnt = QFont("Microsoft YaHei")
    fnt.setPixelSize(22)
    fnt.setBold(True)
    p.setFont(fnt)
    for k, (name, pix) in enumerate(shots):
        r, c = divmod(k, cols)
        x = GAP + c * (cw + GAP)
        y = GAP + r * (ch + GAP)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(x + 4, y + 6, cw - 8, LABEL_H - 12, Qt.AlignVCenter | Qt.AlignLeft, name)
        px = x + (cw - pix.width()) // 2
        py = y + LABEL_H + (ch - LABEL_H - pix.height()) // 2
        p.drawPixmap(px, py, pix)
    p.end()
    img.save(OUT)
    print("GRID OK ->", OUT)
    app.quit()


if __name__ == "__main__":
    main()
