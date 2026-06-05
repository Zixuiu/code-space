import os
import json
import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QScrollArea, QFrame,
    QSizePolicy, QLineEdit, QGridLayout, QGraphicsOpacityEffect,
    QCheckBox, QTextEdit, QComboBox, QSlider, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QSystemTrayIcon,
    QMessageBox, QPlainTextEdit, QListWidget, QListWidgetItem, QInputDialog,
    QAbstractItemView, QShortcut, QDialog, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, QRect, QRectF
)
from PyQt5.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QFontDatabase, QIcon, QPixmap,
    QKeySequence, QLinearGradient, QRadialGradient
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
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: {BorderRadiusSystem.MD}px;
                }}
            """)
            self.icon_label.setStyleSheet(f"""
                color: {MacOSColors.ACCENT};
                font-size: {TypographySystem.SIZE_LG}px;
            """)
            self.text_label.setStyleSheet(f"""
                color: {MacOSColors.ACCENT};
                font-size: {TypographySystem.SIZE_LG}px;
                font-weight: {TypographySystem.WEIGHT_BOLD};
                font-family: {TypographySystem.FONT_FAMILY};
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: {BorderRadiusSystem.MD}px;
                }}
                QFrame:hover {{
                    background-color: {MacOSColors.ACCENT_BG};
                }}
            """)
            self.icon_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: {TypographySystem.SIZE_LG}px;
            """)
            self.text_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: {TypographySystem.SIZE_LG}px;
                font-weight: {TypographySystem.WEIGHT_REGULAR};
                font-family: {TypographySystem.FONT_FAMILY};
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
            ("\u2699\ufe0f", "系统设置"),
            ("📖", "使用帮助"),
        ]

        for i, (icon, text) in enumerate(nav_items):
            item = MacOSSidebarItem(icon, text)
            item.clicked.connect(lambda checked=False, idx=i: self.set_active_tab(idx))
            self.items.append(item)
            layout.addWidget(item)

        layout.addStretch()

        user_frame = QFrame()
        user_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {MacOSColors.CARD_BG};
                border-radius: 12px;
            }}
        """)

        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(12, 10, 12, 10)
        user_layout.setSpacing(12)

        avatar = QLabel("\U0001f464")
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {MacOSColors.ACCENT_BG};
            border-radius: 19px;
            font-size: 18px;
        """)
        user_layout.addWidget(avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(2)

        self.name_label = QLabel("用户")
        self.name_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 15px;
            font-weight: 600;
        """)
        user_info.addWidget(self.name_label)

        self.status_label = QLabel("● 在线")
        self.status_label.setStyleSheet(f"""
            color: {MacOSColors.SYSTEM_GREEN};
            font-size: 12px;
        """)
        user_info.addWidget(self.status_label)

        user_layout.addLayout(user_info)
        user_layout.addStretch()

        layout.addWidget(user_frame)

        self.set_active_tab(0)

    def set_active_tab(self, index):
        for i, item in enumerate(self.items):
            item.set_selected(i == index)
        self.tab_changed.emit(index)

    def set_username(self, username):
        self.name_label.setText(username)


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
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
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
            }}
            QPushButton:hover {{
                background-color: {color}EE;
            }}
            QPushButton:pressed {{
                background-color: {color}CC;
                padding-top: 2px;
            }}
            QPushButton:disabled {{
                background-color: {color}66;
                color: rgba(255, 255, 255, 0.7);
            }}
        """)


