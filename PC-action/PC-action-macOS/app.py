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
        # 设置环境变量，禁用UAC提示
        ctypes.windll.kernel32.SetEnvironmentVariableW("__COMPAT_LAYER", "RUNASINVOKER")
    except:
        pass

import json
import time
import threading
import shutil
import copy
from datetime import datetime
import keyboard
import re
import uuid
import traceback
import sqlite3

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
    get_common_dialog_style, get_dynamic_radius
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
        scale = 4
        bm = QBitmap(s.width() * scale, s.height() * scale)
        bm.clear()
        p = QPainter(bm)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, s.width() * scale, s.height() * scale, 14 * scale, 14 * scale)
        p.fillPath(path, Qt.color1)
        p.end()
        from PyQt5.QtGui import QBitmap as _QB
        self.setMask(_QB(bm.scaled(s, Qt.KeepAspectRatio, Qt.SmoothTransformation)))

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


class RechargeDialog(QDialog):
    """简化的充值对话框 - 直接选择VIP时长并支付"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.login_manager = parent.login_manager if parent else None
        self.selected_amount = 0
        self.selected_months = 0
        self.mock_mode = True  # 模拟支付模式，实际部署时应改为False并接入真实支付API
        
        # VIP时长选项 - 1个月、3个月、6个月、12个月，使用生活化比喻
        self.vip_options = [
            {"months": 1, "price": 29, "text": "1个月\n¥29", "description": "仅需一杯奶茶的价格"},
            {"months": 3, "price": 60, "text": "3个月\n¥60", "description": "平均每天只需几毛钱"},
            {"months": 6, "price": 108, "text": "6个月\n¥108", "description": "相当于一顿聚餐的费用"},
            {"months": 12, "price": 180, "text": "12个月\n¥180", "description": "每天不到5毛钱，畅享全年"}
        ]
        
        self.setWindowTitle("VIP充值")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        self.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        # 获取屏幕尺寸，按比例设置对话框大小
        width, height = get_screen_size(0.35)  # 减小到0.35，使弹窗大小适中
        self.resize(width, int(width * 0.3))  # 高度设为宽度的30%，使界面更紧凑
        
        # 应用统一样式
        from styles import apply_dialog_style
        apply_dialog_style(self)
                # 覆盖全局样式：将所有灰色背景替换为白色
        _, sh = get_screen_size()
        inp_r2 = int(sh * 0.006)
        cb_r2 = int(sh * 0.004)
        self.setStyleSheet(self.styleSheet() + f"""
            QLineEdit {{
                background-color: {THEME_CARD};
                color: {THEME_TEXT};
                border: 1px solid {THEME_BORDER};
                border-radius: {inp_r2}px;
                padding: 8px;
                font-family: {MACOS_FONT_STACK};
            }}
            QTextEdit {{
                background-color: {THEME_CARD};
                color: {THEME_TEXT};
                border: 1px solid {THEME_BORDER};
                border-radius: {inp_r2}px;
                padding: 8px;
                font-family: {MACOS_FONT_STACK};
            }}
            QComboBox {{
                background-color: {THEME_CARD};
                color: {THEME_TEXT};
                border: 1px solid {THEME_BORDER};
                border-radius: {cb_r2}px;
                padding: 8px;
                font-family: {MACOS_FONT_STACK};
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {THEME_CARD};
                color: {THEME_TEXT};
                border: 1px solid {THEME_BORDER};
                border-radius: {inp_r2}px;
                padding: 4px;
                font-family: {MACOS_FONT_STACK};
            }}
        """)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self.card_container)
        # 减小布局的左右边距，优化空间利用率
        layout.setContentsMargins(1, 8, 1, 8)  # 进一步减小左右边距至1像素
        layout.setSpacing(8)  # 减小垂直间距
        # 减小布局的左右边距，优化空间利用率
        layout.setContentsMargins(1, 8, 1, 8)  # 进一步减小左右边距至1像素
        layout.setSpacing(8)  # 减小垂直间距
        # 减小布局的左右边距，优化空间利用率
        layout.setContentsMargins(5, 10, 5, 10)  # 进一步减小左右边距至5像素
        layout.setSpacing(8)  # 减小垂直间距
        
        # 标题区域 - macOS风格
        self.title_container = QFrame()
        self.title_container.setStyleSheet(f"""
            QFrame {{
                background-color: #0A84FF;
                border-radius: 12px;
                padding: 8px;
            }}
        """)
        title_layout = QVBoxLayout(self.title_container)

        # 添加皇冠图标
        crown_label = QLabel("👑")
        crown_label.setAlignment(Qt.AlignCenter)
        crown_font = crown_label.font()
        crown_font.setPointSize(24)
        crown_label.setFont(crown_font)
        crown_label.setStyleSheet("color: white;")
        title_layout.addWidget(crown_label)

        # 标题
        title_label = QLabel("选择您的VIP特权")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; margin: 5px 0;")
        title_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("解锁全部功能，享受专业体验")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = subtitle_label.font()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); margin-bottom: 10px;")
        title_layout.addWidget(subtitle_label)

        layout.addWidget(self.title_container)

        # VIP时长选择按钮区域
        button_container = QFrame()
        button_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(10)  # 减小按钮之间的间距
        
        # 月度套餐区域
        monthly_label = QLabel("月度套餐")
        monthly_label.setAlignment(Qt.AlignCenter)
        monthly_font = monthly_label.font()
        monthly_font.setPointSize(14)
        monthly_font.setBold(True)
        monthly_label.setFont(monthly_font)
        monthly_label.setStyleSheet(f"color: {THEME_TEXT}; margin: 10px 0;")
        button_layout.addWidget(monthly_label)
        
        # 月度套餐按钮网格
        monthly_grid = QGridLayout()
        monthly_grid.setSpacing(10)
        
        self.amount_buttons = []
        # 先添加月度套餐（1个月和3个月）
        for i, option in enumerate(self.vip_options[:2]):
            row = i // 2
            col = i % 2
            
            # 创建卡片式按钮
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 0;
                }
                QFrame:hover {
                    background-color: #f8f9ff;
                }
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)  # 去掉布局的外边距
            card_layout.setSpacing(0)  # 去掉标签之间的间距
            
            # 时长标签
            duration_label = QLabel(f"{option['months']}个月")
            duration_label.setAlignment(Qt.AlignCenter)
            duration_font = duration_label.font()
            duration_font.setPointSize(14)
            duration_font.setBold(True)
            duration_label.setFont(duration_font)
            duration_label.setStyleSheet(f"QLabel {{ color: {TEXT}; padding: 0; margin: 0; background-color: transparent !important; border: none !important; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif; }}")
            card_layout.addWidget(duration_label)
            
            # 价格标签
            price_label = QLabel(f"¥{option['price']}")
            price_label.setAlignment(Qt.AlignCenter)
            price_font = price_label.font()
            price_font.setPointSize(18)
            price_font.setBold(True)
            price_label.setFont(price_font)
            # 更强制的样式设置，确保没有背景和边框 - 统一蓝色风格
            price_label.setStyleSheet(f"QLabel {{ color: {THEME_PRIMARY}; padding: 5px 0; margin: 0; background-color: transparent !important; border: none !important; }}")
            card_layout.addWidget(price_label)
            
            # 生活化比喻描述
            desc_label = QLabel(option["description"])
            desc_label.setAlignment(Qt.AlignCenter)
            desc_font = desc_label.font()
            desc_font.setPointSize(9)
            desc_label.setFont(desc_font)
            # 更强制的样式设置，确保没有背景和边框
            desc_label.setStyleSheet("QLabel { color: #8E8E93; padding: 5px 0; margin: 0 0 10px 0; background-color: transparent !important; border: none !important; }")
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label)
            
            # 选择按钮 - macOS渐变风格
            select_button = QPushButton("立即选择")
            select_button.clicked.connect(lambda checked, opt=option: self.process_recharge(opt))
            select_button.setStyleSheet(f"""
