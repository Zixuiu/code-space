import os
if os.name == "nt":
    os.environ["QT_ENABLE_DIRECTWRITE"] = "1"

import os
import json
import math
import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QScrollArea, QFrame,
    QSizePolicy, QLineEdit, QGridLayout, QGraphicsOpacityEffect,
    QCheckBox, QTextEdit, QComboBox, QSlider, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QSystemTrayIcon,
    QMessageBox, QPlainTextEdit, QListWidget, QListWidgetItem, QInputDialog,
    QAbstractItemView, QShortcut, QDialog, QGraphicsDropShadowEffect, QStyle
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, QRect, QRectF
)
from PyQt5.QtGui import (
    QGuiApplication,
    QColor, QPainter, QBrush, QPen, QFont, QFontDatabase, QIcon, QPixmap,
    QKeySequence, QLinearGradient, QRadialGradient, QRegion, QPainterPath
)

from app import AutoRecorderApp
from utils import get_screen_size, load_json_data, save_json_data
from design_system import (
    TypographySystem, SpacingSystem, BorderRadiusSystem,
    ColorPalette, ShadowSystem, ButtonSize
)
from theme_generator import generate_macos_theme

# 兼容旧代码的颜色常量
THEME_PRIMARY = ColorPalette.PRIMARY
THEME_SECONDARY = ColorPalette.INFO
THEME_ACCENT = ColorPalette.PRIMARY
THEME_BG = ColorPalette.BG_MAIN
THEME_CARD = ColorPalette.BG_CARD
THEME_TEXT = ColorPalette.TEXT_PRIMARY
THEME_MUTED = ColorPalette.TEXT_SECONDARY
THEME_BORDER = ColorPalette.BORDER_DEFAULT


class MacOSColors:
    """macOS 颜色定义 - 基于设计系统"""
    ACCENT = ColorPalette.PRIMARY
    SYSTEM_GREEN = ColorPalette.SUCCESS
    SYSTEM_RED = ColorPalette.ERROR
    SYSTEM_ORANGE = ColorPalette.WARNING
    SYSTEM_PURPLE = "#BF5AF2"
    SYSTEM_PINK = "#FF375F"
    SYSTEM_GRAY = ColorPalette.TEXT_SECONDARY
    SYSTEM_GRAY2 = ColorPalette.GRAY_600
    SYSTEM_GRAY3 = ColorPalette.GRAY_700
    SYSTEM_GRAY4 = ColorPalette.GRAY_800
    SYSTEM_GRAY5 = ColorPalette.GRAY_900
    SYSTEM_GRAY6 = ColorPalette.GRAY_500
    SYSTEM_YELLOW = "#FFD60A"

    WINDOW_BG = ColorPalette.BG_MAIN
    CARD_BG = ColorPalette.BG_CARD
    SIDEBAR_BG = ColorPalette.BG_SIDEBAR
    TOOLBAR_BG = ColorPalette.BG_TOOLBAR

    TEXT_PRIMARY = ColorPalette.TEXT_PRIMARY
    TEXT_SECONDARY = ColorPalette.TEXT_SECONDARY
    SEPARATOR = ColorPalette.SEPARATOR
    ACCENT_BG = ColorPalette.PRIMARY_BG


class MacOSSidebarItem(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.is_selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setMaximumHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(12)

        self.icon_label = QLabel(icon)
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(text)
        layout.addWidget(self.text_label)
        layout.addStretch()

        self.update_style()

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        """使用设计系统更新样式"""
        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border: none;
                    outline: none;
                }
            """)
            self.icon_label.setStyleSheet(f"""
                color: {MacOSColors.ACCENT};
                font-size: {TypographySystem.SIZE_LG}px;
                border: none;
            """)
            self.text_label.setStyleSheet(f"""
                color: {MacOSColors.ACCENT};
                font-size: {TypographySystem.SIZE_LG}px;
                font-weight: {TypographySystem.WEIGHT_BOLD};
                font-family: {TypographySystem.FONT_FAMILY};
                border: none;
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                    outline: none;
                }}
                QFrame:hover {{
                    background-color: {MacOSColors.ACCENT_BG};
                }}
            """)
            self.icon_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: {TypographySystem.SIZE_LG}px;
                border: none;
            """)
            self.text_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: {TypographySystem.SIZE_LG}px;
                font-weight: {TypographySystem.WEIGHT_REGULAR};
                font-family: {TypographySystem.FONT_FAMILY};
                border: none;
            """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class MacOSSidebar(QWidget):
    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border-right: 1px solid {MacOSColors.SEPARATOR};
                border-bottom-left-radius: 28px;
                border-bottom-left-radius: 28px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 28, 12, 16)
        layout.setSpacing(2)

        title = QLabel("导航菜单")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: {TypographySystem.SIZE_XS}px;
            font-weight: {TypographySystem.WEIGHT_SEMIBOLD};
            letter-spacing: 2px;
            padding: 0 {SpacingSystem.SM}px;
            margin-bottom: {SpacingSystem.SM}px;
            font-family: {TypographySystem.FONT_FAMILY};
        """)
        layout.addWidget(title)

        self.items = []
        nav_items = [
            ("\U0001f4ca", "录制控制"),
            ("\U0001f4c1", "流程管理"),
            ("\U0001f3af", "组合技"),
            ("⚙️", "设置"),
            ("📖", "使用帮助"),
        ]

        for i, (icon, text) in enumerate(nav_items):
            item = MacOSSidebarItem(icon, text)
            item.clicked.connect(lambda checked=False, idx=i: self.set_active_tab(idx))
            self.items.append(item)
            layout.addWidget(item)

        layout.addStretch()

        self.set_active_tab(0)

    def set_active_tab(self, index):
        for i, item in enumerate(self.items):
            item.set_selected(i == index)
        self.tab_changed.emit(index)

    def set_username(self, username):
        pass


class MacOSCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {MacOSColors.CARD_BG};
                border-radius: 12px;
            }}
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 5))
        painter.drawRoundedRect(1, 2, self.width() - 3, self.height() - 2, 12, 12)
        painter.setBrush(QColor(MacOSColors.CARD_BG))
        painter.drawRoundedRect(0, 0, self.width() - 2, self.height() - 2, 12, 12)
        painter.end()


