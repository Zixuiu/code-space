import os
import json
import sys
import time
import math
import gc
import shutil
import ctypes
import traceback
import threading
from datetime import datetime

if os.name == "nt":
    os.environ["QT_ENABLE_DIRECTWRITE"] = "1"

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
    Qt, QTimer, QEventLoop, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, QRect, QRectF, QObject, QEvent
)
from PyQt5.QtGui import (
    QGuiApplication,
    QColor, QPainter, QBrush, QPen, QFont, QFontDatabase, QIcon, QPixmap,
    QKeySequence, QLinearGradient, QRadialGradient, QRegion, QPainterPath
)

from app import AutoRecorderApp, ComboSkillRunner, FolderManager
from utils import (
    get_screen_size, load_json_data, save_json_data,
    get_user_data_path, get_recordings_path, get_app_base_dir,
    log_info, log_error, log_warning, log_debug, log_exception,
    is_admin, run_as_admin
)
from combo_skill_manager import ComboSkillManager
from image_recognition import clear_image_cache, clear_replay_stop_flag, set_replay_stop_flag
from design_system import (
    TypographySystem, SpacingSystem, BorderRadiusSystem,
    ColorPalette, ShadowSystem, ButtonSize, configure_table, get_table_stylesheet,
    flat_button_style,
    configure_soft_card_table, configure_row_card_table
)
from theme_generator import generate_macos_theme
from beautiful_dialog import StyledMessageDialog
from combo_skill_edit_dialog import ComboSkillEditDialog
from selection_overlay import SelectionOverlay

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

    # 别名（对话框样式直接引用，语义更直白）
    PRIMARY = ColorPalette.PRIMARY
    PRIMARY_BG = ColorPalette.PRIMARY_BG  # 与 ACCENT_BG 同值，供键帽/对话框样式引用
    PRIMARY_HOVER = ColorPalette.PRIMARY_HOVER
    PRIMARY_ACTIVE = ColorPalette.PRIMARY_ACTIVE
    BG_MAIN = ColorPalette.BG_MAIN
    BG_HOVER = ColorPalette.BG_HOVER
    TEXT_MUTED = ColorPalette.TEXT_MUTED
    BORDER_DEFAULT = ColorPalette.BORDER_DEFAULT
    BORDER_STRONG = ColorPalette.BORDER_STRONG
    ERROR_BG = ColorPalette.ERROR_BG



_COLUMN_WIDTHS_FILE = os.path.join(get_user_data_path(), "table_column_widths.json")

def _apply_saved_column_widths(table, table_id, default_widths):
    saved = load_json_data(_COLUMN_WIDTHS_FILE, {})
    widths = saved.get(table_id, None)
    if widths and len(widths) == len(default_widths):
        for col, w in enumerate(widths):
            if isinstance(w, (int, float)) and w > 0:
                table.setColumnWidth(col, int(w))
    else:
        for col, w in enumerate(default_widths):
            table.setColumnWidth(col, w)

def _connect_column_width_saver(table, table_id):
    _save_timer = QTimer(table)
    _save_timer.setSingleShot(True)
    _save_timer.setInterval(500)
    table._column_width_save_timer = _save_timer

    def _do_save():
        saved = load_json_data(_COLUMN_WIDTHS_FILE, {})
        widths = []
        for col in range(table.columnCount()):
            widths.append(table.columnWidth(col))
        saved[table_id] = widths
        save_json_data(_COLUMN_WIDTHS_FILE, saved)

    _save_timer.timeout.connect(_do_save)

    def _on_section_resized(logical_index, old_size, new_size):
        _save_timer.start()

    table.horizontalHeader().sectionResized.connect(_on_section_resized)


class MacOSSidebarItem(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.is_selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setMaximumHeight(44)
        # 去掉 QFrame 默认可能带的面板边框/阴影
        self.setFrameStyle(QFrame.NoFrame)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignVCenter)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignCenter)
        _svg = load_svg_icon(icon, 18)
        if not _svg.isNull():
            self.icon_label.setPixmap(_svg.pixmap(int(round(18 * ICON_SCALE)), int(round(18 * ICON_SCALE))))
        else:
            self.icon_label.setText(icon)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
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
            self.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border: none;
                    outline: none;
                }
            """)
            self.icon_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: {TypographySystem.SIZE_LG}px;
                border: none;
            """)
            self.text_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: {TypographySystem.SIZE_LG}px;
                font-weight: {TypographySystem.WEIGHT_BOLD};
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
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
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
            ("camera", "录制控制"),
            ("folder", "流程管理"),
            ("layers", "组合技"),
            ("gear", "设置"),
            ("book", "使用帮助"),
            ("feedback", "反馈"),
        ]

        for i, (icon, text) in enumerate(nav_items):
            item = MacOSSidebarItem(icon, text)
            item.clicked.connect(lambda checked=False, idx=i: self.set_active_tab(idx))
            self.items.append(item)
            layout.addWidget(item)

        layout.addStretch()

        # 账户入口（内嵌登录页，方案 7-7）：底部 + 登录状态徽标
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {MacOSColors.SEPARATOR}; border: none;")
        layout.addWidget(divider)
        layout.addSpacing(6)

        account_item = MacOSSidebarItem("member", "账户")
        account_item.clicked.connect(lambda checked=False, idx=len(nav_items): self.set_active_tab(idx))
        self._account_badge = QLabel("未登录")
        self._account_badge.setAlignment(Qt.AlignCenter)
        self._style_account_badge(logged_in=False)
        account_item.layout().addWidget(self._account_badge)
        self.items.append(account_item)
        layout.addWidget(account_item)

        self.set_active_tab(0)

    def _style_account_badge(self, logged_in):
        """账户徽标样式：未登录红色 / 已登录浅灰用户名胶囊"""
        if logged_in:
            self._account_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: #EDEEF0;
                    color: #48484A;
                    font-size: 10px;
                    font-weight: 500;
                    font-family: {TypographySystem.FONT_FAMILY};
                    border: none;
                    border-radius: 7px;
                    padding: 1px 8px;
                }}
            """)
        else:
            self._account_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: #FFE5E5;
                    color: #FF3B30;
                    font-size: 10px;
                    font-weight: 500;
                    font-family: {TypographySystem.FONT_FAMILY};
                    border: none;
                    border-radius: 7px;
                    padding: 1px 8px;
                }}
            """)

    def set_active_tab(self, index):
        for i, item in enumerate(self.items):
            item.set_selected(i == index)
        self.tab_changed.emit(index)

    def set_username(self, username):
        """内嵌登录成功后更新账户徽标（None = 未登录）"""
        if getattr(self, '_account_badge', None) is None:
            return
        if username:
            self._account_badge.setText(username)
            self._style_account_badge(logged_in=True)
        else:
            self._account_badge.setText("未登录")
            self._style_account_badge(logged_in=False)


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
                border-radius: {BorderRadiusSystem.SM}px;
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
    def _adjust_color_opacity(color_hex, opacity):
        """调整颜色透明度，返回 Qt 样式表要求的 #AARRGGBB 格式（透明度在最前）"""
        color_hex = color_hex.lstrip('#')
        if len(color_hex) == 6:
            alpha = hex(int(opacity * 255))[2:].upper().zfill(2)
            return f"#{alpha}{color_hex}"
        return color_hex
    



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
        hover_color = MacOSButton._adjust_color_opacity(color, 0.93)
        pressed_color = MacOSButton._adjust_color_opacity(color, 0.8)
        disabled_color = MacOSButton._adjust_color_opacity(color, 0.4)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: {BorderRadiusSystem.SM}px;
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


# ---- 新拟态风格 SVG 图标加载（第 8 套：拟物凸起） ----
# 图标文件放在与本模块同级的 icons/ 目录下，用绝对路径定位，避免启动后 cwd 变化找不到。
# PyInstaller onefile 兜底：模块 __file__ 在 _MEIPASS 解压目录，datas 已含 ('icons','icons')。
_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
if not os.path.isdir(_ICON_DIR) and getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    _ICON_DIR = os.path.join(sys._MEIPASS, "icons")


# 图标统一放大系数（用户反馈图标偏小）——改这一个值即可全局调整所有图标大小
ICON_SCALE = 1.8

