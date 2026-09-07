# -*- coding: utf-8 -*-
"""
使用帮助 · 翻页流大重构 v3 —— 60 个独立设计页面
================================================
10 套设计语言 × 每套 6 页 = 60 个互不相同的页面布局。
几何全部来自共享令牌；卡片 700×460 = 真实内容区 ÷1.36。
运行：python help_pager_preview.py
"""
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QFrame, QScrollArea, QGridLayout, QSizePolicy,
)

U = 8
GAP_XS, GAP_S, GAP_M, GAP_L, GAP_XL = 4, 8, 16, 24, 40
CARD_W, CARD_H = 700, 460
PAD = 40
FONT = '"Microsoft YaHei", "Segoe UI Emoji", sans-serif'
N = 6

STEPS = [
    dict(icon="⚖️", title="同样的活，两种干法",
         ask="左边是现在，右边是用了 PC-action 之后",
         old=["5 个软件挨个点 ≈ 5 分钟", "复制粘贴填日报 ≈ 3 分钟",
              "账号密码逐个输 ≈ 2 分钟", "菜单导出归档 ≈ 5 分钟"],
         new=["一条流程 ≈ 10 秒", "自动生成发送 ≈ 5 秒",
              "自动登录 ≈ 3 秒", "自动导出 ≈ 8 秒"],
         pain="每天省下约 47 分钟", point="不是你变快了，是你不用再干了。"),
    dict(icon="🎬", title="录一遍，以后不用再干",
         ask="录制时只有 4 个指令，记住就会用",
         keys=[("左键", "框选 = 单击"), ("右键", "框选 = 右击"),
               ("K", "模拟按键"), ("T", "输入文本")],
         pain="按 ESC 结束录制，流程自动保存",
         point="就这 4 个指令 + ESC，你已经都会了。"),
    dict(icon="🔧", title="看它替你干活",
         ask="点一下回放，它开始「模仿」你",
         chips=["自动打开软件", "自动输入文字", "自动点击按钮", "自动完成所有操作"],
         pain="而你只需要 —— 喝杯咖啡，看着它干 ☕",
         point="这种感觉，试过一次就回不去了。"),
    dict(icon="✏️", title="不怕录错，改就完了",
         ask="录错了也不用重新来",
         edits=[("改按键", "按错了？改成对的"), ("改文字", "输错了？直接改掉"),
                ("调顺序", "拖拽调整步骤"), ("删多余", "点 × 删除")],
         pain="找到那一步，直接修改",
         point="修改后自动保存，再回放就是完美版本。"),
    dict(icon="⚙️", title="让电脑 7×24 替你工作",
         ask="组合技：多个流程串起来，一次跑完",
         pipe=[("A", "打开日报系统 → 导出数据"), ("B", "打开邮箱 → 发送晨报"),
               ("C", "打开看板 → 刷新 → 截图")],
         pain="每天早上点一下，它自己全部搞定",
         point="你只需要坐下来，喝口热水，开始真正的工作。"),
    dict(icon="🎉", title="不再做重复劳动的奴隶",
         ask="从今天起，你学会了",
         dones=["录一次", "无限回放", "随意修改", "组合串联"],
         pain="把省下来的时间，留给更重要的事",
         point="把重复的事交给电脑，把时间留给自己。"),
]


def lbl(text, size, color, bold=False, ls=0, align=None, wrap=True, family=FONT, lh=None):
    l = QLabel(text)
    w = 700 if bold else 500
    qss = (f"color:{color};font-size:{size}px;font-weight:{w};font-family:{family};"
           f"background:transparent;border:none;")
    if ls:
        qss += f"letter-spacing:{ls}px;"
    if lh:
        qss += f"line-height:{lh}px;"
    l.setStyleSheet(qss)
    l.setWordWrap(wrap)
    if align is not None:
        l.setAlignment(align)
    return l


def frame(bg="", border="", radius=0, size=None, dash=False):
    f = QFrame()
    qss = "QFrame {"
    if bg:
        qss += f"background:{bg};"
    if border:
        style = "1px dashed" if dash else "1px solid"
        qss += f"border:{style} {border};"
    else:
        qss += "border:none;"
    if radius:
        qss += f"border-radius:{radius}px;"
    qss += "}"
    f.setStyleSheet(qss)
    if size:
        f.setFixedSize(*size)
    return f


def stretch(v=0):
    s = QWidget()
    s.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding if v else QSizePolicy.Minimum)
    return s


def page_std(L, i, inner=None):
    """标准页：大边距 + 页眉（kicker / 页码）"""
    pg = QWidget()
    pg.setStyleSheet("background:transparent;border:none;")
    v = QVBoxLayout(pg)
    v.setContentsMargins(PAD, GAP_M, PAD, GAP_M)
    v.setSpacing(GAP_M)
    head = QHBoxLayout()
    head.addWidget(lbl(f"{L['kicker']} · {i + 1:02d}", L["micro"], L["sub"], bold=True, ls=3))
    head.addStretch()
    head.addWidget(lbl(f"{i + 1} — {N}", L["micro"], L["sub"], bold=True))
    v.addLayout(head)
    if inner:
        v.addWidget(inner, 1)
    return pg


def page_bare(L, widget):
    pg = QWidget()
    pg.setStyleSheet("background:transparent;border:none;")
    v = QVBoxLayout(pg)
    v.setContentsMargins(0, 0, 0, 0)
    v.addWidget(widget)
    return pg