QMessageBox QDialogButtonBox QPushButton{{
                    background: {THEME_PRIMARY};
                    color: white;
                    border-radius: 10px;
                    padding: 10px 20px;
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
            
            card_layout.addWidget(select_button)
            monthly_grid.addWidget(card, row, col)
        
        button_layout.addLayout(monthly_grid)
        
        # 热门推荐区域
        recommend_label = QLabel("🔥 热门推荐")
        recommend_label.setAlignment(Qt.AlignCenter)
        recommend_font = recommend_label.font()
        recommend_font.setPointSize(14)
        recommend_font.setBold(True)
        recommend_label.setFont(recommend_font)
        recommend_label.setStyleSheet("color: #FF453A; margin: 15px 0 10px 0;")
        button_layout.addWidget(recommend_label)
        
        # 热门推荐套餐按钮网格
        recommend_grid = QGridLayout()
        recommend_grid.setSpacing(10)
        
        # 添加热门推荐套餐（6个月和12个月）
        for i, option in enumerate(self.vip_options[2:]):
            row = i // 2
            col = i % 2
            
            # 创建卡片式按钮
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 0;
                }
                QFrame:hover {
                    background-color: #f8f9ff;
                }
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)  # 去掉布局的外边距
            card_layout.setSpacing(0)  # 去掉标签之间的间距
            
            # 时长标签
            duration_label = QLabel(f"{option['months']}个月")
            duration_label.setAlignment(Qt.AlignCenter)
            duration_font = duration_label.font()
            duration_font.setPointSize(14)
            duration_font.setBold(True)
            duration_label.setFont(duration_font)
            duration_label.setStyleSheet(f"QLabel {{ color: {TEXT}; padding: 0; margin: 0; background-color: transparent !important; border: none !important; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif; }}")
            card_layout.addWidget(duration_label)
            
            # 价格标签
            price_label = QLabel(f"¥{option['price']}")
            price_label.setAlignment(Qt.AlignCenter)
            price_font = price_label.font()
            price_font.setPointSize(18)
            price_font.setBold(True)
            price_label.setFont(price_font)
            price_label.setStyleSheet(f"QLabel {{ color: {ACCENT}; padding: 5px 0; margin: 0; background-color: transparent !important; border: none !important; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif; }}")
            card_layout.addWidget(price_label)
            
            # 生活化比喻描述
            desc_label = QLabel(option["description"])
            desc_label.setAlignment(Qt.AlignCenter)
            desc_font = desc_label.font()
            desc_font.setPointSize(9)
            desc_label.setFont(desc_font)
            # 更强制的样式设置，确保没有背景和边框
            desc_label.setStyleSheet("QLabel { color: #6c757d; padding: 5px 0; margin: 0 0 10px 0; background-color: transparent !important; border: none !important; }")
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label)
            
            # 选择按钮 - macOS渐变风格
            select_button = QPushButton("立即选择")
            select_button.clicked.connect(lambda checked, opt=option: self.process_recharge(opt))
            select_button.setStyleSheet(f"""
QMessageBox QDialogButtonBox QPushButton{{
                    background: {THEME_PRIMARY};
                    color: white;
                    border-radius: 10px;
                    padding: 10px 20px;
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
            
            card_layout.addWidget(select_button)
            recommend_grid.addWidget(card, row, col)
        
        button_layout.addLayout(recommend_grid)
        
        layout.addWidget(button_container)
        
        # 底部提示
        tip_label = QLabel("💡 提示：VIP用户可享受无限制操作、优先客服支持等特权")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_font = tip_label.font()
        tip_font.setPointSize(9)
        tip_label.setFont(tip_font)
        tip_label.setStyleSheet("color: #6c757d; margin: 10px 0;")
        layout.addWidget(tip_label)
    
    def set_vip_duration(self, option):
        """设置VIP时长 - 已废弃，保留以防其他地方调用"""
        self.selected_months = option["months"]
        self.selected_amount = option["price"]
    
    def process_recharge(self, option):
        """处理充值流程"""
        # 直接使用传入的选项，不需要用户选择
        self.selected_months = option["months"]
        self.selected_amount = option["price"]
        
        # 显示支付二维码
        self._show_payment_qr_code()
    
    def _show_payment_qr_code(self):
        """显示支付二维码"""
        # 创建支付对话框
        payment_dialog = QDialog(self)
        payment_dialog.setWindowTitle("微信支付")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        payment_dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        # 获取屏幕尺寸，按比例设置对话框大小
        width, height = get_screen_size(0.25)  # 减小到0.25，使支付对话框更小
        payment_dialog.resize(width, int(width * 0.35))  # 高度设为宽度的35%，使支付对话框更加紧凑
        
        # 使用统一的样式应用函数
        from styles import apply_dialog_style
        apply_dialog_style(payment_dialog)
        
        layout = QVBoxLayout(payment_dialog)
        
        # 支付信息
        info_label = QLabel(f"VIP时长: {self.selected_months}个月\n支付金额: ¥{self.selected_amount}")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # 二维码占位图
        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignCenter)
        # 按屏幕比例设置二维码大小
        qr_width = int(width * 0.5)  # 宽度为对话框宽度的50%
        qr_label.setMinimumSize(qr_width, qr_width)  # 设置最小尺寸，保持正方形
        qr_label.setMaximumSize(qr_width, qr_width)  # 设置最大尺寸，保持正方形
        
        # 使用通用样式
        from styles import get_input_style
        screen_width, screen_height = get_screen_size()
        qr_label.setStyleSheet(get_input_style(screen_height))
        
        qr_label.setText("微信支付二维码\n(模拟)")
        layout.addWidget(qr_label)
        
        # 支付说明
        note_label = QLabel("请使用微信扫描上方二维码完成支付")
        note_label.setAlignment(Qt.AlignCenter)
        # 按屏幕比例设置字体大小
        screen_width, screen_height = get_screen_size()
        note_font_size = int(screen_height * 0.025)  # 屏幕高度的2.5%
        note_label.setStyleSheet(f"color: #8E8E93; font-size: {note_font_size}px;")
        layout.addWidget(note_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 支付完成按钮
        complete_button = QPushButton("我已完成支付")
        complete_button.clicked.connect(lambda: self._complete_payment(payment_dialog))
        from styles import get_button_style
        screen_width, screen_height = get_screen_size()
        complete_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #0A84FF;
                color: white;
                border-radius: {int(screen_height * 0.015)}px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: {max(16, min(20, int(screen_width * 0.006)))}px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
                min-height: {int(screen_height * 0.04)}px;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)

        button_layout.addWidget(complete_button)

        # 取消按钮 - 统一蓝色风格
        cancel_button = QPushButton("取消支付")
        cancel_button.clicked.connect(payment_dialog.reject)
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: #8E8E93;
                border: 1px solid #D1D1D6;
                border-radius: {int(screen_height * 0.015)}px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: {max(16, min(20, int(screen_width * 0.006)))}px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
                text-align: center;
                min-height: {int(screen_height * 0.04)}px;
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

        cancel_btn.clicked.connect(confirm_dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        
        # 如果是模拟模式，自动模拟支付成功
        if self.mock_mode:
            QTimer.singleShot(3000, lambda: self._simulate_payment_success(payment_dialog))
        
        # 显示支付对话框
        payment_dialog.exec_()
    
    def _simulate_payment_success(self, payment_dialog):
        """模拟支付成功"""
        # 检查对话框是否仍然显示
        if payment_dialog.isVisible():
            self.show_beautiful_message('information', "支付成功", "模拟支付成功！", parent=payment_dialog)
            self._activate_vip()
            payment_dialog.accept()
            self.accept()
    
    def _complete_payment(self, payment_dialog):
        """完成支付"""
        # 创建自定义确认对话框，使用项目统一的按钮样式
        confirm_dialog = QDialog(self)
        confirm_dialog.setWindowTitle("确认支付")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        confirm_dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        confirm_dialog.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置对话框大小
        screen_width, screen_height = get_screen_size()
        dialog_width = int(screen_width * 0.3)
        dialog_height = int(screen_height * 0.2)
        confirm_dialog.resize(dialog_width, dialog_height)
        
        # 创建布局
        layout = QVBoxLayout(confirm_dialog)
        layout.setAlignment(Qt.AlignCenter)
        
        # 标题图标和文本
        icon_label = QLabel("❓")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_font_size = int(screen_height * 0.03)
        icon_label.setStyleSheet(f"font-size: {icon_font_size}px;")
        layout.addWidget(icon_label)
        
        question_label = QLabel("请确认您已完成微信支付？")
        question_label.setAlignment(Qt.AlignCenter)
        question_font_size = int(screen_height * 0.025)
        question_label.setStyleSheet(f"color: {TEXT}; font-size: {question_font_size}px; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")
        layout.addWidget(question_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(int(screen_width * 0.01))
        button_layout.setAlignment(Qt.AlignCenter)
        
        # Yes按钮
        yes_button = QPushButton("Yes")
        yes_button.setMinimumWidth(int(screen_width * 0.1))
        yes_button.setMinimumHeight(int(screen_height * 0.05))
        yes_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #0A84FF;
                color: white;
                border-radius: {int(screen_height * 0.015)}px;
                font-weight: 500;
                font-size: {int(screen_height * 0.02)}px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #006AE0;
            }}
            QPushButton:pressed {{
                background-color: #004DB3;
            }}
        """)
        yes_button.clicked.connect(lambda: self._handle_confirm_yes(confirm_dialog, payment_dialog))
        button_layout.addWidget(yes_button)

        # No按钮 - 统一蓝色风格
        no_button = QPushButton("No")
        no_button.setMinimumWidth(int(screen_width * 0.1))
        no_button.setMinimumHeight(int(screen_height * 0.05))
        no_button.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: #8E8E93;
                border: 1px solid #D1D1D6;
                border-radius: {int(screen_height * 0.015)}px;
                font-weight: 500;
                font-size: {int(screen_height * 0.02)}px;
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
        no_button.clicked.connect(confirm_dialog.reject)
        button_layout.addWidget(no_button)
        
        layout.addLayout(button_layout)
        
        # 居中显示对话框
        confirm_dialog.move(
            (screen_width - dialog_width) // 2,
            (screen_height - dialog_height) // 2
        )
        
        # 显示对话框
        if confirm_dialog.exec_() == QDialog.Accepted:
            pass  # 已经在handle_confirm_yes中处理
    
    def _handle_confirm_yes(self, confirm_dialog, payment_dialog):
        """处理确认支付成功"""
        confirm_dialog.accept()
        self._activate_vip()
        payment_dialog.accept()
        self.accept()
    
    def _activate_vip(self):
        """激活VIP权限"""
        try:
            if not self.login_manager or not self.login_manager.current_user:
                self.show_beautiful_message('warning', "错误", "用户未登录", parent=self)
                return
            
            current_user = self.login_manager.current_user
            
            # 使用DatabaseHelper管理VIP许可证
            success, message = DatabaseHelper.manage_vip_license(current_user, self.selected_months)
            
            if not success:
                self.show_beautiful_message('warning', "错误", message, parent=self)
                return
            
            # 添加充值记录
            DatabaseHelper.add_recharge_record(current_user, self.selected_amount, self.selected_months)
            
            self.show_beautiful_message('information', "充值成功", message, parent=self)
            
            # 通知父窗口更新状态
            if self.parent:
                self.parent.update_status_display()
                
        except Exception as e:
            self.show_beautiful_message('warning', "错误", f"激活VIP失败: {str(e)}", parent=self)
    
    def _add_recharge_record(self, username, amount, months):
        """添加充值记录"""
        try:
            # 使用DatabaseHelper添加充值记录
            DatabaseHelper.add_recharge_record(username, amount, months)
        except Exception as e:
            # print(f"添加充值记录失败: {e}")  # [日志已禁用]
            pass