class MacOSButton(QPushButton):
    """主按钮 - iOS 风格圆润样式

    不在按钮本体上挂 QGraphicsDropShadowEffect：
    该 Effect 会让按钮渲染到离屏 buffer，导致 :hover 状态下颜色显示异常（变白）。
    阴影由调用方在 _attach_button_shadow() 里挂到外层 QFrame 容器上。
    """
    def __init__(self, text="", color=MacOSColors.ACCENT, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        self.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        # 移除自动填充背景，避免与样式表冲突
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        # 确保颜色值正确处理透明度
        hover_color = self._adjust_color_opacity(color, 0.93)
        pressed_color = self._adjust_color_opacity(color, 0.8)
        disabled_color = self._adjust_color_opacity(color, 0.4)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: {BorderRadiusSystem.MD}px;
                font-size: {TypographySystem.SIZE_BASE}px;
                font-weight: {TypographySystem.WEIGHT_SEMIBOLD};
                font-family: {TypographySystem.FONT_FAMILY};
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
                min-height: {ButtonSize.HEIGHT_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                padding-top: 2px;
            }}
            QPushButton:disabled {{
                background-color: {disabled_color};
                color: rgba(255, 255, 255, 0.7);
            }}
        """)
    
    @staticmethod
    def _adjust_color_opacity_static(color_hex, opacity):
        """调整颜色透明度，返回有效的8位十六进制颜色值"""
        color_hex = color_hex.lstrip('#')
        if len(color_hex) == 6:
            # 标准6位颜色，添加透明度
            alpha = hex(int(opacity * 255))[2:].upper().zfill(2)
            return f"#{color_hex}{alpha}"
        return color_hex
    
    def _adjust_color_opacity(self, color_hex, opacity):
        """调整颜色透明度，返回有效的8位十六进制颜色值"""
        return MacOSButton._adjust_color_opacity_static(color_hex, opacity)


class MacOSDestructiveButton(QPushButton):
    """危险按钮 - 红色破坏性操作（用于停止、删除等）"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        self.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        color = MacOSColors.SYSTEM_RED
        hover_color = MacOSButton._adjust_color_opacity_static(color, 0.93)
        pressed_color = MacOSButton._adjust_color_opacity_static(color, 0.8)
        disabled_color = MacOSButton._adjust_color_opacity_static(color, 0.4)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: {BorderRadiusSystem.MD}px;
                font-size: {TypographySystem.SIZE_BASE}px;
                font-weight: {TypographySystem.WEIGHT_SEMIBOLD};
                font-family: {TypographySystem.FONT_FAMILY};
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
                min-height: {ButtonSize.HEIGHT_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                padding-top: 2px;
            }}
            QPushButton:disabled {{
                background-color: {disabled_color};
                color: rgba(255, 255, 255, 0.7);
            }}
        """)


class MacOSSecondaryButton(QPushButton):
    """次要按钮 - iOS 风格圆润样式"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        self.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: #8E8E93;
                border: 1px solid #D1D1D6;
                border-radius: {BorderRadiusSystem.MD}px;
                font-size: {TypographySystem.SIZE_BASE}px;
                font-weight: {TypographySystem.WEIGHT_MEDIUM};
                font-family: {TypographySystem.FONT_FAMILY};
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
                min-height: {ButtonSize.HEIGHT_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: #F0F0F2;
                color: #6E6E73;
            }}
            QPushButton:pressed {{
                background-color: #E8E8ED;
                padding-top: 2px;
            }}
            QPushButton:disabled {{
                background-color: #F2F2F7;
                color: rgba(0, 0, 0, 0.3);
            }}
        """)


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 8:
        hex_color = hex_color[:6]
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _attach_button_shadow(button, color_hex, blur_radius=18, offset_y=4, alpha=70):
    """把按钮的阴影挂到外层 QFrame 容器上，避免 :hover 失效。

    用法（在调用方创建按钮并 addWidget 之后调用）：
        btn = MacOSButton("+ 新建组合技", MacOSColors.ACCENT)
        layout.addWidget(btn)
        _attach_button_shadow(btn, MacOSColors.ACCENT)
    """
    try:
        parent = button.parentWidget()
        if parent is None:
            return
        layout = parent.layout()
        if layout is None:
            return
        # 找到按钮在父布局中的位置
        index = -1
        for i in range(layout.count()):
            if layout.itemAt(i).widget() is button:
                index = i
                break
        if index < 0:
            return
        # 取出按钮
        layout.removeWidget(button)
        # 创建外层容器
        container = QFrame(parent)
        container.setAttribute(Qt.WA_TranslucentBackground)
        cl = QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.addWidget(button)
        # 阴影挂在外层容器
        r, g, b = _hex_to_rgb(color_hex)
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(r, g, b, alpha))
        shadow.setOffset(0, offset_y)
        container.setGraphicsEffect(shadow)
        # 把容器放回原位置
        layout.insertWidget(index, container)
    except Exception as e:
        print(f"[MacOSButton] 阴影挂载失败（不影响功能）: {e}")


class RoundedRecordButton(QPushButton):
    """霓虹圆环风格录制按钮

    尺寸: 130x130 圆角方形 (圆角 28px)
    空闲态: 暗底 + 青色旋转弧环 + 中心青点
    录制态: 暗底 + 红色旋转弧环 + 中心红点 + 脉冲
    """
    BUTTON_SIZE = 130
    CORNER_RADIUS = 28

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._hovered = False
        self._pressed = False
        self._is_recording = False
        self._t = 0.0

        # 旋转/脉冲动画
        self._anim = QPropertyAnimation(self, b"_anim_progress")
        self._anim.setDuration(2000)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.start()

    # ---------------- Qt 属性 ----------------
    def _get_t(self) -> float: return self._t
    def _set_t(self, v: float):
        self._t = v; self.update()
    _anim_progress = pyqtProperty(float, _get_t, _set_t)

    # ---------------- 公开 API ----------------
    def set_is_recording(self, recording: bool):
        self._is_recording = recording
        self.update()

    def set_recording(self, recording: bool): self.set_is_recording(recording)
    def set_recording_state(self, state: bool): self.set_is_recording(state)
    def get_is_recording(self) -> bool: return self._is_recording

    def setText(self, text):
        super().setText(text); self.update()

    # ---------------- 鼠标事件 ----------------
    def enterEvent(self, event):
        self._hovered = True; self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False; self._pressed = False; self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True; self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False; self.update()
        super().mouseReleaseEvent(event)

    # ---------------- 绘制 ----------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        s = self.BUTTON_SIZE
        cx = s / 2.0
        cr = self.CORNER_RADIUS

        # 缩放
        scale = 0.96 if self._pressed else (1.03 if self._hovered else 1.0)
        ss = s * scale
        off = (s - ss) / 2.0
        rect = QRectF(off, off, ss, ss)

        # ----- 1. 阴影 -----
        sh_rect = QRectF(off + 2, off + 4, ss, ss)
        sh_a = 30 if not self._is_recording else 40
        sh = QRadialGradient(cx + 2, cx + 4, s * 0.55)
        sh.setColorAt(0.0, QColor(0, 0, 0, sh_a))
        sh.setColorAt(0.6, QColor(0, 0, 0, sh_a // 2))
        sh.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(sh))
        painter.drawRoundedRect(sh_rect, cr * scale, cr * scale)

        # ----- 2. 暗底 -----
        if self._hovered:
            bg = QColor("#222226")
        else:
            bg = QColor("#1A1A1E")
        bd = QColor("#3A3A3C")
        painter.setPen(QPen(bd, 1.5))
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(rect, cr * scale, cr * scale)

        # ----- 3. 霓虹旋转弧环 (正圆) -----
        ring_margin = 22
        ring_size = ss - ring_margin * 2
        ring_off = off + ring_margin
        ring_rect = QRectF(ring_off, ring_off, ring_size, ring_size)
        span = 270 * 16
        start = int(self._t * 360 * 16) - span // 2

        # 颜色: 空闲=青, 录制=红
        main_color = QColor("#FF453A") if self._is_recording else QColor("#00D4FF")

        # 残影弧 (全周淡色)
        painter.setPen(QPen(QColor(0, 212, 255, 30) if not self._is_recording else QColor(255, 69, 58, 30), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(ring_rect, 0, 360 * 16)

        # 主弧
        painter.setPen(QPen(main_color, 2.5, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(ring_rect, start, span)

        # 残影尾迹 (反向 90°)
        trail_alpha = 50 if not self._is_recording else 40
        if self._is_recording:
            trail_color = QColor(255, 69, 58, trail_alpha)
        else:
            trail_color = QColor(0, 212, 255, trail_alpha)
        painter.setPen(QPen(trail_color, 2.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(ring_rect, start + span, 90 * 16)

        # 录制中: 脉冲呼吸
        if self._is_recording:
            pulse_alpha = int(20 + 25 * (0.5 + 0.5 * math.sin(self._t * math.pi * 4)))
            painter.setPen(QPen(QColor(255, 69, 58, pulse_alpha), 2, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(ring_rect, start, 360 * 16)

        # ----- 4. 中心小圆 -----
        dot_r = 7
        dot_color = QColor("#FF453A") if self._is_recording else QColor("#00D4FF")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(QRectF(cx - dot_r, cx - dot_r, dot_r * 2, dot_r * 2))

        # 中心发光
        glow_r = dot_r + 4 + 2 * (0.5 + 0.5 * math.sin(self._t * math.pi * 2))
        glow_a = int(15 + 15 * (0.5 + 0.5 * math.sin(self._t * math.pi * 2)))
        painter.setPen(QPen(QColor(dot_color.red(), dot_color.green(), dot_color.blue(), glow_a), 1))
        painter.setBrush(Qt.NoBrush)


class RoundedPillButton(QPushButton):
    """自绘的 iOS 药丸形按钮 - paintEvent 保证所有平台都是绝对圆润"""
    def __init__(self, text="", color_top="#5AC8FA", color_mid="#007AFF", color_bottom="#0062CC",
                 text_color="white", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False
        self._pressed = False
        self._color_top = color_top
        self._color_mid = color_mid
        self._color_bottom = color_bottom
        self._text_color = text_color
        # 透明背景让 paintEvent 自由绘制
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        # 留 4px 给阴影,让按钮看起来更立体
        self.setContentsMargins(0, 2, 0, 6)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """自绘:渐变背景 + 完美药丸形 + 文字"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 药丸形:圆角半径 = 高度的一半
        rect = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 2.0

        # 渐变背景
        gradient = QLinearGradient(0, 0, 0, self.height())
        if self._pressed:
            gradient.setColorAt(0.0, QColor(self._darken(self._color_top, 0.85)))
            gradient.setColorAt(1.0, QColor(self._darken(self._color_bottom, 0.85)))
        elif self._hovered:
            gradient.setColorAt(0.0, QColor(self._lighten(self._color_top)))
            gradient.setColorAt(1.0, QColor(self._lighten(self._color_bottom)))
        else:
            gradient.setColorAt(0.0, QColor(self._color_top))
            gradient.setColorAt(0.5, QColor(self._color_mid))
            gradient.setColorAt(1.0, QColor(self._color_bottom))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, radius, radius)

        # 文字
        painter.setPen(QColor(self._text_color))
        font = QFont("SimHei" if sys.platform == "win32" else "PingFang SC")
        font.setPixelSize(16)
        font.setWeight(QFont.Medium)
        font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
        font.setHintingPreference(QFont.PreferNoHinting)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.text())

    @staticmethod
    def _lighten(hex_color, factor=1.12):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02X}{g:02X}{b:02X}"

    @staticmethod
    def _darken(hex_color, factor=0.85):
        return RoundedPillButton._lighten(hex_color, factor)


class MacOSToolbar(QWidget):
    _drag_pos = None  # 修复：提前初始化，防止 mouseMoveEvent 先被调用时报错
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setStyleSheet(f"""
            MacOSToolbar {{
                background-color: {MacOSColors.TOOLBAR_BG};
                border-bottom: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 28px 28px 0 0;
                }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)

        controls = QWidget()
        controls.setAttribute(Qt.WA_TranslucentBackground)
        controls.setStyleSheet("background-color: transparent;")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        self.min_btn = QFrame()
        self.min_btn.setFixedSize(16, 16)
        self.min_btn.setStyleSheet('QFrame{background-color:%s;border:none;border-radius:8px;}QFrame:hover{background-color:#FFBD3A;}'%MacOSColors.SYSTEM_YELLOW)
        controls_layout.addWidget(self.min_btn)
        self.max_btn = QFrame()
        self.max_btn.setFixedSize(16, 16)
        self.max_btn.setStyleSheet('QFrame{background-color:%s;border:none;border-radius:8px;}QFrame:hover{background-color:#28C840;}'%MacOSColors.SYSTEM_GREEN)
        controls_layout.addWidget(self.max_btn)
        self.close_btn = QFrame()
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setStyleSheet('QFrame{background-color:%s;border:none;border-radius:8px;}QFrame:hover{background-color:#FF6B5E;}'%MacOSColors.SYSTEM_RED)
        controls_layout.addWidget(self.close_btn)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: {TypographySystem.SIZE_MD}px;
            font-weight: {TypographySystem.WEIGHT_SEMIBOLD};
            font-family: {TypographySystem.FONT_FAMILY};
        """)
        layout.addWidget(self.title_label)
        layout.addStretch()

        layout.addWidget(controls)

    def mousePressEvent(self, e):
        if self.close_btn.underMouse():
            self.window().close()
        elif self.min_btn.underMouse():
            self.window().showMinimized()
        elif self.max_btn.underMouse():
            w = self.window()
            if w.isMaximized():
                w.showNormal()
            else:
                w.showMaximized()
        elif e.button() == Qt.LeftButton:
            MacOSToolbar._drag_pos = e.globalPos() - self.window().frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and MacOSToolbar._drag_pos:
            self.window().move(e.globalPos() - MacOSToolbar._drag_pos)
        super().mouseMoveEvent(e)

    def set_title(self, title):
        self.title_label.setText(title)