# ═══════════════════════ 套 1 · 白境画廊 ═══════════════════════
def p101(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    v.addWidget(lbl("同样的活", 46, L["fg"], bold=True))
    row = QHBoxLayout()
    row.addWidget(lbl("两种干法", 46, L["fg"], bold=True))
    row.addStretch()
    row.addWidget(lbl(s["ask"], L["cap"], L["sub"]), 0, Qt.AlignBottom)
    v.addLayout(row)
    v.addStretch()
    rule = frame(border=L["line"])
    rule.setFixedHeight(1)
    v.addWidget(rule)
    foot = QHBoxLayout()
    foot.addWidget(lbl("以前：5 分钟 × 4 项", L["body"], L["sub"]))
    foot.addStretch()
    foot.addWidget(lbl("现在：10 秒 × 1 次", L["body"], L["accent"], bold=True))
    v.addLayout(foot)
    return page_std(L, i, w)


def p102(L, s, i):
    """页2 · 巨大数字 4 + 右侧键名列表"""
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(GAP_L)
    num = lbl("4", 150, L["fg"], bold=True)
    h.addWidget(num, 5, Qt.AlignVCenter)
    col = QVBoxLayout()
    col.setSpacing(GAP_S)
    col.addStretch()
    col.addWidget(lbl("个指令，全教会你", L["cap"], L["sub"], ls=2))
    col.addSpacing(GAP_XS)
    for key, desc in s["keys"]:
        row = QHBoxLayout()
        row.addWidget(lbl(key, L["body"], L["fg"], bold=True))
        row.addStretch()
        row.addWidget(lbl(desc, L["cap"], L["sub"]))
        col.addLayout(row)
    col.addStretch()
    h.addLayout(col, 7)
    return page_std(L, i, w)


def p103(L, s, i):
    """页3 · 巨型播放键"""
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    v.addWidget(lbl("▶", 120, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl("点回放，它替你干", 30, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addSpacing(GAP_XS)
    row = QHBoxLayout()
    row.setSpacing(GAP_L)
    row.addStretch()
    for c in s["chips"]:
        row.addWidget(lbl(c, L["micro"], L["sub"], bold=True))
    row.addStretch()
    v.addLayout(row)
    v.addStretch()
    return page_std(L, i, w)


def p104(L, s, i):
    """页4 · ✗ → ✓ 四格修订"""
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addStretch()
    grid = QGridLayout()
    grid.setSpacing(GAP_M)
    for k, (name, desc) in enumerate(s["edits"]):
        tile = frame("#FFFFFF", L["line"], 0)
        tv = QVBoxLayout(tile)
        tv.setContentsMargins(GAP_M, GAP_M, GAP_M, GAP_M)
        tv.setSpacing(GAP_XS)
        head = QHBoxLayout()
        head.addWidget(lbl("✗", L["body"], L["sub"], bold=True))
        head.addStretch()
        head.addWidget(lbl("✓", L["body"], L["accent"], bold=True))
        tv.addLayout(head)
        tv.addWidget(lbl(name, 22, L["fg"], bold=True))
        tv.addWidget(lbl(desc, L["cap"], L["sub"]))
        grid.addWidget(tile, k // 2, k % 2)
    v.addLayout(grid, 1)
    v.addStretch()
    return page_std(L, i, w)


def p105(L, s, i):
    """页5 · 组合技 · 横向三连齿轮"""
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    v.addWidget(lbl("⚙️", 72, L["fg"], align=Qt.AlignHCenter))
    v.addWidget(lbl("流程 × 流程 × 流程", 26, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addSpacing(GAP_M)
    row = QHBoxLayout()
    row.setSpacing(GAP_S)
    row.addStretch()
    for k, (tag, _) in enumerate(s["pipe"]):
        box = frame(border=L["line"], size=(40, 40))
        bx = QVBoxLayout(box)
        bx.addWidget(lbl(tag, L["body"], L["fg"], bold=True, align=Qt.AlignCenter))
        row.addWidget(box)
        if k < 2:
            row.addWidget(lbl("→", L["body"], L["sub"], bold=True))
    row.addStretch()
    v.addLayout(row)
    v.addStretch()
    v.addWidget(lbl(s["pain"], L["cap"], L["sub"], align=Qt.AlignHCenter))
    return page_std(L, i, w)


def p106(L, s, i):
    """页6 · 巨字「下班」"""
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_XS)
    v.addStretch()
    v.addWidget(lbl("下班", 96, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl("把时间留给值得的人和事 🚀", L["cap"], L["sub"], ls=2, align=Qt.AlignHCenter))
    v.addSpacing(GAP_M)
    row = QHBoxLayout()
    row.setSpacing(GAP_M)
    row.addStretch()
    for d in s["dones"]:
        row.addWidget(lbl("✓ " + d, L["body"], L["fg"], bold=True))
    row.addStretch()
    v.addLayout(row)
    v.addStretch()
    return page_std(L, i, w)


# ═══════════════════════ 套 2 · 墨夜首映 ═══════════════════════
def p201(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    v.addWidget(lbl("同样的活", 40, L["fg"], bold=True))
    bar = frame(L["accent"], radius=3)
    bar.setFixedSize(180, 6)
    v.addWidget(bar)
    v.addSpacing(GAP_XS)
    v.addWidget(lbl("两种干法 —— 你选哪种", L["cap"], L["sub"]))
    v.addStretch()
    pair = QHBoxLayout()
    pair.setSpacing(GAP_L)
    pair.addWidget(lbl("5 分钟 / 项", 22, L["sub"], bold=True))
    pair.addStretch()
    pair.addWidget(lbl("10 秒 / 项", 22, L["accent"], bold=True))
    v.addLayout(pair)
    return page_std(L, i, w)


def p202(L, s, i):
    term = frame("#0B0B0E", L["line"], 12)
    tv = QVBoxLayout(term)
    tv.setContentsMargins(GAP_M, GAP_M, GAP_M, GAP_M)
    tv.setSpacing(GAP_XS)
    bar = QHBoxLayout()
    for c in ("●", "●", "●"):
        dot = QLabel(c)
        dot.setStyleSheet(f"color:{L['sub']};font-size:9px;background:transparent;border:none;")
        bar.addWidget(dot)
        bar.addSpacing(4)
    bar.addStretch()
    bar.addWidget(lbl("record.log", L["micro"], L["sub"], family='"Consolas", monospace'))
    tv.addLayout(bar)
    tv.addSpacing(GAP_XS)
    for line, col in (("› 左键框选      → 已捕获 [单击]", L["fg"]),
                      ("› 右键框选      → 已捕获 [右击]", L["fg"]),
                      ("› 按 K          → 已捕获 [按键]", L["fg"]),
                      ("› 按 T          → 已捕获 [文本]", L["fg"]),
                      ("› ESC           → 录制完成 ✓", L["accent"])):
        tv.addWidget(lbl(line, L["body"], col, family='"Consolas", monospace', bold=(col == L["accent"])))
    return page_std(L, i, term)


def p203(L, s, i):
    halo = frame("qradialgradient(cx:0.5, cy:0.5, radius:0.5, stop:0 #1E3A5F, stop:1 #101012)",
                 radius=CARD_W)
    hv = QVBoxLayout(halo)
    hv.setAlignment(Qt.AlignCenter)
    cup = QLabel("☕")
    cup.setAlignment(Qt.AlignCenter)
    cup.setStyleSheet("font-size:96px;background:transparent;border:none;")
    hv.addWidget(cup)
    hv.addWidget(lbl("你只需要看着", 26, L["fg"], bold=True, align=Qt.AlignHCenter))
    hv.addWidget(lbl("打开 · 输入 · 点击 · 完成，全自动", L["cap"], L["sub"], align=Qt.AlignHCenter))
    return page_std(L, i, halo)


def p204(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_XS)
    v.addWidget(lbl("diff · 录错了不用重录", L["cap"], L["sub"]))
    box = frame("#0B0B0E", L["line"], 10)
    bv = QVBoxLayout(box)
    bv.setContentsMargins(GAP_M, GAP_S, GAP_M, GAP_S)
    bv.setSpacing(2)
    rows = [("- 按 K  →  'Kek'", "#FF6B6B"),
            ("+ 按 K  →  'K'", "#4ade80"),
            ("  文本步骤 ×1", L["sub"]),
            ("  点击步骤 ×2", L["sub"]),
            ("+ 调整顺序  拖拽完成", "#4ade80")]
    for t, c in rows:
        bv.addWidget(lbl(t, L["body"], c, family='"Consolas", monospace'))
    v.addWidget(box, 1)
    v.addWidget(lbl(s["point"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p205(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)
    v.addStretch()
    for k, (tag, desc) in enumerate(s["pipe"]):
        row = QHBoxLayout()
        row.setSpacing(GAP_M)
        dot = frame(L["accent"], radius=9, size=(18, 18))
        row.addWidget(dot)
        if k < len(s["pipe"]) - 1:
            ln = frame(L["line"])
            ln.setFixedWidth(2)
            ln.setFixedHeight(34)
            lcol = QVBoxLayout()
            lcol.setContentsMargins(8, 0, 0, 0)
            lcol.addWidget(ln)
            rowv = QVBoxLayout()
            rowv.addLayout(row)
            rowv.addLayout(lcol)
            v.addLayout(rowv)
            row2 = QHBoxLayout()
            row2.addSpacing(38)
            row2.addWidget(lbl(desc, L["body"], L["fg"], bold=True))
            v.addLayout(row2)
        else:
            row.addWidget(lbl(f"  {tag} · {desc}", L["body"], L["fg"], bold=True))
            v.addLayout(row)
    v.addSpacing(GAP_M)
    v.addWidget(lbl(s["pain"], L["cap"], L["sub"]))
    v.addStretch()
    return page_std(L, i, w)


def p206(L, s, i):
    gridholder = QWidget()
    g = QGridLayout(gridholder)
    g.setContentsMargins(0, 0, 0, 0)
    g.setSpacing(GAP_M)
    dones = [("REC × 1", "录一次"), ("∞", "无限回放"), ("✎", "随意修改"), ("⇄", "组合串联")]
    for k, (sym, name) in enumerate(dones):
        tile = frame(L["chip"], L["line"], 14)
        tv = QVBoxLayout(tile)
        tv.setContentsMargins(GAP_M, GAP_L, GAP_M, GAP_L)
        tv.setSpacing(GAP_XS)
        tv.addWidget(lbl(sym, 30, L["accent"], bold=True, align=Qt.AlignCenter))
        tv.addWidget(lbl(name, L["body"], L["fg"], bold=True, align=Qt.AlignCenter))
        g.addWidget(tile, k // 2, k % 2)
    wrap = QWidget()
    wv = QVBoxLayout(wrap)
    wv.setContentsMargins(0, 0, 0, 0)
    wv.setSpacing(GAP_M)
    wv.addWidget(gridholder, 1)
    wv.addWidget(lbl("🎉 毕业了 —— 把时间留给自己", 20, L["fg"], bold=True, align=Qt.AlignHCenter))
    return page_std(L, i, wrap)


# ═══════════════════════ 套 3 · 电蓝快线 ═══════════════════════
def p301(L, s, i):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    big = lbl("01", 150, L["chip"], bold=True)
    h.addWidget(big, 0, Qt.AlignVCenter)
    col = QVBoxLayout()
    col.addStretch()
    col.addWidget(lbl("同样的活", 32, L["fg"], bold=True))
    col.addWidget(lbl("两种干法", 32, L["accent"], bold=True))
    col.addSpacing(GAP_S)
    col.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    col.addStretch()
    h.addLayout(col, 1)
    return page_std(L, i, w)


def p302(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)
    v.addStretch()
    band = frame(L["accent"], radius=18)
    band.setFixedHeight(150)
    bv = QHBoxLayout(band)
    bv.setContentsMargins(GAP_L, 0, GAP_L, 0)
    bv.setSpacing(GAP_L)
    for key, desc in s["keys"]:
        colv = QVBoxLayout()
        colv.addStretch()
        colv.addWidget(lbl(key, 30, "#FFFFFF", bold=True, align=Qt.AlignHCenter))
        colv.addWidget(lbl(desc, L["micro"], "#BFD3FF", align=Qt.AlignHCenter))
        colv.addStretch()
        bv.addLayout(colv, 1)
    v.addWidget(band)
    v.addSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addStretch()
    return page_std(L, i, w)


def p303(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addStretch()
    row = QHBoxLayout()
    row.setSpacing(GAP_M)
    row.addStretch()
    for c in s["chips"][:3]:
        pill = frame("#FFFFFF", L["chip_border"], 999)
        pv = QVBoxLayout(pill)
        pv.setContentsMargins(GAP_M, GAP_S, GAP_M, GAP_S)
        pv.addWidget(lbl(c, L["cap"], L["fg"], bold=True, align=Qt.AlignCenter))
        row.addWidget(pill)
    row.addStretch()
    v.addLayout(row)
    v.addSpacing(GAP_M)
    circle = frame(L["accent"], radius=120, size=(240, 120))
    cv = QVBoxLayout(circle)
    cv.addWidget(lbl("你只管看着 ☕", 22, "#FFFFFF", bold=True, align=Qt.AlignCenter))
    v.addWidget(circle, 0, Qt.AlignHCenter)
    v.addStretch()
    return page_std(L, i, w)


def p304(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addSpacing(GAP_XS)
    for k, (name, desc) in enumerate(s["edits"]):
        row = QHBoxLayout()
        row.setSpacing(GAP_M)
        num = lbl(f"{k + 1}", L["hero"], L["chip"], bold=True)
        num.setFixedWidth(52)
        row.addWidget(num)
        row.addWidget(lbl(name, L["body"], L["fg"], bold=True))
        row.addWidget(lbl(desc, L["cap"], L["sub"]), 1, Qt.AlignRight)
        v.addLayout(row)
        ln = frame(border=L["line"])
        ln.setFixedHeight(1)
        v.addWidget(ln)
    v.addStretch()
    v.addWidget(lbl(s["point"], L["cap"], L["accent"], bold=True))
    return page_std(L, i, w)


def p305(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addStretch()
    for k, (tag, desc) in enumerate(s["pipe"]):
        card = frame(L["chip"], L["chip_border"], 14)
        cv = QHBoxLayout(card)
        cv.setContentsMargins(GAP_M, GAP_S, GAP_M, GAP_S)
        cv.setSpacing(GAP_M)
        badge = frame(L["accent"], radius=999, size=(30, 30))
        bv = QVBoxLayout(badge)
        bv.addWidget(lbl(tag, L["cap"], "#FFFFFF", bold=True, align=Qt.AlignCenter))
        cv.addWidget(badge)
        cv.addWidget(lbl(desc, L["body"], L["fg"], bold=True), 1)
        cv.addWidget(lbl("□", L["body"], L["sub"]))
        v.addWidget(card)
        if k < 2:
            arrow = lbl("↓", L["cap"], L["accent"], bold=True, align=Qt.AlignHCenter)
            v.addWidget(arrow)
    v.addStretch()
    v.addWidget(lbl(s["pain"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p306(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    stamp = frame(L["accent"], radius=110, size=(220, 220))
    sv = QVBoxLayout(stamp)
    sv.setAlignment(Qt.AlignCenter)
    sv.addWidget(lbl("GO", 56, "#FFFFFF", bold=True, align=Qt.AlignHCenter))
    sv.addWidget(lbl("你已经学会全部操作", L["cap"], "#CFE0FF", align=Qt.AlignHCenter))
    v.addWidget(stamp, 0, Qt.AlignHCenter)
    v.addSpacing(GAP_M)
    row = QHBoxLayout()
    row.setSpacing(GAP_M)
    row.addStretch()
    for d in s["dones"]:
        row.addWidget(lbl("✓ " + d, L["cap"], L["fg"], bold=True))
    row.addStretch()
    v.addLayout(row)
    v.addStretch()
    return page_std(L, i, w)


# ═══════════════════════ 套 4 · 纸上笔记 ═══════════════════════
def p401(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    q = lbl("「", 60, L["accent"], bold=True)
    v.addWidget(q)
    v.addWidget(lbl("同样的活，两种干法。", 30, L["fg"], bold=True))
    v.addSpacing(GAP_XS)
    v.addWidget(lbl("旧法五分钟，新法十秒整。", L["body"], L["sub"]))
    v.addSpacing(GAP_S)
    rule = frame(border=L["line"])
    rule.setFixedHeight(1)
    v.addWidget(rule)
    foot = QHBoxLayout()
    foot.addWidget(lbl("摘自《PC-action 使用笔记》", L["micro"], L["sub"]))
    foot.addStretch()
    foot.addWidget(lbl(f"— {i + 1:02d}", L["micro"], L["accent"], bold=True))
    v.addLayout(foot)
    return page_std(L, i, w)


def p402(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl("四种指令，像盖章一样简单", L["cap"], L["sub"]))
    grid = QGridLayout()
    grid.setSpacing(GAP_M)
    for k, (key, desc) in enumerate(s["keys"]):
        seal = frame("#FFFFFF", L["accent"], 8, dash=True)
        sv = QVBoxLayout(seal)
        sv.setAlignment(Qt.AlignCenter)
        sv.setContentsMargins(GAP_S, GAP_S, GAP_S, GAP_S)
        sv.addWidget(lbl(key, 26, L["accent"], bold=True, align=Qt.AlignHCenter))
        sv.addWidget(lbl(desc, L["micro"], L["sub"], align=Qt.AlignHCenter))
        grid.addWidget(seal, k // 2, k % 2)
    v.addLayout(grid, 1)
    return page_std(L, i, w)


def p403(L, s, i):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(0)
    left = QVBoxLayout()
    left.setContentsMargins(0, 0, GAP_L, 0)
    left.addWidget(lbl("上篇", L["micro"], L["sub"], ls=3))
    left.addSpacing(GAP_S)
    left.addWidget(lbl("它自动打开软件、输入文字、点击按钮。", 20, L["fg"], bold=True))
    left.addStretch()
    right = QVBoxLayout()
    right.setContentsMargins(GAP_L, 0, 0, 0)
    right.addWidget(lbl("下篇", L["micro"], L["sub"], ls=3))
    right.addSpacing(GAP_S)
    right.addWidget(lbl("你什么都不用做，只管喝咖啡。", 20, L["fg"], bold=True))
    right.addStretch()
    h.addLayout(left, 1)
    mid = frame(border=L["line"])
    mid.setFixedWidth(1)
    h.addWidget(mid)
    h.addLayout(right, 1)
    wrapw = QWidget()
    wrapw.setStyleSheet("background:transparent;border:none;")
    wrapv = QVBoxLayout(wrapw)
    wrapv.setContentsMargins(0, 0, 0, 0)
    wrapv.setSpacing(GAP_M)
    wrapv.addLayout(h, 1)
    foot = QHBoxLayout()
    foot.addWidget(lbl("· 12 ·", L["micro"], L["sub"], align=Qt.AlignHCenter), 1)
    wrapv.addLayout(foot)
    return page_std(L, i, wrapw)


def p404(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    v.addWidget(lbl("修改清单（手写批注版）", L["cap"], L["sub"]))
    for k, (name, desc) in enumerate(s["edits"]):
        row = QFrame()
        row.setStyleSheet(f"QFrame {{ background:{'#FFFFFF' if k % 2 == 0 else 'transparent'};"
                          f"border:none;border-radius:6px; }}")
        rv = QHBoxLayout(row)
        rv.setContentsMargins(GAP_S, GAP_XS, GAP_S, GAP_XS)
        rv.addWidget(lbl("☐", L["body"], L["sub"]))
        rv.addWidget(lbl(name + " —— " + desc, L["body"], L["fg"]))
        rv.addStretch()
        rv.addWidget(lbl("✓ 已批注", L["micro"], L["accent"], bold=True))
        v.addWidget(row)
    v.addStretch()
    v.addWidget(lbl("批注完成会自动保存。", L["cap"], L["sub"]))
    return page_std(L, i, w)


def p405(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl("组合技 · 流水账", L["cap"], L["sub"]))
    for k, (tag, desc) in enumerate(s["pipe"]):
        row = QHBoxLayout()
        row.setSpacing(GAP_M)
        row.addWidget(lbl(f"第{k + 1}步", L["micro"], L["accent"], bold=True))
        row.addWidget(lbl(desc, L["body"], L["fg"]))
        row.addStretch()
        if k < 2:
            row.addWidget(lbl("↓ 接上", L["micro"], L["sub"]))
        v.addLayout(row)
        dots = lbl("· · · · · · · · · · · · · · · · · · · · · · · · · · · · · · ·", L["micro"], L["line"], align=Qt.AlignHCenter)
        v.addWidget(dots)
    v.addStretch()
    v.addWidget(lbl(s["pain"], L["body"], L["fg"], bold=True))
    return page_std(L, i, w)


def p406(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    seal = frame(L["accent"], radius=999, size=(150, 150))
    sv = QVBoxLayout(seal)
    sv.setAlignment(Qt.AlignCenter)
    sv.addWidget(lbl("结业", 34, "#FFFFFF", bold=True, align=Qt.AlignHCenter))
    sv.addWidget(lbl("CERTIFIED", L["micro"], "#F5C9C0", ls=3, align=Qt.AlignHCenter))
    v.addWidget(seal, 0, Qt.AlignHCenter)
    v.addSpacing(GAP_M)
    v.addWidget(lbl(" · ".join(s["dones"]), L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addWidget(lbl(s["point"], L["body"], L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addStretch()
    return page_std(L, i, w)


# ═══════════════════════ 套 5 · 森林晨光 ═══════════════════════
def p501(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    leaf = QLabel("🌿")
    leaf.setStyleSheet("font-size:72px;background:transparent;border:none;")
    v.addWidget(leaf)
    v.addWidget(lbl("同样的活，两种干法", 30, L["fg"], bold=True))
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addStretch()
    for o, n in ((s["old"][0], s["new"][0]), (s["old"][3], s["new"][3])):
        row = QHBoxLayout()
        row.addWidget(lbl(o, L["cap"], L["sub"]))
        row.addStretch()
        row.addWidget(lbl(n, L["cap"], L["accent"], bold=True))
        v.addLayout(row)
    return page_std(L, i, w)


def p502(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    for key, desc in s["keys"]:
        b = frame(L["chip"], L["chip_border"], 999)
        bv = QHBoxLayout(b)
        bv.setContentsMargins(GAP_L, GAP_S, GAP_L, GAP_S)
        bv.addWidget(lbl(key, L["body"], L["accent"], bold=True))
        bv.addStretch()
        bv.addWidget(lbl(desc, L["cap"], L["sub"]))
        v.addWidget(b)
    v.addStretch()
    v.addWidget(lbl(s["pain"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p503(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)
    path = QHBoxLayout()
    path.setSpacing(GAP_M)
    line = frame(L["line"])
    line.setFixedWidth(2)
    line.setFixedHeight(240)
    path.addWidget(line)
    colv = QVBoxLayout()
    colv.setSpacing(GAP_M)
    for c in s["chips"]:
        roww = QHBoxLayout()
        roww.setSpacing(GAP_M)
        dot = frame(L["accent"], radius=7, size=(14, 14))
        roww.addWidget(dot)
        roww.addWidget(lbl(c, L["body"], L["fg"], bold=True))
        colv.addLayout(roww)
    path.addLayout(colv, 1)
    v.addStretch()
    v.addLayout(path)
    v.addStretch()
    v.addWidget(lbl(s["pain"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p504(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    card = frame("#FFFFFF", L["chip_border"], 22)
    cv = QVBoxLayout(card)
    cv.setContentsMargins(GAP_L, GAP_L, GAP_L, GAP_L)
    cv.setSpacing(GAP_M)
    cv.addWidget(lbl("✏️", 40, L["fg"], align=Qt.AlignHCenter))
    cv.addWidget(lbl("录错？改掉就行", 24, L["fg"], bold=True, align=Qt.AlignHCenter))
    roww = QHBoxLayout()
    roww.setSpacing(GAP_L)
    roww.addStretch()
    for name, _ in s["edits"]:
        roww.addWidget(lbl(name, L["cap"], L["sub"], bold=True))
    roww.addStretch()
    cv.addLayout(roww)
    cv.addWidget(lbl(s["point"], L["cap"], L["accent"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(card, 1)
    return page_std(L, i, w)


def p505(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addStretch()
    row = QHBoxLayout()
    row.setSpacing(GAP_S)
    for k, (tag, desc) in enumerate(s["pipe"]):
        node = QVBoxLayout()
        node.setSpacing(GAP_S)
        circ = frame(L["accent"], radius=999, size=(64, 64))
        cvv = QVBoxLayout(circ)
        cvv.addWidget(lbl(tag, 24, "#FFFFFF", bold=True, align=Qt.AlignCenter))
        node.addWidget(circ, 0, Qt.AlignHCenter)
        d = lbl(desc.split(" → ")[0], L["micro"], L["sub"], align=Qt.AlignHCenter)
        node.addWidget(d)
        row.addLayout(node)
        if k < 2:
            ar = lbl("→", 24, L["accent"], bold=True, align=Qt.AlignHCenter)
            row.addWidget(ar, 0, Qt.AlignVCenter)
    row.addStretch()
    v.addLayout(row)
    v.addStretch()
    v.addWidget(lbl(s["pain"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p506(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    ring = frame(border=L["accent"], radius=999, size=(190, 190))
    rv = QVBoxLayout(ring)
    rv.setAlignment(Qt.AlignCenter)
    rv.addWidget(lbl("✓", 64, L["accent"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(ring, 0, Qt.AlignHCenter)
    v.addSpacing(GAP_S)
    roww = QHBoxLayout()
    roww.setSpacing(GAP_M)
    roww.addStretch()
    for d in s["dones"]:
        roww.addWidget(lbl("· " + d, L["cap"], L["sub"], bold=True))
    roww.addStretch()
    v.addLayout(roww)
    v.addWidget(lbl(s["point"], L["body"], L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addStretch()
    return page_std(L, i, w)


# ═══════════════════════ 套 6 · 暖阳手账 ═══════════════════════
def p601(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    sun = QLabel("☀️")
    sun.setStyleSheet("font-size:60px;background:transparent;border:none;")
    v.addWidget(sun, 0, Qt.AlignHCenter)
    v.addWidget(lbl("今天也从重复劳动里毕业", 26, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addStretch()
    band = frame(L["accent"], radius=12)
    band.setFixedHeight(64)
    bv = QHBoxLayout(band)
    bv.setContentsMargins(GAP_L, 0, GAP_L, 0)
    bv.addWidget(lbl("旧 · 15 分钟", L["body"], "#FBE3D4", bold=True))
    bv.addStretch()
    bv.addWidget(lbl("→", 20, "#FFFFFF"))
    bv.addStretch()
    bv.addWidget(lbl("新 · 26 秒", L["body"], "#FFFFFF", bold=True))
    v.addWidget(band)
    return page_std(L, i, w)


def p602(L, s, i):
    w = QWidget()
    grid = QGridLayout(w)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setSpacing(GAP_M)
    notes = list(enumerate(s["keys"]))
    for k, (key, desc) in notes:
        note = frame("#FFF6E0", "#F0DFAE", 4)
        nv = QVBoxLayout(note)
        nv.setContentsMargins(GAP_M, GAP_M, GAP_M, GAP_M)
        nv.setSpacing(GAP_XS)
        nv.addWidget(lbl(f"指令 {k + 1}", L["micro"], "#B8945A", bold=True, ls=2))
        nv.addWidget(lbl(key, 30, "#5A4A2E", bold=True))
        nv.addWidget(lbl(desc, L["cap"], "#8A7A5E"))
        grid.addWidget(note, k // 2, k % 2)
    return page_std(L, i, grid.parentWidget())


def p603(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addStretch()
    for c in s["chips"]:
        pill = frame(L["accent"], radius=999)
        pv = QHBoxLayout(pill)
        pv.setContentsMargins(GAP_L, GAP_XS + 2, GAP_L, GAP_XS + 2)
        pv.addWidget(lbl(c, L["body"], "#FFFFFF", bold=True))
        pv.addStretch()
        pv.addWidget(lbl("✓", L["body"], "#FFE0C4"))
        v.addWidget(pill)
    v.addStretch()
    v.addWidget(lbl(s["pain"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p604(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    half = frame(L["accent"], radius=0)
    half.setFixedSize(260, 130)
    half.setStyleSheet(f"QFrame {{ background:{L['accent']};"
                       f"border-top-left-radius:130px;border-top-right-radius:130px;border:none; }}")
    v.addWidget(half, 0, Qt.AlignHCenter)
    v.addSpacing(GAP_M)
    v.addWidget(lbl("录错了？太阳明天照常升起", 22, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl("四件事：改键 · 改字 · 调序 · 删除", L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addStretch()
    return page_std(L, i, w)


def p605(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addStretch()
    for k, (tag, desc) in enumerate(s["pipe"]):
        row = QHBoxLayout()
        row.setSpacing(GAP_M)
        box = frame(L["accent"], radius=10, size=(46, 46))
        bx = QVBoxLayout(box)
        bx.addWidget(lbl(tag, L["body"], "#FFFFFF", bold=True, align=Qt.AlignCenter))
        row.addWidget(box)
        card = frame("#FFFFFF", "#F0E4CE", 10)
        cx = QVBoxLayout(card)
        cx.setContentsMargins(GAP_M, GAP_S, GAP_M, GAP_S)
        cx.addWidget(lbl(desc, L["body"], L["fg"]))
        row.addWidget(card, 1)
        v.addLayout(row)
        if k < 2:
            v.addWidget(lbl("↓", L["cap"], L["accent"], bold=True, align=Qt.AlignHCenter))
    v.addStretch()
    v.addWidget(lbl(s["point"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p606(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_XS)
    v.addStretch()
    conf = lbl("🎉 ✦ 🎊 ✦ 🎉 ✦ 🎊 ✦ 🎉", 22, L["accent"], bold=True, align=Qt.AlignHCenter)
    v.addWidget(conf)
    v.addSpacing(GAP_M)
    v.addWidget(lbl("毕业啦", 44, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl(" · ".join(s["dones"]), L["body"], L["sub"], align=Qt.AlignHCenter))
    v.addSpacing(GAP_M)
    v.addWidget(lbl(s["point"], L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addStretch()
    v.addWidget(lbl("🧡 暖阳手账 · 今天的你也辛苦了", L["micro"], "#B8945A", align=Qt.AlignHCenter))
    return page_std(L, i, w)


# ═══════════════════════ 套 7 · 线稿蓝图 ═══════════════════════
def p701(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_L)
    box = frame("#FFFFFF", L["line"], 0)
    bv = QVBoxLayout(box)
    bv.setContentsMargins(GAP_L, GAP_L, GAP_L, GAP_L)
    bv.addWidget(lbl("FIG.01 — 两种干法", L["micro"], L["sub"], ls=2))
    bv.addSpacing(GAP_S)
    bv.addWidget(lbl("A. 手动 ≈ 15 分钟", L["body"], L["fg"], bold=True))
    rule = frame(border=L["line"])
    rule.setFixedHeight(1)
    bv.addWidget(rule)
    bv.addWidget(lbl("B. 流程 ≈ 26 秒", L["body"], L["fg"], bold=True))
    v.addWidget(box)
    v.addWidget(lbl("—— 手动 vs 流程 · 差距 = 34 倍", L["cap"], L["sub"]))
    return page_std(L, i, w)


def p702(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl("FIG.02 — 指令键位图", L["micro"], L["sub"], ls=2))
    row = QHBoxLayout()
    row.setSpacing(GAP_M)
    for key, desc in s["keys"]:
        capw = frame("#FFFFFF", L["line"], 0, (110, 110), dash=True)
        cv = QVBoxLayout(capw)
        cv.setAlignment(Qt.AlignCenter)
        cv.addWidget(lbl(key, 24, L["fg"], bold=True, align=Qt.AlignHCenter))
        cv.addWidget(lbl(desc, L["micro"], L["sub"], align=Qt.AlignHCenter))
        row.addWidget(capw)
    v.addLayout(row)
    v.addStretch()
    v.addWidget(lbl("[ESC] = 停止录制", L["cap"], L["fg"], bold=True))
    return page_std(L, i, w)


def p703(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl("FIG.03 — 自动执行序列", L["micro"], L["sub"], ls=2))
    for c in s["chips"]:
        roww = QHBoxLayout()
        roww.setSpacing(GAP_S)
        b1 = frame("#FFFFFF", L["line"], 0)
        b1.setFixedSize(14, 14)
        roww.addWidget(b1)
        roww.addWidget(lbl(c, L["body"], L["fg"]))
        ln = frame(border=L["line"], dash=True)
        ln.setFixedHeight(1)
        roww.addWidget(ln, 1)
        roww.addWidget(lbl("▸", L["cap"], L["sub"]))
        v.addLayout(roww)
    v.addStretch()
    v.addWidget(lbl("操作员：不需要。", L["body"], L["fg"], bold=True))
    return page_std(L, i, w)


def p704(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl("FIG.04 — 修订记录", L["micro"], L["sub"], ls=2))
    for name, desc in s["edits"]:
        roww = QHBoxLayout()
        roww.setSpacing(GAP_M)
        roww.addWidget(lbl("┌", L["body"], L["line"]))
        roww.addWidget(lbl(name, L["body"], L["fg"], bold=True))
        roww.addWidget(lbl("· " + desc, L["cap"], L["sub"]), 1)
        roww.addWidget(lbl("[OK]", L["micro"], L["fg"], bold=True))
        v.addLayout(roww)
    v.addStretch()
    v.addWidget(lbl("全部修订自动落盘。", L["cap"], L["sub"]))
    return page_std(L, i, w)


def p705(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl("FIG.05 — 组合管线", L["micro"], L["sub"], ls=2))
    for k, (tag, desc) in enumerate(s["pipe"]):
        roww = QHBoxLayout()
        roww.setSpacing(0)
        b = frame("#FFFFFF", L["line"], 0, (40, 40))
        bv2 = QVBoxLayout(b)
        bv2.addWidget(lbl(tag, L["body"], L["fg"], bold=True, align=Qt.AlignCenter))
        roww.addWidget(b)
        name = frame("#FFFFFF", L["line"], 0)
        nv = QVBoxLayout(name)
        nv.setContentsMargins(GAP_M, GAP_XS, GAP_M, GAP_XS)
        nv.addWidget(lbl(desc, L["body"], L["fg"]))
        roww.addWidget(name, 1)
        v.addLayout(roww)
        if k < 2:
            v.addWidget(lbl("│", L["body"], L["line"], align=Qt.AlignHCenter))
    v.addStretch()
    v.addWidget(lbl("输入：一次点击 · 输出：全部完成", L["cap"], L["sub"]))
    return page_std(L, i, w)


def p706(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    big = frame("#FFFFFF", L["line"], 0, (160, 160))
    bv = QVBoxLayout(big)
    bv.setAlignment(Qt.AlignCenter)
    bv.addWidget(lbl("✓", 72, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(big, 0, Qt.AlignHCenter)
    v.addSpacing(GAP_M)
    v.addWidget(lbl("FIG.06 — 课程完成", L["micro"], L["sub"], ls=2, align=Qt.AlignHCenter))
    v.addWidget(lbl(" · ".join(s["dones"]), L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addStretch()
    return page_std(L, i, w)


# ═══════════════════════ 套 8 · 大字报 ═══════════════════════
BT = ["#FF375F", "#0A84FF", "#30D158", "#FF9F0A", "#BF5AF2", "#FFD60A"]
BT_FG = ["#FFFFFF", "#FFFFFF", "#0B3D1E", "#3D2500", "#FFFFFF", "#3D3000"]


def bt_page(L, i, char, sub, note):
    bg, fg = BT[i], BT_FG[i]
    pg = QFrame()
    pg.setStyleSheet(f"QFrame {{ background:{bg};border-radius:{L['radius_page']}px;border:none; }}")
    v = QVBoxLayout(pg)
    v.setContentsMargins(PAD, GAP_M, PAD, GAP_M)
    v.setSpacing(GAP_S)
    head = QHBoxLayout()
    head.addWidget(lbl(f"{L['kicker']} · {i + 1:02d}", L["micro"], fg, bold=True, ls=3))
    head.addStretch()
    head.addWidget(lbl(f"{i + 1} — {N}", L["micro"], fg, bold=True))
    v.addLayout(head)
    v.addStretch()
    v.addWidget(lbl(char, 150, fg, bold=True, align=Qt.AlignHCenter))
    v.addSpacing(GAP_S)
    v.addWidget(lbl(sub, 22, fg, bold=True, align=Qt.AlignHCenter))
    v.addSpacing(GAP_XS)
    v.addWidget(lbl(note, L["cap"], fg, align=Qt.AlignHCenter))
    v.addStretch()
    v.addWidget(lbl(STEPS[i]["point"], L["micro"], fg, align=Qt.AlignHCenter))
    return page_bare(L, pg)


def p801(L, s, i):
    return bt_page(L, 0, "快", "同样的活 · 两种速度", "15 分钟 → 26 秒")


def p802(L, s, i):
    return bt_page(L, 1, "录", "四个指令 · 一遍学会", "左键 · 右键 · K · T · ESC")


def p803(L, s, i):
    return bt_page(L, 2, "看", "回放 · 它替你干", "打开 输入 点击 完成 ☕")


def p804(L, s, i):
    return bt_page(L, 3, "改", "录错不用重来", "改键 改字 调序 删除")


def p805(L, s, i):
    return bt_page(L, 4, "串", "组合技 · 一键跑完", "A → B → C")


def p806(L, s, i):
    return bt_page(L, 5, "成", "毕业 · 时间还给你", "录一次 · 无限回放 · 随意改 · 随便串")


# ═══════════════════════ 套 9 · 晨雾玻璃 ═══════════════════════
def p901(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    card = frame("#FFFFFF", L["chip_border"], 24)
    cv = QVBoxLayout(card)
    cv.setContentsMargins(GAP_L, GAP_L, GAP_L, GAP_L)
    cv.addWidget(lbl("同样的活 · 两种干法", 26, L["fg"], bold=True))
    cv.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addWidget(card)
    card2 = frame(L["chip"], L["chip_border"], 24)
    c2 = QHBoxLayout(card2)
    c2.setContentsMargins(GAP_L, GAP_M, GAP_L, GAP_M)
    c2.addWidget(lbl("15 分钟", 20, L["sub"], bold=True))
    c2.addStretch()
    c2.addWidget(lbl("→ 26 秒", 20, L["accent"], bold=True))
    v.addWidget(card2)
    v.addStretch()
    return page_std(L, i, w)


def p902(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    grid = QGridLayout()
    grid.setSpacing(GAP_M)
    for k, (key, desc) in enumerate(s["keys"]):
        tile = frame("#FFFFFF", L["chip_border"], 20)
        tv = QVBoxLayout(tile)
        tv.setContentsMargins(GAP_M, GAP_M, GAP_M, GAP_M)
        tv.setSpacing(GAP_XS)
        tv.addWidget(lbl(key, 28, L["accent"], bold=True))
        tv.addWidget(lbl(desc, L["cap"], L["sub"]))
        tile.shadow = True
        grid.addWidget(tile, k // 2, k % 2)
    v.addLayout(grid, 1)
    return page_std(L, i, w)


def p903(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    orb = frame("qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #EAF0FB, stop:1 #FFFFFF)",
                L["chip_border"], 999, (240, 240))
    ov = QVBoxLayout(orb)
    ov.setAlignment(Qt.AlignCenter)
    ov.addWidget(lbl("☕", 64, L["fg"], align=Qt.AlignHCenter))
    ov.addWidget(lbl("它干完的同时，你刚泡好咖啡", 18, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(orb, 0, Qt.AlignHCenter)
    v.addStretch()
    roww = QHBoxLayout()
    roww.setSpacing(GAP_S)
    roww.addStretch()
    for c in s["chips"]:
        roww.addWidget(lbl("· " + c, L["micro"], L["sub"], bold=True))
    roww.addStretch()
    v.addLayout(roww)
    return page_std(L, i, w)


def p904(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_S)
    v.addWidget(lbl("雾面修订 —— 四步就改好", 22, L["fg"], bold=True))
    v.addSpacing(GAP_XS)
    for k, (name, desc) in enumerate(s["edits"]):
        card = frame("rgba(255,255,255,0.75)", L["chip_border"], 16)
        cv = QHBoxLayout(card)
        cv.setContentsMargins(GAP_L, GAP_S, GAP_L, GAP_S)
        cv.addWidget(lbl(f"0{k + 1}", L["body"], L["accent"], bold=True))
        cv.addWidget(lbl(name, L["body"], L["fg"], bold=True))
        cv.addStretch()
        cv.addWidget(lbl(desc, L["cap"], L["sub"]))
        v.addWidget(card)
    v.addStretch()
    v.addWidget(lbl(s["point"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p905(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    for k, (tag, desc) in enumerate(s["pipe"]):
        card = frame("#FFFFFF", L["chip_border"], 18)
        cv = QHBoxLayout(card)
        cv.setContentsMargins(GAP_M, GAP_S, GAP_M, GAP_S)
        cv.setSpacing(GAP_M)
        circ = frame(L["chip"], L["accent"], 999, (34, 34))
        cx = QVBoxLayout(circ)
        cx.addWidget(lbl(tag, L["micro"], L["accent"], bold=True, align=Qt.AlignCenter))
        cv.addWidget(circ)
        cv.addWidget(lbl(desc, L["body"], L["fg"], bold=True), 1)
        v.addWidget(card)
        if k < 2:
            conn = frame(border=L["chip_border"])
            conn.setFixedHeight(1)
            conn.setFixedWidth(180)
            v.addWidget(conn, 0, Qt.AlignHCenter)
    v.addStretch()
    return page_std(L, i, w)


def p906(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    card = frame("qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #FFFFFF, stop:1 #EEF3FC)",
                 L["chip_border"], 26)
    cv = QVBoxLayout(card)
    cv.setContentsMargins(GAP_XL, GAP_L, GAP_XL, GAP_L)
    cv.setSpacing(GAP_M)
    cv.addWidget(lbl("🎉", 44, L["fg"], align=Qt.AlignHCenter))
    cv.addWidget(lbl("四项技能已入袋", 24, L["fg"], bold=True, align=Qt.AlignHCenter))
    roww = QHBoxLayout()
    roww.setSpacing(GAP_L)
    roww.addStretch()
    for d in s["dones"]:
        roww.addWidget(lbl("✓ " + d, L["cap"], L["sub"], bold=True))
    roww.addStretch()
    cv.addLayout(roww)
    v.addWidget(card)
    v.addSpacing(GAP_M)
    v.addWidget(lbl(s["point"], L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addStretch()
    return page_std(L, i, w)


# ═══════════════════════ 套 10 · 聚光舞台 ═══════════════════════
def p1001(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    beam = frame("qradialgradient(cx:0.5, cy:0.1, radius:1.1, stop:0 #4A4A55, stop:1 #131316)",
                 radius=18)
    beam.setFixedHeight(300)
    bv = QVBoxLayout(beam)
    bv.addStretch()
    bv.addWidget(lbl("同样的活 · 两种干法", 30, L["fg"], bold=True, align=Qt.AlignHCenter))
    bv.addWidget(lbl("15 分钟 vs 26 秒 —— 灯光打给谁？", L["cap"], L["sub"], align=Qt.AlignHCenter))
    bv.addStretch()
    v.addWidget(beam, 1)
    v.addWidget(lbl(s["point"], L["cap"], L["accent"], bold=True, align=Qt.AlignHCenter))
    return page_std(L, i, w)


def p1002(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl("登台指令 · 只记四个", L["cap"], L["sub"]))
    roww = QHBoxLayout()
    roww.setSpacing(GAP_M)
    for key, desc in s["keys"]:
        stage = frame("#1E1E24", L["line"], 16)
        sv = QVBoxLayout(stage)
        sv.setContentsMargins(GAP_M, GAP_L, GAP_M, GAP_L)
        sv.setSpacing(GAP_XS)
        sv.addWidget(lbl(key, 30, L["accent"], bold=True, align=Qt.AlignHCenter))
        sv.addWidget(lbl(desc, L["micro"], L["sub"], align=Qt.AlignHCenter))
        roww.addWidget(stage)
    v.addLayout(roww)
    v.addStretch()
    v.addWidget(lbl("谢幕键：ESC", L["body"], L["fg"], bold=True, align=Qt.AlignHCenter))
    return page_std(L, i, w)


def p1003(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    marquee = frame("#131316", L["accent"], 999, (280, 280), dash=True)
    mv = QVBoxLayout(marquee)
    mv.setAlignment(Qt.AlignCenter)
    mv.addWidget(lbl("🎬", 72, L["fg"], align=Qt.AlignHCenter))
    mv.addWidget(lbl("开演中：它替你干", 20, L["fg"], bold=True, align=Qt.AlignHCenter))
    mv.addWidget(lbl("你坐在台下喝咖啡", L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addWidget(marquee, 0, Qt.AlignHCenter)
    v.addStretch()
    roww = QHBoxLayout()
    roww.setSpacing(GAP_M)
    roww.addStretch()
    for c in s["chips"]:
        roww.addWidget(lbl("· " + c, L["micro"], L["sub"], bold=True))
    roww.addStretch()
    v.addLayout(roww)
    return page_std(L, i, w)


def p1004(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl("后台修订室", L["cap"], L["sub"]))
    for k, (name, desc) in enumerate(s["edits"]):
        roww = QHBoxLayout()
        roww.setSpacing(GAP_M)
        num = lbl(f"{k + 1:02d}", L["hero"], "#2E2E36", bold=True)
        num.setFixedWidth(64)
        roww.addWidget(num)
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(lbl(name, L["body"], L["fg"], bold=True))
        col.addWidget(lbl(desc, L["cap"], L["sub"]))
        roww.addLayout(col, 1)
        v.addLayout(roww)
        ln = frame(border=L["line"])
        ln.setFixedHeight(1)
        v.addWidget(ln)
    v.addStretch()
    v.addWidget(lbl("改完自动保存 · 灯再亮时已是完美版本", L["cap"], L["accent"], bold=True))
    return page_std(L, i, w)


def p1005(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addWidget(lbl(s["ask"], L["cap"], L["sub"]))
    v.addStretch()
    for k, (tag, desc) in enumerate(s["pipe"]):
        roww = QHBoxLayout()
        roww.setSpacing(GAP_M)
        spot = frame("#1E1E24", radius=10)
        sx = QHBoxLayout(spot)
        sx.setContentsMargins(GAP_M, GAP_S, GAP_M, GAP_S)
        sx.addWidget(lbl("◉ " + tag, L["body"], L["accent"], bold=True))
        sx.addStretch()
        sx.addWidget(lbl(desc, L["body"], L["fg"]))
        roww.addWidget(spot, 1)
        v.addLayout(roww)
        if k < 2:
            v.addWidget(lbl("▼", L["micro"], L["sub"], align=Qt.AlignHCenter))
    v.addStretch()
    v.addWidget(lbl(s["pain"], L["cap"], L["sub"]))
    return page_std(L, i, w)


def p1006(L, s, i):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(GAP_M)
    v.addStretch()
    v.addWidget(lbl("✨ 🎆 ✨", 30, L["accent"], bold=True, align=Qt.AlignHCenter))
    v.addWidget(lbl("谢幕 —— 时间还给你", 30, L["fg"], bold=True, align=Qt.AlignHCenter))
    v.addSpacing(GAP_M)
    roww = QHBoxLayout()
    roww.setSpacing(GAP_L)
    roww.addStretch()
    for d in s["dones"]:
        roww.addWidget(lbl(d, L["body"], L["fg"], bold=True))
    roww.addStretch()
    v.addLayout(roww)
    v.addSpacing(GAP_M)
    v.addWidget(lbl(s["point"], L["cap"], L["sub"], align=Qt.AlignHCenter))
    v.addStretch()
    return page_std(L, i, w)


# ═══════════════════════ 组装 ═══════════════════════
def LANG(**kw):
    base = dict(
        kicker="PC-ACTION GUIDE", bg="#FFFFFF", fg="#111114", sub="#9A9AA0",
        accent="#111114", chip="#F6F6F7", chip_border="#ECECEF",
        line="#E8E8EC", radius_page=16,
        btn_bg="#111114", btn_fg="#FFFFFF", btn_hover="#333338",
        micro=10, cap=12, body=14, hero=34, nav="arrows",
    )
    base.update(kw)
    return base


DECKS = [
    ("套 1 · 白境画廊", LANG(kicker="GALLERY"),
     [p101, p102, p103, p104, p105, p106]),
    ("套 2 · 墨夜首映", LANG(
        kicker="MIDNIGHT", bg="#101012", fg="#F5F5F7", sub="#8E8E96", accent="#0A84FF",
        chip="#1B1B1F", chip_border="#26262B", line="#26262B",
        btn_bg="#0A84FF", btn_fg="#FFFFFF", btn_hover="#006FE0"),
     [p201, p202, p203, p204, p205, p206]),
    ("套 3 · 电蓝快线", LANG(
        kicker="ELECTRIC", accent="#0051FF", chip="#F0F4FF", chip_border="#DCE6FF",
        line="#E3E9F5", btn_bg="#0051FF", btn_fg="#FFFFFF", btn_hover="#0043D6", nav="bar"),
     [p301, p302, p303, p304, p305, p306]),
    ("套 4 · 纸上笔记", LANG(
        kicker="PAPER", bg="#F7F5F0", fg="#26221C", sub="#8F887A", accent="#C7442E",
        chip="#FFFFFF", chip_border="#E8E3D7", line="#E4DFD2",
        btn_bg="#C7442E", btn_fg="#FFFFFF", btn_hover="#AD3A26", radius_page=6, nav="dots"),
     [p401, p402, p403, p404, p405, p406]),
    ("套 5 · 森林晨光", LANG(
        kicker="FOREST", accent="#0E5E45", chip="#F1F7F4", chip_border="#DFEDE6",
        line="#E2EAE5", btn_bg="#0E5E45", btn_fg="#FFFFFF", btn_hover="#0A4A37", nav="dots"),
     [p501, p502, p503, p504, p505, p506]),
    ("套 6 · 暖阳手账", LANG(
        kicker="SUNNY", bg="#FBF3E4", fg="#2B2118", sub="#9C8D7A", accent="#E8590C",
        chip="#FFFFFF", chip_border="#F0E4CE", line="#EBDFC8",
        btn_bg="#E8590C", btn_fg="#FFFFFF", btn_hover="#D14E08"),
     [p601, p602, p603, p604, p605, p606]),
    ("套 7 · 线稿蓝图", LANG(
        kicker="LINEART", chip="#FFFFFF", chip_border="#22222A", line="#22222A",
        accent="#22222A", btn_bg="#22222A", btn_fg="#FFFFFF", btn_hover="#000000",
        radius_page=0),
     [p701, p702, p703, p704, p705, p706]),
    ("套 8 · 大字报", LANG(
        kicker="BIGTYPE", bg="#111114", fg="#FFFFFF", sub="#C9C9D2", accent="#FF375F",
        chip="#1D1D22", chip_border="#2A2A31", line="#2A2A31",
        btn_bg="#FFFFFF", btn_fg="#111114", btn_hover="#E8E8EE", radius_page=0),
     [p801, p802, p803, p804, p805, p806]),
    ("套 9 · 晨雾玻璃", LANG(
        kicker="MIST", bg="#EEF1F5", fg="#20242B", sub="#8A93A1", accent="#3C6FF0",
        chip="#FFFFFF", chip_border="#E2E7EE", line="#DDE3EB",
        btn_bg="#3C6FF0", btn_fg="#FFFFFF", btn_hover="#2C5CDA", nav="dots"),
     [p901, p902, p903, p904, p905, p906]),
    ("套 10 · 聚光舞台", LANG(
        kicker="SPOTLIGHT", bg="#131316", fg="#F5F5F7", sub="#93939C", accent="#F2C14E",
        chip="#1E1E23", chip_border="#2C2C33", line="#2C2C33",
        btn_bg="#F2C14E", btn_fg="#1A1A1E", btn_hover="#E0AE38"),
     [p1001, p1002, p1003, p1004, p1005, p1006]),
]


class Deck:
    def __init__(self, L, builders):
        self.L = L
        self.idx = 0
        self.card = QFrame()
        self.card.setFixedSize(CARD_W, CARD_H)
        self.card.setStyleSheet(
            f"QFrame {{ background:{L['bg']}; border-radius:{L['radius_page']}px; border:none; }}")
        self.root = QVBoxLayout(self.card)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)
        self.stack = QStackedWidget()
        for i, fn in enumerate(builders):
            self.stack.addWidget(fn(L, STEPS[i], i))
        self.root.addWidget(self.stack, 1)
        self.build_nav()
        self.sync()

    def build_nav(self):
        L = self.L
        nav = QWidget()
        nv = QHBoxLayout(nav)
        nv.setContentsMargins(PAD, 0, PAD, GAP_M)
        nv.setSpacing(GAP_S)
        self.dots = []
        if L["nav"] == "dots":
            for i in range(N):
                d = frame(L["line"], radius=3, size=(6, 6))
                nv.addWidget(d)
                self.dots.append(d)
            nv.addStretch()
        elif L["nav"] == "bar":
            track = QFrame()
            track.setFixedSize(120, 3)
            track.setStyleSheet(f"background:{L['line']};border:none;")
            nv.addWidget(track)
            nv.addStretch()
            self.fill = QFrame(track)
            self.fill.setStyleSheet(f"background:{L['accent']};border:none;")
        else:
            nv.addStretch()
        self.prev = QPushButton("←")
        self.prev.setFixedSize(40, 40)
        self.prev.setCursor(Qt.PointingHandCursor)
        self.nxt = QPushButton("→")
        self.nxt.setFixedSize(40, 40)
        self.nxt.setCursor(Qt.PointingHandCursor)
        for b, solid in ((self.prev, False), (self.nxt, True)):
            b.setStyleSheet(
                f"QPushButton {{ background:{L['btn_bg'] if solid else 'transparent'};"
                f"color:{L['btn_fg'] if solid else L['sub']};"
                f"border:{'none' if solid else '1px solid ' + L['line']};"
                f"border-radius:20px;font-size:16px;font-family:{FONT};font-weight:700; }}"
                f"QPushButton:hover {{ background:{L['btn_hover'] if solid else L['chip']}; }}"
                f"QPushButton:disabled {{ color:{L['line']}; border-color:{L['line']}; }}")
            nv.addWidget(b)
        self.prev.clicked.connect(lambda: self.go(-1))
        self.nxt.clicked.connect(lambda: self.go(1))
        self.root.addWidget(nav)

    def go(self, d):
        ni = self.idx + d
        if 0 <= ni < N:
            self.idx = ni
            self.stack.setCurrentIndex(ni)
            self.sync()

    def sync(self):
        i = self.idx
        self.prev.setEnabled(i > 0)
        self.nxt.setEnabled(i < N - 1)
        L = self.L
        for k, d in enumerate(self.dots):
            on = k == i
            d.setStyleSheet(f"QFrame {{ background:{L['accent'] if on else L['line']};border:none;"
                            f"border-radius:3px; }}")
            d.setFixedSize(16 if on else 6, 6)
        if L["nav"] == "bar":
            self.fill.setGeometry(0, 0, int(120 * (i + 1) / N), 3)


def build_deck(name, L, builders):
    cell = QVBoxLayout()
    cap = lbl(name, 12, "#FFFFFF", bold=True)
    cap.setStyleSheet(f"color:#FFFFFF;font-size:12px;font-weight:700;font-family:{FONT};")
    cell.addWidget(cap)
    cell.addWidget(Deck(L, builders).card)
    return cell


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = QWidget()
    win.setWindowTitle("使用帮助 · 翻页流 v3 —— 60 个独立页面设计（每页不重样，可点击）")
    win.setStyleSheet("background:#B8B8BE;")
    win.resize(1520, 900)
    outer = QVBoxLayout(win)
    outer.setContentsMargins(GAP_M, GAP_M, GAP_M, GAP_M)
    head = lbl("10 套 × 6 页 = 60 个独立设计的页面 —— 每一页布局都不重样"
               "（卡 700×460 = 真实内容区 ÷1.36）", 13, "#FFFFFF", bold=True)
    head.setStyleSheet(f"color:#FFFFFF;font-size:13px;font-weight:700;font-family:{FONT};")
    outer.addWidget(head)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setStyleSheet("background:transparent;")
    holder = QWidget()
    holder.setStyleSheet("background:transparent;")
    grid = QGridLayout(holder)
    grid.setContentsMargins(GAP_S, GAP_S, GAP_S, GAP_M)
    grid.setSpacing(GAP_L)
    for k, (name, L, builders) in enumerate(DECKS):
        row, col = divmod(k, 2)
        grid.addLayout(build_deck(name, L, builders), row, col)
    grid.setRowStretch(grid.rowCount(), 1)
    scroll.setWidget(holder)
    outer.addWidget(scroll, 1)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