class FeedbackDialog(QDialog):
    """反馈对话框 - 使用卡片式设计"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("问题反馈")
        # 设置窗口标志：移除帮助按钮，添加最小化按钮
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
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
            count_val = usage_counts.get(name, 0)
            display_time = f"{ctime}  ({count_val}次)" if count_val > 0 else ctime
            ctime_item = QTableWidgetItem(display_time)
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
            import keyboard
            
            # 使用 suppress=True 确保热键被捕获，不传递给其他应用
            # 保存对话框和路径的引用，避免闭包问题
            current_dialog = dialog
            current_folder = folder_path
            
            def view_images_grave_handler():
                """查看图片窗口中 grave 键的处理"""
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
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll_root = QWidget()  # 最外层容器 (撑满滚动区)
        scroll_root.setStyleSheet("background: transparent; border: none;")
        root_layout = QHBoxLayout(scroll_root)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # 居中定宽容器：列表宽度不超过 560px，居中显示
        list_wrapper = QWidget()
        list_wrapper.setMaximumWidth(9999)
        list_wrapper.setStyleSheet("background: transparent; border: none;")
        list_layout = QVBoxLayout(list_wrapper)
        list_layout.setContentsMargins(12, 8, 12, 8)
        list_layout.setSpacing(4)
        root_layout.addWidget(list_wrapper)
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
        image_files.sort(key=lambda x: int(re.search(r'操作(\d+)', x).group(1)) if re.search(r'操作(\d+)', x) else 0)
        
        # 检查是否有recording.json文件（坐标录制）
        recording_json_path = os.path.join(folder_path, 'recording.json')
        has_recording_json = os.path.exists(recording_json_path)
        
        # 如果没有图片文件，但有recording.json，显示坐标录制数据
        if not image_files:
            if has_recording_json:
                # 显示坐标录制数据
                self.show_coordinate_data(dialog, folder_path, recording_json_path)
                return
            else:
                self.parent.show_beautiful_message('information', "提示", "该文件夹中没有图片文件！", parent=dialog)
                return
        
        # 从recording.json加载操作方式
        self._populate_image_rows(dialog, folder_path, list_layout)
        scroll_area.setWidget(scroll_root)
        _cl.addWidget(scroll_area)
        layout.addWidget(_outer)
        # 添加底部按钮区域 - macOS风格
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(16, 8, 16, 12)
        
        # 继续添加操作按钮
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
                    import keyboard
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
            step_a = idx_a + 1
            step_b = idx_b + 1
            if idx_a >= len(recording_data) or idx_b >= len(recording_data):
                return
            recording_data[idx_a], recording_data[idx_b] = recording_data[idx_b], recording_data[idx_a]
            for i, rec in enumerate(recording_data):
                rec['step'] = i + 1
                if 'image' in rec:
                    rec['image'] = f"操作{i + 1}.png"
            save_json_data(recording_json_path, recording_data)
            step_a_old = idx_a + 1
            step_b_old = idx_b + 1
            img_a = os.path.join(folder_path, f"操作{step_a_old}.png")
            img_b = os.path.join(folder_path, f"操作{step_b_old}.png")
            img_a_tmp = os.path.join(folder_path, f"操作{step_a_old}_tmp.png")
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

    def _populate_image_rows(self, dialog, folder_path, list_layout):
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
        image_files.sort(key=lambda x: int(re.search(r'操作(\d+)', x).group(1)) if re.search(r'操作(\d+)', x) else 0)
        if not image_files:
            return
        recording_json_path = os.path.join(folder_path, 'recording.json')
        has_recording_json = os.path.exists(recording_json_path)
        self.image_actions = []
        if has_recording_json:
            recording_data = load_json_data(recording_json_path)
            if isinstance(recording_data, list):
                action_type_map = {'left_click':'Click', 'right_click':'右击', 'double_click':'双击', 'middle_click':'中键点击'}
                # 构建步骤号→操作文本的映射，避免因键盘操作无图片导致的错位
                step_action_map = {}
                for step in recording_data:
                    step_num = step.get('step', 0)
                    action_type = step.get('action_type', 'left_click')
                    if action_type in ['keyboard', 'keyboard_direct']:
                        key_text = step.get('key', '')
                        step_action_map[step_num] = f"按键: {key_text}"
                    elif action_type == 'text_input':
                        text_content = step.get('text', '')
                        display_text = text_content if len(text_content) <= 10 else text_content[:10] + "..."
                        step_action_map[step_num] = f"文本: {display_text}"
                    elif action_type == 'scroll':
                        scroll_amount = step.get('scroll_amount', 3)
                        direction = "上" if scroll_amount > 0 else "下"
                        step_action_map[step_num] = f"滚动: {direction}{abs(scroll_amount)}"
                    elif action_type == 'condition':
                        step_action_map[step_num] = "条件分支"
                    else:
                        step_action_map[step_num] = action_type_map.get(action_type, 'Click')
                # 根据image_files的顺序构建image_actions，确保两者完全对齐
                for img_file in image_files:
                    match = re.search(r'操作(\d+)', img_file)
                    if match:
                        step_num = int(match.group(1))
                        self.image_actions.append(step_action_map.get(step_num, 'Click'))
                    else:
                        self.image_actions.append('Click')
        # 如果没有JSON数据，使用默认值
        if not self.image_actions:
            self.image_actions = ["Click"] * len(image_files)
        


        def delete_image(img_file):
            """删除指定图片"""
            # 重新加载当前图片列表，确保索引正确
            current_image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
            current_image_files.sort(key=lambda x: int(re.search(r'操作(\d+)', x).group(1)) if re.search(r'操作(\d+)', x) else 0)
            
            if img_file not in current_image_files:
                return
                
            img_path = os.path.join(folder_path, img_file)
            
            confirm_dialog = QDialog(dialog)
            confirm_dialog.setWindowTitle("确认删除")
            confirm_dialog.setFixedSize(300, 120)
            layout = QVBoxLayout(confirm_dialog)
            layout.setSpacing(10)
            layout.setContentsMargins(15, 15, 15, 15)
            
            label = QLabel(f"确定要删除 '{img_file}' 吗？\n这将重新排序后续图片。")
            layout.addWidget(label)
            
            button_layout = QHBoxLayout()
            button_layout.setSpacing(8)
            
            ok_btn = QPushButton("确定")
            ok_btn.setMinimumSize(60, 28)
            ok_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0A84FF;
                    color: white;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                background-color: #006AE0;
                }
            """)
            button_layout.addWidget(ok_btn)

            cancel_btn = QPushButton("取消")
            cancel_btn.setMinimumSize(60, 28)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8E8E93;
                    color: white;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #0A84FF;
                }
            """)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            ok_btn.clicked.connect(confirm_dialog.accept)
            cancel_btn.clicked.connect(confirm_dialog.reject)
            
            if confirm_dialog.exec_() != QDialog.Accepted:
                return
            
            try:
                # 删除图片文件
                if os.path.exists(img_path):
                    os.remove(img_path)
                
                # 删除对应的recording.json中的记录
                recording_json_path = os.path.join(folder_path, 'recording.json')
                recording_data = []
                if os.path.exists(recording_json_path):
                    recording_data = load_json_data(recording_json_path)
                    recording_data.sort(key=lambda x: x.get('step', 0))
                
                # 根据图片文件名中的操作编号找到对应的记录
                step_match = re.search(r'操作(\d+)\.png', img_file)
                if step_match:
                    deleted_step = int(step_match.group(1))
                    # 找到对应step的记录并删除
                    for i, step in enumerate(recording_data):
                        if step.get('step', 0) == deleted_step:
                            del recording_data[i]
                            break
                    
                    # 重命名后续图片文件（按编号从大到小排序，避免重名冲突）
                    other_files = [
                        f for f in os.listdir(folder_path)
                        if f.lower().endswith('.png') and f != img_file
                        and re.search(r'操作(\d+)\.png', f)
                    ]
                    other_files.sort(key=lambda x: -int(re.search(r'操作(\d+)\.png', x).group(1)))
                    for other_file in other_files:
                        other_match = re.search(r'操作(\d+)\.png', other_file)
                        if other_match:
                            other_step = int(other_match.group(1))
                            if other_step > deleted_step:
                                new_step = other_step - 1
                                new_name = f"操作{new_step}.png"
                                old_path = os.path.join(folder_path, other_file)
                                new_path = os.path.join(folder_path, new_name)
                                if os.path.exists(old_path) and not os.path.exists(new_path):
                                    os.rename(old_path, new_path)
                    
                    # 重新排序步骤，并同步更新image字段
                    for i, step in enumerate(recording_data):
                        step['step'] = i + 1
                        # 如果记录中有image字段，同步更新文件名以匹配新的序号
                        if 'image' in step:
                            old_image_name = step['image']
                            image_match = re.search(r'操作(\d+)\.png', old_image_name)
                            if image_match:
                                old_image_step = int(image_match.group(1))
                                # 只更新那些在被删除步骤之后的记录的image字段
                                if old_image_step > deleted_step:
                                    new_image_step = old_image_step - 1
                                    step['image'] = f"操作{new_image_step}.png"
                    
                    save_json_data(recording_json_path, recording_data)
                
                # 删除成功，不再弹出提示窗口
                self.refresh_view_images(folder_path)
                
            except Exception as e:
                self.parent.show_beautiful_message('critical', "错误", f"删除失败: {str(e)}", parent=dialog)

        def _show_large_preview(img_path):
            """弹出大图预览窗口"""
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QScrollArea
            preview = QDialog(dialog)
            preview.setWindowTitle("图片预览")
            preview.setWindowFlags(preview.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            # 获取屏幕尺寸
            from PyQt5.QtWidgets import QDesktopWidget
            desktop = QDesktopWidget()
            sw = desktop.screenGeometry().width()
            sh = desktop.screenGeometry().height()
            max_w = int(sw * 0.7)
            max_h = int(sh * 0.7)
            preview.resize(max_w, max_h)

            layout = QVBoxLayout(preview)
            layout.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea(preview)
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: #1C1C1E; }")

            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            fp = load_qpixmap(img_path)
            if fp:
                # 等比例缩放
                fp = fp.scaled(max_w - 20, max_h - 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(fp)
            img_label.setStyleSheet("background: #1C1C1E; padding: 10px;")
            scroll.setWidget(img_label)
            layout.addWidget(scroll)
            preview.exec_()

        control_height = 24
        action_font_size = 11
        row_height = 54

        for i, img_file in enumerate(image_files):
            img_path = os.path.join(folder_path, img_file)
            step_num = i + 1

            # 每行 = macOS 卡片风格
            row_widget = QWidget()
            row_widget.setFixedHeight(72)
            row_widget.setStyleSheet("""
                QWidget#listRow {
                    background: rgba(245, 245, 247, 0.8);
                    border-radius: 0px;
                    border: none;
                }

            """)
            row_widget.setObjectName("listRow")

            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 8, 12, 10)
            row_layout.setSpacing(10)

            # ── ① 编号徽章 (macOS badge 风格) ──
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
            row_layout.addWidget(step_label)

            # ── ② 圆角缩略图 ──
            thumb_w = QPushButton()
            thumb_w.setFixedSize(48, 48)
            thumb_w.setStyleSheet("QPushButton { background: rgba(195,240,202,0.3); border-radius: 8px; }")
            del_btn = _create_hover_close_button(
                thumb_w,
                on_click=lambda checked=False, fn=img_file: delete_image(fn),
                size=20
            )
            del_btn.move(26, 0)
            pixmap = load_qpixmap(img_path)
            if pixmap is None:
                self.parent.show_beautiful_message('warning', "警告", f"无法加载图片: {img_file}", parent=dialog)
                continue
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
            pixmap = None
            row_layout.addWidget(thumb_w)

            # 点击缩略图查看大图
            thumb_w.clicked.connect(lambda checked, fp=img_path: _show_large_preview(fp))

            # ── ③ 操作控件（统一 90px 宽） ──
            ACT_W = 90
            if i < len(self.image_actions):
                at = self.image_actions[i]

                if at.startswith("按键:"):
                    kw = QLabel(f"⌨️ {at.replace('按键: ','')}")
                    kw.setFixedSize(ACT_W, control_height)
                    kw.setStyleSheet(f"QLabel {{ background: rgba(10,132,255,0.15); color: #0A84FF; padding: 0 6px; border-radius: 12px; font-weight: bold; font-size: {action_font_size}px; }}")
                    kw.setCursor(Qt.PointingHandCursor)
                    kw.setAlignment(Qt.AlignCenter)
                    kw.mousePressEvent = lambda e, idx=i, fp=folder_path: self.show_key_input_dialog(idx, fp)
                    _aw=QWidget();_aw.setFixedWidth(ACT_W);_al=QHBoxLayout(_aw);_al.setContentsMargins(0,0,0,0);_al.addWidget(kw);row_layout.addWidget(_aw)
                elif at.startswith("滚动:"):
                    sw = QLabel(f"🔄 {at.replace('滚动: ','')}")
                    sw.setFixedSize(ACT_W, control_height)
                    sw.setStyleSheet(f"QLabel {{ background: rgba(142,142,147,0.2); color: #6E6E73; padding: 0 6px; border-radius: 12px; font-weight: bold; font-size: {action_font_size}px; }}")
                    sw.setCursor(Qt.PointingHandCursor)
                    sw.setAlignment(Qt.AlignCenter)
                    sw.mousePressEvent = lambda e, idx=i, fp=folder_path: self.show_scroll_input_dialog(idx, fp)
                    _aw=QWidget();_aw.setFixedWidth(ACT_W);_al=QHBoxLayout(_aw);_al.setContentsMargins(0,0,0,0);_al.addWidget(sw);row_layout.addWidget(_aw)
                elif at.startswith("文本:"):
                    tw_w = QLabel("📝 文本")
                    tw_w.setFixedSize(ACT_W, control_height)
                    tw_w.setStyleSheet(f"QLabel {{ background: rgba(255,149,0,0.15); color: #FF9500; padding: 0 6px; border-radius: 12px; font-weight: bold; font-size: {action_font_size}px; }}")
                    tw_w.setCursor(Qt.PointingHandCursor)
                    tw_w.setAlignment(Qt.AlignCenter)
                    tw_w.mousePressEvent = lambda e, idx=i, fp=folder_path: self.show_text_input_dialog(idx, fp)
                    _aw=QWidget();_aw.setFixedWidth(ACT_W);_al=QHBoxLayout(_aw);_al.setContentsMargins(0,0,0,0);_al.addWidget(tw_w);row_layout.addWidget(_aw)
                elif at == "条件分支":
                    cw = QLabel("🔀 条件分支")
                    cw.setFixedSize(ACT_W, control_height)
                    cw.setStyleSheet(f"QLabel {{ background: rgba(175,82,222,0.15); color: #AF52DE; padding: 0 6px; border-radius: 12px; font-weight: bold; font-size: {action_font_size}px; }}")
                    cw.setAlignment(Qt.AlignCenter)
                    _aw=QWidget();_aw.setFixedWidth(ACT_W);_al=QHBoxLayout(_aw);_al.setContentsMargins(0,0,0,0);_al.addWidget(cw);row_layout.addWidget(_aw)
                elif at in ["Click", "右击", "双击", "中击"]:
                    ci = {"Click": "👆", "右击": "👉", "双击": "👆👆", "中击": "🖱️"}
                    cc = {"Click": "#8E8E93", "右击": "#8E8E93", "双击": "#8E8E93", "中击": "#8E8E93"}
                    cb = QPushButton(f"{ci.get(at, '👆')} {at}")
                    cb.setFixedSize(ACT_W, control_height)
                    cb.setCursor(Qt.PointingHandCursor)
                    _menu = QMenu()
                    for _t in [f"{ci['Click']} Click", f"{ci['右击']} 右击", f"{ci['双击']} 双击", f"{ci['中击']} 中击"]:
                        _a = _menu.addAction(_t)
                        _a.triggered.connect(lambda checked, txt=_t, btn=cb, ii=i, fp=folder_path: (btn.setText(txt), self.update_action(ii, txt.split(' ', 1)[1] if ' ' in txt else txt, fp)))
                    cb.setMenu(_menu)
                    c = cc.get(at, "#8E8E93")
                    cb.setStyleSheet(f"""
                        QPushButton {{ background: rgba(52,199,89,0.15); color: #34C759; border: none; border-radius: 12px; font-weight: 600; font-size: 10px; padding: 0; text-align: center; }}
                        QPushButton:hover {{ background: rgba(200,200,210,0.4); }}
                        QPushButton::menu-indicator {{ width: 0; }}
                    """)
                    
                    _aw=QWidget();_aw.setFixedWidth(ACT_W);_al=QHBoxLayout(_aw);_al.setContentsMargins(0,0,0,0);_al.addWidget(cb,0,Qt.AlignCenter);row_layout.addWidget(_aw,0,Qt.AlignVCenter)
                else:
                    cb = QPushButton(f"{ci.get(at, '👆')} {at}")
                    cb.setFixedSize(ACT_W, control_height)
                    cb.setCursor(Qt.PointingHandCursor)
                    _menu = QMenu()
                    for _t in [f"{ci['Click']} Click", f"{ci['右击']} 右击", f"{ci['双击']} 双击", f"{ci['中击']} 中击"]:
                        _a = _menu.addAction(_t)
                        _a.triggered.connect(lambda checked, txt=_t, btn=cb, ii=i, fp=folder_path: (btn.setText(txt), self.update_action(ii, txt.split(' ', 1)[1] if ' ' in txt else txt, fp)))
                    cb.setMenu(_menu)
                    cb.setStyleSheet(f"""
                        QPushButton {{ background: rgba(52,199,89,0.15); color: #34C759; border: none; border-radius: 12px; font-weight: 600; font-size: 10px; padding: 0; text-align: center; }}
                        QPushButton:hover {{ background: rgba(200,200,210,0.4); }}
                        QPushButton::menu-indicator {{ width: 0; }}
                    """)
                    
                    _aw=QWidget();_aw.setFixedWidth(ACT_W);_al=QHBoxLayout(_aw);_al.setContentsMargins(0,0,0,0);_al.addWidget(cb,0,Qt.AlignCenter);row_layout.addWidget(_aw,0,Qt.AlignVCenter)
            else:
                cb = QPushButton(f"{ci['Click']} Click")
                cb.setFixedSize(ACT_W, control_height)
                cb.setCursor(Qt.PointingHandCursor)
                _menu = QMenu()
                for _t in [f"{ci['Click']} Click", f"{ci['右击']} 右击", f"{ci['双击']} 双击", f"{ci['中击']} 中击"]:
                    _a = _menu.addAction(_t)
                    _a.triggered.connect(lambda checked, txt=_t, btn=cb, ii=i, fp=folder_path: (btn.setText(txt), self.update_action(ii, txt.split(' ', 1)[1] if ' ' in txt else txt, fp)))
                cb.setMenu(_menu)
                cb.setStyleSheet(f"""
                    QPushButton {{ background: rgba(52,199,89,0.15); color: #34C759; border: none; border-radius: 12px; font-weight: 600; font-size: 10px; padding: 0; text-align: center; }}
                    QPushButton:hover {{ background: rgba(200,200,210,0.4); }}
                    QPushButton::menu-indicator {{ width: 0; }}
                """)
                
                _aw=QWidget();_aw.setFixedWidth(ACT_W);_al=QHBoxLayout(_aw);_al.setContentsMargins(0,0,0,0);_al.addWidget(cb,0,Qt.AlignCenter);row_layout.addWidget(_aw,0,Qt.AlignVCenter)

            # ── ④ 延迟 ⏱0.5s ──
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
            ds.setValue(self.get_delay_for_step(folder_path, i))
            ds.valueChanged.connect(lambda v, ii=i, fp=folder_path: self.update_delay(ii, v, fp))
            ds.setFixedSize(40, control_height)
            ds.setStyleSheet("QDoubleSpinBox { background: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 8px; font-size: 11px; color: black; padding: 0; } QDoubleSpinBox:focus { border-color: #0A84FF; }")
            dl.addWidget(ds)
            du = QLabel("s")
            du.setStyleSheet("QLabel { color: #999; font-size: 10px; }")
            dl.addWidget(du)
            row_layout.addWidget(delay_w)

            # ── ⑤ 排序按钮 ──
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
            btn_down.setEnabled(i < len(image_files) - 1)
            ml.addWidget(btn_up, 0, Qt.AlignVCenter)
            ml.addWidget(btn_down, 0, Qt.AlignVCenter)
            row_layout.addWidget(move_w, 0, Qt.AlignVCenter)

            btn_up.clicked.connect(lambda checked, idx=i, fp=folder_path: self._swap_steps(idx, idx - 1, fp))
            btn_down.clicked.connect(lambda checked, idx=i, fp=folder_path: self._swap_steps(idx, idx + 1, fp))

            # ── ⑥ 拖拽排序（按住卡片拖动，放置由父容器统一处理） ──
            row_widget._idx = i
            row_widget._fp = folder_path
            row_widget._drag_start_pos = None
            def _bd(w):
                def _mpe(s,e):
                    if e.button()==1: s._drag_start_pos=e.pos()
                    QWidget.mousePressEvent(s,e)
                w.mousePressEvent=_mpe.__get__(w,QWidget)
                def _mme(s,e):
                    if not(e.buttons()&1): return
                    if s._drag_start_pos is None: return
                    if (e.pos()-s._drag_start_pos).manhattanLength()<QApplication.startDragDistance(): return
                    d=QDrag(s); m=QMimeData(); m.setText(f"{s._idx},{s._fp}"); d.setMimeData(m)
                    d.setPixmap(s.grab().scaled(300,72,Qt.KeepAspectRatio,Qt.SmoothTransformation))
                    d.setHotSpot(QPoint(30,36)); d.exec_(2)
                w.mouseMoveEvent=_mme.__get__(w,QWidget)
            _bd(row_widget)

            row_layout.addStretch()
            list_layout.addWidget(row_widget)

        # ── 列表级放置处理（拖到任意子控件上也生效） ──
        _lw = list_layout.parentWidget()
        _lw.setAcceptDrops(True)
        _swap_fn = self._swap_steps
        def _l_dee(s,e):
            if e.mimeData().hasText(): e.acceptProposedAction()
        _lw.dragEnterEvent=_l_dee.__get__(_lw,QWidget)
        def _l_dme(s,e):
            if e.mimeData().hasText(): e.acceptProposedAction()
        _lw.dragMoveEvent=_l_dme.__get__(_lw,QWidget)
        def _l_de(s,e):
            if e.mimeData().hasText():
                try:
                    a,b=e.mimeData().text().split(","); a=int(a)
                    dy=e.pos().y()
                    for ri in range(list_layout.count()):
                        rw=list_layout.itemAt(ri).widget()
                        if rw and rw.y()<=dy<=rw.y()+rw.height() and ri!=a:
                            _swap_fn(a,ri,b)
                            break
                    e.acceptProposedAction()
                except: pass
        _lw.dropEvent=_l_de.__get__(_lw,QWidget)

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
        self._populate_image_rows(dialog, folder_path, list_layout)
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
                    step = index + 1
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
    
    def show_coordinate_data(self, parent_dialog, folder_path, recording_json_path):
        """显示坐标录制数据"""
        try:
            # 加载坐标数据
            recording_data = load_json_data(recording_json_path)
            if not isinstance(recording_data, list) or not recording_data:
                self.parent.show_beautiful_message('information', "提示", "该文件夹中没有坐标数据！", parent=parent_dialog)
                return
            
            # 创建坐标数据显示窗口
            coord_dialog = QDialog(parent_dialog)
            coord_dialog.setWindowTitle(f"坐标录制数据 - {os.path.basename(str(folder_path))}")
            screen_width, screen_height = get_screen_size()
            coord_dialog.resize(int(screen_width * 0.5), int(screen_height * 0.6))
            coord_dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            coord_dialog.setAttribute(Qt.WA_TranslucentBackground)
            center_window(coord_dialog)
            
            # macOS 毛玻璃容器（唯一有边框）
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
            layout = QVBoxLayout(_outer)
            layout.setContentsMargins(16, 12, 16, 16)
            layout.setSpacing(8)
            _dlg_layout.addWidget(_outer)
            
            # 关闭红色圆点（右上角）
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
            layout.addLayout(_dh)
            
            # 标题标签
            title_label = QLabel("📍 坐标录制数据")
            title_label.setStyleSheet("font-size:16px; font-weight:bold; color:#1C1C1E; padding:4px 0; background:transparent; border:none;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)

            # 对话框级别拖动
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

            # 创建表格显示坐标数据
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["步骤", "操作类型", "坐标位置", "操作"])
            table.setRowCount(len(recording_data))

            # configure_table 被 setStyleSheet 覆盖，已移除
            # 彻底清除表格所有边框（系统默认边框也不保留）
            table.setStyleSheet(
                "QTableWidget{background:#FFFFFF;border:none;border-radius:8px;gridline-color:transparent;outline:none;}"
                "QTableWidget::item{padding:4px 6px;border:none;color:#1D1D1F;}"
                "QTableWidget::item:hover{background:#F0F0F2;}"
                "QTableWidget::item:selected{background:#E8F0FE;color:#1D1D1F;}"
                "QTableWidget:focus{border:none;outline:none;}"
                "QHeaderView{border:none;}"
                "QHeaderView::section{background:#FFFFFF;color:#86868B;padding:6px 10px;border:none;font-weight:600;font-size:12px;}"
                "QTableCornerButton::section{background:#FFFFFF;border:none;}"
            )
            table.setColumnWidth(3, 70)
            table.verticalHeader().setDefaultSectionSize(60)
            table.horizontalHeader().setStretchLastSection(False)
            
            # 填充数据
            for i, record in enumerate(recording_data):
                step = record.get('step', i + 1)
                action_type = record.get('action_type', 'left_click')
                x = record.get('x', 0)
                y = record.get('y', 0)
                
                # 步骤
                step_item = QTableWidgetItem(str(step))
                step_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, 0, step_item)
                
                # 操作类型
                action_map = {
                    'left_click': 'click',
                    'right_click': 'right click',
                    'double_click': 'double click',
                    'middle_click': 'middle click'
                }
                action_text = action_map.get(action_type, action_type)
                action_item = QTableWidgetItem(action_text)
                action_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, 1, action_item)
                
                # 坐标
                coord_item = QTableWidgetItem(f"({x}, {y})")
                coord_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, 2, coord_item)
                # 删除按钮（第3列）
                _del_w = QWidget()
                _del_w.setStyleSheet("QWidget{background:transparent;}")
                _del_w.setStyleSheet("QWidget{background:transparent;}")
                _del_l = QHBoxLayout(_del_w)
                _del_l.setContentsMargins(4,0,4,0)
                _del_l.setAlignment(Qt.AlignCenter)
                _del_b = QPushButton("删除")
                _del_b.setFixedHeight(28)
                _del_b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                _del_b.setStyleSheet("QPushButton{background:transparent;color:#FF3B30;border:1px solid #FF3B30;border-radius:6px;padding:2px 8px;font-size:12px;}QPushButton:hover{background:#FF3B30;color:white;}")
                _del_b.setCursor(Qt.PointingHandCursor)
                _row_idx = i
                def _del_row_cb(checked=False, idx=_row_idx):
                    del recording_data[idx]
                    for _ii,_oo in enumerate(recording_data,1): _oo["step"]=_ii
                    save_json_data(recording_json_path, recording_data)
                    _refresh_table()
                _del_b.clicked.connect(_del_row_cb)
                _del_l.addWidget(_del_b, 0, Qt.AlignVCenter | Qt.AlignHCenter)
                table.setCellWidget(i, 3, _del_w)
                table.setRowHeight(i, 60)

            # 表格刷新函数（删除后调用）
            def _refresh_table():
                table.setRowCount(len(recording_data))
                for _i,_o in enumerate(recording_data):
                    _tm = {"left_click":"click","right_click":"right click","double_click":"double click","middle_click":"middle click"}
                    table.setItem(_i,0,QTableWidgetItem(str(_o.get("step",_i+1)))); table.item(_i,0).setTextAlignment(Qt.AlignCenter)
                    table.setItem(_i,1,QTableWidgetItem(_tm.get(_o.get("action_type"),_o.get("action_type")))); table.item(_i,1).setTextAlignment(Qt.AlignCenter)
                    table.setItem(_i,2,QTableWidgetItem("("+str(_o.get("x",0))+", "+str(_o.get("y",0))+")")); table.item(_i,2).setTextAlignment(Qt.AlignCenter)
                    # 重新添加删除按钮
                    _dww = QWidget()
                    _dww.setStyleSheet("QWidget{background:transparent;}")
                    _dww.setStyleSheet("QWidget{background:transparent;}")
                    _dll = QHBoxLayout(_dww)
                    _dll.setContentsMargins(4,0,4,0)
                    _dll.setAlignment(Qt.AlignCenter)
                    _dbb = QPushButton("删除")
                    _dbb.setFixedHeight(28)
                    _dbb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                    _dbb.setStyleSheet("QPushButton{background:transparent;color:#FF3B30;border:1px solid #FF3B30;border-radius:6px;padding:2px 8px;font-size:12px;}QPushButton:hover{background:#FF3B30;color:white;}")
                    _dbb.setCursor(Qt.PointingHandCursor)
                    _rii = _i
                    def _drr(checked=False, idx2=_rii):
                        del recording_data[idx2]
                        for _ii2,_oo2 in enumerate(recording_data,1): _oo2["step"]=_ii2
                        save_json_data(recording_json_path, recording_data)
                        _refresh_table()
                    _dbb.clicked.connect(_drr)
                    _dll.addWidget(_dbb, 0, Qt.AlignVCenter | Qt.AlignHCenter)
                    table.setCellWidget(_i, 3, _dww)
                    table.setRowHeight(_i, 60)

            # 设置列宽
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            table.setColumnWidth(3, 70)

            layout.addWidget(table)

            btn_layout = QHBoxLayout()
            add_btn = QPushButton("+ 添加操作")
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34C759;
                    color: white;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #28A745;
                }
            """)
            def _add_op():
                from PyQt5.QtGui import QPainter as _QP, QFont as _QFt, QColor as _QC
                from PyQt5.QtCore import QTimer as _QT
                # 最小化主窗口
                if self.parent and self.parent.isVisible():
                    self.parent.showMinimized()
                # 最小化坐标对话框
                coord_dialog.showMinimized()
                _ov = QDialog(coord_dialog)
                _ov.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
                _ov.setAttribute(Qt.WA_TranslucentBackground)
                _ov.setMouseTracking(True)
                _tg = QRect()
                for _s in QApplication.screens():
                    _tg = _tg.united(_s.geometry())
                _ov.setGeometry(_tg)
                def _mp(ev):
                    if ev.button() == Qt.LeftButton:
                        _screen = QApplication.primaryScreen(); _dpr = _screen.devicePixelRatio() if _screen else 1.0; _x = int(ev.globalX() * _dpr); _y = int(ev.globalY() * _dpr)
                        recording_data.append({"step":len(recording_data)+1,"action_type":"left_click","x":_x,"y":_y,"delay":0.3})
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
                        # 回车键：用鼠标当前位置作为坐标
                        _cursor = QCursor.pos()
                        _screen = QApplication.primaryScreen(); _dpr = _screen.devicePixelRatio() if _screen else 1.0
                        _x = int(_cursor.x() * _dpr); _y = int(_cursor.y() * _dpr)
                        recording_data.append({"step":len(recording_data)+1,"action_type":"left_click","x":_x,"y":_y,"delay":0.3})
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
            add_btn.clicked.connect(_add_op)
            btn_layout.addWidget(add_btn)
            btn_layout.addStretch()
            close_btn = QPushButton("关闭")
            close_btn.setStyleSheet("""QPushButton{background-color:#0A84FF;color:white;border:none;border-radius:6px;padding:10px 24px;font-size:13px;font-weight:bold;}QPushButton:hover{background-color:#006AE0;}""")
            close_btn.clicked.connect(coord_dialog.close)
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)
            parent_dialog.close()
            coord_dialog.exec_()
            
        except Exception as e:
            # print(f"显示坐标数据失败: {e}")  # [日志已禁用]
            traceback.print_exc()
            StyledMessageDialog(self, title='错误', text=f"显示坐标数据失败: {e}", msg_type='critical', buttons='ok').exec_()
    
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
                            step = index + 1
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
                    step = index + 1
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
                        step = index + 1
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
                    step = index + 1
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
                        step = index + 1
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
                    step = step_index + 1
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
                    step = index + 1
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

    def delete_folder(self, folder_path):
        try:
            from utils import get_recordings_path
            # 创建回收站目录（如果不存在）
            recordings_dir = get_recordings_path()
            trash_dir = os.path.join(recordings_dir, 'trash')
            os.makedirs(trash_dir, exist_ok=True)
            
            # 生成唯一的目标文件夹名
            folder_name = os.path.basename(folder_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            trash_folder_name = f"{folder_name}_{timestamp}"
            trash_folder_path = os.path.join(trash_dir, trash_folder_name)
            
            # 移动文件夹到回收站
            shutil.move(folder_path, trash_folder_path)
            
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
        # 获取点击位置的行和列
        row = self.table.rowAt(position.y())
        col = self.table.columnAt(position.x())
        
        # 只在文件夹名称列（第1列）显示右键菜单
        if col == 1 and row >= 0:
            # 获取文件夹路径
            item = self.table.item(row, col)
            if item:
                folder_path = item.data(Qt.UserRole)
                if folder_path and os.path.exists(folder_path):
                    # 创建右键菜单
                    menu = QMenu(self)
                    
                    # 添加删除动作
                    delete_action = QAction("删除", self)
                    delete_action.triggered.connect(lambda: self.delete_folder(folder_path))
                    menu.addAction(delete_action)
                    
                    # 在鼠标位置显示菜单
                    menu.exec_(self.table.viewport().mapToGlobal(position))

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
        instruction_label.setStyleSheet(f"font-size: {instruction_font_size}px; color: #666; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;")  # 动态字体大小
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
            key = event.key()
            modifiers = event.modifiers()

            # 忽略修饰键本身
            if key in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]:
                return

            # 获取键名
            key_name = {
                Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3", Qt.Key_F4: "F4",
                Qt.Key_F5: "F5", Qt.Key_F6: "F6", Qt.Key_F7: "F7", Qt.Key_F8: "F8",
                Qt.Key_F9: "F9", Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",
                Qt.Key_Escape: "Esc", Qt.Key_Tab: "Tab", Qt.Key_Space: "Space",
                Qt.Key_Return: "Enter", Qt.Key_Enter: "Enter", Qt.Key_Backspace: "Backspace",
                Qt.Key_Delete: "Del", Qt.Key_Insert: "Ins", Qt.Key_Home: "Home",
                Qt.Key_End: "End", Qt.Key_PageUp: "PageUp", Qt.Key_PageDown: "PageDown",
                Qt.Key_Up: "↑", Qt.Key_Down: "↓", Qt.Key_Left: "←", Qt.Key_Right: "→",
                Qt.Key_0: "0", Qt.Key_1: "1", Qt.Key_2: "2", Qt.Key_3: "3",
                Qt.Key_4: "4", Qt.Key_5: "5", Qt.Key_6: "6", Qt.Key_7: "7",
                Qt.Key_8: "8", Qt.Key_9: "9",
            }.get(key, QKeySequence(key).toString())

            if not key_name:
                return

            # 构建快捷键字符串
            parts = []
            if modifiers & Qt.ControlModifier:
                parts.append("Ctrl")
            if modifiers & Qt.ShiftModifier:
                parts.append("Shift")
            if modifiers & Qt.AltModifier:
                parts.append("Alt")

            # 添加当前键
            parts.append(key_name)

            # 检查是否已经有键按下，创建组合键
            if current_keys:
                # 获取最后一个键
                last_key = current_keys[-1]
                # 如果最后一个键不包含修饰键，则创建组合键
                if not any(mod in last_key for mod in ['Ctrl', 'Shift', 'Alt']):
                    # 检查最后一个键是否已经是组合键
                    if '+' in last_key:
                        # 从组合键中提取所有键
                        existing_keys = last_key.split('+')
                        # 添加新键
                        existing_keys.append(key_name)
                        # 限制最多3个键
                        if len(existing_keys) <= 3:
                            # 确保组合键是按字母/数字顺序排序，保持一致性
                            existing_keys.sort()
                            combined_key = "+".join(existing_keys)
                            shortcut_label.setText(combined_key)
                            current_keys.append(combined_key)
                            return
                        else:
                            # 超过3个键，不更新
                            return
                    else:
                        # 创建组合键，例如"F1+F2"
                        combined_key = f"{last_key}+{key_name}"
                        # 确保组合键是按字母/数字顺序排序，保持一致性
                        keys = [last_key, key_name]
                        keys.sort()
                        combined_key = "+".join(keys)
                        shortcut_label.setText(combined_key)
                        current_keys.append(combined_key)
                        return

            # 如果不是组合键，则正常处理
            shortcut = "+".join(parts)
            shortcut_label.setText(shortcut)
            current_keys.append(shortcut)

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
        self.replay_enabled = False  # 回放功能开关（默认关闭）
        self.shortcuts = {}
        self.shortcut_objects = []
        self.alt_press_count = 0  # ALT键按下次数
        self.alt_press_time = 0  # ALT键按下时间
        self.debug_mode = True  # 调试模式开关（控制回放和组合技的调试输出）
        
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
        # 修复：加载快捷键后立即刷新流程表格
        if hasattr(self, "manager_tab") and hasattr(self.manager_tab, "folder_table"):
            self.load_folders_to_table(self.manager_tab.folder_table)
        self.load_debug_mode_setting()
        self.is_folder_manager_open = False
        self.update_shortcuts()
        self.register_record_hotkey()
        self.register_stop_replay_hotkey()
        self.load_font_size_setting()
        if hasattr(self, 'status_label') and self.current_user:
            self.status_label.setText(f"当前用户: {self.current_user}")
        self.update_status_display()

        # ── 商业化：授权状态定时刷新 + 试用到期提醒 ────────────
        from hardware_binder import check_authorization, TrialManager

        # 确保试用已启动
        TrialManager.start_trial()

        # 每分钟刷新一次状态显示
        self._auth_timer = QTimer(self)
        self._auth_timer.timeout.connect(self.update_status_display)
        self._auth_timer.start(60_000)

        # 5 秒后检查一次试用期，如果即将到期则提醒
        QTimer.singleShot(5000, self._check_trial_warning)

    def _check_trial_warning(self):
        """检查试用期状态并提醒用户"""
        from hardware_binder import check_authorization
        auth = check_authorization()
        if auth["activated"]:
            return  # 已激活，无需提醒
        if auth["in_trial"]:
            d = auth["trial_info"]["days_remaining"]
            if d <= 3 and d > 0:
                self.show_beautiful_message(
                    'information', "试用即将到期",
                    f"您的 {d} 天试用期还剩 **{d} 天**，\n"
                    f"到期后将无法使用回放功能，\n"
                    f"请及时购买激活码！"
                )
            elif d == 0:
                self.show_beautiful_message(
                    'warning', "试用已到期",
                    "您的试用期已结束，\n"
                    "请购买激活码以继续使用全部功能。"
                )
    
    
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
        
        # 清理快捷键
        if hasattr(self, 'registered_shortcuts'):
            for hotkey_id in self.registered_shortcuts:
                try:
                    keyboard.remove_hotkey(hotkey_id)
                except:
                    pass
            self.registered_shortcuts.clear()
        
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
        
        # 对话框关闭时清理资源
        dialog.finished.connect(lambda: self._cleanup_view_dialog(dialog, grid))
        
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
            step_a = idx_a + 1
            step_b = idx_b + 1
            if idx_a >= len(recording_data) or idx_b >= len(recording_data):
                return
            recording_data[idx_a], recording_data[idx_b] = recording_data[idx_b], recording_data[idx_a]
            for i, rec in enumerate(recording_data):
                rec['step'] = i + 1
                if 'image' in rec:
                    rec['image'] = f"操作{i + 1}.png"
            save_json_data(recording_json_path, recording_data)
            step_a_old = idx_a + 1
            step_b_old = idx_b + 1
            img_a = os.path.join(folder_path, f"操作{step_a_old}.png")
            img_b = os.path.join(folder_path, f"操作{step_b_old}.png")
            img_a_tmp = os.path.join(folder_path, f"操作{step_a_old}_tmp.png")
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
            self.folder_manager._populate_image_rows(dialog, folder_path, list_layout)
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
            os.remove(img_path)
            json_path = os.path.join(folder_path, 'recording.json')
            data = load_json_data(json_path) if os.path.exists(json_path) else []
            data = [d for d in data if d.get('step') != del_step]
            for i, d in enumerate(data):
                d['step'] = i + 1
            save_json_data(json_path, data)
            for f in os.listdir(folder_path):
                if f.lower().endswith('.png') and f != fname:
                    m2 = re.search(r'操作(\d+)', f)
                    if m2 and int(m2.group(1)) > del_step:
                        new_step = int(m2.group(1)) - 1
                        new_name = re.sub(r'操作\d+', f'操作{new_step}', f)
                        old = os.path.join(folder_path, f)
                        new = os.path.join(folder_path, new_name)
                        if os.path.exists(old) and not os.path.exists(new):
                            os.rename(old, new)
            self.show_beautiful_message('information', '成功', '图片删除成功！')
            if hasattr(self, 'table') and self.table.currentRow() >= 0:
                self.view_folder_images(self.table.currentRow(), folder_path)
        except Exception as e:
            self.show_beautiful_message('critical', '错误', f"删除失败: {e}", parent=trash_table.window())

    def reorder_images(self, folder_path, old_step, new_step, dialog=None):
        """拖拽重排图片顺序"""
        imgs = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.png')]
        step_imgs = []
        for p in imgs:
            sn = self._extract_step_number(os.path.basename(p))
            if sn:
                step_imgs.append((sn, p))
        step_imgs.sort(key=lambda x: x[0])
        
        item = step_imgs.pop(old_step - 1)
        step_imgs.insert(new_step - 1, item)
        
        temp_files = []
        new_names = {}
        for i, (new_num, old_path) in enumerate(step_imgs):
            base = os.path.basename(old_path)
            new_base = re.sub(r'操作\d+', f'操作{i + 1}', base)
            new_path = os.path.join(folder_path, new_base)
            # 记录旧路径到新文件名的映射
            new_names[old_path] = new_base
            if old_path != new_path and os.path.exists(old_path):
                temp_path = os.path.join(folder_path, f'temp_{uuid.uuid4().hex[:8]}_{new_base}')
                shutil.move(old_path, temp_path)
                temp_files.append((temp_path, new_path))
        
        for temp_path, new_path in temp_files:
            if os.path.exists(temp_path):
                shutil.move(temp_path, new_path)
        
        json_path = os.path.join(folder_path, 'recording.json')
        if os.path.exists(json_path):
            data = load_json_data(json_path)
            data.sort(key=lambda x: x.get('step', 0))
            
            # 创建step到数据的映射（使用原始step作为键）
            step_to_data = {}
            for d in data:
                step = d.get('step')
                if step is not None:
                    step_to_data[step] = d
            
            # print(f"[重排] 原始数据步骤: {list(step_to_data.keys())}")  # [日志已禁用]
            # print(f"[重排] 新的图片顺序: {[sn for sn, _ in step_imgs]}")  # [日志已禁用]

            # 根据新的图片顺序重新映射数据
            new_data = []
            for i, (original_step, old_path) in enumerate(step_imgs):
                new_step = i + 1
                if original_step in step_to_data:
                    # 复制数据，避免修改原始数据
                    d = step_to_data[original_step].copy()
                    d['step'] = new_step
                    # 更新image字段为新的图片文件名
                    d['image'] = new_names.get(old_path, f'操作{new_step}.png')
                    new_data.append(d)
                    # print(f"[重排] 步骤 {original_step} -> {new_step}: {d.get('action_type', 'unknown')}")  # [日志已禁用]
                else:
                    # 如果找不到对应数据，创建一个新的
                    # print(f"[重排] 警告: 找不到步骤 {original_step} 的数据，创建默认数据")  # [日志已禁用]
                    new_data.append({'step': new_step, 'action_type': 'left_click', 'image': f'操作{new_step}.png'})
            
            save_json_data(json_path, new_data)
            # print(f"[重排] 已保存新的顺序: {[d['step'] for d in new_data]}")  # [日志已禁用]
        
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
        data = load_json_data(json_path)
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
        self.log_window.setMinimumSize(700, 500)
        self.log_window.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
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
                    self.debug_mode = config.get('debug_mode', True)
            else:
                self.debug_mode = True
        except Exception:
            self.debug_mode = True
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
        
        menu = QMenu(self)
        pin_action = menu.addAction("📌 置顶")
        
        action = menu.exec_(item_widget.mapToGlobal(pos))
        
        if action == pin_action:
            self.pin_recording_to_top(recording_name)
    
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
        
        # 执行第一个选中的流程
        self.play_recording(selected[0])
    
    def show_replay_settings(self):
        """显示回放设置对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSlider, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("回放设置")
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(280, 200)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #2C3E50;
                font-size: 18px;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #0A84FF;
                color: white;
                border-radius: 12px;
                padding: 8px 20px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #006AE0;
            }
            QPushButton:pressed {
                background-color: #004DB3;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # 速度设置
        speed_label = QLabel("回放速度: 1.0x")
        layout.addWidget(speed_label)
        
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setRange(5, 100)
        speed_slider.setValue(10)
        speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #f0f0f0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 12px;
                height: 12px;
                background: #FF453A;
                border-radius: 6px;
            }
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
            # 递增调用次数
            self._increment_usage_count(recording_name)
            
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
            # 按钮回放不改变回放状态，只执行回放操作
            
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
        try:
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
            is_coord_only = all(
                'image' not in op for op in recording_data
            )

            # 执行回放
            self.debug_print(f"[回放] 开始执行回放: {folder_path}")
            if is_coord_only:
                self.debug_print(f"[回放] 检测为坐标录制（无图像），使用 replay_coordinates_only")
                from image_recognition import replay_coordinates_only
                success_count, total_count = replay_coordinates_only(
                    recording_data=recording_data,
                    replay_interval=self.replay_interval
                )
            else:
                from image_recognition import replay_coordinate_operations
                replay_result = replay_coordinate_operations(
                    recording_data=recording_data,
                    folder_path=folder_path,
                    replay_interval=self.replay_interval,
                    consider_color=False,
                    region_center=None,
                    match_timeout=self.replay_timeout
                )
                if len(replay_result) == 3:
                    success_count, total_count, _ = replay_result
                else:
                    success_count, total_count = replay_result
            
            _pg.moveTo(_saved_x, _saved_y, duration=0.15)

            # 回放完成
            self.is_replaying = False
            self.debug_print(f"[回放] 回放完成: {success_count}/{total_count} 操作成功")
            
        except Exception as e:
            self.is_replaying = False
            self.debug_print(f"[回放] 回放失败: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_replay(self):
        """停止当前回放（完全重置状态，同时停止所有组合技）"""
        try:
            # 设置停止标志，让回放函数自行停止
            from image_recognition import set_replay_stop_flag
            set_replay_stop_flag(True)
            
            # 立即重置回放状态
            self.is_replaying = False
            self.replay_enabled = False
            
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

    def close_replay_indicator(self):
        if hasattr(self, 'replay_status_widget'):
            self.replay_status_widget.hide()
    
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

    def open_recharge_dialog(self):
        """打开充值对话框"""
        dialog = RechargeDialog(self)
        dialog.exec_()
    
    def update_status_display(self):
        """更新状态显示（显示激活/试用状态）"""
        if not hasattr(self, 'status_label'):
            return
            
        if not self.current_user:
            self.status_label.setText("未登录")
            return

        from hardware_binder import check_authorization
        auth = check_authorization()

        if auth["activated"]:
            self.status_label.setText(f"✓ 已激活 | 用户: {self.current_user}")
        elif auth["in_trial"]:
            d = auth["trial_info"]["days_remaining"]
            self.status_label.setText(f"🕐 试用剩余 {d} 天 | 用户: {self.current_user}")
        else:
            self.status_label.setText(f"✗ 未激活 | 用户: {self.current_user}")
    
    def add_recharge_record(self, amount, payment_method, service_period=None):
        """添加充值记录"""
        try:
            # 使用db_manager中的连接执行SQL
            from utils import db_manager
            db = db_manager()
            if not db:
                return False
                
            cursor = db.cursor()
            cursor.execute("INSERT INTO recharge_records (username, amount, payment_method, service_period, created_at) VALUES (?, ?, ?, ?, ?)",
                         (self.login_manager.current_user, amount, payment_method, service_period, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            return True
        except Exception as e:
            # print(f"添加充值记录失败: {e}")  # [日志已禁用]
            return False
    
    def check_license_status(self, show_dialog=True):
        """检查当前用户的许可证状态并显示在状态栏"""
        if not self.current_user:
            if hasattr(self, 'status_label'):
                self.status_label.setText("未登录")
            return True  # 移除许可证验证，总是返回True
        
        # 移除许可证验证，直接显示已激活状态
        if hasattr(self, 'status_label'):
            self.status_label.setText("已激活VIP")
        return True  # 移除许可证验证，总是返回True
    
    def get_license_info(self):
        """获取当前用户的许可证信息"""
        if not self.current_user:
            return None
            
        # 移除许可证验证，返回一个有效的许可证信息
        return {
            'valid': True,
            'days_remaining': 999,
            'expiry_date': '2099-12-31'
        }

    def check_replay_permission(self):
        """检查回放权限（硬件激活 + 试用期 + 数据库权限）"""
        try:
            # ── 1. 硬件激活/试用检查 ────────────────────────
            from hardware_binder import check_authorization
            auth = check_authorization()
            if not auth["ok"]:
                self.debug_print(f"授权检查未通过: {auth['message']}")
                return False

            # ── 2. 数据库权限检查 ────────────────────────────
            if not hasattr(self, 'current_user') or not self.current_user:
                return True

            from hybrid_db import hybrid_db_manager
            user = hybrid_db_manager.get_user(self.current_user)
            if user:
                can_replay = user.get('can_replay', True)
                if isinstance(can_replay, bool):
                    return can_replay
                return can_replay == 1
            return True
        except Exception as e:
            self.debug_print(f"检查回放权限失败: {e}")
            return True

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
            key = event.key()
            if key == Qt.Key_Control or key == Qt.Key_Shift or key == Qt.Key_Alt:
                return
            
            modifiers = []
            if event.modifiers() & Qt.ControlModifier:
                modifiers.append("ctrl")
            if event.modifiers() & Qt.ShiftModifier:
                modifiers.append("shift")
            if event.modifiers() & Qt.AltModifier:
                modifiers.append("alt")
            
            key_map = {
                Qt.Key_F1: "f1", Qt.Key_F2: "f2", Qt.Key_F3: "f3", Qt.Key_F4: "f4",
                Qt.Key_F5: "f5", Qt.Key_F6: "f6", Qt.Key_F7: "f7", Qt.Key_F8: "f8",
                Qt.Key_F9: "f9", Qt.Key_F10: "f10", Qt.Key_F11: "f11", Qt.Key_F12: "f12",
                Qt.Key_Space: "space", Qt.Key_Return: "return", Qt.Key_Tab: "tab",
                Qt.Key_Escape: "esc", Qt.Key_Backspace: "backspace", Qt.Key_Delete: "delete",
                Qt.Key_Home: "home", Qt.Key_End: "end", Qt.Key_PageUp: "pageup", Qt.Key_PageDown: "pagedown",
                Qt.Key_Up: "up", Qt.Key_Down: "down", Qt.Key_Left: "left", Qt.Key_Right: "right",
                Qt.Key_Insert: "insert",
            }
            
            if key in key_map:
                key_name = key_map[key]
            else:
                key_name = chr(key).lower() if key < 128 else ""
            
            if key_name:
                shortcut_parts = modifiers + [key_name]
                shortcut_str = "+".join(shortcut_parts)
                current_keys = shortcut_parts
                shortcut_label.setText(shortcut_str)
        
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
            def _bg():
                for path, restore_path, name in items:
                    try:
                        shutil.move(path, restore_path)
                        self.remove_from_trash_index(name)
                    except Exception:
                        pass
                QTimer.singleShot(0, lambda: self._reload_trash_table(trash_table, count_label))
                QTimer.singleShot(0, lambda: self.show_beautiful_message('information', '恢复成功', f'成功恢复 {len(items)} 个流程', parent=trash_table.window()))
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
            def _bg():
                for name, path in items:
                    try:
                        if os.path.exists(path):
                            shutil.rmtree(path)
                        self.remove_from_trash_index(name)
                    except Exception:
                        pass
                QTimer.singleShot(0, lambda: self._reload_trash_table(trash_table, count_label))
                QTimer.singleShot(0, lambda: self.show_beautiful_message('information', '删除成功', f'成功删除 {len(items)} 个流程', parent=trash_table.window()))
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
                QTimer.singleShot(0, lambda: self._reload_trash_table(trash_table, count_label))
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
        count_label.setText(f"{len(index_data)} \u9879")

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
                # print("[DEBUG] ·键被按下，准备在主线程中执行toggle_recording")  # [日志已禁用]
                QTimer.singleShot(0, self.toggle_recording)
                
            # 保存·键的hotkey_id，以便可以临时禁用和重新启用
            self.grave_hotkey_id = keyboard.add_hotkey('grave', hotkey_handler)
            # print("成功注册·键作为开始录制的快捷键")  # [日志已禁用]
        except Exception as e:
            # print(f"注册·键快捷键失败: {e}")  # [日志已禁用]
            self.grave_hotkey_id = None
    
    def register_stop_replay_hotkey(self):
        """注册F12键作为停止回放的快捷键"""
        try:
            def stop_handler():
                self.debug_print("[DEBUG] F12键被按下，准备停止当前回放")
                # 只有在回放进行中时才执行停止
                if getattr(self, 'is_replaying', False):
                    QTimer.singleShot(0, self.stop_replay)
                    self.debug_print("[回放控制] F12停止快捷键已触发")
                else:
                    self.debug_print("[回放控制] F12被按下，但没有正在进行的回放")

            # 保存F12键的hotkey_id
            self.stop_replay_hotkey_id = keyboard.add_hotkey('f12', stop_handler)
        except Exception as e:
            self.debug_print(f"注册F12停止快捷键失败: {e}")
            self.stop_replay_hotkey_id = None
    
    def temporarily_disable_grave_hotkey(self):
        """临时禁用·键的全局快捷键"""
        if hasattr(self, 'grave_hotkey_id') and self.grave_hotkey_id is not None:
            try:
                keyboard.remove_hotkey(self.grave_hotkey_id)
                # print("临时禁用·键快捷键")  # [日志已禁用]
            except Exception as e:
                # print(f"禁用·键快捷键失败: {e}")  # [日志已禁用]
                pass
    
    def reenable_grave_hotkey(self):
        """重新启用·键的全局快捷键"""
        try:
            def hotkey_handler():
                # print("[DEBUG] ·键被按下，准备在主线程中执行toggle_recording")  # [日志已禁用]
                QTimer.singleShot(0, self.toggle_recording)
            
            self.grave_hotkey_id = keyboard.add_hotkey('grave', hotkey_handler)
            # print("重新启用·键快捷键")  # [日志已禁用]
        except Exception as e:
            # print(f"重新启用·键快捷键失败: {e}")  # [日志已禁用]
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
            data = load_json_data(json_path)
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
            # 使用完整路径保存，避免重命名后配置失效
            # print(f"保存快捷键配置到: {config_path}")  # [日志已禁用]
            # print(f"快捷键配置内容: {self.shortcuts}")  # [日志已禁用]
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.shortcuts, f, indent=2, ensure_ascii=False)
            # print("快捷键配置保存成功")  # [日志已禁用]
        except Exception as e:
            # print(f"保存快捷键配置失败: {e}")  # [日志已禁用]
            pass

    def load_shortcut_config(self):
        """加载快捷键配置"""
        try:
            config_path = os.path.join(self.user_data_dir, f'shortcuts_{self.current_user}.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.shortcuts = json.load(f)
                    # print(f"快捷键配置加载成功: {self.shortcuts}")  # [日志已禁用]
            else:
                self.shortcuts = {}
        except Exception:
            self.shortcuts = {}

    def update_shortcuts(self):
        """更新快捷键 - 移除旧的并添加新的"""
        try:
            import keyboard
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
            
            # 添加新的快捷键
            for shortcut_str, folder_paths in shortcut_groups.items():
                try:
                    def make_handler(paths=folder_paths.copy()):
                        def handler():
                            try:
                                # 快捷键回放需要检查回放状态
                                if not self.replay_enabled:
                                    self.debug_print(f"快捷键回放被忽略，当前回放状态为: {self.replay_enabled}")
                                    return
                                # 添加调试日志，确认进入回放分支
                                self.debug_print(f"[快捷键] 触发回放，快捷键: {shortcut_str}, 文件夹列表: {paths}, replay_enabled: {self.replay_enabled}")
                                # 直接从当前线程调用，不使用 QTimer.singleShot
                                # 因为在键盘钩子回调线程中调用 QTimer.singleShot 可能不生效
                                for path in paths:
                                    self.replay_folder_operations(path)
                            except Exception as e:
                                self.debug_print(f"[快捷键] 处理快捷键回放时出错: {e}")
                                import traceback
                                traceback.print_exc()
                        return handler
                    
                    hotkey_id = keyboard.add_hotkey(shortcut_str, make_handler())
                    self.shortcut_objects.append(hotkey_id)
                except Exception as e:
                    self.debug_print(f"[快捷键] 注册快捷键失败 {shortcut_str}: {e}")
                    pass
        except Exception as e:
            self.debug_print(f"[快捷键] 更新快捷键失败: {e}")
            pass



class ComboSkillRunner:
    """组合技执行器 - 在独立线程中运行组合技的各个流程（纯Python回调）"""

    def __init__(self, skill_data, parent=None):
        self.skill_data = skill_data
        self.skill_id = ""
        self.running = False
        self.monitor_mode = False
        self.monitor_target_runner = None
        self._exec_thread = None
        self._current_flow_index = 0
        self._total_flows = len(skill_data.get("flows", []))
        self._loop_count = skill_data.get("loop_count", 1)
        self._current_loop = 1
        self._main_app = parent
        self.interrupt_event = threading.Event()  # 用于唤醒 _wait_interruptible 的中断事件
        # 回调函数（线程安全，由主线程设置）
        self._on_finished = None
        self._on_log = None
        self._on_step = None

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
            total_loops = max(1, self._loop_count)
            _t0 = _time.time()
            from image_recognition import find_image_with_timeout
            _t1 = _time.time()
            try:
                if self._main_app is not None:
                    self._main_app.append_log(f" ║  ⏳ find_image_with_timeout 导入: {_t1-_t0:.3f}s")
                    if flows:
                        self._main_app.append_log(f" ║  📋 流程0数据: {str(flows[0])[:200]}")
            except Exception:
                pass

            for loop in range(1, total_loops + 1):
                if not self.running:
                    break
                self._current_loop = loop
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
                            loc = find_image_with_timeout(condition_image, confidence=0.8, timeout=0.4, consider_color=False, stop_check=lambda: not self.running)
                            condition_met = loc is not None
                            _cond_elapsed = _time.time() - _cond_start
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  🔍 流程{flow_index+1} image_found: {_cond_elapsed:.3f}s {'✅ 满足' if condition_met else '❌ 不满足'}")
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
                            loc = find_image_with_timeout(condition_image, confidence=0.8, timeout=0.01, consider_color=False, stop_check=lambda: not self.running)
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
                            _wf_log(f"⏳ 开始等待出现，timeout={wait_timeout}s")
                            condition_met = False
                            _wait_deadline = _time.time() + wait_timeout
                            _poll_cnt = 0
                            _disappeared = False
                            # wait_for_image 使用更高置信度(0.9)和短超时(0.3s)以减少CPU占用和误报
                            _wf_confidence = 0.9
                            _wf_timeout = 0.3
                            while self.running and _time.time() < _wait_deadline:
                                _poll_cnt += 1
                                loc = find_image_with_timeout(condition_image, confidence=_wf_confidence, timeout=_wf_timeout, consider_color=False, stop_check=lambda: not self.running, strict=True)
                                if not _disappeared:
                                    if loc is None:
                                        _disappeared = True
                                        _wf_log(f"👁 图片已消失，开始等待出现")
                                    else:
                                        if _poll_cnt % 5 == 0:
                                            _wf_log(f"⏳ 等待图片消失中(已轮询{_poll_cnt}次)")
                                    _time.sleep(0.3)
                                    continue
                                if loc is not None:
                                    # 连续确认：再检测2次，全部命中才算真正出现（避免单帧闪烁误报）
                                    _confirm = 1
                                    for _ci in range(2):
                                        _time.sleep(0.2)
                                        _cloc = find_image_with_timeout(condition_image, confidence=_wf_confidence, timeout=_wf_timeout, consider_color=False, stop_check=lambda: not self.running, strict=True)
                                        if _cloc is not None:
                                            _confirm += 1
                                    if _confirm >= 3:
                                        condition_met = True
                                        _wf_log(f"✅ 确认图片出现！第{_poll_cnt}次检测(3中{_confirm})")
                                        break
                                    else:
                                        _wf_log(f"⚠ 第{_poll_cnt}次检测误报({_confirm}/3确认失败)，继续等待")
                                if _poll_cnt % 5 == 0:
                                    _wf_log(f"⏳ 等待图片出现中(已轮询{_poll_cnt}次，剩余{max(0,_wait_deadline-_time.time()):.1f}s)")
                                _time.sleep(0.3)
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
                                break
                            flow_index = target
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  ➡️ 跳转到流程 {target+1}")
                            except Exception:
                                break
                            self._wait_interruptible(0.01)
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
                        except Exception:
                            break
                        if not _action_ok:
                            self._consecutive_failures += 1
                            if self._consecutive_failures >= 3:
                                try:
                                    if self._main_app is not None:
                                        self._main_app.append_log(f" ║  ⛔ 连续 {self._consecutive_failures} 次执行失败，停止组合技")
                                        self._main_app.append_log(f"╚═{'═'*40}")
                                except Exception:
                                    break
                                break
                        else:
                            self._consecutive_failures = 0
                        # 录制回放中图片匹配失败 → 跳过该流程，继续执行下一个
                        if _img_fail_count > 0 and condition not in ("wait_for_image", "image_not_found"):
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  ⛔ 录制回放中图片匹配失败 {_img_fail_count} 次，立即停止组合技")
                                    self._main_app.append_log(f"╚═{'═'*40}")
                            except Exception:
                                break
                            self.running = False
                            break
                        elif _img_fail_count > 0:
                            try:
                                if self._main_app is not None:
                                    self._main_app.append_log(f" ║  ⚠️ 录制回放中图片匹配失败 {_img_fail_count} 次，但条件为{condition}，继续执行")
                            except Exception:
                                break

                    try:
                        if self._main_app is not None:
                            self._main_app.append_log(f"╚═{'═'*40}")
                    except Exception:
                        pass

                    if self.running:
                        self._wait_interruptible(0.3)
                    flow_index += 1

                _loop_elapsed = _time.time() - _loop_start
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(f" ║  ⏱️ 第{loop}轮循环完成")
                except Exception:
                    pass
                self.reset()

            _run_elapsed = _time.time() - _run_start
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

    def _execute_action(self, action):
        import time as _time
        if not action or action == "end":
            return True, 0
        try:
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

            has_images = any(op.get("image", "") for op in recording_data)
            try:
                if self._main_app is not None:
                    self._main_app.append_log(f" ║  🖼️ 动作 '{action}' 含图片={has_images}, 步骤数={len(recording_data)}")
            except Exception:
                pass

            from image_recognition import replay_coordinate_operations, replay_coordinates_only

            if has_images:
                _t_replay0 = _time.time()
                replay_result = replay_coordinate_operations(
                    recording_data, folder_path,
                    replay_interval=0.1, consider_color=False,
                    match_timeout=3.0,
                    stop_check=lambda: not self.running,
                    skip_cache_clear=True
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
                        self._main_app.append_log(f" ║  ▶ replay_coordinate_operations: {_t_replay1-_t_replay0:.3f}s 成功={ok}/{total} 图片匹配失败={img_fail_count}")
                except Exception:
                    pass
            else:
                _t_replay0 = _time.time()
                ok, total = replay_coordinates_only(
                    recording_data, replay_interval=0.2,
                    stop_check=lambda: not self.running
                )
                img_fail_count = 0
                _t_replay1 = _time.time()
                try:
                    if self._main_app is not None:
                        self._main_app.append_log(f" ║  ▶ replay_coordinates_only: {_t_replay1-_t_replay0:.3f}s 成功={ok}/{total}")
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
        app_data_dir = os.path.join(os.path.expanduser('~'), 'PC-action', 'data')
        os.makedirs(app_data_dir, exist_ok=True)
        return os.path.join(app_data_dir, 'combo_skills.json')
    
    def load_combo_skills(self):
        try:
            path = self.get_combo_skills_path()
            if os.path.exists(path):
                from utils import load_json_data
                self.combo_skills = load_json_data(path)
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
        
def start_app():
    """启动应用程序"""
    # 设置临时工作目录
    import tempfile
    temp_dir = tempfile.gettempdir()
    os.chdir(temp_dir)

    app = QApplication(sys.argv)
    
    from PyQt5.QtGui import QFont
    default_font = QFont()
    default_font.setFamily("Microsoft YaHei")
    default_font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
    app.setFont(default_font)
    
    from styles import generate_dynamic_styles, get_screen_size
    screen_width, screen_height = get_screen_size()
    app.setStyleSheet(generate_dynamic_styles(screen_width, screen_height))

    # ── 商业化：EULA 许可协议 ────────────────────────────────
    from hardware_binder import EULAManager, EULA_TEXT
    if not EULAManager.is_accepted():
        from PyQt5.QtWidgets import QMessageBox
        eula_msg = QMessageBox()
        eula_msg.setWindowTitle("最终用户许可协议")
        eula_msg.setText(EULA_TEXT)
        eula_msg.setInformativeText("您必须同意上述条款才能使用本软件。")
        eula_msg.setIcon(QMessageBox.Information)
        agree_btn = eula_msg.addButton("同意", QMessageBox.YesRole)
        reject_btn = eula_msg.addButton("拒绝", QMessageBox.NoRole)
        eula_msg.setDefaultButton(agree_btn)
        eula_msg.exec_()
        if eula_msg.clickedButton() == reject_btn:
            EULAManager.reject()
            sys.exit(0)
        else:
            EULAManager.accept()

    # ── 商业化：启动试用 ─────────────────────────────────────
    from hardware_binder import TrialManager, HardwareBinder
    TrialManager.start_trial()
    # ───────────────────────────────────────────────────────────

    from login_manager import LoginManager
    login_manager = LoginManager()
    from login_ui import LoginDialog
    login_dialog = LoginDialog(login_manager)
    login_dialog.show()
    login_dialog.raise_()
    login_dialog.activateWindow()
    
    login_dialog.finished.connect(lambda result: handle_login_result(result, login_dialog, login_manager, app))
    
    def handle_login_result(result, dialog, manager, app):
        if result == dialog.Accepted:
            # ── 商业化：登录后检查激活状态 ────────────────────────
            from hardware_binder import check_authorization, HardwareBinder
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

            auth = check_authorization()
            if not auth["ok"]:
                # 试用过期 + 未激活，弹出激活对话框
                while True:
                    act = QDialog()
                    act.setWindowTitle("激活软件")
                    act.setFixedSize(420, 240)
                    act.setModal(True)
                    lay = QVBoxLayout(act)
                    lay.setSpacing(12)

                    auth = check_authorization()
                    tip = QLabel(
                        f"⏰ 试用已结束\n请购买激活码激活软件："
                        if auth["trial_info"]["expired"]
                        else f"🎯 试用剩余 {auth['trial_info']['days_remaining']} 天\n输入激活码解锁全部功能："
                    )
                    tip.setWordWrap(True)
                    lay.addWidget(tip)

                    inp = QLineEdit()
                    inp.setPlaceholderText("请输入激活码")
                    lay.addWidget(inp)

                    bl = QHBoxLayout()
                    act_btn = QPushButton("激活")
                    skip_btn = QPushButton("继续试用" if auth["in_trial"] else "退出软件")
                    if not auth["in_trial"]:
                        skip_btn.setStyleSheet("color: red;")
                    bl.addWidget(act_btn)
                    bl.addWidget(skip_btn)
                    lay.addLayout(bl)

                    result_code = {"key": None}

                    def _on_activate():
                        k = inp.text().strip()
                        if not k:
                            QMessageBox.warning(act, "提示", "请输入激活码")
                            return
                        ok, msg = HardwareBinder.verify_key(k)
                        if ok:
                            HardwareBinder.save_activation(k)
                            QMessageBox.information(act, "激活成功", msg)
                            result_code["key"] = k
                            act.accept()
                        else:
                            QMessageBox.critical(act, "激活失败", msg)

                    def _on_skip():
                        if auth["in_trial"]:
                            act.reject()
                        else:
                            app.quit()

                    act_btn.clicked.connect(_on_activate)
                    skip_btn.clicked.connect(_on_skip)
                    act.exec_()

                    if result_code["key"] is not None:
                        break
                    if auth["in_trial"]:
                        break
                    # 过期且未激活 -> 继续弹
            # ─────────────────────────────────────────────────────

            if not hasattr(handle_login_result, 'main_window_created'):
                main_window = AutoRecorderApp(username=dialog.current_user, login_manager=manager)
                handle_login_result.main_window = main_window
                handle_login_result.main_window_created = True
        else:
            app.quit()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_app()