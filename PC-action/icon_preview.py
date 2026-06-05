"""
录制按钮样式预览 - 10种风格
运行此文件查看所有样式，选定后再应用到主程序
"""
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "PC-action-macOS"))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, pyqtProperty
from PyQt5.QtGui import (QPainter, QBrush, QPen, QColor, QFont, QFontDatabase,
                         QRadialGradient, QLinearGradient, QConicalGradient)

from design_system import TypographySystem


# ============================================================
# 样式1: 双环收音 ─ 白底 + 双同心圆环
# ============================================================
class Style1_DualRing(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._t_val = 0.0
        self._anim = QPropertyAnimation(self, b"_t")
        self._anim.setDuration(2000)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.start()

    def _get_t(self): return self._t_val
    def _set_t(self, v): self._t_val = v; self.update()
    _t = pyqtProperty(float, _get_t, _set_t)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s, cx = 120, 60
        # 白底圆角方形
        p.setPen(QPen(QColor("#E0E0E0"), 1.5))
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawRoundedRect(QRectF(3, 3, 114, 114), 24, 24)
        # 顶部柔光
        hl = QRadialGradient(cx, cx-30, 60)
        hl.setColorAt(0, QColor(255,255,255,160))
        hl.setColorAt(1, QColor(255,255,255,0))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(hl))
        p.drawRoundedRect(QRectF(3, 3, 114, 114), 24, 24)
        # 双环
        icx, icy = cx, cx-12
        r1 = 20 + 2*math.sin(self._t_val*math.pi*2)
        p.setPen(QPen(QColor("#1C1C1E"), 2.5)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(icx-r1, icy-r1, r1*2, r1*2))
        r2 = r1*0.6
        p.setPen(QPen(QColor("#1C1C1E"), 1.5))
        p.drawEllipse(QRectF(icx-r2, icy-r2, r2*2, r2*2))
        # 文字
        p.setPen(QColor("#1C1C1E"))
        f = QFont(TypographySystem.FONT_FAMILY, 13, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, cx+2, 110, cx-2), Qt.AlignCenter, "录制")


# ============================================================
# 样式2: 经典红圆 ─ macOS 经典红圆渐变
# ============================================================
class Style2_RedCircle(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._t_val = 0.0
        self._anim = QPropertyAnimation(self, b"_t")
        self._anim.setDuration(2000); self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0); self._anim.setLoopCount(-1); self._anim.start()

    def _get_t(self): return self._t_val
    def _set_t(self, v): self._t_val = v; self.update()
    _t = pyqtProperty(float, _get_t, _set_t)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = 60; r = 38 + 2*math.sin(self._t_val*math.pi*2)
        # 阴影
        sh = QRadialGradient(cx+2, cx+4, 50)
        sh.setColorAt(0, QColor(0,0,0,35)); sh.setColorAt(1, QColor(0,0,0,0))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(sh))
        p.drawEllipse(QRectF(cx-r+4, cx-r+6, r*2, r*2))
        # 红圆渐变
        g = QRadialGradient(cx-r*0.3, cx-r*0.3, r*1.5)
        g.setColorAt(0, QColor("#FF6961")); g.setColorAt(0.55, QColor("#FF3B30")); g.setColorAt(1, QColor("#C71D14"))
        p.setBrush(QBrush(g)); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx-r, cx-r, r*2, r*2))
        # 高光
        hl = QRadialGradient(cx-r*0.5, cx-r*0.7, r*0.6)
        hl.setColorAt(0, QColor(255,255,255,80)); hl.setColorAt(1, QColor(255,255,255,0))
        p.setBrush(QBrush(hl))
        p.drawEllipse(QRectF(cx-r, cx-r, r*2, r*2))
        # 文字
        p.setPen(QColor("#FFFFFF"))
        f = QFont(TypographySystem.FONT_FAMILY, 13, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, cx+5, 110, cx), Qt.AlignCenter, "录制")