class MacOSAutoRecorderApp(AutoRecorderApp):
    def __init__(self, username=None, login_manager=None):
        self._initializing = True
        if username is None:
            username = "macOS用户"
        if login_manager is not None:
            if login_manager.current_user is None:
                login_manager.current_user = username
            # 也设置用户名属性
            login_manager.username = username
        super().__init__(username, login_manager)
        # 双重保险：确保登录状态不为空
        if self.login_manager.current_user is None:
            self.login_manager.current_user = username
        if self.current_user is None:
            self.current_user = username
        self._initializing = False
        self.is_recording = False

    def run_selected_combo_skills(self, table_widget):
        """macOS版本：批量运行选中的组合技"""
        try:
            selected_skills = []
            for row in range(table_widget.rowCount()):
                check_item = table_widget.item(row, 0)
                if check_item and check_item.checkState() == Qt.Checked:
                    skill = check_item.data(Qt.UserRole)
                    if skill:
                        selected_skills.append(skill)

            if not selected_skills:
                self.show_beautiful_message('information', "提示", "请先勾选要启动的组合技（勾选第一列的复选框）")
                return

            self.showMinimized()

            from image_recognition import clear_image_cache
            clear_image_cache()

            normal_skills = [s for s in selected_skills if not s.get('monitor_mode', False)]
            monitor_skills = [s for s in selected_skills if s.get('monitor_mode', False)]

            from app import ComboSkillRunner
            import threading as _threading

            normal_runners = []
            for skill in normal_skills:
                skill_name = skill.get('name', '未命名')
                skill_id = skill.get('name', '')

                if skill_id in self.runners and self.runners[skill_id].isRunning():
                    continue

                if skill_id in self.runners:
                    old_runner = self.runners[skill_id]
                    if not old_runner.isRunning():
                        del self.runners[skill_id]

                runner = ComboSkillRunner(skill, self)
                runner.skill_id = skill_id
                self.runners[skill_id] = runner
                normal_runners.append(runner)

                _sid = skill_id
                runner._on_finished = lambda success, msg, sid=_sid: QTimer.singleShot(0, lambda: self._on_combo_skill_finished(success, msg, sid))
                runner._on_step = lambda step_info, sid=_sid: QTimer.singleShot(0, lambda: self._on_combo_step_changed(step_info, sid))

                _t = _threading.Thread(target=runner.run, daemon=True)
                runner._exec_thread = _t
                _t.start()

            # 监控组合技
            if normal_runners:
                target_runner = normal_runners[0]
                for skill in monitor_skills:
                    skill_name = skill.get('name', '未命名')
                    skill_id = skill.get('name', '')

                    if skill_id in self.runners and self.runners[skill_id].isRunning():
                        continue

                    runner = ComboSkillRunner(skill, self)
                    runner.skill_id = skill_id
                    runner.monitor_mode = True
                    runner.monitor_target_runner = target_runner
                    self.runners[skill_id] = runner

                    _sid = skill_id
                    runner._on_finished = lambda success, msg, sid=_sid: QTimer.singleShot(0, lambda: self._on_combo_skill_finished(success, msg, sid))
                    runner._on_step = lambda step_info, sid=_sid: QTimer.singleShot(0, lambda: self._on_combo_step_changed(step_info, sid))

                    _t = _threading.Thread(target=runner.run, daemon=True)
                    runner._exec_thread = _t
                    _t.start()

            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[MACOS COMBO] 运行组合技失败: {e}")

    def run_combo_skill_in_tab(self, skill):
        """在macOS组合技tab页中运行单个组合技"""
        try:
            skill_name = skill.get('name', '未命名')
            skill_id = skill.get('name', '')

            if skill_id in self.runners and self.runners[skill_id].isRunning():
                self.show_beautiful_message('warning', "提示", f"组合技 '{skill_name}' 正在运行中，请先停止后再执行")
                return

            max_parallel = 3
            running_count = len([r for r in self.runners.values() if r.isRunning()])
            if running_count >= max_parallel:
                self.show_beautiful_message('warning', "提示", f"最多同时运行{max_parallel}个组合技，当前已有{running_count}个在运行")
                return

            if skill_id in self.runners:
                old_runner = self.runners[skill_id]
                if not old_runner.isRunning():
                    del self.runners[skill_id]

            from image_recognition import clear_replay_stop_flag, clear_image_cache
            clear_replay_stop_flag()

            self.showMinimized()

            running_count = len([r for r in self.runners.values() if r.isRunning()])
            if running_count == 0:
                clear_image_cache()

            from app import ComboSkillRunner
            import threading as _threading

            runner = ComboSkillRunner(skill, self)
            runner.skill_id = skill_id
            self.runners[skill_id] = runner

            runner._on_finished = lambda success, msg, sid=skill_id: QTimer.singleShot(0, lambda: self._on_combo_skill_finished(success, msg, sid))
            runner._on_step = lambda step_info, sid=skill_id: QTimer.singleShot(0, lambda: self._on_combo_step_changed(step_info, sid))

            _t = _threading.Thread(target=runner.run, daemon=True)
            runner._exec_thread = _t
            _t.start()

            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def initUI(self):
        desktop = QApplication.desktop()
        screen = QApplication.primaryScreen()
        
        # 使用整个桌面的几何信息来居中窗口,而不是单个屏幕的可用区域
        # 这样可以确保在多显示器环境下窗口也能正确居中
        if screen:
            screen_geometry = screen.geometry()
            available_rect = screen.availableGeometry()
        else:
            screen_geometry = desktop.screenGeometry()
            available_rect = desktop.availableGeometry()
        
        min_dimension = min(available_rect.width(), available_rect.height())
        width = int(min_dimension * 0.85)
        height = int(min_dimension * 0.70)
        
        # 基于屏幕几何中心计算窗口位置,确保真正居中
        x = screen_geometry.x() + (screen_geometry.width() - width) // 2
        y = screen_geometry.y() + (screen_geometry.height() - height) // 2
        self.setGeometry(x, y, width, height)
        self.setMinimumSize(1200, 720)

        self.setAttribute(Qt.WA_TranslucentBackground)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_widget.setObjectName("centralContainer")
        main_widget.setStyleSheet("QWidget#centralContainer{background-color:%s;border-radius:28px;}"%MacOSColors.WINDOW_BG)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.macos_toolbar = MacOSToolbar("录制控制")
        main_layout.addWidget(self.macos_toolbar)

        body = QWidget()
        body.setStyleSheet("background-color: transparent; border: none;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.macos_sidebar = MacOSSidebar()
        
        self.macos_sidebar.tab_changed.connect(self.on_macos_tab_changed)
        body_layout.addWidget(self.macos_sidebar)

        self.macos_stack = QStackedWidget()
        self.macos_stack.setStyleSheet("background-color: transparent; border-bottom-right-radius: 28px;")

        self.record_tab = self.create_record_tab()
        self.manager_tab = self.create_manager_tab()
        self.combo_tab = self.create_combo_tab()
        try:
            self.help_tab = self.create_help_tab()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"\n\n\U0001f525 create_help_tab \u62a5\u9519: {e}\n\n")
            # \u521b\u5efa\u4e00\u4e2a\u7b80\u5355\u7684\u5e2e\u52a9\u9875\u907f\u514d\u5d29\u6e83
            from PyQt5.QtWidgets import QLabel
            self.help_tab = QLabel(f"\u52a0\u8f7d\u5931\u8d25: {e}")

        self.macos_stack.addWidget(self.record_tab)
        self.macos_stack.addWidget(self.manager_tab)
        self.macos_stack.addWidget(self.combo_tab)
        self.settings_tab = self.create_settings_tab()
        self.macos_stack.addWidget(self.settings_tab)
        self.macos_stack.addWidget(self.help_tab)

        body_layout.addWidget(self.macos_stack, 1)
        main_layout.addWidget(body, 1)

        self.create_tray_icon()

        self._macos_titles = [
            "录制控制", "流程管理", "组合技",
            "设置",
            "使用帮助"
        ]

        self.fade_animation = None
        self.macos_stack.setCurrentIndex(0)

        # 使用新的设计系统生成统一样式
        self.setStyleSheet(generate_macos_theme())
        body.setStyleSheet("background-color: transparent; border: none;")
        _bo = QFrame(main_widget)
        _bo.setObjectName("borderOverlay")
        _bo.setStyleSheet("QFrame#borderOverlay{background:transparent;border:1px solid #1C1C1E;border-radius:28px;}")
        _bo.setGeometry(main_widget.rect())
        _bo.raise_()
        _bo.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._border_overlay = _bo

    def resizeEvent(self, e):
        if hasattr(self, "_border_overlay") and self._border_overlay:
            self._border_overlay.setGeometry(self.centralWidget().rect())
        super().resizeEvent(e)

    def on_macos_tab_changed(self, index):
        if self.macos_stack.currentIndex() == index:
            return
        self.macos_toolbar.set_title(self._macos_titles[index])

        new_page = self.macos_stack.widget(index)
        if new_page is None:
            return

        if hasattr(self, '_combo_refresh_timer') and self._combo_refresh_timer.isActive():
            self._combo_refresh_timer.stop()

        self.macos_stack.setCurrentIndex(index)

        if index == 2 and hasattr(self, '_combo_refresh_timer'):
            self._combo_refresh_timer.start(3000)
            self.load_combo_skills_to_table(self.combo_tab.combo_table)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, 'replay_status_widget'):
            self.create_replay_status_indicator()
            self._update_replay_ui()
        elif hasattr(self, 'replay_status_label'):
            self.update_replay_status_indicator()

    def create_tab_ui(self, main_layout):
        pass

    def create_record_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setSpacing(24)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setAlignment(Qt.AlignTop)

        main_card = MacOSCard()
        card_layout = QVBoxLayout(main_card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(28, 28, 28, 28)

        record_title = QLabel("录制控制")
        record_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 20px;
            font-weight: 600;
            background-color: transparent;
            border: none;
        """)
        card_layout.addWidget(record_title)

        record_area = QWidget()
        record_area.setFixedHeight(130)
        record_area.setStyleSheet("background-color: transparent; border: none;")
        record_layout = QHBoxLayout(record_area)
        record_layout.setSpacing(16)
        record_layout.setContentsMargins(0, 0, 0, 0)

        # 自绘圆角方形按钮: 130x130, 黑白极简, 文字内嵌, 自带阴影
        self.record_btn = RoundedRecordButton()
        self.record_btn.clicked.connect(lambda: QTimer.singleShot(0, self.toggle_recording))
        record_layout.addWidget(self.record_btn)

        mode_widget = QWidget()
        mode_widget.setStyleSheet("background-color: transparent; border: none;")
        mode_layout = QVBoxLayout(mode_widget)
        mode_layout.setSpacing(8)
        mode_layout.setContentsMargins(0, 0, 0, 0)

        mode_label = QLabel("录制模式")
        mode_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 13px;
            font-weight: 500;
            background-color: transparent;
        """)
        mode_layout.addWidget(mode_label)

        # ── 自定义 macOS 风格下拉框 ──
        self.record_mode_combo = QPushButton("📷	图像录制")
        self.record_mode_combo.setFixedWidth(200)
        self.record_mode_combo.setCursor(Qt.PointingHandCursor)
        # 兼容父类 currentText() 调用
        self.record_mode_combo.currentText = lambda: self.record_mode_combo.text().replace("📷	", "").replace("📍	", "")
        self.record_mode_combo.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1.5px solid {MacOSColors.SEPARATOR};
                border-radius: 10px;
                padding: 9px 16px;
                padding-right: 36px;
                font-size: 13px;
                font-weight: 500;
                min-height: 22px;
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: {MacOSColors.ACCENT};
                background-color: {ColorPalette.BG_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {ColorPalette.GRAY_200};
                border-color: {MacOSColors.ACCENT};
            }}
            QPushButton::menu-indicator {{
                image: none;
                width: 10px;
                subcontrol-position: right center;
                subcontrol-origin: padding;
                padding-right: 14px;
            }}
        """)
        self._record_menu = QMenu(self.record_mode_combo)
        self._record_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {MacOSColors.CARD_BG};
                border: 1px solid {ColorPalette.GRAY_200};
                border-radius: 0px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 10px 18px;
                border-radius: 8px;
                min-height: 24px;
                font-size: 13px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background-color: {MacOSColors.ACCENT};
                color: white;
            }}
        """)
        self._record_menu.addAction("📷	图像录制")
        self._record_menu.addAction("📍	坐标录制")
        self._record_menu.triggered.connect(
            lambda action: self.record_mode_combo.setText(action.text())
        )
        self.record_mode_combo.setMenu(self._record_menu)
        mode_layout.addWidget(self.record_mode_combo)
        record_layout.addWidget(mode_widget)
        record_layout.addStretch()
        card_layout.addWidget(record_area)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {MacOSColors.SEPARATOR};")
        card_layout.addWidget(separator)

        replay_area = QWidget()
        replay_area.setStyleSheet("background-color: transparent; border: none;")
        replay_layout = QHBoxLayout(replay_area)
        replay_layout.setSpacing(16)
        replay_layout.setContentsMargins(0, 0, 0, 0)

        self.replay_btn = MacOSSecondaryButton("▶ 回放已关闭")
        self.replay_btn.setFixedHeight(48)
        self.replay_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_LARGE + 20)
        self.replay_btn.clicked.connect(self.toggle_replay_status_only)
        replay_layout.addWidget(self.replay_btn)

        float_btn = MacOSSecondaryButton("悬浮窗口")
        float_btn.setFixedHeight(48)
        float_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_LARGE + 20)
        float_btn.clicked.connect(self.switch_to_floating_window)
        replay_layout.addWidget(float_btn)
        replay_layout.addStretch()
        card_layout.addWidget(replay_area)

        layout.addWidget(main_card)
        layout.addStretch()
        return tab

    def create_manager_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #FFFFFF; border-radius: 20px;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)

        refresh_btn = MacOSButton("🔄 刷新", MacOSColors.ACCENT)
        refresh_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        header.addWidget(refresh_btn)
        _attach_button_shadow(refresh_btn, MacOSColors.ACCENT)

        trash_btn = MacOSButton("🗑 回收站", MacOSColors.ACCENT)
        trash_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(trash_btn)
        _attach_button_shadow(trash_btn, MacOSColors.ACCENT)
        header.addStretch()
        layout.addLayout(header)

        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
        from design_system import configure_table, get_table_stylesheet

        folder_table = QTableWidget()
        folder_table.setColumnCount(5)
        folder_table.setHorizontalHeaderLabels(["时间", "流程名称", "快捷键", "重命名", "删除"])
        configure_table(folder_table, get_table_stylesheet(
            bg_color="rgba(255, 255, 255, 0.72)",
            header_bg="rgba(255, 255, 255, 0.5)",
            header_color="#6E6E73",
            text_color="#1D1D1F",
            border_color="rgba(255, 255, 255, 0.5)",
            hover_color="rgba(0, 122, 255, 0.06)",
            selected_color="rgba(0, 122, 255, 0.12)",
            alternate_color="rgba(255, 255, 255, 0.4)",
            border_radius=20,
            header_font_size=12,
            cell_font_size=13,
            cell_padding_v=14,
            cell_padding_h=18,
            row_height=50
        ))
        folder_table.horizontalHeader().setStretchLastSection(False)
        folder_table.setColumnWidth(0, 110)
        folder_table.setColumnWidth(1, 400)
        folder_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        folder_table.setColumnWidth(2, 80)
        folder_table.setColumnWidth(3, 55)
        folder_table.setColumnWidth(4, 55)

        def on_folder_table_click(row, column):
            if column == 1:
                item = folder_table.item(row, column)
                if item:
                    folder_path = item.data(Qt.UserRole)
                    if folder_path and os.path.exists(folder_path):
                        self.open_view_images_in_tab(folder_path)
            elif column == 2:
                item = folder_table.item(row, column)
                if item:
                    data = item.data(Qt.UserRole)
                    if data and data[0] == "shortcut":
                        self.set_folder_shortcut_in_tab(data[1], folder_table)
            elif column == 3:
                item = folder_table.item(row, column)
                if item:
                    data = item.data(Qt.UserRole)
                    if data and data[0] == "rename":
                        self.rename_folder_in_tab(data[1], folder_table)
            elif column == 4:
                item = folder_table.item(row, column)
                if item:
                    data = item.data(Qt.UserRole)
                    if data and data[0] == "delete":
                        self.delete_folder_in_tab(data[1], folder_table)

        folder_table.cellClicked.connect(on_folder_table_click)
        layout.addWidget(folder_table)

        refresh_btn.clicked.connect(lambda: self.load_folders_to_table(folder_table))
        trash_btn.clicked.connect(self.open_trash_dialog)

        self.load_folders_to_table(folder_table)
        tab.folder_table = folder_table
        return tab

    def open_view_images_in_tab(self, folder_path):
        try:
            from app import FolderManager
            folder_manager = FolderManager(self)
            self.folder_manager = folder_manager
            folder_manager.view_images(folder_path)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_beautiful_message('critical', '错误', f'打开查看图片窗口失败: {e}', parent=self)

    def load_folders_to_table(self, table_widget):
        table_widget.setRowCount(0)
        from utils import get_recordings_path
        recordings_dir = get_recordings_path()

        if not os.path.exists(recordings_dir):
            return

        try:
            folders = []
            for item in os.listdir(recordings_dir):
                item_path = os.path.join(recordings_dir, item)
                if os.path.isdir(item_path) and item != 'trash':
                    ctime = datetime.fromtimestamp(os.path.getctime(item_path)).strftime('%m-%d %H:%M')
                    folders.append((ctime, item, item_path))

            folders.sort(key=lambda x: x[0], reverse=True)

            table_widget.setRowCount(len(folders))
            for row, (ctime, name, path) in enumerate(folders):
                table_widget.setItem(row, 0, QTableWidgetItem(ctime))
                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.UserRole, path)
                table_widget.setItem(row, 1, name_item)
                shortcut = self.get_folder_shortcut(path)
                shortcut_item = QTableWidgetItem(shortcut if shortcut else "未设置")
                shortcut_item.setData(Qt.UserRole, ("shortcut", path))
                shortcut_item.setForeground(QColor(MacOSColors.ACCENT) if shortcut else QColor(MacOSColors.TEXT_SECONDARY))
                table_widget.setItem(row, 2, shortcut_item)
                rename_item = QTableWidgetItem("✏️")
                rename_item.setTextAlignment(Qt.AlignCenter)
                rename_item.setData(Qt.UserRole, ("rename", path))
                rename_item.setForeground(QColor(MacOSColors.ACCENT))
                table_widget.setItem(row, 3, rename_item)
                delete_item = QTableWidgetItem("🗑️")
                delete_item.setTextAlignment(Qt.AlignCenter)
                delete_item.setData(Qt.UserRole, ("delete", path))
                delete_item.setForeground(QColor(MacOSColors.SYSTEM_RED))
                table_widget.setItem(row, 4, delete_item)
            table_widget.setColumnWidth(0, 150)
            table_widget.setColumnWidth(1, 200)
            table_widget.setColumnWidth(2, 80)
            table_widget.setColumnWidth(3, 70)
            table_widget.setColumnWidth(4, 55)
            table_widget.horizontalHeader().setStretchLastSection(True)
            table_widget.setColumnWidth(1, 200)
        except Exception as e:
            pass

    def set_folder_shortcut_in_tab(self, folder_path, table_widget):
        from PyQt5.QtWidgets import QDialog
        from PyQt5.QtCore import Qt, QTimer

        folder_name = os.path.basename(folder_path)
        current_shortcut = self.get_folder_shortcut(folder_path)

        self.temporarily_disable_grave_hotkey()

        dialog = QDialog(self)
        dialog.setWindowTitle("设置快捷键 - %s" % folder_name)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {MacOSColors.WINDOW_BG};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(28, 24, 28, 24)

        screen_width, screen_height = get_screen_size()

        instruction_label = QLabel("请按下快捷键组合...")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_font_size = int(screen_height * 0.022)
        instruction_label.setStyleSheet(f"""
            font-size: {instruction_font_size}px;
            color: {MacOSColors.TEXT_SECONDARY};
            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            background-color: transparent;
        """)
        layout.addWidget(instruction_label)

        shortcut_label = QLabel(current_shortcut if current_shortcut else "未设置")
        shortcut_label.setAlignment(Qt.AlignCenter)
        shortcut_font_size = int(screen_height * 0.03)
        shortcut_label.setStyleSheet(f"""
            font-size: {shortcut_font_size}px;
            font-weight: 600;
            padding: 14px;
            border: 2px solid {MacOSColors.ACCENT};
            border-radius: 12px;
            background-color: {MacOSColors.CARD_BG};
            min-height: 44px;
            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            color: {MacOSColors.ACCENT};
        """)
        layout.addWidget(shortcut_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        clear_btn = QPushButton("清除")
        clear_btn.setFixedHeight(ButtonSize.HEIGHT_REGULAR)
        clear_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.SYSTEM_RED};
                color: white;
                border: none;
                border-radius: {BorderRadiusSystem.MD}px;
                font-weight: 500;
                font-size: 13px;
                font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {MacOSColors.SYSTEM_RED}DD;
            }}
            QPushButton:pressed {{
                background-color: {MacOSColors.SYSTEM_RED}BB;
                padding-top: 2px;
            }}
        """)
        clear_btn.setCursor(Qt.PointingHandCursor)

        ok_btn = QPushButton("确定")
        ok_btn.setFixedHeight(ButtonSize.HEIGHT_REGULAR)
        ok_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.ACCENT};
                color: white;
                border: none;
                border-radius: {BorderRadiusSystem.MD}px;
                font-weight: 500;
                font-size: 13px;
                font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {MacOSColors.ACCENT}DD;
            }}
            QPushButton:pressed {{
                background-color: {MacOSColors.ACCENT}BB;
                padding-top: 2px;
            }}
        """)
        ok_btn.setCursor(Qt.PointingHandCursor)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(ButtonSize.HEIGHT_REGULAR)
        cancel_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: {BorderRadiusSystem.MD}px;
                font-weight: 500;
                font-size: 13px;
                font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {MacOSColors.ACCENT_BG};
                border-color: {MacOSColors.ACCENT};
                color: {MacOSColors.ACCENT};
            }}
            QPushButton:pressed {{
                padding-top: 2px;
            }}
        """)
        cancel_btn.setCursor(Qt.PointingHandCursor)

        def clear_shortcut():
            shortcut_label.setText("未设置")
            shortcut_label.setStyleSheet(f"""
                font-size: {shortcut_font_size}px;
                font-weight: 600;
                padding: 14px;
                border: 2px solid {MacOSColors.SEPARATOR};
                border-radius: 12px;
                background-color: {MacOSColors.CARD_BG};
                min-height: 44px;
                font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                color: {MacOSColors.TEXT_SECONDARY};
            """)
            normalized_path = os.path.normpath(str(folder_path))
            keys_to_delete = []
            for key in self.shortcuts.keys():
                if os.path.normpath(str(key)).lower() == normalized_path.lower():
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                del self.shortcuts[key]
            self.save_shortcut_config()
            self.update_shortcuts()

        def confirm_shortcut():
            shortcut_str = shortcut_label.text()
            if shortcut_str and shortcut_str != "未设置":
                normalized_path = os.path.normpath(str(folder_path))
                # 检查快捷键是否已被其他流程使用（跳过不存在的文件夹）
                for path, existing in self.shortcuts.items():
                    if existing == shortcut_str and os.path.normpath(str(path)).lower() != normalized_path.lower():
                        if not os.path.exists(os.path.normpath(str(path))):
                            continue
                        from beautiful_dialog import StyledMessageDialog
                        _d = StyledMessageDialog(dialog, title="快捷键冲突", text=f"快捷键「{shortcut_str}」已被其他流程使用！\n请换一个快捷键。", msg_type="warning", buttons="ok")
                        _d.exec_()
                        return
                self.shortcuts[normalized_path] = shortcut_str
                self.save_shortcut_config()
                self.update_shortcuts()
            else:
                normalized_path = os.path.normpath(str(folder_path))
                keys_to_delete = []
                for key in self.shortcuts.keys():
                    if os.path.normpath(str(key)).lower() == normalized_path.lower():
                        keys_to_delete.append(key)
                for key in keys_to_delete:
                    del self.shortcuts[key]
                self.save_shortcut_config()
                self.update_shortcuts()
            self.load_folders_to_table(table_widget)
            dialog.accept()

        clear_btn.clicked.connect(clear_shortcut)
        ok_btn.clicked.connect(confirm_shortcut)
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(clear_btn)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        self.pending_shortcut = None

        def key_handler(event):
            if event.key() == Qt.Key_Escape:
                dialog.reject()
                return
            if event.key() in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                return
            mods = []
            if event.modifiers() & Qt.ControlModifier:
                mods.append("Ctrl")
            if event.modifiers() & Qt.AltModifier:
                mods.append("Alt")
            if event.modifiers() & Qt.ShiftModifier:
                mods.append("Shift")
            if event.modifiers() & Qt.MetaModifier:
                mods.append("Win")
            key_name = event.text()
            if not key_name:
                key = event.key()
                if key == Qt.Key_Return or key == Qt.Key_Enter:
                    key_name = "Enter"
                elif key == Qt.Key_Tab:
                    key_name = "Tab"
                elif key == Qt.Key_Backspace:
                    key_name = "Backspace"
                elif key == Qt.Key_Delete:
                    key_name = "Delete"
                elif key == Qt.Key_Home:
                    key_name = "Home"
                elif key == Qt.Key_End:
                    key_name = "End"
                elif key == Qt.Key_PageUp:
                    key_name = "PageUp"
                elif key == Qt.Key_PageDown:
                    key_name = "PageDown"
                elif key == Qt.Key_Space:
                    key_name = "Space"
                elif key == Qt.Key_Escape:
                    dialog.reject()
                    return
                else:
                    key_name = event.text()
            if mods and key_name:
                shortcut = "+".join(mods + [key_name.upper()])
            elif key_name:
                shortcut = key_name.upper()
            else:
                return
            shortcut_label.setText(shortcut)
            shortcut_label.setStyleSheet(f"""
                font-size: {shortcut_font_size}px;
                font-weight: 600;
                padding: 14px;
                border: 2px solid {MacOSColors.ACCENT};
                border-radius: 12px;
                background-color: {MacOSColors.CARD_BG};
                min-height: 44px;
                font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                color: {MacOSColors.ACCENT};
            """)

        dialog.keyPressEvent = key_handler
        dialog.setFocusPolicy(Qt.StrongFocus)
        dialog.setFocus()
        dialog.exec_()
        self.reenable_grave_hotkey()

    def rename_folder_in_tab(self, folder_path, table_widget):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
        from PyQt5.QtCore import Qt

        old_name = os.path.basename(folder_path)
        dialog = QDialog(self)
        dialog.setWindowTitle("重命名流程")
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        width, height = get_screen_size(0.25)
        dialog.resize(width, int(height * 0.18))
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {MacOSColors.WINDOW_BG};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        label = QLabel("请输入新的流程名称：")
        label.setStyleSheet(f"""
            font-size: 14px;
            color: {MacOSColors.TEXT_PRIMARY};
            font-weight: 500;
            background-color: transparent;
        """)
        layout.addWidget(label)

        input_field = QLineEdit(old_name)
        input_field.selectAll()
        input_field.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                background: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QLineEdit:focus {{
                border-color: {MacOSColors.ACCENT};
            }}
        """)
        layout.addWidget(input_field)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        ok_btn = QPushButton("确定")
        ok_btn.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        ok_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.ACCENT};
                color: white;
                border: none;
                border-radius: {BorderRadiusSystem.MD}px;
                font-weight: 500;
                font-size: 13px;
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {MacOSColors.ACCENT}DD;
            }}
            QPushButton:pressed {{
                background-color: {MacOSColors.ACCENT}BB;
                padding-top: 2px;
            }}
        """)
        ok_btn.setCursor(Qt.PointingHandCursor)

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        cancel_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: {BorderRadiusSystem.MD}px;
                font-weight: 500;
                font-size: 13px;
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {MacOSColors.ACCENT_BG};
                border-color: {MacOSColors.ACCENT};
                color: {MacOSColors.ACCENT};
            }}
            QPushButton:pressed {{
                padding-top: 2px;
            }}
        """)
        cancel_btn.setCursor(Qt.PointingHandCursor)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)

        def do_rename():
            new_name = input_field.text().strip()
            if not new_name:
                return
            if new_name == old_name:
                dialog.accept()
                return
            try:
                new_path = os.path.join(os.path.dirname(folder_path), new_name)
                os.rename(folder_path, new_path)
                if hasattr(self, 'shortcuts'):
                    old_path_normalized = os.path.normpath(str(folder_path))
                    new_path_normalized = os.path.normpath(str(new_path))
                    old_key = None
                    for key in list(self.shortcuts.keys()):
                        if os.path.normpath(str(key)).lower() == old_path_normalized.lower():
                            old_key = key
                            break
                    if old_key is not None:
                        self.shortcuts[new_path_normalized] = self.shortcuts.pop(old_key)
                        self.save_shortcut_config()
                        self.update_shortcuts()
                self.load_folders_to_table(table_widget)
                dialog.accept()
            except Exception as e:
                self.show_beautiful_message('critical', "错误", f"重命名失败: {e}")

        ok_btn.clicked.connect(do_rename)
        cancel_btn.clicked.connect(dialog.reject)
        input_field.returnPressed.connect(do_rename)

        dialog.exec_()

    def delete_folder_in_tab(self, folder_path, table_widget):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import Qt

        folder_name = os.path.basename(folder_path)
        dialog = QDialog(self)
        dialog.setWindowTitle("确认删除")
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        width, height = get_screen_size(0.2)
        dialog.resize(width, int(height * 0.15))
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {MacOSColors.WINDOW_BG};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(24, 20, 24, 20)

        msg_label = QLabel(f"确定要删除流程「{folder_name}」吗？")
        msg_label.setStyleSheet(f"""
            font-size: 15px;
            color: {MacOSColors.TEXT_PRIMARY};
            font-weight: 500;
            background-color: transparent;
        """)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        hint_label = QLabel("该流程将移动到回收站")
        hint_label.setStyleSheet(f"""
            font-size: 12px;
            color: {MacOSColors.TEXT_SECONDARY};
            background-color: transparent;
        """)
        layout.addWidget(hint_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        delete_btn = QPushButton("删除")
        delete_btn.setFixedHeight(ButtonSize.HEIGHT_REGULAR)
        delete_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.SYSTEM_RED};
                color: white;
                border: none;
                border-radius: {BorderRadiusSystem.MD}px;
                font-weight: 500;
                font-size: 13px;
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {MacOSColors.SYSTEM_RED}DD;
            }}
            QPushButton:pressed {{
                background-color: {MacOSColors.SYSTEM_RED}BB;
                padding-top: 2px;
            }}
        """)
        delete_btn.setCursor(Qt.PointingHandCursor)

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        cancel_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: {BorderRadiusSystem.MD}px;
                font-weight: 500;
                font-size: 13px;
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {MacOSColors.ACCENT_BG};
                border-color: {MacOSColors.ACCENT};
                color: {MacOSColors.ACCENT};
            }}
        """)
        cancel_btn.setCursor(Qt.PointingHandCursor)

        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)

        def do_delete():
            try:
                trash_dir = os.path.join(os.path.dirname(folder_path), 'trash')
                if not os.path.exists(trash_dir):
                    os.makedirs(trash_dir)
                import shutil
                shutil.move(folder_path, os.path.join(trash_dir, os.path.basename(folder_path)))
                # 同时清理该文件夹的快捷键
                normalized_path = os.path.normpath(str(folder_path))
                keys_to_delete = []
                for key in self.shortcuts.keys():
                    if os.path.normpath(str(key)).lower() == normalized_path.lower():
                        keys_to_delete.append(key)
                for key in keys_to_delete:
                    del self.shortcuts[key]
                if keys_to_delete:
                    self.save_shortcut_config()
                self.load_folders_to_table(table_widget)
                dialog.accept()
            except Exception as e:
                from beautiful_dialog import StyledMessageDialog
                _d = StyledMessageDialog(self, title="错误", text=f"删除失败: {e}", msg_type="critical", buttons="ok")
                _d.exec_()

        delete_btn.clicked.connect(do_delete)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()

    def create_combo_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        status_bar = QWidget()
        status_bar.setStyleSheet(f"background-color: {MacOSColors.CARD_BG}; border-radius: 10px;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(16, 10, 16, 10)

        status_text = QLabel("组合技运行状态：空闲")
        status_text.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {MacOSColors.TEXT_SECONDARY}; background-color: transparent;")
        status_layout.addWidget(status_text)

        running_names_label = QLabel("")
        running_names_label.setStyleSheet(f"font-size: 12px; color: {MacOSColors.SYSTEM_GREEN}; background-color: transparent;")
        status_layout.addWidget(running_names_label)
        status_layout.addStretch()

        status_bar.setVisible(True)
        layout.addWidget(status_bar)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        new_btn = MacOSSecondaryButton("+ 新建组合技")
        new_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_LARGE)
        top_layout.addWidget(new_btn)

        refresh_btn = MacOSSecondaryButton("🔄 刷新")
        refresh_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        top_layout.addWidget(refresh_btn)

        run_selected_btn = MacOSSecondaryButton("▶ 启动选中")
        run_selected_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        top_layout.addWidget(run_selected_btn)

        stop_selected_btn = MacOSSecondaryButton("⏹ 停止选中")
        stop_selected_btn.setCursor(Qt.PointingHandCursor)
        top_layout.addWidget(stop_selected_btn)

        stop_all_btn = MacOSSecondaryButton("⏹ 全部停止")
        stop_all_btn.setCursor(Qt.PointingHandCursor)
        stop_all_btn.setVisible(False)
        top_layout.addWidget(stop_all_btn)

        top_layout.addStretch()
        layout.addLayout(top_layout)

        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
        from design_system import configure_table, get_table_stylesheet

        combo_table = QTableWidget()
        combo_table.setColumnCount(7)
        combo_table.setHorizontalHeaderLabels(["☐", "名称", "流程", "状态", "操作", "快捷键", "删除"])
        configure_table(combo_table, get_table_stylesheet(
            cell_padding_v=6, cell_padding_h=12, row_height=44
        ))
        combo_table.verticalHeader().setDefaultSectionSize(44)
        combo_table.setColumnWidth(0, 50)
        combo_table.setColumnWidth(1, 120)
        combo_table.setColumnWidth(2, 60)
        combo_table.setColumnWidth(3, 80)
        combo_table.setColumnWidth(4, 100)
        combo_table.setColumnWidth(5, 100)
        combo_table.setColumnWidth(6, 60)
        combo_table.horizontalHeader().setStretchLastSection(True)

        def on_combo_table_click(row, column):
            combo_table.setCurrentCell(row, column)
            if column == 0:
                check_item = combo_table.item(row, 0)
                if check_item:
                    check_item.setCheckState(Qt.Unchecked if check_item.checkState() == Qt.Checked else Qt.Checked)
            elif column == 1:
                item = combo_table.item(row, column)
                if item:
                    skill = item.data(Qt.UserRole)
                    if skill:
                        self.edit_combo_skill_in_tab(skill, combo_table)
            elif column == 4:
                item = combo_table.item(row, column)
                if item:
                    data = item.data(Qt.UserRole)
                    if data:
                        if data[0] == "run":
                            self.run_combo_skill_in_tab(data[1])
                        elif data[0] == "stop":
                            self.stop_combo_skill(data[1])
            elif column == 5:
                pass
            elif column == 6:
                # 删除列
                item = combo_table.item(row, column)
                if item:
                    skill = item.data(Qt.UserRole)
                    if skill:
                        self.delete_combo_skill_in_tab(skill, combo_table)

        combo_table.cellClicked.connect(on_combo_table_click)
        layout.addWidget(combo_table)

        new_btn.clicked.connect(self.open_combo_skill_editor)
        refresh_btn.clicked.connect(lambda: self.load_combo_skills_to_table(combo_table))
        run_selected_btn.clicked.connect(lambda: self.run_selected_combo_skills(combo_table))
        stop_selected_btn.clicked.connect(lambda: self.stop_selected_combo_skills(combo_table))
        stop_all_btn.clicked.connect(lambda: self.stop_combo_skill())

        self.load_combo_skills_to_table(combo_table)

        tab.combo_table = combo_table
        tab.status_text = status_text
        tab.running_names_label = running_names_label
        tab.status_bar = status_bar
        tab.stop_all_btn = stop_all_btn
        tab.run_selected_btn = run_selected_btn
        tab.stop_selected_btn = stop_selected_btn

        self._combo_refresh_timer = QTimer(self)
        self._combo_refresh_timer.timeout.connect(lambda: self.load_combo_skills_to_table(combo_table))
        self._combo_refresh_timer.start(3000)

        return tab


    def create_settings_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setAlignment(Qt.AlignTop)

        settings_list = [
            ("📋", "查看运行日志", "查看应用程序运行日志", self.show_log_window),
        ]
        for icon, name, desc, handler in settings_list:
            card = MacOSCard()
            cl = QHBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            cl.setSpacing(12)
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"""
                background-color: {MacOSColors.ACCENT_BG};
                border-radius: 22px;
                font-size: 18px;
                min-width: 44px;
                max-width: 44px;
                min-height: 44px;
                max-height: 44px;
            """)
            icon_label.setAlignment(Qt.AlignCenter)
            cl.addWidget(icon_label)
            text_container = QVBoxLayout()
            text_container.setSpacing(2)
            name_label = QLabel(name)
            name_label.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 15px; font-weight: 600; background-color: transparent;")
            desc_label = QLabel(desc)
            desc_label.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 12px; background-color: transparent;")
            text_container.addWidget(name_label)
            text_container.addWidget(desc_label)
            cl.addLayout(text_container, 1)
            arrow = QLabel("›")
            arrow.setStyleSheet(f"""
                color: {MacOSColors.SYSTEM_GRAY};
                font-size: 20px;
                background-color: transparent;
            """)
            cl.addWidget(arrow)
            card.setCursor(Qt.PointingHandCursor)
            if handler:
                card.mousePressEvent = lambda e, h=handler: h()
            layout.addWidget(card)
        layout.addStretch()
        return tab

    def create_help_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setSpacing(0)

        title = QLabel("")
        title.setStyleSheet("color: %s; font-size: 24px; font-weight: 700; padding: 12px 0 8px 0; background-color: transparent;" % MacOSColors.TEXT_PRIMARY)
        layout.addWidget(title)

        steps = []
        self._build_tutorial_steps(steps)
        total_steps = len(steps)
        current_step = [0]

        # 顶部标签导航
        tab_bar = QWidget()
        tab_bar.setFixedHeight(50)
        tab_bar.setStyleSheet("background: white; border-radius: 10px;")
        tl = QHBoxLayout(tab_bar)
        tl.setContentsMargins(4, 4, 4, 4)
        tl.setSpacing(0)
        tab_btns = []
        for i in range(total_steps):
            btn = QPushButton(f"0{i+1}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { font-size: 14px; font-weight: %s; color: %s; "
                "background: %s; border: none; border-radius: 8px; padding: 0; }"
                "QPushButton:hover { color: #007AFF; }"
                % ('700' if i==0 else '400',
                   '#007AFF' if i==0 else '#8E8E93',
                   'white' if i==0 else 'transparent')
            )
            tl.addWidget(btn, 1)
            tab_btns.append(btn)
        layout.addWidget(tab_bar)
        layout.addSpacing(10)

        # 内容卡片
        card = MacOSCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 10, 20, 10)
        cl.setSpacing(8)

        sh = QHBoxLayout()
        icon_lbl = QLabel(steps[0]["icon"])
        icon_lbl.setStyleSheet("font-size: 28px; background-color: transparent;")
        sh.addWidget(icon_lbl)
        title_lbl = QLabel(steps[0]["title"])
        title_lbl.setTextFormat(Qt.RichText)
        title_lbl.setStyleSheet("color: %s; font-size: 20px; font-weight: bold; background-color: transparent;" % MacOSColors.TEXT_PRIMARY)
        sh.addWidget(title_lbl)
        sh.addStretch()
        cl.addLayout(sh)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.viewport().setStyleSheet("margin:0;padding:0;background:transparent;")
        body_lbl = QLabel(steps[0]["content"])
        body_lbl.setWordWrap(True)
        body_lbl.setAlignment(Qt.AlignTop)
        body_lbl.setStyleSheet("background-color: transparent; margin:0; padding:0;")
        bf = body_lbl.font()
        bf.setBold(True)
        body_lbl.setFont(bf)
        scroll.setWidget(body_lbl)
        cl.addWidget(scroll)
        layout.addWidget(card)

        # 底部导航
        nav = QHBoxLayout()
        nav.setSpacing(16)
        prev_btn = QPushButton("← 上一步")
        prev_btn.setFixedSize(130, 42)
        prev_btn.setEnabled(False)
        prev_btn.setStyleSheet(
            "QPushButton { background: %s; color: %s; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; }"
            "QPushButton:hover:!disabled { background: %s; }"
            "QPushButton:disabled { opacity: 0.5; }"
            % (MacOSColors.SEPARATOR, MacOSColors.TEXT_PRIMARY, MacOSColors.ACCENT_BG)
        )
        next_btn = QPushButton("下一步 →")
        next_btn.setFixedSize(130, 42)
        next_btn.setStyleSheet(
            "QPushButton { background: %s; color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; }"
            "QPushButton:hover { background: #0056CC; }"
            % MacOSColors.ACCENT
        )
        nav.addStretch(); nav.addWidget(prev_btn); nav.addSpacing(20); nav.addWidget(next_btn); nav.addStretch()
        layout.addLayout(nav)

        # 辅助函数
        def go_to_step(idx):
            current_step[0] = idx
            s = steps[idx]
            icon_lbl.setText(s["icon"])
            title_lbl.setText(s["title"])
            body_lbl.setText(s["content"])
            for j, b in enumerate(tab_btns):
                b.setStyleSheet(
                    "QPushButton { font-size: 14px; font-weight: %s; color: %s; "
                    "background: %s; border: none; border-radius: 8px; padding: 0; }"
                    "QPushButton:hover { color: #007AFF; }"
                    % ('700' if j==idx else '400',
                       '#007AFF' if j==idx else '#8E8E93',
                       'white' if j==idx else 'transparent')
                )
            prev_btn.setEnabled(idx > 0)
            if idx == total_steps - 1:
                next_btn.setText("重新开始 ↺")
            else:
                next_btn.setText("下一步 →")

        for i, b in enumerate(tab_btns):
            b.clicked.connect(lambda checked=False, idx=i: go_to_step(idx))
        prev_btn.clicked.connect(lambda: current_step[0] > 0 and go_to_step(current_step[0] - 1))
        next_btn.clicked.connect(lambda: go_to_step(0) if current_step[0] == total_steps - 1 else go_to_step(current_step[0] + 1))

        return tab

    def _build_tutorial_steps(self, steps):
        tc = MacOSColors.TEXT_PRIMARY
        ac = MacOSColors.ACCENT
        sc = MacOSColors.SYSTEM_GREEN
        def h(b): return "<div style='font-size:17px;line-height:1.8;color:%s;font-family:Microsoft YaHei,sans-serif;'>%s</div>" % (tc, b)

        data = [
            ("⌨️", "<b>第一步</b>：你每天在当机器人吗？",
             "<p style='margin:8px 0;font-size:18px;color:%s;'><b>🤖 问问自己 —— 这些事情是不是每天都在做？</b></p>"
             "<p style='margin:6px 0;'>• 早上打开 Chrome → 微信 → 钉钉 → 邮箱 → 办公软件</p>"
             "<p style='margin:6px 0;'>• 填日报：复制粘贴 → 改日期 → 改数据 → 发送</p>"
             "<p style='margin:6px 0;'>• 登录系统：输账号 → 输密码 → 点登录</p>"
             "<p style='margin:6px 0;'>• 导出数据：点菜单 → 点导出 → 选格式 → 保存</p>"
             "<p style='margin:10px 0;'><b>一天两天没什么，但一年两年呢？</b></p>"
             "<p style='margin:4px 0;color:#8E8E93;'>这些动作你重复了成千上万次，浪费了几百个小时。</p>"
             "<p style='margin:10px 0 0 0;color:%s;'><b>💡 这个软件的意义：你只需要做一次，以后它替你干。</b></p>" % (ac, sc)),
            ("🎬", "<b>第二步</b>：录一遍，以后就再也不用干了",
             "<p style='margin:8px 0;font-size:18px;color:%s;'><b>🎯 就三步，让你彻底告别重复劳动</b></p>"
             "<p style='margin:8px 0;'>❶ <b>点击〈录制〉</b><span style='color:#8E8E93;'> —— 按钮变红，框选视作点击</span></p>"
             "<p style='margin:8px 0;'>❷ <b>框选要操作的位置</b><span style='color:#8E8E93;'> —— 框选视为点击，自动执行</span></p>"
             "<p style='margin:8px 0;'>❸ <b>按 ESC 退出录制</b><span style='color:#8E8E93;'> —— 录制完毕，自动保存</span></p>"
             "<p style='margin:12px 0 0 0;'>👇 去〈<b>流程管理</b>〉点〈回放〉，看它自动完成一遍</p>"
             "<p style='margin:4px 0 0 0;color:%s;'><b>✔ 录一次，这个操作你一辈子都不用再亲手干了。</b></p>" % (ac, sc)),
            ("🔧", "<b>第三步</b>：看它替你干活，很爽",
             "<p style='margin:8px 0;font-size:18px;color:%s;'><b>🎥 点一下回放，它就开始「模仿」你</b></p>"
             "<p style='margin:6px 0;color:#8E8E93;'>你坐在旁边看着它：</p>"
             "<p style='margin:6px 0;'>• <b>自动打开软件</b> ✓</p>"
             "<p style='margin:6px 0;'>• <b>自动输入文字</b> ✓</p>"
             "<p style='margin:6px 0;'>• <b>自动点击按钮</b> ✓</p>"
             "<p style='margin:6px 0;'>• <b>自动完成所有操作</b> ✓</p>"
             "<p style='margin:8px 0;'>而你只需要 —— <b>喝杯咖啡，看着它干</b> ☕</p>"
             "<p style='margin:6px 0;'>💡 <b>F12 键</b>可以随时叫停，完全由你控制</p>"
             "<p style='margin:10px 0 0 0;color:%s;'><b>这种感觉，试过一次就回不去了。</b></p>" % (ac, sc)),
            ("✏️", "<b>第四步</b>：不怕录错，改就完了",
             "<p style='margin:8px 0;font-size:18px;color:%s;'><b>🛠️ 录错了也不用重新来</b></p>"
             "<p style='margin:6px 0;color:#8E8E93;'>以前录错了 → 重头再录一遍 → 浪费时间还烦躁</p>"
             "<p style='margin:6px 0;'>现在录错了 → 在操作列表里找到那一步 → <b>直接修改</b></p>"
             "<p style='margin:8px 0 4px 0;'>• <b>改按键</b><span style='color:#8E8E93;'>：按错了键？改成正确的就行</span></p>"
             "<p style='margin:4px 0;'>• <b>改文字</b><span style='color:#8E8E93;'>：输错了内容？直接改掉</span></p>"
             "<p style='margin:4px 0;'>• <b>调顺序</b><span style='color:#8E8E93;'>：步骤顺序不对？拖拽调整</span></p>"
             "<p style='margin:4px 0 8px 0;'>• <b>删多余</b><span style='color:#8E8E93;'>：某一步不需要？点×删除</span></p>"
             "<p style='margin:8px 0 0 0;color:%s;'><b>修改后自动保存，再回放就是完美版本。</b></p>" % (ac, sc)),
            ("⚙️", "<b>第五步</b>：让电脑替你 7×24 工作",
             "<p style='margin:8px 0;font-size:18px;color:%s;'><b>⏰ 组合技：把多个流程串起来，一次跑完</b></p>"
             "<p style='margin:6px 0;color:#8E8E93;'>比如一个「每日晨会准备」的组合：</p>"
             "<p style='margin:6px 0;'>• 流程A：打开日报系统 → 导出昨日数据</p>"
             "<p style='margin:4px 0;'>• 流程B：打开邮箱 → 填入数据 → 发送晨会报告</p>"
             "<p style='margin:4px 0;'>• 流程C：打开项目看板 → 刷新状态 → 截图保存</p>"
             "<p style='margin:10px 0;'><b>想象一下：每天早上到公司，点一下，它自己全部搞定。</b></p>"
             "<p style='margin:8px 0 0 0;color:%s;'><b>而你只需要坐下来，喝口热水，开始真正有意义的工作。</b></p>" % (ac, sc)),
            ("🎉", "<b>第六步</b>：不再做重复劳动的奴隶",
             "<p style='margin:8px 0;font-size:18px;color:%s;'><b>🎊 从今天起，告别「低效重复」！</b></p>"
             "<p style='margin:6px 0;color:#8E8E93;'>你学会了：</p>"
             "<p style='margin:6px 0;'>✅ <b>录一次</b><span style='color:#8E8E93;'> —— 它记住你的操作</span></p>"
             "<p style='margin:4px 0;'>✅ <b>无限回放</b><span style='color:#8E8E93;'> —— 以后不用再亲手干</span></p>"
             "<p style='margin:4px 0;'>✅ <b>随意修改</b><span style='color:#8E8E93;'> —— 录错了直接改，不重录</span></p>"
             "<p style='margin:4px 0 10px 0;'>✅ <b>组合串联</b><span style='color:#8E8E93;'> —— 复杂任务一键搞定</span></p>"

             "<p style='margin:10px 0 0 0;color:%s;'><b>💡 你每天省下来的时间，可以做更重要的事。</b></p>"
             "<p style='margin:6px 0 0 0;color:#8E8E93;'>祝你早点下班，把时间留给值得的人和事 🚀🎊</p>" % (ac, sc)),
        ]
        for icon, title, body in data:
            steps.append({"icon": icon, "title": title, "content": h(body)})
    def create_tray_icon(self):
        """创建系统托盘图标"""
        if hasattr(self, "tray_icon") and self.tray_icon:
            return
        from PyQt5.QtWidgets import QSystemTrayIcon
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setToolTip("PC-action")
        tray_menu = QMenu(self)
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_and_raise)
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        from PyQt5.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_raise()

    def show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_application(self):
        self.close()
        QApplication.quit()

    def open_combo_skill_editor(self, skill=None):
        """打开组合技编辑器"""
        from combo_skill_edit_dialog import ComboSkillEditDialog
        from PyQt5.QtWidgets import QDialog as _QD
        from combo_skill_manager import ComboSkillManager
        dialog = ComboSkillEditDialog(self, skill)
        if dialog.exec_() == _QD.Accepted:
            skill_data = dialog.get_skill_data()
            if skill_data:
                combo_manager = ComboSkillManager(self)
                if skill:
                    for i, s in enumerate(combo_manager.combo_skills):
                        if s.get("name") == skill.get("name"):
                            combo_manager.combo_skills[i] = skill_data
                            break
                else:
                    combo_manager.combo_skills.append(skill_data)
                combo_manager.save_combo_skills()
                if hasattr(self, "combo_tab") and hasattr(self.combo_tab, "combo_table"):
                    self.load_combo_skills_to_table(self.combo_tab.combo_table)
    def edit_combo_skill_in_tab(self, skill, combo_table):
        """在组合技tab页中编辑组合技"""
        self.open_combo_skill_editor(skill)
        self.load_combo_skills_to_table(combo_table)

    def delete_combo_skill_in_tab(self, skill, combo_table):
        """在组合技tab页中删除组合技"""
        from combo_skill_manager import ComboSkillManager
        from PyQt5.QtWidgets import QMessageBox
        skill_name = skill.get('name', '')
        reply = QMessageBox.question(None, '确认删除', f'确定要删除组合技 \"{skill_name}\" 吗？', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            combo_manager = ComboSkillManager(self)
            combo_manager.combo_skills = [s for s in combo_manager.combo_skills if s.get('name') != skill.get('name')]
            combo_manager.save_combo_skills()
            self.load_combo_skills_to_table(combo_table)



    def load_combo_skills_to_table(self, table_widget):
        import time
        checked_names = set()
        for row in range(table_widget.rowCount()):
            check_item = table_widget.item(row, 0)
            if check_item and check_item.checkState() == Qt.Checked:
                name_item = table_widget.item(row, 1)
                if name_item:
                    raw = name_item.text()
                    if raw.startswith("🏃 "):
                        raw = raw[2:]
                    checked_names.add(raw)

        table_widget.setRowCount(0)

        combo_skills = self._get_combo_manager().combo_skills

        running_skill_ids = set()
        running_skill_names = []
        if hasattr(self, 'runners'):
            for skill_id, runner in self.runners.items():
                if runner.isRunning():
                    running_skill_ids.add(skill_id)
                    if hasattr(runner, 'skill_data'):
                        running_skill_names.append(runner.skill_data.get('name', ''))

        running_count = len(running_skill_ids)

        if hasattr(self, 'combo_tab'):
            tab = self.combo_tab
            if hasattr(tab, 'status_text') and hasattr(tab, 'running_names_label') and hasattr(tab, 'stop_all_btn'):
                if running_count > 0:
                    tab.status_text.setText(f"运行中（{running_count}个组合技锛?")
                    tab.status_text.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {MacOSColors.SYSTEM_GREEN}; background-color: transparent;")
                    tab.running_names_label.setText("  ".join(running_skill_names))
                    tab.running_names_label.setVisible(True)
                    tab.stop_all_btn.setVisible(True)
                else:
                    tab.status_text.setText("组合技运行状态：空闲")
                    tab.status_text.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {MacOSColors.TEXT_SECONDARY}; background-color: transparent;")
                    tab.running_names_label.setText("")
                    tab.running_names_label.setVisible(False)
                    tab.stop_all_btn.setVisible(False)

        table_widget.setRowCount(len(combo_skills))
        for row, skill in enumerate(combo_skills):
            table_widget.setRowHeight(row, 42)

            name = skill.get('name', '未命名')
            flow_count = len(skill.get('flows', []))
            is_running = (skill.get('name', '') in running_skill_ids)
            is_monitor = skill.get('monitor_mode', False)

            row_font = QFont()
            row_font.setBold(is_running)

            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check_item.setCheckState(Qt.Checked if name in checked_names else Qt.Unchecked)
            check_item.setTextAlignment(Qt.AlignCenter)
            check_item.setData(Qt.UserRole, skill)
            table_widget.setItem(row, 0, check_item)

            name_item = QTableWidgetItem(f"{'🏃 ' if is_monitor else ''}{name}")
            name_item.setData(Qt.UserRole, skill)
            name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            name_item.setForeground(QColor(MacOSColors.SYSTEM_GREEN if is_running else MacOSColors.TEXT_PRIMARY))
            name_item.setFont(row_font)
            table_widget.setItem(row, 1, name_item)

            flow_count_item = QTableWidgetItem(str(flow_count))
            flow_count_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            table_widget.setItem(row, 2, flow_count_item)

            if is_running:
                status_item = QTableWidgetItem("▶ 运行中")
                status_item.setForeground(QColor(MacOSColors.SYSTEM_GREEN))
                status_font = QFont()
                status_font.setBold(True)
                status_item.setFont(status_font)
            elif is_monitor:
                status_item = QTableWidgetItem("🏃 监控")
                status_item.setForeground(QColor(MacOSColors.ACCENT))
            else:
                status_item = QTableWidgetItem("空闲")
                status_item.setForeground(QColor(MacOSColors.TEXT_SECONDARY))
            status_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            table_widget.setItem(row, 3, status_item)

            if is_running:
                stop_btn_item = QTableWidgetItem("⏹ 停止")
                stop_btn_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                stop_btn_item.setData(Qt.UserRole, ("stop", skill))
                stop_btn_item.setForeground(QColor(MacOSColors.SYSTEM_RED))
                btn_font = QFont()
                btn_font.setBold(True)
                stop_btn_item.setFont(btn_font)
                table_widget.setItem(row, 4, stop_btn_item)
            else:
                run_item = QTableWidgetItem("▶ 运行")
                run_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                run_item.setData(Qt.UserRole, ("run", skill))
                run_item.setForeground(QColor(MacOSColors.SYSTEM_GREEN))
                table_widget.setItem(row, 4, run_item)

            stop_shortcut = skill.get('stop_shortcut', '')
            shortcut_display = stop_shortcut if stop_shortcut else "点击设置"
            shortcut_item = QTableWidgetItem(shortcut_display)
            shortcut_item.setTextAlignment(Qt.AlignCenter)
            shortcut_item.setData(Qt.UserRole, skill)
            if not stop_shortcut:
                shortcut_item.setForeground(QColor(MacOSColors.TEXT_SECONDARY))
            table_widget.setItem(row, 5, shortcut_item)

            # 第6列：删除按钮(运行中不允许删除)
            if is_running:
                delete_item = QTableWidgetItem("运行中")
                delete_item.setForeground(QColor(MacOSColors.SYSTEM_GRAY3))
                delete_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            else:
                delete_item = QTableWidgetItem("🗑️ 删除")
                delete_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                delete_item.setData(Qt.UserRole, skill)
                delete_item.setForeground(QColor(MacOSColors.SYSTEM_RED))
                del_font = QFont()
                del_font.setBold(True)
                delete_item.setFont(del_font)
            table_widget.setItem(row, 6, delete_item)

    def _get_combo_manager(self):
        from app import ComboSkillManager
        return ComboSkillManager(self)

    def stop_combo_skill(self, skill=None):
        STOP_JOIN_TIMEOUT = 3.0
        def _wait_runner_finish(runner, timeout):
            try:
                if hasattr(runner, '_exec_thread') and runner._exec_thread is not None:
                    runner._exec_thread.join(timeout=timeout)
            except Exception:
                pass
            return True
        try:
            if skill is not None:
                skill_id = skill.get('name', '')
                if skill_id in self.runners and self.runners[skill_id].isRunning():
                    skill_name = skill.get('name', '未命名')
                    runner = self.runners[skill_id]
                    from image_recognition import set_replay_stop_flag
                    set_replay_stop_flag(True)
                    runner.running = False
                    if hasattr(runner, 'reset'):
                        try:
                            runner.reset()
                        except Exception:
                            pass
                    _wait_runner_finish(runner, STOP_JOIN_TIMEOUT)
                    if skill_id in self.runners:
                        del self.runners[skill_id]
                    self.append_log(f'[{skill_name}] 已停止')
            else:
                from image_recognition import set_replay_stop_flag
                set_replay_stop_flag(True)
                runners_to_reset = []
                for skill_id, runner in list(self.runners.items()):
                    if runner.isRunning():
                        runner.running = False
                        runners_to_reset.append((skill_id, runner))
                for skill_id, runner in runners_to_reset:
                    if hasattr(runner, 'reset'):
                        try:
                            runner.reset()
                        except Exception:
                            pass
                for skill_id, runner in runners_to_reset:
                    _wait_runner_finish(runner, STOP_JOIN_TIMEOUT)
                self.runners.clear()
                self.append_log('[组合技] 所有运行中的组合技已停止')
            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, '错误', f'停止组合技失败: {e}')

    def stop_selected_combo_skills(self, table_widget):
        STOP_JOIN_TIMEOUT = 3.0
        try:
            selected_skills = []
            for row in range(table_widget.rowCount()):
                check_item = table_widget.item(row, 0)
                if check_item and check_item.checkState() == Qt.Checked:
                    skill = check_item.data(Qt.UserRole)
                    if skill:
                        selected_skills.append(skill)
            if not selected_skills:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, '提示', '请先勾选要停止的组合技（勾选第一列的复选框）')
                return
            from image_recognition import set_replay_stop_flag
            set_replay_stop_flag(True)
            stop_count = 0
            for skill in selected_skills:
                skill_id = skill.get('name', '')
                if skill_id in self.runners and self.runners[skill_id].isRunning():
                    runner = self.runners[skill_id]
                    runner.running = False
                    if hasattr(runner, 'reset'):
                        try:
                            runner.reset()
                        except Exception:
                            pass
                    stop_count += 1
                    if skill_id in self.runners:
                        del self.runners[skill_id]
            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
            if stop_count > 0:
                self.append_log(f'已停止 {stop_count} 个组合技')
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, '错误', f'停止组合技失败: {e}')

    def _set_recording_state(self, state: bool):
        """统一设置录制状态并同步到 record_btn"""
        self.is_recording = state
        if hasattr(self, 'record_btn') and self.record_btn is not None:
            if hasattr(self.record_btn, 'set_is_recording'):
                self.record_btn.set_is_recording(state)

    def toggle_recording(self):
        """切换录制状态"""
        if self.is_recording:
            # 正在录制 → 停止（关闭坐标录制覆盖层）
            if hasattr(self, 'coord_recorder') and self.coord_recorder is not None:
                self.coord_recorder.close()
            self._set_recording_state(False)
            self.record_btn.setEnabled(True)
            current_mode = self.record_mode_combo.currentText()
            if current_mode == "图像录制":
                self.record_btn.setText("图像录制")
            elif current_mode == "坐标录制":
                self.record_btn.setText("坐标录制")
            if hasattr(self, 'record_action'):
                self.record_action.setText("开始录制")
            self.showNormal()
        else:
            try:
                self._set_recording_state(True)
                self.record_btn.setEnabled(False)
                self.record_btn.setText('录\n制\n中')
                if hasattr(self, 'record_action'):
                    self.record_action.setEnabled(False)
                    self.record_action.setText('🔴 录制中...')
                current_mode = self.record_mode_combo.currentText()
                self.showMinimized()
                if current_mode == "坐标录制":
                    QTimer.singleShot(300, self.start_coordinate_recording)
                else:
                    QTimer.singleShot(300, self.start_image_recording)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._set_recording_state(False)
                current_mode = self.record_mode_combo.currentText()
                if current_mode == "图像录制":
                    self.record_btn.setText("图像录制")
                elif current_mode == "坐标录制":
                    self.record_btn.setText("坐标录制")
                if hasattr(self, 'record_action'):
                    self.record_action.setText("开始录制")
                self.showNormal()
                self.show_beautiful_message('critical', '错误', f"启动录制失败: {str(e)}")

    def start_image_recording(self):
        try:
            from PyQt5.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            screen_pixmap = screen.grabWindow(0)
            self.current_recording_dir = None
            self.operation_count = 0
            if hasattr(self, 'selection_overlay') and self.selection_overlay:
                try:
                    self.selection_overlay.close()
                    self.selection_overlay.deleteLater()
                except:
                    pass
                self.selection_overlay = None
            from selection_overlay import SelectionOverlay
            self.selection_overlay = SelectionOverlay(self, screen_pixmap=screen_pixmap, recording_dir=None)
            self.selection_overlay.closed.connect(self.on_recording_finished)
            self.selection_overlay.show()
            self.selection_overlay.activateWindow()
            self.selection_overlay.raise_()
            self.selection_overlay.setFocus()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._set_recording_state(False)
            current_mode = self.record_mode_combo.currentText()
            if current_mode == '图像录制':
                self.record_btn.setText('图像录制')
            elif current_mode == '坐标录制':
                self.record_btn.setText('坐标录制')
            if hasattr(self, 'record_action'):
                self.record_action.setText('开始录制')
            self.showNormal()
            self.show_beautiful_message('critical', '错误', f'启动选择界面失败: {e}')

    def on_recording_finished(self):
        self._set_recording_state(False)
        self.record_btn.setEnabled(True)
        self.record_btn.setText('录\n制')
        if hasattr(self, 'manage_recordings_btn'):
            self.manage_recordings_btn.setEnabled(True)
        if hasattr(self, 'record_action'):
            self.record_action.setEnabled(True)
            self.record_action.setText('开始录制')
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if hasattr(self, 'selection_overlay') and self.selection_overlay:
            try:
                self.selection_overlay.deleteLater()
            except:
                pass
            self.selection_overlay = None
        if hasattr(self, 'folder_manager') and self.folder_manager.isVisible():
            self.folder_manager.load_folders()
        if hasattr(self, 'manager_tab') and hasattr(self.manager_tab, 'folder_table'):
            self.load_folders_to_table(self.manager_tab.folder_table)
        self.refresh_floating_window_list()
        self.current_recording_dir = None
        import gc
        gc.collect()

    def on_coordinate_recording_finished(self):
        """坐标录制完成处理"""
        if hasattr(self, 'coordinate_records') and self.coordinate_records:
            try:
                import json
                recording_json_path = os.path.join(self.current_recording_dir, "recording.json")
                with open(recording_json_path, 'w', encoding='utf-8') as f:
                    json.dump(self.coordinate_records, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
        self._set_recording_state(False)
        self.record_btn.setEnabled(True)
        current_mode = self.record_mode_combo.currentText()
        if current_mode == "图像录制":
            self.record_btn.setText("图像录制")
        elif current_mode == "坐标录制":
            self.record_btn.setText("坐标录制")
        if hasattr(self, 'record_action'):
            self.record_action.setEnabled(True)
            self.record_action.setText('开始录制')
        if hasattr(self, 'coord_recorder'):
            try:
                self.coord_recorder.deleteLater()
            except:
                pass
            self.coord_recorder = None
        if hasattr(self, 'manager_tab') and hasattr(self.manager_tab, 'folder_table'):
            self.load_folders_to_table(self.manager_tab.folder_table)
        self.showNormal()

    def start_coordinate_recording(self):
        """启动坐标录制模式（macOS版本）"""
        try:
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_recording_dir = os.path.join(recordings_dir, f"坐标录制_{timestamp}")
            os.makedirs(self.current_recording_dir, exist_ok=True)
            self.operation_count = 0
            self.coordinate_records = []
            self.coord_recorder = CoordinateRecorder(self)
            self.coord_recorder.closed.connect(self.on_coordinate_recording_finished)
            self.coord_recorder.show()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._set_recording_state(False)
            self.record_btn.setEnabled(True)
            current_mode = self.record_mode_combo.currentText()
            if current_mode == "图像录制":
                self.record_btn.setText("图像录制")
            elif current_mode == "坐标录制":
                self.record_btn.setText("坐标录制")
            if hasattr(self, 'record_action'):
                self.record_action.setText("开始录制")
            self.showNormal()
            self.show_beautiful_message('critical', '错误', f"启动坐标录制失败: {str(e)}")


class CoordinateRecorder(QWidget):
    """坐标录制覆盖层 - 记录鼠标点击位置"""
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.records = []
        self.step_counter = 0
        self._focus_timer = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        # 合并所有屏幕的总区域 (支持多显示器)
        total_geo = QRect()
        for s in QApplication.screens():
            total_geo = total_geo.united(s.geometry())
        if total_geo.isValid():
            self.setGeometry(total_geo)
        else:
            self.setGeometry(0, 0, 1920, 1080)

    def showEvent(self, event):
        super().showEvent(event)

    def _delayed_show(self):
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)
        QApplication.processEvents()
        self._focus_timer = QTimer()
        self._focus_timer.timeout.connect(self._ensure_focus)
        self._focus_timer.start(200)

    def _ensure_focus(self):
        if not self.hasFocus():
            self.raise_()
            self.activateWindow()
            self.setFocus(Qt.ActiveWindowFocusReason)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        font = QFont("PingFang SC, SimHei", 17)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))

        if self.step_counter == 0:
            text = "🖱️ 点击屏幕任意位置（记录并执行点击）\n按 Esc 或 右键 结束录制"
        else:
            text = f"✅ 已执行 {self.step_counter} 次点击\n🖱️ 请在当前界面选择下一个点击位置\n按 Esc 或 右键 结束录制"

        painter.drawText(self.rect(), Qt.AlignCenter, text)

    def _send_click_to_target(self, px, py):
        # PostMessage 直接发送点击到目标窗口，零残余事件
        import ctypes
        from ctypes import wintypes
        pt = wintypes.POINT(px, py)
        target_hwnd = ctypes.windll.user32.WindowFromPoint(pt)
        if not target_hwnd:
            return
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(target_hwnd, ctypes.byref(rect))
        cx = px - rect.left
        cy = py - rect.top
        lparam = (cy << 16) | (cx & 0xFFFF)
        ctypes.windll.user32.PostMessageW(target_hwnd, 0x201, 1, lparam)
        ctypes.windll.user32.PostMessageW(target_hwnd, 0x202, 0, lparam)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._finish_recording()
            return
        if event.button() == Qt.LeftButton:
            self.step_counter += 1
            screen = QApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            global_logical = self.mapToGlobal(event.pos())
            px = int(global_logical.x() * dpr)
            py = int(global_logical.y() * dpr)
            rec = {"step": self.step_counter, "action_type": "click", "x": px, "y": py, "delay": 0.3}
            self.records.append(rec)
            if self.parent and hasattr(self.parent, 'coordinate_records'):
                self.parent.coordinate_records = self.records

            # hide -> PostMessage -> show (零残余事件)
            self.hide()
            QApplication.processEvents()
            self._send_click_to_target(px, py)
            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus(Qt.ActiveWindowFocusReason)
            QApplication.processEvents()
            self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._finish_recording()
        super().keyPressEvent(event)

    def _finish_recording(self):
        if self._focus_timer:
            self._focus_timer.stop()
        self.closed.emit()
        self.close()


