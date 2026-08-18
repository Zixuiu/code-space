"""
文件: app.py
用途: 应用程序主模块，实现自动录制器的核心功能。
      包含UI界面实现、屏幕录制逻辑、操作管理以及与用户认证系统的集成。
      提供录制操作、截图、文件管理等主要功能的实现。
"""
import os
import sys

# 尽早隐藏控制台窗口并设置Windows环境变量
if sys.platform == "win32":
    try:
        import ctypes
        # 获取控制台窗口句柄
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            # 隐藏控制台窗口
            ctypes.windll.user32.ShowWindow(whnd, 0)
            # 额外确保窗口完全隐藏
            ctypes.windll.user32.ShowWindow(whnd, 0)  # 再次调用确保隐藏
        # 注意：不再设置 RUNASINVOKER，否则程序不会请求管理员权限，
        # keyboard 库的全局热键在 Windows 上需要管理员权限才能稳定拦截。
    except:
        pass

import json
import time
import threading
import shutil
import copy
from datetime import datetime
import re
import uuid
import traceback
import sqlite3
import keyboard

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入样式模块
try:
    from styles import (
        generate_dynamic_styles, apply_dialog_style, apply_window_style,
        get_table_style, get_button_style, get_input_style,
        get_dynamic_radius,
        ACCENT, SECONDARY, BG, CARD, TEXT, MUTED, BORDER,
        THEME_PRIMARY, THEME_SECONDARY, THEME_ACCENT,
        THEME_BG, THEME_CARD, THEME_TEXT, THEME_MUTED, THEME_BORDER
    )
    APP_STYLES_AVAILABLE = True
    # print("成功导入样式模块")  # [日志已禁用]
except ImportError as e:
    APP_STYLES_AVAILABLE = False
    # print(f"警告: 样式模块未找到，将使用默认样式: {e}")  # [日志已禁用]
    # 定义备用函数
    def get_common_styles(screen_width=None, screen_height=None):
        """备用通用样式函数"""
        return """
        QMainWindow {
            background-color: white;
        }
        """

# 导入utils模块（不导入样式相关函数，避免循环导入）
from beautiful_dialog import StyledMessageDialog
from utils import (
    load_json_data, save_json_data, center_window, get_screen_size, load_qpixmap, 
    load_qimage, get_common_styles, create_styled_button, create_styled_input,
    get_common_dialog_style, get_dynamic_radius,
    log_info, log_error, log_warning, log_debug, log_exception,
    is_admin, run_as_admin
)
# 延迟导入Supabase，避免启动时立即连接
def get_supabase_manager():
    """延迟加载Supabase管理器"""
    from supabase_db import get_supabase_manager as _get_supabase_manager
    return _get_supabase_manager()

from database_helper import DatabaseHelper

# 先导入必要的Qt类
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

# 设置高DPI缩放支持 - 使用RoundPreferFloor以改善字体渲染
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # 启用高DPI缩放
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)      # 使用高DPI像素图
# 设置高DPI缩放策略为RoundPreferFloor，改善2K/4K显示器上的字体渲染
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)

# 导入其他Qt模块
from PyQt5.QtGui import QKeySequence, QGuiApplication, QPixmap, QImage, QFontMetrics, QIcon, QTextCursor, QFont, QColor, QPalette, QDrag, QRadialGradient, QLinearGradient, QPainter, QPen, QBrush
from PyQt5.QtWidgets import (
    QScrollArea, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QMessageBox, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QShortcut, QLineEdit, QDialog, QAbstractItemView, QMenu,
    QAction, QCheckBox, QPushButton, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QInputDialog, QSystemTrayIcon, QPlainTextEdit, QListWidget, QListWidgetItem, QFrame, QButtonGroup,
    QRadioButton, QFileDialog, QStackedWidget
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPointF, QRectF, QEvent, QObject, QSize, QPropertyAnimation, QRect, QAbstractAnimation, QThread, QEasingCurve, QMimeData, pyqtSignal
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QStyle

# image_recognition模块已导入


class _HoverCloseButton(QPushButton):
    """图片右上角关闭按钮 - QPushButton + 样式表，macOS Photos 风格

    半透明灰色正圆 + 细"×"，悬停加深，按下变红。
    """
    def __init__(self, parent_widget, on_click, size=24):
        super().__init__("×", parent_widget)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(on_click)
        s = size  # 别名，保持代码简洁
        self.setFixedSize(s, s)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(80, 80, 80, 150);
                color: rgba(255, 255, 255, 230);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: {s//2}px;
                font-size: {max(12, s - 8)}px;
                font-weight: normal;
                min-width: 0px;
                min-height: 0px;
                max-width: {s}px;
                max-height: {s}px;
                width: {s}px;
                height: {s}px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(30, 30, 30, 200);
                color: white;
                border-color: rgba(255, 255, 255, 70);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 59, 48, 220);
                color: white;
                border-color: rgba(255, 255, 255, 90);
            }}
        """)


def _create_hover_close_button(parent_widget, on_click, size=24):
    """
    创建一个优雅的图片关闭按钮（macOS Photos 风格）
    - 始终可见，不依赖 hover —— paintEvent 已通过颜色 alpha 处理透明度
    - hover 时背景加深、线条加粗变纯白
    - pressed 时变 iOS 红色
    - 不使用 QGraphicsOpacityEffect，避免渲染冲突导致按钮不可见
    """
    btn = _HoverCloseButton(parent_widget, on_click, size)
    return btn


class DraggableImageWidget(QWidget):
    def __init__(self, main_window, parent=None, step_num=None, img_path=None, folder_path=None, dialog=None):
        super().__init__(parent)
        self.main_window = main_window
        self.step_num = step_num
        self.img_path = img_path
        self.folder_path = folder_path
        self.dialog = dialog
        self.setAcceptDrops(True)
        self.dragging = False
        self.drag_start_position = None

    def eventFilter(self, obj, event):
        if obj is not self:
            if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                self.drag_start_position = self.mapFromGlobal(obj.mapToGlobal(event.pos()))
                return False
            elif event.type() == event.MouseMove:
                if event.buttons() & Qt.LeftButton and not self.dragging and self.drag_start_position is not None:
                    mapped = self.mapFromGlobal(obj.mapToGlobal(event.pos()))
                    if (mapped - self.drag_start_position).manhattanLength() >= QApplication.startDragDistance():
                        self.dragging = True
                        self.startDrag(event)
                        return True
                return False
            elif event.type() == event.MouseButtonRelease:
                self.dragging = False; self.drag_start_position = None; return False
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if self.dragging:
            return
        if self.drag_start_position is None:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        self.dragging = True
        self.startDrag(event)

    def startDrag(self, event):
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"{self.step_num},{self.folder_path}")
        drag.setMimeData(mime_data)
        result = drag.exec_(Qt.MoveAction)
        self.dragging = False
        return result

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            try:
                source_step, source_path = event.mimeData().text().split(',')
                source_step = int(source_step)
                target_step = self.step_num
                if source_step != target_step:
                    self.main_window.reorder_images(self.folder_path, source_step, target_step, self.dialog)
                    event.acceptProposedAction()
            except Exception as e:
                # print(f"拖拽失败: {e}")  # [日志已禁用]
                pass


class DraggableWidget(QWidget):
    def __init__(self, parent_app):
        super().__init__(None)
        self.parent_app = parent_app
        self.dragging = False
        self.drag_position = QPoint()
        self.click_start_pos = QPoint()
        self.has_moved = False
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        from PyQt5.QtGui import QBitmap, QPainter, QPainterPath
        s = self.size()
        if s.width() <= 0 or s.height() <= 0: return
        bm = QBitmap(s.width(), s.height())
        bm.clear()
        p = QPainter(bm)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, s.width(), s.height(), 14, 14)
        p.fillPath(path, Qt.color1)
        p.end()
        self.setMask(bm)

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen
        from PyQt5.QtCore import Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(r.x(), r.y(), r.width(), r.height(), 14, 14)
        painter.fillPath(path, QColor(BG))
        bp = QPainterPath()
        bp.addRoundedRect(r.x() + 0.5, r.y() + 0.5, r.width() - 1, r.height() - 1, 13.5, 13.5)
        painter.strokePath(bp, QPen(QColor("#1C1C1E"), 1))
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_start_pos = event.pos()
            self.dragging = True
            self.has_moved = False
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.activateWindow()
            self.raise_()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            self.has_moved = True
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            if self.has_moved:
                self.parent_app.save_replay_indicator_position()
            event.accept()


# ============================================================
#  RechargeDialog 已移除（商业化代码已全部清理）
# ============================================================

# ============================================================
#  FeedbackDialog - 问题反馈对话框
# ============================================================
class FeedbackDialog(QDialog):
    """反馈对话框 - 使用卡片式设计"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("问题反馈")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 获取屏幕尺寸
        screen_width, screen_height = get_screen_size()
        
        # 计算动态尺寸 - 与注册界面保持一致
        spacing_v = 8   # 减小垂直间距，从12减少到8
        spacing_h = 8   # 减小水平间距
        margin = 10     # 减小边距，减少空白区域
        font_size = max(14, int(screen_height * 0.018))  # 增加字体大小
        input_height = max(35, int(screen_height * 0.025))  # 增加输入框高度，最小35px
        button_font_size = max(12, int(screen_height * 0.014))  # 增加按钮字体大小
        
        # 创建卡片容器
        card_container = QFrame()
        card_container.setMinimumWidth(int(screen_width * 0.35))
        card_container.setMaximumWidth(int(screen_width * 0.45))
        card_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card_container.setStyleSheet(f"""
            QFrame {{
                background-color: {BG};
                border-radius: 0px;
                padding: 0px;
            }}
        """)
        card_layout = QVBoxLayout(card_container)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 创建顶部装饰区域 - macOS渐变
        top_decoration = QFrame()
        top_decoration.setFixedHeight(int(screen_height * 0.12))
        top_decoration.setStyleSheet(f"""
            QFrame {{
                background: {THEME_PRIMARY};
                border-radius: 0px;
            }}
        """)
        
        top_layout = QVBoxLayout(top_decoration)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        top_layout.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel("问题反馈")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {int(font_size * 1.3)}px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                background-color: transparent;
            }}
        """)
        top_layout.addWidget(title_label)
        
        card_layout.addWidget(top_decoration)
        
        # 创建表单区域
        form_container = QFrame()
        form_container.setStyleSheet(f"""
            QFrame {{
                background-color: {BG};
                border-radius: 0px;
            }}
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(int(screen_width * 0.02), int(screen_height * 0.02), int(screen_width * 0.02), int(screen_height * 0.02))
        form_layout.setSpacing(spacing_v)
        
        # 问题类型输入区域
        type_section = self._create_radio_section("问题类型", ["功能问题", "界面问题", "性能问题", "建议", "其他"], font_size, spacing_v, spacing_h, screen_width)
        form_layout.addWidget(type_section["container"])
        self.type_group = type_section["group"]
        self.type_selected = type_section["selected"]
        
        # 标题输入区域
        title_section = self._create_input_section("标题", "请简要描述问题", font_size, int(input_height * 1.5), spacing_v * 2, screen_width)
        form_layout.addWidget(title_section["container"])
        self.title_input = title_section["input"]

        # 详细描述输入区域
        detail_section = self._create_text_section("详细描述", "请详细描述遇到的问题或建议…", font_size, input_height, spacing_v * 2, screen_width)
        form_layout.addWidget(detail_section["container"])
        self.detail_text = detail_section["text"]

        # 联系方式输入区域
        contact_section = self._create_input_section("联系方式", "QQ/邮箱/手机号（可选）", font_size, int(input_height * 1.5), spacing_v, screen_width)
        form_layout.addWidget(contact_section["container"])
        self.contact_input = contact_section["input"]
        
        # 按钮区域
        button_section = self._create_feedback_button_section(screen_width, screen_height, input_height, button_font_size, spacing_h, margin)
        form_layout.addWidget(button_section["container"])
        
        card_layout.addWidget(form_container)
        
        # 创建主布局并添加卡片
        self.feedback_layout = QVBoxLayout()
        self.feedback_layout.setContentsMargins(margin, margin, margin, margin)
        self.feedback_layout.setSpacing(spacing_v)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(margin, margin, margin, margin)
        h_layout.setSpacing(spacing_h)
        
        h_layout.addStretch(1)
        h_layout.addWidget(card_container)
        h_layout.addStretch(1)
        
        self.feedback_layout.addLayout(h_layout)
        
        self.setLayout(self.feedback_layout)
        
        # 设置窗口大小 - 调整为细长款式
        min_width = int(screen_width * 0.3)   # 减小最小宽度，实现细长效果
        min_height = int(screen_height * 0.7)  # 增加最小高度，使界面更细长
        self.setMinimumSize(min_width, min_height)  # 使用最小尺寸而非固定尺寸
        
        # 设置最大尺寸，防止窗口过大，保持细长比例
        max_width = int(screen_width * 0.4)   # 减小最大宽度，保持细长比例
        max_height = int(screen_height * 0.85) # 增加最大高度，使界面更细长
        self.setMaximumSize(max_width, max_height)
        
        # 设置窗口可调整大小
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 应用统一样式
        try:
            from styles import apply_dialog_style
            apply_dialog_style(self)
        except ImportError:
            pass
    
    def _create_combo_section(self, label_text, items, font_size, input_height, spacing_v, screen_width):
        """创建下拉选择框区域"""
        section = {}
        
        section["container"] = QWidget()
        layout = QVBoxLayout(section["container"])
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(spacing_v // 3)
        
        # 创建标签
        label = QLabel(label_text)
        label.setWordWrap(False)
        label.setMinimumWidth(1)
        label.setStyleSheet(f"color: {TEXT}; font-size: {font_size + 4}px; font-weight: bold; margin-bottom: {spacing_v // 6}px; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(label)
        
        # 创建下拉框
        section["combo"] = QComboBox()
        section["combo"].addItems(items)
        section["combo"].setFixedHeight(input_height)
        section["combo"].setMinimumWidth(int(screen_width * 0.2))  # 减小最小宽度，适应细长布局
        section["combo"].setMaximumWidth(int(screen_width * 0.25))  # 减小最大宽度，适应细长布局
        # 设置大小策略，允许水平扩展
        section["combo"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 调整内边距，减少额外空间
        padding = max(4, int(input_height * 0.1))  # 动态计算内边距，减小为输入框高度的10%
        section["combo"].setStyleSheet(f"""
            QComboBox {{
                border: 2px solid #d1d5db;
                border-radius: 12px;
                padding: {max(4, int(input_height * 0.1))}px;
                margin: 0;
                font-size: {max(12, font_size)}px;
                background-color: #ffffff;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                min-width: {int(screen_width * 0.25)}px;  # 与实际设置的最小宽度一致
                max-width: {int(screen_width * 0.3)}px;   # 与实际设置的最大宽度一致
            }}
            QComboBox:focus {{
                border: 2px solid #3b82f6;
                background-color: white;
            }}
        """)
        layout.addWidget(section["combo"])

        return section

    def _create_radio_section(self, label_text, items, font_size, spacing_v, spacing_h, screen_width):
        """创建单选按钮组区域"""
        section = {}
        section["container"] = QWidget()
        layout = QVBoxLayout(section["container"])
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(spacing_v // 4)
        
        label = QLabel(label_text)
        label.setWordWrap(False)
        label.setMinimumWidth(1)
        label.setMinimumHeight(30)
        label.setStyleSheet(f"color: {TEXT}; font-size: {font_size + 2}px; font-weight: bold; margin-bottom: {spacing_v}px; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(label)
        
        section["group"] = QButtonGroup()
        
        radio_container = QWidget()
        radio_layout = QHBoxLayout(radio_container)
        radio_layout.setContentsMargins(0, 0, 0, 0)
        radio_layout.setSpacing(spacing_h)
        
        radio_style = f"""
            QRadioButton {{
                spacing: 6px;
                font-size: {font_size - 2}px;
                color: #2c3e50;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                padding: 4px 0;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            QRadioButton::indicator:unchecked {{
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: #3498db;
            }}
        """
        
        for i, item in enumerate(items):
            radio = QRadioButton(item)
            radio.setStyleSheet(radio_style)
            radio_layout.addWidget(radio)
            section["group"].addButton(radio)
            if i == 0:
                radio.setChecked(True)
                section["selected"] = radio
        
        layout.addWidget(radio_container)
        section["container"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        return section
    
    def _create_input_section(self, label_text, placeholder, font_size, input_height, spacing_v, screen_width, echo_mode=QLineEdit.Normal):
        """创建输入框区域"""
        section = {}
        
        section["container"] = QWidget()
        layout = QVBoxLayout(section["container"])
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(spacing_v // 3)
        
        label = QLabel(label_text)
        label.setWordWrap(False)
        label.setMinimumWidth(1)
        label.setFixedHeight(40)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        label.setStyleSheet(f"color: {TEXT}; font-size: {font_size + 2}px; font-weight: bold; margin-bottom: {spacing_v}px; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(label)
        
        section["input"] = QLineEdit()
        section["input"].setPlaceholderText(placeholder)
        section["input"].setFixedHeight(input_height)
        section["input"].setEchoMode(echo_mode)
        section["input"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        padding = max(8, int(input_height * 0.2))
        section["input"].setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: {padding}px;
                margin: 0;
                font-size: {max(12, font_size)}px;
                color: #2c3e50;
                background-color: #ffffff;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QLineEdit:focus {{
                border: 2px solid #3498db;
                background-color: white;
            }}
            QLineEdit:disabled {{
                border: 2px solid #ecf0f1;
                background-color: #f5f6fa;
                color: #95a5a6;
            }}
            QLineEdit:invalid {{
                border: 2px solid #e74c3c;
                background-color: #fdedec;
            }}
        """)
        layout.addWidget(section["input"])
        
        return section
    
    def _create_text_section(self, label_text, placeholder, font_size, input_height, spacing_v, screen_width):
        """创建文本框区域"""
        section = {}
        
        # 创建普通容器作为主容器
        section["container"] = QWidget()
        
        # 创建布局
        layout = QVBoxLayout(section["container"])
        layout.setContentsMargins(0, 0, 0, 0)  # 设置内边距
        layout.setSpacing(spacing_v // 3)  # 减小内部间距，从spacing_v // 2改为spacing_v // 3
        
        label = QLabel(label_text)
        label.setWordWrap(False)
        label.setMinimumWidth(1)
        label.setFixedHeight(40)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        label.setStyleSheet(f"color: {TEXT}; font-size: {font_size + 2}px; font-weight: bold; margin-bottom: {spacing_v // 6}px; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(label)
        
        section["text"] = QTextEdit()
        section["text"].setPlaceholderText(placeholder)
        section["text"].setMinimumHeight(int(input_height * 1.5))
        section["text"].setMaximumHeight(int(input_height * 8))
        section["text"].setMinimumWidth(int(screen_width * 0.3))
        section["text"].setMaximumWidth(int(screen_width * 0.4))
        section["text"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        section["text"].setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        section["text"].setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        padding = max(8, int(input_height * 0.1))
        
        section["text"].setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: {padding}px;
                margin: 0;
                font-size: {max(12, font_size)}px;
                background-color: #ffffff;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                min-width: {int(screen_width * 0.3)}px;
                max-width: {int(screen_width * 0.4)}px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 2px solid #3498db;
                background-color: white;
            }}
            QTextEdit:disabled {{
                border: 2px solid #ecf0f1;
                background-color: #f5f6fa;
                color: #95a5a6;
            }}
        """)
        
        layout.addWidget(section["text"])
        
        return section
    
    def _create_feedback_button_section(self, screen_width, screen_height, input_height, button_font_size, spacing_h, margin):
        """创建反馈界面按钮区域"""
        section = {}
        
        section["container"] = QFrame()
        section["container"].setStyleSheet("QFrame { background-color: transparent; }")
        layout = QHBoxLayout(section["container"])
        layout.setContentsMargins(margin//2, margin//2, margin//2, margin//2)
        layout.setSpacing(spacing_h * 2)
        
        submit_button = QPushButton("提交")
        submit_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #0A84FF;
                color: white;
                border-radius: {int(input_height/2)}px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)
        submit_button.setMinimumWidth(int(screen_width * 0.08))
        submit_button.setMinimumHeight(input_height)
        submit_button.clicked.connect(self.submit_feedback)
        layout.addWidget(submit_button)

        layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: #8E8E93;
                border: 1px solid #D1D1D6;
                border-radius: {int(input_height/2)}px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #F0F0F2;
                border-color: #0A84FF;
                color: #0A84FF;
            }}
            QPushButton:pressed {{
                background-color: #006AE0;
            }}
        """)
        cancel_button.setMinimumWidth(int(screen_width * 0.08))
        cancel_button.setMinimumHeight(input_height)
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        
        return section

    def submit_feedback(self):
        """提交反馈到数据库"""
        feedback_type = self.type_selected.text()
        title = self.title_input.text().strip()
        detail = self.detail_text.toPlainText().strip()
        contact = self.contact_input.text().strip()

        if not title or not detail:
            self.show_beautiful_message('warning', "提示", "标题和详细描述不能为空", parent=self)
            return

        try:
            # 获取当前用户名
            username = "anonymous"
            if hasattr(self.parent(), 'current_user') and self.parent().current_user:
                username = self.parent().current_user

            # 使用全局DatabaseHelper实例提交反馈
            from database_helper import db_helper
            feedback_data = {
                'username': username,
                'feedback_type': feedback_type,
                'title': title,
                'detail': detail,
                'contact': contact,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result = db_helper.try_supabase_then_local(
                lambda: self._submit_feedback_to_supabase(feedback_data),
                lambda: self._submit_feedback_to_sqlite(feedback_data)
            )
            
            if result:
                self.show_beautiful_message('information', "成功", "反馈已提交，感谢您的意见！", parent=self)
                self.accept()
            else:
                self.show_beautiful_message('warning', "失败", "提交反馈失败，请稍后再试", parent=self)
        except Exception as e:
            self.show_beautiful_message('warning', "失败", f"提交失败: {str(e)}", parent=self)

    def _submit_feedback_to_supabase(self, feedback_data):
        """提交反馈到Supabase"""
        # 由于 Supabase 的 feedback 表结构与本地不匹配，直接跳过 Supabase 提交
        # 返回 False 以便系统回退到本地 SQLite 存储
        return False

    def _submit_feedback_to_sqlite(self, feedback_data):
        """提交反馈到SQLite"""
        from utils import get_database_path
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO feedback (username, feedback_type, title, detail, contact, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (feedback_data['username'], feedback_data['feedback_type'], 
              feedback_data['title'], feedback_data['detail'], 
              feedback_data['contact'], feedback_data['created_at']))

        conn.commit()
        conn.close()
        return True



    





class FolderManager(QDialog):
    # 定义信号，用于在主线程中执行操作
    _execute_add_operations_signal = pyqtSignal(object, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("管理录制操作")
        
        # 连接信号到槽函数
        self._execute_add_operations_signal.connect(self._on_execute_add_operations)
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        
        # 使用统一的动态尺寸计算 - 进一步减小窗口宽度
        width = int(get_screen_size(0.45)[0])
        height = int(get_screen_size(0.5)[1])  # 减小高度为50%，使主界面更矮
        self.resize(width, height)
        min_width = int(get_screen_size(0.35)[0])
        min_height = int(get_screen_size(0.4)[1])  # 减小最小高度为40%
        self.setMinimumSize(min_width, min_height)
        
        # 使用统一的窗口居中函数
        center_window(self)
        
        # 使用统一样式函数
        self.table_style = get_table_style()
        self.button_style = get_button_style()
        self.input_style = get_input_style()

        # 组合技风格卡片容器
        _outer = QVBoxLayout(self)
        _outer.setContentsMargins(0, 0, 0, 0)
        _outer.setSpacing(0)
        _card = QFrame(self)
        _card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #FFFFFF, stop:1 #FFFFFF);
                border-radius: 18px;
                border: 2px solid #E5E5EA;
            }
        """)
        _cl = QVBoxLayout(_card)
        _cl.setSpacing(8)
        _cl.setContentsMargins(15, 12, 15, 15)
        _outer.addWidget(_card)
        layout = _cl

        # 添加顶部按钮区域
        top_button_layout = QHBoxLayout()
        top_button_layout.setSpacing(5)  # 进一步减小按钮间距
        
        # 添加"删除无需确认"复选框
        self.confirm_delete_checkbox = QCheckBox("删除无需确认")
        self.confirm_delete_checkbox.setToolTip("勾选后，点击删除按钮将直接删除操作，不再弹出确认对话框")
        # 按屏幕比例设置字体大小
        screen_width, screen_height = get_screen_size()
        font_size = int(screen_height * 0.015)  # 屏幕高度的1.5%
        self.confirm_delete_checkbox.setStyleSheet(f"font-size: {font_size}px; padding: 4px; color: black;")
        top_button_layout.addWidget(self.confirm_delete_checkbox)
        
        # 添加回收站按钮
        self.trash_button = QPushButton("🗑️ 回收站")
        self.trash_button.setMinimumSize(120, 30)
        self.trash_button.setStyleSheet(f"""
            QPushButton {{
                background: #0A84FF;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)
        self.trash_button.clicked.connect(self.open_trash)
        top_button_layout.addWidget(self.trash_button)
        
        # 添加弹性空间
        top_button_layout.addStretch()
        
        layout.addLayout(top_button_layout)

        # 创建文件夹表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["创建时间", "文件夹名称", "快捷键", "重命名"])
        
        # 隐藏垂直表头（行号），解决左上角空白问题
        self.table.verticalHeader().setVisible(False)
        
        # 应用表格样式 - 与styles.py保持一致
        self.table.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                color: black;
                border-radius: 12px;
                border-radius: 12px;
                gridline-color: transparent;
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                font-size: 13px;
            }
            QHeaderView::section {
                background: white;
                color: #6E6E73;
                padding: 14px 18px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.06);
                font-weight: 600;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 14px 18px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            }
            QTableWidget::item:hover {
                background: rgba(195,240,202,0.3);
            }
            QTableWidget::item:selected {
                background: transparent;
                color: black;
            }
            QScrollBar:vertical {
                width: 8px; background: transparent; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,0,0,0.15); border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0,0,0,0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal {
                height: 8px; background: transparent; border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(0,0,0,0.15); border-radius: 4px; min-width: 30px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """)

        # 设置表格字体以支持中文显示，调整字体大小
        font = self.table.font()
        font.setFamily("PingFang SC")  # 使用微软雅黑字体支持中文
        font.setPointSize(9)  # 减小字体大小
        self.table.setFont(font)

    # 设置列宽模式 - 所有列都可调整，默认填满窗口
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)  # 禁用最后一列自动拉伸
        
        # 所有列都设置为Interactive模式，允许用户手动调整列宽
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # 文件夹名称列可调整
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 创建时间列可调整
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 快捷键按钮列可调整
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # 重命名按钮列可调整
        
        # 先添加表格到布局，然后再设置列宽
        layout.addWidget(self.table)
        
        # 延迟设置列宽，确保窗口已经完全布局
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.setup_table_columns)


        # 加载文件夹数据
        self.load_folders()

        # 加载删除确认设置
        self.load_delete_confirm_setting()
        # 当复选框状态改变时保存设置
        self.confirm_delete_checkbox.stateChanged.connect(self.save_delete_confirm_setting)

        # 优化表格布局设置
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.NoPen)
        
        # 确保表格单元格内容垂直居中
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        
        # 设置表格单元格内容居中
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                if self.table.item(row, col):
                    self.table.item(row, col).setTextAlignment(Qt.AlignCenter)

        # 设置合适的行高 - 增加行间距
        self.table.verticalHeader().setDefaultSectionSize(50)

        # 设置表头字体
        header_font = self.table.horizontalHeader().font()
        header_font.setPointSize(9)  # 减小表头字体大小
        header_font.setFamily("PingFang SC")
        self.table.horizontalHeader().setFont(header_font)
        
        # 设置表格选择行为，禁用选中效果
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        # 监听列宽变化，实时更新按钮位置
        self.table.horizontalHeader().sectionResized.connect(self.on_column_resized)
        
        # 添加单元格点击事件处理，使点击文件夹名称列直接打开查看画面
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        
        # 添加右键菜单事件处理
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 表格显示完成后更新按钮位置
        self.table.showEvent = self.on_table_show

    def load_folders(self):
        from utils import get_recordings_path
        recordings_dir = get_recordings_path()
        os.makedirs(recordings_dir, exist_ok=True)
        folders = []
        try:
            # 使用try-except块处理可能的编码问题
            for item in os.listdir(recordings_dir):
                try:
                    item_path = os.path.join(recordings_dir, item)
                    if os.path.isdir(item_path) and item != 'trash':
                        ctime = datetime.fromtimestamp(os.path.getctime(item_path)).strftime('%m-%d %H:%M')
                        folders.append((item, ctime, item_path))
                except Exception as e:
                    # print(f"处理文件夹 {item} 时出错: {e}")  # [日志已禁用]
                    continue
        except Exception as e:
            # print(f"读取录制目录时出错: {e}")  # [日志已禁用]
            return
            
        # 加载调用次数
        usage_counts = {}
        if hasattr(self, 'parent') and self.parent:
            usage_counts = self.parent._get_usage_counts()
        for fi in range(len(folders)):
            fi_name = folders[fi][0]
            fi_count = usage_counts.get(fi_name, 0)
            folders[fi] = folders[fi] + (fi_count,)
        folders.sort(key=lambda x: (-x[3], x[1]), reverse=False)
        # 恢复到原始格式
        folders = [(f[0], f[1], f[2]) for f in folders]
        self.table.setRowCount(len(folders))
        for i, (name, ctime, path) in enumerate(folders):
            # 创建创建时间项
            ctime_item = QTableWidgetItem(ctime)
            ctime_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, ctime_item)
            
            # 创建文件夹名称项并设置字体
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)  # 设置水平和垂直居中对齐
            # 确保路径使用正确的编码，特别是中文路径
            normalized_path = os.path.normpath(str(path))
            name_item.setData(Qt.UserRole, normalized_path)
            self.table.setItem(i, 1, name_item)
            # 创建样式化的按钮，使用按屏幕比例计算的尺寸和字体大小
            screen_width, screen_height = get_screen_size()
            btn_height = int(screen_height * 0.03)  # 屏幕高度的3%
            
            # 按屏幕比例设置按钮字体大小
            shortcut_btn_font_size = int(screen_height * 0.011)  # 屏幕高度的1.1%
            rename_btn_font_size = int(screen_height * 0.012)  # 屏幕高度的1.2%

            # 规范化路径后查找快捷键，确保路径格式一致
            current_shortcut = ""
            normalized_path_lower = normalized_path.lower()
            for stored_path, shortcut in self.parent.shortcuts.items():
                stored_norm = os.path.normpath(stored_path).lower()
                if stored_norm == normalized_path_lower:
                    current_shortcut = shortcut
                    break
            
            shortcut_text = current_shortcut if current_shortcut else "快捷键"
            shortcut_btn = QPushButton(shortcut_text)
            _fm = QFontMetrics(shortcut_btn.font())
            _tw = _fm.horizontalAdvance(shortcut_text) if hasattr(_fm, 'horizontalAdvance') else _fm.width(shortcut_text)
            shortcut_btn.setFixedSize(max(60, _tw + 20), 30)
            shortcut_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: #0A84FF;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: {shortcut_btn_font_size}px;
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                    text-align: center;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(200,200,210,0.4);
                }}
                QPushButton:pressed {{
                    background-color: rgba(200,200,210,0.6);
                }}
            """)
            shortcut_btn.clicked.connect(lambda _, p=normalized_path: self.set_shortcut(p))

            rename_btn = QPushButton("重命名")
            rename_btn.setFixedSize(56, 30)
            rename_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: #0A84FF;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: {rename_btn_font_size}px;
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                    text-align: center;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(200,200,210,0.4);
                }}
                QPushButton:pressed {{
                    background-color: rgba(200,200,210,0.6);
                }}
            """)
            rename_btn.clicked.connect(lambda _, p=normalized_path: self.rename_folder(p))
            
            # 创建重命名按钮的容器，确保按钮在单元格中居中
            rename_container = QWidget()
            rename_container.setStyleSheet("background: transparent;")  # 设置透明背景
            rename_layout = QHBoxLayout(rename_container)
            rename_layout.setContentsMargins(0, 0, 0, 0)
            rename_layout.setSpacing(0)
            rename_layout.setAlignment(Qt.AlignCenter)
            rename_layout.addWidget(rename_btn)
            
            # 创建快捷键按钮的容器，确保按钮在单元格中居中
            shortcut_container = QWidget()
            shortcut_container.setStyleSheet("background: transparent;")  # 设置透明背景
            shortcut_layout = QHBoxLayout(shortcut_container)
            shortcut_layout.setContentsMargins(0, 0, 0, 0)
            shortcut_layout.setSpacing(0)
            shortcut_layout.setAlignment(Qt.AlignCenter)
            shortcut_layout.addWidget(shortcut_btn)
            
            # 直接使用setCellWidget，让Qt自动处理按钮位置
            self.table.setCellWidget(i, 2, shortcut_container)
            self.table.setCellWidget(i, 3, rename_container)
            
            # 确保按钮容器在单元格中居中
            for container in [rename_container, shortcut_container]:
                if container:
                    # 设置容器样式，确保在单元格中居中
                    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                    layout = container.layout()
                    if layout:
                        layout.setContentsMargins(0, 0, 0, 0)
                        layout.setAlignment(Qt.AlignCenter)

            # ★ 修复：右键落在"快捷键/重命名"单元格（cellWidget 容器或按钮）上时，
            # 这些子控件默认 DefaultContextMenu 会吞掉右键事件，导致表格的右键菜单
            # （含"设置默认间隔"）弹不出来。给容器和按钮都挂上 CustomContextMenu，
            # 并把坐标转换回表格 viewport 坐标系转发给 show_context_menu。
            for _cw in (shortcut_container, rename_container, shortcut_btn, rename_btn):
                if _cw is None:
                    continue
                _cw.setContextMenuPolicy(Qt.CustomContextMenu)
                _cw.customContextMenuRequested.connect(
                    lambda pos, w=_cw: self.show_context_menu(
                        self.table.viewport().mapFromGlobal(w.mapToGlobal(pos))
                    )
                )

            # 保持按钮原有大小设置，确保与容器匹配
            pass
    
    def setup_table_columns(self):
        """设置表格列宽，填满整个窗口"""
        header = self.table.horizontalHeader()
        window_width = self.width()
        layout_margin = 2  # 左右边距各1像素
        available_width = window_width - layout_margin
        button_width = max(60, int(available_width * 0.1))  # 按钮宽度最小60像素，或可用宽度的10%
        remaining_width = available_width - 2 * button_width
        folder_name_width = int(remaining_width * 0.7)  # 文件夹名称列占70%
        time_width = remaining_width - folder_name_width  # 创建时间列占剩余的30%
        
        header.resizeSection(0, time_width)  # 创建时间
        header.resizeSection(1, folder_name_width)  # 文件夹名称
        header.resizeSection(2, button_width)  # 快捷键按钮
        header.resizeSection(3, button_width)  # 重命名按钮

    def view_images(self, folder_path):
        folder_path = str(folder_path)
        if not os.path.isdir(folder_path):
            self.parent.show_beautiful_message('critical', "错误", f"无效的目录路径: {folder_path}", parent=self)
            return
        
        # 临时禁用·键的全局快捷键，避免在查看图片窗口中触发录制新流程
        self.parent.temporarily_disable_grave_hotkey()
        # print("[查看图片] 临时禁用·键全局快捷键")  # [日志已禁用]
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"查看图片 - {os.path.basename(str(folder_path))}")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        # 设置对话框大小为屏幕的60%，使界面更紧凑
        screen_width, screen_height = get_screen_size()
        dialog.resize(int(screen_width * 0.6), int(screen_height * 0.6))
        
        # 存储当前查看的文件夹路径，用于热键回调
        self._current_view_folder_path = folder_path
        
        # 注册查看图片窗口专用的·键全局热键
        self._view_images_grave_hotkey_id = None
        try:
            
            # 使用 suppress=True 确保热键被捕获，不传递给其他应用
            # 保存对话框和路径的引用，避免闭包问题
            current_dialog = dialog
            current_folder = folder_path
            
            def view_images_grave_handler():
                """查看图片窗口中 grave 键的处理"""
                # ★ 检查临时禁用标志
                if getattr(self, '_hotkeys_temporarily_disabled', False):
                    return
                # print("[查看图片] ===== 全局热键 grave 被按下 =====")  # [日志已禁用]
                # print(f"[查看图片] current_dialog: {current_dialog}")  # [日志已禁用]
                # print(f"[查看图片] current_folder: {current_folder}")  # [日志已禁用]

                # 直接调用，不使用 QTimer
                try:
                    self._on_grave_key_in_view_images(current_dialog, current_folder)
                except Exception as e:
                    # print(f"[查看图片] _on_grave_key_in_view_images 调用失败: {e}")  # [日志已禁用]
                    import traceback
                    traceback.print_exc()
            
            # 注册热键，不使用 suppress，避免线程问题
            self._view_images_grave_hotkey_id = keyboard.add_hotkey(
                'grave', 
                view_images_grave_handler,
                suppress=False,
                trigger_on_release=False
            )
            # print(f"[查看图片] 注册 grave 键专用热键成功，ID: {self._view_images_grave_hotkey_id}")  # [日志已禁用]
        except Exception as e:
            # print(f"[查看图片] 注册 grave 键专用热键失败: {e}")  # [日志已禁用]
            import traceback
            traceback.print_exc()
            self._view_images_grave_hotkey_id = None
        
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        center_window(dialog)
        dialog.setMinimumHeight(400)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # ── macOS 毛玻璃容器（唯一有边框）──
        _outer = QFrame(dialog)
        _outer.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 12px;
                border: 2px solid #E5E5EA;
            }
        """)
        _cl = QVBoxLayout(_outer)
        _cl.setContentsMargins(0,0,0,0)
        _cl.setSpacing(0)
        # ── 交通灯（macOS 三色点）──
        _dot_bar = QWidget()
        _dot_bar.setFixedHeight(38)
        _dot_bar.setStyleSheet("background:transparent; border:none;")
        _dot_lo = QHBoxLayout(_dot_bar)
        _dot_lo.setContentsMargins(16, 10, 16, 0)
        _dot_lo.addStretch()
        def _closeD(ev):
            if ev.button()==Qt.LeftButton: dialog.close()
        _red_dot = QFrame()
        _red_dot.setFixedSize(16, 16)
        _red_dot.setStyleSheet("background:#FF5F57; border-radius:6px; border:none;")
        _red_dot.mousePressEvent = _closeD
        _red_dot.setCursor(Qt.PointingHandCursor)
        _dot_lo.addWidget(_red_dot)
        # 交通灯条也支持拖动窗口
        def _dot_start_drag(ev):
            if ev.button()==Qt.LeftButton: dialog._drag_pos=ev.globalPos()-dialog.pos()
        def _dot_do_drag(ev):
            if getattr(dialog,'_drag_pos',None) is not None and ev.buttons()&Qt.LeftButton:
                dialog.move(ev.globalPos()-dialog._drag_pos)
        _dot_bar.mousePressEvent=_dot_start_drag
        _dot_bar.mouseMoveEvent=_dot_do_drag
        _cl.addWidget(_dot_bar)
        # ── 标题栏 ──
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("background:transparent; border:none;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 16, 0)
        title_label = QLabel(f"📁 {os.path.basename(str(folder_path))}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size:14px; font-weight:600; color:#1D1D1F; background:transparent; border:none;")
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        title_layout.addStretch()
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        # 标题栏拖动窗口
        def _start_drag(ev):
            if ev.button() == Qt.LeftButton:
                dialog._drag_pos = ev.globalPos() - dialog.pos()
        def _do_drag(ev):
            if getattr(dialog, '_drag_pos', None) is not None and ev.buttons() & Qt.LeftButton:
                dialog.move(ev.globalPos() - dialog._drag_pos)
        title_bar.mousePressEvent = _start_drag
        title_bar.mouseMoveEvent = _do_drag
        _cl.addWidget(title_bar)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; padding: 0; margin: 0; }")
        scroll_area.viewport().setStyleSheet("background: transparent; padding: 0; margin: 0;")
        scroll_root = QWidget()  # 最外层容器 (撑满滚动区)
        scroll_root.setStyleSheet("background: transparent; border: none;")
        root_layout = QHBoxLayout(scroll_root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 列表容器：占满整个宽度
        list_wrapper = QWidget()
        list_wrapper.setStyleSheet("background: rgba(245, 245, 247, 0.8); border: none;")
        list_wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        list_layout = QVBoxLayout(list_wrapper)
        list_layout.setContentsMargins(12, 12, 12, 12)
        list_layout.setSpacing(0)
        list_layout.setAlignment(Qt.AlignTop)
        root_layout.addWidget(list_wrapper)
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
        image_files.sort(key=lambda x: int(re.search(r'操作(\d+)', x).group(1)) if re.search(r'操作(\d+)', x) else 0)
        
        # 检查是否有recording.json文件（坐标录制）
        recording_json_path = os.path.join(folder_path, 'recording.json')
        has_recording_json = os.path.exists(recording_json_path)
        
        # 如果没有图片文件也没有recording.json，提示错误
        if not image_files and not has_recording_json:
            self.parent.show_beautiful_message('information', "提示", "该文件夹中没有图片文件！", parent=dialog)
            return
        
        # 统一融合视图：按 recording.json 步骤顺序显示所有操作
        if has_recording_json:
            self._populate_unified_rows(dialog, folder_path, list_layout)
        elif image_files:
            # 没有 recording.json 但有图片时，降级显示纯图片列表
            def _preview_img(fp):
                _d = QDialog(dialog)
                _d.setWindowTitle("图片预览")
                _d.resize(600, 500)
                _l = QVBoxLayout(_d)
                _s = QScrollArea()
                _s.setWidgetResizable(True)
                _s.setStyleSheet("QScrollArea{border:none;background:#1C1C1E;}")
                _lb = QLabel()
                _lb.setAlignment(Qt.AlignCenter)
                _p = load_qpixmap(fp)
                if _p: _lb.setPixmap(_p.scaled(560, 460, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                _lb.setStyleSheet("background:#1C1C1E;padding:10px;")
                _s.setWidget(_lb)
                _l.addWidget(_s)
                _d.exec_()
            _fallback_label = QLabel(f"📁 共 {len(image_files)} 张图片（无操作步骤数据）")
            _fallback_label.setStyleSheet("font-size:12px; color:#86868B; padding:8px 0; background:transparent; border:none;")
            list_layout.addWidget(_fallback_label)
            for _i, _f in enumerate(image_files):
                _img_path = os.path.join(folder_path, _f)
                _thumb = QLabel()
                _pix = load_qpixmap(_img_path)
                if _pix:
                    _pix = _pix.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    _thumb.setPixmap(_pix)
                _thumb.setFixedSize(64, 64)
                _thumb.setStyleSheet("QLabel{background:#F5F5F7;border-radius:6px;padding:2px;}")
                _thumb.setAlignment(Qt.AlignCenter)
                _thumb.setCursor(Qt.PointingHandCursor)
                _thumb.mousePressEvent = lambda e, fp=_img_path: _preview_img(fp)
                list_layout.addWidget(_thumb, 0, Qt.AlignTop)
            list_layout.addStretch()
        
        scroll_area.setWidget(scroll_root)
        _cl.addWidget(scroll_area)
        layout.addWidget(_outer)
        # 添加底部按钮区域 - macOS风格
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(16, 8, 16, 12)
        
        # 继续添加操作按钮（有图片或 recording.json 时显示）
        if image_files or has_recording_json:
            add_btn = QPushButton("➕ 继续添加操作")
            add_btn.setFixedSize(180, 42)
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 21px;
                    font-weight: 600;
                    font-size: 14px;
                    font-family: 'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei UI', sans-serif;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #006AE0;
                }
                QPushButton:pressed {
                    background-color: #004DB3;
                }
            """)
            add_btn.clicked.connect(lambda: self.add_more_operations(dialog, folder_path))
            button_layout.addWidget(add_btn)
            
            # 纯坐标录制按钮
            coord_btn = QPushButton("🖱️ 添加坐标操作")
            coord_btn.setFixedSize(180, 42)
            coord_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34C759;
                    color: white;
                    border-radius: 21px;
                    font-weight: 600;
                    font-size: 14px;
                    font-family: 'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei UI', sans-serif;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #28A745;
                }
                QPushButton:pressed {
                    background-color: #1E7E34;
                }
            """)
            coord_btn.clicked.connect(lambda: self.add_more_operations_coord(dialog, folder_path))
            button_layout.addWidget(coord_btn)
        
        _cl.addLayout(button_layout)
        self.parent._view_images_dialog = dialog
        # 如果parent有folder_manager属性，也设置它
        if hasattr(self.parent, 'folder_manager') and self.parent.folder_manager:
            self.parent.folder_manager._view_images_dialog = dialog
        self.parent._view_images_grid_layout = list_layout
        
        # 添加键盘事件处理 - ·键触发继续添加操作
        def keyPressEvent(event):
            from PyQt5.QtCore import Qt
            # 检查是否按下·键（grave键，ASCII 96）
            if event.key() == Qt.Key_QuoteLeft or event.key() == 96:
                # print("[查看图片] 检测到·键，触发继续添加操作")  # [日志已禁用]
                self.add_more_operations(dialog, folder_path)
            else:
                # 其他键调用默认处理
                QDialog.keyPressEvent(dialog, event)
        
        dialog.keyPressEvent = keyPressEvent
        
        # 对话框关闭时清理资源
        def on_dialog_finished(result):
            # 检查是否需要在延迟后移除热键（避免在热键回调中直接移除导致崩溃）
            need_remove = getattr(self, '_need_remove_grave_hotkey', False)
            
            def delayed_cleanup():
                # 移除查看图片窗口专用的·键热键
                try:
                    if hasattr(self, '_view_images_grave_hotkey_id') and self._view_images_grave_hotkey_id:
                        keyboard.remove_hotkey(self._view_images_grave_hotkey_id)
                        # print("[查看图片] 移除 grave 键专用热键")  # [日志已禁用]
                        self._view_images_grave_hotkey_id = None
                except Exception as e:
                    # print(f"[查看图片] 移除 grave 键专用热键失败: {e}")  # [日志已禁用]
                    pass
                
                # 重新启用全局·键快捷键
                self.parent.reenable_grave_hotkey()
                # print("[查看图片] 重新启用 grave 键全局快捷键")  # [日志已禁用]
                
                # 清理存储的路径
                if hasattr(self, '_current_view_folder_path'):
                    delattr(self, '_current_view_folder_path')
                
                # 清理标记
                if hasattr(self, '_need_remove_grave_hotkey'):
                    delattr(self, '_need_remove_grave_hotkey')
            
            if need_remove:
                # 延迟100ms执行清理，避免在热键回调线程中操作
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, delayed_cleanup)
            else:
                # 直接执行清理
                delayed_cleanup()
        
        dialog.finished.connect(on_dialog_finished)
        
        dialog.show()

    def _on_grave_key_in_view_images(self, dialog, folder_path):
        """处理查看图片窗口中的 grave 键按下事件"""
        # print("[查看图片] ===== _on_grave_key_in_view_images 被调用 =====")  # [日志已禁用]
        # print(f"[查看图片] dialog 对象: {dialog}")  # [日志已禁用]
        # print(f"[查看图片] dialog.isVisible(): {dialog.isVisible() if dialog else 'N/A'}")  # [日志已禁用]
        # print(f"[查看图片] folder_path: {folder_path}")  # [日志已禁用]
        
        # 检查对话框是否仍然打开
        if dialog and dialog.isVisible():
            # print("[查看图片] 对话框可见，准备执行继续添加操作")  # [日志已禁用]
            # 使用信号槽机制确保在主线程中执行
            self._execute_add_operations_signal.emit(dialog, folder_path)
        else:
            # print("[查看图片] 对话框已关闭或无效，忽略此次按键")  # [日志已禁用]
            pass

    def _on_execute_add_operations(self, dialog, folder_path):
        """槽函数：在主线程中执行继续添加操作"""
        # print("[查看图片] _on_execute_add_operations 槽函数被调用")  # [日志已禁用]
        try:
            self.add_more_operations(dialog, folder_path)
            # self.debug_print("[查看图片] add_more_operations 执行完成")  # [日志已禁用]
        except Exception as e:
            # self.debug_print(f"[查看图片] add_more_operations 执行失败: {e}")  # [日志已禁用]
            import traceback
            traceback.print_exc()

    def _swap_steps(self, idx_a, idx_b, folder_path):
        try:
            recording_json_path = os.path.join(folder_path, 'recording.json')
            recording_data = []
            if os.path.exists(recording_json_path):
                recording_data = load_json_data(recording_json_path)
            if not isinstance(recording_data, list) or len(recording_data) < 2:
                return
            recording_data.sort(key=lambda x: x.get('step', 0))
            
            # ★ 修复：UI 列表只显示有图片的操作，但 recording_data 包含所有操作
            # 必须通过图片文件名获取步骤号，再映射到 recording_data 中的真实索引
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
            image_files.sort(key=lambda x: int(re.search(r'操作(\d+)', x).group(1)) if re.search(r'操作(\d+)', x) else 0)
            if idx_a >= len(image_files) or idx_b >= len(image_files):
                return
            match_a = re.search(r'操作(\d+)', image_files[idx_a])
            match_b = re.search(r'操作(\d+)', image_files[idx_b])
            if not match_a or not match_b:
                return
            step_a = int(match_a.group(1))
            step_b = int(match_b.group(1))
            
            # 在 recording_data 中找到对应步骤号的索引
            rec_a_idx = rec_b_idx = None
            for i, rec in enumerate(recording_data):
                if rec.get('step') == step_a:
                    rec_a_idx = i
                if rec.get('step') == step_b:
                    rec_b_idx = i
            if rec_a_idx is None or rec_b_idx is None:
                return
            
            # 交换两个记录
            recording_data[rec_a_idx], recording_data[rec_b_idx] = recording_data[rec_b_idx], recording_data[rec_a_idx]
            
            # 重新编号并更新 image 字段
            for i, rec in enumerate(recording_data):
                rec['step'] = i + 1
                if 'image' in rec:
                    rec['image'] = f"操作{i + 1}.png"
            save_json_data(recording_json_path, recording_data)
            
            # 交换图片文件（使用原始步骤号定位文件）
            img_a = os.path.join(folder_path, f"操作{step_a}.png")
            img_b = os.path.join(folder_path, f"操作{step_b}.png")
            img_a_tmp = os.path.join(folder_path, f"操作{step_a}_tmp.png")
            if os.path.exists(img_a) and os.path.exists(img_b):
                os.rename(img_a, img_a_tmp)
                os.rename(img_b, img_a)
                os.rename(img_a_tmp, img_b)
            elif os.path.exists(img_a) and not os.path.exists(img_b):
                os.rename(img_a, img_b)
            elif os.path.exists(img_b) and not os.path.exists(img_a):
                os.rename(img_b, img_a)
            
            if idx_a < len(self.image_actions) and idx_b < len(self.image_actions):
                self.image_actions[idx_a], self.image_actions[idx_b] = self.image_actions[idx_b], self.image_actions[idx_a]
            self.refresh_view_images(folder_path)
        except Exception as e:
            self.parent.show_beautiful_message('critical', "错误", f"交换步骤失败: {str(e)}")

    def _populate_unified_rows(self, dialog, folder_path, list_layout):
        """统一融合视图：按 recording.json 步骤顺序显示所有操作（图片/坐标/按键/文本/滚动等）"""
        recording_json_path = os.path.join(folder_path, 'recording.json')
        has_recording_json = os.path.exists(recording_json_path)
        if not has_recording_json:
            return
        recording_data = load_json_data(recording_json_path)
        if not isinstance(recording_data, list) or not recording_data:
            return

        # ======================================================================
        # ★★★ 历史数据自修复（解决：删除/交换纯坐标步骤后，image文件名与磁盘物理文件错乱 ★★★
        # 检查：磁盘上的操作*.png数量 是否等于 JSON中image字段非空的条目数，且每个image字段都真实存在
        # 如果不一致 → 按"磁盘图片顺序"重新给 JSON中的image条目分配 操作1,操作2,... 文件名
        # 这样之前被bug搞坏的数据，用户只要打开"查看步骤"一次就自动修复了！
        # ======================================================================
        try:
            import os as _os
            import re as _re
            _disk_imgs = [_f for _f in _os.listdir(folder_path) if _f.lower().endswith('.png') and _re.search(r'操作(\d+)\.png', _f)]
            def _dn(_f):
                _mm = _re.search(r'操作(\d+)\.png', _f)
                return int(_mm.group(1)) if _mm else 999999
            _disk_imgs_sorted = sorted(_disk_imgs, key=_dn)
            _disk_count = len(_disk_imgs_sorted)
            _json_image_entries = [(i, d) for i, d in enumerate(recording_data) if d.get('image')]
            _json_img_count = len(_json_image_entries)
            # 判定是否需要修复：(数量对不上) OR (有任意image字段指向的文件不存在) OR (image编号和第几次出现不匹配)
            _need_fix = False
            if _disk_count != _json_img_count:
                _need_fix = True
            else:
                _c = 0
                for _, _d in _json_image_entries:
                    _c += 1
                    _expected = f"操作{_c}.png"
                    if _d.get('image') != _expected or not _os.path.exists(_os.path.join(folder_path, _expected)):
                        _need_fix = True
                        break
            if _need_fix:
                # ★★★ 核心修复：rename 磁盘文件必须跟着 JSON 里的有image条目走！
                # （而不是磁盘和JSON各自排序 → 会导致"图片内容"与"JSON里的x/y坐标"错位！）
                # 逻辑：遍历JSON，按顺序遇到每一条有image的条目 → 把这个条目当前引用的磁盘图片
                #       rename成 "操作N.png"（N=这是第几张图），保证图片内容和JSON的x/y永远绑定！
                import uuid as _uuid
                import os as _os
                # 第一阶段：先把所有 "有image条目对应的磁盘文件" 改成临时名（避免重名冲突）
                _tmp_rename_map = []  # [(旧磁盘路径, 临时磁盘路径, 最终应该叫的新名)]
                _used_tmp = set()
                _img_counter = 0
                for _i, _d in enumerate(recording_data):
                    if 'image' in _d and _d.get('image'):
                        _img_counter += 1
                        _old_name = _d['image']
                        _oldp = _os.path.join(folder_path, _old_name)
                        _final_name = f"操作{_img_counter}.png"
                        if _os.path.exists(_oldp) and _old_name != _final_name:
                            while True:
                                _tmp_name = f"_fix_tmp_{_uuid.uuid4().hex[:10]}_{_old_name}"
                                _tmpp = _os.path.join(folder_path, _tmp_name)
                                if not _os.path.exists(_tmpp) and _tmp_name not in _used_tmp:
                                    _used_tmp.add(_tmp_name)
                                    break
                            try:
                                _os.rename(_oldp, _tmpp)
                                _tmp_rename_map.append((_oldp, _tmpp, _final_name))
                            except Exception:
                                pass
                # 第二阶段：所有临时文件 → 改成最终的新编号名
                for _oldp, _tmpp, _final_name in _tmp_rename_map:
                    try:
                        if _os.path.exists(_tmpp):
                            _finalp = _os.path.join(folder_path, _final_name)
                            if _os.path.exists(_finalp):
                                try: _os.replace(_tmpp, _finalp)
                                except Exception: _os.rename(_tmpp, _finalp)
                            else:
                                _os.rename(_tmpp, _finalp)
                    except Exception:
                        pass
                # 修复JSON：按"image条目出现顺序"重新对齐 image 字段 + step也严格1..N
                _img_counter = 0
                for _i, _d in enumerate(recording_data):
                    _d['step'] = _i + 1
                    if 'image' in _d and _d.get('image'):
                        _img_counter += 1
                        if _img_counter <= _disk_count:
                            _d['image'] = f"操作{_img_counter}.png"
                        else:
                            # 异常：image条目比磁盘图片多 → 清掉变成纯坐标步骤
                            _d.pop('image', None)
                # 保存修复后的数据
                save_json_data(recording_json_path, recording_data)
        except Exception:
            pass

        # 操作类型标签配置
        _at_cfg = {
            'left_click':    ('👆 Click',     '#34C759', 'rgba(52,199,89,0.15)'),
            'right_click':   ('👉 右击',      '#34C759', 'rgba(52,199,89,0.15)'),
            'double_click':  ('👆👆 双击',    '#34C759', 'rgba(52,199,89,0.15)'),
            'middle_click':  ('🖱️ 中击',     '#34C759', 'rgba(52,199,89,0.15)'),
            'text_input':    ('📝 文本',      '#FF9500', 'rgba(255,149,0,0.15)'),
            'keyboard':      ('⌨️ 按键',      '#0A84FF', 'rgba(10,132,255,0.15)'),
            'keyboard_direct': ('⌨️ 按键',    '#0A84FF', 'rgba(10,132,255,0.15)'),
            'scroll':        ('🔄 滚动',      '#6E6E73', 'rgba(142,142,147,0.2)'),
            'condition':     ('🔀 条件分支',   '#AF52DE', 'rgba(175,82,222,0.15)'),
        }
        _menu_items = [
            ("👆 Click", "left_click"), ("👉 右击", "right_click"),
            ("👆👆 双击", "double_click"), ("🖱️ 中击", "middle_click"),
            ("📝 文本", "text_input"), ("⌨️ 按键", "keyboard"),
            ("🔄 滚动", "scroll")
        ]

        control_height = 24
        action_font_size = 11

        def _refresh_image_map():
            """重新从磁盘获取最新的图片文件映射（每次重命名/删除/交换后必须调用）"""
            _image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
            _map = {}
            for _f in _image_files:
                _m = re.search(r'操作(\d+)', _f)
                if _m:
                    _map[int(_m.group(1))] = _f
            return _map

        def _rebuild_all():
            """清空并重建所有行"""
            while list_layout.count():
                item = list_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            _build_rows()

        def _build_rows():
            """根据 recording_data 构建所有行"""
            image_map = _refresh_image_map()
            for i, record in enumerate(recording_data):
                step_num = record.get('step', i + 1)
                action_type = record.get('action_type', 'left_click')
                # ★★★ 核心修复：直接用 JSON 里的 image 字段，不再用 step_num 查 image_map
                # 有非图片步骤（按键/坐标/文本）时，step编号 ≠ 图片文件名编号，误判为无图显示绿点
                img_file = record.get('image')
                if img_file and not os.path.exists(os.path.join(folder_path, img_file)):
                    img_file = None

                # ── 每行 = macOS 卡片风格 ──
                row_widget = QWidget()
                row_widget.setFixedHeight(48)
                row_widget.setMaximumHeight(48)
                row_widget.setContentsMargins(0, 0, 0, 0)
                row_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                row_widget.setStyleSheet("""
                    QWidget#listRow {
                        background: rgba(245, 245, 247, 0.8);
                        border-radius: 0px;
                        border: none;
                        height: 48px;
                        max-height: 48px;
                        min-height: 48px;
                    }
                """)
                row_widget.setObjectName("listRow")
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(8, 0, 8, 0)
                row_layout.setSpacing(6)

                # ── ① 编号徽章 ──
                step_label = QLabel(str(step_num))
                step_label.setFixedSize(26, 26)
                step_label.setAlignment(Qt.AlignCenter)
                step_label.setStyleSheet("""
                    QLabel {
                        background-color: transparent;
                        color: #0A84FF;
                        border-radius: 13px;
                        font-size: 11px;
                        font-weight: 700;
                        font-family: 'Helvetica Neue', 'PingFang SC', sans-serif;
                    }
                """)
                row_layout.addWidget(step_label, 0, Qt.AlignTop)

                # ── ② 缩略图 / 操作类型图标 ──
                if img_file:
                    # 有图片 → 显示缩略图
                    img_path = os.path.join(folder_path, img_file)
                    thumb_w = QPushButton()
                    thumb_w.setFixedSize(48, 48)
                    thumb_w.setStyleSheet("QPushButton { background: rgba(195,240,202,0.3); border-radius: 8px; }")
                    del_btn = _create_hover_close_button(
                        thumb_w,
                        on_click=lambda checked=False, idx=i, fn=img_file: _delete_step(idx, fn),
                        size=20
                    )
                    del_btn.move(26, 0)
                    pixmap = load_qpixmap(img_path)
                    if pixmap:
                        tl = QLabel(thumb_w)
                        tp = pixmap.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        from PyQt5.QtGui import QPixmap as _QPx, QPainter as _QPa, QPainterPath as _QPP
                        _rp = _QPx(44, 44)
                        _rp.fill(Qt.transparent)
                        _pp = _QPa(_rp)
                        _pp.setRenderHint(_QPa.Antialiasing)
                        _path = _QPP()
                        _path.addRoundedRect(0, 0, 44, 44, 8, 8)
                        _pp.setClipPath(_path)
                        _pp.drawPixmap(0, 0, tp)
                        _pp.end()
                        tl.setPixmap(_rp)
                        tl.setGeometry(2, 2, 44, 44)
                        tl.setStyleSheet("QLabel { background: transparent; border: none; }")
                        tl.lower()
                    del_btn.raise_()
                    thumb_w.clicked.connect(lambda checked, fp=img_path: _show_large_preview(fp))
                    row_layout.addWidget(thumb_w, 0, Qt.AlignTop)
                else:
                    # 无图片 → 显示操作类型小色块，带上删除按钮
                    _dot_color = _at_cfg.get(action_type, ('', '#8E8E93', ''))[1]
                    _iw = QPushButton()
                    _iw.setFixedSize(48, 48)
                    _iw.setStyleSheet(f"QPushButton{{background:{_at_cfg.get(action_type, ('','#8E8E93',''))[2]};border-radius:8px;border:none;}}")
                    del_btn = _create_hover_close_button(
                        _iw,
                        on_click=lambda checked=False, idx=i: _delete_step(idx, None),
                        size=20
                    )
                    del_btn.move(26, 0)
                    icon_w = QLabel(_iw)
                    icon_w.setFixedSize(12, 12)
                    icon_w.setAlignment(Qt.AlignCenter)
                    icon_w.setStyleSheet(f"QLabel{{background:{_dot_color};border-radius:6px;border:none;}}")
                    icon_w.move(18, 18)
                    icon_w.lower()
                    del_btn.raise_()
                    row_layout.addWidget(_iw, 0, Qt.AlignTop)

                # ── ③ 操作类型按钮（带下拉菜单） ──
                _cfg = _at_cfg.get(action_type, (action_type, '#8E8E93', 'rgba(142,142,147,0.2)'))
                # 按键和文本类型显示具体内容
                if action_type in ('keyboard', 'keyboard_direct'):
                    _k = record.get('key', '')
                    _btn_label = f"⌨ {_k}" if _k else "⌨ 按键"
                elif action_type == 'text_input':
                    _txt = record.get('text', '')
                    _disp = _txt[:6] + "…" if len(_txt) > 6 else (_txt if _txt else "📝 文本")
                    _btn_label = _disp
                else:
                    _btn_label = _cfg[0]
                type_btn = QPushButton(_btn_label)
                type_btn.setFixedSize(90, control_height)
                type_btn.setCursor(Qt.PointingHandCursor)
                type_btn.setStyleSheet(f"QPushButton{{background:{_cfg[2]};color:{_cfg[1]};border:none;border-radius:12px;font-weight:600;font-size:10px;padding:0;text-align:center;}}QPushButton:hover{{background:rgba(200,200,210,0.4);}}QPushButton::menu-indicator{{width:0;}}")
                _m = QMenu()
                for _lbl, _val in _menu_items:
                    _a = _m.addAction(_lbl)
                    _a.triggered.connect(lambda checked, v=_val, idx=i: (
                        _update_step_type(idx, v)
                    ))
                type_btn.setMenu(_m)
                _tw = QWidget()
                _tw.setFixedWidth(90)
                _tl = QHBoxLayout(_tw)
                _tl.setContentsMargins(0, 0, 0, 0)
                _tl.addWidget(type_btn, 0, Qt.AlignCenter)
                row_layout.addWidget(_tw, 0, Qt.AlignTop)

                # ── ④ 参数显示（点击可编辑） ──
                _pw = QWidget()
                _pw.setFixedWidth(90)
                _pl = QHBoxLayout(_pw)
                _pl.setContentsMargins(0, 0, 0, 0)
                _pl.setAlignment(Qt.AlignCenter)
                if action_type == 'text_input':
                    _txt = record.get('text', '')
                    _disp = _txt[:10] + "..." if len(_txt) > 10 else (_txt if _txt else "(空)")
                    _lb = QLabel(f"📝 {_disp}")
                    _lb.setStyleSheet("QLabel{color:#FF9500;font-size:10px;padding:2px 4px;background:rgba(255,149,0,0.1);border-radius:6px;}")
                    _lb.setCursor(Qt.PointingHandCursor)
                    _lb.mousePressEvent = lambda e, idx=i: _show_text_dialog(idx)
                    _pl.addWidget(_lb, 0, Qt.AlignCenter)
                elif action_type in ('keyboard', 'keyboard_direct'):
                    _k = record.get('key', '')
                    _lb = QLabel(f"⌨ {_k}" if _k else "(空)")
                    _lb.setStyleSheet("QLabel{color:#0A84FF;font-size:10px;padding:2px 4px;background:rgba(10,132,255,0.1);border-radius:6px;}")
                    _lb.setCursor(Qt.PointingHandCursor)
                    _lb.mousePressEvent = lambda e, idx=i: _show_key_dialog(idx)
                    _pl.addWidget(_lb, 0, Qt.AlignCenter)
                elif action_type == 'scroll':
                    _amt = record.get('scroll_amount', 3)
                    # ★★★ 修复：防御 0 值，避免显示"下滑0"
                    if _amt == 0:
                        _amt = 3
                    _dir = "上" if _amt > 0 else "下"
                    _lb = QLabel(f"{_dir}{abs(_amt)}")
                    _lb.setStyleSheet("QLabel{color:#6E6E73;font-size:10px;padding:2px 4px;background:rgba(142,142,147,0.15);border-radius:6px;}")
                    _lb.setCursor(Qt.PointingHandCursor)
                    _lb.mousePressEvent = lambda e, idx=i: _show_scroll_dialog(idx)
                    _pl.addWidget(_lb, 0, Qt.AlignCenter)
                elif action_type == 'condition':
                    _lb = QLabel("条件分支")
                    _lb.setStyleSheet("QLabel{color:#AF52DE;font-size:10px;padding:2px 4px;background:rgba(175,82,222,0.1);border-radius:6px;}")
                    _pl.addWidget(_lb, 0, Qt.AlignCenter)
                else:
                    _px = record.get('x', 0); _py = record.get('y', 0)
                    _lb = QLabel(f"({_px},{_py})")
                    _lb.setStyleSheet("QLabel{color:#8E8E93;font-size:10px;}")
                    _pl.addWidget(_lb, 0, Qt.AlignCenter)
                row_layout.addWidget(_pw, 0, Qt.AlignTop)

                # ── ⑤ 延迟 ⏱ ──
                delay_w = QWidget()
                delay_w.setFixedWidth(72)
                dl = QHBoxLayout(delay_w)
                dl.setContentsMargins(0, 0, 0, 0)
                dl.setSpacing(2)
                dl2 = QLabel("⏱")
                dl2.setStyleSheet("QLabel { color: #999; font-size: 12px; }")
                dl.addWidget(dl2)
                ds = QDoubleSpinBox()
                ds.setSingleStep(0.1); ds.setDecimals(1)
                ds.setValue(record.get('delay', 0.1))
                ds.valueChanged.connect(lambda v, idx=i: _update_delay(idx, v))
                ds.setFixedSize(40, control_height)
                ds.setStyleSheet("QDoubleSpinBox { background: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 8px; font-size: 11px; color: black; padding: 0; } QDoubleSpinBox:focus { border-color: #0A84FF; }")
                dl.addWidget(ds)
                du = QLabel("s")
                du.setStyleSheet("QLabel { color: #999; font-size: 10px; }")
                dl.addWidget(du)
                row_layout.addWidget(delay_w, 0, Qt.AlignTop)

                # ── ⑥ 排序按钮 ──
                move_w = QWidget()
                move_w.setFixedWidth(52)
                ml = QHBoxLayout(move_w)
                ml.setContentsMargins(0, 0, 0, 0)
                ml.setSpacing(2)
                btn_up = QPushButton("▲")
                btn_up.setFixedSize(24, 24)
                btn_up.setStyleSheet("QPushButton{background:rgba(142,142,147,0.12);color:#6E6E73;border:none;border-radius:4px;font-size:12px;font-weight:bold;}QPushButton:hover{background:rgba(10,132,255,0.15);color:#0A84FF;}")
                btn_up.setEnabled(i > 0)
                btn_down = QPushButton("▼")
                btn_down.setFixedSize(24, 24)
                btn_down.setStyleSheet("QPushButton{background:rgba(142,142,147,0.12);color:#6E6E73;border:none;border-radius:4px;font-size:12px;font-weight:bold;}QPushButton:hover{background:rgba(10,132,255,0.15);color:#0A84FF;}")
                btn_down.setEnabled(i < len(recording_data) - 1)
                ml.addWidget(btn_up, 0, Qt.AlignTop)
                ml.addWidget(btn_down, 0, Qt.AlignTop)
                row_layout.addWidget(move_w, 0, Qt.AlignTop)

                btn_up.clicked.connect(lambda checked, idx=i: _swap_rows(idx, idx - 1))
                btn_down.clicked.connect(lambda checked, idx=i: _swap_rows(idx, idx + 1))

                # ── ⑦ 拖拽排序 ──
                row_widget._idx = i
                row_widget._drag_start_pos = None  # ★★★ 修复：提前初始化，避免 AttributeError
                def _bd(w):
                    def _mpe(s, e):
                        if e.button() == 1: s._drag_start_pos = e.pos()
                        QWidget.mousePressEvent(s, e)
                    if not hasattr(w, '_drag_start_pos'):
                        w._drag_start_pos = None
                    w.mousePressEvent = _mpe.__get__(w, QWidget)
                    def _mme(s, e):
                        if not (e.buttons() & 1): return
                        # ★★★ 修复：用 hasattr + getattr 双保险，避免 _drag_start_pos 不存在导致崩溃
                        _dsp = getattr(s, '_drag_start_pos', None)
                        if _dsp is None: return
                        if (e.pos() - _dsp).manhattanLength() < QApplication.startDragDistance(): return
                        d = QDrag(s)
                        m = QMimeData()
                        m.setText(f"{s._idx},{folder_path}")
                        d.setMimeData(m)
                        d.setPixmap(s.grab().scaled(300, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        d.setHotSpot(QPoint(30, 36))
                        d.exec_(2)
                    w.mouseMoveEvent = _mme.__get__(w, QWidget)
                _bd(row_widget)

                list_layout.addWidget(row_widget, 0, Qt.AlignTop)

        # 内部辅助函数
        def _update_step_type(idx, new_type):
            """更新步骤的操作类型"""
            if idx < len(recording_data):
                old_type = recording_data[idx].get('action_type', 'left_click')
                recording_data[idx]['action_type'] = new_type
                if new_type in ('left_click', 'right_click', 'double_click', 'middle_click'):
                    recording_data[idx].pop('text', None)
                    recording_data[idx].pop('key', None)
                    recording_data[idx].pop('scroll_amount', None)
                    if 'x' not in recording_data[idx] or 'y' not in recording_data[idx]:
                        recording_data[idx]['x'] = 0
                        recording_data[idx]['y'] = 0
                elif new_type == 'text_input':
                    if 'text' not in recording_data[idx] or not recording_data[idx]['text']:
                        recording_data[idx]['text'] = ''
                    recording_data[idx].pop('scroll_amount', None)
                elif new_type == 'keyboard':
                    if 'key' not in recording_data[idx] or not recording_data[idx]['key']:
                        recording_data[idx]['key'] = ''
                    recording_data[idx].pop('text', None)
                    recording_data[idx].pop('scroll_amount', None)
                elif new_type == 'scroll':
                    if 'scroll_amount' not in recording_data[idx]:
                        recording_data[idx]['scroll_amount'] = 3
                    recording_data[idx].pop('text', None)
                    recording_data[idx].pop('key', None)
                save_json_data(recording_json_path, recording_data)
                _rebuild_all()

        def _update_delay(idx, value):
            if idx < len(recording_data):
                recording_data[idx]['delay'] = value
                save_json_data(recording_json_path, recording_data)

        def _show_text_dialog(idx):
            """显示文本编辑对话框"""
            self._show_text_input_dialog_coord(idx, folder_path, recording_data, recording_json_path, _rebuild_all)

        def _show_key_dialog(idx):
            """显示按键编辑对话框"""
            self._show_key_input_dialog_coord(idx, folder_path, recording_data, recording_json_path, _rebuild_all)

        def _show_scroll_dialog(idx):
            """显示滚动编辑对话框"""
            self._show_scroll_input_dialog_coord(idx, folder_path, recording_data, recording_json_path, _rebuild_all)

        def _swap_rows(idx_a, idx_b):
            """交换两行顺序（同步重命名图片文件）"""
            if 0 <= idx_a < len(recording_data) and 0 <= idx_b < len(recording_data):
                # 交换前先刷新图片映射，确保使用最新的磁盘文件状态
                image_map = _refresh_image_map()
                # 交换图片文件名（保持步骤号与文件名一致）
                step_a = recording_data[idx_a].get('step', idx_a + 1)
                step_b = recording_data[idx_b].get('step', idx_b + 1)
                img_a = recording_data[idx_a].get('image')
                img_b = recording_data[idx_b].get('image')
                if img_a and not os.path.exists(os.path.join(folder_path, img_a)):
                    img_a = None
                if img_b and not os.path.exists(os.path.join(folder_path, img_b)):
                    img_b = None
                if img_a and img_b:
                    path_a = os.path.join(folder_path, img_a)
                    path_b = os.path.join(folder_path, img_b)
                    # 三步交换法：a → tmp, b → a, tmp → b
                    tmp_name = f"_swap_tmp_{img_a}"
                    tmp_path = os.path.join(folder_path, tmp_name)
                    if os.path.exists(path_a) and os.path.exists(path_b):
                        os.rename(path_a, tmp_path)
                        os.rename(path_b, path_a)
                        os.rename(tmp_path, path_b)
                # 无图片的步骤只需要交换数据
                recording_data[idx_a], recording_data[idx_b] = recording_data[idx_b], recording_data[idx_a]
                # ★ 重新编号 step + 按出现顺序重新分配 image（磁盘物理顺序已经是1..N）
                _img_counter = 0
                for _i, _o in enumerate(recording_data):
                    _o['step'] = _i + 1
                    if 'image' in _o and _o['image']:
                        _img_counter += 1
                        _o['image'] = f"操作{_img_counter}.png"
                # ★ 同步重命名磁盘图片文件为 操作1,2,3... 顺序
                # 先收集磁盘上的图片，按编号排序，再两步法重命名避免冲突
                _disk_imgs = [f for f in os.listdir(folder_path) if f.lower().endswith('.png') and re.search(r'操作(\d+)\.png', f)]
                def _dnum(f):
                    mm = re.search(r'操作(\d+)\.png', f)
                    return int(mm.group(1)) if mm else 999999
                _disk_imgs_sorted = sorted(_disk_imgs, key=_dnum)
                import uuid as _uuid
                _tmps = {}
                for _ni, _oldf in enumerate(_disk_imgs_sorted):
                    _newname = f"操作{_ni + 1}.png"
                    if _oldf == _newname:
                        continue
                    _oldp = os.path.join(folder_path, _oldf)
                    _tmpp = os.path.join(folder_path, f"_sw_tmp_{_uuid.uuid4().hex[:8]}_{_oldf}")
                    if os.path.exists(_oldp):
                        try:
                            os.rename(_oldp, _tmpp)
                            _tmps[_oldf] = (_tmpp, _newname)
                        except Exception:
                            pass
                for _oldf, (_tmpp, _newname) in _tmps.items():
                    _newp = os.path.join(folder_path, _newname)
                    try:
                        if os.path.exists(_tmpp):
                            if os.path.exists(_newp):
                                try: os.replace(_tmpp, _newp)
                                except Exception: os.rename(_tmpp, _newp)
                            else:
                                os.rename(_tmpp, _newp)
                    except Exception:
                        pass
                save_json_data(recording_json_path, recording_data)
                _rebuild_all()

        def _delete_step(idx, img_file=None):
            """删除指定步骤"""
            if idx < 0 or idx >= len(recording_data):
                return
            confirm_dialog = QDialog(dialog)
            confirm_dialog.setWindowTitle("确认删除")
            confirm_dialog.setFixedSize(300, 120)
            _layout = QVBoxLayout(confirm_dialog)
            _layout.setSpacing(10)
            _layout.setContentsMargins(15, 15, 15, 15)
            _label = QLabel(f"确定要删除步骤 {recording_data[idx].get('step', idx+1)} 吗？")
            _layout.addWidget(_label)
            _btn_layout = QHBoxLayout()
            _ok_btn = QPushButton("确定")
            _ok_btn.setMinimumSize(60, 28)
            _ok_btn.setStyleSheet("QPushButton{background-color:#0A84FF;color:white;border-radius:4px;font-size:14px;}")
            _ok_btn.clicked.connect(confirm_dialog.accept)
            _btn_layout.addWidget(_ok_btn)
            _cancel_btn = QPushButton("取消")
            _cancel_btn.setMinimumSize(60, 28)
            _cancel_btn.setStyleSheet("QPushButton{background-color:#8E8E93;color:white;border-radius:4px;font-size:14px;}")
            _cancel_btn.clicked.connect(confirm_dialog.reject)
            _btn_layout.addWidget(_cancel_btn)
            _layout.addLayout(_btn_layout)
            if confirm_dialog.exec_() != QDialog.Accepted:
                return

            # 删除图片文件
            if img_file:
                img_path = os.path.join(folder_path, img_file)
                if os.path.exists(img_path):
                    try: os.remove(img_path)
                    except: pass
            # 从 recording_data 中移除
            recording_data.pop(idx)
            # 重排序号 + ★ 同步更新每个步骤的 image 字段
            # ★★ 关键修复：不能用全局索引 _i 分配图片号！要用"有image的条目出现的顺序"计数
            #    否则纯坐标步骤（无image）会占一个编号，导致图片步骤和磁盘上的物理文件错开！
            _img_counter = 0
            for _i, _o in enumerate(recording_data):
                _o['step'] = _i + 1
                if 'image' in _o and _o['image']:
                    _img_counter += 1
                    _o['image'] = f"操作{_img_counter}.png"
            # ★ 重命名磁盘上的所有图片，严格匹配 recording_data 的 image 字段
            #  不再依赖 deleted_step 推导，避免键盘步骤占位错位；并且清理历史残留 tmp 文件防 183 错
            # 0) 先清理残留的 _tmp 临时文件（上次崩溃遗留的）
            for _leftover in os.listdir(folder_path):
                if _leftover.lower().endswith('.png') and ('_tmp' in _leftover or '_r_tmp' in _leftover or _leftover.startswith('_tmp_')):
                    try: os.remove(os.path.join(folder_path, _leftover))
                    except: pass
            # 1) 收集磁盘上的操作*.png，按编号排序；操作1.png,操作2.png,操作3.png...
            disk_imgs = [f for f in os.listdir(folder_path) if f.lower().endswith('.png') and re.search(r'操作(\d+)\.png', f)]
            def _num(f):
                m = re.search(r'操作(\d+)\.png', f)
                return int(m.group(1)) if m else 999999
            disk_imgs_sorted = sorted(disk_imgs, key=_num)
            # 2) 按新编号给图片改名：操作1.png保留，操作3.png→操作2.png，...统一对齐1,2,3...
            #    用uuid保证tmp名唯一，永远不会 FileExistsError(183)
            tmp_map = {}  # {旧文件名: (临时文件路径, 新文件名)}
            import uuid as _uuid
            for new_idx, old_f in enumerate(disk_imgs_sorted):
                new_name = f"操作{new_idx + 1}.png"
                old_p = os.path.join(folder_path, old_f)
                if old_f == new_name:
                    continue  # 名字一致跳过
                tmp_name = f"_del_tmp_{_uuid.uuid4().hex[:10]}_{old_f}"
                tmp_p = os.path.join(folder_path, tmp_name)
                if os.path.exists(old_p):
                    try:
                        os.rename(old_p, tmp_p)
                        tmp_map[old_f] = (tmp_p, new_name)
                    except Exception as _e:
                        print(f"[warn] 重命名图片失败(第一步) {old_f}: {_e}")
            # 3) 全部 tmp -> 最终名
            for old_f, (tmp_p, new_name) in tmp_map.items():
                new_p = os.path.join(folder_path, new_name)
                try:
                    if os.path.exists(tmp_p):
                        if os.path.exists(new_p):
                            # 极端情况下新文件已存在：用 os.replace(Windows上安全覆盖)
                            try: os.replace(tmp_p, new_p)
                            except Exception: os.rename(tmp_p, new_p)
                        else:
                            os.rename(tmp_p, new_p)
                except Exception as _e:
                    print(f"[warn] 重命名图片失败(第二步) {old_f}->{new_name}: {_e}")
            save_json_data(recording_json_path, recording_data)
            _rebuild_all()

        def _show_large_preview(img_path):
            """弹出大图预览"""
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QScrollArea
            from PyQt5.QtWidgets import QDesktopWidget
            preview = QDialog(dialog)
            preview.setWindowTitle("图片预览")
            preview.setWindowFlags(preview.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            desktop = QDesktopWidget()
            sw = desktop.screenGeometry().width()
            sh = desktop.screenGeometry().height()
            max_w = int(sw * 0.7)
            max_h = int(sh * 0.7)
            preview.resize(max_w, max_h)
            _layout = QVBoxLayout(preview)
            _layout.setContentsMargins(0, 0, 0, 0)
            scroll = QScrollArea(preview)
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: #1C1C1E; }")
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            fp = load_qpixmap(img_path)
            if fp:
                fp = fp.scaled(max_w - 20, max_h - 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(fp)
            img_label.setStyleSheet("background: #1C1C1E; padding: 10px;")
            scroll.setWidget(img_label)
            _layout.addWidget(scroll)
            preview.exec_()

        # 构建所有行
        _build_rows()

        # 列表级放置处理（拖拽排序）
        list_layout.activate()
        list_layout.parentWidget().adjustSize()
        _lw = list_layout.parentWidget()
        _lw.setAcceptDrops(True)
        def _l_dee(s, e):
            if e.mimeData().hasText(): e.acceptProposedAction()
        _lw.dragEnterEvent = _l_dee.__get__(_lw, QWidget)
        def _l_dme(s, e):
            if e.mimeData().hasText(): e.acceptProposedAction()
        _lw.dragMoveEvent = _l_dme.__get__(_lw, QWidget)
        def _l_de(s, e):
            if e.mimeData().hasText():
                try:
                    a, _ = e.mimeData().text().split(",")
                    a = int(a)
                    dy = e.pos().y()
                    for ri in range(list_layout.count()):
                        rw = list_layout.itemAt(ri).widget()
                        if rw and rw.y() <= dy <= rw.y() + rw.height() and ri != a:
                            _swap_rows(a, ri)
                            break
                    e.acceptProposedAction()
                except:
                    pass
        _lw.dropEvent = _l_de.__get__(_lw, QWidget)

    def refresh_view_images(self, folder_path):
        if not hasattr(self.parent, '_view_images_dialog') or not self.parent._view_images_dialog:
            return
        if not hasattr(self.parent, '_view_images_grid_layout'):
            return
        dialog = self.parent._view_images_dialog
        list_layout = self.parent._view_images_grid_layout
        while list_layout.count():
            item = list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._populate_unified_rows(dialog, folder_path, list_layout)
    def add_more_operations(self, parent_dialog, folder_path):
        """继续添加新的操作到现有文件夹"""
        # print("===== add_more_operations 被调用 =====")  # [日志已禁用]
        # print(f"parent_dialog: {parent_dialog}")  # [日志已禁用]
        # print(f"parent_dialog.isVisible(): {parent_dialog.isVisible() if parent_dialog else 'N/A'}")  # [日志已禁用]
        # print(f"folder_path: {folder_path}")  # [日志已禁用]
        
        try:
            # print("开始继续添加操作流程...")  # [日志已禁用]
            
            # 设置录制状态，与toggle_recording方法保持一致
            if not hasattr(self.parent, 'is_recording'):
                self.parent.is_recording = False
                
            self.parent.is_recording = True
            # 禁用所有可能的停止录制按钮
            self.parent.record_btn.setEnabled(False)
            self.parent.record_btn.setText('录\n制\n中')
            # 同时禁用管理文件按钮
            if hasattr(self.parent, 'manage_recordings_btn'):
                self.parent.manage_recordings_btn.setEnabled(False)
            # 禁用托盘菜单中的录制动作
            if hasattr(self.parent, 'record_action'):
                self.parent.record_action.setEnabled(False)
                self.parent.record_action.setText('🔴 录制中...')
            
            # print("已设置录制状态")  # [日志已禁用]
            
            # 隐藏所有窗口，确保截图时不包含程序窗口
            # print("隐藏所有程序窗口...")  # [日志已禁用]
            # 隐藏查看图片对话框
            if parent_dialog and parent_dialog.isVisible():
                parent_dialog.hide()
                # print("已隐藏查看图片对话框")  # [日志已禁用]
            # 隐藏 FolderManager 窗口
            if self.isVisible():
                self.hide()
                # print("已隐藏 FolderManager 窗口")  # [日志已禁用]
            # 最小化主窗口
            if self.parent and self.parent.isVisible():
                self.parent.showMinimized()
                # print("已最小化主窗口")  # [日志已禁用]
            
            # 等待窗口完全隐藏
            from PyQt5.QtCore import QThread
            QThread.msleep(200)  # 等待200ms确保窗口完全隐藏
            
            # 启动区域选择
            screen = QGuiApplication.primaryScreen()
            screen_pixmap = screen.grabWindow(0)
            # print("已获取屏幕截图")  # [日志已禁用]
            
            # 设置当前录制目录为传入的文件夹路径
            self.parent.current_recording_dir = folder_path
            # print(f"设置录制目录: {folder_path}")  # [日志已禁用]
            
            # 读取recording.json文件，获取当前最大的step编号
            import json
            max_step = 0
            recording_json_path = os.path.join(folder_path, 'recording.json')
            if os.path.exists(recording_json_path):
                try:
                    with open(recording_json_path, 'r', encoding='utf-8') as f:
                        operations = json.load(f)
                        if operations and isinstance(operations, list):
                            # 找出最大的step编号
                            max_step = max(op.get('step', 0) for op in operations)
                            # print(f"找到现有操作，最大step编号: {max_step}")  # [日志已禁用]
                except Exception as e:
                    # print(f"读取recording.json失败: {e}")  # [日志已禁用]
                    max_step = 0
            
            # 创建选择覆盖层，传入现有文件夹路径和初始操作计数
            # print("创建SelectionOverlay窗口...")  # [日志已禁用]
            from selection_overlay import SelectionOverlay
            self.parent.selection_overlay = SelectionOverlay(self.parent, screen_pixmap=screen_pixmap, recording_dir=folder_path, initial_operation_count=max_step)
            # print(f"SelectionOverlay窗口创建成功，窗口对象: {self.parent.selection_overlay}")  # [日志已禁用]
            # print(f"SelectionOverlay窗口标志: {self.parent.selection_overlay.windowFlags()}")  # [日志已禁用]
            # print(f"SelectionOverlay窗口大小: {self.parent.selection_overlay.size()}")  # [日志已禁用]
            
            # 连接关闭信号，处理录制完成
            self.parent.selection_overlay.closed.connect(self.parent.on_recording_finished)
            
            # 先显示截图窗口，确保它能正常显示
            # print("准备显示截图窗口...")  # [日志已禁用]
            self.parent.selection_overlay.show()
            # self.parent.debug_print(f"SelectionOverlay.show()调用完成，可见性: {self.parent.selection_overlay.isVisible()}")  # [日志已禁用]
            self.parent.selection_overlay.activateWindow()
            self.parent.selection_overlay.raise_()
            self.parent.selection_overlay.setFocus()
            # print("截图窗口已显示")  # [日志已禁用]
            
            # 标记热键需要移除，在对话框关闭回调中处理
            self._need_remove_grave_hotkey = True
            
            # 关闭父对话框
            # print("关闭父对话框...")  # [日志已禁用]
            parent_dialog.close()
            # print("已关闭父对话框")  # [日志已禁用]
            
        except Exception as e:
            # print(f"继续添加操作失败: {e}")  # [日志已禁用]
            import traceback
            traceback.print_exc()
            
            # 恢复状态
            try:
                self.parent.is_recording = False
                self.parent.record_btn.setEnabled(True)
                self.parent.record_btn.setText('录\n制')
                # 同时恢复管理文件按钮
                if hasattr(self.parent, 'manage_recordings_btn'):
                    self.parent.manage_recordings_btn.setEnabled(True)
                if hasattr(self.parent, 'record_action'):
                    self.parent.record_action.setEnabled(True)
                    self.parent.record_action.setText('开始录制')
                self.parent.showNormal()
            except:
                pass
            
            # 显示错误信息
            from PyQt5.QtWidgets import QMessageBox
            self.parent.show_beautiful_message('critical', "错误", f"继续添加操作失败: {str(e)}", parent=parent_dialog)
            parent_dialog.close()

    def add_more_operations_coord(self, parent_dialog, folder_path):
        """继续添加纯坐标操作（不截图，只记录鼠标点击位置）"""
        try:
            # 读取现有 recording.json 获取最大 step
            import json
            max_step = 0
            recording_json_path = os.path.join(folder_path, 'recording.json')
            if os.path.exists(recording_json_path):
                with open(recording_json_path, 'r', encoding='utf-8') as f:
                    ops = json.load(f)
                    if ops and isinstance(ops, list):
                        max_step = max(op.get('step', 0) for op in ops)

            # 隐藏父对话框
            if parent_dialog and parent_dialog.isVisible():
                parent_dialog.hide()
            if self.isVisible():
                self.hide()
            if self.parent and self.parent.isVisible():
                self.parent.showMinimized()

            from PyQt5.QtCore import QThread
            QThread.msleep(200)

            # 创建坐标录制覆盖层
            from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
            from PyQt5.QtGui import QPainter, QColor, QFont, QGuiApplication
            from PyQt5.QtCore import Qt, QRect, QTimer

            class _CoordRecorder(QWidget):
                closed = __import__('PyQt5.QtCore', fromlist=['pyqtSignal']).pyqtSignal()
                def __init__(self, parent_w, folder, base_step):
                    super().__init__()
                    self.parent_w = parent_w
                    self.folder = folder
                    self.base_step = base_step
                    self.step_counter = 0
                    self.new_records = []
                    self._focus_timer = None
                    self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
                    self.setAttribute(Qt.WA_TranslucentBackground)
                    self.setMouseTracking(True)
                    total_geo = QRect()
                    for s in __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication.screens():
                        total_geo = total_geo.united(s.geometry())
                    self.setGeometry(total_geo if total_geo.isValid() else QRect(0, 0, 1920, 1080))

                def showEvent(self, event):
                    super().showEvent(event)
                    QTimer.singleShot(100, self._delayed_show)

                def _delayed_show(self):
                    self.raise_(); self.activateWindow(); self.setFocus(Qt.ActiveWindowFocusReason)
                    __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication.processEvents()
                    self._focus_timer = QTimer()
                    self._focus_timer.timeout.connect(self._ensure_focus)
                    self._focus_timer.start(200)

                def _ensure_focus(self):
                    if not self.hasFocus():
                        self.raise_(); self.activateWindow(); self.setFocus(Qt.ActiveWindowFocusReason)

                def paintEvent(self, event):
                    p = QPainter(self)
                    p.setRenderHint(QPainter.Antialiasing)
                    p.fillRect(self.rect(), QColor(0, 0, 0, 100))
                    font = QFont("PingFang SC, SimHei", 17)
                    p.setFont(font)
                    p.setPen(QColor("#FFFFFF"))
                    if self.step_counter == 0:
                        text = "🖱️ 左键点击记录位置\n🖱️ 右键点击记录右键\n按 Esc 结束录制"
                    else:
                        text = f"✅ 已记录 {self.step_counter} 个坐标\n🖱️ 继续点击或按 Esc 结束"
                    p.drawText(self.rect(), Qt.AlignCenter, text)

                def mousePressEvent(self, event):
                    if event.button() == Qt.LeftButton:
                        self.step_counter += 1
                        global_logical = self.mapToGlobal(event.pos())
                        # 记录坐标，不截图
                        rec = {
                            "step": self.base_step + self.step_counter,
                            "action_type": "left_click",
                            "x": global_logical.x(),
                            "y": global_logical.y(),
                            "delay": 0.1
                        }
                        self.new_records.append(rec)
                        self.update()
                    elif event.button() == Qt.RightButton:
                        self.step_counter += 1
                        global_logical = self.mapToGlobal(event.pos())
                        rec = {
                            "step": self.base_step + self.step_counter,
                            "action_type": "right_click",
                            "x": global_logical.x(),
                            "y": global_logical.y(),
                            "delay": 0.1
                        }
                        self.new_records.append(rec)
                        self.update()

                def keyPressEvent(self, event):
                    if event.key() == Qt.Key_Escape:
                        self._finish()
                    super().keyPressEvent(event)

                def _finish(self):
                    if self._focus_timer:
                        self._focus_timer.stop()
                    # 保存到 recording.json
                    try:
                        import json
                        rp = os.path.join(self.folder, 'recording.json')
                        all_ops = []
                        if os.path.exists(rp):
                            with open(rp, 'r', encoding='utf-8') as f:
                                all_ops = json.load(f)
                        if not isinstance(all_ops, list):
                            all_ops = []
                        all_ops.extend(self.new_records)
                        with open(rp, 'w', encoding='utf-8') as f:
                            json.dump(all_ops, f, indent=2, ensure_ascii=False)
                    except Exception:
                        import traceback
                        traceback.print_exc()
                    self.closed.emit()
                    self.close()

            self._coord_recorder = _CoordRecorder(self, folder_path, max_step)
            self._coord_recorder.closed.connect(self._on_coord_recording_done)
            self._coord_recorder.show()
            self._coord_recorder.raise_()
            self._coord_recorder.activateWindow()
            self._coord_recorder.setFocus(Qt.ActiveWindowFocusReason)

            self._need_remove_grave_hotkey = True
            parent_dialog.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self.parent.is_recording = False
                self.parent.record_btn.setEnabled(True)
                self.parent.record_btn.setText('录\n制')
                self.parent.showNormal()
            except:
                pass
            self.parent.show_beautiful_message('critical', "错误", f"添加坐标操作失败: {str(e)}", parent=parent_dialog)
            parent_dialog.close()

    def _on_coord_recording_done(self):
        """坐标录制完成后的清理"""
        try:
            self.parent._set_recording_state(False)
            self.parent.record_btn.setEnabled(True)
            self.parent.record_btn.setText('录\n制')
            if hasattr(self.parent, 'manage_recordings_btn'):
                self.parent.manage_recordings_btn.setEnabled(True)
            if hasattr(self.parent, 'record_action'):
                self.parent.record_action.setEnabled(True)
                self.parent.record_action.setText('开始录制')
            self.parent.showNormal()
            self.parent.raise_()
            self.parent.activateWindow()
        except:
            pass
        # 刷新视图
        if hasattr(self, '_coord_recorder'):
            try:
                self._coord_recorder.deleteLater()
            except:
                pass
            self._coord_recorder = None
        self.refresh_view_images(str(self._current_view_folder_path)) if hasattr(self, '_current_view_folder_path') else None
        if hasattr(self.parent, 'folder_manager') and self.parent.folder_manager:
            try:
                self.parent.folder_manager.load_folders()
            except:
                pass

    def update_action(self, index, action, folder_path=None):
        try:
            self.image_actions[index] = action
            if folder_path is None:
                return
            recording_json_path = os.path.join(folder_path, 'recording.json')
            if os.path.exists(recording_json_path):
                recording_data = load_json_data(recording_json_path)
                if isinstance(recording_data, list):
                    action_type_map = {'Click':'left_click', '右击':'right_click', '双击':'double_click', '中键点击':'middle_click', '中击':'middle_click'}
                    # 使用 image_step_map 获取实际步骤号，避免键盘操作无图片导致的错位
                    step = self.image_step_map.get(index, index + 1)
                    for d in recording_data:
                        if d.get('step') == step:
                            if action.startswith('按键:'):
                                d['action_type'] = 'keyboard'
                                d['key'] = action.replace('按键: ', '')
                            elif action.startswith('文本:'):
                                d['action_type'] = 'text_input'
                                d['text'] = action.replace('文本: ', '')
                            elif action.startswith('滚动:'):
                                d['action_type'] = 'scroll'
                                scroll_text = action.replace('滚动: ', '')
                                direction = 1 if scroll_text.startswith('上') else -1
                                amount_str = scroll_text.lstrip('上下')
                                try:
                                    amount = int(amount_str)
                                except:
                                    amount = 3
                                d['scroll_amount'] = direction * amount
                            elif action == '条件分支':
                                d['action_type'] = 'condition'
                            else:
                                d['action_type'] = action_type_map.get(action, 'left_click')
                            break
                    save_json_data(recording_json_path, recording_data)
        except Exception as e:
            # print(f"更新操作类型失败: {e}")  # [日志已禁用]
            pass
    
    def _build_coord_table_panel(self, parent_window, folder_path, recording_json_path):
        """
        构建坐标数据表格面板（可嵌入任意对话框）
        返回: QWidget 包含表格和操作按钮，或 None（数据为空时）
        """
        recording_data = load_json_data(recording_json_path)
        if not isinstance(recording_data, list) or not recording_data:
            return None

        container = QWidget()
        container.setStyleSheet("QWidget{background:transparent;}")
        _cl = QVBoxLayout(container)
        _cl.setContentsMargins(0, 0, 0, 0)
        _cl.setSpacing(6)

        # 标题栏（macOS 风格分段标题）
        _header = QFrame()
        _header.setStyleSheet("QFrame{background:rgba(245,245,247,0.9);border-radius:8px;}")
        _hl = QHBoxLayout(_header)
        _hl.setContentsMargins(12, 6, 12, 6)
        _title = QLabel("📋 操作步骤详情")
        _title.setStyleSheet("font-size:13px; font-weight:600; color:#1C1C1E; background:transparent; border:none;")
        _hl.addWidget(_title)
        _hl.addStretch()
        _count = QLabel(f"{len(recording_data)} 步")
        _count.setStyleSheet("font-size:11px; color:#86868B; background:transparent; border:none;")
        _hl.addWidget(_count)
        _cl.addWidget(_header)

        # 创建表格
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["步骤", "操作类型", "参数", "操作"])
        table.setRowCount(len(recording_data))

        table.setStyleSheet(
            "QTableWidget{background:#FFFFFF;border:1px solid #E5E5EA;border-radius:8px;gridline-color:transparent;outline:none;}"
            "QTableWidget::item{padding:4px 6px;border:none;color:#1D1D1F;}"
            "QTableWidget::item:hover{background:#F0F0F2;}"
            "QTableWidget::item:selected{background:#E8F0FE;color:#1D1D1F;}"
            "QHeaderView{border:none;}"
            "QHeaderView::section{background:#F5F5F7;color:#86868B;padding:6px 10px;border-bottom:1px solid #E5E5EA;border-right:none;font-weight:600;font-size:12px;}"
            "QTableCornerButton::section{background:#F5F5F7;border:none;}"
        )
        table.verticalHeader().setDefaultSectionSize(60)
        table.horizontalHeader().setStretchLastSection(False)

        # 操作类型显示配置
        _at_cfg = {
            'left_click':    ('👆 Click',     '#34C759', 'rgba(52,199,89,0.15)'),
            'right_click':   ('👉 右击',      '#34C759', 'rgba(52,199,89,0.15)'),
            'double_click':  ('👆👆 双击',    '#34C759', 'rgba(52,199,89,0.15)'),
            'middle_click':  ('🖱️ 中击',     '#34C759', 'rgba(52,199,89,0.15)'),
            'text_input':    ('📝 文本',      '#FF9500', 'rgba(255,149,0,0.15)'),
            'keyboard':      ('⌨️ 按键',      '#0A84FF', 'rgba(10,132,255,0.15)'),
            'keyboard_direct': ('⌨️ 按键',    '#0A84FF', 'rgba(10,132,255,0.15)'),
            'scroll':        ('🔄 滚动',      '#6E6E73', 'rgba(142,142,147,0.2)'),
            'condition':     ('🔀 条件分支',   '#AF52DE', 'rgba(175,82,222,0.15)'),
        }
        _menu_items = [
            ("👆 Click", "left_click"), ("👉 右击", "right_click"),
            ("👆👆 双击", "double_click"), ("🖱️ 中击", "middle_click"),
            ("📝 文本", "text_input"), ("⌨️ 按键", "keyboard"),
            ("🔄 滚动", "scroll")
        ]

        def _make_type_btn(row_idx, current_type):
            _cfg = _at_cfg.get(current_type, (current_type, '#8E8E93', 'rgba(142,142,147,0.2)'))
            _btn = QPushButton(_cfg[0])
            _btn.setFixedHeight(28)
            _btn.setCursor(Qt.PointingHandCursor)
            _btn.setStyleSheet(f"QPushButton{{background:{_cfg[2]};color:{_cfg[1]};border:none;border-radius:12px;font-weight:600;font-size:10px;padding:0 8px;}}QPushButton:hover{{background:rgba(200,200,210,0.4);}}QPushButton::menu-indicator{{width:0;}}")
            _m = QMenu()
            for _lbl, _val in _menu_items:
                _a = _m.addAction(_lbl)
                _a.triggered.connect(lambda checked, v=_val, idx=row_idx: (
                    self._update_coord_action_type(recording_data, recording_json_path, idx, v, _refresh_table)
                ))
            _btn.setMenu(_m)
            return _btn

        def _make_param_widget(row_idx, record):
            _at = record.get('action_type', 'left_click')
            _w = QWidget()
            _w.setStyleSheet("QWidget{background:transparent;}")
            _l = QHBoxLayout(_w)
            _l.setContentsMargins(4,0,4,0)
            _l.setAlignment(Qt.AlignCenter)
            if _at == 'text_input':
                _txt = record.get('text', '')
                _disp = _txt[:15] + "..." if len(_txt) > 15 else _txt
                _lb = QLabel(_disp if _disp else "(空)")
                _lb.setStyleSheet("QLabel{color:#FF9500;font-size:11px;padding:2px 6px;background:rgba(255,149,0,0.1);border-radius:6px;}")
                _lb.setCursor(Qt.PointingHandCursor)
                _lb.mousePressEvent = lambda e, idx=row_idx: self._show_text_input_dialog_coord(idx, folder_path, recording_data, recording_json_path, _refresh_table)
                _l.addWidget(_lb, 0, Qt.AlignCenter)
            elif _at in ('keyboard', 'keyboard_direct'):
                _k = record.get('key', '')
                _lb = QLabel(f"⌨ {_k}" if _k else "(空)")
                _lb.setStyleSheet("QLabel{color:#0A84FF;font-size:11px;padding:2px 6px;background:rgba(10,132,255,0.1);border-radius:6px;}")
                _lb.setCursor(Qt.PointingHandCursor)
                _lb.mousePressEvent = lambda e, idx=row_idx: self._show_key_input_dialog_coord(idx, folder_path, recording_data, recording_json_path, _refresh_table)
                _l.addWidget(_lb, 0, Qt.AlignCenter)
            elif _at == 'scroll':
                _amt = record.get('scroll_amount', 3)
                # ★★★ 修复：防御 0 值，避免显示"下滑0"
                if _amt == 0:
                    _amt = 3
                _dir = "上" if _amt > 0 else "下"
                _lb = QLabel(f"{_dir}{abs(_amt)}")
                _lb.setStyleSheet("QLabel{color:#6E6E73;font-size:11px;padding:2px 6px;background:rgba(142,142,147,0.15);border-radius:6px;}")
                _l.addWidget(_lb, 0, Qt.AlignCenter)
            elif _at == 'condition':
                _lb = QLabel("条件分支")
                _lb.setStyleSheet("QLabel{color:#AF52DE;font-size:11px;padding:2px 6px;background:rgba(175,82,222,0.1);border-radius:6px;}")
                _l.addWidget(_lb, 0, Qt.AlignCenter)
            else:
                _px = record.get('x', 0); _py = record.get('y', 0)
                _lb = QLabel(f"({_px}, {_py})")
                _lb.setStyleSheet("QLabel{color:#8E8E93;font-size:11px;}")
                _l.addWidget(_lb, 0, Qt.AlignCenter)
            return _w

        def _make_del_widget(row_idx):
            _w = QWidget()
            _w.setStyleSheet("QWidget{background:transparent;}")
            _l = QHBoxLayout(_w)
            _l.setContentsMargins(4,0,4,0)
            _l.setAlignment(Qt.AlignCenter)
            _b = QPushButton("删除")
            _b.setFixedHeight(28)
            _b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            _b.setStyleSheet("QPushButton{background:transparent;color:#FF3B30;border:1px solid #FF3B30;border-radius:6px;padding:2px 8px;font-size:12px;}QPushButton:hover{background:#FF3B30;color:white;}")
            _b.setCursor(Qt.PointingHandCursor)
            _b.clicked.connect(lambda checked=False, idx=row_idx: (
                recording_data.pop(idx),
                [None for _ii,_oo in enumerate(recording_data,1) for _ in (_oo.__setitem__("step",_ii),)],
                save_json_data(recording_json_path, recording_data),
                _refresh_table()
            ))
            _l.addWidget(_b, 0, Qt.AlignVCenter | Qt.AlignHCenter)
            return _w

        # 填充数据
        for i, record in enumerate(recording_data):
            step = record.get('step', i + 1)
            action_type = record.get('action_type', 'left_click')
            step_item = QTableWidgetItem(str(step))
            step_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 0, step_item)
            _ab = _make_type_btn(i, action_type)
            _aw = QWidget(); _aw.setStyleSheet("QWidget{background:transparent;}")
            _al = QHBoxLayout(_aw); _al.setContentsMargins(4,0,4,0); _al.setAlignment(Qt.AlignCenter)
            _al.addWidget(_ab, 0, Qt.AlignVCenter | Qt.AlignHCenter)
            table.setCellWidget(i, 1, _aw)
            table.setCellWidget(i, 2, _make_param_widget(i, record))
            table.setCellWidget(i, 3, _make_del_widget(i))
            table.setRowHeight(i, 60)

        # 表格刷新函数
        def _refresh_table():
            table.setRowCount(len(recording_data))
            for _i,_o in enumerate(recording_data):
                _at = _o.get('action_type', 'left_click')
                table.setItem(_i,0,QTableWidgetItem(str(_o.get("step",_i+1)))); table.item(_i,0).setTextAlignment(Qt.AlignCenter)
                _ab2 = _make_type_btn(_i, _at)
                _aw2 = QWidget(); _aw2.setStyleSheet("QWidget{background:transparent;}")
                _al2 = QHBoxLayout(_aw2); _al2.setContentsMargins(4,0,4,0); _al2.setAlignment(Qt.AlignCenter)
                _al2.addWidget(_ab2, 0, Qt.AlignVCenter | Qt.AlignHCenter)
                table.setCellWidget(_i, 1, _aw2)
                table.setCellWidget(_i, 2, _make_param_widget(_i, _o))
                table.setCellWidget(_i, 3, _make_del_widget(_i))
                table.setRowHeight(_i, 60)

        # 设置列宽
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        table.setColumnWidth(3, 70)

        _cl.addWidget(table, 1)  # stretch=1 让表格占满空间

        # 底部按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ 添加操作 ▼")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #28A745;
            }
            QPushButton::menu-indicator { width: 0; }
        """)
        add_menu = QMenu()
        add_menu.addAction("👆 点击坐标").triggered.connect(lambda: _add_coord_op())
        add_menu.addAction("📝 文本输入").triggered.connect(lambda: _add_text_op())
        add_menu.addAction("⌨️ 按键输入").triggered.connect(lambda: _add_key_op())
        add_menu.addAction("🔄 滚动").triggered.connect(lambda: _add_scroll_op())
        add_btn.setMenu(add_menu)

        def _add_coord_op():
            """添加坐标点击操作"""
            from PyQt5.QtGui import QPainter as _QP, QFont as _QFt, QColor as _QC
            from PyQt5.QtCore import QTimer as _QT
            if self.parent and self.parent.isVisible():
                self.parent.showMinimized()
            parent_window.showMinimized()
            _ov = QDialog(parent_window)
            _ov.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            _ov.setAttribute(Qt.WA_TranslucentBackground)
            _ov.setMouseTracking(True)
            _tg = QRect()
            for _s in QApplication.screens():
                _tg = _tg.united(_s.geometry())
            _ov.setGeometry(_tg)
            def _mp(ev):
                if ev.button() == Qt.LeftButton:
                    _x = int(ev.globalX()); _y = int(ev.globalY())
                    recording_data.append({"step":len(recording_data)+1,"action_type":"left_click","x":_x,"y":_y,"delay":0.1})
                    for _i,_o in enumerate(recording_data,1): _o["step"]=_i
                    save_json_data(recording_json_path, recording_data)
                    _refresh_table()
                    _ov.accept()
                elif ev.button() == Qt.RightButton:
                    _ov.reject()
            _ov.mousePressEvent = _mp
            def _pe(ev):
                _p = _QP(_ov)
                _p.setRenderHint(_p.Antialiasing)
                _p.fillRect(_ov.rect(), _QC(0,0,0,100))
                _f = _QFt("PingFang SC,SimHei",16)
                _p.setFont(_f)
                _p.setPen(_QC("#FFFFFF"))
                _p.drawText(_ov.rect(), Qt.AlignCenter, "🖱️ 点击目标位置添加左键操作\n右键/Esc 取消")
                _p.end()
            _ov.paintEvent = _pe
            def _kp(ev):
                if ev.key() == Qt.Key_Escape:
                    _ov.reject()
                elif ev.key() in (Qt.Key_Return, Qt.Key_Enter):
                    _cursor = QCursor.pos()
                    _x = int(_cursor.x()); _y = int(_cursor.y())
                    recording_data.append({"step":len(recording_data)+1,"action_type":"left_click","x":_x,"y":_y,"delay":0.1})
                    for _i,_o in enumerate(recording_data,1): _o["step"]=_i
                    save_json_data(recording_json_path, recording_data)
                    _refresh_table()
                    _ov.accept()
            _ov.keyPressEvent = _kp
            def _focus():
                _ov.raise_(); _ov.activateWindow(); _ov.setFocus()
            _QT.singleShot(100, _focus)
            _QT.singleShot(300, _focus)
            _ov.exec_()

        def _add_text_op():
            recording_data.append({"step":len(recording_data)+1,"action_type":"text_input","text":"","delay":0})
            for _i,_o in enumerate(recording_data,1): _o["step"]=_i
            save_json_data(recording_json_path, recording_data)
            _refresh_table()
            self._show_text_input_dialog_coord(len(recording_data)-1, folder_path, recording_data, recording_json_path, _refresh_table)

        def _add_key_op():
            recording_data.append({"step":len(recording_data)+1,"action_type":"keyboard","key":"","delay":0})
            for _i,_o in enumerate(recording_data,1): _o["step"]=_i
            save_json_data(recording_json_path, recording_data)
            _refresh_table()
            self._show_key_input_dialog_coord(len(recording_data)-1, folder_path, recording_data, recording_json_path, _refresh_table)

        def _add_scroll_op():
            recording_data.append({"step":len(recording_data)+1,"action_type":"scroll","scroll_amount":3,"delay":0})
            for _i,_o in enumerate(recording_data,1): _o["step"]=_i
            save_json_data(recording_json_path, recording_data)
            _refresh_table()

        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        _cl.addLayout(btn_layout)

        return container

    def show_coordinate_data(self, parent_dialog, folder_path, recording_json_path):
        """显示坐标录制数据（独立对话框，供外部调用）"""
        try:
            recording_data = load_json_data(recording_json_path)
            if not isinstance(recording_data, list) or not recording_data:
                self.parent.show_beautiful_message('information', "提示", "该文件夹中没有坐标数据！", parent=parent_dialog)
                return

            coord_dialog = QDialog(parent_dialog)
            coord_dialog.setWindowTitle(f"坐标录制数据 - {os.path.basename(str(folder_path))}")
            screen_width, screen_height = get_screen_size()
            coord_dialog.resize(int(screen_width * 0.5), int(screen_height * 0.6))
            coord_dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            coord_dialog.setAttribute(Qt.WA_TranslucentBackground)
            center_window(coord_dialog)

            _dlg_layout = QVBoxLayout(coord_dialog)
            _dlg_layout.setContentsMargins(0, 0, 0, 0)
            _dlg_layout.setSpacing(0)
            _outer = QFrame(coord_dialog)
            _outer.setStyleSheet("""
                QFrame {
                    background: #FFFFFF;
                    border-radius: 18px;
                    border: 2px solid #E5E5EA;
                }
            """)
            _inner = QVBoxLayout(_outer)
            _inner.setContentsMargins(16, 12, 16, 16)
            _inner.setSpacing(8)
            _dlg_layout.addWidget(_outer)

            # 关闭红色圆点
            _dh = QHBoxLayout()
            _dh.setContentsMargins(0, 0, 0, 0)
            _dh.addStretch()
            _dot = QFrame()
            _dot.setFixedSize(16, 16)
            _dot.setStyleSheet("background:#FF5F57; border-radius:6px; border:none;")
            _dot.setCursor(Qt.PointingHandCursor)
            def _closeD(ev):
                if ev.button()==Qt.LeftButton: coord_dialog.close()
            _dot.mousePressEvent = _closeD
            _dh.addWidget(_dot)
            _inner.addLayout(_dh)

            title_label = QLabel("📍 坐标录制数据")
            title_label.setStyleSheet("font-size:16px; font-weight:bold; color:#1C1C1E; padding:4px 0; background:transparent; border:none;")
            title_label.setAlignment(Qt.AlignCenter)
            _inner.addWidget(title_label)

            # 对话框拖动
            coord_dialog._drag_pos = None
            def _dialog_press(ev):
                if ev.button() == Qt.LeftButton:
                    coord_dialog._drag_pos = ev.globalPos() - coord_dialog.pos()
            def _dialog_move(ev):
                if getattr(coord_dialog, '_drag_pos', None) and ev.buttons() & Qt.LeftButton:
                    coord_dialog.move(ev.globalPos() - coord_dialog._drag_pos)
            coord_dialog.mousePressEvent = _dialog_press
            coord_dialog.mouseMoveEvent = _dialog_move
            coord_dialog.setMouseTracking(True)

            # 嵌入可复用的表格面板
            panel = self._build_coord_table_panel(coord_dialog, folder_path, recording_json_path)
            if panel:
                _inner.addWidget(panel, 1)

            # 添加关闭按钮
            _btn_bar = QHBoxLayout()
            _btn_bar.addStretch()
            close_btn = QPushButton("关闭")
            close_btn.setStyleSheet("""QPushButton{background-color:#0A84FF;color:white;border:none;border-radius:6px;padding:10px 24px;font-size:13px;font-weight:bold;}QPushButton:hover{background-color:#006AE0;}""")
            close_btn.clicked.connect(coord_dialog.close)
            _btn_bar.addWidget(close_btn)
            _inner.addLayout(_btn_bar)

            parent_dialog.close()
            coord_dialog.exec_()
        except Exception as e:
            traceback.print_exc()
            StyledMessageDialog(self, title='错误', text=f"显示坐标数据失败: {e}", msg_type='critical', buttons='ok').exec_()
    
    def _update_coord_action_type(self, recording_data, recording_json_path, index, new_type, refresh_cb, btn=None):
        """更新坐标录制数据中指定步骤的操作类型"""
        if index < len(recording_data):
            record = recording_data[index]
            old_type = record.get('action_type', 'left_click')
            record['action_type'] = new_type
            # 切换操作类型时，清理不相关的字段
            if new_type in ('left_click', 'right_click', 'double_click', 'middle_click'):
                # 保留坐标，移除文本/按键相关字段
                record.pop('text', None)
                record.pop('key', None)
                record.pop('scroll_amount', None)
                if 'x' not in record or 'y' not in record:
                    record['x'] = 0
                    record['y'] = 0
            elif new_type == 'text_input':
                if 'text' not in record or not record['text']:
                    record['text'] = ''
                record.pop('scroll_amount', None)
            elif new_type == 'keyboard':
                if 'key' not in record or not record['key']:
                    record['key'] = ''
                record.pop('text', None)
                record.pop('scroll_amount', None)
            elif new_type == 'scroll':
                if 'scroll_amount' not in record:
                    record['scroll_amount'] = 3
                record.pop('text', None)
                record.pop('key', None)
            save_json_data(recording_json_path, recording_data)
            refresh_cb()
    
    def _show_text_input_dialog_coord(self, index, folder_path, recording_data, recording_json_path, refresh_cb):
        """坐标数据表格用的文本输入对话框（直接操作 recording_data）"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
        from PyQt5.QtCore import Qt
        current_text = ""
        if index < len(recording_data):
            current_text = recording_data[index].get('text', '')
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("修改文本")
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        apply_dialog_style(dialog, 0.35, 0.2)
        layout = QVBoxLayout()
        label = QLabel("请输入新的文本内容:")
        layout.addWidget(label)
        text_edit = QLineEdit(current_text)
        text_edit.setClearButtonEnabled(True)
        text_edit.selectAll()
        layout.addWidget(text_edit)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.setFocusPolicy(Qt.StrongFocus)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.setFocusPolicy(Qt.StrongFocus)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        if dialog.exec_() == QDialog.Accepted:
            new_text = text_edit.text()
            if index < len(recording_data):
                recording_data[index]['text'] = new_text
                recording_data[index]['action_type'] = 'text_input'
                save_json_data(recording_json_path, recording_data)
                refresh_cb()

    def _show_key_input_dialog_coord(self, index, folder_path, recording_data, recording_json_path, refresh_cb):
        """坐标数据表格用的按键输入对话框（直接操作 recording_data）"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
        from PyQt5.QtCore import Qt
        current_key = ""
        if index < len(recording_data):
            current_key = recording_data[index].get('key', '')
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("修改按键")
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        apply_dialog_style(dialog, 0.3, 0.2)
        layout = QVBoxLayout()
        label = QLabel("请按下要修改的按键(支持组合键):")
        layout.addWidget(label)
        line_edit = QLineEdit()
        line_edit.setClearButtonEnabled(True)
        line_edit.setReadOnly(True)
        if current_key:
            line_edit.setText(current_key)
        layout.addWidget(line_edit)
        def on_key(event):
            key = event.key()
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return
            modifiers = []
            if event.modifiers() & Qt.ControlModifier: modifiers.append("ctrl")
            if event.modifiers() & Qt.ShiftModifier: modifiers.append("shift")
            if event.modifiers() & Qt.AltModifier: modifiers.append("alt")
            if event.modifiers() & Qt.MetaModifier: modifiers.append("meta")
            key_map = {
                Qt.Key_F1:"f1",Qt.Key_F2:"f2",Qt.Key_F3:"f3",Qt.Key_F4:"f4",
                Qt.Key_F5:"f5",Qt.Key_F6:"f6",Qt.Key_F7:"f7",Qt.Key_F8:"f8",
                Qt.Key_F9:"f9",Qt.Key_F10:"f10",Qt.Key_F11:"f11",Qt.Key_F12:"f12",
                Qt.Key_Space:"space",Qt.Key_Return:"return",Qt.Key_Tab:"tab",
                Qt.Key_Escape:"esc",Qt.Key_Backspace:"backspace",Qt.Key_Delete:"delete",
                Qt.Key_Home:"home",Qt.Key_End:"end",Qt.Key_PageUp:"pageup",Qt.Key_PageDown:"pagedown",
                Qt.Key_Up:"up",Qt.Key_Down:"down",Qt.Key_Left:"left",Qt.Key_Right:"right",
                Qt.Key_Insert:"insert",
            }
            key_name = key_map.get(key, (chr(key).lower() if key < 128 else ""))
            if key_name:
                parts = modifiers + [key_name]
                line_edit.setText("+".join(parts))
        dialog.keyPressEvent = on_key
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.setFocusPolicy(Qt.StrongFocus)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.setFocusPolicy(Qt.StrongFocus)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        if dialog.exec_() == QDialog.Accepted:
            new_key = line_edit.text()
            if index < len(recording_data):
                recording_data[index]['key'] = new_key
                recording_data[index]['action_type'] = 'keyboard'
                save_json_data(recording_json_path, recording_data)
                refresh_cb()

    def _show_scroll_input_dialog_coord(self, index, folder_path, recording_data, recording_json_path, refresh_cb):
        """滚动操作编辑对话框（设置方向和格数）"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QPushButton, QHBoxLayout, QButtonGroup, QRadioButton
        from PyQt5.QtCore import Qt
        from styles import apply_dialog_style

        current_amt = 3
        if index < len(recording_data):
            current_amt = recording_data[index].get('scroll_amount', 3)
        # ★★★ 修复：防御 0 值，确保 QSpinBox 初始值至少为 1
        if current_amt == 0:
            current_amt = 3

        dialog = QDialog(self.parent)
        dialog.setWindowTitle("设置滚动")
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        apply_dialog_style(dialog, 0.28, 0.2)
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # 方向选择
        dir_label = QLabel("滚动方向:")
        layout.addWidget(dir_label)
        dir_group = QButtonGroup(dialog)
        dir_layout = QHBoxLayout()
        rb_up = QRadioButton("向上")
        rb_down = QRadioButton("向下")
        # ⚠️ 注意：ID 必须用正数，避免 checkedId() 返回 -1 时无法区分"无选中"和"选中 ID=-1 的按钮"
        dir_group.addButton(rb_up, 1)
        dir_group.addButton(rb_down, 2)
        if current_amt > 0:
            rb_up.setChecked(True)
        else:
            rb_down.setChecked(True)
        dir_layout.addWidget(rb_up)
        dir_layout.addWidget(rb_down)
        layout.addLayout(dir_layout)

        # 格数输入
        amount_label = QLabel("滚动格数（正数表示格数，负数表示反向）:")
        layout.addWidget(amount_label)
        amount_spin = QSpinBox()
        amount_spin.setRange(1, 100)
        amount_spin.setValue(abs(current_amt))
        amount_spin.setFixedWidth(80)
        layout.addWidget(amount_spin)

        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.setFocusPolicy(Qt.StrongFocus)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.setFocusPolicy(Qt.StrongFocus)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            checked_id = dir_group.checkedId()
            direction = 1 if checked_id == 1 else -1  # 1=向上, 2=向下
            # ★★★ 修复：确保 amount 至少为 1（防御 QSpinBox.value() 可能返回 0 的边界情况）
            amount = max(1, amount_spin.value())
            scroll_amount = direction * amount
            # 确保结果不为 0（防御性）
            if scroll_amount == 0:
                scroll_amount = 3 if direction >= 0 else -3
            if index < len(recording_data):
                recording_data[index]['scroll_amount'] = scroll_amount
                recording_data[index]['action_type'] = 'scroll'
                save_json_data(recording_json_path, recording_data)
                refresh_cb()

    def show_key_input_dialog(self, index, folder_path):
        """显示按键输入对话框，用于修改按键"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
            from PyQt5.QtCore import Qt, pyqtSignal
            
            class KeyInputDialog(QDialog):
                key_pressed = pyqtSignal(str)
                
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("修改按键")
                    self.setModal(True)
                    # 设置窗口标志：移除帮助按钮，添加最小化按钮，保持置顶
                    self.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                    
                    # 应用统一的对话框样式
                    apply_dialog_style(self, 0.3, 0.2)
                    
                    layout = QVBoxLayout()
                    
                    label = QLabel("请按下要修改的按键(支持组合键):")
                    layout.addWidget(label)
                    
                    self.line_edit = QLineEdit()
                    self.line_edit.setClearButtonEnabled(True)
                    self.line_edit.setReadOnly(True)
                    layout.addWidget(self.line_edit)
                    
                    button_layout = QHBoxLayout()
                    
                    self.ok_btn = QPushButton("确定")
                    self.ok_btn.setFocusPolicy(Qt.StrongFocus)
                    self.ok_btn.setDefault(True)
                    self.ok_btn.clicked.connect(self.accept)
                    self.ok_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {THEME_PRIMARY};
                            color: white;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: bold;
                            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                        }}
                        QPushButton:hover {{
                background-color: #006AE0;
                        }}
                        QPushButton:pressed {{
                background-color: #004DB3;
                        }}
                    """)
                    button_layout.addWidget(self.ok_btn)

                    self.cancel_btn = QPushButton("取消")
                    self.cancel_btn.setFocusPolicy(Qt.StrongFocus)
                    self.cancel_btn.clicked.connect(self.reject)
                    self.cancel_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: #FFFFFF;
                            color: #8E8E93;
                            border: 1px solid #D1D1D6;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                        }}
                        QPushButton:hover {{
                            background-color: #F0F0F2;
                            color: #6E6E73;
                        }}
                    """)
                    button_layout.addWidget(self.cancel_btn)
                    
                    layout.addLayout(button_layout)
                    self.setLayout(layout)
                    
                    self.current_keys = []
                    self.key_map = {
                        Qt.Key_Return: 'enter',
                        Qt.Key_Enter: 'enter',
                        Qt.Key_Escape: 'esc',
                        Qt.Key_Tab: 'tab',
                        Qt.Key_Backspace: 'backspace',
                        Qt.Key_Delete: 'delete',
                        Qt.Key_Space: 'space',
                        Qt.Key_Up: 'up',
                        Qt.Key_Down: 'down',
                        Qt.Key_Left: 'left',
                        Qt.Key_Right: 'right',
                        Qt.Key_F1: 'f1',
                        Qt.Key_F2: 'f2',
                        Qt.Key_F3: 'f3',
                        Qt.Key_F4: 'f4',
                        Qt.Key_F5: 'f5',
                        Qt.Key_F6: 'f6',
                        Qt.Key_F7: 'f7',
                        Qt.Key_F8: 'f8',
                        Qt.Key_F9: 'f9',
                        Qt.Key_F10: 'f10',
                        Qt.Key_F11: 'f11',
                        Qt.Key_F12: 'f12',
                    }
                    
                def showEvent(self, event):
                    super().showEvent(event)
                    self.activateWindow()
                    self.raise_()
                    self.setFocus()
                    
                def keyPressEvent(self, event):
                    key = event.key()
                    
                    if key in [Qt.Key_Return, Qt.Key_Enter]:
                        key_name = 'enter'
                        modifiers = []
                        if event.modifiers() & Qt.ControlModifier:
                            modifiers.append('ctrl')
                        if event.modifiers() & Qt.ShiftModifier:
                            modifiers.append('shift')
                        if event.modifiers() & Qt.AltModifier:
                            modifiers.append('alt')
                        if event.modifiers() & Qt.MetaModifier:
                            modifiers.append('meta')
                        
                        if modifiers:
                            key_str = '+'.join(modifiers + [key_name])
                        else:
                            key_str = key_name
                        
                        self.line_edit.setText(key_str)
                        # 按键已设置，自动确认关闭对话框
                        self.accept()
                        event.accept()
                        return
                    
                    if key in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]:
                        return
                    
                    if key in self.key_map:
                        key_name = self.key_map[key]
                    else:
                        if key >= Qt.Key_A and key <= Qt.Key_Z:
                            key_name = chr(key + 32)
                        elif key >= Qt.Key_0 and key <= Qt.Key_9:
                            key_name = chr(key)
                        else:
                            key_name = event.text() or ''
                            if not key_name:
                                return
                    
                    modifiers = []
                    if event.modifiers() & Qt.ControlModifier:
                        modifiers.append('ctrl')
                    if event.modifiers() & Qt.ShiftModifier:
                        modifiers.append('shift')
                    if event.modifiers() & Qt.AltModifier:
                        modifiers.append('alt')
                    if event.modifiers() & Qt.MetaModifier:
                        modifiers.append('meta')
                    
                    if modifiers:
                        key_str = '+'.join(modifiers + [key_name])
                    else:
                        key_str = key_name
                    
                    self.line_edit.setText(key_str)
                    # 按键已设置，自动确认关闭对话框
                    self.accept()
                    event.accept()
            
            dialog = KeyInputDialog(self.parent)
            if dialog.exec_() == QDialog.Accepted:
                new_key = dialog.line_edit.text()
                if new_key:
                    # 更新image_actions
                    self.image_actions[index] = f"按键: {new_key}"
                    # 保存到JSON文件
                    recording_json_path = os.path.join(folder_path, 'recording.json')
                    if os.path.exists(recording_json_path):
                        recording_data = load_json_data(recording_json_path)
                        if isinstance(recording_data, list):
                            # 使用 image_step_map 获取实际步骤号，避免键盘操作无图片导致的错位
                            step = self.image_step_map.get(index, index + 1)
                            for d in recording_data:
                                if d.get('step') == step:
                                    d['action_type'] = 'keyboard'
                                    d['key'] = new_key
                                    break
                            save_json_data(recording_json_path, recording_data)
                    # 刷新界面
                    self.refresh_view_images(folder_path)
        except Exception as e:
            # print(f"修改按键失败: {e}")  # [日志已禁用]
            from PyQt5.QtWidgets import QMessageBox
            self.parent.show_beautiful_message('critical', "错误", f"修改按键失败: {e}", parent=self.parent)

    def show_scroll_input_dialog(self, index, folder_path):
        """显示滚动设置对话框，用于修改滚动参数"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QPushButton, QHBoxLayout, QComboBox
            from PyQt5.QtCore import Qt
            
            # 先获取当前的滚动参数
            current_scroll_amount = 3
            recording_json_path = os.path.join(folder_path, 'recording.json')
            if os.path.exists(recording_json_path):
                recording_data = load_json_data(recording_json_path)
                if isinstance(recording_data, list):
                    # 使用 image_step_map 获取实际步骤号，避免键盘操作无图片导致的错位
                    step = self.image_step_map.get(index, index + 1)
                    for d in recording_data:
                        if d.get('step') == step and d.get('action_type') == 'scroll':
                            current_scroll_amount = d.get('scroll_amount', 3)
                            break
            
            class ScrollInputDialog(QDialog):
                def __init__(self, parent=None, current_amount=3):
                    super().__init__(parent)
                    self.setWindowTitle("修改滚动设置")
                    self.setModal(True)
                    self.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                    
                    apply_dialog_style(self, 0.3, 0.2)
                    
                    layout = QVBoxLayout()
                    
                    # 方向选择
                    direction_layout = QHBoxLayout()
                    direction_label = QLabel("滚动方向:")
                    direction_layout.addWidget(direction_label)
                    
                    self.direction_combo = QComboBox()
                    self.direction_combo.addItems(["向上", "向下"])
                    if current_amount > 0:
                        self.direction_combo.setCurrentIndex(0)
                    else:
                        self.direction_combo.setCurrentIndex(1)
                    direction_layout.addWidget(self.direction_combo)
                    layout.addLayout(direction_layout)
                    
                    # 滚动量
                    amount_layout = QHBoxLayout()
                    amount_label = QLabel("滚动量(每格):")
                    amount_layout.addWidget(amount_label)
                    
                    self.amount_spin = QSpinBox()
                    self.amount_spin.setMinimum(1)
                    self.amount_spin.setMaximum(999999)
                    self.amount_spin.setValue(abs(current_amount))
                    amount_layout.addWidget(self.amount_spin)
                    layout.addLayout(amount_layout)
                    
                    button_layout = QHBoxLayout()
                    
                    self.ok_btn = QPushButton("确定")
                    self.ok_btn.setFocusPolicy(Qt.StrongFocus)
                    self.ok_btn.setDefault(True)
                    self.ok_btn.clicked.connect(self.accept)
                    self.ok_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {THEME_PRIMARY};
                            color: white;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: bold;
                            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                        }}
                        QPushButton:hover {{
                            background-color: #006AE0;
                        }}
                        QPushButton:pressed {{
                            background-color: #004DB3;
                        }}
                    """)
                    button_layout.addWidget(self.ok_btn)

                    self.cancel_btn = QPushButton("取消")
                    self.cancel_btn.setFocusPolicy(Qt.StrongFocus)
                    self.cancel_btn.clicked.connect(self.reject)
                    self.cancel_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: #FFFFFF;
                            color: #8E8E93;
                            border: 1px solid #D1D1D6;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                        }}
                        QPushButton:hover {{
                            background-color: #F0F0F2;
                            color: #6E6E73;
                        }}
                    """)
                    button_layout.addWidget(self.cancel_btn)
                    
                    layout.addLayout(button_layout)
                    self.setLayout(layout)
                    
                def get_scroll_amount(self):
                    direction = self.direction_combo.currentText()
                    amount = self.amount_spin.value()
                    return amount if direction == "向上" else -amount
            
            dialog = ScrollInputDialog(self.parent, current_scroll_amount)
            if dialog.exec_() == QDialog.Accepted:
                new_scroll_amount = dialog.get_scroll_amount()
                # 更新image_actions
                direction = "上" if new_scroll_amount > 0 else "下"
                self.image_actions[index] = f"滚动: {direction}{abs(new_scroll_amount)}"
                # 保存到JSON文件
                if os.path.exists(recording_json_path):
                    recording_data = load_json_data(recording_json_path)
                    if isinstance(recording_data, list):
                        # 使用 image_step_map 获取实际步骤号，避免键盘操作无图片导致的错位
                        step = self.image_step_map.get(index, index + 1)
                        for d in recording_data:
                            if d.get('step') == step:
                                d['action_type'] = 'scroll'
                                d['scroll_amount'] = new_scroll_amount
                                break
                        save_json_data(recording_json_path, recording_data)
                # 刷新界面
                self.refresh_view_images(folder_path)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.parent, '错误', f'修改滚动设置失败: {e}')

    def show_text_input_dialog(self, index, folder_path):
        """显示文本输入对话框，用于修改文本内容"""
        try:
            from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                                         QLineEdit, QPushButton, QHBoxLayout)
            from PyQt5.QtCore import Qt

            # 获取当前的文本内容
            current_text = ""
            recording_json_path = os.path.join(folder_path, 'recording.json')
            if os.path.exists(recording_json_path):
                recording_data = load_json_data(recording_json_path)
                if isinstance(recording_data, list):
                    # 使用 image_step_map 获取实际步骤号，避免键盘操作无图片导致的错位
                    step = self.image_step_map.get(index, index + 1)
                    for d in recording_data:
                        if d.get('step') == step and d.get('action_type') == 'text_input':
                            current_text = d.get('text', '')
                            break

            class TextInputDialog(QDialog):
                def __init__(self, parent=None, current_text=""):
                    super().__init__(parent)
                    self.setWindowTitle("修改文本")
                    self.setModal(True)
                    self.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint |
                                        Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

                    apply_dialog_style(self, 0.35, 0.2)

                    layout = QVBoxLayout()

                    label = QLabel("请输入新的文本内容:")
                    layout.addWidget(label)

                    self.text_edit = QLineEdit(current_text)
                    self.text_edit.setClearButtonEnabled(True)
                    self.text_edit.selectAll()
                    layout.addWidget(self.text_edit)

                    button_layout = QHBoxLayout()

                    self.ok_btn = QPushButton("确定")
                    self.ok_btn.setFocusPolicy(Qt.StrongFocus)
                    self.ok_btn.setDefault(True)
                    self.ok_btn.clicked.connect(self.accept)
                    self.ok_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {THEME_PRIMARY};
                            color: white;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: bold;
                            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                        }}
                        QPushButton:hover {{
                            background-color: #006AE0;
                        }}
                        QPushButton:pressed {{
                            background-color: #004DB3;
                        }}
                    """)
                    button_layout.addWidget(self.ok_btn)

                    self.cancel_btn = QPushButton("取消")
                    self.cancel_btn.setFocusPolicy(Qt.StrongFocus)
                    self.cancel_btn.clicked.connect(self.reject)
                    self.cancel_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: #FFFFFF;
                            color: #8E8E93;
                            border: 1px solid #D1D1D6;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                        }}
                        QPushButton:hover {{
                            background-color: #F0F0F2;
                            color: #6E6E73;
                        }}
                    """)
                    button_layout.addWidget(self.cancel_btn)

                    layout.addLayout(button_layout)
                    self.setLayout(layout)

            dialog = TextInputDialog(self.parent, current_text)
            if dialog.exec_() == QDialog.Accepted:
                new_text = dialog.text_edit.text()
                if new_text == current_text:
                    return
                # 更新 image_actions
                display_text = new_text if len(new_text) <= 10 else new_text[:10] + "..."
                self.image_actions[index] = f"文本: {display_text}"
                # 保存到 JSON 文件
                if os.path.exists(recording_json_path):
                    recording_data = load_json_data(recording_json_path)
                    if isinstance(recording_data, list):
                        # 使用 image_step_map 获取实际步骤号，避免键盘操作无图片导致的错位
                        step = self.image_step_map.get(index, index + 1)
                        for d in recording_data:
                            if d.get('step') == step:
                                d['action_type'] = 'text_input'
                                d['text'] = new_text
                                break
                        save_json_data(recording_json_path, recording_data)
                # 刷新界面
                self.refresh_view_images(folder_path)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            self.parent.show_beautiful_message('critical', "错误", f"修改文本失败: {e}", parent=self.parent)

    def get_delay_for_step(self, folder_path, step_index):
        """获取指定步骤的延迟时间（秒）"""
        try:
            recording_json_path = os.path.join(folder_path, 'recording.json')
            if os.path.exists(recording_json_path):
                recording_data = load_json_data(recording_json_path)
                if isinstance(recording_data, list):
                    # 使用 image_step_map 获取实际步骤号，避免键盘操作无图片导致的错位
                    step = self.image_step_map.get(step_index, step_index + 1)
                    for d in recording_data:
                        if d.get('step') == step:
                            return d.get('delay', 0)
        except Exception as e:
            # print(f"获取延迟时间失败: {e}")  # [日志已禁用]
            pass
        return 0

    def update_delay(self, index, delay_seconds, folder_path):
        """更新指定步骤的延迟时间"""
        try:
            recording_json_path = os.path.join(folder_path, 'recording.json')
            if os.path.exists(recording_json_path):
                recording_data = load_json_data(recording_json_path)
                if isinstance(recording_data, list):
                    # 使用 image_step_map 获取实际步骤号，避免键盘操作无图片导致的错位
                    step = self.image_step_map.get(index, index + 1)
                    for d in recording_data:
                        if d.get('step') == step:
                            d['delay'] = delay_seconds
                            break
                    save_json_data(recording_json_path, recording_data)
        except Exception as e:
            # print(f"更新延迟时间失败: {e}")  # [日志已禁用]
            pass

    def reorder_images(self, folder_path):
        """重新排序图片文件名"""
        try:
            # 获取所有图片文件
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            
            # 提取步骤编号并排序
            step_files = []
            for img_file in image_files:
                match = re.search(r'操作(\d+)\.', img_file)
                if match:
                    step_num = int(match.group(1))
                    step_files.append((step_num, img_file))
            
            # 按步骤编号排序
            step_files.sort(key=lambda x: x[0])
            
            # 重新编号
            for i, (old_step, file_name) in enumerate(step_files):
                new_step = i + 1
                if old_step != new_step:
                    # 创建新文件名
                    new_name = re.sub(r'操作(\d+)\.', f'操作{new_step}.', file_name)
                    old_path = os.path.join(folder_path, file_name)
                    new_path = os.path.join(folder_path, new_name)
                    
                    # 重命名文件
                    if os.path.exists(old_path) and not os.path.exists(new_path):
                        os.rename(old_path, new_path)
                        
        except Exception as e:
            # print(f"重命名图片文件失败: {e}")  # [日志已禁用]
            pass






    def add_condition_for_image(self, image_index, folder_path):
        """为特定图片添加条件分支"""
        # 获取图片文件列表
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        # 使用自然排序：按「操作X」中的数字X排序，避免 1,10,11,2 这种字符串排序问题
        image_files.sort(key=lambda x: int(re.search(r'操作(\d+)', x).group(1)) if re.search(r'操作(\d+)', x) else 0)

        if 0 <= image_index < len(image_files):
            image_path = image_files[image_index]
            self.add_condition_branch(None, folder_path, image_index, image_path)
        
    def add_condition_branch(self, parent_dialog, folder_path, image_index=None, image_path=None):
        """添加条件分支操作"""
        if parent_dialog:
            parent_dialog.close()
        
        # 创建条件分支对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加条件分支")
        
        # 使用统一的样式函数
        apply_dialog_style(dialog, 0.5, 0.35)
        layout = QVBoxLayout(dialog)
        
        # 条件类型选择和条件图片输入框（水平排列）
        condition_layout = QHBoxLayout()
        condition_label = QLabel("条件类型:")
        condition_combo = QComboBox()
        condition_combo.addItems(["如果找到图片", "如果找不到图片"])
        
        # 条件图片输入框（移到条件类型旁边）
        image_path_edit = QLineEdit()
        image_path_edit.setReadOnly(True)
        if image_path:
            # 只显示文件名，不显示完整路径
            image_path_edit.setText(os.path.basename(image_path))
        
        # 添加到同一水平布局
        condition_layout.addWidget(condition_label)
        condition_layout.addWidget(condition_combo)
        condition_layout.addWidget(image_path_edit)
        layout.addLayout(condition_layout)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 操作步骤
        true_label = QLabel("操作步骤:")
        true_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(true_label)
        
        # 操作步骤下拉框（减少与上方标签的间距）
        true_steps_layout = QHBoxLayout()
        true_steps_layout.setContentsMargins(0, 5, 0, 0)  # 减少上边距
        true_steps_combo = QComboBox()
        true_steps_combo.addItems([
            "继续执行后续操作", 
            "跳转到指定步骤", 
            "停止执行",
            "等待指定秒数后继续执行"
        ])
        true_steps_layout.addWidget(true_steps_combo)
        layout.addLayout(true_steps_layout)
        
        # 输入框容器（按屏幕比例设置大小，避免UI跳动）
        screen_width, screen_height = get_screen_size()
        input_container = QWidget()
        input_container.setFixedHeight(int(screen_height * 0.04))  # 屏幕高度的4%
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        # 跳转步骤输入框（默认隐藏）
        true_step_layout = QHBoxLayout()
        true_step_label = QLabel("跳转到步骤:")
        true_step_input = QSpinBox()
        true_step_input.setRange(1, 100)
        true_step_input.setValue(1)
        true_step_layout.addWidget(true_step_label)
        true_step_layout.addWidget(true_step_input)
        true_step_widget = QWidget()
        true_step_widget.setLayout(true_step_layout)
        true_step_widget.hide()
        input_layout.addWidget(true_step_widget)
        
        # 等待时间输入框（默认隐藏）
        delay_layout = QHBoxLayout()
        delay_label = QLabel("等待时间(秒):")
        delay_spinbox = QDoubleSpinBox()
        delay_spinbox.setSingleStep(0.1)
        delay_spinbox.setDecimals(1)
        delay_spinbox.setValue(1.0)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(delay_spinbox)
        delay_widget = QWidget()
        delay_widget.setLayout(delay_layout)
        delay_widget.hide()
        input_layout.addWidget(delay_widget)
        
        layout.addWidget(input_container)
        
        # 显示/隐藏输入框的函数
        def show_input_widgets():
            if true_steps_combo.currentText() == "跳转到指定步骤":
                true_step_widget.show()
                delay_widget.hide()
            elif true_steps_combo.currentText() == "等待指定秒数后继续执行":
                true_step_widget.hide()
                delay_widget.show()
            else:
                true_step_widget.hide()
                delay_widget.hide()
        
        true_steps_combo.currentTextChanged.connect(show_input_widgets)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存条件")
        save_btn.setFixedSize(100, 36)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #0A84FF;

            }
            QPushButton:pressed {
                background-color: #0A84FF;

            }
        """)
        save_btn.clicked.connect(lambda: self.save_condition_branch(
            dialog, folder_path, condition_combo.currentText(),
            image_path, true_steps_combo.currentText(),
            true_step_input.value(), delay_spinbox.value(), image_index
          ))
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #0A84FF;

            }
            QPushButton:pressed {
                background-color: #0A84FF;

            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        
        
        dialog.exec_()
    
    def browse_condition_image(self, line_edit, folder_path):
        """浏览选择条件图片"""
        from utils import get_recordings_path
        # 默认打开当前录制文件夹
        initial_dir = folder_path
        if not os.path.exists(initial_dir):
            initial_dir = get_recordings_path()
        
        # 获取图片文件
        image_files = []
        for root, dirs, files in os.walk(initial_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            self.show_beautiful_message('warning', '警告', '在指定目录中未找到图片文件')
            return
        
        # 创建图片选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择条件图片")
        
        # 使用统一的样式函数
        apply_dialog_style(dialog, 0.4, 0.45)
        layout = QVBoxLayout(dialog)
        
        # 图片列表
        list_widget = QListWidget()
        for img_path in image_files:
            # 只显示文件名，不显示完整路径
            file_name = os.path.basename(img_path)
            list_widget.addItem(file_name)
        layout.addWidget(list_widget)
        
        # 图片预览
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignCenter)
        # 按屏幕比例设置最小高度
        screen_width, screen_height = get_screen_size()
        preview_min_height = int(screen_height * 0.25)  # 屏幕高度的25%
        preview_label.setMinimumHeight(preview_min_height)
        layout.addWidget(preview_label)
        
        # 更新预览函数
        def update_preview():
            current_row = list_widget.currentRow()
            if 0 <= current_row < len(image_files):
                img_path = image_files[current_row]
                # 按屏幕比例缩放图片以适应预览区域
                screen_width, screen_height = get_screen_size()
                preview_width = int(screen_width * 0.25)  # 屏幕宽度的25%
                preview_height = int(screen_height * 0.2)  # 屏幕高度的20%
                pixmap = load_qpixmap(img_path, preview_width, preview_height)
                if pixmap is not None:
                    preview_label.setPixmap(pixmap)
        
        # 连接选择变化信号
        list_widget.currentRowChanged.connect(update_preview)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        select_btn = QPushButton("选择")
        select_btn.setFixedSize(100, 36)
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #0A84FF;
                
            }
            QPushButton:pressed {
                background-color: #0A84FF;
                
            }
        """)
        select_btn.clicked.connect(lambda: self.select_condition_image(
            dialog, line_edit, image_files, list_widget.currentRow()
        ))
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #0A84FF;
                
            }
            QPushButton:pressed {
                background-color: #0A84FF;
                
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(select_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # 默认选择第一项并显示预览
        if list_widget.count() > 0:
            list_widget.setCurrentRow(0)
        
        dialog.exec_()
    
    def select_condition_image(self, dialog, line_edit, image_files, current_row):
        """选择条件图片"""
        if 0 <= current_row < len(image_files):
            # 只设置文件名，不设置完整路径
            file_name = os.path.basename(image_files[current_row])
            line_edit.setText(file_name)
        dialog.accept()
    
    def save_condition_branch(self, dialog, folder_path, condition_text, image_path, action_text, step_value, delay_time, image_index=None):
        """保存条件分支"""
        # 现在image_path是直接传入的，不需要检查是否为空
        # 因为用户点击图片下方按钮时已经指定了图片路径
        
        # 转换条件类型
        condition_type = "if_found" if condition_text == "如果找到图片" else "if_not_found"
        
        # 转换操作类型
        def convert_action(action_text, step_value, delay_time):
            if action_text == "继续执行后续操作":
                return {"type": "continue", "step": None}
            elif action_text == "跳转到指定步骤":
                return {"type": "jump", "step": step_value}
            elif action_text == "停止执行":
                return {"type": "stop", "step": None}
            elif action_text == "等待指定秒数后继续执行":
                return {"type": "delay_continue", "step": None, "delay": delay_time}
            else:
                return {"type": "continue", "step": None}
        
        action_data = convert_action(action_text, step_value, delay_time)
        
        # 创建条件步骤
        from selection_overlay import SelectionOverlay
        overlay = SelectionOverlay(self.parent, parent=self.parent, screen_pixmap=None, recording_dir=folder_path)
        overlay.save_condition_step(condition_type, image_path, action_data, image_index)
        
        self.show_beautiful_message('success', '成功', '条件分支已保存')
        dialog.accept()
        
        # 重新打开查看窗口
        self.view_images(folder_path)

    def rename_folder(self, folder_path):
        """重命名文件夹"""
        try:
            # 获取当前文件夹名称
            current_name = os.path.basename(folder_path)
            
            # 创建自定义对话框，避免QInputDialog.getText的输入法问题
            dialog = QDialog(self)
            dialog.setWindowTitle("重命名文件夹")
            dialog.setModal(False)
            
            # 应用统一的对话框样式
            apply_dialog_style(dialog, 0.3, 0.2)
            
            layout = QVBoxLayout()
            label = QLabel("请输入新的文件夹名称:")
            layout.addWidget(label)
            
            # 创建自定义的QLineEdit类，优化输入法处理
            class CustomLineEdit(QLineEdit):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    
                def inputMethodEvent(self, event):
                    try:
                        # 直接处理输入法事件，不调用processEvents避免死锁
                        super().inputMethodEvent(event)
                    except Exception as e:
                        # print(f"输入法事件处理错误: {e}")  # [日志已禁用]
                        pass
                    # 即使出错也要调用父类方法，确保基本功能可用
                    super().inputMethodEvent(event)
                
                def keyPressEvent(self, event):
                    # 处理回车键，触发确定
                    if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                        # 找到父对话框并触发确定按钮
                        parent = self.parent()
                        while parent and not isinstance(parent, QDialog):
                            parent = parent.parent()
                        if parent:
                            # 查找确定按钮
                            for button in parent.findChildren(QPushButton):
                                if button.text() == "确定":
                                    button.click()
                                    return
                        return
                    # 处理ESC键，触发取消
                    if event.key() == Qt.Key_Escape:
                        parent = self.parent()
                        while parent and not isinstance(parent, QDialog):
                            parent = parent.parent()
                        if parent:
                            parent.close()
                        return
                    # 特殊处理空格键，避免输入法事件导致死锁
                    if event.key() == Qt.Key_Space:
                        # 直接插入空格字符，不调用父类方法
                        cursor = self.cursorPosition()
                        text = self.text()
                        new_text = text[:cursor] + ' ' + text[cursor:]
                        self.setText(new_text)
                        self.setCursorPosition(cursor + 1)
                        return
                    # 正常处理其他按键
                    super().keyPressEvent(event)
                    
                def inputMethodQuery(self, query):
                    # 重写查询方法，确保输入法正常工作
                    return super().inputMethodQuery(query)
                    
                def event(self, event):
                    # 重写event方法，特殊处理输入法相关事件
                    if event.type() == QEvent.InputMethod:
                        try:
                            # 直接处理输入法事件，不调用processEvents避免死锁
                            return super().event(event)
                        except Exception as e:
                            # print(f"输入法事件处理错误: {e}")  # [日志已禁用]
                            return False
                    return super().event(event)
            
            # 使用自定义的QLineEdit
            line_edit = CustomLineEdit()
            line_edit.setText(current_name)
            line_edit.selectAll()  # 选中所有文本，方便用户直接输入
            # 设置输入法提示，帮助处理中文输入
            line_edit.setInputMethodHints(Qt.ImhNone)  # 允许所有输入法
            layout.addWidget(line_edit)
            
            # 添加按钮
            button_layout = QHBoxLayout()
            ok_button = QPushButton("确定")
            ok_button.setFixedSize(100, 36)
            ok_button.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                background-color: #006AE0;
                }
            """)
            cancel_button = QPushButton("取消")
            cancel_button.setFixedSize(100, 36)
            cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #0A84FF;

                }
                QPushButton:pressed {
                    background-color: #0A84FF;

                }
            """)
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            
            # 连接信号 - 简化逻辑，直接让按钮点击触发重命名
            def on_ok():
                new_name = line_edit.text().strip()
                if new_name and new_name != current_name:
                    # 清理新名称中的非法字符
                    # Windows文件夹不能包含的字符
                    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
                    for char in invalid_chars:
                        new_name = new_name.replace(char, '_')
                    
                    # 获取父目录路径
                    parent_dir = os.path.dirname(folder_path)
                    # 构建新路径
                    new_path = os.path.join(parent_dir, new_name)
                    
                    # 检查新名称是否已存在
                    if os.path.exists(new_path):
                        self.show_beautiful_message('warning', '警告', f"文件夹名称 '{new_name}' 已存在，请使用其他名称。")
                        return
                    
                    # 重命名文件夹 - Python3原生支持Unicode路径
                    os.rename(folder_path, new_path)
                    
                    # 更新快捷键配置
                    if hasattr(self.parent, 'shortcuts'):
                        old_path_normalized = os.path.normpath(str(folder_path)).lower()
                        new_path_normalized = os.path.normpath(str(new_path)).lower()
                        if old_path_normalized in self.parent.shortcuts:
                            self.parent.shortcuts[new_path_normalized] = self.parent.shortcuts.pop(old_path_normalized)
                            self.parent.save_shortcut_config()
                            self.parent.update_shortcuts()
                    
                    # 刷新文件夹列表
                    self.load_folders()
                dialog.close()
                
            ok_button.clicked.connect(on_ok)
            cancel_button.clicked.connect(dialog.close)
            
            # 给对话框本身也加上键盘事件处理
            def dialog_keyPressEvent(event):
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    ok_button.click()  # 直接触发按钮点击
                    event.accept()
                    return
                if event.key() == Qt.Key_Escape:
                    cancel_button.click()  # 直接触发取消按钮
                    event.accept()
                    return
                super(QDialog, dialog).keyPressEvent(event)
            
            dialog.keyPressEvent = dialog_keyPressEvent
            
            # 给输入框设置回车键处理
            line_edit.returnPressed.connect(ok_button.click)
            
            # 显示对话框
            dialog.show()
        except Exception as e:
            self.show_beautiful_message('critical', '错误', f"重命名失败: {str(e)}")

    def _robust_move_folder(self, src, dst, max_retries=5, delay=0.5):
        """
        尽量把 src 目录树移动到 dst。
        遇到被 Windows 锁定的文件时自动重试；仍失败则跳过该文件并继续，
        避免因为单个文件被占用导致整个删除流程崩溃。
        返回未能移动的文件路径列表。
        """
        os.makedirs(dst, exist_ok=True)
        skipped = []

        for root, dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            dst_dir = os.path.join(dst, rel) if rel != '.' else dst
            os.makedirs(dst_dir, exist_ok=True)

            for name in files:
                src_file = os.path.join(root, name)
                dst_file = os.path.join(dst_dir, name)
                moved = False

                for attempt in range(max_retries):
                    try:
                        os.replace(src_file, dst_file)
                        moved = True
                        break
                    except FileNotFoundError:
                        moved = True
                        break
                    except (PermissionError, OSError) as e:
                        if getattr(e, 'winerror', None) in (5, 32) and attempt < max_retries - 1:
                            time.sleep(delay)
                            continue
                        break

                if not moved:
                    # 直接移动失败，尝试复制后删除源
                    try:
                        shutil.copy2(src_file, dst_file)
                        try:
                            os.remove(src_file)
                            moved = True
                        except Exception:
                            pass
                    except Exception:
                        pass

                if not moved:
                    skipped.append(src_file)

        # 清理 src 中已空的目录（从下往上）
        for root, dirs, files in os.walk(src, topdown=False):
            try:
                os.rmdir(root)
            except OSError:
                pass

        return skipped

    def delete_folder(self, folder_path):
        try:
            from utils import get_recordings_path

            # ★修复：删除前强力清理 _debug_failed_match 调试截图目录。
            # 这些临时调试图被图片查看器/杀毒软件/未释放句柄占用时，会导致
            # shutil.move 整个流程目录失败（WinError 5）。先带重试删除它们。
            for root, dirs, files in os.walk(folder_path, topdown=False):
                if os.path.basename(root) == '_debug_failed_match':
                    for name in files:
                        fpath = os.path.join(root, name)
                        for attempt in range(5):
                            try:
                                os.remove(fpath)
                                break
                            except (PermissionError, OSError):
                                if attempt < 4:
                                    time.sleep(0.5)
                    for attempt in range(5):
                        try:
                            os.rmdir(root)
                            break
                        except OSError:
                            if attempt < 4:
                                time.sleep(0.5)
                    dirs[:] = []

            # 创建回收站目录（如果不存在）
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            os.makedirs(trash_dir, exist_ok=True)

            # 生成唯一的目标文件夹名
            folder_name = os.path.basename(folder_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            trash_folder_name = f"{folder_name}_{timestamp}"
            trash_folder_path = os.path.join(trash_dir, trash_folder_name)

            # 移动文件夹到回收站；若整目录移动因文件被占用失败，
            # 降级为逐个文件移动，跳过被锁定的文件，避免删除流程崩溃。
            try:
                shutil.move(folder_path, trash_folder_path)
            except (PermissionError, OSError) as e:
                if getattr(e, 'winerror', None) in (5, 32):
                    skipped = self._robust_move_folder(folder_path, trash_folder_path)
                    if skipped:
                        skip_log = os.path.join(trash_folder_path, '_move_skipped_files.txt')
                        try:
                            with open(skip_log, 'w', encoding='utf-8') as f:
                                f.write("以下文件在删除时被占用，未能移入回收站：\n")
                                for p in skipped:
                                    f.write(p + '\n')
                        except Exception:
                            pass
                else:
                    raise

            # 保存删除信息到回收站索引文件
            self.update_trash_index(trash_folder_name, folder_name, folder_path)

            # 清理对应的快捷键 - 使用小写路径匹配
            if hasattr(self, 'parent') and hasattr(self.parent, 'shortcuts'):
                # 获取小写绝对路径，与保存时保持一致
                abs_target = os.path.abspath(os.path.normpath(folder_path)).lower()
                keys_to_remove = []
                
                # 找出所有匹配的快捷键路径
                for stored_path in list(self.parent.shortcuts.keys()):
                    abs_stored = os.path.abspath(os.path.normpath(stored_path)).lower()
                    if abs_stored == abs_target:
                        keys_to_remove.append(stored_path)
                
                # 删除匹配的快捷键
                for key in keys_to_remove:
                    del self.parent.shortcuts[key]

                self.parent.save_shortcut_config()
                self.parent.update_shortcuts()

            # 立即从表格中移除该文件夹行
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 1)
                if item and os.path.normpath(item.data(Qt.UserRole)) == os.path.normpath(folder_path):
                    self.table.removeRow(row)
                    break
            
            # 静默删除，不显示提示框
        except Exception as e:
            self.show_beautiful_message('critical', '错误', f"删除失败: {str(e)}")
    
    def update_trash_index(self, trash_folder_name, original_name, original_path):
        """更新回收站索引文件"""
        from utils import get_recordings_path
        recordings_dir = get_recordings_path()
        trash_dir = os.path.join(recordings_dir, 'trash')
        index_file = os.path.join(trash_dir, 'trash_index.json')
        
        # 加载现有索引
        index_data = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except Exception as e:
                # print(f"加载回收站索引失败: {e}")  # [日志已禁用]
                pass
        
        # 添加新条目
        index_data.append({
            'trash_folder_name': trash_folder_name,
            'original_name': original_name,
            'original_path': original_path,
            'deleted_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 保存索引
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # print(f"保存回收站索引失败: {e}")  # [日志已禁用]
            pass
    
    def open_trash(self):
        """打开回收站窗口"""
        dialog = QDialog(self)
        dialog.setWindowTitle("回收站")
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setStyleSheet("background: transparent; border: none;")
        screen_width, screen_height = get_screen_size()
        dialog.setMinimumSize(int(screen_width * 0.35), int(screen_height * 0.5))
        center_window(dialog)

        container = QWidget(dialog)
        container.setObjectName("trashContainer")
        container.setStyleSheet("""
            QWidget#trashContainer {
                background: #F5F5F7;
                border: 1px solid #1C1C1E;
                border-radius: 16px;
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                color: black;
            }
        """)
        layout.addWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        _header = QWidget()
        _header.setFixedHeight(44)
        _header.setStyleSheet("background-color: #1C1C1E; border-top-left-radius: 13px; border-top-right-radius: 13px; border: none;")
        _hdr_lo = QHBoxLayout(_header)
        _hdr_lo.setContentsMargins(16, 0, 16, 0)
        _hdr_lo.setSpacing(8)
        _hdr_title = QLabel("回收站")
        _hdr_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        _hdr_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: transparent; border: none;")
        _hdr_lo.addWidget(_hdr_title)
        _hdr_lo.addStretch()
        def _closeD(ev):
            if ev.button() == Qt.LeftButton: dialog.close()
        _red_dot = QFrame()
        _red_dot.setFixedSize(16, 16)
        _red_dot.setStyleSheet("background:#FF5F57; border-radius:8px; border:none;")
        _red_dot.mousePressEvent = _closeD
        _red_dot.setCursor(Qt.PointingHandCursor)
        _hdr_lo.addWidget(_red_dot)
        def _start_drag(ev):
            if ev.button() == Qt.LeftButton:
                dialog._drag_pos = ev.globalPos() - dialog.pos()
        def _do_drag(ev):
            if getattr(dialog, '_drag_pos', None) is not None and ev.buttons() & Qt.LeftButton:
                dialog.move(ev.globalPos() - dialog._drag_pos)
        _header.mousePressEvent = _start_drag
        _header.mouseMoveEvent = _do_drag
        main_layout.addWidget(_header)

        content = QWidget()
        content.setStyleSheet("background-color: #FFFFFF; border: none; border-bottom-left-radius: 13px; border-bottom-right-radius: 13px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 16)
        content_layout.setSpacing(10)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["原名称", "删除时间", "恢复", "永久删除"])
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(self.table_style + """
            QTableWidget::item { padding: 5px; margin: 0px; }
            QTableWidget::item:hover { background: transparent; }
            QTableWidget::item:nth-child(1):hover, QTableWidget::item:nth-child(2):hover {
                background: rgba(195, 240, 202, 0.3);
            }
            QTableWidget::item:focus { outline: none; selection-background-color: transparent; selection-color: #212529; }
            QTableWidget:focus { outline: none; }
            QTableWidget::item:selected { background: transparent; color: #212529; }
            QTableWidget::item:selected:!active { background: transparent; color: #212529; }
        """)
        font = table.font()
        font.setFamily("PingFang SC")
        font.setPointSize(max(9, int(screen_height * 0.01)))
        table.setFont(font)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        content_layout.addWidget(table)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.setup_trash_table_columns(table))
        table.verticalHeader().setDefaultSectionSize(max(50, int(screen_height * 0.05)))
        table.verticalHeader().setVisible(False)
        header_font = table.horizontalHeader().font()
        header_font.setPointSize(max(9, int(screen_height * 0.009)))
        header_font.setFamily("PingFang SC")
        table.horizontalHeader().setFont(header_font)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        self.load_trash_data(table)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 15, 0, 0)
        button_layout.setSpacing(20)
        clear_btn = QPushButton("清空回收站")
        clear_btn.setObjectName("clearTrashBtn")
        clear_btn.setFixedSize(110, 32)
        clear_btn.setStyleSheet("""
            QPushButton#clearTrashBtn {
                background-color: #0A84FF; color: white; border: none; border-radius: 4px;
                font-weight: bold; font-size: 12px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QPushButton#clearTrashBtn:hover { background-color: #006AE0; }
            QPushButton#clearTrashBtn:pressed { background-color: #004DB3; }
        """)
        clear_btn.clicked.connect(lambda: self.clear_trash(table))
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        content_layout.addLayout(button_layout)

        main_layout.addWidget(content)
        dialog.show()

    def load_trash_data(self, table):
        """加载回收站数据到表格"""
        from utils import get_recordings_path
        recordings_dir = get_recordings_path()
        trash_dir = os.path.join(recordings_dir, 'trash')
        index_file = os.path.join(trash_dir, 'trash_index.json')
        
        # 获取屏幕尺寸
        screen_width, screen_height = get_screen_size()
        
        # 加载索引数据
        index_data = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except Exception as e:
                # print(f"加载回收站索引失败: {e}")  # [日志已禁用]
                pass
        
        # 填充表格
        table.setRowCount(len(index_data))
        for i, item in enumerate(index_data):
            # 原名称
            name_item = QTableWidgetItem(item['original_name'])
            name_item.setTextAlignment(Qt.AlignCenter)  # 设置水平和垂直居中对齐
            name_item.setData(Qt.UserRole, item)  # 存储完整数据
            table.setItem(i, 0, name_item)
            
            # 删除时间
            time_item = QTableWidgetItem(item['deleted_time'])
            time_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 1, time_item)
            
            # 恢复按钮
            restore_btn = QPushButton("恢复")
            restore_btn.setFixedSize(80, 28)  # 减小按钮高度，避免与行高冲突
            restore_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 4px;  /* 减小圆角 */
                    font-weight: bold;
                    font-size: 11px;  /* 减小字体大小 */
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                    text-align: center;
                }
                QPushButton:hover {
                background-color: #006AE0;

                }
                QPushButton:pressed {
                background-color: #004DB3;

                }
            """)
            
            # 创建恢复按钮的容器，确保按钮在单元格中居中
            restore_container = QWidget()
            restore_container.setStyleSheet("background: transparent;")  # 设置透明背景
            restore_layout = QHBoxLayout(restore_container)
            restore_layout.setContentsMargins(5, 2, 5, 2)  # 添加适当的边距，确保按钮不贴边
            restore_layout.setSpacing(0)
            restore_layout.setAlignment(Qt.AlignCenter)
            restore_layout.addWidget(restore_btn)
            
            restore_btn.clicked.connect(lambda _, row=i, tbl=table: self.restore_from_trash(row, tbl))
            table.setCellWidget(i, 2, restore_container)
            
            # 永久删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(80, 28)  # 减小按钮高度，避免与行高冲突
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 4px;  /* 减小圆角 */
                    font-weight: bold;
                    font-size: 11px;  /* 减小字体大小 */
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                    text-align: center;
                }
                QPushButton:hover {
                background-color: #006AE0;

                }
                QPushButton:pressed {
                background-color: #004DB3;

                }
            """)
            
            # 创建删除按钮的容器，确保按钮在单元格中居中
            delete_container = QWidget()
            delete_container.setStyleSheet("background: transparent;")  # 设置透明背景
            delete_layout = QHBoxLayout(delete_container)
            delete_layout.setContentsMargins(5, 2, 5, 2)  # 添加适当的边距，确保按钮不贴边
            delete_layout.setSpacing(0)
            delete_layout.setAlignment(Qt.AlignCenter)
            delete_layout.addWidget(delete_btn)
            
            delete_btn.clicked.connect(lambda _, row=i, tbl=table: self.permanent_delete_from_trash(row, tbl))
            table.setCellWidget(i, 3, delete_container)
    
    def setup_trash_table_columns(self, table):
        """设置回收站表格列宽，填满整个窗口"""
        header = table.horizontalHeader()
        window_width = table.parent().width()
        layout_margin = 4  # 左右边距各2像素
        available_width = window_width - layout_margin
        button_width = max(90, int(available_width * 0.1))  # 按钮宽度
        remaining_width = available_width - 2 * button_width
        name_width = int(remaining_width * 0.7)  # 原名称列占70%
        time_width = remaining_width - name_width  # 删除时间列占剩余的30%
        
        header.resizeSection(0, name_width)  # 原名称
        header.resizeSection(1, time_width)  # 删除时间
        header.resizeSection(2, button_width)  # 恢复按钮列
        header.resizeSection(3, button_width)  # 永久删除按钮列
    
    def restore_from_trash(self, row, table):
        """从回收站恢复文件夹"""
        try:
            # 获取数据
            item = table.item(row, 0).data(Qt.UserRole)
            trash_folder_name = item['trash_folder_name']
            original_name = item['original_name']
            original_path = item['original_path']
            
            # 获取回收站文件夹路径
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            trash_folder_path = os.path.join(trash_dir, trash_folder_name)
            
            # 检查原路径是否可用
            if os.path.exists(original_path):
                # 如果原路径已存在，生成新名称
                base_path = os.path.dirname(original_path)
                timestamp = datetime.now().strftime('_%Y%m%d_%H%M%S')
                new_name = original_name + timestamp
                new_path = os.path.join(base_path, new_name)
                
                reply = self.show_beautiful_message('question', "路径冲突",                     f"原路径已存在，将恢复为 '{new_name}'",                     buttons=QMessageBox.Yes | QMessageBox.No,                     default_button=QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                
                original_path = new_path
            
            # 移动文件夹回原位置
            shutil.move(trash_folder_path, original_path)
            
            # 从索引中移除
            self.remove_from_trash_index(trash_folder_name)
            
            # 刷新表格
            self.load_trash_data(table)
            
            # 刷新主界面
            self.load_folders()
            
            # 静默恢复，不显示提示框
        except Exception as e:
            self.show_beautiful_message('critical', '错误', f"恢复失败: {str(e)}")
    
    def permanent_delete_from_trash(self, row, table):
        """从回收站永久删除文件夹"""
        try:
            # 创建自定义确认对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
            from PyQt5.QtCore import Qt
            
            item = table.item(row, 0).data(Qt.UserRole)
            original_name = item['original_name']
            
            confirm_dialog = QDialog(self)
            confirm_dialog.setWindowTitle("确认永久删除")
            confirm_dialog.setModal(True)
            # 设置窗口标志：移除帮助按钮，添加最小化按钮，保持置顶
            confirm_dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            
            # 应用统一的对话框样式
            apply_dialog_style(confirm_dialog, 0.3, 0.2)
            
            layout = QVBoxLayout()
            
            label = QLabel(f"确定要永久删除 '{original_name}' 吗？\n此操作不可撤销！")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            button_layout = QHBoxLayout()
            
            yes_btn = QPushButton("确定")
            yes_btn.setFixedSize(100, 36)
            yes_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {THEME_PRIMARY};
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                }}
                QPushButton:hover {{
                background-color: #006AE0;
                }}
                QPushButton:pressed {{
                background-color: #004DB3;
                }}
            """)
            button_layout.addWidget(yes_btn)
            
            no_btn = QPushButton("取消")
            no_btn.setFixedSize(100, 36)
            no_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    color: #8E8E93;
                    border: 1px solid #D1D1D6;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                }}
                QPushButton:hover {{
                    background-color: #F0F0F2;
                    color: #6E6E73;
                }}
            """)
            button_layout.addWidget(no_btn)
            
            layout.addLayout(button_layout)
            confirm_dialog.setLayout(layout)
            
            yes_btn.clicked.connect(confirm_dialog.accept)
            no_btn.clicked.connect(confirm_dialog.reject)
            
            if confirm_dialog.exec_() != QDialog.Accepted:
                return
            
            # 获取回收站文件夹路径
            trash_folder_name = item['trash_folder_name']
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            trash_folder_path = os.path.join(trash_dir, trash_folder_name)
            
            # 删除文件夹
            if os.path.exists(trash_folder_path):
                shutil.rmtree(trash_folder_path)
            
            # 从索引中移除
            self.remove_from_trash_index(trash_folder_name)
            
            # 刷新表格
            self.load_trash_data(table)
            
            # 创建自定义成功提示对话框
            success_dialog = QDialog(self)
            success_dialog.setWindowTitle("成功")
            success_dialog.setModal(True)
            # 设置窗口标志：移除帮助按钮，添加最小化按钮，保持置顶
            success_dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            
            # 应用统一的对话框样式
            apply_dialog_style(success_dialog, 0.3, 0.2)
            
            layout = QVBoxLayout()
            
            label = QLabel(f"'{original_name}' 已永久删除")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            button_layout = QHBoxLayout()
            
            ok_btn = QPushButton("确定")
            ok_btn.setFixedSize(100, 36)
            ok_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                background-color: #006AE0;
                }
            """)
            ok_btn.clicked.connect(success_dialog.accept)
            button_layout.addWidget(ok_btn)
            
            layout.addLayout(button_layout)
            success_dialog.setLayout(layout)
            
            success_dialog.exec_()
        except Exception as e:
            self.show_beautiful_message('critical', "错误", f"删除失败: {str(e, parent=self)}")
    
    def clear_trash(self, table):
        """清空回收站"""
        try:
            # 创建自定义确认对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
            from PyQt5.QtCore import Qt
            
            confirm_dialog = QDialog(self)
            confirm_dialog.setWindowTitle("确认清空回收站")
            confirm_dialog.setModal(True)
            # 设置窗口标志：移除帮助按钮，添加最小化按钮，保持置顶
            confirm_dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            
            # 应用统一的对话框样式
            apply_dialog_style(confirm_dialog, 0.3, 0.2)
            
            layout = QVBoxLayout()
            
            label = QLabel("确定要清空回收站吗？\n此操作不可撤销！")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            button_layout = QHBoxLayout()
            
            yes_btn = QPushButton("确定")
            yes_btn.setFixedSize(100, 36)
            yes_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                background-color: #006AE0;
                }
            """)
            button_layout.addWidget(yes_btn)

            no_btn = QPushButton("取消")
            no_btn.setFixedSize(100, 36)
            no_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    color: #8E8E93;
                    border: 1px solid #D1D1D6;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                }}
                QPushButton:hover {{
                    background-color: #F0F0F2;
                    color: #6E6E73;
                }}
            """)
            button_layout.addWidget(no_btn)
            
            layout.addLayout(button_layout)
            confirm_dialog.setLayout(layout)
            
            yes_btn.clicked.connect(confirm_dialog.accept)
            no_btn.clicked.connect(confirm_dialog.reject)
            
            if confirm_dialog.exec_() != QDialog.Accepted:
                return
            
            # 获取回收站路径
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            
            # 删除回收站目录中的所有内容
            if os.path.exists(trash_dir):
                for item in os.listdir(trash_dir):
                    item_path = os.path.join(trash_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
            
            # 删除索引文件
            index_file = os.path.join(trash_dir, 'trash_index.json')
            if os.path.exists(index_file):
                os.remove(index_file)
            
            # 刷新表格
            table.setRowCount(0)
            
            # 创建自定义成功提示对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
            from PyQt5.QtCore import Qt
            
            success_dialog = QDialog(self)
            success_dialog.setWindowTitle("成功")
            success_dialog.setModal(True)
            # 设置窗口标志：移除帮助按钮，添加最小化按钮，保持置顶
            success_dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            
            # 应用统一的对话框样式
            apply_dialog_style(success_dialog, 0.3, 0.2)
            
            layout = QVBoxLayout()
            
            label = QLabel("回收站已清空")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            button_layout = QHBoxLayout()
            
            ok_btn = QPushButton("确定")
            ok_btn.setFixedSize(100, 36)
            ok_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                background-color: #006AE0;
                }
            """)
            ok_btn.clicked.connect(success_dialog.accept)
            button_layout.addWidget(ok_btn)
            
            layout.addLayout(button_layout)
            success_dialog.setLayout(layout)
            
            success_dialog.exec_()
        except Exception as e:
            self.show_beautiful_message('critical', "错误", f"清空回收站失败: {str(e, parent=self)}")
    
    def remove_from_trash_index(self, trash_folder_name):
        """从回收站索引中移除指定项"""
        from utils import get_recordings_path
        recordings_dir = get_recordings_path()
        trash_dir = os.path.join(recordings_dir, 'trash')
        index_file = os.path.join(trash_dir, 'trash_index.json')
        
        # 加载现有索引
        index_data = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except Exception as e:
                # print(f"加载回收站索引失败: {e}")  # [日志已禁用]
                return
        
        # 移除指定项
        index_data = [item for item in index_data if item['trash_folder_name'] != trash_folder_name]
        
        # 保存索引
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # print(f"保存回收站索引失败: {e}")  # [日志已禁用]
            pass

    def load_delete_confirm_setting(self):
        """加载删除确认设置"""
        if not hasattr(self, 'parent') or not self.parent or not hasattr(self.parent, 'user_data_dir') or not hasattr(self.parent, 'current_user'):
            return

        config_path = os.path.join(self.parent.user_data_dir, f'delete_confirm_{self.parent.current_user}.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.confirm_delete_checkbox.setChecked(not config.get('confirm_delete', True))
            else:
                self.confirm_delete_checkbox.setChecked(True)
        except Exception as e:
            # print(f"加载删除确认设置失败: {e}")  # [日志已禁用]
            self.confirm_delete_checkbox.setChecked(True)

    def save_delete_confirm_setting(self):
        """保存删除确认设置"""
        if not hasattr(self, 'parent') or not self.parent or not hasattr(self.parent, 'user_data_dir') or not hasattr(self.parent, 'current_user'):
            return

        config_path = os.path.join(self.parent.user_data_dir, f'delete_confirm_{self.parent.current_user}.json')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'confirm_delete': not self.confirm_delete_checkbox.isChecked()}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # print(f"保存删除确认设置失败: {e}")  # [日志已禁用]
            pass

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件，使点击文件夹名称列直接打开查看画面"""
        # 检查是否点击的是文件夹名称列（第1列，索引为1）
        if column == 1:
            # 获取文件夹路径
            item = self.table.item(row, column)
            if item:
                folder_path = item.data(Qt.UserRole)
                if folder_path and os.path.exists(folder_path):
                    # 直接调用view_images方法打开查看画面
                    self.view_images(folder_path)

    def show_context_menu(self, position):
        """显示右键菜单"""
        row = self.table.rowAt(position.y())
        col = self.table.columnAt(position.x())
        
        if row >= 0:
            name_item = self.table.item(row, 1)
            if name_item:
                folder_path = name_item.data(Qt.UserRole)
                folder_name = name_item.text()
                if folder_path and os.path.exists(folder_path):
                    usage_counts = {}
                    if hasattr(self, 'parent') and self.parent:
                        usage_counts = self.parent._get_usage_counts()
                    count = usage_counts.get(folder_name, 0)
                    
                    menu = QMenu(self)
                    
                    count_action = menu.addAction(f"已执行 {count} 次")
                    count_action.setEnabled(False)
                    menu.addSeparator()
                    
                    interval_action = QAction("设置默认间隔", self)
                    interval_action.triggered.connect(lambda: self.set_folder_interval(folder_path))
                    menu.addAction(interval_action)
                    
                    delete_action = QAction("删除", self)
                    delete_action.triggered.connect(lambda: self.delete_folder(folder_path))
                    menu.addAction(delete_action)
                    
                    menu.exec_(self.table.viewport().mapToGlobal(position))

    def set_folder_interval(self, folder_path):
        """设置流程文件夹的默认操作间隔（秒）"""
        folder_name = os.path.basename(folder_path)
        current_interval = self.parent.folder_intervals.get(folder_path, self.parent.replay_interval)

        from PyQt5.QtWidgets import QDoubleSpinBox

        dialog = QDialog(self)
        dialog.setWindowTitle("设置默认间隔")
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        width, height = get_screen_size(0.3)
        dialog.resize(width, int(height * 0.32))
        dialog.setWindowModality(Qt.WindowModal)
        dialog.activateWindow()
        apply_dialog_style(dialog, 0.3, 0.32)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        screen_width, screen_height = get_screen_size()

        instruction_label = QLabel(f"设置流程「{folder_name}」的默认操作间隔")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_font_size = int(screen_height * 0.025)
        instruction_label.setStyleSheet(f"font-size: {instruction_font_size}px; color: #0A84FF; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(instruction_label)

        spin = QDoubleSpinBox()
        spin.setRange(0.0, 10.0)
        spin.setSingleStep(0.01)
        spin.setDecimals(3)
        try:
            spin.setValue(float(current_interval))
        except (TypeError, ValueError):
            spin.setValue(0.001)
        spin.setSuffix(" 秒")
        spin_font_size = int(screen_height * 0.03)
        spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                font-size: {spin_font_size}px;
                padding: 8px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: white;
                min-height: 35px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QDoubleSpinBox:focus {{ border-color: #0A84FF; }}
        """)
        layout.addWidget(spin)

        hint_label = QLabel("每个操作之间默认等待的秒数。设为 0 表示几乎无间隔；"
                            "若某个操作单独设置了延迟，会优先使用它单独的值。")
        hint_label.setWordWrap(True)
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet(f"font-size: {int(screen_height*0.018)}px; color: #666; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(hint_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(100, 36)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover { background-color: #0A84FF; }
            QPushButton:pressed { background-color: #0A84FF; }
        """)
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover { background-color: #0A84FF; }
            QPushButton:pressed { background-color: #0A84FF; }
        """)
        button_layout.addStretch(1)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)

        def on_ok():
            val = round(float(spin.value()), 3)
            self.parent.folder_intervals[folder_path] = val
            self.parent.save_interval_config()
            dialog.accept()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()

    def on_table_show(self, event):
        """表格显示事件处理，确保按钮正确对齐"""
        super().showEvent(event)
        # 延迟一点时间再更新按钮位置，确保表格已经完全显示
        QTimer.singleShot(100, self.update_button_positions)

    def on_column_resized(self, logicalIndex, oldSize, newSize):
        """当列宽改变时更新按钮位置"""
        # 立即更新按钮位置，不依赖定时器
        self.update_button_positions()
        # 重绘表格以确保显示正确
        self.table.viewport().update()

    def update_button_positions(self):
        """更新所有按钮的大小和位置"""
        screen_width, screen_height = get_screen_size()
        btn_height = int(screen_height * 0.03)
        btn_width = 50
        
        for row in range(self.table.rowCount()):
            rename_container = self.table.cellWidget(row, 3)
            delete_container = self.table.cellWidget(row, 4)
            shortcut_container = self.table.cellWidget(row, 2)
            
            for container in [rename_container, delete_container]:
                if container:
                    btn = container.findChild(QPushButton)
                    if btn:
                        btn.setFixedSize(btn_width, btn_height)
                        layout = container.layout()
                        if layout:
                            layout.setContentsMargins(0, 0, 0, 0)
                            layout.setAlignment(Qt.AlignCenter)
            
            if shortcut_container:
                shortcut_btn = shortcut_container.findChild(QPushButton)
                if shortcut_btn:
                    _s_text = shortcut_btn.text()
                    _s_fm = QFontMetrics(shortcut_btn.font())
                    _s_tw = _s_fm.horizontalAdvance(_s_text) if hasattr(_s_fm, 'horizontalAdvance') else _s_fm.width(_s_text)
                    shortcut_btn.setFixedSize(max(60, _s_tw + 20), btn_height)
                    layout = shortcut_container.layout()
                    if layout:
                        layout.setContentsMargins(0, 0, 0, 0)
                        layout.setAlignment(Qt.AlignCenter)

    def update_shortcut_button_text(self, folder_path, shortcut):
        """更新快捷键按钮的文本"""
        target_path = os.path.normpath(str(folder_path)).lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item:
                item_path = os.path.normpath(str(item.data(Qt.UserRole))).lower()
                if item_path == target_path:
                    # 获取快捷键容器
                    shortcut_container = self.table.cellWidget(row, 2)
                    if shortcut_container:
                        # 从容器中获取按钮
                        shortcut_btn = shortcut_container.findChild(QPushButton)
                        if shortcut_btn:
                            shortcut_btn.setText(shortcut if shortcut else "快捷键")
                            # 根据新文本调整按钮宽度
                            text = shortcut if shortcut else "快捷键"
                            _u_fm = QFontMetrics(shortcut_btn.font())
                            _u_tw = _u_fm.horizontalAdvance(text) if hasattr(_u_fm, 'horizontalAdvance') else _u_fm.width(text)
                            button_width = max(60, min(_u_tw + 20, 150))
                            shortcut_btn.setFixedWidth(button_width)
                    break

    def set_shortcut(self, folder_path):
        folder_name = os.path.basename(folder_path)
        current_shortcut = self.parent.shortcuts.get(folder_path, "")

        # 临时禁用·键的全局快捷键，避免冲突
        self.parent.temporarily_disable_grave_hotkey()

        dialog = QDialog(self)
        dialog.setWindowTitle("设置快捷键")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        # 按比例设置对话框大小
        width, height = get_screen_size(0.3)  # 减小窗口大小比例
        dialog.resize(width, int(height * 0.25))  # 减小窗口高度比例

        dialog.setWindowModality(Qt.WindowModal)

        # 拦截 F1 触发的系统“帮助”事件（Windows 下 F1 会被系统抢走焦点/弹帮助，
        # 导致 F1、F2 等功能键组合录不进弹窗）。拦截后 F1 能干净进入 keyPressEvent 录入。
        from PyQt5.QtCore import QObject, QEvent

        class _F1HelpBlocker(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Help:
                    event.accept()
                    return True
                return False

        _help_blocker = _F1HelpBlocker(dialog)
        dialog.installEventFilter(_help_blocker)
        dialog._help_blocker_ref = _help_blocker  # 保持引用，防止被 GC
        dialog.activateWindow()

        # 应用统一的对话框样式
        apply_dialog_style(dialog, 0.3, 0.25)

        layout = QVBoxLayout()
        layout.setSpacing(15)  # 减小间距
        layout.setContentsMargins(25, 20, 25, 20)  # 减小边距

        # 按屏幕比例设置字体大小
        screen_width, screen_height = get_screen_size()

        instruction_label = QLabel("请按下快捷键组合...")
        instruction_label.setAlignment(Qt.AlignCenter)
        # 按屏幕比例设置字体大小
        instruction_font_size = int(screen_height * 0.025)  # 屏幕高度的2.5%
        instruction_label.setStyleSheet(f"font-size: {instruction_font_size}px; color: #0A84FF; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")  # 动态字体大小
        layout.addWidget(instruction_label)

        shortcut_label = QLabel(current_shortcut if current_shortcut else "未设置")
        shortcut_label.setAlignment(Qt.AlignCenter)
        # 按屏幕比例设置字体大小
        shortcut_font_size = int(screen_height * 0.03)  # 屏幕高度的3%
        shortcut_label.setStyleSheet(f"""
            font-size: {shortcut_font_size}px;
            font-weight: bold;
            padding: 8px;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            background-color: white;
            min-height: 35px;
            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
        """)
        layout.addWidget(shortcut_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)  # 减小按钮间距
        clear_btn = QPushButton("清除")
        clear_btn.setFixedSize(100, 36)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #0A84FF;
                
            }
            QPushButton:pressed {
                background-color: #0A84FF;
                
            }
        """)
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(100, 36)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #0A84FF;
                
            }
            QPushButton:pressed {
                background-color: #0A84FF;
                
            }
        """)
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #0A84FF;
                
            }
            QPushButton:pressed {
                background-color: #0A84FF;
                
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        # 存储当前按下的键
        current_keys = []

        def clear_shortcut():
            nonlocal current_keys
            current_keys = []
            shortcut_label.setText("")

        def keyPressEvent(event):
            # 忽略系统自动重复，避免重复录入
            if getattr(event, 'isAutoRepeat', None) and event.isAutoRepeat():
                return

            key = event.key()

            # 忽略单独的修饰键本身（只按修饰键不计入组合）
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return

            # 将按键转换为可读名称（字母/数字统一小写，便于阅读与热键注册）
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

            # 当前按住的修饰键（不再强制要求必须有修饰键，任意键均可自由组合）
            mods = []
            if event.modifiers() & Qt.ControlModifier:
                mods.append("Ctrl")
            if event.modifiers() & Qt.AltModifier:
                mods.append("Alt")
            if event.modifiers() & Qt.ShiftModifier:
                mods.append("Shift")

            token = "+".join(mods + [key_name])

            # 在上一次组合基础上累积，支持任意 2~3 个键自由组合（如 c+2、1+2、shift+a+b）
            existing = current_keys[-1].split("+") if current_keys else []
            if token in existing:
                return  # 同一按键不重复计入
            existing.append(token)
            if len(existing) > 3:
                existing = existing[:3]
            combo = "+".join(existing)
            shortcut_label.setText(combo)
            current_keys.append(combo)

        # 连接信号
        clear_btn.clicked.connect(clear_shortcut)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        # 重写键盘事件
        dialog.keyPressEvent = keyPressEvent

        result = dialog.exec_()
        
        # 重新启用·键的全局快捷键
        self.parent.reenable_grave_hotkey()
        
        if result == QDialog.Accepted and current_keys:
            shortcut = current_keys[-1]  # 取最后一次输入的

            # 检查是否已被使用，同时清理无效路径
            invalid_paths = []
            normalized_folder_path = os.path.normpath(str(folder_path))
            for path, existing_shortcut in self.parent.shortcuts.items():
                if not os.path.exists(path):
                    invalid_paths.append(path)
                    continue
                normalized_path = os.path.normpath(path)
                if existing_shortcut == shortcut and normalized_path != normalized_folder_path:
                    self.parent.show_beautiful_message('warning', "警告", f"快捷键 '{shortcut}' 已被其他流程使用", parent=self)
                    return

            # 检查是否与组合技停止快捷键冲突
            if shortcut:
                from combo_skill_manager import ComboSkillManager
                combo_manager = ComboSkillManager(self.parent)
                for skill in combo_manager.combo_skills:
                    if skill.get('stop_shortcut') == shortcut:
                        self.parent.show_beautiful_message('warning', "警告", f"快捷键 '{shortcut}' 已被组合技「{skill.get('name')}」的停止快捷键使用", parent=self)
                        return

            # 清理无效路径
            for invalid_path in invalid_paths:
                del self.parent.shortcuts[invalid_path]

            # 规范化路径后再保存快捷键，使用小写格式确保一致性
            normalized_path = os.path.normpath(str(folder_path)).lower()
            self.parent.shortcuts[normalized_path] = shortcut
            self.parent.save_shortcut_config()
            self.parent.update_shortcuts()
            # 静默更新，不显示提示框
            self.update_shortcut_button_text(normalized_path, shortcut)
        elif result == QDialog.Accepted and not current_keys:
            # 清除快捷键 - 使用规范化路径匹配，使用小写格式确保一致性
            normalized_path = os.path.normpath(str(folder_path)).lower()
            keys_to_remove = []
            for stored_path in self.parent.shortcuts.keys():
                if os.path.normpath(stored_path).lower() == normalized_path:
                    keys_to_remove.append(stored_path)
            for key in keys_to_remove:
                del self.parent.shortcuts[key]
            self.parent.save_shortcut_config()
            self.parent.update_shortcuts()
            # 静默清除，不显示提示框
            self.update_shortcut_button_text(normalized_path, "")
    
    def resizeEvent(self, event):
        """处理窗口大小变化事件，确保表格列宽自适应"""
        super().resizeEvent(event)
        
        # 获取当前窗口宽度
        window_width = self.width()
        
        # 重新计算按钮宽度（按窗口宽度的8%，最小60像素）
        button_width = max(60, int(window_width * 0.08))
        
        # 更新按钮列的宽度
        header = self.table.horizontalHeader()
        header.resizeSection(2, button_width)  # 查看按钮
        header.resizeSection(3, button_width)  # 重命名按钮
        header.resizeSection(4, button_width)  # 删除按钮
        
        # 更新按钮位置
        self.update_button_positions()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.parent:
            self.parent.is_folder_manager_open = False
        event.accept()


class RoundedPillButton(QPushButton):
    """自绘 iOS 药丸形按钮 - paintEvent 保证完美胶囊形状"""
    def __init__(self, text="", bg_color="#0A84FF", text_color="white", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False
        self._pressed = False
        self._bg_color = bg_color
        self._text_color = text_color
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def enterEvent(self, event):
        self._hovered = True; self.update(); super().enterEvent(event)
    def leaveEvent(self, event):
        self._hovered = False; self._pressed = False; self.update(); super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self._pressed = True; self.update()
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        self._pressed = False; self.update(); super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(2, 2, self.width() - 4, self.height() - 4)
        radius = r.height() / 2.0
        col = QColor(self._bg_color)
        if self._pressed: col = col.darker(130)
        elif self._hovered: col = col.lighter(115)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(col))
        painter.drawRoundedRect(r, radius, radius)
        painter.setPen(QColor(self._text_color))
        f = QFont("PingFang SC", 13)
        f.setWeight(QFont.Medium)
        painter.setFont(f)
        f2 = QFont("PingFang SC", 9)
        f2.setWeight(QFont.Normal)
        painter.setFont(f2)
        painter.drawText(r, Qt.AlignCenter, self.text())

class _FolderTableCtxFilter(QObject):
    """右键事件过滤器：直接拦截 folder_table 的右键事件并弹出菜单。
    比依赖 customContextMenuRequested 信号更稳——不受表格内部子控件/信号细节影响。"""

    def __init__(self, table, handler):
        super().__init__(table)
        self._table = table
        self._handler = handler

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ContextMenu:
            # 全局坐标 -> 视口坐标，交给菜单处理器
            pos = self._table.viewport().mapFromGlobal(event.globalPos())
            try:
                self._handler(pos, self._table)
            except Exception:
                import traceback
                traceback.print_exc()
            return True  # 拦截，避免再触发默认右键/信号
        return super().eventFilter(obj, event)


class AutoRecorderApp(QMainWindow):
    log_signal = pyqtSignal(str)
    
    def __init__(self, username=None, login_manager=None):
        super().__init__()
        
        self.recording_dir = None
        from login_manager import LoginManager
        self.login_manager = login_manager if login_manager else LoginManager()
        self.current_user = username
        self.current_recording_dir = None
        self.replay_interval = 0.001  # 操作间隔1毫秒
        # 图像匹配超时时间（秒）：至少要 1.5s 才能确保小图标有足够时间匹配
        self.replay_timeout = 2.0
        self._replay_lock = threading.Lock()  # ★ 多线程回放互斥锁
        self._reinitializing = False  # ★ 热键重初始化标志（含超时检测，防止卡死）
        self._hotkeys_temporarily_disabled = False  # ★ 回放期间临时禁用热键标志（不清空字典）
        self.replay_enabled = False  # 回放功能开关（默认关闭）
        self.shortcuts = {}
        self.folder_intervals = {}  # 文件夹默认操作间隔(秒): folder_path -> interval
        self.shortcut_objects = []
        self.alt_press_count = 0  # ALT键按下次数
        self.alt_press_time = 0  # ALT键按下时间
        self.debug_mode = False  # ★ 调试模式默认关闭！开启后每步剪贴板I/O+大量日志会让回放慢3-5倍
        # 需要排查问题时再通过 设置→调试模式 手动打开
        
        self.runners = {}  # 存储多个并行执行的组合技runner
        
        from utils import get_user_data_path
        self.user_data_dir = get_user_data_path()
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        self.initUI()
        self.log_signal.connect(self._append_log_impl)
        
        # 窗口先显示，非关键初始化延后执行
        QTimer.singleShot(0, self._lazy_init)
    
    
    def _lazy_init(self):
        """延后初始化：窗口显示后再加载配置和注册热键"""
        self.load_shortcut_config()
        self.load_interval_config()
        # 修复：加载快捷键后立即刷新流程表格
        if hasattr(self, "manager_tab") and hasattr(self.manager_tab, "folder_table"):
            self.load_folders_to_table(self.manager_tab.folder_table)
        self.load_debug_mode_setting()
        self.is_folder_manager_open = False
        self.update_shortcuts()
        self.register_record_hotkey()
        self.register_stop_replay_hotkey()
        self._start_hotkey_health_check()
        self.load_font_size_setting()
        if hasattr(self, 'status_label') and self.current_user:
            self.status_label.setText(f"当前用户: {self.current_user}")
    def show_beautiful_message(self, msg_type, title, text, buttons=None, default_button=None, parent=None):
        """显示美化的消息框 - 直接使用 StyledMessageDialog（粉红色风格）"""
        from beautiful_dialog import StyledMessageDialog
        from PyQt5.QtWidgets import QMessageBox

        if parent is None:
            parent = self

        # 按钮类型映射
        if buttons is not None:
            if buttons & QMessageBox.Yes and buttons & QMessageBox.No and buttons & QMessageBox.Cancel:
                btn_str = "yes_no_cancel"
            elif buttons & QMessageBox.Yes and buttons & QMessageBox.No:
                btn_str = "yes_no"
            elif buttons & QMessageBox.Ok and buttons & QMessageBox.Cancel:
                btn_str = "ok_cancel"
            else:
                btn_str = "ok"
        elif msg_type == "question":
            btn_str = "yes_no"
        else:
            btn_str = "ok"

        dialog = StyledMessageDialog(parent, title=title, text=text, msg_type=msg_type, buttons=btn_str)
        dialog.exec_()
        result = dialog.get_result()

        result_map = {
            StyledMessageDialog.OK: QMessageBox.Ok,
            StyledMessageDialog.CANCEL: QMessageBox.Cancel,
            StyledMessageDialog.YES: QMessageBox.Yes,
            StyledMessageDialog.NO: QMessageBox.No,
        }
        return result_map.get(result, QMessageBox.No)

    def showEvent(self, event):
        super().showEvent(event)
        
        # 确保窗口居中显示（防止某些系统偏移）
        if not hasattr(self, '_centered'):
            self._centered = True
            desktop = QApplication.desktop()
            available_rect = desktop.availableGeometry()
            
            width = self.width()
            height = self.height()
            
            screen_center_x = available_rect.x() + available_rect.width() // 2
            screen_center_y = available_rect.y() + available_rect.height() // 2
            
            x = screen_center_x - width // 2
            y = screen_center_y - height // 2
            
            self.move(x, y)
        
        if not hasattr(self, 'replay_status_widget'):
            self.create_replay_status_indicator()
        elif hasattr(self, 'replay_status_label'):
            self.update_replay_status_indicator()
        # 主窗口显示时，不自动显示悬浮窗口（两者互斥）
        # if hasattr(self, 'replay_status_widget'):
        #     self.replay_status_widget.show()
    
    def closeEvent(self, event):
        """窗口关闭事件 - 清理资源防止内存泄露"""
        # 停止所有定时器
        if hasattr(self, 'replay_timer') and self.replay_timer:
            self.replay_timer.stop()
        if hasattr(self, 'status_timer') and self.status_timer:
            self.status_timer.stop()
        if hasattr(self, '_hotkey_health_timer') and self._hotkey_health_timer:
            self._hotkey_health_timer.stop()

        # 清理快捷键
        if hasattr(self, 'registered_shortcuts'):
            for hotkey_id in self.registered_shortcuts:
                try:
                    keyboard.remove_hotkey(hotkey_id)
                except:
                    pass
            self.registered_shortcuts.clear()

        # 清理文件夹快捷键
        if hasattr(self, 'shortcut_objects'):
            for hotkey_id in self.shortcut_objects:
                try:
                    keyboard.remove_hotkey(hotkey_id)
                except:
                    pass
            self.shortcut_objects.clear()

        # 清理录制热键
        if hasattr(self, 'grave_hotkey_id') and self.grave_hotkey_id:
            try:
                keyboard.remove_hotkey(self.grave_hotkey_id)
            except:
                pass

        # 清理停止回放热键
        if hasattr(self, 'stop_replay_hotkey_id') and self.stop_replay_hotkey_id:
            try:
                keyboard.remove_hotkey(self.stop_replay_hotkey_id)
            except:
                pass

        # 隐藏托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
        
        # 清理悬浮窗口
        if hasattr(self, 'replay_status_widget') and self.replay_status_widget:
            self.replay_status_widget.close()
            self.replay_status_widget.deleteLater()
        
        # 清理组合技刷新定时器
        if hasattr(self, '_combo_refresh_timer') and self._combo_refresh_timer:
            self._combo_refresh_timer.stop()
            self._combo_refresh_timer.deleteLater()
        
        # 清理选择覆盖层
        if hasattr(self, 'selection_overlay') and self.selection_overlay:
            self.selection_overlay.close()
            self.selection_overlay.deleteLater()
        
        event.accept()

    # -------------------- 图片网格相关公用方法 --------------------
    def screen_size(self):
        """返回屏幕可用宽高，避免重复计算"""
        return QApplication.primaryScreen().availableGeometry()

    def paste_image(self, dialog, folder_path, grid_layout):
        """粘贴剪贴板图片到录制步骤"""
        from PIL import ImageGrab
        image = ImageGrab.grabclipboard()
        if image is None:
            self.show_beautiful_message('information', '提示', '剪贴板中没有图片', parent=dialog)
            return

    def clear_layout(self, layout):
        """清空布局中的所有控件"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    widget = item.widget()
                    # 递归清理子布局
                    if hasattr(widget, 'layout') and widget.layout():
                        self.clear_layout(widget.layout())
                    widget.deleteLater()
                elif item.layout():
                    self.clear_layout(item.layout())
                    # 删除子布局
                    item.layout().deleteLater()

    def create_image_grid(self, grid_layout, folder_path, parent_widget, dialog=None, step_action_map=None, max_cols=None):
        """创建图片网格布局的共用函数"""
        self.clear_layout(grid_layout)
        image_files = self.get_image_files(folder_path)
        if not image_files:
            return
        step_images = []
        for file_path in image_files:
            step_number = self._extract_step_number(os.path.basename(file_path))
            if step_number:
                step_images.append((step_number, file_path))
        step_images.sort(key=lambda x: x[0])
        if step_action_map is None:
            step_action_map = self.get_step_action_map(folder_path)
        if max_cols is None:
            max_cols = max(2, min(6, int(self.screen_size().width() * 0.75 / 200)))
        row, col = 0, 0
        for step_num, img_path in step_images:
            container = DraggableImageWidget(self, parent_widget, step_num=step_num,
                                           img_path=img_path, folder_path=folder_path, dialog=dialog)
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(10, 10, 10, 10)
            vbox.setSpacing(8)
            img_container = QWidget()
            # 图像容器按屏幕比例计算大小
            img_container_size = int(self.screen_size().width() * 0.12)  # 屏幕宽度的12%
            img_container.setFixedSize(img_container_size, img_container_size)
            # 获取屏幕尺寸并计算动态圆角
            screen_width, screen_height = get_screen_size()
            img_border_radius = get_dynamic_radius("image", screen_height)  # 图像容器圆角
            # 使用优雅的 hover-show 关闭按钮（macOS Photos 风格）
            # 按钮大小按图像容器大小的 14% 计算，限制在 20-30 像素之间
            del_btn_size = max(20, min(30, int(img_container_size * 0.14)))
            del_btn = _create_hover_close_button(
                img_container,
                on_click=lambda _, p=img_path, f=folder_path: self.delete_image_from_grid(p, f),
                size=del_btn_size
            )
            del_btn.move(img_container_size - del_btn_size - 2, 2)
            del_btn.raise_()
            img = load_qimage(img_path)
            if img is not None:
                size = int(self.screen_size().width() * 0.12)
                scaled_img = img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl = QLabel(img_container)
                pixmap = QPixmap.fromImage(scaled_img)
                lbl.setPixmap(pixmap)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
                lbl.move(10, 10)
                lbl.lower()
                vbox.addWidget(img_container, alignment=Qt.AlignCenter)
                img_container.installEventFilter(container)
                # 清理临时图片对象
                scaled_img = None
                img = None
            op_type = {'left_click': 'Click', 'right_click': '右击',
                       'keyboard': '键盘输入', 'double_click': '双击', 'drag': '拖拽'}.get(
                step_action_map.get(step_num, 'left_click'), 'Click')
            btn = QPushButton(f"{op_type} {step_num}")
            btn.setFixedHeight(24)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("step_num", step_num)
            btn.setProperty("img_path", img_path)
            btn.setProperty("folder_path", folder_path)
            btn.setProperty("current_action_type", step_action_map.get(step_num, 'left_click'))
            btn.clicked.connect(lambda _, b=btn: self.show_action_type_menu(b))
            # 操作类型按钮 - iOS 药丸风格
            step_actual = step_action_map.get(step_num, 'left_click')
            btn_colors = {'left_click': '#8E8E93', 'right_click': '#8E8E93',
                         'double_click': '#8E8E93', 'keyboard': '#0A84FF', 'drag': '#8E8E93'}
            pill_color = btn_colors.get(step_actual, '#8E8E93')
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {pill_color};
                    color: white;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 0 12px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: #0A84FF;
                }}
                QPushButton:pressed {{
                    background-color: #004DB3;
                }}
            """)
            vbox.addWidget(btn)
            grid_layout.addWidget(container, row, col)
            col += 1
            if col >= max_cols:
                col, row = 0, row + 1

    def view_folder_images(self, row, folder_path):
        """查看文件夹中的所有图片"""
        folder_name = self.table.item(row, 1).text()
        dialog = QDialog(self)
        dialog.setWindowTitle(f"查看录制图片 - {folder_name}")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        scr = self.screen_size()
        dialog.setMinimumSize(int(scr.width() * 0.8), int(scr.height() * 0.8))
        layout = QVBoxLayout(dialog)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        grid = QGridLayout(content)
        imgs = self.get_image_files(folder_path)
        if not imgs:
            layout.addWidget(QLabel("该文件夹中没有图片文件"))
        else:
            self.create_image_grid(grid, folder_path, content, dialog)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        QShortcut(QKeySequence('Ctrl+V'), dialog).activated.connect(
            lambda: self.paste_image(dialog, folder_path, grid))
        btn_box = QHBoxLayout()
        btn_box.addWidget(QPushButton("关闭", clicked=dialog.close))
        layout.addLayout(btn_box)

        # ★ 保存引用，给删除图片后的 refresh_view_images 用（防止闪退！）
        self._view_images_dialog = dialog
        self._view_images_grid_layout = grid
        # 兼容 folder_manager 上的访问（两套refresh都要用）
        if hasattr(self, 'folder_manager') and self.folder_manager:
            self.folder_manager._view_images_dialog = dialog
            self.folder_manager._view_images_grid_layout = grid

        # 对话框关闭时清理资源
        def _on_cleanup(*a, _dlg=dialog, _g=grid):
            try: self._cleanup_view_dialog(_dlg, _g)
            except: pass
            # 清理引用
            if getattr(self, '_view_images_dialog', None) is _dlg:
                self._view_images_dialog = None
            if getattr(self, '_view_images_grid_layout', None) is _g:
                self._view_images_grid_layout = None
            try:
                fm = getattr(self, 'folder_manager', None)
                if fm and getattr(fm, '_view_images_dialog', None) is _dlg:
                    fm._view_images_dialog = None
                if fm and getattr(fm, '_view_images_grid_layout', None) is _g:
                    fm._view_images_grid_layout = None
            except: pass
        dialog.finished.connect(_on_cleanup)
        
        dialog.show()
    
    def _cleanup_view_dialog(self, dialog, grid_layout):
        """清理查看图片对话框的资源"""
        # 清理网格布局中的所有控件
        self.clear_layout(grid_layout)
        # 强制垃圾回收
        import gc
        gc.collect()

    def _swap_steps(self, idx_a, idx_b, folder_path):
        try:
            recording_json_path = os.path.join(folder_path, 'recording.json')
            recording_data = []
            if os.path.exists(recording_json_path):
                recording_data = load_json_data(recording_json_path)
            if not isinstance(recording_data, list) or len(recording_data) < 2:
                return
            recording_data.sort(key=lambda x: x.get('step', 0))
            
            # ★ 修复：UI 列表只显示有图片的操作，但 recording_data 包含所有操作
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
            image_files.sort(key=lambda x: int(re.search(r'操作(\d+)', x).group(1)) if re.search(r'操作(\d+)', x) else 0)
            if idx_a >= len(image_files) or idx_b >= len(image_files):
                return
            match_a = re.search(r'操作(\d+)', image_files[idx_a])
            match_b = re.search(r'操作(\d+)', image_files[idx_b])
            if not match_a or not match_b:
                return
            step_a = int(match_a.group(1))
            step_b = int(match_b.group(1))
            
            rec_a_idx = rec_b_idx = None
            for i, rec in enumerate(recording_data):
                if rec.get('step') == step_a:
                    rec_a_idx = i
                if rec.get('step') == step_b:
                    rec_b_idx = i
            if rec_a_idx is None or rec_b_idx is None:
                return
            
            recording_data[rec_a_idx], recording_data[rec_b_idx] = recording_data[rec_b_idx], recording_data[rec_a_idx]
            for i, rec in enumerate(recording_data):
                rec['step'] = i + 1
                if 'image' in rec:
                    rec['image'] = f"操作{i + 1}.png"
            save_json_data(recording_json_path, recording_data)
            
            img_a = os.path.join(folder_path, f"操作{step_a}.png")
            img_b = os.path.join(folder_path, f"操作{step_b}.png")
            img_a_tmp = os.path.join(folder_path, f"操作{step_a}_tmp.png")
            if os.path.exists(img_a) and os.path.exists(img_b):
                os.rename(img_a, img_a_tmp)
                os.rename(img_b, img_a)
                os.rename(img_a_tmp, img_b)
            elif os.path.exists(img_a) and not os.path.exists(img_b):
                os.rename(img_a, img_b)
            elif os.path.exists(img_b) and not os.path.exists(img_a):
                os.rename(img_b, img_a)
            if idx_a < len(self.image_actions) and idx_b < len(self.image_actions):
                self.image_actions[idx_a], self.image_actions[idx_b] = self.image_actions[idx_b], self.image_actions[idx_a]
            self.refresh_view_images(folder_path)
        except Exception as e:
            self.show_beautiful_message('critical', "错误", f"交换步骤失败: {str(e)}")

    def refresh_view_images(self, folder_path):
        if hasattr(self, 'folder_manager') and hasattr(self.folder_manager, '_view_images_dialog') and self.folder_manager._view_images_dialog:
            dialog = self.folder_manager._view_images_dialog
            if not hasattr(self, '_view_images_grid_layout'):
                return
            list_layout = self._view_images_grid_layout
            while list_layout.count():
                item = list_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            self.folder_manager._populate_unified_rows(dialog, folder_path, list_layout)
    def delete_image_from_grid(self, img_path, folder_path):
        """从图片网格中删除指定图片"""
        if not os.path.exists(img_path):
            return
        fname = os.path.basename(img_path)
        
        confirm_dialog = QDialog(self)
        confirm_dialog.setWindowTitle("确认删除")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        confirm_dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        confirm_dialog.setAttribute(Qt.WA_TranslucentBackground)
        confirm_dialog.setFixedSize(300, 120)
        layout = QVBoxLayout(confirm_dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        label = QLabel(f"确定要删除 '{fname}' 吗？\n这将重新排序后续图片。")
        layout.addWidget(label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(60, 28)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_PRIMARY};
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumSize(60, 28)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: {CARD};
                border-color: {ACCENT};
                color: {ACCENT};
            }}
        """)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        ok_btn.clicked.connect(confirm_dialog.accept)
        cancel_btn.clicked.connect(confirm_dialog.reject)
        
        if confirm_dialog.exec_() != QDialog.Accepted:
            return
        try:
            m = re.search(r'操作(\d+)', fname)
            if not m:
                self.show_beautiful_message('critical', "错误", "无法从文件名中提取步骤号", parent=self)
                return
            del_step = int(m.group(1))
            json_path = os.path.join(folder_path, 'recording.json')
            data = load_json_data(json_path, []) if os.path.exists(json_path) else []
            if not isinstance(data, list):
                data = []

            # --- 策略：找到该图片对应的步骤条目 ---
            # 先定位 data 中【正好使用了这张图片】的步骤索引（不是step==del_step，因为键盘无图步骤的step和图片编号会错开）
            target_data_idx = None
            for idx, d in enumerate(data):
                if d.get('image') == fname:
                    target_data_idx = idx
                    break
            # 没找到匹配image字段的，兜底：按step找（老版本/异常情况）
            if target_data_idx is None:
                for idx, d in enumerate(data):
                    if d.get('step') == del_step:
                        target_data_idx = idx
                        break

            # 1) 先删磁盘文件
            if os.path.exists(img_path):
                os.remove(img_path)

            # 2) 处理 JSON：两种情况
            if target_data_idx is not None:
                target_entry = data[target_data_idx]
                # 如果该条目是【纯图片点击】（没有键盘key等且action_type是click）→ 整个条目删除
                # 如果该条目还有键盘等其他信息 → 仅移除image字段，保留坐标/键盘动作
                is_pure_image_click = (
                    'image' in target_entry
                    and target_entry.get('action_type') in ('left_click', 'right_click', 'double_click', 'middle_click', 'drag')
                    and 'key' not in target_entry
                )
                if is_pure_image_click:
                    data.pop(target_data_idx)
                else:
                    # 混合条目（键盘步骤配了图等）→ 只清掉图片引用，保留动作本身
                    target_entry.pop('image', None)

            # 3) 【核心】统一编号：先重命名磁盘图片文件 → 再重新分配JSON步骤编号和image字段
            # Step 0: 清理历史残留的 tmp 临时文件，避免 183 冲突
            for _leftover in os.listdir(folder_path):
                if _leftover.lower().endswith('.png') and ('_tmp' in _leftover or '_r_tmp' in _leftover or _leftover.startswith('_tmp_') or _leftover.startswith('_del_tmp_')):
                    try: os.remove(os.path.join(folder_path, _leftover))
                    except Exception: pass
            # Step A: 收集磁盘上所有操作*.png，按编号排序，按顺序重新命名为 操作1.png,操作2.png,...
            disk_imgs = [f for f in os.listdir(folder_path) if f.lower().endswith('.png') and re.search(r'操作(\d+)\.png', f)]
            def _img_num(f):
                mm = re.search(r'操作(\d+)\.png', f)
                return int(mm.group(1)) if mm else 999999
            disk_imgs_sorted = sorted(disk_imgs, key=_img_num)
            # 两步法重命名：先全改成tmp避免冲突
            import uuid as _uuid
            tmp_mapping = {}  # 旧名 -> 新名
            for new_idx, old_f in enumerate(disk_imgs_sorted):
                new_name = f"操作{new_idx + 1}.png"
                tmp_mapping[old_f] = new_name
            # 第一遍：全部 -> tmp_xxx
            for old_f in disk_imgs_sorted:
                old_p = os.path.join(folder_path, old_f)
                tmp_p = os.path.join(folder_path, f"_tmp_{_uuid.uuid4().hex[:8]}_{old_f}")
                if os.path.exists(old_p):
                    os.rename(old_p, tmp_p)
                    tmp_mapping[old_f] = (tmp_p, tmp_mapping[old_f])
            # 第二遍：tmp_xxx -> 新名
            final_name_map = {}  # 用于后面JSON更新：图片原名(不含路径) -> 新名
            for old_f in disk_imgs_sorted:
                tmp_info = tmp_mapping[old_f]
                if isinstance(tmp_info, tuple):
                    tmp_p, new_name = tmp_info
                    new_p = os.path.join(folder_path, new_name)
                    if os.path.exists(tmp_p) and not os.path.exists(new_p):
                        os.rename(tmp_p, new_p)
                    final_name_map[old_f] = new_name

            # Step B: 重新分配 JSON step编号 + 重新对齐 image 字段
            # ★ 关键修复：磁盘图片已按"物理顺序"被强制重命名为 操作1, 操作2, ..., 操作N（N=磁盘上的图片数）
            #   所以 JSON 中有 image 字段的条目，必须按它们【在 data 中的出现顺序】依次对应到
            #   操作1.png, 操作2.png, ...（这样无论增删了多少纯坐标/键盘步骤，都不会错位）
            #   这比靠"旧文件名映射"可靠得多！
            img_counter = 1
            max_disk_img = len(disk_imgs_sorted)  # 磁盘上实际有多少张图片（就是最终有几张 操作N.png）
            for i, d in enumerate(data):
                d['step'] = i + 1
                if 'image' in d and d['image']:
                    # 按出现顺序分配新的图片文件名（和磁盘物理顺序严格对齐）
                    if img_counter <= max_disk_img:
                        d['image'] = f"操作{img_counter}.png"
                        img_counter += 1
                    else:
                        # 异常：有image字段的条目数 > 磁盘图片数（不可能，安全兜底清掉）
                        d.pop('image', None)

            save_json_data(json_path, data)
            self.show_beautiful_message('information', '成功', '图片删除成功！')
            # ★ 防闪退关键：先关闭旧的"查看图片"对话框（如果有），然后用QTimer延迟开新的
            #   绝对不能在当前按钮的回调栈里直接view_folder_images开新dialog，会导致控件交叉销毁崩溃
            from PyQt5.QtCore import QTimer
            old_dialog = getattr(self, '_view_images_dialog', None)
            if old_dialog is None and hasattr(self, 'folder_manager') and self.folder_manager:
                old_dialog = getattr(self.folder_manager, '_view_images_dialog', None)
            _row = None
            if hasattr(self, 'table') and self.table.currentRow() >= 0:
                _row = self.table.currentRow()
            if old_dialog is not None:
                try:
                    old_dialog.close()
                    old_dialog.deleteLater()
                except Exception:
                    pass
                self._view_images_dialog = None
                if hasattr(self, 'folder_manager') and self.folder_manager:
                    self.folder_manager._view_images_dialog = None
            # 延迟 80ms 重新打开（等旧dialog销毁完成、当前回调栈退出）
            if _row is not None:
                QTimer.singleShot(80, lambda _r=_row, _fp=folder_path: self.view_folder_images(_r, _fp))
        except Exception as e:
            self.show_beautiful_message('critical', '错误', f"删除失败: {e}", parent=self)

    def reorder_images(self, folder_path, old_step, new_step, dialog=None):
        """拖拽重排图片顺序"""
        json_path = os.path.join(folder_path, 'recording.json')
        if not os.path.exists(json_path):
            return
        data = load_json_data(json_path)
        if not isinstance(data, list) or len(data) < 2:
            return
        data.sort(key=lambda x: x.get('step', 0))

        # 获取所有有图片的操作（按步骤号排序），用于映射视觉索引
        image_ops = [(i, d) for i, d in enumerate(data) if d.get('image')]
        if len(image_ops) < 2:
            return

        # 找到 old_step 和 new_step 在 image_ops 中的视觉索引（0-based，仅限有图片的条目）
        old_vi = next((vi for vi, (_, d) in enumerate(image_ops) if d.get('step') == old_step), None)
        new_vi = next((vi for vi, (_, d) in enumerate(image_ops) if d.get('step') == new_step), None)
        if old_vi is None or new_vi is None:
            return

        # 找到 source 在 data 中的实际索引
        old_data_idx = next((i for i, d in enumerate(data) if d.get('step') == old_step), None)
        if old_data_idx is None:
            return

        # 计算目标位置在 data 中的实际索引
        # new_vi 是 visual index（在有图片的条目中的位置），需要映射回 data 中的真实索引
        target_vi = new_vi
        if new_vi >= old_vi:
            # 向后移动时，目标在 data 中的索引是目标 visual 条目后面的位置
            # 但我们需要的是在移动前找到目标位置
            if target_vi + 1 < len(image_ops):
                next_img_data_idx = image_ops[target_vi + 1][0]
            else:
                next_img_data_idx = len(data)  # 移到末尾
        else:
            # 向前移动时，目标在 data 中的索引就是目标 visual 条目的位置
            next_img_data_idx = image_ops[target_vi][0]

        # pop + insert：真正地移动条目位置
        item = data.pop(old_data_idx)
        # 如果 old_data_idx < new_target，由于前面已经 pop 了，索引会偏移
        insert_idx = next_img_data_idx
        if old_data_idx < insert_idx:
            insert_idx -= 1
        data.insert(insert_idx, item)

        # ★ 重新编号所有操作 + 同步更新 image 字段（两步法移动磁盘文件防冲突）
        # Step 1: 先记录所有【旧名->新名】的映射
        # ★★ 关键修复：新图片编号不能用全局索引 i！必须按"有image条目的出现顺序"递增，
        #    否则纯坐标步骤（无image）会占编号，导致JSON image字段与磁盘物理文件名错开！
        rename_plan = {}  # {old_img_name: new_img_name}
        _img_counter = 0
        for i, d in enumerate(data):
            d['step'] = i + 1
            if 'image' in d and d.get('image'):
                _img_counter += 1
                old_image = d['image']
                new_image = f'操作{_img_counter}.png'
                if old_image != new_image:
                    rename_plan[old_image] = new_image
                d['image'] = new_image
        # Step 2: 两步法移动磁盘文件
        #  先全部重命名为 tmp，避免覆盖
        tmp_paths = {}  # old: tmp_xxx.png
        for old_name, new_name in rename_plan.items():
            old_p = os.path.join(folder_path, old_name)
            if os.path.exists(old_p):
                tmp_n = f"_r_tmp_{uuid.uuid4().hex[:8]}_{old_name}"
                tmp_p = os.path.join(folder_path, tmp_n)
                shutil.move(old_p, tmp_p)
                tmp_paths[old_name] = tmp_p
        # 再从 tmp -> 新名字
        for old_name, new_name in rename_plan.items():
            old_p = tmp_paths.get(old_name)
            if not old_p or not os.path.exists(old_p):
                continue
            new_p = os.path.join(folder_path, new_name)
            if not os.path.exists(new_p):
                shutil.move(old_p, new_p)
            else:
                # 新路径存在（极端情况），用更稳妥的不丢失覆盖
                try:
                    os.replace(old_p, new_p)
                except:
                    shutil.move(old_p, new_p)

        save_json_data(json_path, data)

        from PyQt5.QtCore import QTimer
        QTimer.singleShot(300, lambda: self.refresh_view_images(folder_path))

    def show_action_type_menu(self, button):
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu {"
            "    background-color: #2C2C2E;"
            "    border: 1px solid #3A3A3C;"
            "    border-radius: 8px;"
            "    padding: 6px;"
            "}"
            "QMenu::item {"
            "    padding: 8px 20px;"
            "    border-radius: 6px;"
            "    color: #FFFFFF;"
            "    font-size: 13px;"
            "}"
            "QMenu::item:selected {"
            "    background-color: #0A84FF;"
            "    color: white;"
            "}"
        )
        current = button.property('current_action_type') or 'left_click'
        action_items = [
            ('Click', 'left_click'),
            ('右击', 'right_click'),
            ('双击', 'double_click'),
            ('中击', 'middle_click'),
            ('键盘输入', 'keyboard'),
            ('拖拽', 'drag'),
        ]
        for label, action_type in action_items:
            action = menu.addAction(label)
            if action_type == current:
                action.setText('✓ ' + label)
            action.triggered.connect(lambda checked, at=action_type: self.change_action_type(button, at))
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

    def change_action_type(self, button, new_action_type):
        """更新recording.json文件中的操作类型"""
        if new_action_type == 'right_click':
            reply = self.show_beautiful_message('question', '⚠️ 右击风险提示', '右击会弹出系统菜单，可能导致程序暂时无响应！\n'
                '建议：\n1. 优先Click\n2. 若必须右击，确保目标在前台\n'
                '3. 卡死可按ESC恢复', buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        json_path = os.path.join(button.property("folder_path"), "recording.json")
        if not os.path.exists(json_path):
            return
        data = load_json_data(json_path, [])
        if not isinstance(data, list):
            return
        updated = False
        for d in data:
            if d.get('step') == button.property("step_num"):
                d['action_type'] = new_action_type
                updated = True
                break
        if updated:
            save_json_data(json_path, data)
            op = {'left_click': 'Click', 'right_click': '右击', 'keyboard': '键盘输入',
                  'double_click': '双击', 'drag': '拖拽'}.get(new_action_type, new_action_type)
            button.setText(f"{op} {button.property('step_num')}")
            button.setProperty("current_action_type", new_action_type)
            # 更新按钮颜色以匹配新操作类型
            btn_colors = {'left_click': '#8E8E93', 'right_click': '#8E8E93',
                         'double_click': '#8E8E93', 'keyboard': '#0A84FF', 'drag': '#8E8E93'}
            new_color = btn_colors.get(new_action_type, '#8E8E93')
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {new_color};
                    color: white;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 0 12px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: #0A84FF;
                }}
                QPushButton:pressed {{
                    background-color: #004DB3;
                }}
            """)

    # -------------------- 原__init__后续内容 --------------------

    def open_font_size_dialog(self):
        current_font = self.font()
        current_size = current_font.pointSize()
        
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("字体大小设置")
        # 按屏幕比例设置对话框大小
        scr = self.screen_size()
        dialog.setFixedSize(int(scr.width() * 0.2), int(scr.height() * 0.15))
        
        # 应用统一样式
        if APP_STYLES_AVAILABLE:
            apply_dialog_style(dialog)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 添加标签
        label = QLabel("请输入字体大小:")
        layout.addWidget(label)
        
        # 添加输入框
        spin_box = QSpinBox()
        spin_box.setRange(8, 72)
        spin_box.setValue(current_size)
        spin_box.setSuffix(" px")
        layout.addWidget(spin_box)

        # 添加按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        # 添加确定按钮 - macOS渐变风格
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(60, 28)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_PRIMARY};
                color: white;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)
        ok_btn.clicked.connect(lambda: self.apply_font_size(spin_box.value(), dialog))
        button_layout.addWidget(ok_btn)

        # 添加取消按钮 - macOS风格
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumSize(60, 28)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-size: 12px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: {CARD};
                border-color: {ACCENT};
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec_()
    
    def apply_font_size(self, size, dialog):
        """应用字体大小设置"""
        current_font = self.font()
        current_font.setPointSize(size)
        current_font.setFamily("PingFang SC")  # 确保字体家族为微软雅黑
        self.setFont(current_font)
        for widget in self.findChildren(QWidget):
            widget_font = widget.font()
            widget_font.setPointSize(size)
            widget_font.setFamily("PingFang SC")  # 确保字体家族为微软雅黑
            widget.setFont(widget_font)
        # 保存字体大小设置
        self.save_font_size_setting(size)
        dialog.accept()

    def save_font_size_setting(self, size):
        """保存字体大小设置"""
        if not self.current_user:
            return
        
        try:
            config_path = os.path.join(self.user_data_dir, f'font_size_{self.current_user}.json')
            config = {'font_size': size}
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # print(f"保存字体大小设置失败: {e}")  # [日志已禁用]
            pass
    
    def load_font_size_setting(self):
        """加载字体大小设置"""
        if not self.current_user:
            return
        
        try:
            config_path = os.path.join(self.user_data_dir, f'font_size_{self.current_user}.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    font_size = config.get('font_size', 9)  # 默认字体大小为9
                    # 应用字体大小设置
                    current_font = self.font()
                    current_font.setPointSize(font_size)
                    current_font.setFamily("PingFang SC")  # 确保字体家族为微软雅黑
                    self.setFont(current_font)
                    for widget in self.findChildren(QWidget):
                        widget_font = widget.font()
                        widget_font.setPointSize(font_size)
                        widget_font.setFamily("PingFang SC")  # 确保字体家族为微软雅黑
                        widget.setFont(widget_font)
        except Exception as e:
            # print(f"加载字体大小设置失败: {e}")  # [日志已禁用]
            pass

    def debug_print(self, message):
        """调试输出：仅在调试模式下打印信息，同时发送到日志窗口"""
        if getattr(self, 'debug_mode', False):
            print(message)
            # 发送到日志窗口
            self.append_log(message)

    def append_log(self, message):
        """线程安全的日志追加 - 根据调用线程决定直接执行或通过信号转发"""
        from PyQt5.QtCore import QThread
        if QThread.currentThread() is QApplication.instance().thread():
            self._append_log_impl(message)
        else:
            self.log_signal.emit(message)

    def _append_log_impl(self, message):
        """实际的日志追加实现（始终在主线程中执行）"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        # 盒式日志（以 ╔═/ ║/╚═ 开头）不加时间戳，保持排版整洁
        if message.startswith('╔═') or message.startswith(' ║') or message.startswith('╚═'):
            log_line = message
        else:
            log_line = f"[{timestamp}] {message}"
        
        # 确保日志窗口已创建（但不一定显示）
        if not hasattr(self, 'log_window') or self.log_window is None:
            self.create_log_window()
        
        # 追加到文本框
        if hasattr(self, 'log_text_edit') and self.log_text_edit is not None:
            try:
                # 检查用户是否在查看历史日志（不在底部）
                scrollbar = self.log_text_edit.verticalScrollBar()
                current_value = scrollbar.value()
                max_value = scrollbar.maximum()
                # 如果用户在底部附近（距离底部小于50像素），则自动滚动
                # 否则保持当前位置，不打扰用户查看历史
                should_auto_scroll = (max_value - current_value) < 50
                
                self.log_text_edit.append(log_line)
                
                # 限制日志行数，防止 QTextEdit 文档过大导致 UI 卡死
                doc = self.log_text_edit.document()
                MAX_LOG_LINES = 500
                if doc.blockCount() > MAX_LOG_LINES:
                    # 删除最前面的 100 行，保留最近的内容
                    cursor = self.log_text_edit.textCursor()
                    cursor.movePosition(cursor.Start)
                    # 选择前 100 个 block 的文本内容
                    for _ in range(100):
                        cursor.movePosition(cursor.Down, cursor.KeepAnchor)
                    cursor.removeSelectedText()
                    # 删除留下的空行（block separator）
                    cursor.movePosition(cursor.Start)
                    if cursor.movePosition(cursor.Down, cursor.KeepAnchor):
                        cursor.removeSelectedText()
                
                # 只有在用户在底部时才自动滚动
                if should_auto_scroll:
                    scrollbar.setValue(scrollbar.maximum())
            except Exception:
                pass

    def clear_log(self):
        """清空日志（线程安全）"""
        from PyQt5.QtCore import QThread
        if QThread.currentThread() is QApplication.instance().thread():
            self._clear_log_impl()
        else:
            QTimer.singleShot(0, self._clear_log_impl)
    
    def _clear_log_impl(self):
        """实际的日志清空实现"""
        if hasattr(self, 'log_text_edit') and self.log_text_edit is not None:
            try:
                self.log_text_edit.clear()
            except Exception:
                pass

    def show_log_window(self):
        """显示日志窗口"""
        if not hasattr(self, 'log_window') or self.log_window is None:
            self.create_log_window()
        screen = QApplication.primaryScreen().geometry()
        self.log_window.move(
            screen.center().x() - self.log_window.width() // 2,
            screen.center().y() - self.log_window.height() // 2
        )
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def create_log_window(self):
        """创建日志窗口"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
        from PyQt5.QtCore import Qt

        self.log_window = QDialog(self)
        self.log_window.setWindowTitle("运行日志")
        self.log_window.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.log_window.setMinimumSize(700, 500)
        center_window(self.log_window)

        layout = QVBoxLayout(self.log_window)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        _outer = QFrame(self.log_window)
        _outer.setObjectName("logOuter")
        _outer.setStyleSheet("""
            QFrame#logOuter {
                background-color: #1C1C1E;
                border-radius: 14px;
                border: 1px solid #1C1C1E;
            }
        """)
        _cl = QVBoxLayout(_outer)
        _cl.setContentsMargins(1, 1, 1, 1)
        _cl.setSpacing(0)

        _header = QWidget()
        _header.setFixedHeight(44)
        _header.setStyleSheet("background-color: #1C1C1E; border-top-left-radius: 11px; border-top-right-radius: 11px; border: none;")
        _hdr_lo = QHBoxLayout(_header)
        _hdr_lo.setContentsMargins(16, 0, 16, 0)
        _hdr_lo.setSpacing(8)
        _hdr_title = QLabel("运行日志")
        _hdr_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: transparent; border: none;")
        _hdr_lo.addWidget(_hdr_title)
        _hdr_lo.addStretch()
        def _closeD(ev):
            if ev.button() == Qt.LeftButton: self.log_window.close()
        _red_dot = QFrame()
        _red_dot.setFixedSize(16, 16)
        _red_dot.setStyleSheet("background:#FF5F57; border-radius:8px; border:none;")
        _red_dot.mousePressEvent = _closeD
        _red_dot.setCursor(Qt.PointingHandCursor)
        _hdr_lo.addWidget(_red_dot)
        def _start_drag(ev):
            if ev.button() == Qt.LeftButton:
                self.log_window._drag_pos = ev.globalPos() - self.log_window.pos()
        def _do_drag(ev):
            if hasattr(self.log_window, '_drag_pos') and ev.buttons() & Qt.LeftButton:
                self.log_window.move(ev.globalPos() - self.log_window._drag_pos)
        _header.mousePressEvent = _start_drag
        _header.mouseMoveEvent = _do_drag
        _cl.addWidget(_header)

        content = QWidget()
        content.setStyleSheet("background-color: #FFFFFF; border: none; border-bottom-left-radius: 11px; border-bottom-right-radius: 11px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 16)
        content_layout.setSpacing(10)

        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("clearLogBtn")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton#clearLogBtn {
                background-color: #0A84FF; color: white; border: none; border-radius: 4px;
                padding: 6px 16px; font-weight: bold; font-size: 12px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QPushButton#clearLogBtn:hover { background-color: #006AE0; }
            QPushButton#clearLogBtn:pressed { background-color: #004DB3; }
        """)
        clear_btn.clicked.connect(self.clear_log)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        content_layout.addLayout(btn_row)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                color: #2C3E50;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                padding: 12px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 14px;
            }
        """)
        content_layout.addWidget(self.log_text_edit)

        hint_label = QLabel("提示：日志仅在调试模式开启时记录。可在设置中开启/关闭调试模式。")
        hint_label.setStyleSheet("color: #8E8E93; font-size: 12px; background: transparent; border: none;")
        content_layout.addWidget(hint_label)

        _cl.addWidget(content)
        layout.addWidget(_outer)

    def save_debug_mode_setting(self):
        """保存调试模式设置"""
        try:
            config_path = os.path.join(self.user_data_dir, 'debug_mode.json')
            config = {'debug_mode': getattr(self, 'debug_mode', False)}
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_debug_mode_setting(self):
        """加载调试模式设置"""
        try:
            config_path = os.path.join(self.user_data_dir, 'debug_mode.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.debug_mode = config.get('debug_mode', False)
            else:
                self.debug_mode = False  # 默认关闭！打开会让回放慢3-5倍
        except Exception:
            self.debug_mode = False
        # 同步设置 image_recognition 模块的调试模式
        from image_recognition import set_debug_mode, set_log_callback
        set_debug_mode(self.debug_mode)
        # 设置日志回调，将 image_recognition 的日志发送到日志窗口
        set_log_callback(lambda msg: self.append_log(f" ║  {msg}"))

    def toggle_debug_mode(self):
        """切换调试模式开关"""
        self.debug_mode = not getattr(self, 'debug_mode', False)
        self.save_debug_mode_setting()
        # 同步设置 image_recognition 模块的调试模式
        from image_recognition import set_debug_mode, set_log_callback
        set_debug_mode(self.debug_mode)
        # 设置日志回调
        set_log_callback(lambda msg: self.append_log(f" ║  {msg}"))
        return self.debug_mode

    def create_replay_status_indicator(self):
        """创建回放控制窗口 - 极简扁平风格 (方案3)"""
        from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QFrame, QCheckBox
        from PyQt5.QtCore import Qt, QPoint, QTimer
        from PyQt5.QtGui import QColor, QPalette
        
        # 清理旧的悬浮窗口
        if hasattr(self, 'replay_status_widget') and self.replay_status_widget:
            try:
                self.replay_status_widget.close()
                self.replay_status_widget.deleteLater()
            except:
                pass
            self.replay_status_widget = None
        
        # 创建主窗口
        self.replay_status_widget = DraggableWidget(self)
        self.replay_status_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.replay_status_widget.setFixedSize(306, 426)

        main_layout = QVBoxLayout(self.replay_status_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        
        # 标题栏 - 带绿色状态点
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        # 绿色状态点
        status_dot = QLabel("●")
        status_dot.setStyleSheet("""
            QLabel {
                color: #52c41a;
                font-size: 16px;
                background: transparent;
            }
        """)
        title_layout.addWidget(status_dot)
        
        # 标题
        title_label = QLabel("录制控制")
        title_label.setStyleSheet("""
            QLabel {
                color: #262626;
                font-size: 14px;
                font-weight: 500;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                background: transparent;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        from PyQt5.QtWidgets import QFrame as _QF2
        _dots_w = QWidget()
        _dots_w.setAttribute(Qt.WA_TranslucentBackground)
        _dots_w.setStyleSheet("background:transparent;")
        _dots_l = QHBoxLayout(_dots_w)
        _dots_l.setContentsMargins(0,0,0,0)
        _dots_l.setSpacing(6)
        _d_close = _QF2()
        _d_close.setFixedSize(16, 16)
        _d_close.setStyleSheet("QFrame{background-color:#FF5F57;border:none;border-radius:8px;}QFrame:hover{background-color:#FF3B30;}")
        _d_close.setCursor(Qt.PointingHandCursor)
        def _dclose_ev(ev):
            if ev.button()==Qt.LeftButton: self.close_replay_indicator()
        _d_close.mousePressEvent = _dclose_ev
        _dots_l.addWidget(_d_close)
        title_layout.addWidget(_dots_w)
        
        main_layout.addLayout(title_layout)
        
        # 分隔线 - 已移除，减少线条
        
        # 回放状态开关按钮 - 只切换状态，不执行回放
        self.floating_replay_btn = QPushButton("▶ 回放已关闭")
        self.floating_replay_btn.setCursor(Qt.PointingHandCursor)
        self.floating_replay_btn.setFixedHeight(32)
        self.floating_replay_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG};
                color: {TEXT};
                border-radius: 6px;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: {CARD};
                color: {ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {CARD};
            }}
        """)
        self.floating_replay_btn.clicked.connect(self.toggle_replay_status_only)
        main_layout.addWidget(self.floating_replay_btn)
        
        main_layout.addSpacing(16)
        
        # 流程列表区域 - 使用QScrollArea实现滚动
        from PyQt5.QtWidgets import QScrollArea
        self.list_scroll_area = QScrollArea()
        self.list_scroll_area.setWidgetResizable(True)
        self.list_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.list_scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 创建列表容器
        self.list_container = QWidget()
        self.list_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        
        # 加载流程列表
        self.load_replay_list(self.list_layout)
        
        # 将列表容器添加到滚动区域
        self.list_scroll_area.setWidget(self.list_container)
        
        # 设置滚动区域的最大高度，避免窗口过大
        self.list_scroll_area.setMaximumHeight(300)
        
        main_layout.addWidget(self.list_scroll_area, 1)
        
        main_layout.addSpacing(16)
        
        # 进入主程序按钮
        enter_main_btn = QPushButton("🏠 进入主程序")
        enter_main_btn.setCursor(Qt.PointingHandCursor)
        enter_main_btn.setFixedHeight(40)
        enter_main_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_PRIMARY};
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)
        enter_main_btn.clicked.connect(self.enter_main_program)
        main_layout.addWidget(enter_main_btn)
        
        # 加载保存的位置
        self.load_replay_indicator_position()
        
        self.update_replay_status_indicator()
    
    def show_recording_context_menu(self, pos, recording_name, item_widget):
        """显示流程列表项的右键菜单"""
        from PyQt5.QtWidgets import QMenu
        from PyQt5.QtCore import QPoint
        
        from utils import get_recordings_path
        folder_path = os.path.join(get_recordings_path(), recording_name)
        
        menu = QMenu(self)
        pin_action = menu.addAction("置顶")
        interval_action = menu.addAction("设置默认间隔")
        if not os.path.exists(folder_path):
            interval_action.setEnabled(False)
        
        action = menu.exec_(item_widget.mapToGlobal(pos))
        
        if action == pin_action:
            self.pin_recording_to_top(recording_name)
        elif action == interval_action:
            self.set_folder_interval(folder_path)
    
    def pin_recording_to_top(self, recording_name):
        """将指定的流程置顶到列表最上面"""
        try:
            # 从当前布局中获取流程列表顺序
            current_recordings = []
            for i in range(self.list_layout.count()):
                item = self.list_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    name = widget.property('recording_name')
                    if name:
                        current_recordings.append(name)
            
            # 将指定的流程移到最前面
            if recording_name in current_recordings:
                current_recordings.remove(recording_name)
                current_recordings.insert(0, recording_name)
            
            # 清空当前列表
            while self.list_layout.count():
                child = self.list_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # 重新加载列表
            self.recording_checkboxes = {}
            for recording in current_recordings:
                self._create_recording_item(recording, self.list_layout)
            
            # 保存新的顺序
            self.save_recording_order(current_recordings)
            
            # 如果没有流程，显示提示
            if not current_recordings:
                from PyQt5.QtWidgets import QLabel
                empty_label = QLabel("暂无录制流程")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet("""
                    QLabel {
                        color: #9ca3af;
                        font-size: 13px;
                        background: transparent;
                    }
                """)
                self.list_layout.addWidget(empty_label)
            
            self.list_layout.addStretch()
            
        except Exception as e:
            pass
    
    def _refresh_recording_list(self):
        """刷新录制列表显示"""
        self.load_replay_list(self.list_layout)
    
    def _create_recording_item(self, recording, layout):
        """创建单个流程列表项 - 极简风格"""
        from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QMenu
        from PyQt5.QtCore import Qt
        
        item_widget = QWidget()
        item_widget.setProperty('recording_name', recording)
        item_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QWidget:hover {
                background-color: rgba(0,0,0,0.03);
            }
        """)
        item_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        item_widget.customContextMenuRequested.connect(
            lambda pos, name=recording, widget=item_widget: self.show_recording_context_menu(pos, name, widget)
        )
        
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(12, 8, 12, 8)
        item_layout.setSpacing(12)
        
        # 流程名称
        name_label = QLabel(recording)
        name_label.setStyleSheet("""
            QLabel {
                color: #1a1a1a;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                background: transparent;
            }
        """)
        item_layout.addWidget(name_label, 1)
        
        # 播放按钮
        play_btn = QPushButton("▶")
        play_btn.setFixedSize(32, 32)
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_PRIMARY};
                color: white;
                border-radius: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)
        play_btn.clicked.connect(lambda checked, name=recording: self.play_recording(name))
        item_layout.addWidget(play_btn)
        
        # ★ 修复：右键落在行内子控件（名称标签/播放按钮）上时，子控件默认策略
        # （Qt.DefaultContextMenu）会把右键事件吞掉，父容器收不到 customContextMenuRequested，
        # 导致"右键流程文件夹没弹出菜单/看不到设置默认间隔"。
        # 给子控件也挂上 CustomContextMenu，且用子控件自身的坐标系做 mapToGlobal。
        for _child in (name_label, play_btn):
            _child.setContextMenuPolicy(Qt.CustomContextMenu)
            _child.customContextMenuRequested.connect(
                lambda pos, name=recording, w=_child: self.show_recording_context_menu(pos, name, w)
            )
        
        layout.addWidget(item_widget)
    
    def load_replay_list(self, layout):
        """加载流程列表到回放控制窗口 - 极简扁平风格"""
        from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QCheckBox, QMenu
        from PyQt5.QtCore import Qt
        from utils import get_recordings_path
        
        # 存储复选框引用
        self.recording_checkboxes = {}
        
        # 获取流程列表
        recordings_dir = get_recordings_path()
        try:
            recordings = [d for d in os.listdir(recordings_dir) 
                         if os.path.isdir(os.path.join(recordings_dir, d)) and d != 'trash']
        except:
            recordings = []
        
        # 加载保存的顺序
        saved_order = self.load_recording_order()
        
        # 如果有保存的顺序，按照保存的顺序排序
        if saved_order:
            # 过滤掉已不存在的流程
            valid_order = [r for r in saved_order if r in recordings]
            # 添加新增的流程（不在保存顺序中的）
            new_recordings = [r for r in recordings if r not in valid_order]
            # 最终顺序：已排序的 + 新增的
            final_order = valid_order + new_recordings
        else:
            # 没有保存的顺序，使用默认顺序
            final_order = recordings
        
        # 显示所有流程（支持滚动）
        for recording in final_order:
            self._create_recording_item(recording, layout)
        
        # 如果没有流程，显示提示
        if not final_order:
            empty_label = QLabel("暂无录制流程")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #9ca3af;
                    font-size: 20px;
                    background: transparent;
                }
            """)
            layout.addWidget(empty_label)
        
        layout.addStretch()
    
    def update_replay_status_indicator(self):
        """更新回放状态指示器显示 - 用于快捷键切换状态，只更新状态不播放"""
        # 这个方法只更新内部状态，不更新按钮显示
        # 按钮显示由 update_replay_playback_indicator 控制
        pass
    
    def update_replay_playback_indicator(self):
        """更新回放播放状态指示器 - 只更新is_replaying状态，不更新按钮显示"""
        # 状态按钮的文字和样式由 toggle_replay_status_only 方法控制
        # 这个方法只更新内部状态，不改变按钮显示
        pass
    
    def select_all_recordings(self):
        """全选/取消全选所有流程"""
        if not hasattr(self, 'recording_checkboxes'):
            return
        
        # 检查是否已经有选中的
        any_checked = any(cb.isChecked() for cb in self.recording_checkboxes.values())
        
        # 如果已经有选中的，则全部取消；否则全部选中
        for checkbox in self.recording_checkboxes.values():
            checkbox.setChecked(not any_checked)
        
        # 更新按钮文字
        if hasattr(self, 'select_all_btn'):
            self.select_all_btn.setText("取消全选" if not any_checked else "全选")
    
    def batch_play_recordings(self):
        """批量执行选中的流程"""
        if not hasattr(self, 'recording_checkboxes'):
            return
        
        selected = [name for name, cb in self.recording_checkboxes.items() if cb.isChecked()]
        
        if not selected:
            return
        
        # 逐个执行选中的流程，每个回放完成后自动播放下一个
        self._batch_play_queue = selected.copy()
        self._play_next_in_batch()
    
    def _play_next_in_batch(self):
        """播放批量队列中的下一个流程"""
        if not hasattr(self, '_batch_play_queue') or not self._batch_play_queue:
            if hasattr(self, '_batch_play_queue'):
                del self._batch_play_queue
            return
        next_name = self._batch_play_queue.pop(0)
        self.play_recording(next_name)
        # play_recording 为同步阻塞调用，返回时回放已完成
        # 使用 QTimer 避免潜在递归问题，继续播放下一个
        if hasattr(self, '_batch_play_queue') and self._batch_play_queue:
            QTimer.singleShot(0, self._play_next_in_batch)
    
    def show_replay_settings(self):
        """显示回放设置对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSlider, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("回放设置")
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(280, 200)
        from design_system import ColorPalette as _C
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {_C.BG_CARD};
            }}
            QLabel {{
                color: {_C.TEXT_PRIMARY};
                font-size: 18px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton {{
                background-color: {_C.PRIMARY};
                color: white;
                border-radius: 12px;
                padding: 8px 20px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: {_C.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {_C.PRIMARY_ACTIVE};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # 速度设置
        speed_label = QLabel("回放速度: 1.0x")
        layout.addWidget(speed_label)
        
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setRange(5, 100)
        speed_slider.setValue(10)
        speed_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 4px;
                background: {_C.LIGHT_GRAY_200};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 12px;
                height: 12px;
                background: {_C.LIGHT_SYSTEM_RED};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(speed_slider)
        
        # 实时更新速度标签
        def update_speed_label(value):
            speed_x = value / 10.0
            speed_label.setText(f"回放速度: {speed_x:.1f}x")
        
        speed_slider.valueChanged.connect(update_speed_label)
        
        # 确定按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("确定")
        
        def apply_settings():
            speed_x = speed_slider.value() / 10.0
            # replay_interval: 速度越快间隔越小
            self.replay_interval = max(0.0, 0.3 / speed_x)
            # match_timeout: 优化后,1.0x=0.5s, 2.0x=0.25s, 0.5x=1.0s(反应更快)
            self.replay_timeout = max(0.1, min(2.0, 0.5 / speed_x))
            dialog.accept()
        
        ok_btn.clicked.connect(apply_settings)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def save_recording_order(self, order_list):
        """保存流程顺序到配置文件"""
        try:
            config_path = os.path.join(self.user_data_dir, 'recording_order.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'order': order_list}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.debug_print(f"保存流程顺序失败: {e}")
    
    def load_recording_order(self):
        """加载保存的流程顺序"""
        try:
            config_path = os.path.join(self.user_data_dir, 'recording_order.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('order', [])
        except Exception as e:
            self.debug_print(f"加载流程顺序失败: {e}")
        return []
    
    def load_replay_indicator_position(self):
        """加载回放指示器位置"""
        if not hasattr(self, 'replay_status_widget'):
            return
        
        try:
            config_path = os.path.join(self.user_data_dir, 'replay_indicator_position.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    x = config.get('x', 0)
                    y = config.get('y', 0)
                    self.replay_status_widget.move(x, y)
                    return
        except Exception as e:
            self.debug_print(f"加载回放指示器位置失败: {e}")

        # 默认位置：屏幕中央偏右
        screen = QApplication.primaryScreen().geometry()
        widget_width = self.replay_status_widget.width()
        widget_height = self.replay_status_widget.height()
        default_x = screen.x() + screen.width() - widget_width - 50
        default_y = screen.y() + (screen.height() - widget_height) // 2
        self.replay_status_widget.move(default_x, default_y)
        # print(f"[调试] 悬浮窗口默认位置: ({default_x}, {default_y}), 屏幕大小: {screen.width()}x{screen.height()}")  # [日志已禁用]
    
    def _usage_counts_path(self):
        return os.path.join(self.user_data_dir, 'usage_counts.json')

    def _increment_usage_count(self, folder_name):
        path = self._usage_counts_path()
        counts = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    counts = json.load(f)
            except: pass
        counts[folder_name] = counts.get(folder_name, 0) + 1
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(counts, f, ensure_ascii=False, indent=2)
        except: pass
        return counts[folder_name]

    def _get_usage_counts(self):
        path = self._usage_counts_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {}

    def play_recording(self, recording_name):
        """播放指定录制流程 - 总是从头开始执行"""
        # print(f"[DEBUG] play_recording called: {recording_name}")  # [日志已禁用]
        try:
            # 设置当前流程
            self.current_recording = recording_name
            # 计数已统一在 replay_folder_operations 中处理
            
            # 如果已有回放正在运行，先完全停止
            if getattr(self, 'is_replaying', False):
                self.debug_print("[DEBUG] 检测到正在进行的回放，先停止")
                self.stop_replay()
                # 等待一小段时间确保停止完成
                import time
                time.sleep(0.1)
            
            # 清除停止标志，确保新回放可以正常开始
            from image_recognition import clear_replay_stop_flag
            clear_replay_stop_flag()
            
            # 直接开始回放
            if not getattr(self, 'is_recording', False):
                # 调用实际的回放方法
                from utils import get_recordings_path
                recordings_dir = get_recordings_path()
                folder_path = os.path.join(recordings_dir, recording_name)
                
                if os.path.exists(folder_path):
                    self.debug_print(f"[DEBUG] 从头开始回放流程: {recording_name}")
                    self.is_replaying = True
                    self.replay_folder_operations(folder_path)
                else:
                    self.debug_print(f"[DEBUG] 文件夹不存在: {folder_path}")
                    
        except Exception as e:
            # print(f"[DEBUG] 播放流程失败: {e}")  # [日志已禁用]
            import traceback
            traceback.print_exc()
    
    def _start_replay_direct(self, recording_name):
        """直接开始回放 - 调用实际的回放方法（按钮回放，不检查回放状态，也不改变回放状态）"""
        # print(f"[DEBUG] _start_replay_direct called: {recording_name}")  # [日志已禁用]
        try:
            # ★ 防止并发回放：如果已有回放在运行，跳过本次请求
            if getattr(self, 'is_replaying', False):
                self.debug_print("[回放] 检测到已有回放在运行，跳过重复请求")
                return
            
            # 获取录制文件夹路径
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            folder_path = os.path.join(recordings_dir, recording_name)
            # print(f"[DEBUG] folder_path: {folder_path}")  # [日志已禁用]
            
            # 检查文件夹是否存在
            if not os.path.exists(folder_path):
                # print(f"[DEBUG] 文件夹不存在: {folder_path}")  # [日志已禁用]
                return
            
            # print(f"[DEBUG] 调用 replay_folder_operations")  # [日志已禁用]
            # 调用实际的回放方法
            self.replay_folder_operations(folder_path)
            
        except Exception as e:
            self.debug_print(f"[DEBUG] 启动回放失败: {e}")
            import traceback
            traceback.print_exc()
    
    def replay_folder_operations(self, folder_path):
        """执行指定文件夹中的操作回放"""
        # ★ 线程安全锁：防止多线程并发回放
        if not self._replay_lock.acquire(blocking=False):
            self.debug_print("[回放] 检测到回放已在执行中，跳过本次请求")
            return
        
        # ★ 记录锁获取时间，用于超时检测
        self._replay_lock_time = time.time()
        # ★ 新策略：使用标志位禁用热键，不清空字典
        # 这样可以保留 keyboard 库的完整状态（handlers、nonblocking_hotkeys 等）
        # 避免事件处理链断裂的风险，回放完成后只需清除标志位
        _hooks_disabled = False
        try:
            # ★ 设置临时禁用标志
            self._hotkeys_temporarily_disabled = True
            _hooks_disabled = True
            self.debug_print("[回放] 已设置热键临时禁用标志，keyboard库状态完整保留")

            # 递增调用次数（只要是回放就计数，不依赖成功失败）
            folder_name = os.path.basename(folder_path)
            self._increment_usage_count(folder_name)
            
            # 读取recording.json文件
            recording_json_path = os.path.join(folder_path, 'recording.json')
            if not os.path.exists(recording_json_path):
                self.debug_print(f"[回放] 找不到recording.json文件: {recording_json_path}")
                return
            
            with open(recording_json_path, 'r', encoding='utf-8') as f:
                recording_data = json.load(f)
            
            if not recording_data:
                self.debug_print(f"[回放] recording.json为空: {recording_json_path}")
                return
            
            # 清除图像缓存，确保使用最新的图像
            from image_recognition import clear_image_cache
            clear_image_cache()

            # ★ 保存回放前的鼠标位置，结束后恢复 ★
            import pyautogui as _pg
            _saved_x, _saved_y = _pg.position()

            # ★ 修复：检测录制类型，选择正确的回放函数 ★
            # 如果存在键盘、文本输入或滚动操作，必须使用 replay_coordinate_operations
            # （replay_coordinates_only 不支持这些操作类型）
            has_keyboard_or_scroll = any(
                op.get('action_type') in ('keyboard', 'keyboard_direct', 'text_input', 'scroll')
                for op in recording_data
            )
            is_coord_only = not has_keyboard_or_scroll and all(
                'image' not in op for op in recording_data
            )

            # ★ 每次回放前清空日志窗口
            self.clear_log()

            # ★ 热键状态诊断
            try:
                import keyboard as _kb_pre
                _hotkeys = getattr(_kb_pre, '_hotkeys', {})
                _listener = getattr(_kb_pre, '_listener', None)
                if _listener:
                    _h_pre = len(getattr(_listener, 'handlers', []))
                    _lt = getattr(_listener, 'listening_thread', None)
                    _lt_alive = _lt.is_alive() if _lt else False
                    self.debug_print(f"[热键诊断-回放前] _hotkeys={len(_hotkeys)} | handlers={_h_pre} | listen线程={_lt_alive}")
            except Exception:
                pass

            # 执行回放
            self.append_log(f"[回放] 开始执行回放: {folder_path}")
            # ★ 文件夹默认操作间隔：若该文件夹设置了默认间隔则使用，否则用全局默认
            folder_interval = self.folder_intervals.get(folder_path, self.replay_interval)
            if folder_interval is None:
                folder_interval = self.replay_interval
            try:
                folder_interval = float(folder_interval)
            except (TypeError, ValueError):
                folder_interval = self.replay_interval
            self.append_log(f"[回放] 使用操作间隔: {folder_interval}s（文件夹默认: {self.folder_intervals.get(folder_path, '未设置')}）")

            if is_coord_only:
                self.append_log(f"[回放] 检测为坐标录制（无图像），使用 replay_coordinates_only")
                from image_recognition import replay_coordinates_only
                success_count, total_count = replay_coordinates_only(
                    recording_data=recording_data,
                    replay_interval=folder_interval
                )
            else:
                self.append_log(f"[回放] 检测为含图像/键盘录制，使用 replay_coordinate_operations")
                from image_recognition import replay_coordinate_operations
                # ★ 极速/高速档下启用 turbo_match（与组合技路径 app.py:11308 一致）：
                # 单次 0.005s 闪匹配 + Win32 直点，跳过稳定检测/轮询/点击后剪贴板读取，
                # 单步从普通模式的 ~100-500ms 降到 ~10ms 量级。
                # 判定依据用本路径可靠的 replay_interval / replay_timeout（随速度档更新），
                # 不引用组合技路径专属的 _turbo_mode/_speed_scale，避免属性未定义。
                _turbo = (self.replay_interval <= 0.01) or (self.replay_timeout <= 0.15)
                replay_result = replay_coordinate_operations(
                    recording_data=recording_data,
                    folder_path=folder_path,
                    replay_interval=folder_interval,
                    consider_color=False,
                    region_center=None,
                    match_timeout=self.replay_timeout,
                    turbo_match=_turbo
                )
                if len(replay_result) == 3:
                    success_count, total_count, _ = replay_result
                else:
                    success_count, total_count = replay_result
            
            _pg.moveTo(_saved_x, _saved_y, duration=0.15)

            # 回放完成
            self.is_replaying = False
            self.append_log(f"[回放] 回放完成: {success_count}/{total_count} 操作成功")
            
        except Exception as e:
            self.is_replaying = False
            self.append_log(f"[回放] 回放失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # ★ 释放回放锁，允许后续回放执行
            self._replay_lock_time = None
            self._replay_lock.release()
            # ★ 强制释放所有可能卡住的修饰键，防止快捷键无法响应 ★
            try:
                import pyautogui as _pg_release
                for _key in ['ctrl', 'shift', 'alt', 'win']:
                    _pg_release.keyUp(_key)
                self.append_log("[回放] 已释放所有修饰键")
            except Exception:
                pass
            # ★ 回放结束后恢复全局热键处理器（只需清除标志位）★
            if _hooks_disabled:
                # ★ 策略变更：不再调用 _reinitialize_all_hotkeys，它可能破坏 keyboard 库状态
                # 只清除禁用标志，让热键回调正常工作
                self._hotkeys_temporarily_disabled = False
                self.debug_print("[回放] 已清除热键临时禁用标志，热键恢复响应")

                # ★ 主动自愈：回放过程（ctrl+a/ctrl+v/enter 高频模拟按键）可能让 keyboard 库的
                # 监听/处理线程崩溃（尤其非管理员权限下）。仅清标志位无法救活已死的线程，
                # 因此立即在后台线程跑一次健康检查：线程若已死会触发 _reinitialize_all_hotkeys 恢复；
                # 线程若仍存活则零副作用（不重初始化）。比单纯等待 1 秒健康检查更及时。
                try:
                    import threading as _th_reinit
                    _th_reinit.Thread(target=self._check_and_restore_hotkeys, daemon=True).start()
                    self.debug_print("[回放] 已触发热键健康检查（后台），自动恢复可能失效的线程")
                except Exception as _re_e:
                    self.debug_print(f"[回放] 触发热键健康检查失败: {_re_e}")

                # 简单诊断：检查 keyboard 库状态
                try:
                    import keyboard as _kb_simple
                    _hotkeys = len(getattr(_kb_simple, '_hotkeys', {}))
                    _listener = getattr(_kb_simple, '_listener', None)
                    if _listener:
                        _lt = getattr(_listener, 'listening_thread', None)
                        _lt_alive = _lt.is_alive() if _lt else False
                        _pt = getattr(_listener, 'processing_thread', None)
                        _pt_alive = _pt.is_alive() if _pt else False
                        _listening = getattr(_listener, 'listening', False)
                        self.debug_print(f"[回放诊断] _hotkeys={_hotkeys} | listen线程={_lt_alive} | process线程={_pt_alive} | listening={_listening}")
                except Exception as _e:
                    self.debug_print(f"[回放诊断] 检查失败: {_e}")

                # ★ 关键修复：keyboard 库可能因为 pyautogui 模拟按键而失效
                # 尝试通过调用 keyboard.hook() 来"激活"监听线程
                try:
                    import keyboard as _kb_reactivate
                    self.debug_print("[回放诊断] 尝试重新激活 keyboard 库...")
                    
                    # 检查 listening 状态
                    _listener = getattr(_kb_reactivate, '_listener', None)
                    if _listener:
                        _was_listening = getattr(_listener, 'listening', False)
                        self.debug_print(f"[回放诊断] 当前 listening={_was_listening}")

                        # ★ 不要添加临时钩子！它可能覆盖 process_event，导致事件处理链断裂
                        # 之前的尝试证明：添加空钩子会破坏 keyboard 库的内部状态
                        # _temp_hook = _kb_reactivate.hook(lambda e: None)  # 已禁用

                        # 验证状态
                        _listening_after = getattr(_listener, 'listening', False)
                        _lt_after = getattr(_listener, 'listening_thread', None)
                        _lt_alive_after = _lt_after.is_alive() if _lt_after else False
                        self.debug_print(f"[回放诊断] 激活后: listening={_listening_after}, listen线程={_lt_alive_after}")
                        
                        # ★ 新增：检查热键是否正确注册
                        _hk_dict = getattr(_kb_reactivate, '_hotkeys', {})
                        self.debug_print(f"[回放诊断] _hotkeys 字典中有 {len(_hk_dict)} 个条目")
                        # 打印热键字符串（不是函数对象）
                        _hk_keys = [k for k in _hk_dict.keys() if isinstance(k, str)]
                        self.debug_print(f"[回放诊断] 热键字符串: {_hk_keys[:10]}")
                        
                        # ★ 关键诊断：检查 keyboard 库的热键匹配状态
                        _pressed = getattr(_kb_reactivate, '_pressed_events', set())
                        self.debug_print(f"[回放诊断] 当前按下事件集合: {_pressed}")
                        
                        # ★ 真正的热键匹配字典在 _listener.nonblocking_hotkeys
                        _nb_hotkeys = getattr(_listener, 'nonblocking_hotkeys', {})
                        self.debug_print(f"[回放诊断] nonblocking_hotkeys 数量: {len(_nb_hotkeys)}")
                        # 打印前5个热键组合
                        _nb_keys = list(_nb_hotkeys.keys())[:5]
                        self.debug_print(f"[回放诊断] 热键组合示例: {_nb_keys}")
                        
                        # 检查物理和逻辑按下键
                        _phys_pressed = getattr(_kb_reactivate, '_physically_pressed_keys', set())
                        _log_pressed = getattr(_kb_reactivate, '_logically_pressed_keys', set())
                        self.debug_print(f"[回放诊断] 物理按下键: {_phys_pressed}, 逻辑按下键: {_log_pressed}")
                        
                        # ★ 尝试手动触发热键匹配测试
                        try:
                            # 测试 alt+m 是否在 _hotkeys 中
                            _test_hotkey = 'alt+m'
                            if _test_hotkey in _hk_dict:
                                self.debug_print(f"[回放诊断] ✅ '{_test_hotkey}' 在 _hotkeys 中")
                            else:
                                self.debug_print(f"[回放诊断] ❌ '{_test_hotkey}' 不在 _hotkeys 中")
                            
                            # ★ 关键修复：强制清空按下键集合，重置热键匹配状态
                            # keyboard 库有多种按下键状态，需要全部清空
                            _cleaned = []
                            for _attr in ['_pressed_events', '_physically_pressed_keys', '_logically_pressed_keys']:
                                if hasattr(_kb_reactivate, _attr):
                                    getattr(_kb_reactivate, _attr).clear()
                                    _cleaned.append(_attr)
                            if _cleaned:
                                self.debug_print(f"[回放诊断] ✅ 已清空按下键状态: {_cleaned}")

                            # ★ 不要清空 _triggers！它破坏了 keyboard 库的热键触发机制
                            # _triggers 用于追踪热键触发状态，清空它会导致热键无法被正确触发
                            # if hasattr(_kb_reactivate, '_triggers'):
                            #     _kb_reactivate._triggers.clear()

                            # 打印 _triggers 状态用于诊断
                            if hasattr(_kb_reactivate, '_triggers'):
                                self.debug_print(f"[回放诊断] _triggers 数量: {len(_kb_reactivate._triggers)}")

                            # 清空 hooks 中可能残留的状态
                            if hasattr(_kb_reactivate, '_hooks'):
                                # 不要清空 _hooks，只打印状态
                                self.debug_print(f"[回放诊断] _hooks 数量: {len(_kb_reactivate._hooks)}")
                        except Exception as _test_e:
                            self.debug_print(f"[回放诊断] 热键测试失败: {_test_e}")
                except Exception as _react_e:
                    self.debug_print(f"[回放诊断] 激活失败: {_react_e}")

            # ★★★ 修复：不再"完全重新初始化" keyboard 库 ★★★
            # 原因：回放期间热键只是置了 _hotkeys_temporarily_disabled 标志（并未 remove_hotkey），
            # 清掉标志后回调即可恢复（见 7185 的"新策略"注释）。
            # 旧代码这里调用 unhook_all() 会杀死 keyboard 的监听线程，导致之后重注册的热键
            # "按了没反应"（快捷键失效）——正是用户反馈的问题。故不再卸载/重注册热键。
            self.debug_print("[回放诊断] 跳过 keyboard 库重新初始化（避免 unhook_all 杀死监听线程）")

    def stop_replay(self):
        """停止当前回放（完全重置状态，同时停止所有组合技）"""
        try:
            # 清除批量播放队列
            if hasattr(self, '_batch_play_queue'):
                del self._batch_play_queue

            # 设置停止标志，让回放函数自行停止
            from image_recognition import set_replay_stop_flag
            set_replay_stop_flag(True)

            # 立即重置回放状态
            self.is_replaying = False
            self.replay_enabled = False
            # ★ 清除热键临时禁用标志
            self._hotkeys_temporarily_disabled = False
            
            # 同时停止所有组合技
            if hasattr(self, 'runners') and self.runners:
                STOP_JOIN_TIMEOUT = 3.0
                # 收集所有需要重置和等待的runner
                runners_to_reset = []
                for skill_id, runner in list(self.runners.items()):
                    if runner.isRunning():
                        runner.running = False
                        runners_to_reset.append((skill_id, runner))
                # 重置所有runner状态
                for skill_id, runner in runners_to_reset:
                    if hasattr(runner, 'reset'):
                        try:
                            runner.reset()
                        except Exception:
                            break
                # 注：移除主线程join等待，避免卡死UI，子线程会检测running标志自行退出
                # for skill_id, runner in runners_to_reset:
                #     try:
                #         if hasattr(runner, '_exec_thread') and runner._exec_thread is not None:
                #             runner._exec_thread.join(timeout=STOP_JOIN_TIMEOUT)
                #     except Exception:
                #         pass
                # 清空 runners
                self.runners.clear()
                self.append_log("[组合技] 所有运行中的组合技已停止，下次运行将从第一个流程重新开始")
            
            # 清除当前流程记录，确保下次从头开始
            if hasattr(self, 'current_recording'):
                # 不清除current_recording，保留以便重新播放
                pass
            
            self._update_replay_ui()
            self.debug_print("[回放控制] 已停止回放，状态已重置")
        except Exception as e:
            self.debug_print(f"停止回放失败: {e}")
    
    def save_replay_indicator_position(self):
        """保存回放指示器位置"""
        if not hasattr(self, 'replay_status_widget'):
            return
        
        try:
            config_path = os.path.join(self.user_data_dir, 'replay_indicator_position.json')
            config = {
                'x': self.replay_status_widget.x(),
                'y': self.replay_status_widget.y()
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.debug_print(f"保存回放指示器位置失败: {e}")

    def show_replay_indicator(self):
        # 单窗口模式：隐藏主窗口，只显示录制控制窗口
        self.hide()
        
        if not hasattr(self, 'replay_status_widget'):
            self.create_replay_status_indicator()
        else:
            # 刷新流程列表，确保新录制的流程立即显示
            self.refresh_floating_window_list()
            self.replay_status_widget.show()
            self.replay_status_widget.raise_()
            self.replay_status_widget.activateWindow()
    
    def close_replay_indicator(self):
        """关闭录制控制窗口并恢复主窗口显示"""
        # 关闭录制控制窗口
        if hasattr(self, 'replay_status_widget'):
            self.replay_status_widget.hide()
        
        # 单窗口模式：恢复主窗口显示
        self.showNormal()
        self.raise_()
        self.activateWindow()
    
    def switch_to_floating_window(self):
        """切换到悬浮窗口（录制控制窗口）"""
        # print("[调试] 切换到悬浮窗口")  # [日志已禁用]
        self.show_replay_indicator()
    
    def toggle_replay_status(self):
        """切换回放状态 - 用于快捷键

        说明：只切换状态,不再强制弹出悬浮窗口。悬浮窗口由用户通过
        "悬浮窗口" 按钮主动打开,或由回放/录制流程按需显示。
        """
        from PyQt5.QtCore import QTimer
        import traceback

        # 记录调用堆栈，便于调试
        # print(f"[DEBUG] toggle_replay_status 被调用，当前状态: {self.replay_enabled}")  # [日志已禁用]
        # print(f"[DEBUG] 调用堆栈:\n{traceback.format_stack()[-4:-1]}")  # [日志已禁用]

        def do_toggle():
            self.replay_enabled = not self.replay_enabled
            self.debug_print(f"[DEBUG] 回放状态已切换为: {self.replay_enabled}")
            if hasattr(self, 'replay_switch'):
                try:
                    self.replay_switch.setChecked(self.replay_enabled)
                except:
                    pass

            # 更新UI
            self._update_replay_ui()
            self.update_replay_status_indicator()
            # 不再强制弹出悬浮窗口

        QTimer.singleShot(0, do_toggle)

    def _update_replay_ui(self):
        """更新回放状态的UI显示 - 公共方法

        注意：主窗口的 replay_btn 现在是 RoundedPillButton（自绘按钮），
        不支持 setStyleSheet，只更新文字。样式由按钮自身的 paintEvent 处理。
        """
        # 更新主窗口按钮文字（仅当它是普通 QPushButton 时才设置样式）
        if hasattr(self, 'replay_btn'):
            if self.replay_enabled:
                self.replay_btn.setText("⏹ 回放已开启")
            else:
                self.replay_btn.setText("▶ 回放已关闭")
            # 强制刷新自绘按钮
            self.replay_btn.update()
            # 不要对 RoundedPillButton 调用 setStyleSheet，会破坏自绘

        # 更新悬浮窗口按钮文字和样式（floating_replay_btn 是普通 QPushButton）
        if hasattr(self, 'floating_replay_btn'):
            _closed_style = """
                QPushButton {
                    background-color: #F2F2F7;
                    color: #8E8E93;
                    border-radius: 22px;
                    padding: 0 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #E5E5EA;
                    color: #636366;
                }
                QPushButton:pressed {
                    background-color: #D1D1D6;
                    padding-top: 2px;
                }
            """
            _open_style = """
                QPushButton {
                    background-color: #F2F2F7;
                    color: #8E8E93;
                    border-radius: 22px;
                    padding: 0 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #E5E5EA;
                    color: #636366;
                }
                QPushButton:pressed {
                    background-color: #D1D1D6;
                    padding-top: 2px;
                }
            """
            if self.replay_enabled:
                self.floating_replay_btn.setText("● 回放已开启")
                self.floating_replay_btn.setStyleSheet(_open_style)
            else:
                self.floating_replay_btn.setText("● 回放已关闭")
                self.floating_replay_btn.setStyleSheet(_closed_style)

    def toggle_replay_status_only(self):
        """切换回放状态 - 只切换状态，不执行回放（用于按钮点击）

        说明：只切换状态,不再强制弹出悬浮窗口。悬浮窗口由用户通过
        "悬浮窗口" 按钮主动打开,或由回放/录制流程按需显示。
        """
        from PyQt5.QtCore import QTimer

        def do_toggle():
            # 记录悬浮窗口切换前的状态,确保切换回放状态不会让它从隐藏变成显示
            floating_was_visible = False
            if hasattr(self, 'replay_status_widget') and self.replay_status_widget is not None:
                try:
                    floating_was_visible = self.replay_status_widget.isVisible()
                except Exception:
                    floating_was_visible = False

            self.replay_enabled = not self.replay_enabled
            self.debug_print(f"[DEBUG] 回放状态已切换为: {self.replay_enabled}")

            # 更新UI(按钮文字、状态显示等)
            self._update_replay_ui()
            # 明确: 切换回放状态时,绝对不弹出悬浮窗口
            # 如果悬浮窗口之前是隐藏的,保持隐藏
            if hasattr(self, 'replay_status_widget') and self.replay_status_widget is not None:
                try:
                    if not floating_was_visible and self.replay_status_widget.isVisible():
                        self.replay_status_widget.hide()
                        self.debug_print(f"[DEBUG] 拦截了悬浮窗口的意外显示")
                except Exception:
                    pass
        QTimer.singleShot(0, do_toggle)

    def toggle_replay_playback(self):
        """切换回放播放/暂停 - 单击按钮即可播放/暂停，无需选择文件夹"""
        from PyQt5.QtCore import QTimer
        import traceback


        def do_toggle():
            try:
                # 检查当前是否有正在运行的回放
                is_replaying = getattr(self, 'is_replaying', False)

                if is_replaying:
                    # 如果有正在进行的回放，停止它
                    self.debug_print(f"[DEBUG] 停止当前回放")
                    self.stop_replay()
                    self.is_replaying = False
                    self.replay_enabled = False
                else:
                    # 如果没有回放，获取要播放的流程
                    current_recording = getattr(self, 'current_recording', None)

                    # 如果没有选中的流程，自动选择第一个流程
                    if not current_recording:
                        if hasattr(self, 'recording_checkboxes') and self.recording_checkboxes:
                            first_recording = list(self.recording_checkboxes.keys())[0]
                            current_recording = first_recording

                    # 开始回放
                    if current_recording:
                        self.debug_print(f"[DEBUG] 开始回放流程: {current_recording}")
                        self.is_replaying = True
                        self.replay_enabled = True
                        self.play_recording(current_recording)
                    else:
                        self.debug_print(f"[DEBUG] 没有可用的流程，无法开始回放")
            finally:
                # 始终更新按钮显示状态
                self._update_replay_ui()
        
        QTimer.singleShot(0, do_toggle)
    
    def enter_main_program(self):
        """从录制控制窗口进入主程序"""
        # 隐藏录制控制窗口
        if hasattr(self, 'replay_status_widget'):
            self.replay_status_widget.hide()
        
        # 显示主窗口
        self.showNormal()
        self.raise_()
        self.activateWindow()
    
    def show_main_window(self):
        """显示主窗口"""
        self.showNormal()
        self.raise_()
        self.activateWindow()
    
    def on_replay_switch_changed(self, state):
        """回放开关状态改变"""
        self.replay_enabled = (state == 2)
        self.debug_print(f"[DEBUG] 回放开关状态改变: replay_enabled = {self.replay_enabled}")
        
        # 同步更新主界面按钮状态
        self._update_replay_ui()
        if hasattr(self, 'replay_btn'):
            if self.replay_enabled:
                self.replay_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0A84FF;
                        color: white;
                        border-radius: 22px;
                        font-size: 18px;
                        font-weight: bold;
                        font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                    }
                    QPushButton:hover {
                        background-color: #FF453A;
                        color: white;
                    }
                    QPushButton:pressed {
                background-color: #004DB3;
                        color: white;
                    }
                """)
            else:
                self.replay_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #8E8E93;
                        color: white;
                        border-radius: 22px;
                        font-size: 18px;
                        font-weight: bold;
                        font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                    }
                    QPushButton:hover {
                        background-color: #FF453A;
                        color: white;
                    }
                    QPushButton:pressed {
                background-color: #004DB3;
                        color: white;
                    }
                """)
        
        self.update_replay_status_indicator()

    def show_floating_message(self, message):
        """显示浮动消息"""
        from PyQt5.QtWidgets import QLabel, QFrame
        from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QRect

        # 先关闭之前的浮动消息
        if hasattr(self, 'current_floating_message') and self.current_floating_message:
            try:
                self.current_floating_message.close()
                self.current_floating_message = None
            except:
                pass

        # 创建消息标签
        msg_label = QLabel(message)
        msg_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 255);
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
        """)

        # 设置窗口标志，使标签浮动在主窗口上方
        msg_label.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        msg_label.setAttribute(Qt.WA_TranslucentBackground)
        msg_label.setAttribute(Qt.WA_ShowWithoutActivating)
        msg_label.setAlignment(Qt.AlignCenter)

        # 先调整大小，确保尺寸正确
        msg_label.adjustSize()

        # 计算标签位置 - 使用屏幕中心
        screen = QApplication.primaryScreen().geometry()
        x = screen.x() + (screen.width() - msg_label.width()) // 2
        y = screen.y() + (screen.height() - msg_label.height()) // 2

        msg_label.move(x, y)

        # 显示标签
        msg_label.show()
        msg_label.raise_()

        # 2秒后自动关闭
        QTimer.singleShot(2000, msg_label.close)

        # 保存标签引用以便后续关闭
        self.current_floating_message = msg_label
    
    def close_floating_message(self):
        """关闭浮动消息"""
        if hasattr(self, 'current_floating_message') and self.current_floating_message:
            # 设置淡出动画
            fade_out = QPropertyAnimation(self.current_floating_message, b"windowOpacity")
            fade_out.setDuration(300)  # 300ms
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.InOutQuad)
            fade_out.finished.connect(self.current_floating_message.deleteLater)
            fade_out.start()
            
            # 清除引用
            self.current_floating_message = None

    def open_feedback_dialog(self):
        dialog = FeedbackDialog(self)
        dialog.exec_()

    def open_admin_console(self):
        """打开管理员控制台"""
        try:
            from admin_manager import AdminManager
            self.admin_window = AdminManager(self.login_manager)
            self.admin_window.show()
        except ImportError:
            self.show_beautiful_message('warning', '错误', '管理员模块加载失败')

    def initUI(self):
        desktop = QApplication.desktop()
        available_rect = desktop.availableGeometry()

        # 使用较小尺寸作为基准，确保窗口在任何屏幕上都合适
        min_dimension = min(available_rect.width(), available_rect.height())

        # 宽度设为较小尺寸的80%
        width = int(min_dimension * 0.8)
        # 高度设为较小尺寸的65%，确保不超出屏幕
        height = int(min_dimension * 0.65)

        # 强制限制最大高度为较小尺寸的65%
        max_h = int(min_dimension * 0.65)

        # 居中位置 - 使用屏幕中心点计算
        screen_center_x = available_rect.x() + available_rect.width() // 2
        screen_center_y = available_rect.y() + available_rect.height() // 2
        
        x = screen_center_x - width // 2
        y = screen_center_y - height // 2

        self.setGeometry(x, y, width, height)
        # 使用setFixedHeight确保高度不会被改变
        self.setFixedHeight(max_h)
        self.setMaximumHeight(max_h)
        
        # 保存窗口大小，以便后续使用
        self.window_width = width
        self.window_height = max_h
        
        # 应用统一样式
        if APP_STYLES_AVAILABLE:
            apply_window_style(self, available_rect.width(), available_rect.height())

        # 创建中央部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 5)

        # 保存初始屏幕尺寸
        self.screen_width = available_rect.width()
        self.screen_height = available_rect.height()
        
        # 创建TabWidget整合所有功能
        self.create_tab_ui(main_layout)

        # 创建托盘图标
        self.create_tray_icon()

        # 应用macOS主题全局样式覆盖
        self.apply_candy_theme()

    def apply_candy_theme(self):
        """应用macOS主题样式 - 覆盖所有硬编码颜色"""
        candy_theme = f"""
            QWidget {{
                background-color: {THEME_BG};
                color: {THEME_TEXT};
            }}
            QPushButton {{
                background-color: {THEME_PRIMARY};
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: {THEME_SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
            QLineEdit, QTextEdit {{
                background-color: {THEME_BG};
                color: {THEME_TEXT};
                border: 2px solid {THEME_BORDER};
                border-radius: 6px;
                padding: 6px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {THEME_PRIMARY};
            }}
            QTabWidget::pane {{
                border: 1px solid {THEME_BORDER};
                background-color: {THEME_BG};
            }}
            QTabBar::tab:selected {{
                background-color: {THEME_PRIMARY};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #fff5f5;
                color: {THEME_PRIMARY};
            }}
            QCheckBox {{
                color: {THEME_TEXT};
            }}
            QCheckBox::indicator:checked {{
                background-color: {THEME_PRIMARY};
                border-color: {THEME_PRIMARY};
            }}
            QRadioButton {{
                color: {THEME_TEXT};
            }}
            QRadioButton::indicator:checked {{
                background-color: {THEME_PRIMARY};
                border-color: {THEME_PRIMARY};
            }}
            QSlider::handle:horizontal {{
                background: {THEME_PRIMARY};
            }}
            QSlider::sub-page:horizontal {{
                background: {THEME_PRIMARY};
            }}
            QComboBox {{
                background-color: {THEME_BG};
                color: {THEME_TEXT};
                border: 1px solid {THEME_BORDER};
                border-radius: 6px;
            }}
            QComboBox::drop-down {{
            }}
            QMenu {{
                background-color: {THEME_CARD};
                color: {THEME_TEXT};
                border: 1px solid {THEME_BORDER};
            }}
            QMenu::item:selected {{
                background-color: #fff5f5;
                color: {THEME_PRIMARY};
            }}
            QScrollBar:vertical {{
                background: #fafafa;
            }}
            QScrollBar::handle:vertical {{
                background: #d0d0d0;
            }}
            QScrollBar:horizontal {{
                background: #fafafa;
            }}
            QScrollBar::handle:horizontal {{
                background: #d0d0d0;
            }}
        """
        self.setStyleSheet(candy_theme)

        # 直接设置子组件样式，覆盖 create_tab_ui 中的硬编码颜色
        if hasattr(self, 'tab_widget') and self.tab_widget:
            self.tab_widget.setStyleSheet(f"""
                QTabWidget::pane {{
                    border: 1px solid {THEME_BORDER};
                    border-radius: 6px;
                    background: {THEME_CARD};                }}
                QTabBar::tab {{
                    background: {THEME_CARD};
                    border: 1px solid {THEME_BORDER};
                    border-bottom: none;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    padding: 6px 12px;
                    min-width: 60px;
                    font-size: 14px;
                    font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                    color: {THEME_MUTED};
                    font-weight: 500;
                }}
                QTabBar::tab:selected {{
                    background: {THEME_PRIMARY};
                    color: white;
                    border-color: {THEME_PRIMARY};
                }}
                QTabBar::tab:hover:!selected {{
                    background: #fff5f5;
                    color: {THEME_PRIMARY};
                }}
            """)

    def create_tab_ui(self, main_layout):
        """创建TabWidget整合所有功能 - 替代多个弹窗"""
        from PyQt5.QtWidgets import QTabWidget

        # 创建TabWidget - 使用macOS主题颜色
        self.tab_widget = QTabWidget()
        
        # Tab 0: 录制控制
        self.record_tab = self.create_record_tab()
        self.tab_widget.addTab(self.record_tab, "录制")

        # Tab 1: 流程管理（简化版，直接显示功能按钮）
        self.manager_tab = self.create_manager_tab()
        self.tab_widget.addTab(self.manager_tab, "流程管理")

        # Tab 2: 组合技（简化版，直接显示功能按钮）
        self.combo_tab = self.create_combo_tab()
        self.tab_widget.addTab(self.combo_tab, "组合技")

        # Tab 3: 设置
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "设置")

        # Tab 4: 帮助
        self.help_tab = self.create_help_tab()
        self.tab_widget.addTab(self.help_tab, "帮助")
        
        main_layout.addWidget(self.tab_widget)
        
        # 底部录制按钮已移除
        # self.create_record_button(main_layout)
    
    def create_record_tab(self):
        """创建录制控制Tab页面 - 简约惊艳风格"""
        tab = QWidget()
        tab.setStyleSheet("background-color: #f5f7fa;")
        layout = QVBoxLayout(tab)
        layout.setSpacing(24)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignTop)

        class PillButton(QPushButton):
            """iOS 风格药丸按钮 - 自绘确保绝对圆润"""
            def __init__(self, text="", color_top="#0A84FF", color_mid="#0A84FF", color_bottom="#004DB3",
                         text_color="white", parent=None):
                super().__init__(text, parent)
                self.setCursor(Qt.PointingHandCursor)
                self._hovered = False
                self._pressed = False
                self._color_top = color_top
                self._color_mid = color_mid
                self._color_bottom = color_bottom
                self._text_color = text_color
                self.setAttribute(Qt.WA_TranslucentBackground, True)
                self.setAttribute(Qt.WA_NoSystemBackground, True)
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
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

                rect = QRectF(0, 0, self.width(), self.height())
                radius = self.height() / 2.0

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

                painter.setPen(QColor(self._text_color))
                font = QFont()
                font.setFamilies(['PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', 'sans-serif'])
                font.setPixelSize(15)
                # PyQt5 没有 QFont.Medium(500),用数值 500
                font.setWeight(500)
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
                return PillButton._lighten(hex_color, factor)

        class RecordCircleButton(QPushButton):
            """iOS 17 风格录制按钮 - 圆环 + 内部状态指示(圆/方) + 下方文字"""
            def __init__(self, text="", parent=None):
                super().__init__(text, parent)
                self.setCursor(Qt.PointingHandCursor)
                self._hovered = False
                self._pressed = False
                self._recording = False
                self.setAttribute(Qt.WA_TranslucentBackground, True)
                self.setAttribute(Qt.WA_NoSystemBackground, True)

            def set_recording(self, rec):
                self._recording = rec
                self.update()

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
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

                w, h = self.width(), self.height()
                cx, cy = w / 2, h / 2 - 8  # 圆心稍微上移,给文字留位置
                ring_radius = min(w, h) * 0.36  # 圆环半径

                # 1. 外发光阴影(hover 时增强)
                if self._hovered or self._pressed:
                    shadow_color = QColor(255, 59, 48, 80 if self._pressed else 60)
                    for i in range(8, 0, -1):
                        glow = QColor(255, 59, 48, max(8, 30 - i * 3))
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(QBrush(glow))
                        painter.drawEllipse(QPointF(cx, cy), ring_radius + i * 1.2, ring_radius + i * 1.2)

                # 2. 外环(细白线)
                ring_pen = QPen(QColor(220, 220, 225), 2)
                painter.setPen(ring_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(cx, cy), ring_radius, ring_radius)

                # 3. 内圆(大渐变红圆 - 比外环小一圈)
                inner_radius = ring_radius - 8
                if self._recording:
                    # 录制中: 圆变方(经典 iOS 录制指示)
                    square_size = (inner_radius - 4) * 1.4
                    square_rect = QRectF(cx - square_size/2, cy - square_size/2, square_size, square_size)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor("#FF453A")))
                    painter.drawRoundedRect(square_rect, 6, 6)
                else:
                    # 未录制: 漂亮的大红色渐变圆
                    inner_rect = QRectF(cx - inner_radius, cy - inner_radius,
                                        inner_radius * 2, inner_radius * 2)
                    gradient = QRadialGradient(cx - inner_radius * 0.3, cy - inner_radius * 0.3, inner_radius * 1.5)
                    if self._pressed:
                        gradient.setColorAt(0.0, QColor("#FF6B61"))
                        gradient.setColorAt(0.7, QColor("#E5352B"))
                        gradient.setColorAt(1.0, QColor("#A01510"))
                    elif self._hovered:
                        gradient.setColorAt(0.0, QColor("#FF8B82"))
                        gradient.setColorAt(0.6, QColor("#FF453A"))
                        gradient.setColorAt(1.0, QColor("#D9231B"))
                    else:
                        gradient.setColorAt(0.0, QColor("#FF6961"))
                        gradient.setColorAt(0.55, QColor("#FF453A"))
                        gradient.setColorAt(1.0, QColor("#C71D14"))
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(gradient))
                    painter.drawEllipse(inner_rect)

                    # 4. 高光(左上角光斑,让圆更立体)
                    highlight = QRectF(cx - inner_radius * 0.7, cy - inner_radius * 0.85,
                                       inner_radius * 0.7, inner_radius * 0.5)
                    highlight_gradient = QLinearGradient(cx, cy - inner_radius, cx, cy)
                    highlight_gradient.setColorAt(0.0, QColor(255, 255, 255, 100))
                    highlight_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
                    painter.setBrush(QBrush(highlight_gradient))
                    painter.drawEllipse(highlight)

                # 5. 下方文字(在圆环下面,而不是中间)
                text_y = cy + ring_radius + 16
                text_color = QColor("#1a1a2e") if not self._recording else QColor("#FF453A")
                painter.setPen(text_color)
                font = QFont()
                font.setFamilies(['PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', 'sans-serif'])
                font.setPixelSize(15)
                font.setBold(True)
                painter.setFont(font)
                text_rect = QRectF(0, text_y - 12, w, 24)
                painter.drawText(text_rect, Qt.AlignCenter, self.text())

        # 主卡片容器
        main_card = QWidget()
        main_card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e8ecf0;
            }
        """)
        card_layout = QVBoxLayout(main_card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(32, 32, 32, 32)

        # 录制区域标题
        record_title = QLabel("录制控制")
        record_title.setStyleSheet("""
            QLabel {
                color: #1a1a2e;
                font-size: 20px;
                font-weight: 600;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                background: transparent;
                border: none;
            }
        """)
        card_layout.addWidget(record_title)

        # 录制按钮区域 - 水平布局
        record_area = QWidget()
        record_area.setStyleSheet("background: transparent; border: none;")
        record_layout = QHBoxLayout(record_area)
        record_layout.setSpacing(12)
        record_layout.setContentsMargins(0, 0, 0, 0)

        # 录制按钮 - iOS 17 录制圆按钮(自绘,绝对圆润)
        self.record_btn = RecordCircleButton("开始录制")
        self.record_btn.setFixedSize(140, 165)  # 140x140 圆 + 25 文字
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.clicked.connect(lambda: QTimer.singleShot(0, self.toggle_recording))
        record_layout.addWidget(self.record_btn)

        # 录制模式选择 - 简约下拉框
        mode_widget = QWidget()
        mode_widget.setStyleSheet("background: transparent; border: none;")
        mode_layout = QVBoxLayout(mode_widget)
        mode_layout.setSpacing(8)
        mode_layout.setContentsMargins(0, 0, 0, 0)

        self.record_mode_combo = QComboBox()
        self.record_mode_combo.addItems(["图像录制", "坐标录制"])
        self.record_mode_combo.setFixedWidth(160)
        self.record_mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                color: black;
                border: 1px solid #D1D1D6;
                border-radius: 12px;
                padding: 8px 32px 8px 16px;
                font-size: 14px;
                font-weight: 500;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                min-height: 36px;
            }
            QComboBox:hover {
                border-color: #0A84FF;
                background-color: #FFFFFF;
            }
            QComboBox:focus {
                border-color: #0A84FF;
                outline: none;
            }
            QComboBox::drop-down {
                width: 32px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTEgMSIgc3Ryb2tlPSIjOEU4RTkzIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: black;
                border: 1px solid #D1D1D6;
                border-radius: 12px;
                selection-background-color: #0A84FF;
                selection-color: white;
                padding: 4px 0;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 16px;
                min-height: 32px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #F0F4FF;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0A84FF;
                color: white;
            }
        """)
        self.record_mode_combo.currentTextChanged.connect(self.update_record_button_text)
        mode_layout.addWidget(self.record_mode_combo)
        record_layout.addWidget(mode_widget)
        record_layout.addStretch()
        card_layout.addWidget(record_area)

        # 分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e8ecf0;")
        card_layout.addWidget(separator)

        # 回放控制区域
        replay_area = QWidget()
        replay_area.setStyleSheet("background: transparent; border: none;")
        replay_layout = QHBoxLayout(replay_area)
        replay_layout.setSpacing(16)
        replay_layout.setContentsMargins(0, 0, 0, 0)

        # 回放状态按钮 - 药丸形状(iOS 风格,自绘)
        self.replay_btn = PillButton("▶ 开始回放",
                                     color_top="#E8ECF0", color_mid="#D1D5DB", color_bottom="#C0C4CC",
                                     text_color="#2C3E50")
        self.replay_btn.setFixedHeight(44)
        self.replay_btn.clicked.connect(self.toggle_replay_playback)
        replay_layout.addWidget(self.replay_btn)

        # 切换到悬浮窗口按钮 - 药丸形状(iOS 风格,自绘)
        float_btn = PillButton("悬浮窗口",
                               color_top="#0A84FF", color_mid="#0A84FF", color_bottom="#004DB3",
                               text_color="white")
        float_btn.setFixedHeight(44)
        float_btn.clicked.connect(self.switch_to_floating_window)
        replay_layout.addWidget(float_btn)
        replay_layout.addStretch()
        card_layout.addWidget(replay_area)

        layout.addWidget(main_card)
        layout.addStretch()
        return tab
    
    def create_settings_tab(self):
        """创建设置Tab页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 字体大小设置
        font_btn = QPushButton("📝 字体大小设置")
        font_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_PRIMARY};
                color: white;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                text-align: left;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
        """)
        font_btn.clicked.connect(self.open_font_size_dialog)
        layout.addWidget(font_btn)

        # 快捷键设置
        shortcut_btn = QPushButton("⌨️ 快捷键设置")
        shortcut_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_PRIMARY};
                color: white;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                text-align: left;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
        """)
        shortcut_btn.clicked.connect(self.show_shortcut_settings)
        layout.addWidget(shortcut_btn)

        # 调试模式开关 - 已移除
        # debug_btn = QPushButton("🐛 调试模式: 开" if getattr(self, 'debug_mode', True) else " 调试模式: 关")
        # debug_btn.setObjectName("debug_mode_btn")
        # debug_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #faad14;
        #         color: white;
        #         border: none;
        #         border-radius: 6px;
        #         padding: 12px 20px;
        #         font-size: 14px;
        #         text-align: left;
        #     }
        #     QPushButton:hover {
        #         background-color: #ffc53d;
        #     }
        # """)
        # debug_btn.clicked.connect(lambda: self.on_debug_mode_toggle(debug_btn))
        # layout.addWidget(debug_btn)

        # 查看日志按钮
        log_btn = QPushButton("📋 查看运行日志")
        log_btn.setStyleSheet("""
            QPushButton {
                background-color: #722ed1;
                color: white;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #9254de;
            }
        """)
        log_btn.clicked.connect(self.show_log_window)
        layout.addWidget(log_btn)

        layout.addStretch()
        return tab

    def on_debug_mode_toggle(self, btn):
        """切换调试模式并更新按钮显示"""
        is_enabled = self.toggle_debug_mode()
        if is_enabled:
            btn.setText("🐛 调试模式: 开")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #faad14;
                    color: white;
                    border-radius: 6px;
                    padding: 12px 20px;
                    font-size: 14px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #ffc53d;
                }
            """)
            self.show_beautiful_message('information', "调试模式", "调试模式已开启\n\n回放和组合技运行时将输出详细调试信息到控制台", parent=self)
        else:
            btn.setText("🐛 调试模式: 关")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #52c41a;
                    color: white;
                    border-radius: 6px;
                    padding: 12px 20px;
                    font-size: 14px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #73d13d;
                }
            """)
            self.show_beautiful_message('information', "调试模式", "调试模式已关闭", parent=self)

    def create_help_tab(self):
        """创建使用帮助Tab页面 - 分步引导教程"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # 帮助卡片
        help_card = QWidget()
        help_card.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        help_layout = QVBoxLayout(help_card)

        # 标题
        title_label = QLabel("📖 使用教程")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2C3E50;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                background: transparent;
            }
        """)
        help_layout.addWidget(title_label)

        # 步骤列表
        steps = [
            {
                "title": "步骤 1：快捷键介绍",
                "content": """
                    <div style="font-size: 18px; line-height: 2.2; color: #2C3E50;">
                    <p style="font-weight: bold; color: #FF453A;">⌨️ 记住这两个快捷键！</p>
                    <p>&nbsp;&nbsp;• <b>· 键</b>（反引号键，在键盘数字1左边）：开始/停止录制</p>
                    <p>&nbsp;&nbsp;• <b>Home 键</b>：一键回到主窗口</p>
                    </div>
                """,
                "icon": "⌨️"
            },
            {
                "title": "步骤 2：开始录制你的第一个流程",
                "content": """
                    <div style="font-size: 18px; line-height: 2.2; color: #2C3E50;">
                    <p style="font-weight: bold; color: #FF453A;">🎬 开始录制</p>
                    <p>&nbsp;&nbsp;1️⃣ 点击「录制」按钮（或按 · 键）开始</p>
                    <p>&nbsp;&nbsp;2️⃣ 在屏幕上执行你要录制的操作</p>
                    <p>&nbsp;&nbsp;3️⃣ 再次点击「录制」按钮（或按 · 键）停止</p>
                    <p>&nbsp;&nbsp;💡 录制时会自动截图，方便后续编辑查看</p>
                    </div>
                """,
                "icon": "🎬"
            },
            {
                "title": "步骤 3：管理录制的流程",
                "content": """
                    <div style="font-size: 18px; line-height: 2.2; color: #2C3E50;">
                    <p style="font-weight: bold; color: #FF453A;">📁 查看和管理你的流程</p>
                    <p>&nbsp;&nbsp;1️⃣ 点击「流程管理」标签页</p>
                    <p>&nbsp;&nbsp;2️⃣ 点击流程名称查看录制的截图</p>
                    <p>&nbsp;&nbsp;3️⃣ 在这里你可以：</p>
                    <p>&nbsp;&nbsp;&nbsp;&nbsp;• 重命名流程</p>
                    <p>&nbsp;&nbsp;&nbsp;&nbsp;• 设置快捷键一键执行</p>
                    <p>&nbsp;&nbsp;&nbsp;&nbsp;• 删除不需要的流程</p>
                    </div>
                """,
                "icon": "📁"
            },
            {
                "title": "步骤 4：编辑流程中的操作",
                "content": """
                    <div style="font-size: 18px; line-height: 2.2; color: #2C3E50;">
                    <p style="font-weight: bold; color: #FF453A;">✏️ 修改录制好的操作</p>
                    <p>&nbsp;&nbsp;1️⃣ 在流程管理中，点击流程名称</p>
                    <p>&nbsp;&nbsp;2️⃣ 每张图片下方都有操作标签</p>
                    <p>&nbsp;&nbsp;3️⃣ 点击这些标签可以修改操作：</p>
                    <p>&nbsp;&nbsp;&nbsp;&nbsp;• <span style="color: #FF9500;">👆 Click/右击</span>：切换点击类型</p>
                    <p>&nbsp;&nbsp;&nbsp;&nbsp;• <span style="color: #0A84FF;">⌨️ 按键</span>：修改按键</p>
                    <p>&nbsp;&nbsp;&nbsp;&nbsp;• <span style="color: #A6E3A1;">📝 文本</span>：修改文本内容</p>
                    </div>
                """,
                "icon": "✏️"
            },
            {
                "title": "步骤 5：创建组合技（进阶）",
                "content": """
                    <div style="font-size: 18px; line-height: 2.2; color: #2C3E50;">
                    <p style="font-weight: bold; color: #FF453A;">⚡ 更强大的组合技</p>
                    <p>&nbsp;&nbsp;1️⃣ 点击「组合技」标签页</p>
                    <p>&nbsp;&nbsp;2️⃣ 可以把多个流程组合起来</p>
                    <p>&nbsp;&nbsp;3️⃣ 设置条件，自动选择执行哪个流程</p>
                    </div>
                """,
                "icon": "⚡"
            },
            {
                "title": "完成！开始使用吧！",
                "content": """
                    <div style="font-size: 18px; line-height: 2.2; color: #2C3E50;">
                    <p style="font-weight: bold; color: #34C759;">🎉 恭喜你，已经掌握基本操作了！</p>
                    <p>&nbsp;&nbsp;💡 建议先录制一个简单的测试流程试试</p>
                    <p>&nbsp;&nbsp;💡 遇到问题随时回来查看</p>
                    <p>&nbsp;&nbsp;祝您使用愉快！</p>
                    </div>
                """,
                "icon": "🎉"
            }
        ]

        # 当前步骤索引
        current_step = 0
        total_steps = len(steps)

        # 进度指示器容器
        indicator_layout = QHBoxLayout()
        indicator_layout.addStretch()
        indicators = []
        for i in range(total_steps):
            indicator = QPushButton(f"{i+1}")
            indicator.setFixedSize(36, 36)
            if i == 0:
                indicator.setStyleSheet("""
                    QPushButton {
                        background-color: #0A84FF;
                        color: white;
                        border-radius: 18px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                """)
            else:
                indicator.setStyleSheet("""
                    QPushButton {
                        background-color: #D1D1D6;
                        color: #8E8E93;
                        border-radius: 18px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                """)
            indicator_layout.addWidget(indicator)
            indicators.append(indicator)
        indicator_layout.addStretch()
        help_layout.addLayout(indicator_layout)
        
        help_layout.addSpacing(15)

        # 内容显示区域
        content_card = QWidget()
        content_card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        content_layout = QVBoxLayout(content_card)

        # 步骤标题
        step_title = QLabel(f"{steps[0]['icon']} {steps[0]['title']}")
        step_title.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #2C3E50;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                background: transparent;
            }
        """)
        content_layout.addWidget(step_title)
        
        content_layout.addSpacing(10)

        # 步骤内容
        step_content = QLabel(steps[0]['content'])
        step_content.setWordWrap(True)
        step_content.setStyleSheet("background: transparent;")
        content_layout.addWidget(step_content)

        help_layout.addWidget(content_card)

        help_layout.addSpacing(20)

        # 导航按钮
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        # 上一步按钮
        prev_btn = QPushButton("← 上一步")
        prev_btn.setFixedSize(120, 44)
        prev_btn.setEnabled(False)  # 第一步时禁用
        prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #E5E5EA;
                color: #2C3E50;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QPushButton:hover:!disabled {
                background-color: #D1D1D6;
            }
            QPushButton:!enabled {
                opacity: 0.5;
            }
        """)
        nav_layout.addWidget(prev_btn)

        nav_layout.addSpacing(20)

        # 下一步按钮
        next_btn = QPushButton("下一步 →")
        next_btn.setFixedSize(120, 44)
        next_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #006AE0;
            }
        """)
        nav_layout.addWidget(next_btn)

        nav_layout.addStretch()
        help_layout.addLayout(nav_layout)

        layout.addWidget(help_card)
        layout.addStretch()

        # 定义更新步骤的函数
        def update_step(step_idx):
            nonlocal current_step
            current_step = step_idx

            # 更新内容
            step = steps[step_idx]
            step_title.setText(f"{step['icon']} {step['title']}")
            step_content.setText(step['content'])

            # 更新指示器
            for i, indicator in enumerate(indicators):
                if i == step_idx:
                    indicator.setStyleSheet("""
                        QPushButton {
                            background-color: #0A84FF;
                            color: white;
                            border-radius: 18px;
                            font-size: 16px;
                            font-weight: bold;
                        }
                    """)
                elif i < step_idx:
                    indicator.setStyleSheet("""
                        QPushButton {
                            background-color: #34C759;
                            color: white;
                            border-radius: 18px;
                            font-size: 16px;
                            font-weight: bold;
                        }
                    """)
                else:
                    indicator.setStyleSheet("""
                        QPushButton {
                            background-color: #D1D1D6;
                            color: #8E8E93;
                            border-radius: 18px;
                            font-size: 16px;
                            font-weight: bold;
                        }
                    """)

            # 更新按钮状态
            prev_btn.setEnabled(step_idx > 0)
            if step_idx == total_steps - 1:
                next_btn.setText("重新开始 ↺")
            else:
                next_btn.setText("下一步 →")

        # 按钮点击事件
        def go_prev():
            if current_step > 0:
                update_step(current_step - 1)

        def go_next():
            if current_step < total_steps - 1:
                update_step(current_step + 1)
            else:
                # 最后一步，回到第一步
                update_step(0)

        prev_btn.clicked.connect(go_prev)
        next_btn.clicked.connect(go_next)

        # 指示器点击事件
        for i, indicator in enumerate(indicators):
            def make_go_to_step(idx=i):
                return lambda: update_step(idx)
            indicator.clicked.connect(make_go_to_step())

        return tab
    
    def create_manager_tab(self):
        """创建流程管理Tab页面 - 完整功能版"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 顶部按钮区域
        top_layout = QHBoxLayout()

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_PRIMARY};
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 12px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
        """)
        top_layout.addWidget(refresh_btn)
        
        # 回收站按钮
        trash_btn = QPushButton("🗑️ 回收站")
        trash_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
        """)
        top_layout.addWidget(trash_btn)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # 使用QTableWidget显示流程列表（支持更多操作）
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView
        from design_system import configure_table, get_table_stylesheet

        folder_table = QTableWidget()
        folder_table.setColumnCount(5)
        folder_table.setHorizontalHeaderLabels(["时间", "流程名称", "快捷键", "重命名", "删除"])
        configure_table(folder_table, get_table_stylesheet(
            cell_padding_v=8, cell_padding_h=12, row_height=44
        ))

        # 添加单击事件 - 点击流程名称打开查看图片窗口，点击Emoji执行操作
        def on_folder_table_click(row, column):
            if column == 1:  # 流程名称列
                item = folder_table.item(row, column)
                if item:
                    folder_path = item.data(Qt.UserRole)
                    if folder_path and os.path.exists(folder_path):
                        # print(f"[Tab] 单击打开流程: {folder_path}")  # [日志已禁用]
                        self.open_view_images_in_tab(folder_path)
            elif column == 2:  # 快捷键列
                item = folder_table.item(row, column)
                if item:
                    data = item.data(Qt.UserRole)
                    if data and data[0] == "shortcut":
                        self.set_folder_shortcut_in_tab(data[1], folder_table)
            elif column == 3:  # 重命名列
                item = folder_table.item(row, column)
                if item:
                    data = item.data(Qt.UserRole)
                    if data and data[0] == "rename":
                        self.rename_folder_in_tab(data[1], folder_table)
            elif column == 4:  # 删除列
                item = folder_table.item(row, column)
                if item:
                    data = item.data(Qt.UserRole)
                    if data and data[0] == "delete":
                        self.delete_folder_in_tab(data[1], folder_table)
        
        folder_table.cellClicked.connect(on_folder_table_click)
        # ★ 流程管理Tab 右键菜单（已执行次数 / 设置默认间隔 / 删除）
        # 用事件过滤器直接拦截右键，比 customContextMenuRequested 信号更可靠
        folder_table.setContextMenuPolicy(Qt.CustomContextMenu)
        _folder_ctx_filter = _FolderTableCtxFilter(
            folder_table, self.show_folder_table_context_menu
        )
        folder_table.viewport().installEventFilter(_folder_ctx_filter)
        folder_table.installEventFilter(_folder_ctx_filter)
        folder_table._ctx_filter = _folder_ctx_filter  # 保持引用，防止被 GC
        layout.addWidget(folder_table)
        
        # 连接按钮
        refresh_btn.clicked.connect(lambda: self.load_folders_to_table(folder_table))
        trash_btn.clicked.connect(self.open_trash_dialog)
        
        # 加载流程列表
        self.load_folders_to_table(folder_table)
        
        # 保存引用
        tab.folder_table = folder_table
        
        return tab
    
    def load_folders_to_table(self, table_widget):
        """加载流程到表格"""
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
            
            # 加载调用次数
            counts = self._get_usage_counts()
            for fi in range(len(folders)):
                fi_name = folders[fi][1]
                fi_count = counts.get(fi_name, 0)
                folders[fi] = folders[fi] + (fi_count,)
            # 按调用次数排序（多者在前），次数相同的按时间排序
            folders.sort(key=lambda x: (-x[3], x[0]), reverse=False)
            # 恢复原始格式
            folders = [(f[0], f[1], f[2]) for f in folders]
            
            table_widget.setRowCount(len(folders))
            for row, (ctime, name, path) in enumerate(folders):
                # 时间
                table_widget.setItem(row, 0, QTableWidgetItem(ctime))
                # 名称
                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.UserRole, path)
                table_widget.setItem(row, 1, name_item)
                # 快捷键（从配置加载）
                shortcut = self.get_folder_shortcut(path)
                shortcut_item = QTableWidgetItem(shortcut if shortcut else "未设置")
                shortcut_item.setData(Qt.UserRole, ("shortcut", path))
                shortcut_item.setForeground(QColor("#1890ff") if shortcut else QColor("#999"))
                table_widget.setItem(row, 2, shortcut_item)
                # 重命名 - 使用彩色Emoji作为单元格内容
                rename_item = QTableWidgetItem("✏️")
                rename_item.setTextAlignment(Qt.AlignCenter)
                rename_item.setData(Qt.UserRole, ("rename", path))
                rename_item.setForeground(QColor("#1890ff"))  # 蓝色
                table_widget.setItem(row, 3, rename_item)
                # 删除 - 使用彩色Emoji作为单元格内容
                delete_item = QTableWidgetItem("🗑️")
                delete_item.setTextAlignment(Qt.AlignCenter)
                delete_item.setData(Qt.UserRole, ("delete", path))
                delete_item.setForeground(QColor("#ff4d4f"))  # 红色
                table_widget.setItem(row, 4, delete_item)
                
            # 调整列宽 - 给按钮列更多空间
            table_widget.setColumnWidth(0, 100)  # 时间
            table_widget.setColumnWidth(1, 200)  # 流程名称
            table_widget.setColumnWidth(2, 80)   # 快捷键
            table_widget.setColumnWidth(3, 70)   # 重命名按钮
            table_widget.setColumnWidth(4, 55)   # 删除按钮
                
        except Exception as e:
            # print(f"加载流程列表失败: {e}")  # [日志已禁用]
            pass


    def show_folder_table_context_menu(self, position, folder_table):
        """流程管理Tab的表格右键菜单：已执行次数 / 设置默认间隔 / 删除"""
        try:
            row = folder_table.rowAt(position.y())
            # 点到空白/表头区域时 rowAt 返回 -1，兜底选最接近的一行，保证菜单一定能弹出
            if row < 0 and folder_table.rowCount() > 0:
                best, best_dist = 0, 10 ** 9
                for r in range(folder_table.rowCount()):
                    rect = folder_table.visualRect(folder_table.model().index(r, 1))
                    mid = rect.top() + rect.height() // 2
                    d = abs(position.y() - mid)
                    if d < best_dist:
                        best_dist, best = d, r
                row = best
            if row < 0 or row >= folder_table.rowCount():
                return
            name_item = folder_table.item(row, 1)  # 流程名称列
            if not name_item:
                return
            folder_path = name_item.data(Qt.UserRole)
            if not folder_path or not os.path.exists(folder_path):
                return
            folder_name = os.path.basename(folder_path)
            try:
                usage_counts = self._get_usage_counts()
                count = usage_counts.get(folder_name, 0)
            except Exception:
                count = 0
            from PyQt5.QtWidgets import QMenu
            menu = QMenu(self)
            count_action = menu.addAction(f"已执行 {count} 次")
            count_action.setEnabled(False)
            menu.addSeparator()
            interval_action = QAction("设置默认间隔", self)
            interval_action.triggered.connect(lambda: self.set_folder_interval_in_tab(folder_path))
            menu.addAction(interval_action)
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(lambda: self.delete_folder_in_tab(folder_path, folder_table))
            menu.addAction(delete_action)
            menu.exec_(folder_table.viewport().mapToGlobal(position))
        except Exception:
            import traceback
            traceback.print_exc()

    def set_folder_interval_in_tab(self, folder_path):
        """流程管理Tab：设置流程文件夹的默认操作间隔（秒）"""
        folder_name = os.path.basename(folder_path)
        current_interval = self.folder_intervals.get(folder_path, self.replay_interval)

        from PyQt5.QtWidgets import QDoubleSpinBox

        dialog = QDialog(self)
        dialog.setWindowTitle("设置默认间隔")
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        width, height = get_screen_size(0.3)
        dialog.resize(width, int(height * 0.32))
        dialog.setWindowModality(Qt.WindowModal)
        dialog.activateWindow()
        apply_dialog_style(dialog, 0.3, 0.32)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        screen_width, screen_height = get_screen_size()

        instruction_label = QLabel(f"设置流程「{folder_name}」的默认操作间隔")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_font_size = int(screen_height * 0.025)
        instruction_label.setStyleSheet(f"font-size: {instruction_font_size}px; color: #0A84FF; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(instruction_label)

        spin = QDoubleSpinBox()
        spin.setRange(0.0, 10.0)
        spin.setSingleStep(0.01)
        spin.setDecimals(3)
        try:
            spin.setValue(float(current_interval))
        except (TypeError, ValueError):
            spin.setValue(0.001)
        spin.setSuffix(" 秒")
        spin_font_size = int(screen_height * 0.03)
        spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                font-size: {spin_font_size}px;
                padding: 8px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: white;
                min-height: 35px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QDoubleSpinBox:focus {{ border-color: #0A84FF; }}
        """)
        layout.addWidget(spin)

        hint_label = QLabel("每个操作之间默认等待的秒数。设为 0 表示几乎无间隔；"
                            "若某个操作单独设置了延迟，会优先使用它单独的值。")
        hint_label.setWordWrap(True)
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet(f"font-size: {int(screen_height*0.018)}px; color: #666; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(hint_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(100, 36)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover { background-color: #0A84FF; }
            QPushButton:pressed { background-color: #0A84FF; }
        """)
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
            }
            QPushButton:hover { background-color: #0A84FF; }
            QPushButton:pressed { background-color: #0A84FF; }
        """)
        button_layout.addStretch(1)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        def on_ok():
            val = round(float(spin.value()), 3)
            self.folder_intervals[folder_path] = val
            self.save_interval_config()
            dialog.accept()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()
    
    def get_folder_shortcut(self, folder_path):
        """获取流程的快捷键"""
        try:
            # 直接从self.shortcuts获取（AutoRecorderApp的shortcuts）
            if hasattr(self, 'shortcuts') and self.shortcuts:
                # 尝试多种路径格式
                normalized_path = os.path.normpath(str(folder_path))
                folder_name = os.path.basename(normalized_path).lower()

                # print(f"[快捷键查找] 查找: {folder_path}")  # [日志已禁用]
                # print(f"[快捷键查找] 规范化路径: {normalized_path}")  # [日志已禁用]
                # print(f"[快捷键查找] 文件夹名: {folder_name}")  # [日志已禁用]
                # print(f"[快捷键查找] shortcuts: {self.shortcuts}")  # [日志已禁用]

                # 首先尝试完整路径匹配（最精确）
                if normalized_path in self.shortcuts:
                    # print(f"[快捷键查找] 完整路径匹配找到: {self.shortcuts[normalized_path]}")  # [日志已禁用]
                    return self.shortcuts[normalized_path]

                # 尝试小写路径匹配
                if normalized_path.lower() in self.shortcuts:
                    # print(f"[快捷键查找] 小写路径匹配找到: {self.shortcuts[normalized_path.lower()]}")  # [日志已禁用]
                    return self.shortcuts[normalized_path.lower()]

                # 最后使用文件夹名匹配（兼容旧格式）
                for path, shortcut in self.shortcuts.items():
                    stored_folder_name = os.path.basename(path).lower()
                    # print(f"[快捷键查找] 文件夹名比较: {stored_folder_name} == {folder_name}")  # [日志已禁用]
                    if stored_folder_name == folder_name:
                        # print(f"[快捷键查找] 文件夹名匹配找到: {shortcut}")  # [日志已禁用]
                        return shortcut

                # print(f"[快捷键查找] 未找到")  # [日志已禁用]
            else:
                # print(f"[快捷键查找] 没有shortcuts属性或为空")  # [日志已禁用]
                pass
        except Exception as e:
            # print(f"获取快捷键失败: {e}")  # [日志已禁用]
            import traceback
            traceback.print_exc()
        return None
    
    def set_folder_shortcut_in_tab(self, folder_path, table_widget):
        """在Tab中设置流程快捷键"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor
        
        folder_name = os.path.basename(folder_path)
        current_shortcut = self.get_folder_shortcut(folder_path)
        
        # 临时禁用·键的全局快捷键，避免冲突
        self.temporarily_disable_grave_hotkey()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("设置快捷键")
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        
        # 按比例设置对话框大小
        width, height = get_screen_size(0.3)
        dialog.resize(width, int(height * 0.25))
        dialog.setWindowModality(Qt.WindowModal)

        # 拦截 F1 触发的系统“帮助”事件（Windows 下 F1 会被系统抢走焦点/弹帮助，
        # 导致 F1、F2 等功能键组合录不进弹窗）。拦截后 F1 能干净进入 keyPressEvent 录入。
        from PyQt5.QtCore import QObject, QEvent

        class _F1HelpBlocker(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Help:
                    event.accept()
                    return True
                return False

        _help_blocker = _F1HelpBlocker(dialog)
        dialog.installEventFilter(_help_blocker)
        dialog._help_blocker_ref = _help_blocker  # 保持引用，防止被 GC
        dialog.activateWindow()

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        screen_width, screen_height = get_screen_size()

        instruction_label = QLabel("请按下快捷键组合...")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_font_size = int(screen_height * 0.022)
        instruction_label.setStyleSheet(f"font-size: {instruction_font_size}px; color: #8c8c8c; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(instruction_label)
        
        shortcut_label = QLabel(current_shortcut if current_shortcut else "未设置")
        shortcut_label.setAlignment(Qt.AlignCenter)
        shortcut_font_size = int(screen_height * 0.03)
        shortcut_label.setStyleSheet(f"""
            font-size: {shortcut_font_size}px;
            font-weight: bold;
            padding: 12px;
            border: 2px solid #FF453A;
            border-radius: 12px;
            background-color: #FFFFFF;
            min-height: 40px;
            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            color: #FF453A;
        """)
        layout.addWidget(shortcut_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        clear_btn = QPushButton("清除")
        clear_btn.setFixedSize(100, 36)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #ff4d4f;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: #ff7875;
            }
            QPushButton:pressed {
                background: #d9363e;
            }
        """)
        
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(100, 36)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_PRIMARY};
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: {CARD};
                border-color: {ACCENT};
                color: {ACCENT};
            }}
        """)

        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # 存储当前按下的键
        current_keys = []
        
        def clear_shortcut():
            nonlocal current_keys
            current_keys = []
            shortcut_label.setText("")
        
        def keyPressEvent(event):
            # 忽略系统自动重复，避免重复录入
            if getattr(event, 'isAutoRepeat', None) and event.isAutoRepeat():
                return

            key = event.key()
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return

            def _key_name(k):
                if Qt.Key_F1 <= k <= Qt.Key_F12:
                    return "f%d" % (k - Qt.Key_F1 + 1)
                if Qt.Key_0 <= k <= Qt.Key_9:
                    return str(k - Qt.Key_0)
                if Qt.Key_A <= k <= Qt.Key_Z:
                    return chr(k).lower()
                _special = {
                    Qt.Key_Space: "space", Qt.Key_Return: "return", Qt.Key_Enter: "return",
                    Qt.Key_Tab: "tab", Qt.Key_Escape: "esc", Qt.Key_Backspace: "backspace",
                    Qt.Key_Delete: "delete", Qt.Key_Insert: "insert", Qt.Key_Home: "home",
                    Qt.Key_End: "end", Qt.Key_PageUp: "pageup", Qt.Key_PageDown: "pagedown",
                    Qt.Key_Up: "up", Qt.Key_Down: "down", Qt.Key_Left: "left", Qt.Key_Right: "right",
                }
                return _special.get(k, "")

            key_name = _key_name(key)
            if not key_name:
                return

            # 当前按住的修饰键（任意键均可自由组合，不再限定 alt/ctrl）
            mods = []
            if event.modifiers() & Qt.ControlModifier:
                mods.append("ctrl")
            if event.modifiers() & Qt.AltModifier:
                mods.append("alt")
            if event.modifiers() & Qt.ShiftModifier:
                mods.append("shift")

            token = "+".join(mods + [key_name])

            # 在上一次组合基础上累积，支持任意 2~3 个键自由组合（如 c+2、1+2）
            existing = current_keys[-1].split("+") if current_keys else []
            if token in existing:
                return
            existing.append(token)
            if len(existing) > 3:
                existing = existing[:3]
            combo = "+".join(existing)
            shortcut_label.setText(combo)
            current_keys.append(combo)
        
        dialog.keyPressEvent = keyPressEvent
        dialog.setFocusPolicy(Qt.StrongFocus)
        dialog.setFocus()
        
        def save_shortcut():
            shortcut_str = shortcut_label.text()
            if shortcut_str and shortcut_str != "未设置":
                # 检查是否已被其他流程使用
                for path, shortcut in self.shortcuts.items():
                    if shortcut == shortcut_str and path != folder_path:
                        from PyQt5.QtWidgets import QMessageBox
                        self.show_beautiful_message('warning', "警告", f"快捷键 '{shortcut_str}' 已被其他流程使用", parent=self)
                        return
                
                # 保存快捷键 - 使用规范化路径
                normalized_path = os.path.normpath(str(folder_path))
                self.shortcuts[normalized_path] = shortcut_str
                self.save_shortcut_config()
                self.update_shortcuts()
                # print(f"设置快捷键成功: {normalized_path} -> {shortcut_str}")  # [日志已禁用]
            else:
                # 清除快捷键 - 使用规范化路径匹配
                normalized_path = os.path.normpath(str(folder_path))
                # 尝试多种路径格式匹配
                keys_to_delete = []
                for key in self.shortcuts.keys():
                    if os.path.normpath(str(key)).lower() == normalized_path.lower():
                        keys_to_delete.append(key)
                for key in keys_to_delete:
                    del self.shortcuts[key]
                self.save_shortcut_config()
                self.update_shortcuts()
                # print(f"清除快捷键: {normalized_path}")  # [日志已禁用]
            
            dialog.accept()
            # 刷新表格
            self.load_folders_to_table(table_widget)
        
        clear_btn.clicked.connect(clear_shortcut)
        ok_btn.clicked.connect(save_shortcut)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
        
        # 重新启用·键的全局快捷键
        self.reenable_grave_hotkey()
    
    def rename_folder_in_tab(self, folder_path, table_widget):
        """在Tab中重命名流程"""
        from PyQt5.QtWidgets import QInputDialog
        old_name = os.path.basename(folder_path)
        new_name, ok = QInputDialog.getText(self, "重命名", "请输入新名称:", text=old_name)
        if ok and new_name and new_name != old_name:
            try:
                new_path = os.path.join(os.path.dirname(folder_path), new_name)
                os.rename(folder_path, new_path)
                # print(f"重命名成功: {old_name} -> {new_name}")  # [日志已禁用]
                
                # 更新快捷键配置（大小写不敏感匹配）
                if hasattr(self, 'shortcuts'):
                    old_path_normalized = os.path.normpath(str(folder_path)).lower()
                    new_path_normalized = os.path.normpath(str(new_path))
                    old_key = None
                    for key in list(self.shortcuts.keys()):
                        if os.path.normpath(str(key)).lower() == old_path_normalized:
                            old_key = key
                            break
                    if old_key:
                        self.shortcuts[new_path_normalized] = self.shortcuts.pop(old_key)
                        self.save_shortcut_config()
                        self.update_shortcuts()
                
                self.load_folders_to_table(table_widget)
            except Exception as e:
                self.show_beautiful_message('critical', "错误", f"重命名失败: {e}", parent=self)
    
    def delete_folder_in_tab(self, folder_path, table_widget):
        """在Tab中删除流程"""
        reply = self.show_beautiful_message('question', "确认删除", f"确定要删除流程 '{os.path.basename(folder_path)}'?", buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                from datetime import datetime as _dt
                trash_dir = os.path.join(os.path.dirname(folder_path), 'trash')
                if not os.path.exists(trash_dir):
                    os.makedirs(trash_dir)
                import shutil
                timestamp = _dt.now().strftime('_%Y%m%d_%H%M%S')
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
                self.show_beautiful_message('critical', '错误', f"删除失败: {e}")
    
    def open_trash_dialog(self):
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
            QLabel, QPushButton, QHeaderView, QWidget,
            QTableWidget, QTableWidgetItem, QAbstractItemView,
            QMessageBox, QFrame)
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("回收站")
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        dialog.resize(680, 500)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setStyleSheet("background: transparent; border: none;")

        dialog._drag_pos = None
        def _mp(ev):
            if ev.button() == Qt.LeftButton:
                dialog._drag_pos = ev.globalPos() - dialog.frameGeometry().topLeft()
                ev.accept()
        def _mm(ev):
            if ev.buttons() == Qt.LeftButton and dialog._drag_pos is not None:
                dialog.move(ev.globalPos() - dialog._drag_pos)
                ev.accept()
        def _mr(ev):
            dialog._drag_pos = None
        dialog.mousePressEvent = _mp
        dialog.mouseMoveEvent   = _mm
        dialog.mouseReleaseEvent = _mr

        container = QWidget(dialog)
        container.setObjectName("tdContainer")
        container.setStyleSheet("""
            QWidget#tdContainer {
                background: #F5F5F7;
                border: 1px solid #1C1C1E;
                border-radius: 16px;
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                color: black;
            }
        """)

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        _header = QWidget()
        _header.setFixedHeight(44)
        _header.setStyleSheet("background-color: #1C1C1E; border-top-left-radius: 13px; border-top-right-radius: 13px; border: none;")
        _hdr_lo = QHBoxLayout(_header)
        _hdr_lo.setContentsMargins(16, 0, 16, 0)
        _hdr_lo.setSpacing(8)
        _hdr_title = QLabel("回收站")
        _hdr_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: transparent; border: none;")
        _hdr_lo.addWidget(_hdr_title)
        _hdr_lo.addStretch()
        count_label = QLabel("")
        count_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        count_label.setStyleSheet("font-size: 12px; color: #86868B; background: transparent; border: none;")
        _hdr_lo.addWidget(count_label)
        _hdr_lo.addSpacing(12)
        dot_close = QFrame()
        dot_close.setFixedSize(16, 16)
        dot_close.setStyleSheet('QFrame{background-color:#FF5F57;border:none;border-radius:8px;}QFrame:hover{background-color:#FF3B30;}')
        dot_close.setCursor(Qt.PointingHandCursor)
        def _dot_close_click(ev):
            if ev.button() == Qt.LeftButton: dialog.close()
        dot_close.mousePressEvent = _dot_close_click
        _hdr_lo.addWidget(dot_close)
        def _start_drag(ev):
            if ev.button() == Qt.LeftButton:
                dialog._drag_pos = ev.globalPos() - dialog.pos()
        def _do_drag(ev):
            if getattr(dialog, '_drag_pos', None) is not None and ev.buttons() & Qt.LeftButton:
                dialog.move(ev.globalPos() - dialog._drag_pos)
        _header.mousePressEvent = _start_drag
        _header.mouseMoveEvent = _do_drag
        cl.addWidget(_header)

        content = QWidget()
        content.setStyleSheet("background-color: #FFFFFF; border: none; border-bottom-left-radius: 13px; border-bottom-right-radius: 13px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 16)
        content_layout.setSpacing(10)

        trash_table = QTableWidget()
        trash_table.setColumnCount(5)
        trash_table.setHorizontalHeaderLabels(["", "流程名称", "删除时间", "恢复", "删除"])
        trash_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        trash_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        trash_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        trash_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        trash_table.setColumnWidth(0, 80)
        trash_table.setColumnWidth(3, 80)
        trash_table.setColumnWidth(4, 80)
        trash_table.verticalHeader().setVisible(False)
        trash_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        trash_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        trash_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        trash_table.setAlternatingRowColors(False)
        trash_table.setStyleSheet("""
            QTableWidget { border: none; border-radius: 8px; gridline-color: #E8E8ED; background-color: #FFFFFF; }
            QTableWidget::item { padding: 6px 10px; }
            QTableWidget::item:selected { background-color: #0A84FF; color: white; }
            QHeaderView::section { background: #F5F5F7; color: black; font-weight: 600; padding: 8px 12px; border: none; border-bottom: 1px solid #E8E8ED; font-size: 12px; }
        """)
        content_layout.addWidget(trash_table)

        def _load_trash_data():
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            index_file = os.path.join(trash_dir, 'trash_index.json')
            index_data = []
            if os.path.exists(index_file):
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                except:
                    pass
            trash_table.setRowCount(len(index_data))
            for i, item in enumerate(index_data):
                check_item = QTableWidgetItem("")
                check_item.setData(Qt.UserRole, item)
                check_item.setTextAlignment(Qt.AlignCenter)
                trash_table.setItem(i, 0, check_item)
                name_item = QTableWidgetItem(item.get('original_name', ''))
                name_item.setTextAlignment(Qt.AlignCenter)
                name_item.setData(Qt.UserRole, item)
                trash_table.setItem(i, 1, name_item)
                time_item = QTableWidgetItem(item.get('deleted_time', ''))
                time_item.setTextAlignment(Qt.AlignCenter)
                trash_table.setItem(i, 2, time_item)

                btn_r = QPushButton("恢复")
                btn_r.setStyleSheet("QPushButton{background:#0A84FF;color:white;border:none;border-radius:4px;padding:4px 6px;font-size:11px;} QPushButton:hover{background:#006AE0;} QPushButton:pressed{background:#004DB3;}")
                btn_r.clicked.connect(lambda _, row=i: (trash_table.selectRow(row), self.restore_selected_trash(trash_table, count_label)))
                trash_table.setCellWidget(i, 3, btn_r)

                btn_d = QPushButton("删除")
                btn_d.setStyleSheet("QPushButton{background:#FF3B30;color:white;border:none;border-radius:4px;padding:4px 6px;font-size:11px;} QPushButton:hover{background:#D62820;} QPushButton:pressed{background:#B01A10;}")
                btn_d.clicked.connect(lambda _, row=i: (trash_table.selectRow(row), self.delete_selected_trash(trash_table, count_label)))
                trash_table.setCellWidget(i, 4, btn_d)
            count_label.setText(f"{len(index_data)} \u9879")
        _load_trash_data()

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 12, 0, 0)
        btn_row.setSpacing(16)

        _icon_font = "font-size: 14px;"

        restore_btn = RoundedPillButton("🔄 恢复选中", bg_color="#0A84FF")
        restore_btn.setFixedSize(130, 40)
        restore_btn.clicked.connect(lambda: self.restore_selected_trash(trash_table, count_label))
        btn_row.addWidget(restore_btn)

        delete_btn = RoundedPillButton("✖ 永久删除", bg_color="#FF3B30")
        delete_btn.setFixedSize(130, 40)
        delete_btn.clicked.connect(lambda: self.delete_selected_trash(trash_table, count_label))
        btn_row.addWidget(delete_btn)

        clear_btn = RoundedPillButton("🗑 清空回收站", bg_color="#8E8E93")
        clear_btn.setFixedSize(150, 40)
        clear_btn.clicked.connect(lambda: self.clear_trash_dialog(trash_table, count_label))
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        content_layout.addLayout(btn_row)

        cl.addWidget(content)
        dialog.show()


    def restore_selected_trash(self, trash_table, count_label):
        try:
            rows = set()
            for item in trash_table.selectedItems():
                rows.add(item.row())
            if not rows:
                self.show_beautiful_message('information', '提示', '请先选择要恢复的流程', parent=trash_table.window())
                return
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            import shutil, threading
            items = []
            for row in sorted(rows, reverse=True):
                item_data = trash_table.item(row, 0).data(Qt.UserRole)
                if not item_data:
                    continue
                trash_folder_name = item_data['trash_folder_name']
                original_path = item_data['original_path']
                original_name = item_data['original_name']
                trash_folder_path = os.path.join(trash_dir, trash_folder_name)
                if not os.path.exists(trash_folder_path):
                    continue
                restore_path = original_path
                if os.path.exists(original_path):
                    from datetime import datetime as _dt
                    timestamp = _dt.now().strftime('_%Y%m%d_%H%M%S')
                    restore_path = os.path.join(os.path.dirname(original_path), original_name + timestamp)
                items.append((trash_folder_path, restore_path, trash_folder_name))
            if not items:
                return

            class _TrashUISignal(QObject):
                reload = pyqtSignal()
                message = pyqtSignal(str, str)
            ui_signal = _TrashUISignal()
            ui_signal.reload.connect(lambda: self._reload_trash_table(trash_table, count_label))
            ui_signal.message.connect(lambda title, text: self.show_beautiful_message('information', title, text, parent=trash_table.window()))

            def _bg():
                for path, restore_path, name in items:
                    try:
                        shutil.move(path, restore_path)
                        self.remove_from_trash_index(name)
                    except Exception:
                        pass
                ui_signal.reload.emit()
                ui_signal.message.emit('恢复成功', f'成功恢复 {len(items)} 个流程')
            threading.Thread(target=_bg, daemon=True).start()
        except Exception as e:
            self.show_beautiful_message('critical', '错误', f"恢复失败: {e}", parent=trash_table.window())
    def delete_selected_trash(self, trash_table, count_label):
        try:
            rows = set()
            for item in trash_table.selectedItems():
                rows.add(item.row())
            if not rows:
                self.show_beautiful_message('information', '提示', '请先选择要永久删除的流程', parent=trash_table.window())
                return
            reply = self.show_beautiful_message('question', '确认', '确定要永久删除选中的流程吗？此操作不可撤销！', buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No, parent=trash_table.window())
            if reply != QMessageBox.Yes:
                return
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            import shutil, threading
            items = []
            for row in sorted(rows, reverse=True):
                item_data = trash_table.item(row, 0).data(Qt.UserRole)
                if not item_data:
                    continue
                items.append((item_data['trash_folder_name'], os.path.join(trash_dir, item_data['trash_folder_name'])))
            if not items:
                return

            class _TrashUISignal(QObject):
                reload = pyqtSignal()
                message = pyqtSignal(str, str)
            ui_signal = _TrashUISignal()
            ui_signal.reload.connect(lambda: self._reload_trash_table(trash_table, count_label))
            ui_signal.message.connect(lambda title, text: self.show_beautiful_message('information', title, text, parent=trash_table.window()))

            def _bg():
                for name, path in items:
                    try:
                        if os.path.exists(path):
                            shutil.rmtree(path)
                        self.remove_from_trash_index(name)
                    except Exception:
                        pass
                ui_signal.reload.emit()
                ui_signal.message.emit('删除成功', f'成功删除 {len(items)} 个流程')
            threading.Thread(target=_bg, daemon=True).start()
        except Exception as e:
            self.show_beautiful_message('critical', '错误', f"删除失败: {e}")
    def clear_trash_dialog(self, trash_table, count_label):
        try:
            reply = self.show_beautiful_message('question', '确认', '确定要清空回收站吗？此操作不可撤销！', buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No, parent=trash_table.window())
            if reply != QMessageBox.Yes:
                return
            from utils import get_recordings_path
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            import shutil, threading
            all_items = []
            if os.path.exists(trash_dir):
                all_items = [(n, os.path.join(trash_dir, n)) for n in os.listdir(trash_dir)]
            if not all_items:
                return

            class _ReloadSignal(QObject):
                reload = pyqtSignal()
            reload_signal = _ReloadSignal()
            reload_signal.reload.connect(lambda: self._reload_trash_table(trash_table, count_label))

            def _bg():
                for name, p in all_items:
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p)
                        else:
                            os.remove(p)
                    except Exception:
                        pass
                import json
                idx_f = os.path.join(trash_dir, 'trash_index.json')
                try:
                    if os.path.exists(idx_f):
                        os.remove(idx_f)
                except:
                    pass
                reload_signal.reload.emit()
            threading.Thread(target=_bg, daemon=True).start()
        except Exception as e:
            self.show_beautiful_message('critical', '错误', f"清空失败: {e}", parent=trash_table.window())
    def _reload_trash_table(self, trash_table, count_label):
        from utils import get_recordings_path
        recordings_dir = get_recordings_path()
        trash_dir = os.path.join(recordings_dir, 'trash')
        index_file = os.path.join(trash_dir, 'trash_index.json')
        index_data = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except:
                pass
        trash_table.setRowCount(len(index_data))
        for i, item in enumerate(index_data):
            check_item = QTableWidgetItem("")
            check_item.setData(Qt.UserRole, item)
            check_item.setTextAlignment(Qt.AlignCenter)
            trash_table.setItem(i, 0, check_item)
            name_item = QTableWidgetItem(item.get('original_name', ''))
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setData(Qt.UserRole, item)
            trash_table.setItem(i, 1, name_item)
            time_item = QTableWidgetItem(item.get('deleted_time', ''))
            time_item.setTextAlignment(Qt.AlignCenter)
            trash_table.setItem(i, 2, time_item)

            btn_r = QPushButton("恢复")
            btn_r.setStyleSheet("QPushButton{background:#0A84FF;color:white;border:none;border-radius:4px;padding:4px 6px;font-size:11px;} QPushButton:hover{background:#006AE0;} QPushButton:pressed{background:#004DB3;}")
            btn_r.clicked.connect(lambda _, row=i: (trash_table.selectRow(row), self.restore_selected_trash(trash_table, count_label)))
            trash_table.setCellWidget(i, 3, btn_r)

            btn_d = QPushButton("删除")
            btn_d.setStyleSheet("QPushButton{background:#FF3B30;color:white;border:none;border-radius:4px;padding:4px 6px;font-size:11px;} QPushButton:hover{background:#D62820;} QPushButton:pressed{background:#B01A10;}")
            btn_d.clicked.connect(lambda _, row=i: (trash_table.selectRow(row), self.delete_selected_trash(trash_table, count_label)))
            trash_table.setCellWidget(i, 4, btn_d)
        count_label.setText(f"{len(index_data)} \u9879")
        # 同步刷新主流程列表
        if hasattr(self, 'manager_tab') and hasattr(self.manager_tab, 'folder_table'):
            self.load_folders_to_table(self.manager_tab.folder_table)

    def refresh_floating_window_list(self):
        """刷新悬浮窗口的流程列表"""
        if hasattr(self, 'list_layout') and hasattr(self, 'list_container'):
            # 清除旧的内容
            self.clear_layout(self.list_layout)
            
            # 重新加载流程列表
            self.load_replay_list(self.list_layout)
            
            # 更新显示
            self.list_container.update()
            
            # 强制垃圾回收
            import gc
            gc.collect()

    def show_recording_manager(self):
        """显示录制管理窗口 - 切换到对应Tab"""
        if hasattr(self, 'tab_widget'):
            # 切换到流程管理Tab（索引1）
            self.tab_widget.setCurrentIndex(1)
            # 设置标志为True，表示管理录制操作界面已打开
            self.is_folder_manager_open = True
            # 延迟注册快捷键，避免阻塞UI
            QTimer.singleShot(100, self.update_shortcuts)
        else:
            # 兼容旧版本，弹窗显示
            self.is_folder_manager_open = True
            QTimer.singleShot(100, self.update_shortcuts)
            self.folder_manager = FolderManager(self)
            self.folder_manager.show()



    def register_record_hotkey(self):
        """注册·键作为开始录制的快捷键"""
        try:
            def hotkey_handler():
                try:
                    # ★ 检查临时禁用标志
                    if getattr(self, '_hotkeys_temporarily_disabled', False):
                        return
                    # print("[DEBUG] ·键被按下，准备在主线程中执行toggle_recording")  # [日志已禁用]
                    QTimer.singleShot(0, self.toggle_recording)
                except Exception as _eh:
                    log_error(f'[热键] ·键回调异常: {_eh}')

            # 保存·键的hotkey_id，以便可以临时禁用和重新启用
            self.grave_hotkey_id = keyboard.add_hotkey('grave', hotkey_handler)
            log_info(f'[热键] 已注册 · 键录制热键，id={self.grave_hotkey_id}')
        except Exception as e:
            log_error(f"[热键] 注册·键快捷键失败: {e}")
            self.grave_hotkey_id = None
    
    def register_stop_replay_hotkey(self):
        """注册F12键作为停止回放的快捷键"""
        try:
            def stop_handler():
                try:
                    self.debug_print("[DEBUG] F12键被按下，准备停止当前回放")
                    # 只有在回放进行中时才执行停止
                    if getattr(self, 'is_replaying', False):
                        QTimer.singleShot(0, self.stop_replay)
                        self.debug_print("[回放控制] F12停止快捷键已触发")
                    else:
                        self.debug_print("[回放控制] F12被按下，但没有正在进行的回放")
                except Exception as _eh:
                    log_error(f'[热键] F12回调异常: {_eh}')

            # 保存F12键的hotkey_id
            self.stop_replay_hotkey_id = keyboard.add_hotkey('f12', stop_handler)
            log_info(f'[热键] 已注册 F12 停止回放热键，id={self.stop_replay_hotkey_id}')
        except Exception as e:
            log_error(f"[热键] 注册F12停止快捷键失败: {e}")
            self.stop_replay_hotkey_id = None

    def _start_hotkey_health_check(self):
        """启动全局热键健康检查定时器，自动恢复失效的热键"""
        self._hotkey_health_timer = QTimer(self)
        self._hotkey_health_timer.timeout.connect(self._check_and_restore_hotkeys)
        self._hotkey_health_timer.start(1000)  # 每1秒检查一次，更快响应
        log_info('[热键健康] 已启动热键健康检查定时器(1秒间隔)')

        # 健康检查日志定时器（每30秒打印一次状态，避免刷屏）
        self._health_log_timer = QTimer(self)
        self._health_log_timer.timeout.connect(self._log_hotkey_status)
        self._health_log_timer.start(30000)

        # ★ 添加全局按键监听器，用于诊断 keyboard 库是否捕获到按键
        try:
            import keyboard as _kb
            def _key_logger(event):
                if event.event_type == 'down':
                    # 只记录 Alt 和 Ctrl 等修饰键，以及字母数字键
                    if event.name in ['alt', 'ctrl', 'shift', 'left alt', 'right alt'] or len(event.name) == 1:
                        self.debug_print(f"[键盘事件] 捕获按键: {event.name}")
            _kb.hook(_key_logger)
            self.debug_print("[热键健康] 已注册全局按键监听器")
        except Exception as _e:
            self.debug_print(f"[热键健康] 注册按键监听器失败: {_e}")

    def _check_and_restore_hotkeys(self):
        """检查全局热键是否仍然有效，失效时自动重新注册"""
        try:
            import keyboard as _kb
        except Exception as _e:
            log_error(f'[热键健康] 无法导入 keyboard 模块: {_e}')
            return

        try:
            # 检查 keyboard 后台线程是否存活
            # ★ 关键：需要检查 BOTH listening_thread 和 processing_thread
            listener_alive = False
            processing_alive = False
            try:
                listener = getattr(_kb, '_listener', None)
                if listener is not None:
                    if listener.listening:
                        # 检查接收OS事件的线程
                        if hasattr(listener, 'listening_thread') and listener.listening_thread:
                            listener_alive = listener.listening_thread.is_alive()
                        else:
                            listener_alive = False
                        # 检查处理热键回调的线程（processing_thread 死亡会导致事件入队却无人处理）
                        if hasattr(listener, 'processing_thread') and listener.processing_thread:
                            processing_alive = listener.processing_thread.is_alive()
                        else:
                            processing_alive = False
            except Exception:
                listener_alive = False
                processing_alive = False

            grave_disabled = getattr(self, '_grave_hotkey_temporarily_disabled', False)
            has_grave = getattr(self, 'grave_hotkey_id', None) is not None
            has_f12 = getattr(self, 'stop_replay_hotkey_id', None) is not None
            shortcut_objects = getattr(self, 'shortcut_objects', [])
            shortcuts_config = getattr(self, 'shortcuts', {})
            expected_folder_shortcuts = len(shortcuts_config)
            actual_folder_shortcuts = len(shortcut_objects)

            need_restore = False
            # 0. ★ 事件队列积压检测：processing_thread 卡死（不消费事件）时 is_alive() 仍为 True，
            #     但 OS 线程仍在往队列里塞事件，队列会持续积压——这是"线程活着却不处理事件"的铁证，
            #     仅靠线程存活检测查不出来。积压 >8 条判定处理线程卡死（正常使用中队列几乎恒为空/≤2）。
            queue_stalled = False
            try:
                if listener is not None:
                    _q = getattr(listener, 'queue', None)
                    if _q is not None and hasattr(_q, 'qsize'):
                        _qs = _q.qsize()
                        if _qs > 8:
                            self.debug_print(f'[热键健康] ❌ 事件队列积压 {_qs} 条（处理线程疑似卡死），准备恢复')
                            queue_stalled = True
            except Exception:
                queue_stalled = False
            # 1. 检查 listening_thread 是否存活
            if queue_stalled:
                need_restore = True
            elif not listener_alive:
                self.debug_print('[热键健康] ❌ listening_thread 未存活，准备恢复')
                need_restore = True
            # 1b. 检查 processing_thread 是否存活
            elif not processing_alive:
                self.debug_print('[热键健康] ❌ processing_thread 未存活（事件入队但无人处理），准备恢复')
                need_restore = True
            # 2. 检查grave热键是否注册
            elif not grave_disabled and not has_grave:
                self.debug_print('[热键健康] ❌ ·键录制热键未注册，准备恢复')
                need_restore = True
            # 3. 检查F12热键是否注册
            elif not has_f12:
                self.debug_print('[热键健康] ❌ F12停止热键未注册，准备恢复')
                need_restore = True
            # 4. 检查文件夹快捷键是否注册
            elif expected_folder_shortcuts > 0 and actual_folder_shortcuts == 0:
                self.debug_print(f'[热键健康] ❌ 配置了{expected_folder_shortcuts}个快捷键但均未注册，准备恢复')
                need_restore = True

            # 5. 检查回放锁是否超时
            lock_time = getattr(self, '_replay_lock_time', None)
            if lock_time is not None:
                elapsed = time.time() - lock_time
                if elapsed > 300:
                    self.debug_print(f'[热键健康] 回放锁已锁定{elapsed:.0f}秒，强制释放')
                    try:
                        self._replay_lock.release()
                        self._replay_lock_time = None
                    except Exception as _re_err:
                        log_error(f'[热键健康] 强制释放回放锁失败: {_re_err}')

            # 6. ★ 不再主动强制刷新 — 强行重启反而会破坏正常工作的热键
            #     旧代码每5分钟调用 unhook_all() 会杀死监听线程，
            #     且旧线程的 finally 块会卸载新线程刚安装的钩子，导致热键永久失效
            #     改为：只在实际检测到热键失效时才恢复

            if need_restore:
                import threading as _th
                _th.Thread(target=self._reinitialize_all_hotkeys, daemon=True).start()
        except Exception as _e:
            log_error(f'[热键健康] 检查失败: {_e}')

    def _log_hotkey_status(self):
        """记录热键状态日志"""
        try:
            import keyboard as _kb
            listener = getattr(_kb, '_listener', None)
            alive = False
            proc_alive = False
            if listener:
                if hasattr(listener, 'listening_thread') and listener.listening_thread:
                    alive = listener.listening_thread.is_alive()
                else:
                    alive = listener.listening
                if hasattr(listener, 'processing_thread') and listener.processing_thread:
                    proc_alive = listener.processing_thread.is_alive()
            has_grave = getattr(self, 'grave_hotkey_id', None) is not None
            has_f12 = getattr(self, 'stop_replay_hotkey_id', None) is not None
            log_info(f'[热键状态] listener={alive} | processor={proc_alive} | grave={"✓" if has_grave else "✗"} | f12={"✓" if has_f12 else "✗"} | shortcuts={len(getattr(self, "shortcut_objects", []))}')
        except Exception:
            pass

    def _reinitialize_all_hotkeys(self):
        """清理并重新注册所有全局热键（带超时看门狗，防止卡死）"""
        # ★ 超时检测：如果上次重初始化超过10秒未完成，视为卡死，强制重试
        if self._reinitializing:
            if time.time() - self._reinitializing_start > 10:
                log_warning('[热键健康] 上次重初始化超过10秒未完成，疑似卡死，强制重试')
            else:
                log_info('[热键健康] 重初始化已在执行中，跳过本次请求')
                self.debug_print('[热键恢复] 跳过：重初始化已在执行中')
                return
        self._reinitializing = True
        self._reinitializing_start = time.time()
        # ★ 清除热键临时禁用标志，确保恢复后可以正常工作
        self._hotkeys_temporarily_disabled = False
        self.debug_print('[热键恢复] 开始重新初始化所有全局热键')

        # ★ 简化：不再手动操作 handlers，让 keyboard 库自己管理
        # 检查 handlers 状态用于诊断
        try:
            import keyboard as _kb_pre
            self.debug_print(f"[热键恢复] 正在获取 process_event, _listener存在: {hasattr(_kb_pre, '_listener')}")
            if hasattr(_kb_pre, '_listener') and _kb_pre._listener:
                self.debug_print(f"[热键恢复] _listener 类型: {type(_kb_pre._listener)}")
                self.debug_print(f"[热键恢复] _listener 有 process_event: {hasattr(_kb_pre._listener, 'process_event')}")
                
                # 检查 handlers 中有什么
                _handlers = _kb_pre._listener.handlers
                self.debug_print(f"[热键恢复] handlers 数量: {len(_handlers)}")
                for i, _h in enumerate(_handlers):
                    self.debug_print(f"[热键恢复] handler[{i}]: {type(_h).__name__}, str: {str(_h)[:60]}")
        except Exception as _e:
            self.debug_print(f"[热键恢复] 检查状态失败: {_e}")

        # ★ 启动看门狗线程：15秒后如果重初始化仍未完成，自动重置标志位
        _watchdog_start = time.time()
        _watchdog_triggered = [False]
        def _watchdog():
            while time.time() - _watchdog_start < 15:
                time.sleep(1)
                if not self._reinitializing:
                    return
            if self._reinitializing:
                _watchdog_triggered[0] = True
                log_warning('[热键健康] ★ 重初始化看门狗超时(15s)，强制重置 _reinitializing 标志')
                self.debug_print('[热键恢复] ★ 看门狗超时(15s)，强制重置标志')
                self._reinitializing = False
        _wd = threading.Thread(target=_watchdog, daemon=True)
        _wd.start()

        try:
            self.debug_print('[热键恢复] 清理旧钩子...')
            self._cleanup_all_hotkeys()

            # ★ 不再手动恢复 process_event，让 keyboard 库自己管理

            # ★ 关键修复：检查 keyboard 监听线程是否还活着
            # keyboard 的监听线程可能因异常崩溃，但 listening 标志位仍是 True
            # 导致 add_hotkey → start_if_necessary 跳过启动新线程，热键永久失效
            # ★ 新增：同时检查 processing_thread，如果死亡则事件入队但无人处理，热键也不响应
            try:
                import keyboard as _kb_check
                if hasattr(_kb_check, '_listener') and _kb_check._listener:
                    _kb_listener = _kb_check._listener
                    _need_reset = False
                    # 检查 listening_thread
                    if hasattr(_kb_listener, 'listening_thread') and _kb_listener.listening_thread:
                        if not _kb_listener.listening_thread.is_alive() and _kb_listener.listening:
                            self.debug_print('[热键恢复] ⚠️ listening_thread 已死但 listening=True，强制重置')
                            _need_reset = True
                    # 检查 processing_thread（事件处理线程，死亡会导致热键无响应）
                    if hasattr(_kb_listener, 'processing_thread') and _kb_listener.processing_thread:
                        if not _kb_listener.processing_thread.is_alive() and _kb_listener.listening:
                            self.debug_print('[热键恢复] ⚠️ processing_thread 已死但 listening=True，强制重置')
                            _need_reset = True
                    if _need_reset:
                        _kb_listener.listening = False
            except Exception as _le:
                self.debug_print(f'[热键恢复] 检查监听线程状态失败: {_le}')

            self.debug_print('[热键恢复] 注册文件夹快捷键...')
            self.update_shortcuts()
            self.debug_print('[热键恢复] 注册·键录制热键...')
            self.register_record_hotkey()
            self.debug_print('[热键恢复] 注册F12停止热键...')
            self.register_stop_replay_hotkey()
            self.debug_print('[热键恢复] ★ 所有全局热键重新初始化完成')

            # ★ 诊断：检查注册后热键容器状态
            # keyboard 库使用 _hotkeys 字典存储热键（模块级别），不是 _listener.nonblocking_hotkeys
            try:
                import keyboard as _kb_diag
                # ★ 热键存储在模块级别的 _hotkeys 字典中
                _hotkeys = getattr(_kb_diag, '_hotkeys', {})
                _hotkeys_count = len(_hotkeys)
                _handlers = getattr(_kb_diag._listener, 'handlers', []) if hasattr(_kb_diag, '_listener') and _kb_diag._listener else []
                _h_count = len(_handlers)
                _listener_alive = False
                _processor_alive = False
                if hasattr(_kb_diag, '_listener') and _kb_diag._listener:
                    if hasattr(_kb_diag._listener, 'listening_thread') and _kb_diag._listener.listening_thread:
                        _listener_alive = _kb_diag._listener.listening_thread.is_alive()
                    if hasattr(_kb_diag._listener, 'processing_thread') and _kb_diag._listener.processing_thread:
                        _processor_alive = _kb_diag._listener.processing_thread.is_alive()
                    _listening = _kb_diag._listener.listening
                else:
                    _listening = False
                self.debug_print(f'[热键诊断] _hotkeys={_hotkeys_count}个 | handlers={_h_count}个 | listen线程={_listener_alive} | process线程={_processor_alive} | listening={_listening}')
            except Exception as _diag_e:
                self.debug_print(f'[热键诊断] 失败: {_diag_e}')
        except Exception as _e:
            self.debug_print(f'[热键恢复] ❌ 重新初始化失败: {_e}')
        finally:
            if not _watchdog_triggered[0]:
                self._reinitializing = False
                self.debug_print('[热键恢复] 标志位已重置')

    def _cleanup_all_hotkeys(self):
        """清理所有已注册的全局热键（不卸载 Windows 钩子，只移除处理器）"""
        try:
            import keyboard as _kb
        except Exception:
            self.debug_print('[热键清理] 无法导入keyboard模块')
            return

        # ★ 关键修复：不再调用 unhook_all()，它会导致：
        #   1. 杀死 keyboard 监听线程
        #   2. 旧线程 finally 块会卸载新线程刚安装的钩子
        #   3. 热键永久失效
        # 正确做法：只移除处理器，保留监听线程和钩子继续运行

        # ★ 检查两个线程是否存活，如果已死则重置 listening 标志
        # 避免 add_hotkey → start_if_necessary 因 listening=True 而跳过启动新线程
        try:
            if hasattr(_kb, '_listener') and _kb._listener:
                _need_reset = False
                if hasattr(_kb._listener, 'listening_thread') and _kb._listener.listening_thread:
                    if not _kb._listener.listening_thread.is_alive() and _kb._listener.listening:
                        self.debug_print('[热键清理] ⚠️ listening_thread 已死，重置 listening=False 以便重新启动')
                        _need_reset = True
                if hasattr(_kb._listener, 'processing_thread') and _kb._listener.processing_thread:
                    if not _kb._listener.processing_thread.is_alive() and _kb._listener.listening:
                        self.debug_print('[热键清理] ⚠️ processing_thread 已死，重置 listening=False 以便重新启动')
                        _need_reset = True
                if _need_reset:
                    _kb._listener.listening = False
        except Exception as _le:
            self.debug_print(f'[热键清理] 检查监听线程状态失败: {_le}')

        # 手动清理已注册的快捷键
        shortcut_count = len(getattr(self, 'shortcut_objects', []))
        for hotkey_id in getattr(self, 'shortcut_objects', []):
            try:
                _kb.remove_hotkey(hotkey_id)
            except Exception:
                pass
        self.shortcut_objects = []
        self.debug_print(f'[热键清理] 已清理 {shortcut_count} 个文件夹快捷键')

        if getattr(self, 'grave_hotkey_id', None):
            try:
                _kb.remove_hotkey(self.grave_hotkey_id)
            except Exception:
                pass
            self.grave_hotkey_id = None
            self.debug_print('[热键清理] 已清理·键录制热键')

        if getattr(self, 'stop_replay_hotkey_id', None):
            try:
                _kb.remove_hotkey(self.stop_replay_hotkey_id)
            except Exception:
                pass
            self.stop_replay_hotkey_id = None
            self.debug_print('[热键清理] 已清理F12停止热键')

        # ★ 注意：不清空 _listener.handlers！
        # handlers 是 keyboard 库自己的原始事件处理器列表，清空会导致事件处理链断裂
        # 热键处理器存储在 blocking_hotkeys 和 nonblocking_hotkeys 中，
        # 已通过上面的 remove_hotkey() 调用正确清理，无需额外操作
        # 保留监听线程继续运行，避免旧线程的 finally 卸载新钩子
        self.debug_print('[热键清理] 已清理所有热键处理器（保留监听线程）')

    def temporarily_disable_grave_hotkey(self):
        """临时禁用·键的全局快捷键"""
        self._grave_hotkey_temporarily_disabled = True
        if hasattr(self, 'grave_hotkey_id') and self.grave_hotkey_id is not None:
            try:
                keyboard.remove_hotkey(self.grave_hotkey_id)
                self.grave_hotkey_id = None
                log_info('[热键] 临时禁用 · 键全局快捷键')
            except Exception as e:
                log_error(f"[热键] 禁用·键快捷键失败: {e}")
                self.grave_hotkey_id = None
                pass

    def reenable_grave_hotkey(self):
        """重新启用·键的全局快捷键"""
        self._grave_hotkey_temporarily_disabled = False
        try:
            def hotkey_handler():
                try:
                    if getattr(self, '_hotkeys_temporarily_disabled', False):
                        return
                    if getattr(self, '_grave_hotkey_temporarily_disabled', False):
                        return
                    QTimer.singleShot(0, self.toggle_recording)
                except Exception as _eh:
                    log_error(f'[热键] ·键回调异常(reenable): {_eh}')

            self.grave_hotkey_id = keyboard.add_hotkey('grave', hotkey_handler)
            log_info(f'[热键] 重新启用 · 键全局快捷键，id={self.grave_hotkey_id}')
        except Exception as e:
            log_error(f"[热键] 重新启用·键快捷键失败: {e}")
            self.grave_hotkey_id = None
    
    def logout(self):
        self.hide()
        if hasattr(self, 'replay_status_widget'):
            self.replay_status_widget.hide()
        from login_ui import LoginDialog
        login_dialog = LoginDialog(self.login_manager)
        if login_dialog.exec_() == login_dialog.Accepted:
            self.username = login_dialog.current_user
            self.current_user = login_dialog.current_user
            self.load_shortcut_config()
            self.initUI()
            self.load_font_size_setting()
            self.update_shortcuts()
            self.show()
        else:
            QApplication.quit()

    def _extract_step_number(self, filename):
        """提取文件名中的步骤编号"""
        match = re.search(r'操作(\d+)(?:_region_\d+_\d+_\d+_\d+|_\d+_[0-9a-f]+)?.png', filename)
        if match:
            return int(match.group(1))
        return None

    def get_image_files(self, folder_path):
        """获取文件夹中的图片文件"""
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.png')]

    def get_step_action_map(self, folder_path):
        """获取步骤操作类型映射"""
        json_path = os.path.join(folder_path, 'recording.json')
        if os.path.exists(json_path):
            data = load_json_data(json_path, [])
            if not isinstance(data, list):
                return {}
            return {d.get('step', 0): d.get('action_type', 'left_click') for d in data}
        return {}

    def handle_error(self, error_msg, parent=None):
        """共用错误处理函数"""
        self.show_beautiful_message('critical', '错误', error_msg, parent=parent)

    def save_shortcut_config(self):
        """保存快捷键配置"""
        if not self.current_user:
            return

        config_path = os.path.join(self.user_data_dir, f'shortcuts_{self.current_user}.json')
        try:
            shortcuts_lower = {path: shortcut.lower() for path, shortcut in self.shortcuts.items()}
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(shortcuts_lower, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def load_shortcut_config(self):
        """加载快捷键配置"""
        try:
            config_path = os.path.join(self.user_data_dir, f'shortcuts_{self.current_user}.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.shortcuts = json.load(f)
                    # ★ 将快捷键字符串统一转换为小写，确保与keyboard库匹配
                    self.shortcuts = {path: shortcut.lower() for path, shortcut in self.shortcuts.items()}
            else:
                self.shortcuts = {}
        except Exception:
            self.shortcuts = {}

    def save_interval_config(self):
        """保存文件夹默认操作间隔配置"""
        if not self.current_user:
            return
        config_path = os.path.join(self.user_data_dir, f'intervals_{self.current_user}.json')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.folder_intervals, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def load_interval_config(self):
        """加载文件夹默认操作间隔配置"""
        try:
            if not hasattr(self, 'folder_intervals'):
                self.folder_intervals = {}
            config_path = os.path.join(self.user_data_dir, f'intervals_{self.current_user}.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.folder_intervals = json.load(f)
                # 转为 float，容错非法值
                self.folder_intervals = {k: float(v) for k, v in self.folder_intervals.items()}
            else:
                self.folder_intervals = {}
        except Exception:
            self.folder_intervals = {}

    def update_shortcuts(self):
        """更新快捷键 - 移除旧的并添加新的"""
        try:
            # 先清理旧的快捷键
            for hotkey_id in getattr(self, 'shortcut_objects', []):
                try:
                    keyboard.remove_hotkey(hotkey_id)
                except Exception:
                    pass
            self.shortcut_objects = []

            # 按快捷键分组，一个快捷键可以绑定多个流程
            shortcut_groups = {}
            for folder_path, shortcut_str in self.shortcuts.items():
                if shortcut_str not in shortcut_groups:
                    shortcut_groups[shortcut_str] = []
                shortcut_groups[shortcut_str].append(folder_path)

            log_info(f'[热键] 开始更新文件夹快捷键，共 {len(shortcut_groups)} 组')

            # 添加新的快捷键（每个快捷键的回放在独立线程中执行，避免阻塞键盘钩子）
            for shortcut_str, folder_paths in shortcut_groups.items():
                try:
                    def make_handler(paths=folder_paths.copy(), _sc=shortcut_str):
                        # ★ 防抖：记录每个快捷键的上次触发时间，同一快捷键 500ms 内只执行一次
                        _last_trigger_time = 0
                        def handler():
                            nonlocal _last_trigger_time
                            try:
                                # ★ 新策略：使用标志位禁用热键，不清空字典
                                # 这样可以保留 keyboard 库的完整状态，避免事件链断裂
                                if getattr(self, '_hotkeys_temporarily_disabled', False):
                                    # ★ 兜底修复：若回放已结束但禁用标志仍残留（回放线程异常/状态未清干净），
                                    # 自动清除并继续执行，避免"回放后快捷键永久失效、怎么按都没反应"。
                                    if not self._replay_lock.locked():
                                        self._hotkeys_temporarily_disabled = False
                                        self.debug_print(f"[热键] {_sc} 触发时发现禁用标志残留（回放已结束），已自动清除并继续")
                                    else:
                                        # 回放真正在进行中，临时禁用生效，不执行
                                        self.debug_print(f"[热键] {_sc} 触发但热键已临时禁用（回放进行中）")
                                        return
                                # ★ 诊断：即使不执行也要记录热键触发，便于排查问题
                                if not self.replay_enabled:
                                    self.debug_print(f"[热键] 快捷键 {_sc} 触发但回放已关闭 (replay_enabled=False)")
                                    return
                                # ★ 热键触发时打印 keyboard 库状态
                                try:
                                    import keyboard as _kb_trig
                                    _hk = getattr(_kb_trig, '_hotkeys', {})
                                    _l = getattr(_kb_trig, '_listener', None)
                                    if _l:
                                        self.debug_print(f"[热键诊断-触发时] _hotkeys={len(_hk)} | handlers={len(getattr(_l, 'handlers', []))} | listen线程={getattr(_l, 'listening_thread', None) and getattr(_l, 'listening_thread', None).is_alive()}")
                                except Exception:
                                    pass
                                # ★ 防抖：如果 500ms 内已触发过，忽略本次
                                _now = time.time()
                                if _now - _last_trigger_time < 0.5:
                                    return
                                _last_trigger_time = _now
                                # ★ 诊断日志：记录热键被触发
                                self.debug_print(f"[热键] 快捷键 {_sc} 被触发，共 {len(paths)} 个流程")
                                import threading as _th
                                for path in paths:
                                    if not self.replay_enabled:
                                        break
                                    # ★ 跳过已删除/无效的流程文件夹
                                    recording_json = os.path.join(path, 'recording.json')
                                    if not os.path.exists(recording_json):
                                        self.debug_print(f"[热键] 跳过无效流程: {os.path.basename(path)}（无recording.json）")
                                        continue
                                    _t = _th.Thread(target=self._safe_replay_folder, args=(path,), daemon=True)
                                    _t.start()
                            except Exception as e:
                                try:
                                    log_error(f"[热键] 处理快捷键回放时出错: {e}")
                                except Exception:
                                    pass
                        return handler

                    shortcut_str_lower = shortcut_str.lower()
                    hotkey_id = keyboard.add_hotkey(shortcut_str_lower, make_handler())
                    self.shortcut_objects.append(hotkey_id)
                    log_info(f'[热键] 已注册文件夹快捷键 {shortcut_str} -> {folder_paths}（注册为{shortcut_str_lower}），id={hotkey_id}')
                except Exception as e:
                    log_error(f"[热键] 注册快捷键失败 {shortcut_str}: {e}")
                    pass
        except Exception as e:
            log_error(f"[热键] 更新快捷键失败: {e}")
            pass

    def _safe_replay_folder(self, folder_path):
        """在线程中安全执行回放，防止异常导致线程崩溃"""
        # ★ 提前检查文件夹和recording.json是否存在，避免不必要地获取锁
        recording_json_path = os.path.join(folder_path, 'recording.json')
        if not os.path.exists(recording_json_path):
            self.debug_print(f"[回放] 找不到recording.json文件: {recording_json_path}")
            return
        try:
            self.replay_folder_operations(folder_path)
        except Exception as e:
            try:
                self.debug_print(f"[回放] 线程中回放异常: {e}")
                import traceback
                traceback.print_exc()
            except Exception:
                pass
        finally:
            self.is_replaying = False


class ComboSkillRunner:
    """组合技执行器 - 在独立线程中运行组合技的各个流程（纯Python回调）"""

    def __init__(self, skill_data, parent=None):
        # 必须深拷贝！否则运行时引用原始字典对象，任何修改都会污染保存的数据
        self.skill_data = copy.deepcopy(skill_data) if skill_data else {}
        self.skill_id = ""
        self.running = False
        self.monitor_mode = False
        self.monitor_target_runner = None
        self._exec_thread = None
        self._current_flow_index = 0
        self._total_flows = len(self.skill_data.get("flows", []))
        self._loop_count = self.skill_data.get("loop_count", 1)
        self._current_loop = 1
        self._main_app = parent
        self.interrupt_event = threading.Event()  # 用于唤醒 _wait_interruptible 的中断事件
        # 回调函数（线程安全，由主线程设置）
        self._on_finished = None
        self._on_log = None
        self._on_step = None
        # 耗时统计：面板内可见的计时器数据
        self._combo_step_times = []   # (step, action, ms, flow_index)
        self._combo_flow_times = []   # (flow_index, action, exec_elapsed)

    def isRunning(self):
        return self.running

    def reset(self):
        """重置执行状态，下次从第一个流程开始"""
        self._current_flow_index = 0
        self._current_loop = 1

    def run(self):
        """执行组合技的所有流程（支持条件、else分支、跳转）"""
        import time as _time
        self.running = True
        self._consecutive_failures = 0
        _run_start = _time.time()
        try:
            if self._main_app is not None:
                self._main_app.append_log(f"╔═ {'='*45}")
                self._main_app.append_log(f" ║  🚀 组合技开始: {self.skill_data.get('name', '')}")
                self._main_app.append_log(f" ║  📊 流程数: {len(self.skill_data.get('flows', []))}, 循环次数: {self._loop_count}")
        except Exception:
            pass
        try:
            flows = self.skill_data.get("flows", [])
            self.skip_on_fail = self.skill_data.get("skip_on_fail", False)
            total_loops = max(1, self._loop_count)

            # ── 有效强制间隔（流程/跳转之间的默认等待，用户设0就真的0）──
            # ★★★ 速度优化：默认 0.1s → 0.02s（20ms），对UI刷新完全足够，原来的100ms太保守
            # 规则：用户 step_interval=0 时，_flow_gap=0（真·极速，不做任何强制等待）
            #       否则 _flow_gap = step_interval（未配置时默认 0.02 秒）
            _raw_si = self.skill_data.get('step_interval', None)
            try:
                if _raw_si is None:
                    _flow_gap = 0.02  # ★ 默认从 0.1s → 0.02s，流程间提速 5 倍
                else:
                    _f = float(_raw_si)
                    if abs(_f - 0.0) < 0.0001:
                        _flow_gap = 0.0  # 用户明确设0 → 真0，不强制
                    else:
                        _flow_gap = max(0.0, _f)
            except (TypeError, ValueError):
                _flow_gap = 0.02  # ★ 同上
            self._flow_gap = _flow_gap
            # 「极速模式」开关：用户明确设为0秒(极速)时启用
            #   启用后：条件判断 / 录制回放的图片匹配 → 只做一次快速闪匹配（不做轮询重试）
            self._turbo_mode = (abs(self._flow_gap - 0.0) < 0.0001)
            # 「速度比例因子」：根据 step_interval 自动缩放图片匹配超时
            # ★ 基准0.02s(新默认值)：0.02s→1.0(标准)，0.01→0.5，0→极速
            # 注意：旧的 min(1.0) 上界去掉了，设0.1s的老用户获得更长匹配超时(更稳)
            if self._turbo_mode:
                self._speed_scale = 0.0
            else:
                self._speed_scale = max(0.0, _flow_gap / 0.02)

            _t0 = _time.time()
            from image_recognition import find_image_with_timeout
            _t1 = _time.time()
            try:
                if self._main_app is not None:
                    self._main_app.append_log(f" ║  ⏳ find_image_with_timeout 导入: {_t1-_t0:.3f}s")
                    self._main_app.append_log(f" ║  ⚙️  步间间隔(录制内): {self._flow_gap:.3f}s | 流程间强制等待: {'关闭(极速)' if _flow_gap <= 0 else str(round(_flow_gap,3))+'s'} | 速度比例: {'极速' if self._turbo_mode else f'{self._speed_scale:.2f}x'} | 图片匹配: {'⚡闪匹配(极速)' if self._turbo_mode else '智能缩放' if self._speed_scale < 0.8 else '标准(带重试)'}")
                    if flows:
                        self._main_app.append_log(f" ║  📋 流程0数据: {str(flows[0])[:200]}")
            except Exception:
                pass

            for loop in range(1, total_loops + 1):
                if not self.running:
                    break
                self._current_loop = loop
                # 每轮循环开始重置连续失败计数（不同轮次的失败不应跨轮累加）
                self._consecutive_failures = 0
                _loop_start = _time.time()

                flow_index = 0
                total_jumps = 0
                max_jumps = 999999999
                while flow_index < len(flows):
                    if not self.running:
                        break
                    _flow_start = _time.time()
                    self._current_flow_index = flow_index
                    flow = flows[flow_index]
                    action = flow.get("action", "")
                    condition = flow.get("condition", "always")
                    else_branch = flow.get("else_branch") or {}

                    # ====== 0. 流程进度日志 ======
                    _total_flows = len(flows)
                    _cond_label = {"always": "总是执行", "image_found": "找到图片", "image_not_found": "找不到图片", "wait_for_image": "等待图片"}.get(condition, condition)
                    try:
                        if self._main_app is not None:
                            _cond_emoji = {"always": "▶", "image_found": "🔍", "image_not_found": "👻", "wait_for_image": "⏳"}.get(condition, "▶")
                            self._main_app.append_log(f"╔═ {_cond_emoji} 流程{flow_index+1}/{_total_flows} [第{loop}轮] ═══")
                            self._main_app.append_log(f" ║  {_cond_emoji} {_cond_label} → {action if action else '(无)'}")
                    except Exception:
                        pass

                    # ====== 1. 判断条件 ======
                    condition_met = True
                    condition_image = flow.get("condition_image", "")
                    _cond_start = _time.time()

                    if condition == "image_found":
                        if not condition_image:
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  ⚠️ 流程{flow_index+1} image_found 未设置条件图片，条件视为不满足")
                            except Exception:
                                break
                            condition_met = False
                        else:
                            # ★★★ 速度优化：基准从 0.15s → 0.04s（40ms够做一次截图+模板匹配了）
                            # 极速：0.005s / 标准(0.02s flow_gap)：0.04s → 实际执行大多在10~20ms就完成
                            _t = 0.005 if self._turbo_mode else max(0.01, 0.04 * self._speed_scale)
                            loc = find_image_with_timeout(condition_image, confidence=0.8, timeout=_t, consider_color=False, stop_check=lambda: not self.running, skip_small_match=True)
                            condition_met = loc is not None
                            _cond_elapsed = _time.time() - _cond_start
                            try:
                                if self._main_app is not None:
                                    _mode_tag = ' (⚡极速)' if self._turbo_mode else f' (x{self._speed_scale:.1f})'
                                    self._main_app.append_log(f" ║  🔍 流程{flow_index+1} image_found: {_cond_elapsed:.3f}s {'✅ 满足' if condition_met else '❌ 不满足'}{_mode_tag}")
                            except Exception:
                                break
                    elif condition == "image_not_found":
                        if not condition_image:
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  ⚠️ 流程{flow_index+1} image_not_found 未设置条件图片，条件视为不满足")
                            except Exception:
                                break
                            condition_met = False
                        else:
                            # image_not_found 本来就是 timeout=0.01 快速检测，极速模式不变
                            loc = find_image_with_timeout(condition_image, confidence=0.8, timeout=0.01, consider_color=False, stop_check=lambda: not self.running, skip_small_match=True)
                            condition_met = loc is None
                            _cond_elapsed = _time.time() - _cond_start
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  👻 流程{flow_index+1} image_not_found: {_cond_elapsed:.3f}s {'✅ 满足' if condition_met else '❌ 不满足'}")
                            except Exception:
                                break
                    elif condition == "wait_for_image":
                        def _wf_log(msg):
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  {msg}")
                            except Exception:
                                pass
                        if not condition_image:
                            _wf_log(f"⚠ 未设置条件图片，条件不满足")
                            condition_met = False
                        else:
                            raw_timeout = flow.get("wait_timeout", 30)
                            try:
                                wait_timeout = float(raw_timeout)
                                if wait_timeout <= 0:
                                    wait_timeout = 30.0
                            except (TypeError, ValueError):
                                wait_timeout = 30.0
                            _wf_log(f"⏳ 开始等待出现，timeout={wait_timeout}s{' (⚡极速模式)' if self._turbo_mode else ''}")
                            condition_met = False
                            _wait_deadline = _time.time() + wait_timeout
                            _poll_cnt = 0
                            _disappeared = False
                            # 速度比例缩放：step_interval=0.1→标准值, 0.05→减半, 0→极速值
                            _wf_confidence = 0.9
                            _wf_timeout = 0.08 if self._turbo_mode else max(0.04, 0.2 * self._speed_scale)
                            _wf_poll = 0.02 if self._turbo_mode else max(0.01, 0.1 * self._speed_scale)
                            _wf_confirm_count = 0 if self._turbo_mode else (0 if self._speed_scale < 0.6 else 1)
                            _wf_confirm_sleep = 0.02 if self._turbo_mode else max(0.01, 0.08 * self._speed_scale)
                            while self.running and _time.time() < _wait_deadline:
                                _poll_cnt += 1
                                loc = find_image_with_timeout(condition_image, confidence=_wf_confidence, timeout=_wf_timeout, consider_color=False, stop_check=lambda: not self.running, strict=True, skip_small_match=True)
                                if not _disappeared:
                                    if loc is None:
                                        _disappeared = True
                                        _wf_log(f"👁 图片已消失，开始等待出现")
                                    else:
                                        if _poll_cnt % 10 == 0:
                                            _wf_log(f"⏳ 等待图片消失中(已轮询{_poll_cnt}次)")
                                    _time.sleep(_wf_poll)
                                    continue
                                if loc is not None:
                                    # 极速模式：不做重复确认，1次命中即成立（避免两次间的0.08秒延迟）
                                    _confirm = 1
                                    for _ci in range(_wf_confirm_count):
                                        _time.sleep(_wf_confirm_sleep)
                                        _cloc = find_image_with_timeout(condition_image, confidence=_wf_confidence, timeout=_wf_timeout, consider_color=False, stop_check=lambda: not self.running, strict=True, skip_small_match=True)
                                        if _cloc is not None:
                                            _confirm += 1
                                    _need = _wf_confirm_count + 1
                                    if _confirm >= _need:
                                        condition_met = True
                                        _wf_log(f"✅ 确认图片出现！第{_poll_cnt}次检测({_need}中{_confirm})")
                                        break
                                    else:
                                        _wf_log(f"⚠ 第{_poll_cnt}次检测误报({_confirm}/{_need}确认失败)，继续等待")
                                if _poll_cnt % 10 == 0:
                                    _wf_log(f"⏳ 等待图片出现中(已轮询{_poll_cnt}次，剩余{max(0,_wait_deadline-_time.time()):.1f}s)")
                                _time.sleep(_wf_poll)
                            _cond_elapsed = _time.time() - _cond_start
                            if not _disappeared:
                                _wf_log(f"⚠ 图片始终存在(未消失)，超时{_cond_elapsed:.1f}s 结果=不满足")
                            else:
                                _wf_log(f"📊 结束: {_cond_elapsed:.1f}s 轮询{_poll_cnt}次 结果={'满足' if condition_met else '不满足(超时)'}")
                    elif condition == "always":
                        try:
                            if self._main_app is not None:
                                self._main_app.append_log(f" ║  ▶ 流程{flow_index+1} always 条件: 跳过判断")
                        except Exception:
                            break

                    # ====== 2. 决定执行哪个分支的动作 ======
                    use_branch = "main" if condition_met else "else"
                    branch_label = "主分支" if condition_met else "Else分支"
                    target_action = action if condition_met else else_branch.get("action", "")
                    target_else_branch = else_branch if not condition_met else None
                    # 取当前被执行分支的 delay_after（动作执行完后等待多久再进入下一个流程）
                    delay_after = 0.0
                    if condition_met:
                        delay_after = flow.get("delay_after", 0) or 0
                    else:
                        delay_after = (else_branch or {}).get("delay_after", 0) or 0
                    delay_after = max(0.0, float(delay_after))

                    step_info = {
                        "step_num": flow_index + 1,
                        "total_steps": len(flows),
                        "condition": condition,
                        "action": target_action,
                        "branch": branch_label,
                        "loop": loop,
                        "total_loops": total_loops,
                    }
                    if self._on_step:
                        self._on_step(step_info)

                    # ====== 3. 处理跳转/结束 ======
                    if target_action and target_action.startswith("跳转_"):
                        try:
                            if self._main_app is not None:
                                self._main_app.append_log(f" ║  🔀 流程{flow_index+1}: → 跳转 {target_action} (总跳转: {total_jumps+1})")
                        except Exception:
                            break
                        try:
                            target = int(target_action.split("_")[1])
                        except (IndexError, ValueError):
                            target = -1
                        if 0 <= target < len(flows):
                            total_jumps += 1
                            if total_jumps > max_jumps:
                                try:
                                    if self._main_app is not None:
                                        self._main_app.append_log(f" ║  ⛔ 跳转次数超过上限({max_jumps})，停止")
                                        self._main_app.append_log(f"╚═{'═'*40}")
                                except Exception:
                                    break
                                # 设置 running=False 确保停止整个组合技（而非仅跳出内层 while）
                                self.running = False
                                break
                            flow_index = target
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  ➡️ 跳转到流程 {target+1}")
                            except Exception:
                                break
                            # 跳转后的等待：delay_after > 0 时优先用单独设置；否则用统一的 _flow_gap（用户设0就真0）
                            _wait = delay_after if (delay_after and delay_after > 0) else (self._flow_gap if hasattr(self, '_flow_gap') else 0.01)
                            if _wait and _wait > 0:
                                try:
                                    if self._main_app is not None:
                                        self._main_app.append_log(f" ║  ⏱️ 跳转后等待: {_wait:.2f}s{' (统一间隔)' if not (delay_after and delay_after>0) else ''}")
                                except Exception:
                                    pass
                                self._wait_interruptible(_wait)
                            continue
                        else:
                            flow_index += 1
                            continue
                    elif target_action == "end":
                        break

                    # ====== 4. 执行动作 ======
                    if target_action:
                        _exec_start = _time.time()
                        try:
                            if self._main_app is not None:
                                self._main_app.append_log(f" ║  ▶ 执行动作 '{target_action}'")
                        except Exception:
                            break
                        _action_result = self._execute_action(target_action)
                        if isinstance(_action_result, tuple):
                            _action_ok, _img_fail_count = _action_result
                        else:
                            _action_ok, _img_fail_count = _action_result, 0
                        _exec_elapsed = _time.time() - _exec_start
                        try:
                            if self._main_app is not None:
                                _emoji = "✅" if _action_ok else "❌"
                                self._main_app.append_log(f" ║  {_emoji} Flow{flow_index+1} 动作完成: {_exec_elapsed:.3f}s 图片匹配失败={_img_fail_count}")
                            try:
                                self._combo_flow_times.append((flow_index, target_action, _exec_elapsed))
                            except Exception:
                                pass
                        except Exception:
                            break
                        # skip_on_fail 开启时，即使全部步骤失败也不计入连续失败（避免很快停止）
                        if not _action_ok and not self.skip_on_fail:
                            self._consecutive_failures += 1
                            if self._consecutive_failures >= 10000:
                                try:
                                    if self._main_app is not None:
                                        self._main_app.append_log(f" ║  ⛔ 连续 {self._consecutive_failures} 次执行失败，停止组合技")
                                        self._main_app.append_log(f"╚═{'═'*40}")
                                except Exception:
                                    break
                                # 设置running=False，确保停止整个组合技（不只跳出内层while）
                                self.running = False
                                break
                        else:
                            self._consecutive_failures = 0
                        # 录制回放中图片匹配失败 → 跳过该流程，继续执行下一个
                        if _img_fail_count > 0 and condition not in ("wait_for_image", "image_not_found"):
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  ⚠️ 录制回放中图片匹配失败 {_img_fail_count} 次，跳过此流程继续执行")
                            except Exception:
                                pass

                    try:
                        if self._main_app is not None:
                            self._main_app.append_log(f"╚═{'═'*40}")
                    except Exception:
                        pass

                    # 流程结束后的等待：delay_after>0时用单独设置；否则用统一的 _flow_gap（用户设0就真0，不再强制死值）
                    if delay_after and delay_after > 0 and self.running:
                        try:
                            if self._main_app is not None:
                                self._main_app.append_log(f" ║  ⏱️ 动作后等待: {delay_after:.1f}s")
                        except Exception:
                            pass
                        self._wait_interruptible(delay_after)
                    else:
                        _gap = self._flow_gap if hasattr(self, '_flow_gap') else 0.05
                        if _gap and _gap > 0 and self.running:
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  ⏱️ 流程间等待(统一间隔): {_gap:.2f}s")
                            except Exception:
                                pass
                            self._wait_interruptible(_gap)
                        # _gap == 0 → 用户明确设了0秒(极速) → 完全不等待
                    flow_index += 1

                _loop_elapsed = _time.time() - _loop_start
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(f" ║  ⏱️ 第{loop}轮循环完成")
                except Exception:
                    pass
                self.reset()

            _run_elapsed = _time.time() - _run_start
            # ===== 耗时统计汇总（面板内可见，定位最慢流程/最慢单步）=====
            try:
                if self._main_app is not None:
                    _st = getattr(self, '_combo_step_times', [])
                    _ft = getattr(self, '_combo_flow_times', [])
                    self._main_app.append_log(f"╔═ {'═'*45}")
                    self._main_app.append_log(f" ║  📊 耗时统计汇总")
                    self._main_app.append_log(f" ║    总耗时: {_run_elapsed:.3f}s | 流程数: {len(flows)} | 执行步数: {len(_st)}")
                    if _ft:
                        # 按流程聚合（同一流程可能被执行多次，取平均）
                        _by_flow = {}
                        for _f, _a, _d in _ft:
                            _by_flow.setdefault(_f, []).append(_d)
                        _avg = sorted(
                            ((_f, sum(_ds) / len(_ds), len(_ds)) for _f, _ds in _by_flow.items()),
                            key=lambda x: x[1], reverse=True
                        )
                        _top = " > ".join(f"流程{_f + 1} {_avg_d * 1000:.0f}ms(×{_n})" for _f, _avg_d, _n in _avg[:3])
                        self._main_app.append_log(f" ║    最慢流程(均): {_top}")
                    if _st:
                        _ss = max(_st, key=lambda x: x[2])
                        self._main_app.append_log(f" ║    ⚠️ 最慢单步: 流程{_ss[3] + 1} 步骤{_ss[0]}({_ss[1]}): {_ss[2]:.0f}ms")
                    self._main_app.append_log(f"╚═{'═'*45}")
            except Exception:
                pass
            if self.running:
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(f" ║  ✅ 组合技完毕: {_run_elapsed:.3f}s")
                        self._main_app.append_log(f"╚═{'═'*45}")
                except Exception:
                    pass
                if self._on_finished:
                    self._on_finished(True, f"组合技 '{self.skill_data.get('name', '')}' 执行完成")
            else:
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(f" ║  ⏹️ 组合技被停止，已执行: {_run_elapsed:.3f}s")
                        self._main_app.append_log(f"╚═{'═'*45}")
                except Exception:
                    pass
                if self._on_finished:
                    self._on_finished(False, "已停止")

        except Exception as e:
            import traceback
            traceback.print_exc()
            if self._on_finished:
                self._on_finished(False, f"执行失败: {str(e)}")
        finally:
            self.running = False

    def _combo_step_timing_cb(self, step, action, ms):
        """逐步骤耗时回调：同时累计到面板计时器数据，并实时打印到组合技日志"""
        try:
            _fid = getattr(self, '_current_flow_index', 0)
            self._combo_step_times.append((step, action, ms, _fid))
            if self._main_app is not None:
                self._main_app.append_log(f" ║    ⏱ 步骤{step}({action}): {ms:.0f}ms  [流程{_fid + 1}]")
        except Exception:
            pass

    def _execute_action(self, action):
        import time as _time
        if not action or action == "end":
            return True, 0
        try:
            skip_on_fail = self.skill_data.get("skip_on_fail", False)
            _ea_start = _time.time()
            from utils import get_recordings_path, load_json_data
            folder_path = os.path.join(get_recordings_path(), action)
            json_path = os.path.join(folder_path, "recording.json")
            if not os.path.exists(json_path):
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(f" ║  ❌ 找不到录制文件: {action} ({_time.time()-_ea_start:.3f}s)")
                except Exception:
                    pass
                return False, 0

            _t_load0 = _time.time()
            recording_data = load_json_data(json_path)
            _t_load1 = _time.time()
            try:
                if self._main_app is not None:
                    self._main_app.append_log(f" ║  📂 load_json_data: {_t_load1-_t_load0:.3f}s 共{len(recording_data) if recording_data else 0}步")
            except Exception:
                pass
            if not recording_data:
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(f" ║  ⚠️ 录制数据为空: {action}")
                except Exception:
                    pass
                return False, 0

            # ======================================================================
            # ★★★ 回放前自修复：如果 recording.json 的image字段 与 磁盘图片文件顺序错位
            #        （由之前删除纯坐标步骤的bug引起），直接在内存中修复对齐（不写盘）
            # ======================================================================
            try:
                import re as _re_exec
                _disk_imgs_exec = [_f for _f in os.listdir(folder_path)
                                   if _f.lower().endswith('.png') and _re_exec.search(r'操作(\d+)\.png', _f)]
                def _dn_exec(_f):
                    _mm = _re_exec.search(r'操作(\d+)\.png', _f)
                    return int(_mm.group(1)) if _mm else 999999
                _disk_imgs_exec_sorted = sorted(_disk_imgs_exec, key=_dn_exec)
                _disk_cnt = len(_disk_imgs_exec_sorted)
                _json_imgs_idx = [i for i, d in enumerate(recording_data) if d.get('image')]
                _json_cnt = len(_json_imgs_idx)
                # 检查是否错位：有任意image条目不对应"第几次出现就该是操作N.png"→修复
                _need_fix_exec = False
                if _disk_cnt != _json_cnt:
                    _need_fix_exec = True
                else:
                    _c_exec = 0
                    for i, d in enumerate(recording_data):
                        if d.get('image'):
                            _c_exec += 1
                            _expected_exec = f"操作{_c_exec}.png"
                            if d.get('image') != _expected_exec or not os.path.exists(os.path.join(folder_path, _expected_exec)):
                                _need_fix_exec = True
                                break
                if _need_fix_exec:
                    _img_cnt_exec = 0
                    for i, d in enumerate(recording_data):
                        d['step'] = i + 1
                        if 'image' in d and d.get('image'):
                            _img_cnt_exec += 1
                            if _img_cnt_exec <= _disk_cnt:
                                d['image'] = f"操作{_img_cnt_exec}.png"
                            else:
                                d.pop('image', None)
            except Exception:
                pass

            has_images = any(op.get("image", "") for op in recording_data)
            try:
                if self._main_app is not None:
                    self._main_app.append_log(f" ║  🖼️ 动作 '{action}' 含图片={has_images}, 步骤数={len(recording_data)}")
            except Exception:
                pass

            from image_recognition import replay_coordinate_operations, replay_coordinates_only

            # ── 统一步骤间隔（组合技级配置）──
            # ★★★ 优先级：1. skill_data.step_interval 配置  2. 默认 0.02 秒（和_flow_gap同步，之前0.1s太慢）
            _raw_interval = self.skill_data.get('step_interval', None)
            try:
                if _raw_interval is None:
                    step_interval = 0.02  # ★ 默认0.1s → 0.02s，步间提速5倍
                else:
                    step_interval = float(_raw_interval)
                    if step_interval < 0:
                        step_interval = 0.0
            except (TypeError, ValueError):
                step_interval = 0.02  # ★ 同上

            if has_images:
                _t_replay0 = _time.time()
                # ★ 录制回放内每张图的匹配超时：
                # 极速(step_interval=0)：0.15s/次，只做1次闪匹配
                # 标准(step_interval=0.02s → speed_scale=1.0)：0.75s/次，带轮询（比之前1.5s省一半）
                _match_timeout = 0.15 if self._turbo_mode else min(2.0, max(0.15, 0.75 * self._speed_scale))
                # ★ 速度优化：speed_scale>=1.0（含 25x 这类"想快"的配置）启用 turbo 闪匹配
                #   （局部 ROI 截图 + 全屏兜底，又快又不易 miss）；仅极慢配置才走标准重试
                _turbo = self._turbo_mode or self._speed_scale >= 1.0
                replay_result = replay_coordinate_operations(
                    recording_data, folder_path,
                    replay_interval=step_interval, consider_color=False,
                    match_timeout=_match_timeout,
                    stop_check=lambda: not self.running,
                    skip_cache_clear=True,
                    skip_on_fail=self.skip_on_fail,
                    turbo_match=_turbo,  # 极速/快速模式：一次即止不重试
                    on_step_timing=self._combo_step_timing_cb
                )
                # 兼容新旧返回值
                if len(replay_result) == 3:
                    ok, total, img_fail_count = replay_result
                else:
                    ok, total = replay_result
                    img_fail_count = 0
                _t_replay1 = _time.time()
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(
                            f" ║  ▶ replay_coordinate_operations: {_t_replay1-_t_replay0:.3f}s "
                            f"成功={ok}/{total} 图片匹配失败={img_fail_count} | 步间间隔={step_interval:.2f}s"
                        )
                except Exception:
                    pass
            else:
                _t_replay0 = _time.time()
                ok, total = replay_coordinates_only(
                    recording_data, replay_interval=step_interval,
                    stop_check=lambda: not self.running
                )
                img_fail_count = 0
                _t_replay1 = _time.time()
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(
                            f" ║  ▶ replay_coordinates_only: {_t_replay1-_t_replay0:.3f}s "
                            f"成功={ok}/{total} | 步间间隔={step_interval:.2f}s"
                        )
                except Exception:
                    pass

            # 先计数（不管成功失败，只要调用了就计数）
            try:
                if self._main_app is not None:
                    self._main_app._increment_usage_count(action)
            except Exception:
                pass

            # 如果全部步骤都失败，返回 False
            if ok == 0 and total > 0:
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(f" ║  ❌ 执行失败: {action} 全部 {total} 个步骤均未成功")
                except Exception:
                    pass
                return False, img_fail_count

            try:
                if self._main_app is not None:
                    self._main_app.append_log(f" ║  ✅ 动作 '{action}' 完成: {_time.time()-_ea_start:.3f}s")
            except Exception:
                pass
            return True, img_fail_count
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                if self._main_app is not None:
                    self._main_app.append_log(f" ║  ❌ 执行动作失败: {str(e)}")
            except Exception:
                pass
            return False, 0

    def _wait_interruptible(self, seconds):
        import time
        if not self.running:
            return
        self.interrupt_event.clear()
        self.interrupt_event.wait(timeout=seconds)
        if self.interrupt_event.is_set():
            self.running = False
            return
        if not self.running:
            return



class ComboSkillManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.combo_skills = []
        self.load_combo_skills()
    
    def get_combo_skills_path(self):
        base_dir = get_app_base_dir()
        app_data_dir = os.path.join(base_dir, 'data')
        os.makedirs(app_data_dir, exist_ok=True)
        return os.path.join(app_data_dir, 'combo_skills.json')
    
    def load_combo_skills(self):
        try:
            path = self.get_combo_skills_path()
            if os.path.exists(path):
                from utils import load_json_data
                self.combo_skills = load_json_data(path, [])
                if not isinstance(self.combo_skills, list):
                    self.combo_skills = []
            else:
                self.combo_skills = []
        except:
            self.combo_skills = []
    
    def save_combo_skills(self):
        try:
            from utils import save_json_data
            path = self.get_combo_skills_path()
            save_json_data(path, self.combo_skills)
        except:
            pass
        
# ============================================================
#  直接运行 app.py 将启动 macOS 风格界面
# ============================================================

def start_app():
    """启动 macOS 风格界面"""
    from app_macos import start_macos_app
    start_macos_app()

if __name__ == "__main__":
    # 自动以管理员身份运行：未提权则派生一个管理员进程并退出当前实例，
    # 避免 keyboard 全局热键在非管理员环境下偶发失效。用户取消 UAC 时
    # run_as_admin 返回 False，当前进程降级为非管理员继续运行（仍有提示）。
    if sys.platform == "win32" and not is_admin():
        if run_as_admin():
            sys.exit(0)
    start_app()