# ============================================================
# 样式3: 圆角方红钮 ─ 圆角方形红色按钮
# ============================================================
class Style3_RoundRectRed(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(4, 4, 112, 112)
        # 阴影
        sh = QRadialGradient(62, 64, 60)
        sh.setColorAt(0, QColor(0,0,0,30)); sh.setColorAt(1, QColor(0,0,0,0))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(sh))
        p.drawRoundedRect(QRectF(6, 6, 112, 112), 28, 28)
        # 红色渐变底
        g = QLinearGradient(0, 0, 0, 120)
        g.setColorAt(0, QColor("#FF5A4A")); g.setColorAt(1, QColor("#D92B1E"))
        p.setBrush(QBrush(g)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(r, 28, 28)
        # 内白描边圆
        p.setPen(QPen(QColor(255,255,255,180), 2.5)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(28, 22, 64, 64))
        # 内圆
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawEllipse(QRectF(42, 36, 36, 36))
        # 文字
        p.setPen(QColor("#FFFFFF"))
        f = QFont(TypographySystem.FONT_FAMILY, 13, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, 65, 110, 50), Qt.AlignCenter, "录制")


# ============================================================
# 样式4: 简约白圆 ─ 纯白底 + 红色圆点
# ============================================================
class Style4_WhiteDot(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = 120; cx = 60
        # 白底圆
        p.setPen(QPen(QColor("#E8E8E8"), 1.5)); p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawRoundedRect(QRectF(3,3,114,114), 60, 60)
        # 红色圆点
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#FF3B30")))
        p.drawEllipse(QRectF(40, 34, 40, 40))
        # 文字
        p.setPen(QColor("#1C1C1E"))
        f = QFont(TypographySystem.FONT_FAMILY, 13, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, cx+5, 110, cx-5), Qt.AlignCenter, "录制")


# ============================================================
# 样式5: 发光环 ─ 暗底 + 发光圆环
# ============================================================
class Style5_GlowRing(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._t_val = 0.0
        self._anim = QPropertyAnimation(self, b"_t")
        self._anim.setDuration(1500); self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0); self._anim.setLoopCount(-1); self._anim.start()

    def _get_t(self): return self._t_val
    def _set_t(self, v): self._t_val = v; self.update()
    _t = pyqtProperty(float, _get_t, _set_t)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = 60
        glow = 10 + 5*math.sin(self._t_val*math.pi*2)
        # 暗色圆角方底
        p.setPen(QPen(QColor("#3A3A3C"), 1)); p.setBrush(QBrush(QColor("#2C2C2E")))
        p.drawRoundedRect(QRectF(3,3,114,114), 28, 28)
        # 发光环
        r = 32
        for i in range(8, 0, -1):
            a = max(5, 30 - i*3)
            p.setPen(QPen(QColor(255, 69, 58, a), 1))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(cx-r-glow-i, cx-r-glow-i-10, (r+glow+i)*2, (r+glow+i)*2))
        # 主环
        p.setPen(QPen(QColor("#FF453A"), 3))
        p.drawEllipse(QRectF(cx-r, cx-r-10, r*2, r*2))
        # 文字
        p.setPen(QColor(255,255,255,200))
        f = QFont(TypographySystem.FONT_FAMILY, 13, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, cx+2, 110, cx-2), Qt.AlignCenter, "录制")


# ============================================================
# 样式6: 胶囊按钮 ─ 横向药丸形 + 文字内置
# ============================================================
class Style6_Capsule(QPushButton):
    def __init__(self, parent=None):
        super().__init__("⏺ 录制", parent)
        self.setFixedSize(140, 56)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # 渐变背景
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor("#FF5A4A")); g.setColorAt(1, QColor("#E5352B"))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(g))
        p.drawRoundedRect(QRectF(0,0,w,h), h/2, h/2)
        # 左侧小圆点
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(255,255,255,220)))
        p.drawEllipse(QRectF(18, h/2-8, 16, 16))
        # 阴影
        f = QFont(TypographySystem.FONT_FAMILY, 16, QFont.DemiBold)
        p.setFont(f); p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(42, 0, w-48, h), Qt.AlignVCenter|Qt.AlignLeft, "录制")