def load_svg_icon(name, size=27, color=None):
    """加载 icons/ 目录下的 SVG 图标并渲染为 QIcon（矢量，任意缩放清晰）。

    跑 / 启动 共用 play，停止 共用 stop，刷新 用 refresh。
    color 为 None 时保留 SVG 原有语义配色（绿=运行/红=删除/蓝=信息/灰=中性）；
    传 color 则把所有非背景色统一为该色。
    """
    import re
    size = int(round(size * ICON_SCALE))
    path = os.path.join(_ICON_DIR, name + ".svg")
    try:
        from PyQt5.QtSvg import QSvgRenderer
        from PyQt5.QtCore import QByteArray
        if color is None:
            renderer = QSvgRenderer(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                svg = f.read()
            # 保留背景凸块/阴影与透明，其余 fill/stroke 统一为指定色
            _preserve = {"#ECEFF4", "#C5CEDB", "none", "transparent"}
            def _repl_attr(m):
                attr, val = m.group(1), m.group(2)
                if val.lower() in ("none", "transparent") or val.upper() in _preserve:
                    return m.group(0)
                return f'{attr}="{color}"'
            svg = re.sub(r'\b(fill|stroke)="([^"]+)"', _repl_attr, svg)
            def _repl_style(m):
                attr, val = m.group(1), m.group(2)
                if val.lower() in ("none", "transparent") or val.upper() in _preserve:
                    return m.group(0)
                return f'{attr}:{color}'
            svg = re.sub(r'\b(fill|stroke):([^;\s]+)', _repl_style, svg)
            renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        if not renderer.isValid():
            return QIcon()
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        return QIcon(pix)
    except Exception:
        return QIcon()


def _set_table_icon_centered(table, row, col, icon_name, size):
    """在 QTableWidget 单元格中显示一个严格水平+垂直居中的图标。

    QTableWidgetItem 的 setIcon + setTextAlignment 在不同平台/风格下不一定能让图标居中，
    用 QLabel 作为 cell widget 并开启鼠标事件穿透，可保证居中且不影响表格点击逻辑。
    """
    icon = load_svg_icon(icon_name, size)
    render_size = int(round(size * ICON_SCALE))
    pixmap = icon.pixmap(QSize(render_size, render_size))
    if pixmap.isNull():
        table.removeCellWidget(row, col)
        return None
    label = QLabel()
    label.setPixmap(pixmap)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("background-color: transparent; border: none;")
    label.setAttribute(Qt.WA_TransparentForMouseEvents)
    table.setCellWidget(row, col, label)
    return label


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
                color: #5A6069;
                border: 1px solid #D1D1D6;
                border-radius: {BorderRadiusSystem.SM}px;
                font-size: {TypographySystem.SIZE_BASE}px;
                font-weight: {TypographySystem.WEIGHT_SEMIBOLD};
                font-family: {TypographySystem.FONT_FAMILY};
                padding: 0 {ButtonSize.PADDING_H_REGULAR}px;
                min-height: {ButtonSize.HEIGHT_REGULAR}px;
            }}
            QPushButton:hover {{
                background-color: #F0F0F2;
                color: #474C54;
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


class ApplePillButton(QPushButton):
    """苹果官网风药丸按钮 - paintEvent 自绘圆角，保证任何环境下都是完整药丸形"""

    def __init__(self, text="", bg="#0071E3", fg="#FFFFFF",
                 hover="#0077ED", pressed="#006EDB",
                 font_size=14, bold=True, arrow=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._bg = bg
        self._fg = fg
        self._hover = hover
        self._pressed = pressed
        self._font_size = font_size
        self._bold = bold
        self._show_arrow = arrow
        self._hovered = False
        self._down = False
        self.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        self.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._down = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._down = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._down = False
        self.update()
        super().mouseReleaseEvent(event)

    def setText(self, text):
        super().setText(text)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        r = 8.0
        color = self._pressed if self._down else (self._hover if self._hovered else self._bg)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        painter.drawRoundedRect(QRectF(self.rect()), r, r)

        # 文字（整体居中；带箭头时文字略偏左，箭头固定在右侧）
        text = self.text().replace('\t', ' ')
        font = painter.font()
        font.setPixelSize(self._font_size + 2)
        font.setBold(self._bold)
        painter.setFont(font)
        painter.setPen(QColor(self._fg))
        rect = self.rect()
        if self._show_arrow:
            text_rect = QRectF(rect.x() + 10, rect.y(), rect.width() - 44, rect.height())
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
            painter.drawText(QRectF(rect.right() - 30, rect.y(), 22, rect.height()),
                             Qt.AlignCenter, "▾")
        else:
            painter.drawText(QRectF(rect), Qt.AlignCenter, text)
        painter.end()


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

        # 旋转/脉冲动画（转一圈 3 秒）
        self._anim = QPropertyAnimation(self, b"_anim_progress")
        self._anim.setDuration(3000)
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
        painter.end()


class RoundedPillButton(QPushButton):
    """自绘的 iOS 药丸形按钮 - paintEvent 保证所有平台都是绝对圆润"""
    def __init__(self, text="", color_top="#6E747C", color_mid="#5A6069", color_bottom="#474C54",
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
        self.setMinimumHeight(ButtonSize.HEIGHT_REGULAR)
        self.setMinimumWidth(ButtonSize.MIN_WIDTH_REGULAR)
        # 留少量边距给阴影，让按钮看起来更立体
        self.setContentsMargins(0, 1, 0, 3)

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
        radius = 8.0

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
        font.setPixelSize(TypographySystem.SIZE_BASE)
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
            font-weight: {TypographySystem.WEIGHT_MEDIUM};
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
        # 内嵌登录（方案 7-7）：未登录时使用占位用户名，登录成功后再真正写入
        self._placeholder_user = False
        if username is None and login_manager is not None:
            username = getattr(login_manager, 'current_user', None)
        if username is None:
            username = "未登录"
            self._placeholder_user = True
        if login_manager is not None and not self._placeholder_user:
            if login_manager.current_user is None:
                login_manager.current_user = username
            # 也设置用户名属性
            login_manager.username = username
        super().__init__(username, login_manager)
        # 双重保险：确保登录状态不为空（仅真实登录后）
        if not self._placeholder_user:
            if self.login_manager.current_user is None:
                self.login_manager.current_user = username
            if self.current_user is None:
                self.current_user = username
        self._initializing = False
        self.is_recording = False
        self._combo_stop_shortcuts = {}
        self._combo_stop_key_state = {}
        self._combo_stop_hotkey_ids = {}
        self._combo_stop_check_timer = QTimer(self)
        self._combo_stop_check_timer.timeout.connect(self._check_combo_stop_shortcuts)

    def run_selected_combo_skills(self, table_widget):
        """macOS版本：批量运行选中的组合技"""
        # 商业化付费闸：与单个组合技（run_combo_skill_in_tab）保持一致。
        # 原先只有单个组合技有闸，勾选多个走批量运行即可绕过付费判定。
        if not self.check_entitlement_gate():
            return
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

            # 每次运行组合技前清空日志，重新录制
            self.clear_log()

            clear_image_cache()

            normal_skills = [s for s in selected_skills if not s.get('monitor_mode', False)]
            monitor_skills = [s for s in selected_skills if s.get('monitor_mode', False)]


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

                # 清除停止标志，确保组合技能正常启动
                clear_replay_stop_flag()

                runner = ComboSkillRunner(skill, self)
                runner.skill_id = skill_id
                self.runners[skill_id] = runner
                normal_runners.append(runner)

                _sid = skill_id
                runner._on_finished = lambda success, msg, sid=_sid: QTimer.singleShot(0, lambda: self._on_combo_skill_finished(success, msg, sid))
                runner._on_step = lambda step_info, sid=_sid: QTimer.singleShot(0, lambda: self._on_combo_step_changed(step_info, sid))
                runner._on_log = lambda msg, sid=_sid: QTimer.singleShot(0, lambda: self.append_log(f" ║  [{sid}] {msg}"))

                _t = threading.Thread(target=runner.run, daemon=True)
                runner._exec_thread = _t
                _t.start()

                stop_shortcut = skill.get('stop_shortcut', '')
                if stop_shortcut:
                    kb_shortcut = self._convert_shortcut_for_keyboard(stop_shortcut)
                    self._combo_stop_shortcuts[skill_id] = kb_shortcut
                    self._combo_stop_key_state[skill_id] = False
                    if not self._combo_stop_check_timer.isActive():
                        self._combo_stop_check_timer.start(500)
                    try:
                        import keyboard as _kb
                        def _mk_hk2(sid):
                            def _hk():
                                print(f'[STOP_SHORTCUT] add_hotkey triggered for {sid}')
                                QTimer.singleShot(0, lambda: self._do_stop_combo_skill(sid))
                            return _hk
                        hid = _kb.add_hotkey(kb_shortcut, _mk_hk2(skill_id), suppress=False)
                        self._combo_stop_hotkey_ids[skill_id] = hid
                        print(f'[STOP_SHORTCUT] Registered add_hotkey: {kb_shortcut} -> {skill_id} (id={hid})')
                    except Exception as _e:
                        print(f'[STOP_SHORTCUT] add_hotkey failed: {_e}')
                        self._combo_stop_hotkey_ids = getattr(self, '_combo_stop_hotkey_ids', {})

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
                    runner._on_log = lambda msg, sid=_sid: QTimer.singleShot(0, lambda: self.append_log(f" ║  [{sid}] {msg}"))

                    _t = threading.Thread(target=runner.run, daemon=True)
                    runner._exec_thread = _t
                    _t.start()

            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as e:
            traceback.print_exc()
            print(f"[MACOS COMBO] 运行组合技失败: {e}")

    def run_combo_skill_in_tab(self, skill):
        """在macOS组合技tab页中运行单个组合技"""
        # 商业化付费闸：试用过期且非 VIP 时禁止执行组合技
        if not self.check_entitlement_gate():
            return
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

            clear_replay_stop_flag()

            self.showMinimized()

            self.clear_log()

            running_count = len([r for r in self.runners.values() if r.isRunning()])
            if running_count == 0:
                clear_image_cache()


            runner = ComboSkillRunner(skill, self)
            runner.skill_id = skill_id
            self.runners[skill_id] = runner

            runner._on_finished = lambda success, msg, sid=skill_id: QTimer.singleShot(0, lambda: self._on_combo_skill_finished(success, msg, sid))
            runner._on_step = lambda step_info, sid=skill_id: QTimer.singleShot(0, lambda: self._on_combo_step_changed(step_info, sid))
            runner._on_log = lambda msg: self.append_log(f" ║  {msg}")

            _t = threading.Thread(target=runner.run, daemon=True)
            runner._exec_thread = _t
            _t.start()

            stop_shortcut = skill.get('stop_shortcut', '')
            if stop_shortcut:
                kb_shortcut = self._convert_shortcut_for_keyboard(stop_shortcut)
                self._combo_stop_shortcuts[skill_id] = kb_shortcut
                self._combo_stop_key_state[skill_id] = False
                if not self._combo_stop_check_timer.isActive():
                    self._combo_stop_check_timer.start(100)
                try:
                    import keyboard as _kb
                    _sid = skill_id
                    def _mk_hk(sid):
                        def _hk():
                            print(f'[STOP_SHORTCUT] add_hotkey triggered for {sid}')
                            QTimer.singleShot(0, lambda: self._do_stop_combo_skill(sid))
                        return _hk
                    hid = _kb.add_hotkey(kb_shortcut, _mk_hk(skill_id), suppress=False)
                    self._combo_stop_hotkey_ids[skill_id] = hid
                    print(f'[STOP_SHORTCUT] Registered add_hotkey: {kb_shortcut} -> {skill_id} (id={hid})')
                except Exception as _e:
                    print(f'[STOP_SHORTCUT] add_hotkey failed: {_e}')
                    self._combo_stop_hotkey_ids = getattr(self, '_combo_stop_hotkey_ids', {})

            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as e:
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

        # ★ 启动提速（2026-09-05 二期）：tab 懒加载。
        #   原来主窗构造 1.4s 的大头是 7 个 tab 全量构建；现在启动只建默认展示的
        #   record_tab，其余 5 个 tab（管理/组合技/设置/帮助/反馈）放空壳占位，
        #   首次切入时在 on_macos_tab_changed 里再真正构建（_ensure_tab_built）。
        self.record_tab = self.create_record_tab()
        self.macos_stack.addWidget(self.record_tab)  # index 0
        self._lazy_tab_factories = {
            1: ('manager_tab', self.create_manager_tab),
            2: ('combo_tab', self.create_combo_tab),
            3: ('settings_tab', self.create_settings_tab),
            4: ('help_tab', self.create_help_tab),
            5: ('feedback_tab', self.create_feedback_tab),
        }
        self._tab_built = {0}
        for _idx in range(1, 6):
            _ph = QWidget()
            _ph.setStyleSheet("background-color: transparent;")
            self.macos_stack.addWidget(_ph)

        # 内嵌登录页（方案 7-7）：不再弹出独立登录窗口
        # 「账户」页 = 双页 stack：未登录显示登录表单，已登录显示账户概览
        try:
            from login_pane import LoginPane
            self.login_pane = LoginPane(self.login_manager)
            self.login_pane.login_success.connect(self._on_embedded_login_success)
        except Exception as e:
            traceback.print_exc()
            self.login_pane = QLabel(f"登录页加载失败: {e}")

        self.account_stack = QStackedWidget()
        self.account_stack.addWidget(self.login_pane)  # index 0: 登录表单

        try:
            from account_pane import AccountPane
            self.account_pane = AccountPane()
            self.account_pane.logout_requested.connect(self._on_account_logout)
            self.account_pane.open_activation_requested.connect(self._on_account_open_activation)
            self.account_pane.open_recharge_requested.connect(self._on_account_open_recharge)
        except Exception as e:
            traceback.print_exc()
            self.account_pane = QLabel(f"账户页加载失败: {e}")
        self.account_stack.addWidget(self.account_pane)  # index 1: 已登录账户页

        self.macos_stack.addWidget(self.account_stack)

        body_layout.addWidget(self.macos_stack, 1)
        main_layout.addWidget(body, 1)

        self.create_tray_icon()

        self._macos_titles = [
            "录制控制", "流程管理", "组合技",
            "设置",
            "使用帮助",
            "反馈",
            "账户",
        ]

        self.fade_animation = None

        # 未登录时默认展示内嵌「账户」页；已登录则进入录制控制
        _logged_in = bool(self.login_manager and getattr(self.login_manager, 'current_user', None))
        if _logged_in:
            self.macos_stack.setCurrentIndex(0)
            self.macos_sidebar.set_username(self.login_manager.current_user)
            # 启动已登录：账户页直接切到账户概览
            if hasattr(self, 'account_stack'):
                self.account_stack.setCurrentWidget(self.account_pane)
                if hasattr(self.account_pane, 'refresh'):
                    # ★ 启动提速（2026-09-05）：refresh 会同步查 Supabase 权益（网络往返
                    #   1~2s，日志里的"创建新的Supabase管理器实例"就是它），原来堵在
                    #   窗口显示之前。挪到 show 之后再刷，账户页先渲染本地状态。
                    QTimer.singleShot(200, self._refresh_account_pane_deferred)
        else:
            self.macos_sidebar.set_active_tab(len(self._macos_titles) - 1)

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

        QTimer.singleShot(500, self._check_admin_permission)

    def _refresh_account_pane_deferred(self):
        """窗口显示后补刷账户页权益（get_entitlement 查 Supabase，不阻塞启动）"""
        try:
            if hasattr(self, 'account_pane') and hasattr(self.account_pane, 'refresh'):
                if self.login_manager and getattr(self.login_manager, 'current_user', None):
                    self.account_pane.refresh(self.login_manager.current_user)
        except Exception:
            traceback.print_exc()

    def _check_admin_permission(self):
        if sys.platform != 'win32':
            return
        if is_admin():
            log_info("当前以管理员权限运行")
            return
        log_warning("当前未以管理员权限运行，快捷键和自动化操作可能受限")
        # 仅在打包后的 exe 中提示，保持开发版原版体验一致
        if not getattr(sys, 'frozen', False):
            return
        try:
            from beautiful_dialog import StyledMessageDialog
            dialog = StyledMessageDialog(
                parent=self,
                title='权限提示',
                text='检测到当前未以管理员身份运行\n\n全局快捷键、键鼠模拟等功能可能无法正常工作\n\n建议以管理员身份重新启动程序',
                msg_type='warning',
                buttons='yes_no'
            )
            result = dialog.exec_()
            if result == StyledMessageDialog.YES:
                log_info("用户选择以管理员身份重启")
                if run_as_admin():
                    QTimer.singleShot(100, self.close)
        except Exception as e:
            log_exception(e, "显示管理员权限提示失败")

    def resizeEvent(self, e):
        if hasattr(self, "_border_overlay") and self._border_overlay:
            self._border_overlay.setGeometry(self.centralWidget().rect())
        super().resizeEvent(e)

    def _ensure_tab_built(self, index):
        """tab 懒加载：首次切到某页时才真正构建并替换占位空壳"""
        if index in self._tab_built or index not in self._lazy_tab_factories:
            return
        self._tab_built.add(index)
        attr, factory = self._lazy_tab_factories.pop(index)
        old = self.macos_stack.widget(index)
        try:
            page = factory()
        except Exception as e:
            traceback.print_exc()
            page = QLabel(f"加载失败: {e}")
        setattr(self, attr, page)
        # QStackedWidget 没有 replaceWidget（那是 QStackedLayout 的方法）：
        # 先在原位置插入新页、再移除旧占位壳，期间 index 不翻转
        _idx = self.macos_stack.indexOf(old)
        _was_current = self.macos_stack.currentWidget() is old
        self.macos_stack.insertWidget(_idx, page)
        self.macos_stack.removeWidget(old)
        old.deleteLater()
        if _was_current:
            # 移除旧页后 Qt 会把 currentIndex 漂移到别的页，恢复指向新页
            self.macos_stack.setCurrentIndex(_idx)

    def on_macos_tab_changed(self, index):
        self._ensure_tab_built(index)
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

        # 「账户」页：按登录状态分流——未登录显示登录表单，已登录显示账户概览
        if index == len(self._macos_titles) - 1 and hasattr(self, 'account_stack'):
            _user = bool(self.login_manager and getattr(self.login_manager, 'current_user', None))
            self.account_stack.setCurrentWidget(self.account_pane if _user else self.login_pane)
            if _user and hasattr(self.account_pane, 'refresh'):
                # ★ 响应提速：先渲染账户界面，会员权益查询（可能同步查 Supabase）挪到事件循环后，避免点后卡顿
                try:
                    from PyQt5.QtCore import QTimer
                    _u = self.login_manager.current_user
                    QTimer.singleShot(0, lambda u=_u: self.account_pane.refresh(u))
                except Exception:
                    traceback.print_exc()

    def _on_embedded_login_success(self, username):
        """内嵌登录页登录成功：同步用户名并跳回录制控制页"""
        try:
            self.current_user = username
            if self.login_manager is not None:
                self.login_manager.current_user = username
                self.login_manager.username = username
            self._placeholder_user = False
            if hasattr(self, 'macos_sidebar'):
                self.macos_sidebar.set_username(username)
                self.macos_sidebar.set_active_tab(0)
            # 已登录：账户页切到账户概览并刷新
            if hasattr(self, 'account_stack'):
                self.account_stack.setCurrentWidget(self.account_pane)
                if hasattr(self.account_pane, 'refresh'):
                    try:
                        self.account_pane.refresh(username)
                    except Exception:
                        traceback.print_exc()
            log_info(f"内嵌登录成功: {username}")
            # ★ 登录后重新加载该用户的快捷键配置并注册（启动时 _lazy_init 早于登录，
            #   此前读的是空配置，不在此重载会导致每次重启快捷键丢失）
            try:
                if hasattr(self, 'load_shortcut_config'):
                    self.load_shortcut_config()
                    if hasattr(self, 'update_shortcuts'):
                        self.update_shortcuts()
                    if hasattr(self, 'load_folders_to_table') and hasattr(self, 'manager_tab') and hasattr(self.manager_tab, 'folder_table'):
                        self.load_folders_to_table(self.manager_tab.folder_table)
            except Exception:
                traceback.print_exc()
        except Exception:
            traceback.print_exc()

    def _on_account_logout(self):
        """账户页「退出登录」：清除状态并切回登录表单"""
        try:
            if self.login_manager is not None:
                try:
                    self.login_manager.logout()
                except Exception:
                    pass
                self.login_manager.current_user = None
            self.current_user = None
            self._placeholder_user = False
            # 退出登录：清除快捷键注册与配置，避免残留上一用户的热键
            try:
                self.shortcuts = {}
                if hasattr(self, 'update_shortcuts'):
                    self.update_shortcuts()
            except Exception:
                traceback.print_exc()
            if hasattr(self, 'macos_sidebar'):
                self.macos_sidebar.set_username(None)
            if hasattr(self, 'account_stack'):
                self.account_stack.setCurrentWidget(self.login_pane)
            log_info("账户页退出登录")
        except Exception:
            traceback.print_exc()

    def _on_account_open_activation(self):
        """账户页「会员与激活」"""
        try:
            self.open_activation_dialog()
        except Exception:
            traceback.print_exc()

    def _on_account_open_recharge(self):
        """账户页「续费 / 购买会员」：后台解析出真实可用的充值地址再打开
        （cpolar 域名漂移自愈：本地/远程/镜像候选逐个验证品牌指纹，杜绝打开死链或别人的站）"""
        try:
            import threading
            from entitlement import resolve_channel_url

            def _work():
                url = ''
                try:
                    url = resolve_channel_url(deep=True) or ''
                except Exception:
                    traceback.print_exc()
                if url:
                    QTimer.singleShot(0, lambda: self._open_recharge_url(url))
            threading.Thread(target=_work, daemon=True).start()
        except Exception:
            traceback.print_exc()

    def _open_recharge_url(self, url):
        try:
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(url))
        except Exception:
            traceback.print_exc()

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
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignTop)

        main_card = MacOSCard()
        card_layout = QVBoxLayout(main_card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(28, 28, 28, 28)

        record_title = QLabel("录制控制")
        record_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 20px;
            font-weight: 700;
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
        self.record_mode_combo = QPushButton("图像录制")
        self.record_mode_combo.setIcon(load_svg_icon("camera", 20))
        self.record_mode_combo.setIconSize(QSize(36, 36))
        self.record_mode_combo.setFixedWidth(200)
        self.record_mode_combo.setCursor(Qt.PointingHandCursor)
        # 兼容父类 currentText() 调用
        self.record_mode_combo.currentText = lambda: self.record_mode_combo.text()
        self.record_mode_combo.setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.CARD_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1.5px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 9px 16px;
                padding-right: 36px;
                font-size: 13px;
                font-weight: 500;
                min-height: 22px;
                text-align: left;
            }}
            QPushButton:hover {{
                border: 1.5px solid {MacOSColors.SEPARATOR};
                background-color: {MacOSColors.CARD_BG};
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
                border-radius: 14px;
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
        self._record_menu.addAction(load_svg_icon("camera", 18), "图像录制")
        self._record_menu.addAction(load_svg_icon("location", 18), "坐标录制")
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

        self.replay_btn = MacOSSecondaryButton("回放已关闭")
        self.replay_btn.setIcon(load_svg_icon("play", 16))
        self.replay_btn.setIconSize(QSize(24, 24))
        self.replay_btn.setMinimumWidth(100)
        self.replay_btn.clicked.connect(self.toggle_replay_status_only)
        replay_layout.addWidget(self.replay_btn)

        float_btn = MacOSSecondaryButton("悬浮窗口")
        float_btn.setMinimumWidth(100)
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

        # 白色面板内缩，左缘从 24px 起，与其余页面卡片对齐（不再顶到最左）
        card = MacOSCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)

        # 统一扁平按钮样式（无边框 / 无阴影 / 统一圆角与内边距 / 语义配色）
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(flat_button_style("neutral"))
        refresh_btn.setIcon(load_svg_icon("refresh", 16))
        refresh_btn.setIconSize(QSize(14, 14))
        refresh_btn.setMinimumWidth(60)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(refresh_btn)

        trash_btn = QPushButton("回收站")
        trash_btn.setStyleSheet(flat_button_style("danger"))
        trash_btn.setIcon(load_svg_icon("trash", 16))
        trash_btn.setIconSize(QSize(14, 14))
        trash_btn.setMinimumWidth(60)
        trash_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(trash_btn)
        header.addStretch()
        card_layout.addLayout(header)

        folder_table = QTableWidget()
        folder_table.setIconSize(QSize(16, 16))
        folder_table.setColumnCount(5)
        folder_table.setHorizontalHeaderLabels(["时间", "流程名称", "快捷键", "重命名", "删除"])
        # 紧凑高密度风格：白底细边框表格 + 40px 行高 + 14px 字号
        folder_table.setStyleSheet("""
            QTableWidget { background:#FFFFFF; border:1px solid #E5E7EC; border-radius:10px;
                outline:none; gridline-color:transparent; font-size:14px;
                font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#333333; }
            QTableWidget::item { border-bottom:1px solid #F0F1F4; color:#333333; padding:7px 12px; }
            QTableWidget::item:hover { background:#F5F8FF; }
            QTableWidget::item:selected { background:#E8F0FE; color:#333333; }
            QHeaderView::section { background:#F4F6FB; color:#667085; padding:7px 12px; border:none;
                border-bottom:1px solid #E5E9F2; font-weight:600; font-size:12px;
                font-family:"Microsoft YaHei","Segoe UI Emoji"; }
            QHeaderView::section:first { border-top-left-radius:10px; }
            QHeaderView::section:last { border-top-right-radius:10px; }
            QScrollBar:vertical { width:6px; background:transparent; }
            QScrollBar::handle:vertical { background:#D5D9E2; border-radius:3px; min-height:20px; }
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0px; background:transparent; }
        """)
        folder_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        folder_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        folder_table.setMouseTracking(True)
        folder_table.setShowGrid(False)
        folder_table.setAlternatingRowColors(False)
        folder_table.verticalHeader().setVisible(False)
        folder_table.verticalHeader().setDefaultSectionSize(40)
        folder_table.horizontalHeader().setHighlightSections(False)
        folder_table.horizontalHeader().setStretchLastSection(False)
        _folder_default_widths = [110, 400, 110, 90, 48]
        _apply_saved_column_widths(folder_table, "manager_table", _folder_default_widths)
        header = folder_table.horizontalHeader()
        # 去除横向滚动：横向滚动条永远隐藏，列宽不足时由 Stretch 列吸收
        folder_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header.setMinimumSectionSize(36)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        folder_table.setColumnWidth(3, 90)
        folder_table.setColumnWidth(4, 48)

        def on_folder_table_click(row, column):
            if column in (0, 1):
                # 点击"时间"或"流程名称"单元格都进入流程（路径存在名称列的 UserRole 里）
                item = folder_table.item(row, 1)
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
        
        folder_table.setContextMenuPolicy(Qt.CustomContextMenu)
        folder_table.customContextMenuRequested.connect(lambda pos, ft=folder_table: self.show_folder_context_menu(pos, ft))
        
        _connect_column_width_saver(folder_table, "manager_table")
        card_layout.addWidget(folder_table, 1)
        layout.addWidget(card, 1)

        refresh_btn.clicked.connect(lambda: self.load_folders_to_table(folder_table))
        trash_btn.clicked.connect(self.open_trash_dialog)

        self.load_folders_to_table(folder_table)
        tab.folder_table = folder_table
        return tab

    def open_view_images_in_tab(self, folder_path):
        try:
            folder_manager = FolderManager(self)
            self.folder_manager = folder_manager
            folder_manager.view_images(folder_path)
        except Exception as e:
            traceback.print_exc()
            self.show_beautiful_message('critical', '错误', f'打开查看图片窗口失败: {e}', parent=self)

    def show_folder_context_menu(self, position, table_widget):
        """流程右键菜单：自绘圆角弹层（QMenu 的 QSS 圆角在 Windows 上不生效，
        四角会露出直角；改为 QFrame Popup 卡片确保圆润无直角）"""
        row = table_widget.rowAt(position.y())
        # 点到空白/表头区域时 rowAt 返回 -1，兜底选最接近的一行，保证菜单一定能弹出
        if row < 0 and table_widget.rowCount() > 0:
            best, best_dist = 0, 10 ** 9
            for r in range(table_widget.rowCount()):
                rect = table_widget.visualRect(table_widget.model().index(r, 1))
                mid = rect.top() + rect.height() // 2
                d = abs(position.y() - mid)
                if d < best_dist:
                    best_dist, best = d, r
            row = best

        if row < 0 or row >= table_widget.rowCount():
            return
        name_item = table_widget.item(row, 1)
        if not name_item:
            return
        folder_path = name_item.data(Qt.UserRole)
        folder_name = name_item.text()
        if not folder_path or not os.path.exists(folder_path):
            return

        try:
            usage_counts = self._get_usage_counts()
        except Exception:
            usage_counts = {}
        count = usage_counts.get(folder_name, 0)

        card = QFrame(table_widget)
        card.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        card.setAttribute(Qt.WA_TranslucentBackground)
        card.setObjectName("folderMenuCard")
        card.setStyleSheet("""
            #folderMenuCard {
                background: #FFFFFF;
                border: 1px solid #E7EAF0;
                border-radius: 12px;
            }
            QLabel#folderMenuTitle {
                color: #6B7280;
                background: #F3F4F6;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                padding: 8px 12px;
            }
            QLabel#folderMenuLabel { color: #6B7280; font-size: 12px; }
        """)
        try:
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(18)
            shadow.setOffset(0, 3)
            shadow.setColor(QColor(0, 0, 0, 60))
            card.setGraphicsEffect(shadow)
        except Exception:
            pass

        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        title = QLabel(f"已执行 {count} 次")
        title.setObjectName("folderMenuTitle")
        lay.addWidget(title)

        rename_btn = QPushButton("重命名")
        rename_btn.setCursor(Qt.PointingHandCursor)
        rename_btn.setStyleSheet("""
            QPushButton {
                text-align: left; border: none; background: #FFFFFF;
                color: #374151; font-size: 13px; padding: 9px 14px;
                border-radius: 0px;
            }
            QPushButton:hover { background: #E8F0FE; color: #111827; }
        """)
        delete_btn = QPushButton("删除")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet("""
            QPushButton {
                text-align: left; border: none; background: #FFFFFF;
                color: #DC2626; font-size: 13px; padding: 9px 14px;
                border-top: 1px solid #EEF0F4;
                border-radius: 0px;
            }
            QPushButton:hover { background: #FDECEC; color: #B91C1C; }
        """)
        rename_btn.clicked.connect(lambda: (card.close(), self.rename_folder_in_tab(folder_path, table_widget)))
        delete_btn.clicked.connect(lambda: (card.close(), self.delete_folder_in_tab(folder_path, table_widget)))
        lay.addWidget(rename_btn)
        lay.addWidget(delete_btn)

        gpos = table_widget.viewport().mapToGlobal(position)
        card.adjustSize()
        # 避免贴到屏幕右/下边缘被裁掉
        screen = QApplication.primaryScreen().availableGeometry()
        x = min(gpos.x(), screen.right() - card.width() - 8)
        y = min(gpos.y(), screen.bottom() - card.height() - 8)
        card.move(max(screen.left(), x), max(screen.top(), y))
        card.show()
        card.raise_()

    def load_folders_to_table(self, table_widget):
        table_widget.setRowCount(0)
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

            usage_counts = self._get_usage_counts()
            folders_with_count = []
            for fi in folders:
                fi_name = fi[1]
                fi_count = usage_counts.get(fi_name, 0)
                folders_with_count.append((fi[0], fi[1], fi[2], fi_count))
            folders_with_count.sort(key=lambda x: (-x[3], x[0]), reverse=False)

            table_widget.setRowCount(len(folders_with_count))
            for row, (ctime, name, path, count) in enumerate(folders_with_count):
                table_widget.setItem(row, 0, QTableWidgetItem(ctime))
                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.UserRole, path)
                table_widget.setItem(row, 1, name_item)
                shortcut = self.get_folder_shortcut(path)
                shortcut_display = shortcut.lower() if shortcut else "未设置"
                shortcut_item = QTableWidgetItem(shortcut_display)
                shortcut_item.setData(Qt.UserRole, ("shortcut", path))
                shortcut_item.setForeground(QColor(MacOSColors.ACCENT) if shortcut else QColor(MacOSColors.TEXT_SECONDARY))
                table_widget.setItem(row, 2, shortcut_item)
                rename_item = QTableWidgetItem("")
                rename_item.setIcon(load_svg_icon("edit", 16))
                rename_item.setTextAlignment(Qt.AlignCenter)
                rename_item.setData(Qt.UserRole, ("rename", path))
                rename_item.setForeground(QColor(MacOSColors.ACCENT))
                table_widget.setItem(row, 3, rename_item)
                delete_item = QTableWidgetItem("")
                delete_item.setIcon(load_svg_icon("trash", 16))
                delete_item.setTextAlignment(Qt.AlignCenter)
                delete_item.setData(Qt.UserRole, ("delete", path))
                delete_item.setForeground(QColor(MacOSColors.SYSTEM_RED))
                table_widget.setItem(row, 4, delete_item)
            _folder_reload_widths = [150, 200, 110, 90, 55]
            _apply_saved_column_widths(table_widget, "manager_table", _folder_reload_widths)
            table_widget.horizontalHeader().setStretchLastSection(True)
        except Exception as e:
            traceback.print_exc()

    def set_folder_shortcut_in_tab(self, folder_path, table_widget):
        folder_name = os.path.basename(folder_path)
        current_shortcut = self.get_folder_shortcut(folder_path)

        self.temporarily_disable_grave_hotkey()

        dialog = QDialog(self)
        dialog.setWindowTitle("设置快捷键 - %s" % folder_name)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setFixedWidth(420)
        # 「删除确认」同款卡片骨架：半透明窗口 + 实心白圆角卡 + 左侧竖条 + 图标标题
        from beautiful_dialog import build_styled_card, styled_button, center_dialog, fade_in_dialog
        content = build_styled_card(dialog, "设置快捷键", "keyboard")

        # ── 副标题（流程名） ──
        folder_hint = QLabel(folder_name)
        folder_hint.setAlignment(Qt.AlignCenter)
        folder_hint.setStyleSheet("font-size: 13px; color: #8E8E93; background: transparent; padding: 0 8px;")
        content.addWidget(folder_hint)

        # ── 键帽式快捷键显示屏（配色对齐卡片家族） ──
        shortcut_label = QLabel(current_shortcut if current_shortcut else "未设置")
        shortcut_label.setAlignment(Qt.AlignCenter)
        _KEYCAP_UNSET_QSS = """
            font-size: 18px; font-weight: 600; letter-spacing: 2px;
            padding: 18px 14px;
            border: 1.5px dashed #D1D1D6;
            border-radius: 10px;
            background-color: #FAFAFA;
            color: #8E8E93;
            min-height: 44px;
        """
        _KEYCAP_SET_QSS = """
            font-size: 20px; font-weight: 700; letter-spacing: 3px;
            padding: 18px 14px;
            border: 1.5px solid #5A6069;
            border-radius: 10px;
            background-color: #F0F0F2;
            color: #1A1A2E;
            min-height: 44px;
        """
        shortcut_label.setStyleSheet(_KEYCAP_SET_QSS if current_shortcut else _KEYCAP_UNSET_QSS)
        content.addWidget(shortcut_label)

        # ── 录入提示 ──
        instruction_label = QLabel("直接按下按键即可录入（最多 3 键组合） · Esc 取消")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("font-size: 12px; color: #8E8E93; background: transparent;")
        content.addWidget(instruction_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        clear_btn = styled_button("清除", danger=True)

        ok_btn = styled_button("确定", primary=True)

        cancel_btn = styled_button("取消", primary=False)

        def clear_shortcut():
            shortcut_label.setText("未设置")
            shortcut_label.setStyleSheet(_KEYCAP_UNSET_QSS)
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
                    if existing.lower() == shortcut_str.lower() and os.path.normpath(str(path)).lower() != normalized_path.lower():
                        if not os.path.exists(os.path.normpath(str(path))):
                            continue
                        _d = StyledMessageDialog(dialog, title="快捷键冲突", text=f"快捷键「{shortcut_str}」已被其他流程使用！\n请换一个快捷键。", msg_type="warning", buttons="ok")
                        _d.exec_()
                        return
                # 检查是否与组合技停止快捷键冲突
                _combo_mgr = ComboSkillManager(self)
                for _s in _combo_mgr.combo_skills:
                    if _s.get('stop_shortcut', '').lower() == shortcut_str.lower():
                        _d = StyledMessageDialog(dialog, title="快捷键冲突", text=f"快捷键「{shortcut_str}」已被组合技「{_s.get('name')}」的停止快捷键使用！\n请换一个快捷键。", msg_type="warning", buttons="ok")
                        _d.exec_()
                        return
                self.shortcuts[normalized_path] = shortcut_str.lower()
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
        content.addLayout(button_layout)

        center_dialog(dialog)
        fade_in_dialog(dialog)

        self.pending_shortcut = None

        def key_handler(event):
            if event.key() == Qt.Key_Escape:
                dialog.reject()
                return
            if event.key() in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                return
            # 忽略系统自动重复，避免重复录入
            if getattr(event, 'isAutoRepeat', None) and event.isAutoRepeat():
                return

            def _key_name(k):
                if Qt.Key_F1 <= k <= Qt.Key_F12:
                    return "F%d" % (k - Qt.Key_F1 + 1)
                if Qt.Key_0 <= k <= Qt.Key_9:
                    return str(k - Qt.Key_0)
                if Qt.Key_A <= k <= Qt.Key_Z:
                    return chr(k).lower()
                _special = {
                    Qt.Key_Space: "Space", Qt.Key_Return: "Enter", Qt.Key_Enter: "Enter",
                    Qt.Key_Tab: "Tab", Qt.Key_Backspace: "Backspace", Qt.Key_Delete: "Delete",
                    Qt.Key_Insert: "Insert", Qt.Key_Home: "Home", Qt.Key_End: "End",
                    Qt.Key_PageUp: "PageUp", Qt.Key_PageDown: "PageDown",
                    Qt.Key_Up: "up", Qt.Key_Down: "down", Qt.Key_Left: "left", Qt.Key_Right: "right",
                }
                return _special.get(k, "")

            key_name = _key_name(event.key())
            if not key_name:
                return

            # 当前按住的修饰键（任意键均可自由组合，不再限定 alt/ctrl）
            mods = []
            if event.modifiers() & Qt.ControlModifier:
                mods.append("Ctrl")
            if event.modifiers() & Qt.AltModifier:
                mods.append("Alt")
            if event.modifiers() & Qt.ShiftModifier:
                mods.append("Shift")
            if event.modifiers() & Qt.MetaModifier:
                mods.append("Win")

            token = "+".join(mods + [key_name])

            # 基于当前已输入的快捷键继续累积，支持任意 2~3 个键自由组合（如 c+2、1+2）
            cur = shortcut_label.text()
            existing = [] if cur in ("未设置", "", None) else cur.split("+")
            if token in existing:
                return
            existing.append(token)
            if len(existing) > 3:
                existing = existing[:3]
            combo = "+".join(existing)
            shortcut_label.setText(combo)
            shortcut_label.setStyleSheet(_KEYCAP_SET_QSS)

        dialog.keyPressEvent = key_handler
        dialog.setFocusPolicy(Qt.StrongFocus)
        dialog.setFocus()
        dialog.exec_()
        self.reenable_grave_hotkey()

    def rename_folder_in_tab(self, folder_path, table_widget):
        old_name = os.path.basename(folder_path)
        # 「删除确认」同款输入卡片（StyledInputDialog：白圆角卡+左竖条+图标标题）
        from beautiful_dialog import show_styled_input
        new_name, ok = show_styled_input(self, "重命名流程", "请输入新的流程名称：", text=old_name)
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name or new_name == old_name:
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
        except Exception as e:
            self.show_beautiful_message('critical', "错误", f"重命名失败: {e}")

    def delete_folder_in_tab(self, folder_path, table_widget):
        folder_name = os.path.basename(folder_path)
        reply = self.show_beautiful_message(
            'question', "确认删除",
            f"确定要删除流程「{folder_name}」吗？\n\n该流程将移动到回收站",
            buttons=QMessageBox.Yes | QMessageBox.No,
            default_button=QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            trash_dir = os.path.join(os.path.dirname(folder_path), 'trash')
            if not os.path.exists(trash_dir):
                os.makedirs(trash_dir)
            timestamp = datetime.now().strftime('_%Y%m%d_%H%M%S')
            trash_folder_name = os.path.basename(folder_path) + timestamp
            shutil.move(folder_path, os.path.join(trash_dir, trash_folder_name))
            self.update_trash_index(trash_folder_name, os.path.basename(folder_path), folder_path)
            normalized_path = os.path.normpath(str(folder_path))
            keys_to_delete = []
            for key in list(self.shortcuts.keys()):
                if os.path.normpath(str(key)).lower() == normalized_path.lower():
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                del self.shortcuts[key]
            if keys_to_delete:
                self.save_shortcut_config()
                self.update_shortcuts()
            self.load_folders_to_table(table_widget)
        except Exception as e:
            _d = StyledMessageDialog(self, title="错误", text=f"删除失败: {e}", msg_type="critical", buttons="ok")
            _d.exec_()

    def update_trash_index(self, trash_folder_name, original_name, original_path):
        """更新回收站索引文件"""
        recordings_dir = get_recordings_path()
        trash_dir = os.path.join(recordings_dir, 'trash')
        index_file = os.path.join(trash_dir, 'trash_index.json')

        index_data = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except Exception:
                pass

        index_data.append({
            'trash_folder_name': trash_folder_name,
            'original_name': original_name,
            'original_path': original_path,
            'deleted_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def remove_from_trash_index(self, trash_folder_name):
        """从回收站索引中移除指定项（恢复/永久删除后同步清理 trash_index.json）"""
        recordings_dir = get_recordings_path()
        trash_dir = os.path.join(recordings_dir, 'trash')
        index_file = os.path.join(trash_dir, 'trash_index.json')

        index_data = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except Exception:
                return

        index_data = [item for item in index_data if item.get('trash_folder_name') != trash_folder_name]

        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def create_combo_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # 白色卡片容器，与流程管理页风格一致
        card = MacOSCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)

        # 统一扁平按钮样式（无边框 / 无阴影 / 统一圆角与内边距 / 语义配色）
        _flat_primary = flat_button_style("primary")
        _flat_neutral = flat_button_style("neutral")

        new_btn = QPushButton("+ 新建组合技")
        new_btn.setStyleSheet(_flat_primary)
        new_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(new_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(_flat_neutral)
        refresh_btn.setIcon(load_svg_icon("refresh", 16))
        refresh_btn.setIconSize(QSize(14, 14))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(refresh_btn)

        run_selected_btn = QPushButton("启动选中")
        run_selected_btn.setStyleSheet(_flat_neutral)
        run_selected_btn.setIcon(load_svg_icon("play", 16))
        run_selected_btn.setIconSize(QSize(14, 14))
        run_selected_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(run_selected_btn)

        stop_selected_btn = QPushButton("停止选中")
        stop_selected_btn.setStyleSheet(_flat_neutral)
        stop_selected_btn.setIcon(load_svg_icon("stop", 16))
        stop_selected_btn.setIconSize(QSize(14, 14))
        stop_selected_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(stop_selected_btn)

        stop_all_btn = QPushButton("全部停止")
        stop_all_btn.setStyleSheet(_flat_neutral)
        stop_all_btn.setIcon(load_svg_icon("stop", 16))
        stop_all_btn.setIconSize(QSize(14, 14))
        stop_all_btn.setCursor(Qt.PointingHandCursor)
        stop_all_btn.setVisible(False)
        header.addWidget(stop_all_btn)

        header.addStretch()
        card_layout.addLayout(header)

        combo_table = QTableWidget()
        combo_table.setColumnCount(6)
        combo_table.setHorizontalHeaderLabels(["", "名称", "状态", "操作", "快捷键", "删除"])
        # 紧凑高密度风格：与流程管理页同款白底细边框表格（40px 行高 + 14px 字号）
        combo_table.setStyleSheet("""
            QTableWidget { background:#FFFFFF; border:1px solid #E5E7EC; border-radius:10px;
                outline:none; gridline-color:transparent; font-size:14px;
                font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#333333; }
            QTableWidget::item { border-bottom:1px solid #F0F1F4; color:#333333; padding:7px 12px; }
            QTableWidget::item:hover { background:#F5F8FF; }
            QTableWidget::item:selected { background:#E8F0FE; color:#333333; }
            QHeaderView::section { background:#F4F6FB; color:#667085; padding:7px 12px; border:none;
                border-bottom:1px solid #E5E9F2; font-weight:600; font-size:12px;
                font-family:"Microsoft YaHei","Segoe UI Emoji"; }
            QHeaderView::section:first { border-top-left-radius:10px; }
            QHeaderView::section:last { border-top-right-radius:10px; }
            QScrollBar:vertical { width:6px; background:transparent; }
            QScrollBar::handle:vertical { background:#D5D9E2; border-radius:3px; min-height:20px; }
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0px; background:transparent; }
        """)
        combo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        combo_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        combo_table.setMouseTracking(True)
        combo_table.setShowGrid(False)
        combo_table.setAlternatingRowColors(False)
        combo_table.verticalHeader().setVisible(False)
        combo_table.verticalHeader().setDefaultSectionSize(40)
        combo_table.horizontalHeader().setHighlightSections(False)
        combo_table.setIconSize(QSize(16, 16))
        # 所有列默认可交互拖动；删除列固定窄宽度。取消 Stretch 列，避免拖动时整表抖动。
        _combo_default_widths = [50, 260, 80, 80, 100, 52]
        _apply_saved_column_widths(combo_table, "combo_table", _combo_default_widths)
        combo_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header = combo_table.horizontalHeader()
        header.setStretchLastSection(False)
        # 名称列自适应填充剩余宽度，其余列固定，消除右侧空白与横向裁切
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        combo_table.setColumnWidth(0, 50)
        combo_table.setColumnWidth(5, 52)

        # 拦截第0列的鼠标点击：由我们自己切换勾选，避免与 Qt 原生勾选切换叠加导致状态紊乱
        class _ComboCheckFilter(QObject):
            def __init__(self, table):
                super().__init__(table)
                self._table = table

            def eventFilter(self, obj, event):
                if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                    index = self._table.indexAt(event.pos())
                    if index.isValid() and index.column() == 0:
                        item = self._table.item(index.row(), 0)
                        if item:
                            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
                            return True  # 吞掉事件，Qt 不再做原生勾选切换
                return False

        combo_table.viewport().installEventFilter(_ComboCheckFilter(combo_table))

        def on_combo_table_click(row, column):
            combo_table.setCurrentCell(row, column)
            if column == 0:
                pass  # 勾选切换已由事件过滤器统一处理
            elif column == 1:
                item = combo_table.item(row, column)
                if item:
                    skill = item.data(Qt.UserRole)
                    if skill:
                        self.edit_combo_skill_in_tab(skill, combo_table)
            elif column == 3:
                item = combo_table.item(row, column)
                if item:
                    data = item.data(Qt.UserRole)
                    if data:
                        if data[0] == "run":
                            self.run_combo_skill_in_tab(data[1])
                        elif data[0] == "stop":
                            self.stop_combo_skill(data[1])
            elif column == 4:
                item = combo_table.item(row, column)
                if item:
                    skill = item.data(Qt.UserRole)
                    if skill:
                        self.set_combo_stop_shortcut(skill, combo_table)
            elif column == 5:
                # 删除列
                item = combo_table.item(row, column)
                if item:
                    skill = item.data(Qt.UserRole)
                    if skill:
                        self.delete_combo_skill_in_tab(skill, combo_table)

        combo_table.cellClicked.connect(on_combo_table_click)
        _connect_column_width_saver(combo_table, "combo_table")
        card_layout.addWidget(combo_table, 1)
        layout.addWidget(card, 1)

        new_btn.clicked.connect(self.open_combo_skill_editor)
        refresh_btn.clicked.connect(lambda: self.load_combo_skills_to_table(combo_table))
        run_selected_btn.clicked.connect(lambda: self.run_selected_combo_skills(combo_table))
        stop_selected_btn.clicked.connect(lambda: self.stop_selected_combo_skills(combo_table))
        stop_all_btn.clicked.connect(lambda: self.stop_combo_skill())

        self.load_combo_skills_to_table(combo_table)

        tab.combo_table = combo_table
        tab.stop_all_btn = stop_all_btn
        tab.run_selected_btn = run_selected_btn
        tab.stop_selected_btn = stop_selected_btn

        self._combo_refresh_timer = QTimer(self)
        self._combo_refresh_timer.timeout.connect(lambda: self.refresh_combo_table_status(combo_table))
        self._combo_refresh_timer.start(3000)

        return tab


    def create_settings_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignTop)

        settings_list = [
            ("member", "会员与激活", "查看会员状态 / 付款开通 VIP", self.open_activation_dialog),
            ("clipboard", "查看运行日志", "查看应用程序运行日志", self.show_log_window),
        ]
        for icon, name, desc, handler in settings_list:
            card = MacOSCard()
            cl = QHBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            cl.setSpacing(12)
            icon_label = QLabel()
            icon_label.setFixedSize(48, 48)
            icon_label.setAlignment(Qt.AlignCenter)
            _svg = load_svg_icon(icon, 22)
            if not _svg.isNull():
                icon_label.setPixmap(_svg.pixmap(int(round(22 * ICON_SCALE)), int(round(22 * ICON_SCALE))))
            else:
                icon_label.setText(icon)
            icon_label.setStyleSheet(f"""
                background-color: transparent;
                border-radius: 0px;
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
            name_label.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 15px; font-weight: 700; background-color: transparent;")
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

    def create_feedback_tab(self):
        """反馈页：bug 报告与功能建议的联系方式"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)

        card = MacOSCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(12)

        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent; font-size: 28px;")
        _svg = load_svg_icon("feedback", 24)
        if not _svg.isNull():
            icon_label.setPixmap(_svg.pixmap(int(round(24 * ICON_SCALE)), int(round(24 * ICON_SCALE))))
        else:
            icon_label.setText("\U0001f4e7")
        cl.addWidget(icon_label, 0, Qt.AlignLeft)

        title = QLabel("反馈与建议")
        title.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 16px; font-weight: 700; background-color: transparent;")
        cl.addWidget(title)

        desc = QLabel("遇到 bug，或者有新的功能建议？欢迎随时联系我们，我们会尽快处理并回复。")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 13px; background-color: transparent;")
        cl.addWidget(desc)

        cl.addSpacing(6)

        email_row = QHBoxLayout()
        email_row.setSpacing(10)
        email_hint = QLabel("联系邮箱")
        email_hint.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 12px; background-color: transparent;")
        email_row.addWidget(email_hint)

        email_label = QLabel("iikya@foxmail.com")
        email_label.setStyleSheet(f"color: {MacOSColors.ACCENT}; font-size: 14px; font-weight: 600; background-color: transparent;")
        email_row.addWidget(email_label)

        copy_btn = MacOSSecondaryButton("复制")
        copy_btn.setMinimumWidth(64)
        copy_btn.setCursor(Qt.PointingHandCursor)

        def _copy_email():
            QApplication.clipboard().setText("iikya@foxmail.com")
            copy_btn.setText("已复制")
            QTimer.singleShot(1500, lambda: copy_btn.setText("复制"))

        copy_btn.clicked.connect(_copy_email)
        email_row.addWidget(copy_btn)
        email_row.addStretch()
        cl.addLayout(email_row)

        layout.addWidget(card)
        layout.addStretch()
        return tab

    def create_help_tab(self):
        """使用帮助 · 「白境画廊」翻页流（60 页设计赛 · 套 1 获选实装）
        数学对齐：真实尺寸 = 预览值 × 1.36（预览卡 700×460 → 真实 952×626），禁止目测。"""

        def S(x):
            """预览像素 → 真实像素（×1.36，四舍五入）"""
            return round(x * 1.36)

        FG, SUB, ACC = "#111114", "#9A9AA0", "#111114"
        LINE, CHIP = "#E8E8EC", "#F6F6F7"
        PADV, GAPXS, GAPS, GAPM, GAPL = S(40), S(4), S(8), S(16), S(24)

        tab = QWidget()
        tab.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        card = MacOSCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        def glabel(text, size, color, bold=False, ls=0, align=None):
            w = "700" if bold else "500"
            qss = (f"color:{color}; font-size:{S(size)}px; font-weight:{w};"
                   'font-family:"Microsoft YaHei","Segoe UI Emoji";'
                   "background:transparent; border:none;")
            if ls:
                qss += f"letter-spacing:{S(ls)}px;"
            lab = QLabel(text)
            lab.setStyleSheet(qss)
            lab.setWordWrap(True)
            if align is not None:
                lab.setAlignment(align)
            return lab

        def hairline():
            ln = QFrame()
            ln.setFixedHeight(1)
            ln.setStyleSheet(f"background:{LINE}; border:none;")
            return ln

        def page_shell(idx, widget, inner, spacing):
            """统一页边距 + 页眉（kicker / 页码），与预览 page_std 一致"""
            pg = QWidget()
            pg.setStyleSheet("background-color: transparent;")
            v = QVBoxLayout(pg)
            v.setContentsMargins(PADV, GAPM, PADV, GAPM)
            v.setSpacing(GAPM)
            head = QHBoxLayout()
            head.addWidget(glabel(f"GALLERY · {idx + 1:02d}", 10, SUB, bold=True, ls=3))
            head.addStretch()
            head.addWidget(glabel(f"{idx + 1} — 6", 10, SUB, bold=True))
            v.addLayout(head)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(spacing)
            v.addWidget(widget, 1)
            return pg

        stack = QStackedWidget()

        # ── 页 1 · 巨字宣言 + 灰/黑对比脚注 ──
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(glabel("同样的活", 46, FG, bold=True))
        row = QHBoxLayout()
        row.addWidget(glabel("两种干法", 46, FG, bold=True))
        row.addStretch()
        v.addLayout(row)
        v.addStretch()
        v.addWidget(hairline())
        foot = QHBoxLayout()
        foot.addWidget(glabel("以前：5min", 14, SUB))
        foot.addStretch()
        foot.addWidget(glabel("现在：10s", 14, ACC, bold=True))
        v.addLayout(foot)
        stack.addWidget(page_shell(0, w, v, S(8)))

        # ── 页 2 · 巨大数字 4 + 键名清单 ──
        w = QWidget()
        h = QHBoxLayout(w)
        h.setSpacing(GAPL)
        h.addWidget(glabel("4", 150, FG, bold=True), 5, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(GAPS)
        col.addStretch()
        col.addWidget(glabel("个指令，全教会你", 12, SUB, ls=2))
        col.addSpacing(GAPXS)
        for key, desc in (("左键", "框选 = 单击"), ("右键", "框选 = 右击"),
                          ("K", "模拟按键"), ("T", "输入文本")):
            r = QHBoxLayout()
            r.addWidget(glabel(key, 14, FG, bold=True))
            r.addStretch()
            r.addWidget(glabel(desc, 12, SUB))
            col.addLayout(r)
        col.addStretch()
        h.addLayout(col, 7)
        stack.addWidget(page_shell(1, w, h, 0))

        # ── 页 3 · 巨型播放键 ──
        w = QWidget()
        v = QVBoxLayout(w)
        v.addStretch()
        v.addWidget(glabel("▶", 120, FG, bold=True, align=Qt.AlignHCenter))
        v.addWidget(glabel("点回放，它替你干", 30, FG, bold=True, align=Qt.AlignHCenter))
        v.addSpacing(GAPXS)
        chips = QHBoxLayout()
        chips.setSpacing(GAPL)
        chips.addStretch()
        for c in ("自动打开软件", "自动输入文字", "自动点击按钮", "自动完成所有操作"):
            chips.addWidget(glabel(c, 10, SUB, bold=True))
        chips.addStretch()
        v.addLayout(chips)
        v.addStretch()
        stack.addWidget(page_shell(2, w, v, GAPM))

        # ── 页 4 · ✗→✓ 四格修订 ──
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(glabel("录错了也不用重新来", 12, SUB))
        v.addStretch()
        grid = QGridLayout()
        grid.setSpacing(GAPM)
        edits = (("改按键", "按错了？改成对的"), ("改文字", "输错了？直接改掉"),
                 ("调顺序", "拖拽调整步骤"), ("删多余", "点 × 删除"))
        for k, (name, desc) in enumerate(edits):
            tile = QFrame()
            tile.setStyleSheet(
                f"QFrame {{ background:#FFFFFF; border:1px solid {LINE}; border-radius:0px; }}")
            tv = QVBoxLayout(tile)
            tv.setContentsMargins(GAPM, GAPM, GAPM, GAPM)
            tv.setSpacing(GAPXS)
            head = QHBoxLayout()
            head.addWidget(glabel("✗", 14, SUB, bold=True))
            head.addStretch()
            head.addWidget(glabel("✓", 14, ACC, bold=True))
            tv.addLayout(head)
            tv.addWidget(glabel(name, 22, FG, bold=True))
            tv.addWidget(glabel(desc, 12, SUB))
            grid.addWidget(tile, k // 2, k % 2)
        v.addLayout(grid, 1)
        v.addStretch()
        stack.addWidget(page_shell(3, w, v, GAPM))

        # ── 页 5 · 组合技 · 三连方块链 ──
        w = QWidget()
        v = QVBoxLayout(w)
        v.addStretch()
        v.addWidget(glabel("⚙️", 72, FG, align=Qt.AlignHCenter))
        v.addWidget(glabel("流程 × 流程 × 流程", 26, FG, bold=True, align=Qt.AlignHCenter))
        v.addWidget(glabel("组合技：多个流程串起来，一次跑完", 12, SUB, align=Qt.AlignHCenter))
        v.addSpacing(GAPM)
        brow = QHBoxLayout()
        brow.setSpacing(GAPS)
        brow.addStretch()
        for k, tag in enumerate(("A", "B", "C")):
            box = QFrame()
            box.setFixedSize(S(40), S(40))
            box.setStyleSheet(
                f"QFrame {{ background:transparent; border:1px solid {LINE}; border-radius:0px; }}")
            bv = QVBoxLayout(box)
            bv.addWidget(glabel(tag, 14, FG, bold=True, align=Qt.AlignCenter))
            brow.addWidget(box)
            if k < 2:
                brow.addWidget(glabel("→", 14, SUB, bold=True))
        brow.addStretch()
        v.addLayout(brow)
        v.addStretch()
        v.addWidget(glabel("每天早上点一下，它自己全部搞定", 12, SUB, align=Qt.AlignHCenter))
        stack.addWidget(page_shell(4, w, v, GAPM))

        # ── 页 6 · 巨字「下班」收官 ──
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(GAPXS)
        v.addStretch()
        v.addWidget(glabel("效率", 96, FG, bold=True, align=Qt.AlignHCenter))
        v.addWidget(glabel("帮你把时间留给值得的人和事 🚀", 12, SUB, ls=2, align=Qt.AlignHCenter))
        v.addSpacing(GAPM)
        drow = QHBoxLayout()
        drow.setSpacing(GAPM)
        drow.addStretch()
        for d in ("录一次", "无限回放", "随意修改", "组合串联"):
            drow.addWidget(glabel("✓ " + d, 14, FG, bold=True))
        drow.addStretch()
        v.addLayout(drow)
        v.addStretch()
        stack.addWidget(page_shell(5, w, v, GAPXS))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.viewport().setStyleSheet("background: transparent;")
        scroll.setWidget(stack)
        cl.addWidget(scroll, 1)
        layout.addWidget(card)

        # 底部导航（套 1 · 极简圆箭头）
        # 注意：显式声明 min-height/padding，防止全局主题 QPushButton 规则撑爆圆角
        def nav_btn(text, solid):
            b = QPushButton(text)
            b.setFixedSize(S(40), S(40))
            b.setCursor(Qt.PointingHandCursor)
            if solid:
                qss = (f"QPushButton {{ background:{ACC}; color:#FFFFFF; border:none;"
                       f" border-radius:{S(20)}px; font-size:{S(16)}px; font-weight:700;"
                       ' font-family:"Microsoft YaHei"; min-height:0px; padding:0px; }'
                       "QPushButton:hover { background:#333338; }")
            else:
                qss = (f"QPushButton {{ background:transparent; color:{SUB};"
                       f" border:1px solid {LINE}; border-radius:{S(20)}px;"
                       f" font-size:{S(16)}px; font-weight:700;"
                       ' font-family:"Microsoft YaHei"; min-height:0px; padding:0px; }'
                       f"QPushButton:hover {{ background:{CHIP}; }}")
            qss += ("QPushButton:disabled { color:%s; border-color:%s; }"
                    % (LINE, LINE))
            b.setStyleSheet(qss)
            return b

        nav = QWidget()
        nav.setStyleSheet("background-color: transparent;")
        nv = QHBoxLayout(nav)
        nv.setContentsMargins(PADV, 0, PADV, GAPM)
        nv.setSpacing(GAPS)
        nv.addStretch()
        prev_btn = nav_btn("←", solid=False)
        next_btn = nav_btn("→", solid=True)
        prev_btn.setEnabled(False)
        nv.addWidget(prev_btn)
        nv.addWidget(next_btn)
        cl.addWidget(nav)

        # 辅助函数
        def go_to_step(idx):
            stack.setCurrentIndex(idx)
            prev_btn.setEnabled(idx > 0)
            next_btn.setEnabled(idx < 5)

        prev_btn.clicked.connect(lambda: go_to_step(stack.currentIndex() - 1))
        next_btn.clicked.connect(lambda: go_to_step(stack.currentIndex() + 1))

        return tab

    def create_tray_icon(self):
        """创建系统托盘图标"""
        if hasattr(self, "tray_icon") and self.tray_icon:
            return
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setToolTip("Action")
        tray_menu = QMenu(self)
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_and_raise)
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
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
        dialog = ComboSkillEditDialog(self, skill)
        if dialog.exec_() == QDialog.Accepted:
            skill_data = dialog.get_skill_data()
            if skill_data:
                combo_manager = ComboSkillManager(self)
                if skill:
                    for i, s in enumerate(combo_manager.combo_skills):
                        _oldn = skill.get("name", "")
                        _newn = skill_data.get("name", "")
                        _sn = s.get("name", "")
                        if _sn == _oldn or (_newn and _sn == _newn):
                            combo_manager.combo_skills[i] = skill_data
                            break
                else:
                    combo_manager.combo_skills.append(skill_data)
                combo_manager.save_combo_skills()
                if hasattr(self, "combo_tab") and hasattr(self.combo_tab, "combo_table"):
                    self.load_combo_skills_to_table(self.combo_tab.combo_table)
    def set_combo_stop_shortcut(self, skill, combo_table):
        skill_name = skill.get('name', '')
        current_shortcut = skill.get('stop_shortcut', '')
        dialog = QDialog(self)
        dialog.setWindowTitle("设置停止快捷键")
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setFixedWidth(420)
        # 「删除确认」同款卡片骨架（左竖条+图标+标题）
        from beautiful_dialog import build_styled_card, styled_button
        _outer = build_styled_card(dialog, "设置停止快捷键", "stop")
        _outer.setSpacing(12)

        skill_hint = QLabel(f"运行中按此快捷键停止「{skill_name}」")
        skill_hint.setAlignment(Qt.AlignCenter)
        skill_hint.setStyleSheet("font-size:13px;color:#8E8E93;background:transparent;")
        _outer.addWidget(skill_hint)

        _KEYCAP_SET_QSS = """
            font-size: 20px; font-weight: 700; letter-spacing: 3px;
            padding: 18px 14px;
            border: 1.5px solid #5A6069;
            border-radius: 10px;
            background-color: #F0F0F2;
            color: #1A1A2E;
            min-height: 44px;
        """
        _KEYCAP_UNSET_QSS = """
            font-size: 18px; font-weight: 600; letter-spacing: 2px;
            padding: 18px 14px;
            border: 1.5px dashed #D1D1D6;
            border-radius: 10px;
            background-color: #FAFAFA;
            color: #8E8E93;
            min-height: 44px;
        """
        shortcut_label = QLabel(current_shortcut if current_shortcut else "未设置")
        shortcut_label.setAlignment(Qt.AlignCenter)
        shortcut_label.setStyleSheet(_KEYCAP_SET_QSS if current_shortcut else _KEYCAP_UNSET_QSS)
        _outer.addWidget(shortcut_label)

        instruction_label = QLabel("直接按下按键即可录入（最多 3 键组合） · Esc 取消")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("font-size:12px;color:#8E8E93;background:transparent;")
        _outer.addWidget(instruction_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        clear_btn = styled_button("清除", danger=True)
        ok_btn = styled_button("确定", primary=True)
        cancel_btn = styled_button("取消", primary=False)
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        _outer.addLayout(btn_layout)
        current_keys = []
        def clear_shortcut():
            nonlocal current_keys
            current_keys = []
            shortcut_label.setText("未设置")
            shortcut_label.setStyleSheet(_KEYCAP_UNSET_QSS)
        def keyPressEvent(event):
            # 忽略系统自动重复，避免重复录入
            if getattr(event, 'isAutoRepeat', None) and event.isAutoRepeat():
                return

            key = event.key()
            # 兑现「Esc 取消」承诺：Esc 直接关闭对话框而不是被录进快捷键
            if key == Qt.Key_Escape:
                dialog.reject()
                return
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return

            def _key_name(k):
                if Qt.Key_F1 <= k <= Qt.Key_F12:
                    return "F%d" % (k - Qt.Key_F1 + 1)
                if Qt.Key_0 <= k <= Qt.Key_9:
                    return str(k - Qt.Key_0)
                if Qt.Key_A <= k <= Qt.Key_Z:
                    return chr(k).lower()
                _special = {
                    Qt.Key_Space: "Space", Qt.Key_Return: "Enter", Qt.Key_Enter: "Enter",
                    Qt.Key_Escape: "Esc", Qt.Key_Tab: "Tab", Qt.Key_Backspace: "Backspace",
                    Qt.Key_Delete: "Del", Qt.Key_Insert: "Ins", Qt.Key_Home: "Home",
                    Qt.Key_End: "End", Qt.Key_PageUp: "PageUp", Qt.Key_PageDown: "PageDown",
                    Qt.Key_Up: "↑", Qt.Key_Down: "↓", Qt.Key_Left: "←", Qt.Key_Right: "→",
                }
                return _special.get(k, "")

            key_name = _key_name(key)
            if not key_name:
                return

            mods = []
            if event.modifiers() & Qt.ControlModifier:
                mods.append("Ctrl")
            if event.modifiers() & Qt.ShiftModifier:
                mods.append("Shift")
            if event.modifiers() & Qt.AltModifier:
                mods.append("Alt")

            token = "+".join(mods + [key_name])

            # 累积组合（支持任意 2~3 个键自由组合，不再限定 alt/ctrl）
            existing = current_keys[-1].split("+") if current_keys else []
            if token in existing:
                return
            existing.append(token)
            if len(existing) > 3:
                existing = existing[:3]
            combo = "+".join(existing)
            shortcut_label.setText(combo)
            shortcut_label.setStyleSheet(_KEYCAP_SET_QSS)
            current_keys.clear()
            current_keys.append(combo)
        clear_btn.clicked.connect(clear_shortcut)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.keyPressEvent = keyPressEvent
        result = dialog.exec_()
        if result == QDialog.Accepted:
            new_shortcut = current_keys[-1] if current_keys else ''
            # 统一转小写，避免大小写不一致导致重复检测失败
            new_shortcut_lower = new_shortcut.lower()
            # 检查是否与流程运行快捷键冲突
            if new_shortcut:
                for _path, _existing in getattr(self, 'shortcuts', {}).items():
                    if _existing.lower() == new_shortcut_lower:
                        _d = StyledMessageDialog(dialog, title="快捷键冲突", text=f"快捷键「{new_shortcut}」已被其他流程的运行快捷键使用！\n请换一个快捷键。", msg_type="warning", buttons="ok")
                        _d.exec_()
                        return
            # 检查是否与其他组合技的停止快捷键冲突
            combo_manager = ComboSkillManager(self)
            for _s in combo_manager.combo_skills:
                if _s.get('name') != skill_name and _s.get('stop_shortcut', '').lower() == new_shortcut_lower:
                    _d = StyledMessageDialog(dialog, title="快捷键冲突", text=f"快捷键「{new_shortcut}」已被组合技「{_s.get('name')}」的停止快捷键使用！\n请换一个快捷键。", msg_type="warning", buttons="ok")
                    _d.exec_()
                    return
            for i, s in enumerate(combo_manager.combo_skills):
                if s.get('name') == skill_name:
                    combo_manager.combo_skills[i]['stop_shortcut'] = new_shortcut_lower
                    break
            combo_manager.save_combo_skills()
            self.load_combo_skills_to_table(combo_table)

    def edit_combo_skill_in_tab(self, skill, combo_table):
        """在组合技tab页中编辑组合技"""
        self.open_combo_skill_editor(skill)
        self.load_combo_skills_to_table(combo_table)

    def delete_combo_skill_in_tab(self, skill, combo_table):
        """在组合技tab页中删除组合技"""
        skill_name = skill.get('name', '')
        reply = self.show_beautiful_message(
            'question', "确认删除",
            f"确定要删除组合技「{skill_name}」吗？\n\n删除后该组合技的录制流程将无法恢复",
            buttons=QMessageBox.Yes | QMessageBox.No,
            default_button=QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            combo_manager = ComboSkillManager(self)
            combo_manager.combo_skills = [s for s in combo_manager.combo_skills if s.get('name') != skill.get('name')]
            combo_manager.save_combo_skills()
            self.load_combo_skills_to_table(combo_table)



    def _update_combo_status_bar(self, running_count, running_skill_names):
        """更新组合技页工具栏中「全部停止」按钮的显隐"""
        if hasattr(self, 'combo_tab'):
            tab = self.combo_tab
            if hasattr(tab, 'stop_all_btn'):
                tab.stop_all_btn.setVisible(running_count > 0)

    def refresh_combo_table_status(self, table_widget):
        """定时刷新：仅原地更新各行的运行状态，不重建表格，避免吞掉用户的点击"""
        combo_skills = self._get_combo_manager().combo_skills
        names = [s.get('name', '未命名') for s in combo_skills]

        running_skill_ids = set()
        running_skill_names = []
        if hasattr(self, 'runners'):
            for skill_id, runner in self.runners.items():
                if runner.isRunning():
                    running_skill_ids.add(skill_id)
                    if hasattr(runner, 'skill_data'):
                        running_skill_names.append(runner.skill_data.get('name', ''))

        # 行数或行顺序与当前技能列表不一致时（新增/删除/编辑过），退化为完整重建
        need_full_reload = (table_widget.rowCount() != len(combo_skills))
        if not need_full_reload:
            for row in range(table_widget.rowCount()):
                name_item = table_widget.item(row, 1)
                if not name_item or not isinstance(name_item.data(Qt.UserRole), dict) \
                        or name_item.data(Qt.UserRole).get('name', '未命名') != names[row]:
                    need_full_reload = True
                    break
        if need_full_reload:
            self.load_combo_skills_to_table(table_widget)
            return

        running_count = len(running_skill_ids)
        self._update_combo_status_bar(running_count, running_skill_names)

        for row, skill in enumerate(combo_skills):
            name = skill.get('name', '未命名')
            is_running = (name in running_skill_ids)
            is_monitor = skill.get('monitor_mode', False)

            row_font = QFont()
            row_font.setBold(is_running)

            # 第1列：名称（颜色/加粗/监控前缀）
            name_item = table_widget.item(row, 1)
            display = name
            if name_item.text() != display:
                name_item.setText(display)
            name_item.setForeground(QColor(MacOSColors.SYSTEM_GREEN if is_running else MacOSColors.TEXT_PRIMARY))
            name_item.setFont(row_font)

            # 第2列：状态
            status_item = table_widget.item(row, 2)
            if is_running:
                status_text, status_color, status_bold = "运行中", MacOSColors.SYSTEM_GREEN, True
            elif is_monitor:
                status_text, status_color, status_bold = "监控", MacOSColors.ACCENT, False
            else:
                status_text, status_color, status_bold = "空闲", MacOSColors.TEXT_SECONDARY, False
            if status_item.text() != status_text:
                status_item.setText(status_text)
            status_item.setForeground(QColor(status_color))
            status_font = QFont()
            status_font.setBold(status_bold)
            status_item.setFont(status_font)

            # 第3列：操作（运行/停止）
            op_item = table_widget.item(row, 3)
            want_op = "stop" if is_running else "run"
            cur_op = op_item.data(Qt.UserRole)
            if not (isinstance(cur_op, tuple) and len(cur_op) == 2 and cur_op[0] == want_op):
                table_widget.removeCellWidget(row, 3)
                op_new = QTableWidgetItem()
                op_new.setData(Qt.UserRole, (want_op, skill))
                table_widget.setItem(row, 3, op_new)
                icon_name = "stop" if is_running else "play"
                _set_table_icon_centered(table_widget, row, 3, icon_name, 16)

            # 第5列：删除按钮（运行中禁用）
            del_item = table_widget.item(row, 5)
            if is_running and del_item.data(Qt.UserRole) is not None:
                table_widget.removeCellWidget(row, 5)
                del_new = QTableWidgetItem("运行中")
                del_new.setForeground(QColor(MacOSColors.SYSTEM_GRAY3))
                del_new.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                table_widget.setItem(row, 5, del_new)
            elif not is_running and del_item.data(Qt.UserRole) is None:
                table_widget.removeCellWidget(row, 5)
                del_new = QTableWidgetItem()
                del_new.setData(Qt.UserRole, skill)
                table_widget.setItem(row, 5, del_new)
                _set_table_icon_centered(table_widget, row, 5, "trash", 14)

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
        self._update_combo_status_bar(running_count, running_skill_names)

        table_widget.setRowCount(len(combo_skills))
        for row, skill in enumerate(combo_skills):
            table_widget.setRowHeight(row, 52)

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

            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, skill)
            name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            name_item.setForeground(QColor(MacOSColors.SYSTEM_GREEN if is_running else MacOSColors.TEXT_PRIMARY))
            name_item.setFont(row_font)
            table_widget.setItem(row, 1, name_item)

            # ── 第2列：状态 ──
            if is_running:
                status_item = QTableWidgetItem("运行中")
                status_item.setForeground(QColor(MacOSColors.SYSTEM_GREEN))
                status_font = QFont()
                status_font.setBold(True)
                status_item.setFont(status_font)
            elif is_monitor:
                status_item = QTableWidgetItem("监控")
                status_item.setForeground(QColor(MacOSColors.ACCENT))
            else:
                status_item = QTableWidgetItem("空闲")
                status_item.setForeground(QColor(MacOSColors.TEXT_SECONDARY))
            status_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            table_widget.setItem(row, 2, status_item)

            # ── 第3列：操作（运行/停止）──
            op_item = QTableWidgetItem()
            if is_running:
                op_item.setData(Qt.UserRole, ("stop", skill))
                icon_name = "stop"
            else:
                op_item.setData(Qt.UserRole, ("run", skill))
                icon_name = "play"
            table_widget.setItem(row, 3, op_item)
            _set_table_icon_centered(table_widget, row, 3, icon_name, 16)

            # ── 第4列：停止快捷键 ──
            stop_shortcut = skill.get('stop_shortcut', '')
            shortcut_display = stop_shortcut if stop_shortcut else "点击设置"
            shortcut_item = QTableWidgetItem(shortcut_display)
            shortcut_item.setTextAlignment(Qt.AlignCenter)
            shortcut_item.setData(Qt.UserRole, skill)
            if not stop_shortcut:
                shortcut_item.setForeground(QColor(MacOSColors.TEXT_SECONDARY))
            table_widget.setItem(row, 4, shortcut_item)

            # ── 第5列：删除按钮（运行中不允许删除）──
            if is_running:
                delete_item = QTableWidgetItem("运行中")
                delete_item.setForeground(QColor(MacOSColors.SYSTEM_GRAY3))
                delete_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                table_widget.setItem(row, 5, delete_item)
            else:
                delete_item = QTableWidgetItem()
                delete_item.setData(Qt.UserRole, skill)
                table_widget.setItem(row, 5, delete_item)
                _set_table_icon_centered(table_widget, row, 5, "trash", 14)

    def _get_combo_manager(self):
        return ComboSkillManager(self)

    def _convert_shortcut_for_keyboard(self, shortcut):
        key_map = {
            '\u2191': 'up', '\u2193': 'down', '\u2190': 'left', '\u2192': 'right',
            'Space': 'space', 'Enter': 'enter', 'Esc': 'esc',
            'Tab': 'tab', 'Backspace': 'backspace', 'Del': 'delete',
            'Ins': 'insert', 'Home': 'home', 'End': 'end',
            'PageUp': 'page up', 'PageDown': 'page down',
        }
        parts = shortcut.split('+')
        converted = []
        for p in parts:
            p_stripped = p.strip()
            if p_stripped in key_map:
                converted.append(key_map[p_stripped])
            else:
                converted.append(p_stripped.lower())
        return '+'.join(converted)

    def _check_combo_stop_shortcuts(self):
        try:
            import keyboard as _kb
            to_remove = []
            for skill_id, shortcut in list(self._combo_stop_shortcuts.items()):
                if skill_id not in self.runners or not self.runners[skill_id].isRunning():
                    to_remove.append(skill_id)
                    continue
                try:
                    pressed = _kb.is_pressed(shortcut)
                except Exception as _e:
                    print(f'[STOP_SHORTCUT] is_pressed({shortcut!r}) error: {_e}')
                    pressed = False
                was_pressed = self._combo_stop_key_state.get(skill_id, False)
                if pressed and not was_pressed:
                    print(f'[STOP_SHORTCUT] Detected stop shortcut: {shortcut} for {skill_id}')
                    QTimer.singleShot(0, lambda sid=skill_id: self._do_stop_combo_skill(sid))
                self._combo_stop_key_state[skill_id] = pressed
            for sid in to_remove:
                self._combo_stop_shortcuts.pop(sid, None)
                self._combo_stop_key_state.pop(sid, None)
            if not self._combo_stop_shortcuts:
                self._combo_stop_check_timer.stop()
        except Exception as _e:
            print(f'[STOP_SHORTCUT] _check_combo_stop_shortcuts error: {_e}')

    def _remove_combo_stop_hotkey(self, skill_id):
        _combo_stop_hotkey_ids = getattr(self, '_combo_stop_hotkey_ids', {})
        if skill_id in _combo_stop_hotkey_ids:
            try:
                import keyboard as _kb
                _kb.remove_hotkey(_combo_stop_hotkey_ids[skill_id])
                print(f'[STOP_SHORTCUT] Removed add_hotkey for {skill_id}')
            except Exception:
                pass
            del _combo_stop_hotkey_ids[skill_id]

    def _do_stop_combo_skill(self, skill_id):
        try:
            if skill_id in self.runners and self.runners[skill_id].isRunning():
                runner = self.runners[skill_id]
                runner._stop_reason = '快捷键停止'
                runner.running = False
                if hasattr(runner, 'interrupt_event'):
                    runner.interrupt_event.set()
                self.append_log(f'[{skill_id}] 快捷键停止')
            self._remove_combo_stop_hotkey(skill_id)
            self._combo_stop_shortcuts.pop(skill_id, None)
            self._combo_stop_key_state.pop(skill_id, None)
            if not self._combo_stop_shortcuts:
                self._combo_stop_check_timer.stop()
            if skill_id in self.runners:
                del self.runners[skill_id]
            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as _e:
            print(f'[STOP_SHORTCUT] _do_stop_combo_skill error: {_e}')

    def _on_combo_skill_finished(self, success, msg, skill_id):
        try:
            self._combo_stop_shortcuts.pop(skill_id, None)
            self._combo_stop_key_state.pop(skill_id, None)
            # 清理组合技停止热键ID
            self._remove_combo_stop_hotkey(skill_id)
            if not self._combo_stop_shortcuts:
                self._combo_stop_check_timer.stop()
            if skill_id in self.runners:
                del self.runners[skill_id]
            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
            self.append_log(f'[组合技] {skill_id}: {msg}')
        except Exception:
            pass

    def stop_combo_skill(self, skill=None):
        try:
            if skill is not None:
                skill_id = skill.get('name', '')
                if skill_id in self.runners and self.runners[skill_id].isRunning():
                    runner = self.runners[skill_id]
                    runner._stop_reason = '手动停止'
                    runner.running = False
                    if hasattr(runner, 'interrupt_event'):
                        runner.interrupt_event.set()
                    if hasattr(runner, 'reset'):
                        try:
                            runner.reset()
                        except Exception:
                            pass
                    self._remove_combo_stop_hotkey(skill_id)
                    self._combo_stop_shortcuts.pop(skill_id, None)
                    self._combo_stop_key_state.pop(skill_id, None)
                    if not self._combo_stop_shortcuts:
                        self._combo_stop_check_timer.stop()
                    if skill_id in self.runners:
                        del self.runners[skill_id]
                    self.append_log(f'[{skill_id}] 已停止')
            else:
                set_replay_stop_flag(True)
                for skill_id, runner in list(self.runners.items()):
                    if runner.isRunning():
                        runner._stop_reason = '全部停止'
                        runner.running = False
                        if hasattr(runner, 'interrupt_event'):
                            runner.interrupt_event.set()
                        if hasattr(runner, 'reset'):
                            try:
                                runner.reset()
                            except Exception:
                                pass
                for sid in list(getattr(self, '_combo_stop_hotkey_ids', {}).keys()):
                    self._remove_combo_stop_hotkey(sid)
                self._combo_stop_shortcuts.clear()
                self._combo_stop_key_state.clear()
                self._combo_stop_check_timer.stop()
                self.runners.clear()
                self.append_log('[组合技] 所有运行中的组合技已停止')
            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
        except Exception as e:
                self.show_beautiful_message('critical', '错误', f'停止组合技失败: {e}')

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
                self.show_beautiful_message('information', '提示', '请先勾选要停止的组合技（勾选第一列的复选框）')
                return
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
                    self._combo_stop_shortcuts.pop(skill_id, None)
                    self._combo_stop_key_state.pop(skill_id, None)
                    if skill_id in self.runners:
                        del self.runners[skill_id]
            if hasattr(self, 'combo_tab') and hasattr(self.combo_tab, 'combo_table'):
                self.load_combo_skills_to_table(self.combo_tab.combo_table)
            if stop_count > 0:
                self.append_log(f'已停止 {stop_count} 个组合技')
        except Exception as e:
                self.show_beautiful_message('critical', '错误', f'停止组合技失败: {e}')

    def register_stop_replay_hotkey(self):
        try:
            import keyboard as _kb
            def stop_handler():
                stopped = False
                if getattr(self, 'is_replaying', False):
                    QTimer.singleShot(0, self.stop_replay)
                    stopped = True
                if hasattr(self, 'runners') and self.runners:
                    any_running = any(r.isRunning() for r in self.runners.values())
                    if any_running:
                        QTimer.singleShot(0, lambda: self.stop_combo_skill())
                        stopped = True
            self.stop_replay_hotkey_id = _kb.add_hotkey('f12', stop_handler)
            log_info(f'[热键] macOS版已注册 F12 停止热键，id={self.stop_replay_hotkey_id}')
        except Exception as _e:
            log_error(f'[热键] macOS版注册 F12 停止热键失败: {_e}')
            self.stop_replay_hotkey_id = None

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
            # 商业化付费闸：试用过期且非 VIP 时禁止开始新录制
            if not self.check_entitlement_gate():
                return
            try:
                self._set_recording_state(True)
                self.record_btn.setEnabled(False)
                self.record_btn.setText('录\n制\n中')
                if hasattr(self, 'record_action'):
                    self.record_action.setEnabled(False)
                    self.record_action.setText('录制中...')
                current_mode = self.record_mode_combo.currentText()
                self.showMinimized()
                if current_mode == "坐标录制":
                    QTimer.singleShot(300, self.start_coordinate_recording)
                else:
                    QTimer.singleShot(300, self.start_image_recording)
            except Exception as e:
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
            self.selection_overlay = SelectionOverlay(self, screen_pixmap=screen_pixmap, recording_dir=None)
            self.selection_overlay.closed.connect(self.on_recording_finished)
            self.selection_overlay.show()
            self.selection_overlay.activateWindow()
            self.selection_overlay.raise_()
            self.selection_overlay.setFocus()
        except Exception as e:
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

    def on_coordinate_recording_finished(self):
        """坐标录制完成处理"""
        if hasattr(self, 'coordinate_records') and self.coordinate_records:
            try:
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
            recordings_dir = get_recordings_path()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            self.current_recording_dir = os.path.join(recordings_dir, f"流程_{timestamp}")
            os.makedirs(self.current_recording_dir, exist_ok=True)
            self.operation_count = 0
            self.coordinate_records = []
            self.coord_recorder = CoordinateRecorder(self)
            self.coord_recorder.closed.connect(self.on_coordinate_recording_finished)
            self.coord_recorder.show()
        except Exception as e:
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
        self._processing_click = False  # 点击事件去重锁：True 期间忽略所有鼠标事件，防二次计数

        # 注意：不要加 Qt.Tool —— Tool 窗口在 Windows 上通常拿不到键盘焦点，
        # 会导致 keyPressEvent 收不到 Esc，录制无法用 Esc 退出（旧 bug）。
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
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

        # 全局 Esc 兜底：即便覆盖层因焦点问题没收到键盘事件，也能退出录制
        self._esc_hotkey_id = None
        try:
            import keyboard as _kb
            self._esc_hotkey_id = _kb.add_hotkey(
                'esc',
                lambda: __import__('PyQt5.QtCore', fromlist=['QTimer']).QTimer.singleShot(0, self._finish_recording),
                suppress=False,
            )
        except Exception:
            self._esc_hotkey_id = None

    def showEvent(self, event):
        super().showEvent(event)
        # 延迟启动焦点定时器 + 置顶，确保窗口已经完全显示
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self._delayed_show)
        QTimer.singleShot(200, self._delayed_show)  # 二次保险

    def _delayed_show(self):
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)
        QApplication.processEvents()
        # 只创建一次定时器，防止重复连接
        if self._focus_timer is None:
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
            text = "左键点击记录位置\n右键点击记录右键\n按 Esc 结束录制"
        else:
            text = f"已执行 {self.step_counter} 次点击\n继续点击或按 Esc 结束"

        painter.drawText(self.rect(), Qt.AlignCenter, text)

    def _send_click_to_target(self, px, py, is_right=False):
        # 使用 SendInput API 模拟真实硬件输入
        # 将 dx/dy 归一化到 [0, 65535] 范围，与 MOUSEEVENTF_ABSOLUTE 配合使用
        from ctypes import wintypes
        MOUSEEVENTF_ABSOLUTE = 0x8000
        MOUSEEVENTF_MOVE     = 0x0001
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP   = 0x0004
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP  = 0x0010
        # 获取屏幕物理尺寸（用于坐标归一化）
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        norm_x = int(px * 65535 // sw)
        norm_y = int(py * 65535 // sh)
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ('dx', wintypes.LONG),
                ('dy', wintypes.LONG),
                ('mouseData', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD),
                ('dwExtraInfo', ctypes.c_void_p),  # ULONG_PTR → void* 而非指针
            ]
        class INPUT_UNION(ctypes.Union):
            _fields_ = [
                ('mi', MOUSEINPUT),
            ]
        class INPUT(ctypes.Structure):
            _fields_ = [
                ('type', wintypes.DWORD),
                ('u', INPUT_UNION),
            ]
        down_flag = MOUSEEVENTF_RIGHTDOWN if is_right else MOUSEEVENTF_LEFTDOWN
        up_flag   = MOUSEEVENTF_RIGHTUP   if is_right else MOUSEEVENTF_LEFTUP
        # 先移动鼠标到目标位置（含绝对坐标）
        move_inp = INPUT()
        move_inp.type = 0  # INPUT_MOUSE
        move_inp.u = INPUT_UNION()
        move_inp.u.mi = MOUSEINPUT(norm_x, norm_y, 0, MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, 0, 0)
        ctypes.windll.user32.SendInput(1, ctypes.byref(move_inp), ctypes.sizeof(move_inp))
        # 再发送 按下+释放（去掉 MOUSEEVENTF_MOVE，避免 MOVE+UP 组合被Windows Shell 对右键拆分成两次检测）
        for flag in (down_flag, up_flag):
            inp = INPUT()
            inp.type = 0
            inp.u = INPUT_UNION()
            inp.u.mi = MOUSEINPUT(norm_x, norm_y, 0, MOUSEEVENTF_ABSOLUTE | flag, 0, 0)
            ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def mousePressEvent(self, event):
        event.accept()  # 消费按下事件
        # 去重锁：正在处理一次点击（hide→SendInput→show）期间，丢弃所有后续鼠标事件
        if self._processing_click:
            return
        if event.button() == Qt.LeftButton:
            self._processing_click = True
            try:
                self.step_counter += 1
                global_logical = self.mapToGlobal(event.pos())
                px = int(global_logical.x())
                py = int(global_logical.y())
                rec = {"step": self.step_counter, "action_type": "left_click", "x": px, "y": py, "delay": 0.1}
                self.records.append(rec)
                if self.parent and hasattr(self.parent, 'coordinate_records'):
                    self.parent.coordinate_records = self.records

                # hide → 排除用户输入事件的方式处理 hide → SendInput → show
                self.hide()
                # 只处理非输入事件，防止鼠标释放事件穿透到目标窗口
                QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
                self._send_click_to_target(px, py, is_right=False)
                # 等待 SendInput 完成后再显示，防止残留合成事件被窗口捕获
                QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(30, self._unlock_and_reshow)
            except Exception:
                self._processing_click = False
                raise
        elif event.button() == Qt.RightButton:
            self._processing_click = True
            try:
                self.step_counter += 1
                global_logical = self.mapToGlobal(event.pos())
                px = int(global_logical.x())
                py = int(global_logical.y())
                rec = {"step": self.step_counter, "action_type": "right_click", "x": px, "y": py, "delay": 0.1}
                self.records.append(rec)
                if self.parent and hasattr(self.parent, 'coordinate_records'):
                    self.parent.coordinate_records = self.records

                self.hide()
                # 只处理非输入事件，防止鼠标释放事件穿透到目标窗口
                QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
                self._send_click_to_target(px, py, is_right=True)
                # 等待 SendInput 完成后再显示，防止残留合成事件被窗口捕获
                QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(50, self._unlock_and_reshow)  # 右键给更长冷却：系统右键检测有延迟
            except Exception:
                self._processing_click = False
                raise

    def _unlock_and_reshow(self):
        """延迟去锁 + 重显示：确保 SendInput 的合成事件已经被下层应用消费"""
        try:
            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus(Qt.ActiveWindowFocusReason)
            QApplication.processEvents()
            self.update()
        finally:
            self._processing_click = False

    def mouseReleaseEvent(self, event):
        """消费鼠标释放事件，防止穿透到目标窗口；去重锁期间一律丢弃"""
        event.accept()
        # 去重锁激活时，忽略鼠标释放（物理按键的 release 会在 hide→show 后迟到，必须挡住）

    def mouseMoveEvent(self, event):
        """去重锁期间忽略移动事件，但始终 accept() 防止穿透到下层"""
        # 始终 accept，防止事件透过透明窗口到下层应用
        event.accept()

    def event(self, event):
        """全局事件拦截：去重锁激活时丢弃所有类型的鼠标事件（含 ContextMenu/DblClick），彻底防重"""
        if self._processing_click:
            et = event.type()
            if et in (
                QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
                QEvent.MouseButtonDblClick, QEvent.MouseMove,
                QEvent.ContextMenu,  # 关键！Windows 右键弹起后会发 ContextMenu 事件，被 Qt 转成二次点击
            ):
                event.accept()
                return True
        return super().event(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._finish_recording()
        super().keyPressEvent(event)

    def _finish_recording(self):
        # 清理全局 Esc 钩子（避免退出后仍拦截 Esc）
        if getattr(self, '_esc_hotkey_id', None):
            try:
                import keyboard as _kb
                _kb.remove_hotkey(self._esc_hotkey_id)
            except Exception:
                pass
            self._esc_hotkey_id = None
        if self._focus_timer:
            self._focus_timer.stop()
        self.closed.emit()
        self.close()

    def closeEvent(self, event):
        # close() 不一定走 _finish_recording，这里兜底清理钩子/定时器
        if getattr(self, '_esc_hotkey_id', None):
            try:
                import keyboard as _kb
                _kb.remove_hotkey(self._esc_hotkey_id)
            except Exception:
                pass
            self._esc_hotkey_id = None
        if self._focus_timer:
            self._focus_timer.stop()
        super().closeEvent(event)


def start_macos_app():
    from PyQt5.QtGui import QFont

    log_info("=" * 50)
    log_info("程序启动")
    
    admin_status = "管理员" if is_admin() else "非管理员"
    log_info(f"权限状态: {admin_status}")
    
    frozen_status = "打包版" if getattr(sys, 'frozen', False) else "开发版"
    log_info(f"运行模式: {frozen_status}")
    log_info(f"工作目录: {os.getcwd()}")

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
            # 不再设置 RUNASINVOKER，否则程序不会请求管理员权限，
            # 导致 keyboard 库的全局热键在某些窗口/场景下被系统忽略。
        except:
            pass

    import tempfile
    temp_dir = tempfile.gettempdir()
    os.chdir(temp_dir)

    from crash_logger import make_application
    app = make_application(sys.argv)

    # 全局字体栈——与使用帮助页保持一致（PingFang SC 优先，Windows 回落微软雅黑，
    # 西文回落 Helvetica Neue / Segoe UI；正常字重，长文阅读更舒服）
    FONT_STACK = ["PingFang SC", "Microsoft YaHei", "Helvetica Neue", "Segoe UI", "sans-serif"]

    font = QFont()
    font.setFamilies(FONT_STACK)
    font.setPointSize(17)
    font.setBold(False)
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

    # 商业化：登录改为内嵌主窗口「账户」页（方案 7-7 左对齐极简），
    # 不再弹出独立登录窗；未登录时默认展示账户页，登录成功后自动进入录制控制。
    main_window = MacOSAutoRecorderApp(username=None, login_manager=login_manager)
    main_window.setWindowFlags(Qt.FramelessWindowHint)
    main_window.show()

    # 启动时检查管理员权限，未以管理员运行时提示一次
    def _show_admin_tip_once():
        try:
            if sys.platform != 'win32' or is_admin():
                return
            flag_path = os.path.join(get_user_data_path(), '.admin_tip_shown')
            if os.path.exists(flag_path):
                return
            main_window.show_beautiful_message(
                'information', '权限提示',
                '检测到当前未以管理员身份运行。\n'
                '全局快捷键在某些窗口或安全软件环境下可能需要管理员权限才能正常响应。\n\n'
                '如果快捷键偶尔失效，请尝试右键程序图标选择「以管理员身份运行」。'
            )
            try:
                with open(flag_path, 'w', encoding='utf-8') as _f:
                    _f.write('1')
            except Exception:
                pass
        except Exception as _e:
            log_error(f'显示管理员提示失败: {_e}')

    QTimer.singleShot(800, _show_admin_tip_once)

    main_window.create_replay_status_indicator()


    sys.exit(app.exec_())


if __name__ == "__main__":
    # 自动以管理员身份运行（与 app.py 入口保持一致）
    if sys.platform == "win32" and not is_admin():
        if run_as_admin():
            sys.exit(0)
    start_macos_app()