def start_macos_app():
    import sys
    import os
    import ctypes

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFont

    import ctypes
    try:
        ctypes.windll.kernel32.SetEnvironmentVariableW('QT_ENABLE_DIRECTWRITE', '1')
    except:
        pass
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    if sys.platform == "win32":
        try:
            whnd = ctypes.windll.kernel32.GetConsoleWindow()
            if whnd != 0:
                ctypes.windll.user32.ShowWindow(whnd, 0)
                ctypes.windll.user32.ShowWindow(whnd, 0)
            ctypes.windll.kernel32.SetEnvironmentVariableW("__COMPAT_LAYER", "RUNASINVOKER")
        except:
            pass

    import tempfile
    temp_dir = tempfile.gettempdir()
    os.chdir(temp_dir)

    app = QApplication(sys.argv)

    # 设置支持中文的字体（Windows上使用微软雅黑，macOS使用苹方）
    if sys.platform == "win32":
        font_name = "Microsoft YaHei"  # Windows
    else:
        font_name = "PingFang SC"  # macOS
    
    font = QFont(font_name, 17)
    font.setBold(True)
    font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
    font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(font)

    app.setStyle("Fusion")

    app.setStyleSheet(f"""
        QMainWindow, QWidget#centralWidget {{ border-radius: 16px; }}
        QToolTip {{
            background-color: {MacOSColors.CARD_BG};
            color: {MacOSColors.TEXT_PRIMARY};
            border: none;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 11px;
        }}
        QScrollBar:vertical {{
            background-color: transparent;
            width: 7px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {MacOSColors.SYSTEM_GRAY3}30;
            border-radius: 3px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {MacOSColors.SYSTEM_GRAY2}50;
        }}
        QScrollBar:horizontal {{
            background-color: transparent;
            height: 7px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {MacOSColors.SYSTEM_GRAY3}30;
            border-radius: 3px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {MacOSColors.SYSTEM_GRAY2}50;
        }}
    """)

    from login_manager import LoginManager

    login_manager = LoginManager()
    main_window = MacOSAutoRecorderApp(login_manager=login_manager)
    main_window.setWindowFlags(Qt.FramelessWindowHint)
    main_window.show()

    main_window.create_replay_status_indicator()


    sys.exit(app.exec_())


if __name__ == "__main__":
    start_macos_app()