# ============================================================
# 样式7: 霓虹圆环 ─ 暗背景 + 青色霓虹环
# ============================================================
class Style7_NeonRing(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._t_val = 0.0
        self._anim = QPropertyAnimation(self, b"_t")
        self._anim.setDuration(3000); self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0); self._anim.setLoopCount(-1); self._anim.start()

    def _get_t(self): return self._t_val
    def _set_t(self, v): self._t_val = v; self.update()
    _t = pyqtProperty(float, _get_t, _set_t)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = 60
        # 暗底
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#1A1A1E")))
        p.drawRoundedRect(QRectF(3,3,114,114), 28, 28)
        # 旋转环
        start = int(self._t_val * 360 * 16)
        p.setPen(QPen(QColor("#00D4FF"), 3, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(QRectF(22, 12, 76, 76), start, 270*16)
        # 残影
        p.setPen(QPen(QColor(0, 212, 255, 60), 2))
        p.drawArc(QRectF(22, 12, 76, 76), start+180*16, 90*16)
        # 中心小圆
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#00D4FF")))
        p.drawEllipse(QRectF(52, 42, 16, 16))
        # 文字
        p.setPen(QColor(255,255,255,180))
        f = QFont(TypographySystem.FONT_FAMILY, 12, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, cx+2, 110, cx-2), Qt.AlignCenter, "录制")


# ============================================================
# 样式8: 分层圆 ─ 白底 + 多层嵌套圆
# ============================================================
class Style8_LayeredCircle(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s, cx = 120, 60
        # 白底圆角方
        p.setPen(QPen(QColor("#E0E0E0"), 1)); p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawRoundedRect(QRectF(3,3,114,114), 28, 28)
        # 外层大环
        p.setPen(QPen(QColor("#FF453A"), 2)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(24, 14, 72, 72))
        # 中层环
        p.setPen(QPen(QColor("#FF453A"), 1.5))
        p.drawEllipse(QRectF(32, 22, 56, 56))
        # 内层实心
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#FF3B30")))
        p.drawEllipse(QRectF(46, 36, 28, 28))
        # 文字
        p.setPen(QColor("#1C1C1E"))
        f = QFont(TypographySystem.FONT_FAMILY, 13, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, cx+2, 110, cx-2), Qt.AlignCenter, "录制")


# ============================================================
# 样式9: 极简线条 ─ 只画一个细线圆环，无填充
# ============================================================
class Style9_MinimalLine(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._t_val = 0.0
        self._anim = QPropertyAnimation(self, b"_t")
        self._anim.setDuration(2500); self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0); self._anim.setLoopCount(-1); self._anim.start()

    def _get_t(self): return self._t_val
    def _set_t(self, v): self._t_val = v; self.update()
    _t = pyqtProperty(float, _get_t, _set_t)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = 60
        a = 40 + 20*math.sin(self._t_val*math.pi*2)
        # 几乎透明底
        p.setPen(QPen(QColor(200,200,200,80), 1)); p.setBrush(QBrush(QColor(255,255,255,30)))
        p.drawRoundedRect(QRectF(3,3,114,114), 28, 28)
        # 单个细环
        r = 32 + 3*math.sin(self._t_val*math.pi*2)
        p.setPen(QPen(QColor("#1C1C1E"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(cx-r, cx-r-10, r*2, r*2))
        # 小点缀
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#1C1C1E")))
        p.drawEllipse(QRectF(cx-3, cx-3-10, 6, 6))
        # 文字
        p.setPen(QColor("#1C1C1E"))
        f = QFont(TypographySystem.FONT_FAMILY, 12, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, cx+2, 110, cx-2), Qt.AlignCenter, "录制")


# ============================================================
# 样式10: 多彩渐变 ─ 渐变底色 + 白色图标
# ============================================================
class Style10_GradientBG(QPushButton):
    def __init__(self, parent=None):
        super().__init__("录制", parent)
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = 60
        # 渐变背景
        g = QConicalGradient(cx, cx, 0)
        g.setColorAt(0, QColor("#667EEA")); g.setColorAt(0.5, QColor("#764BA2"))
        g.setColorAt(1, QColor("#667EEA"))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(g))
        p.drawRoundedRect(QRectF(3,3,114,114), 28, 28)
        # 白色半透明环
        p.setPen(QPen(QColor(255,255,255,180), 2.5)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(28, 18, 64, 64))
        # 白色内环
        p.setPen(QPen(QColor(255,255,255,120), 1.5))
        p.drawEllipse(QRectF(36, 26, 48, 48))
        # 白色中心
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(255,255,255,200)))
        p.drawEllipse(QRectF(50, 40, 20, 20))
        # 文字
        p.setPen(QColor(255,255,255,230))
        f = QFont(TypographySystem.FONT_FAMILY, 13, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(5, cx+2, 110, cx-2), Qt.AlignCenter, "录制")