class MacOSDestructiveButton(QPushButton):
    """危险按钮 - 红色破坏性操作（用于停止、删除等）"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        self.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.SYSTEM_RED};
                color: white;
                border: none;
                border-radius: {BorderRadiusSystem.MD}px;
                font-size: {TypographySystem.SIZE_BASE}px;
                font-weight: {TypographySystem.WEIGHT_SEMIBOLD};
                font-family: {TypographySystem.FONT_FAMILY};
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: {MacOSColors.SYSTEM_RED}EE;
            }}
            QPushButton:pressed {{
                background-color: {MacOSColors.SYSTEM_RED}CC;
                padding-top: 2px;
            }}
            QPushButton:disabled {{
                background-color: {MacOSColors.SYSTEM_RED}66;
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
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #F2F2F7;
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: {BorderRadiusSystem.MD}px;
                font-size: {TypographySystem.SIZE_BASE}px;
                font-weight: {TypographySystem.WEIGHT_MEDIUM};
                font-family: {TypographySystem.FONT_FAMILY};
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: #E5E5EA;
            }}
            QPushButton:pressed {{
                background-color: #D1D1D6;
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
        btn = MacOSButton("+ 新建组合技", MacOSColors.SYSTEM_GREEN)
        layout.addWidget(btn)
        _attach_button_shadow(btn, MacOSColors.SYSTEM_GREEN)
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
    """圆角方形录制按钮 - 黑白极简，大尺寸消除割裂感

    尺寸: 130x130 圆角方形 (圆角 28px)
    ┌──────────────────┐
    │                  │
    │    ● / ■         │
    │    录制 / 停止     │
    │                  │
    └──────────────────┘
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
        self._shape_progress = 0.0
        self._target_shape = 0.0
        self._pulse_t = 0.0

        # 图标形状过渡
        self._shape_anim = QPropertyAnimation(self, b"_shape_progress_anim")
        self._shape_anim.setDuration(280)
        self._shape_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # 脉冲动画
        self._pulse_anim = QPropertyAnimation(self, b"_pulse_progress_anim")
        self._pulse_anim.setDuration(1600)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_anim.start()

    # ---------------- Qt 属性 ----------------
    def _get_shape(self) -> float: return self._shape_progress
    def _set_shape(self, v: float):
        self._shape_progress = v
        self.update()
    _shape_progress_anim = pyqtProperty(float, _get_shape, _set_shape)

    def _get_pulse(self) -> float: return self._pulse_t
    def _set_pulse(self, v: float):
        self._pulse_t = v
        self.update()
    _pulse_progress_anim = pyqtProperty(float, _get_pulse, _set_pulse)

    # ---------------- 公开 API ----------------
    def set_is_recording(self, recording: bool):
        self._is_recording = recording
        self._target_shape = 1.0 if recording else 0.0
        self._shape_anim.stop()
        self._shape_anim.setStartValue(self._shape_progress)
        self._shape_anim.setEndValue(self._target_shape)
        self._shape_anim.start()
        self.update()

    def set_recording(self, recording: bool): self.set_is_recording(recording)
    def set_recording_state(self, state: bool): self.set_is_recording(state)
    def get_is_recording(self) -> bool: return self._is_recording

    def setText(self, text):
        super().setText(text)
        self.update()

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

        # ----- 1. 阴影(内置,避免外框割裂) -----
        sh_rect = QRectF(off + 2, off + 4, ss, ss)
        if self._is_recording:
            sh_a = 35
        else:
            bf = 0.5 + 0.5 * (0.5 + 0.5 * (1 - abs(self._pulse_t * 2 - 1)))
            sh_a = int(10 + 22 * bf)
        sh = QRadialGradient(cx + 2, cx + 4, s * 0.55)
        sh.setColorAt(0.0, QColor(0, 0, 0, sh_a))
        sh.setColorAt(0.6, QColor(0, 0, 0, sh_a // 2))
        sh.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(sh))
        painter.drawRoundedRect(sh_rect, cr * scale, cr * scale)

        # ----- 2. 底色 -----
        if self._is_recording:
            bg, bd = QColor("#2C2C2E"), QColor("#3A3A3C")
        elif self._hovered:
            bg, bd = QColor("#EBEBEB"), QColor("#C8C8C8")
        else:
            bg, bd = QColor("#FFFFFF"), QColor("#DADADA")

        painter.setPen(QPen(bd, 1.5))
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(rect, cr * scale, cr * scale)

        # ----- 3. 空闲态顶部柔光 -----
        if not self._is_recording:
            hl = QRadialGradient(cx, cx - s * 0.2, s * 0.5)
            hl.setColorAt(0.0, QColor(255, 255, 255, 170))
            hl.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(hl))
            painter.drawRoundedRect(rect, cr * scale, cr * scale)

        # ----- 4. 录制中: 旋转环 -----
        if self._is_recording:
            ring_r = rect.adjusted(-5, -5, 5, 5)
            span = 90 * 16
            start = int(self._pulse_t * 360 * 16) - span // 2
            painter.setPen(QPen(QColor("#8E8E93"), 2.5, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(ring_r, start, span)
            painter.setPen(QPen(QColor(255, 255, 255, 25), 1, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(ring_r, 0, 360 * 16)

        # ----- 5. 图标 ● ↔ ■ -----
        margin = 30
        area = s - margin * 2
        icon_d = area * (0.38 - self._shape_progress * 0.12)
        icon_r = icon_d * (0.5 - self._shape_progress * 0.38)
        icon_y = cx - icon_d / 2 - 10
        icon_rect = QRectF(cx - icon_d / 2, icon_y, icon_d, icon_d)

        ic = QColor(255, 255, 255, 245) if self._is_recording else QColor("#1C1C1E")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(ic))
        painter.drawRoundedRect(icon_rect, icon_r, icon_r)

        if self._is_recording:
            ih = QLinearGradient(icon_rect.center().x(), icon_rect.top(),
                                 icon_rect.center().x(), icon_rect.bottom())
            ih.setColorAt(0.0, QColor(255, 255, 255, 60))
            ih.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(ih))
            painter.drawRoundedRect(icon_rect, icon_r, icon_r)

        # ----- 6. 文字(图标下方) -----
        txt = self.text() or ""
        if txt:
            font = QFont(TypographySystem.FONT_FAMILY)
            font.setPixelSize(15)
            font.setWeight(QFont.DemiBold)
            painter.setFont(font)
            tc = QColor(255, 255, 255, 230) if self._is_recording else QColor("#1C1C1E")
            painter.setPen(tc)
            painter.drawText(QRectF(10, cx + 4, s - 20, cx - 6),
                             int(Qt.AlignCenter | Qt.TextWordWrap), txt)


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
        font = QFont(TypographySystem.FONT_FAMILY)
        font.setPixelSize(15)
        font.setWeight(QFont.Medium)
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
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {MacOSColors.TOOLBAR_BG};
                border-bottom: 1px solid {MacOSColors.SEPARATOR};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        for color in [MacOSColors.SYSTEM_RED, MacOSColors.SYSTEM_YELLOW, MacOSColors.SYSTEM_GREEN]:
            dot = QFrame()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border: none;
                    border-radius: 6px;
                }}
            """)
            controls_layout.addWidget(dot)

        layout.addWidget(controls)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: {TypographySystem.SIZE_MD}px;
            font-weight: {TypographySystem.WEIGHT_SEMIBOLD};
            font-family: {TypographySystem.FONT_FAMILY};
        """)
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("\U0001f50d 搜索")
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: none;
                border-radius: {BorderRadiusSystem.MD}px;
                padding: {SpacingSystem.SM}px {SpacingSystem.SM}px;
                font-size: {TypographySystem.SIZE_BASE}px;
                font-family: {TypographySystem.FONT_FAMILY};
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                background-color: {MacOSColors.CARD_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
            }}
        """)
        layout.addWidget(self.search_input)

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

    def run_selected_combo_skills(self, table_widget):
        """macOS版本：批量运行选中的组合技"""
        from PyQt5.QtWidgets import QMessageBox
        try:
            print(f"[MACOS COMBO] run_selected_combo_skills 被调用")
            print(f"[MACOS COMBO] login_manager.current_user={self.login_manager.current_user if hasattr(self, 'login_manager') else 'N/A'}")
            print(f"[MACOS COMBO] current_user={self.current_user if hasattr(self, 'current_user') else 'N/A'}")

            selected_skills = []
            for row in range(table_widget.rowCount()):
                check_item = table_widget.item(row, 0)
                if check_item and check_item.checkState() == Qt.Checked:
                    skill = check_item.data(Qt.UserRole)
                    if skill:
                        selected_skills.append(skill)
                        print(f"[MACOS COMBO] 选中: {skill.get('name', '?')}")

            print(f"[MACOS COMBO] 共选中 {len(selected_skills)} 个组合技")

            if not selected_skills:
                QMessageBox.information(self, "提示", "请先勾选要启动的组合技（勾选第一列的复选框）")
                return

            self.showMinimized()

            from image_recognition import clear_image_cache
            clear_image_cache()

            normal_skills = [s for s in selected_skills if not s.get('monitor_mode', False)]
            monitor_skills = [s for s in selected_skills if s.get('monitor_mode', False)]

            print(f"[MACOS COMBO] 普通{len(normal_skills)}, 监控={len(monitor_skills)}")

            from app import ComboSkillRunner
            import threading as _threading

            normal_runners = []
            for skill in normal_skills:
                skill_name = skill.get('name', '未命名')
                skill_id = skill.get('name', '')

                if skill_id in self.runners and self.runners[skill_id].isRunning():
                    print(f"[MACOS COMBO] '{skill_name}' 已在运行中，跳过")
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
                _sname = skill_name
                runner.finished.connect(lambda success, msg, sid=_sid: self._on_combo_skill_finished(success, msg, sid))
                runner.log_signal.connect(lambda msg, sname=_sname: print(f"[{sname}] {msg}"))
                runner.step_signal.connect(lambda step_info, sid=_sid: self._on_combo_step_changed(step_info, sid))

                _t = _threading.Thread(target=runner.run, daemon=True)
                runner._exec_thread = _t
                _t.start()
                print(f"[MACOS COMBO] 已启动  {skill_name}")

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
                    _sname = skill_name
                    runner.finished.connect(lambda success, msg, sid=_sid: self._on_combo_skill_finished(success, msg, sid))
                    runner.log_signal.connect(lambda msg, sname=_sname: print(f"[{sname}] {msg}"))
                    runner.step_signal.connect(lambda step_info, sid=_sid: self._on_combo_step_changed(step_info, sid))

                    _t = _threading.Thread(target=runner.run, daemon=True)
                    runner._exec_thread = _t
                    _t.start()

            print(f"[MACOS COMBO] 所有组合技启动完成")
            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[MACOS COMBO] 运行组合技失败: {e}")

    def run_combo_skill_in_tab(self, skill):
        """在macOS组合技tab页中运行单个组合技"""
        from PyQt5.QtWidgets import QMessageBox
        try:
            skill_name = skill.get('name', '未命名')
            skill_id = skill.get('name', '')
            print(f"[MACOS COMBO] run_combo_skill_in_tab: {skill_name}")

            if skill_id in self.runners and self.runners[skill_id].isRunning():
                QMessageBox.warning(self, "提示", f"组合技 '{skill_name}' 正在运行中，请先停止后再执行")
                return

            max_parallel = 3
            running_count = len([r for r in self.runners.values() if r.isRunning()])
            if running_count >= max_parallel:
                QMessageBox.warning(self, "提示", f"最多同时运行{max_parallel}个组合技，当前已有{running_count}个在运行")
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

            runner.finished.connect(lambda success, msg, sid=skill_id: self._on_combo_skill_finished(success, msg, sid))
            runner.log_signal.connect(lambda msg, sname=skill_name: print(f"[{sname}] {msg}"))
            runner.step_signal.connect(lambda step_info, sid=skill_id: self._on_combo_step_changed(step_info, sid))

            _t = _threading.Thread(target=runner.run, daemon=True)
            runner._exec_thread = _t
            _t.start()
            print(f"[MACOS COMBO] 已启动单个组合技: {skill_name}")

            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[MACOS COMBO] 运行单个组合技失败: {e}")

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
        self.setMinimumSize(1200, 700)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.macos_toolbar = MacOSToolbar("录制控制")
        main_layout.addWidget(self.macos_toolbar)

        body = QWidget()
        body.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        print("[MACOS DEBUG] macOS initUI called, stylesheet cleared", flush=True)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.macos_sidebar = MacOSSidebar()
        self.macos_sidebar.tab_changed.connect(self.on_macos_tab_changed)
        body_layout.addWidget(self.macos_sidebar)

        self.macos_stack = QStackedWidget()
        self.macos_stack.setStyleSheet("background-color: transparent;")

        self.record_tab = self.create_record_tab()
        self.manager_tab = self.create_manager_tab()
        self.combo_tab = self.create_combo_tab()
        self.settings_tab = self.create_settings_tab()
        self.help_tab = self.create_help_tab()

        self.macos_stack.addWidget(self.record_tab)
        self.macos_stack.addWidget(self.manager_tab)
        self.macos_stack.addWidget(self.combo_tab)
        self.macos_stack.addWidget(self.settings_tab)
        self.macos_stack.addWidget(self.help_tab)

        body_layout.addWidget(self.macos_stack, 1)
        main_layout.addWidget(body, 1)

        self.create_tray_icon()

        if self.current_user:
            self.macos_sidebar.set_username(self.current_user)

        self._macos_titles = [
            "录制控制", "流程管理", "组合技",
            "系统设置", "使用帮助"
        ]

        self.fade_animation = None
        self.macos_stack.setCurrentIndex(0)

        print("[MACOS] Applying macOS design system stylesheet...", flush=True)
        # 使用新的设计系统生成统一样式
        self.setStyleSheet(generate_macos_theme())
        body.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        print("[MACOS] Design system stylesheet applied successfully", flush=True)

    def on_macos_tab_changed(self, index):
        if self.macos_stack.currentIndex() == index:
            return
        self.macos_toolbar.set_title(self._macos_titles[index])

        new_page = self.macos_stack.widget(index)

        opacity_effect = QGraphicsOpacityEffect(new_page)
        new_page.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0)

        self.macos_stack.setCurrentIndex(index)

        self.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_animation.setDuration(250)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, 'replay_status_widget'):
            self.create_replay_status_indicator()
        elif hasattr(self, 'replay_status_label'):
            self.update_replay_status_indicator()

    def create_tab_ui(self, main_layout):
        pass

    def create_record_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setSpacing(24)
        layout.setContentsMargins(32, 28, 32, 12)
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
            background: transparent;
            border: none;
        """)
        card_layout.addWidget(record_title)

        record_area = QWidget()
        record_area.setFixedHeight(130)
        record_area.setStyleSheet("background: transparent; border: none;")
        record_layout = QHBoxLayout(record_area)
        record_layout.setSpacing(16)
        record_layout.setContentsMargins(0, 0, 0, 0)

        # 自绘圆角方形按钮: 130x130, 黑白极简, 文字内嵌, 自带阴影
        self.record_btn = RoundedRecordButton()
        self.record_btn.clicked.connect(lambda: QTimer.singleShot(0, self.toggle_recording))
        record_layout.addWidget(self.record_btn)

        mode_widget = QWidget()
        mode_widget.setStyleSheet("background: transparent; border: none;")
        mode_layout = QVBoxLayout(mode_widget)
        mode_layout.setSpacing(8)
        mode_layout.setContentsMargins(0, 0, 0, 0)

        mode_label = QLabel("录制模式")
        mode_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 13px;
            font-weight: 500;
            background: transparent;
        """)
        mode_layout.addWidget(mode_label)

        self.record_mode_combo = QComboBox()
        self.record_mode_combo.addItems(["图像录制", "坐标录制"])
        self.record_mode_combo.setFixedWidth(180)
        self.record_mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                border-color: {MacOSColors.ACCENT};
            }}
            QComboBox:focus {{
                border-color: {MacOSColors.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                selection-background-color: {MacOSColors.ACCENT_BG};
                selection-color: {MacOSColors.ACCENT};
                padding: 4px;
            }}
        """)
        self.record_mode_combo.currentTextChanged.connect(self.update_record_button_text)
        mode_layout.addWidget(self.record_mode_combo)
        record_layout.addWidget(mode_widget)
        record_layout.addStretch()
        card_layout.addWidget(record_area)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {MacOSColors.SEPARATOR};")
        card_layout.addWidget(separator)

        replay_area = QWidget()
        replay_area.setStyleSheet("background: transparent; border: none;")
        replay_layout = QHBoxLayout(replay_area)
        replay_layout.setSpacing(16)
        replay_layout.setContentsMargins(0, 0, 0, 0)

        self.replay_btn = RoundedPillButton(
            "▶ 开始回放",
            color_top="#FFFFFF",
            color_mid="#F8F8FA",
            color_bottom="#E8E8ED",
            text_color=MacOSColors.TEXT_PRIMARY
        )
        self.replay_btn.setFixedHeight(48)
        self.replay_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_LARGE + 20)
        self.replay_btn.clicked.connect(self.toggle_replay_playback)
        replay_layout.addWidget(self.replay_btn)

        float_btn = RoundedPillButton(
            "悬浮窗口",
            color_top="#5AC8FA",
            color_mid="#007AFF",
            color_bottom="#0062CC",
            text_color="white"
        )
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
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)

        refresh_btn = MacOSSecondaryButton("🔄 刷新")
        refresh_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        header.addWidget(refresh_btn)
        _attach_button_shadow(refresh_btn, "#000000", blur_radius=12, offset_y=2, alpha=25)

        trash_btn = MacOSDestructiveButton("🗑 回收站")
        trash_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(trash_btn)
        _attach_button_shadow(trash_btn, MacOSColors.SYSTEM_RED)
        header.addStretch()
        layout.addLayout(header)

        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
        folder_table = QTableWidget()
        folder_table.setColumnCount(5)
        folder_table.setHorizontalHeaderLabels(["时间", "流程名称", "快捷键", "重命名", "删除"])
        folder_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 12px;
                background: {MacOSColors.CARD_BG};
                outline: none;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {MacOSColors.SEPARATOR}60;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QTableWidget::item:hover {{
                background: {MacOSColors.ACCENT_BG};
            }}
            QTableWidget::item:selected {{
                background: {MacOSColors.ACCENT_BG};
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_SECONDARY};
                padding: 10px 12px;
                border: none;
                border-bottom: 1px solid {MacOSColors.SEPARATOR};
                font-weight: 600;
                font-size: 12px;
            }}
            QScrollBar:vertical {{
                width: 0px;
                background: transparent;
            }}
            QScrollBar:horizontal {{
                height: 0px;
                background: transparent;
            }}
        """)
        folder_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        folder_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        folder_table.horizontalHeader().setStretchLastSection(True)
        folder_table.verticalHeader().setVisible(False)

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

            table_widget.setColumnWidth(0, 100)
            table_widget.setColumnWidth(1, 200)
            table_widget.setColumnWidth(2, 80)
            table_widget.setColumnWidth(3, 70)
            table_widget.setColumnWidth(4, 55)

        except Exception as e:
            pass

    def set_folder_shortcut_in_tab(self, folder_path, table_widget):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import Qt, QTimer

        folder_name = os.path.basename(folder_path)
        current_shortcut = self.get_folder_shortcut(folder_path)

        self.temporarily_disable_grave_hotkey()

        dialog = QDialog(self)
        dialog.setWindowTitle("设置快捷键")
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        width, height = get_screen_size(0.3)
        dialog.resize(width, int(height * 0.25))
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
            font-family: 'PingFang SC', 'Microsoft YaHei UI', 'Helvetica Neue', 'Segoe UI', sans-serif;
            background: transparent;
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
            font-family: 'PingFang SC', 'Microsoft YaHei UI', 'Helvetica Neue', 'Segoe UI', sans-serif;
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
                font-family: 'PingFang SC', 'Microsoft YaHei UI', 'Helvetica Neue', 'Segoe UI', sans-serif;
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
                font-family: 'PingFang SC', 'Microsoft YaHei UI', 'Helvetica Neue', 'Segoe UI', sans-serif;
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
                font-family: 'PingFang SC', 'Microsoft YaHei UI', 'Helvetica Neue', 'Segoe UI', sans-serif;
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
                font-family: 'PingFang SC', 'Microsoft YaHei UI', 'Helvetica Neue', 'Segoe UI', sans-serif;
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
                font-family: 'PingFang SC', 'Microsoft YaHei UI', 'Helvetica Neue', 'Segoe UI', sans-serif;
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
            background: transparent;
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
                font-family: 'PingFang SC', 'Microsoft YaHei UI', 'Helvetica Neue', 'Segoe UI', sans-serif;
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
                    old_path_normalized = os.path.normpath(str(folder_path)).lower()
                    new_path_normalized = os.path.normpath(str(new_path)).lower()
                    if old_path_normalized in self.shortcuts:
                        self.shortcuts[new_path_normalized] = self.shortcuts.pop(old_path_normalized)
                        self.save_shortcut_config()
                        self.update_shortcuts()
                self.load_folders_to_table(table_widget)
                dialog.accept()
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"重命名失败: {e}")

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
            background: transparent;
        """)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        hint_label = QLabel("该流程将移动到回收站")
        hint_label.setStyleSheet(f"""
            font-size: 12px;
            color: {MacOSColors.TEXT_SECONDARY};
            background: transparent;
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
                self.load_folders_to_table(table_widget)
                dialog.accept()
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"删除失败: {e}")

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
        status_text.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {MacOSColors.TEXT_SECONDARY}; background: transparent;")
        status_layout.addWidget(status_text)

        running_names_label = QLabel("")
        running_names_label.setStyleSheet(f"font-size: 12px; color: {MacOSColors.SYSTEM_GREEN}; background: transparent;")
        status_layout.addWidget(running_names_label)
        status_layout.addStretch()

        status_bar.setVisible(True)
        layout.addWidget(status_bar)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        new_btn = MacOSButton("+ 新建组合技", MacOSColors.SYSTEM_GREEN)
        new_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_LARGE)
        top_layout.addWidget(new_btn)
        _attach_button_shadow(new_btn, MacOSColors.SYSTEM_GREEN)

        refresh_btn = MacOSSecondaryButton("🔄 刷新")
        refresh_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        top_layout.addWidget(refresh_btn)
        _attach_button_shadow(refresh_btn, "#000000", blur_radius=12, offset_y=2, alpha=25)

        run_selected_btn = MacOSButton("▶ 启动选中", MacOSColors.ACCENT)
        run_selected_btn.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        top_layout.addWidget(run_selected_btn)
        _attach_button_shadow(run_selected_btn, MacOSColors.ACCENT)

        stop_selected_btn = MacOSDestructiveButton("⏹ 停止选中")
        stop_selected_btn.setCursor(Qt.PointingHandCursor)
        top_layout.addWidget(stop_selected_btn)
        _attach_button_shadow(stop_selected_btn, MacOSColors.SYSTEM_RED)

        stop_all_btn = MacOSDestructiveButton("⏹ 全部停止")
        stop_all_btn.setCursor(Qt.PointingHandCursor)
        stop_all_btn.setVisible(False)
        top_layout.addWidget(stop_all_btn)
        _attach_button_shadow(stop_all_btn, MacOSColors.SYSTEM_RED)

        top_layout.addStretch()
        layout.addLayout(top_layout)

        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
        combo_table = QTableWidget()
        combo_table.setColumnCount(7)
        combo_table.setHorizontalHeaderLabels(["选择", "组合技名称", "流程数", "状态", "操作", "停止快捷键", "删除"])
        combo_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 12px;
                background: {MacOSColors.CARD_BG};
                outline: none;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 6px 12px;
                border-bottom: 1px solid {MacOSColors.SEPARATOR}60;
                min-height: 40px;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QTableWidget::item:hover {{
                background: {MacOSColors.ACCENT_BG};
            }}
            QTableWidget::item:selected {{
                background: {MacOSColors.ACCENT_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                min-height: 40px;
            }}
            QHeaderView::section {{
                background: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_SECONDARY};
                padding: 6px 12px;
                border: none;
                border-bottom: 1px solid {MacOSColors.SEPARATOR};
                font-weight: 600;
                font-size: 12px;
            }}
        """)
        combo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        combo_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        combo_table.horizontalHeader().setStretchLastSection(True)
        combo_table.verticalHeader().setVisible(False)
        combo_table.verticalHeader().setDefaultSectionSize(40)

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
        self._combo_refresh_timer.start(1000)

        return tab

    def create_settings_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 12)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("系统设置")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 24px;
            font-weight: 700;
            padding-bottom: 8px;
            background: transparent;
        """)
        layout.addWidget(title)

        settings_list = [
            ("🎨", "字体大小设置", "调整界面字体大小", self.open_font_size_dialog),
            ("⌨️", "快捷键设置", "配置全局快捷键", self.show_shortcut_settings),
            ("📋", "查看运行日志", "查看应用程序运行日志", self.show_log_window),
        ]

        for icon, name, desc, handler in settings_list:
            card = MacOSCard()
            card.setCursor(Qt.PointingHandCursor)
            card.setMinimumHeight(60)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(20, 14, 20, 14)
            cl.setSpacing(16)

            icon_label = QLabel(icon)
            icon_label.setFixedSize(36, 36)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(f"""
                background-color: {MacOSColors.ACCENT_BG};
                border-radius: 18px;
                font-size: 18px;
            """)
            cl.addWidget(icon_label)

            text_container = QVBoxLayout()
            text_container.setSpacing(2)
            name_label = QLabel(name)
            name_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 15px;
                font-weight: 600;
                background: transparent;
            """)
            text_container.addWidget(name_label)

            desc_label = QLabel(desc)
            desc_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 13px;
                background: transparent;
            """)
            text_container.addWidget(desc_label)
            cl.addLayout(text_container, 1)

            arrow = QLabel("›")
            arrow.setStyleSheet(f"""
                color: {MacOSColors.SYSTEM_GRAY};
                font-size: 22px;
                font-weight: 300;
                background: transparent;
            """)
            cl.addWidget(arrow)

            layout.addWidget(card)

            card.mousePressEvent = lambda e, h=handler: (h(), e.accept()) if h else QFrame.mousePressEvent(card, e)

        layout.addStretch()
        return tab

    def create_help_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 12)

        title = QLabel("使用帮助")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 24px;
            font-weight: 700;
            padding-bottom: 4px;
            background: transparent;
        """)
        layout.addWidget(title)

        card = MacOSCard()
        help_layout = QVBoxLayout(card)
        help_layout.setContentsMargins(24, 24, 24, 24)
        help_layout.setSpacing(16)

        sections = [
            ("⌨️ 快捷键", [
                "· 键：开始/停止录制",
                "Home 键：回到主窗口",
            ]),
            ("🎬 录制流程", [
                "点击「录制」按钮开始录制操作",
                "再次点击或按 · 键停止录制",
                "录制完成后可在「流程管理」中查看",
            ]),
            ("🔧 流程管理", [
                "在「流程管理」标签页管理录制",
                "支持重命名、设置快捷键、删除等操作",
            ]),
            ("⚙️ 组合技", [
                "在「组合技」标签页创建组合流程",
                "根据条件自动选择并执行多个录制流程",
            ]),
        ]

        for sec_title, items in sections:
            sec_label = QLabel(sec_title)
            sec_label.setStyleSheet(f"""
                color: {MacOSColors.ACCENT};
                font-size: 16px;
                font-weight: 600;
                background: transparent;
            """)
            help_layout.addWidget(sec_label)

            for item in items:
                item_label = QLabel(f"  {item}")
                item_label.setStyleSheet(f"""
                    color: {MacOSColors.TEXT_PRIMARY};
                    font-size: 14px;
                    line-height: 1.8;
                    background: transparent;
                """)
                help_layout.addWidget(item_label)

        layout.addWidget(card)
        layout.addStretch()
        return tab

    def load_combo_skills_to_table(self, table_widget):
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

        combo_manager = self._get_combo_manager()
        combo_skills = combo_manager.combo_skills

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
                    tab.status_text.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {MacOSColors.SYSTEM_GREEN}; background: transparent;")
                    tab.running_names_label.setText("  ".join(running_skill_names))
                    tab.running_names_label.setVisible(True)
                    tab.stop_all_btn.setVisible(True)
                else:
                    tab.status_text.setText("组合技运行状态：空闲")
                    tab.status_text.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {MacOSColors.TEXT_SECONDARY}; background: transparent;")
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

def start_macos_app():
    import sys
    import os
    import ctypes

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFont

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
    
    font = QFont(font_name, 13)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    app.setStyle("Fusion")

    app.setStyleSheet(f"""
        QToolTip {{
            background-color: {MacOSColors.CARD_BG};
            color: {MacOSColors.TEXT_PRIMARY};
            border: none;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 11px;
        }}
        QScrollBar:vertical {{
            background: transparent;
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
            background: transparent;
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
    main_window.show()

    main_window.create_replay_status_indicator()

    sys.exit(app.exec_())


if __name__ == "__main__":
    start_macos_app()









