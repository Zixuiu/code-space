# -*- coding: utf-8 -*-
"""录制控制卡片 - 10 种样式 GUI 选型预览
运行: .venv\\Scripts\\python.exe _preview_record_styles.py
从窗口里挑一个编号告诉 AI 即可应用到主程序。
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 确保 Qt 能找到平台插件（与 run.py 相同的处理）
import PyQt5
_plugin = os.path.join(PyQt5.__path__[0], 'Qt5', 'plugins')
os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', _plugin)
os.environ.setdefault('QT_PLUGIN_PATH', _plugin)

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient


# ---------------- 自绘控件（保证圆角） ----------------
class PillBtn(QPushButton):
    """自绘药丸按钮，支持纯色/渐变"""
    def __init__(self, text, bg="#0071E3", fg="#FFFFFF", hover=None, pressed=None,
                 grad=None, h=44, font_size=14, bold=True, arrow=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._bg, self._fg = bg, fg
        self._hover = hover or bg
        self._pressed = pressed or bg
        self._grad = grad
        self._fs, self._bold, self._arrow = font_size, bold, arrow
        self._hv = self._dn = False
        self.setFixedHeight(h)
        self.setMinimumWidth(120)

    def enterEvent(self, e): self._hv = True; self.update(); super().enterEvent(e)
    def leaveEvent(self, e): self._hv = False; self._dn = False; self.update(); super().leaveEvent(e)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._dn = True; self.update()
        super().mousePressEvent(e)
    def mouseReleaseEvent(self, e):
        self._dn = False; self.update(); super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = self.height() / 2.0
        p.setPen(Qt.NoPen)
        if self._grad:
            g = QLinearGradient(0, 0, self.width(), self.height())
            g.setColorAt(0, QColor(self._grad[0]))
            g.setColorAt(1, QColor(self._grad[1]))
            p.setBrush(QBrush(g))
        else:
            c = self._pressed if self._dn else (self._hover if self._hv else self._bg)
            p.setBrush(QColor(c))
        p.drawRoundedRect(QRectF(self.rect()), r, r)
        f = QFont("Microsoft YaHei", 9)
        f.setPixelSize(self._fs + 2)
        f.setBold(self._bold)
        p.setFont(f)
        p.setPen(QColor(self._fg))
        text = self.text().replace('\t', ' ')
        rect = self.rect()
        if self._arrow:
            p.drawText(QRectF(rect.x()+10, rect.y(), rect.width()-44, rect.height()),
                       Qt.AlignLeft | Qt.AlignVCenter, text)
            p.drawText(QRectF(rect.right()-30, rect.y(), 22, rect.height()), Qt.AlignCenter, "▾")
        else:
            p.drawText(QRectF(rect), Qt.AlignCenter, text)
        p.end()


class RecCircle(QPushButton):
    """自绘录制圆钮"""
    def __init__(self, size=96, shape="circle", plate="#FFFFFF", border="#E5E5EA",
                 border_w=1, dot="#FF3B30", dot_ratio=0.6, ring=None,
                 square_dot=False, shadow=True, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._s = size; self._shape = shape; self._plate = plate
        self._border = border; self._bw = border_w; self._dot = dot
        self._ratio = dot_ratio; self._ring = ring
        self._sq = square_dot; self._shadow = shadow
        self.setFixedSize(size, size)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        s, c = self._s, self._s / 2.0
        # 阴影
        if self._shadow:
            g = QColor(0, 0, 0, 40)
            p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 28))
            p.drawEllipse(QRectF(2, 4, s - 4, s - 4))
        # 底板
        rect = QRectF(1, 1, s - 2, s - 2)
        p.setPen(QPen(QColor(self._border), self._bw) if self._bw else Qt.NoPen)
        p.setBrush(QColor(self._plate))
        if self._shape == "circle":
            p.drawEllipse(rect)
        else:
            p.drawRoundedRect(rect, s * 0.24, s * 0.24)
        # 外环
        d = s * self._ratio
        if self._ring:
            ring = QRectF(c - d/2, c - d/2, d, d)
            p.setPen(QPen(QColor(self._ring), max(2, s * 0.045)))
            p.setBrush(Qt.NoBrush)
            if self._shape == "circle":
                p.drawEllipse(ring)
            else:
                p.drawRoundedRect(ring, s * 0.14, s * 0.14)
        # 中心点
        d2 = d * (0.82 if self._ring else 1.0)
        p.setPen(Qt.NoPen); p.setBrush(QColor(self._dot))
        if self._sq:
            p.drawRoundedRect(QRectF(c - d2/2, c - d2/2, d2, d2), 3, 3)
        else:
            p.drawEllipse(QRectF(c - d2/2, c - d2/2, d2, d2))
        p.end()


def label(text, color="#333", size=13, bold=False, spacing=None):
    lb = QLabel(text)
    st = f"color:{color}; font-size:{size}px; background:transparent; border:none;"
    if bold: st += " font-weight:700;"
    if spacing: st += f" letter-spacing:{spacing}px;"
    lb.setStyleSheet(st)
    return lb


def panel(bg, border=None, radius=18):
    w = QWidget()
    st = f"background:{bg}; border-radius:{radius}px;"
    if border: st += f" border:1px solid {border};"
    w.setStyleSheet(st)
    return w


# ---------------- 10 种样式 ----------------
def style1():  # 玻璃深色
    card = panel("#20263F")
    v = QVBoxLayout(card); v.setContentsMargins(28, 22, 28, 22); v.setSpacing(16)
    head = QHBoxLayout(); head.addWidget(label("● 录制控制", "#FFFFFF", 17, True, 1)); head.addStretch()
    v.addLayout(head)
    row = QHBoxLayout(); row.setSpacing(24)
    row.addWidget(RecCircle(92, plate="#161B2E", border="#3A4468", dot="#22D3EE",
                            ring="#22D3EE", dot_ratio=0.68))
    col = QVBoxLayout(); col.setSpacing(8)
    col.addWidget(label("录 制 模 式", "#8A93B2", 12, spacing=2))
    col.addWidget(PillBtn("📷 图像录制", bg="#2C3352", fg="#E8ECFF", hover="#39415F", arrow=True, h=46))
    col.addStretch()
    row.addLayout(col); row.addStretch()
    v.addLayout(row)
    foot = QHBoxLayout(); foot.setSpacing(12)
    foot.addWidget(PillBtn("● 回放已开启", bg="#22D3EE", fg="#0B1120", hover="#4BDCf2", pressed="#19B6D4", h=42))
    foot.addWidget(PillBtn("悬浮窗口", bg="#2C3352", fg="#AAB4D8", hover="#39415F", h=42))
    foot.addStretch()
    v.addLayout(foot)
    return card


def style2():  # 极简苹果白（当前）
    card = panel("#FFFFFF", border="#ECECF0")
    v = QVBoxLayout(card); v.setContentsMargins(32, 26, 32, 26); v.setSpacing(18)
    v.addWidget(label("录制控制", "#1D1D1F", 21, True))
    row = QHBoxLayout(); row.setSpacing(28)
    row.addWidget(RecCircle(100, plate="#FFFFFF", border="#E0E0E5", dot="#FF3B30"))
    col = QVBoxLayout(); col.setSpacing(9)
    col.addWidget(label("录制模式", "#86868B", 13))
    col.addWidget(PillBtn("📷 图像录制", bg="#F5F5F7", fg="#1D1D1F", hover="#EBEBF0", h=48, bold=False, arrow=True))
    col.addStretch()
    row.addLayout(col); row.addStretch()
    v.addLayout(row)
    foot = QHBoxLayout(); foot.setSpacing(14)
    foot.addWidget(PillBtn("● 回放已开启", bg="#0071E3", fg="#FFF", hover="#0077ED", h=46))
    foot.addWidget(PillBtn("悬浮窗口", bg="#F5F5F7", fg="#1D1D1F", hover="#EBEBF0", h=46, bold=False))
    foot.addStretch()
    v.addLayout(foot)
    return card


def style3():  # Bento 网格
    card = panel("#F7F7F9")
    v = QVBoxLayout(card); v.setContentsMargins(24, 20, 24, 20); v.setSpacing(12)
    v.addWidget(label("录制控制", "#1C1C1E", 17, True))
    grid = QGridLayout(); grid.setSpacing(10)
    big = panel("#1C1C1E", radius=16)
    bv = QVBoxLayout(big); bv.setContentsMargins(8, 12, 8, 12); bv.setSpacing(6)
    big_btn = RecCircle(70, plate="transparent", border="transparent", dot="#FF453A",
                        ring="#FF453A", dot_ratio=0.62, shadow=False)
    big_btn._plate = QColor("#1C1C1E")
    bv.addWidget(big_btn, 0, Qt.AlignCenter)
    bv.addWidget(label("点击录制", "#BBBBBB", 11), 0, Qt.AlignCenter)
    grid.addWidget(big, 0, 0, 2, 1)
    c1 = panel("#FFFFFF", border="#ECECF0", radius=16)
    c1v = QVBoxLayout(c1); c1v.setContentsMargins(6, 4, 6, 4); c1v.setSpacing(4)
    c1v.addWidget(label("录制模式", "#999", 11), 0, Qt.AlignCenter)
    c1v.addWidget(label("📷 图像录制", "#222", 13, True), 0, Qt.AlignCenter)
    grid.addWidget(c1, 0, 1)
    c2 = panel("#FF453A", radius=16)
    c2v = QVBoxLayout(c2); c2v.setContentsMargins(6, 4, 6, 4); c2v.setSpacing(4)
    c2v.addWidget(label("回放已开启", "#FFF", 13, True), 0, Qt.AlignCenter)
    grid.addWidget(c2, 0, 2)
    c3 = panel("#FFFFFF", border="#ECECF0", radius=16)
    c3v = QVBoxLayout(c3); c3v.setContentsMargins(6, 4, 6, 4); c3v.setSpacing(4)
    c3v.addWidget(label("悬浮窗口", "#999", 11), 0, Qt.AlignCenter)
    c3v.addWidget(label("可切换", "#222", 13, True), 0, Qt.AlignCenter)
    grid.addWidget(c3, 1, 1)
    c4 = panel("#FFFFFF", border="#ECECF0", radius=16)
    c4v = QVBoxLayout(c4); c4v.setContentsMargins(6, 4, 6, 4); c4v.setSpacing(4)
    c4v.addWidget(label("当前状态", "#999", 11), 0, Qt.AlignCenter)
    c4v.addWidget(label("空闲中", "#222", 13, True), 0, Qt.AlignCenter)
    grid.addWidget(c4, 1, 2)
    v.addLayout(grid)
    return card


def style4():  # 暗黑控制台
    card = panel("#11161F", border="#243040", radius=10)
    v = QVBoxLayout(card); v.setContentsMargins(24, 18, 24, 18); v.setSpacing(14)
    head = QHBoxLayout()
    head.addWidget(label("RECORD_CONTROL", "#E6EDF3", 14, True, 1))
    head.addStretch()
    head.addWidget(label("● REC READY", "#FF4D4D", 12, spacing=2))
    v.addLayout(head)
    line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background:#243040; border:none;")
    v.addWidget(line)
    row = QHBoxLayout(); row.setSpacing(22)
    row.addWidget(RecCircle(84, shape="rounded", plate="#0D1117", border="#22C55E",
                            border_w=1, dot="#22C55E", dot_ratio=0.4, square_dot=True, shadow=False))
    col = QVBoxLayout(); col.setSpacing(8)
    col.addWidget(label("-- 录制模式 --", "#58A6FF", 12))
    col.addWidget(PillBtn("📷 图像录制", bg="#0D1117", fg="#E6EDF3", hover="#1B2534", arrow=True, h=42))
    col.addStretch()
    row.addLayout(col); row.addStretch()
    v.addLayout(row)
    foot = QHBoxLayout(); foot.setSpacing(10)
    foot.addWidget(PillBtn("[●] 回放已开启", bg="#16241C", fg="#22C55E", hover="#1D3325", h=40, bold=False))
    foot.addWidget(PillBtn("[ ] 悬浮窗口", bg="#161C26", fg="#8B949E", hover="#1F2836", h=40, bold=False))
    foot.addStretch()
    v.addLayout(foot)
    return card


def style5():  # 录音室拟物
    card = panel("#33282A")
    v = QVBoxLayout(card); v.setContentsMargins(30, 24, 30, 24); v.setSpacing(18)
    v.addWidget(label("录 制 控 制", "#D4A373", 16, True, 5))
    row = QHBoxLayout(); row.setSpacing(30)
    row.addWidget(RecCircle(104, plate="#241C1E", border="#4A3B3D", border_w=2,
                            dot="#E5383B", ring="#C1121F", dot_ratio=0.66))
    col = QVBoxLayout(); col.setSpacing(8)
    col.addWidget(label("录 制 模 式", "#A99883", 12, spacing=3))
    col.addWidget(PillBtn("📷 图像录制", bg="#241C1E", fg="#F5E9D5", hover="#33262A", arrow=True, h=46))
    col.addStretch()
    row.addLayout(col); row.addStretch()
    v.addLayout(row)
    foot = QHBoxLayout(); foot.setSpacing(14)
    foot.addWidget(PillBtn("● 回放已开启", bg="#C1121F", fg="#FFF", hover="#D02230", h=44))
    foot.addWidget(PillBtn("悬浮窗口", bg="#241C1E", fg="#A99883", hover="#33262A", h=44, bold=False))
    foot.addStretch()
    v.addLayout(foot)
    return card


def style6():  # 渐变活力
    card = panel("#FFFFFF", radius=20)
    v = QVBoxLayout(card); v.setContentsMargins(30, 24, 30, 24); v.setSpacing(18)
    title = QLabel("录制控制")
    title.setStyleSheet("font-size:20px; font-weight:800; color:#8B5CF6; background:transparent; border:none;")
    v.addWidget(title)
    row = QHBoxLayout(); row.setSpacing(26)
    row.addWidget(RecCircle(96, shape="rounded", plate="#8B5CF6", border="transparent",
                            dot="#FFFFFF", dot_ratio=0.42, shadow=False))
    col = QVBoxLayout(); col.setSpacing(8)
    col.addWidget(label("录制模式", "#94A3B8", 13, True))
    col.addWidget(PillBtn("📷 图像录制", bg="#FDF2F8", fg="#7C3AED", hover="#F5E0F5", arrow=True, h=46, bold=True))
    col.addStretch()
    row.addLayout(col); row.addStretch()
    v.addLayout(row)
    foot = QHBoxLayout(); foot.setSpacing(12)
    foot.addWidget(PillBtn("● 回放已开启", grad=("#F43F5E", "#8B5CF6"), fg="#FFF", h=44))
    foot.addWidget(PillBtn("悬浮窗口", bg="#FDF2F8", fg="#8B5CF6", hover="#F5E0F5", h=44, bold=False))
    foot.addStretch()
    v.addLayout(foot)
    return card


def style7():  # 新拟态
    card = panel("#E0E5EC", radius=22)
    v = QVBoxLayout(card); v.setContentsMargins(32, 26, 32, 26); v.setSpacing(20)
    v.addWidget(label("录制控制", "#4A5568", 19, True))
    row = QHBoxLayout(); row.setSpacing(30)
    row.addWidget(RecCircle(100, plate="#E0E5EC", border="#CFD6E0", border_w=1,
                            dot="#FF6B6B", dot_ratio=0.55))
    col = QVBoxLayout(); col.setSpacing(9)
    col.addWidget(label("录制模式", "#8A94A6", 13))
    col.addWidget(PillBtn("📷 图像录制", bg="#E0E5EC", fg="#4A5568", hover="#D5DBE4", arrow=True, h=48, bold=False))
    col.addStretch()
    row.addLayout(col); row.addStretch()
    v.addLayout(row)
    foot = QHBoxLayout(); foot.setSpacing(16)
    foot.addWidget(PillBtn("● 回放已开启", bg="#FF6B6B", fg="#FFF", hover="#F55F5F", h=46))
    foot.addWidget(PillBtn("悬浮窗口", bg="#E0E5EC", fg="#8A94A6", hover="#D5DBE4", h=46, bold=False))
    foot.addStretch()
    v.addLayout(foot)
    return card


def style8():  # 状态横幅
    card = panel("#FFFFFF", border="#E2E8F0", radius=16)
    v = QVBoxLayout(card); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(16)
    banner = panel("#DC2626", radius=0)
    bv = QHBoxLayout(banner); bv.setContentsMargins(26, 14, 26, 14)
    bv.addWidget(label("录制控制", "#FFF", 16, True))
    bv.addStretch()
    bv.addWidget(label("● 录制就绪", "#FFF", 12, spacing=1))
    v.addWidget(banner)
    body = QWidget(); body.setStyleSheet("background:transparent; border:none;")
    bl = QHBoxLayout(body); bl.setContentsMargins(26, 6, 26, 0); bl.setSpacing(24)
    bl.addWidget(RecCircle(82, shape="rounded", plate="#FEF2F2", border="#FECACA",
                           dot="#DC2626", dot_ratio=0.4, square_dot=True, shadow=False))
    col = QVBoxLayout(); col.setSpacing(8)
    col.addWidget(label("录制模式", "#94A3B8", 12))
    col.addWidget(PillBtn("📷 图像录制", bg="#FFFFFF", fg="#334155", hover="#F1F5F9", arrow=True, h=44, bold=False))
    col.addStretch()
    bl.addLayout(col); bl.addStretch()
    v.addWidget(body)
    foot = QWidget(); foot.setStyleSheet("background:transparent; border:none;")
    fl = QHBoxLayout(foot); fl.setContentsMargins(26, 0, 26, 20); fl.setSpacing(10)
    fl.addWidget(PillBtn("● 回放已开启", bg="#334155", fg="#FFF", hover="#41556E", h=42))
    fl.addWidget(PillBtn("悬浮窗口", bg="#F1F5F9", fg="#475569", hover="#E2E8F0", h=42, bold=False))
    fl.addStretch()
    v.addWidget(foot)
    return card


def style9():  # 横向极简条
    card = panel("#FFFFFF", border="#ECECF0", radius=18)
    h = QHBoxLayout(card); h.setContentsMargins(24, 18, 24, 18); h.setSpacing(18)
    h.addWidget(RecCircle(60, plate="#111111", border="transparent", dot="#FF3B30", dot_ratio=0.36, shadow=False))
    mid = QVBoxLayout(); mid.setSpacing(4)
    mid.addWidget(label("录制控制", "#111", 15, True))
    mid.addWidget(label("回放已开启 · 模式：图像录制", "#FF3B30", 12))
    h.addLayout(mid); h.addStretch()
    h.addWidget(PillBtn("📷 图像录制 ▾", bg="#F5F5F7", fg="#333", hover="#EBEBF0", h=40, bold=False))
    h.addWidget(PillBtn("回放开", bg="#111111", fg="#FFF", hover="#2A2A2A", h=40))
    h.addWidget(PillBtn("悬浮窗", bg="#F5F5F7", fg="#333", hover="#EBEBF0", h=40, bold=False))
    return card


def style10():  # 左色带仪表盘
    card = panel("#FFFFFF", border="#E2E8F0", radius=18)
    h = QHBoxLayout(card); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
    side = panel("#0F172A", radius=0)
    side.setFixedWidth(150)
    sv = QVBoxLayout(side); sv.setSpacing(12)
    sv.addStretch()
    sv.addWidget(RecCircle(70, plate="transparent", border="#3B82F6", border_w=2,
                           dot="#60A5FA", dot_ratio=0.42, shadow=False), 0, Qt.AlignCenter)
    sv.addWidget(label("STANDBY", "#93C5FD", 12, spacing=3), 0, Qt.AlignCenter)
    sv.addStretch()
    h.addWidget(side)
    main = QWidget(); main.setStyleSheet("background:transparent; border:none;")
    mv = QVBoxLayout(main); mv.setContentsMargins(30, 24, 30, 24); mv.setSpacing(16)
    mv.addWidget(label("录制控制", "#0F172A", 18, True))
    mv.addWidget(label("录制模式", "#94A3B8", 12, True))
    mv.addWidget(PillBtn("📷 图像录制", bg="#F8FAFC", fg="#0F172A", hover="#EEF2F7", arrow=True, h=46, bold=False))
    mv.addStretch()
    foot = QHBoxLayout(); foot.setSpacing(12)
    foot.addWidget(PillBtn("● 回放已开启", bg="#2563EB", fg="#FFF", hover="#3B74F0", h=44))
    foot.addWidget(PillBtn("悬浮窗口", bg="#F1F5F9", fg="#475569", hover="#E2E8F0", h=44, bold=False))
    foot.addStretch()
    mv.addLayout(foot)
    h.addWidget(main)
    return card


STYLES = [
    ("样式 1 · 玻璃深色", "深蓝夜空底 + 青色霓虹圆环，科技感最强", style1),
    ("样式 2 · 极简苹果白", "白底红圆钮 + 苹果蓝药丸（当前已应用的就是这版）", style2),
    ("样式 3 · Bento 网格", "功能拆成信息格子，一屏看全所有状态", style3),
    ("样式 4 · 暗黑控制台", "终端风 + 荧光绿方钮，程序员味", style4),
    ("样式 5 · 录音室拟物", "复古录音棚，深棕底 + 红色胶环", style5),
    ("样式 6 · 渐变活力", "白卡 + 紫色圆角钮 + 玫红渐变按钮", style6),
    ("样式 7 · 新拟态", "米灰浮雕质感，柔和按压感", style7),
    ("样式 8 · 状态横幅", "顶部红色状态条，状态一眼可见", style8),
    ("样式 9 · 横向极简条", "压成一条工具栏，最省空间", style9),
    ("样式 10 · 左色带仪表盘", "深蓝侧栏 + 浅色主区，仪表盘布局", style10),
]


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { font-family: 'Microsoft YaHei'; }")

    root = QWidget()
    root.setWindowTitle("录制控制 · 10 种样式选型（挑好告诉我编号）")
    root.resize(960, 860)
    root.setStyleSheet("background:#EDEFF3;")

    outer = QVBoxLayout(root)
    tip = QLabel("↓ 往下滚动看全部 10 种，挑一个编号告诉我即可应用到主程序")
    tip.setStyleSheet("color:#666; font-size:14px; padding:10px 4px; background:transparent;")
    outer.addWidget(tip)

    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setStyleSheet("QScrollArea { border:none; background:transparent; }")
    inner = QWidget()
    inner.setStyleSheet("background:transparent;")
    lay = QVBoxLayout(inner)
    lay.setSpacing(10)
    lay.setContentsMargins(8, 0, 16, 24)

    for i, (name, desc, fn) in enumerate(STYLES, 1):
        title = QLabel(f"{name}　<small style='color:#999'>{desc}</small>")
        title.setStyleSheet("font-size:14px; font-weight:700; color:#444; background:transparent; padding:6px 2px 0 2px;")
        lay.addWidget(title)
        lay.addWidget(fn())

    area.setWidget(inner)
    outer.addWidget(area)
    root.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