# ============================================================
STYLES = [
    ("1. 双环收音", "白底+双同心圆环\n简洁克制", Style1_DualRing),
    ("2. 经典红圆", "macOS经典红圆\n渐变立体", Style2_RedCircle),
    ("3. 圆角方钮", "红底+白描边圆\n有力醒目", Style3_RoundRectRed),
    ("4. 简约白圆", "纯白圆底+红点\n极简干净", Style4_WhiteDot),
    ("5. 发光环", "暗底+红色光晕\n夜间氛围", Style5_GlowRing),
    ("6. 胶囊按钮", "横向药丸形\n紧凑好用", Style6_Capsule),
    ("7. 霓虹圆环", "暗底+青色旋转\n科技感", Style7_NeonRing),
    ("8. 分层圆", "白底+三层嵌套\n层次丰富", Style8_LayeredCircle),
    ("9. 极简线条", "透明底+细线环\n极致简约", Style9_MinimalLine),
    ("10. 多彩渐变", "渐变紫底+白环\n绚丽出彩", Style10_GradientBG),
]


class PreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("录制按钮样式预览 - 请选择你喜欢的风格")
        self.setStyleSheet("background-color: #F5F5F7;")
        self.resize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 28, 32, 28)

        title = QLabel("选择你喜欢的录制按钮样式")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #1C1C1E; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel("点击「确定选择」后样式会被应用到主程序")
        subtitle.setStyleSheet("font-size: 13px; color: #8E8E93; background: transparent;")
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(20)

        self.selected_index = None
        self.cards = []

        for i, (name, desc, cls) in enumerate(STYLES):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border-radius: 16px;
                    border: 2px solid #E8E8E8;
                }
                QFrame:hover {
                    border-color: #007AFF;
                }
            """)
            card.setCursor(Qt.PointingHandCursor)
            card.setFixedSize(240, 260)

            cl = QVBoxLayout(card)
            cl.setSpacing(8)
            cl.setContentsMargins(16, 16, 16, 16)
            cl.setAlignment(Qt.AlignCenter)

            # 按钮预览
            btn = cls()
            btn.setEnabled(False)  # 禁用交互，纯展示
            wrapper = QWidget()
            wrapper.setFixedSize(140, 140)
            wrapper.setStyleSheet("background: transparent; border: none;")
            wl = QHBoxLayout(wrapper)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setAlignment(Qt.AlignCenter)
            wl.addWidget(btn)
            cl.addWidget(wrapper, 0, Qt.AlignCenter)

            # 名称
            nl = QLabel(name)
            nl.setStyleSheet("font-size: 15px; font-weight: 600; color: #1C1C1E; background: transparent;")
            nl.setAlignment(Qt.AlignCenter)
            cl.addWidget(nl)

            # 描述
            dl = QLabel(desc)
            dl.setStyleSheet("font-size: 11px; color: #8E8E93; background: transparent; line-height: 1.3;")
            dl.setAlignment(Qt.AlignCenter)
            cl.addWidget(dl)

            def make_click(idx, card_frame):
                def handler(ev):
                    self.select_style(idx, card_frame)
                return handler

            card.mousePressEvent = make_click(i, card)
            self.cards.append(card)
            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid, 1)

        # 底部确认按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.confirm_btn = QPushButton("确定选择 (未选择)")
        self.confirm_btn.setFixedSize(200, 48)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0062CC; }
            QPushButton:disabled { background-color: #C7C7CC; color: rgba(255,255,255,0.6); }
        """)
        self.confirm_btn.clicked.connect(self.on_confirm)
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 状态栏
        self.status_label = QLabel("点击卡片选择样式")
        self.status_label.setStyleSheet("font-size: 13px; color: #8E8E93; background: transparent;")
        layout.addWidget(self.status_label)

    def select_style(self, idx, card):
        self.selected_index = idx
        for i, c in enumerate(self.cards):
            if i == idx:
                c.setStyleSheet("""
                    QFrame {
                        background-color: #FFFFFF;
                        border-radius: 16px;
                        border: 3px solid #007AFF;
                    }
                """)
            else:
                c.setStyleSheet("""
                    QFrame {
                        background-color: #FFFFFF;
                        border-radius: 16px;
                        border: 2px solid #E8E8E8;
                    }
                """)
        name, desc, _ = STYLES[idx]
        self.status_label.setText(f"已选择: {name} — {desc.split(chr(10))[0]}")
        self.confirm_btn.setText(f"✓ 确定选择: {name}")
        self.confirm_btn.setEnabled(True)

    def on_confirm(self):
        if self.selected_index is None:
            return
        name, desc, cls = STYLES[self.selected_index]
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "已选择",
            f"你选择了: {name}\n\n{desc}\n\n请记住编号，在对话中告知我即可应用。"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    w = PreviewWindow()
    w.show()
    sys.exit(app.exec_())