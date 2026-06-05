"""
文件: admin_manager.py
用途: 提供管理员功能，包括用户管理、账户注销、权限控制等
"""

import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QPushButton, 
                           QMessageBox, QLabel, QDialog, QLineEdit, 
                           QFormLayout, QCheckBox, QHeaderView, QApplication, QMenu, QAction, QTabWidget, QComboBox, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from utils import get_screen_size, apply_styles_to_dialog, get_common_dialog_style, hash_password, STYLES_AVAILABLE, create_styled_button
try:
    from supabase_db import get_supabase_manager
    # 延迟初始化，避免启动时立即连接数据库
    # supabase_manager = get_supabase_manager()
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("警告: Supabase模块未安装，将使用本地数据库")

# 尝试导入混合数据库管理器
try:
    from hybrid_db import hybrid_db_manager
    HYBRID_DB_AVAILABLE = True
except ImportError:
    HYBRID_DB_AVAILABLE = False
    print("警告: 混合数据库模块未找到")

try:
    from database_helper import DatabaseHelper
    DB_HELPER_AVAILABLE = True
except ImportError:
    DB_HELPER_AVAILABLE = False
    print("警告: 数据库助手模块未找到")

# 尝试导入样式模块
try:
    from styles import generate_dynamic_styles, apply_dialog_style
    ADMIN_STYLES_AVAILABLE = True
except ImportError:
    ADMIN_STYLES_AVAILABLE = False
    print("警告: 样式模块未找到，将使用默认样式")

class LoadUsersThread(QThread):
    """异步加载用户数据的线程"""
    data_loaded = pyqtSignal(dict)  # 改为发送分页数据
    error_occurred = pyqtSignal(str)  # 错误发生信号
    
    def __init__(self, db_manager, page=1, page_size=50):
        super().__init__()
        self.db_manager = db_manager
        self.page = page
        self.page_size = page_size
    
    def run(self):
        """执行数据加载"""
        try:
            # 直接调用db_manager，不再做额外检查
            result = self.db_manager.get_users_paginated(self.page, self.page_size)
            self.data_loaded.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class AdminManager(QMainWindow):
    def __init__(self, login_manager=None):
        super().__init__()
        self.login_manager = login_manager
        
        # 初始化数据库管理器，优先使用混合数据库管理器
        self.db_manager = None
        print(f"调试: HYBRID_DB_AVAILABLE = {HYBRID_DB_AVAILABLE}")
        if HYBRID_DB_AVAILABLE:
            self.db_manager = hybrid_db_manager
            print("使用混合数据库管理器")
            print(f"调试: hybrid_db_manager = {hybrid_db_manager}")
        elif DB_HELPER_AVAILABLE:
            from database_helper import db_helper
            self.db_manager = db_helper
            print("使用数据库助手")
        elif SUPABASE_AVAILABLE:
            self.db_manager = supabase_manager
            print("使用Supabase数据库")
        else:
            print("警告: 没有可用的数据库管理器")
            
        # 为了保持兼容性，将db_manager赋值给db_helper
        self.db_helper = self.db_manager
        print(f"调试: self.db_manager = {self.db_manager}")
        print(f"调试: self.db_helper = {self.db_helper}")
        print(f"调试: hasattr(self, 'db_helper') = {hasattr(self, 'db_helper')}")
        
        # 设置全局字体为微软雅黑
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        default_font = QFont()
        default_font.setFamily("Microsoft YaHei")
        app.setFont(default_font)
        
        self.setWindowTitle("管理员控制台")
        
        # 设置窗口尺寸，确保所有控件可见
        screen_width, screen_height = get_screen_size()
        width = int(screen_width * 0.7)  # 窗口宽度为屏幕的70%
        height = int(screen_height * 0.8)  # 窗口高度为屏幕的80%
        self.resize(width, height)  # 使用动态尺寸
        
        # 设置窗口最小和最大宽度，防止用户调整窗口大小
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)
        
        self.center_window()
        
        # 分页相关属性
        self.current_page = 1
        self.page_size = 20  # 减少默认页大小，提升首屏加载速度
        self.total_pages = 1
        self.total_count = 0
        
        self.init_ui()
        self.setup_loading_indicator()
        # 延迟异步加载，避免阻塞UI初始化
        QTimer.singleShot(100, lambda: self.load_users_async())
        
    def center_window(self):
        """居中显示窗口，确保菜单栏可见"""
        screen = QApplication.primaryScreen().availableGeometry()
        window = self.frameGeometry()
        window.moveCenter(screen.center())
        # 确保窗口顶部不超出屏幕可用区域，留出菜单栏空间
        y = max(50, window.topLeft().y())  # 至少留出50像素顶部边距
        self.move(window.topLeft().x(), y)
        
    def keyPressEvent(self, event):
        """处理键盘事件，实现ESC键退出功能"""
        if event.key() == Qt.Key_Escape:
            # 检查是否有活动的对话框
            active_dialogs = [d for d in QApplication.topLevelWidgets() 
                             if isinstance(d, QDialog) and d.isVisible()]
            
            if active_dialogs:
                # 如果有活动的对话框，关闭最顶层的对话框
                active_dialogs[-1].reject()
            else:
                # 如果没有活动的对话框，关闭管理员控制台
                self.close()
        else:
            # 其他按键事件交给父类处理
            super().keyPressEvent(event)
        
    def format_datetime(self, datetime_str):
        """统一的时间格式化函数"""
        if not datetime_str:
            return "无"
            
        try:
            # 处理各种时间格式
            if isinstance(datetime_str, str):
                # 处理ISO格式（带T）
                formatted_time = datetime_str.replace('T', ' ')
                # 处理毫秒部分
                if '.' in formatted_time:
                    formatted_time = formatted_time.split('.')[0]
                # 处理空字符串或无效字符串
                if formatted_time.strip() == "" or formatted_time.strip() == "null" or formatted_time.strip() == "None":
                    return "无"
                return formatted_time
            # 处理其他类型
            return str(datetime_str)
        except Exception as e:
            print(f"时间格式化失败: {e}")
            return str(datetime_str) if datetime_str else "无"
    
    def show_message_box(self, msg_type, title, text, buttons=None, default_button=None):
        """
        显示支持ESC键的消息框
        msg_type: 'information', 'warning', 'critical', 'question'
        title: 消息框标题
        text: 消息框内容
        buttons: 按钮组合，默认为QMessageBox.Ok
        default_button: 默认按钮
        """
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        
        # 设置消息框类型
        if msg_type == 'information':
            msg_box.setIcon(QMessageBox.Information)
        elif msg_type == 'warning':
            msg_box.setIcon(QMessageBox.Warning)
        elif msg_type == 'critical':
            msg_box.setIcon(QMessageBox.Critical)
        elif msg_type == 'question':
            msg_box.setIcon(QMessageBox.Question)
        
        # 设置按钮
        if buttons is None:
            if msg_type == 'question':
                buttons = QMessageBox.Yes | QMessageBox.No
                default_button = QMessageBox.No
            else:
                buttons = QMessageBox.Ok
                default_button = QMessageBox.Ok
        
        msg_box.setStandardButtons(buttons)
        if default_button:
            msg_box.setDefaultButton(default_button)
        
        # ESC键处理
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                if msg_type == 'question':
                    msg_box.done(QMessageBox.No)
                else:
                    msg_box.reject()
            else:
                super(QMessageBox, msg_box).keyPressEvent(event)
        
        msg_box.keyPressEvent = keyPressEvent
        return msg_box.exec_()
    
    def setup_loading_indicator(self):
        """设置加载指示器"""
        # 创建加载指示器标签
        self.loading_label = QLabel("正在加载用户数据，请稍候...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        # 按屏幕比例设置字体大小
        screen_width, screen_height = get_screen_size()
        loading_font_size = int(screen_height * 0.018)  # 屏幕高度的1.8%
        self.loading_label.setStyleSheet(f"""
            QLabel {{
                color: #22c55e;
                font-size: {loading_font_size}px;
                font-weight: bold;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }}
        """)
    
    def load_users_async(self, page=1, page_size=50):
        """异步加载用户数据"""
        # 创建并启动加载线程
        self.load_thread = LoadUsersThread(self.db_manager, page, page_size)
        self.load_thread.data_loaded.connect(self.on_users_loaded)
        self.load_thread.error_occurred.connect(self.on_load_error)
        self.load_thread.start()
    
    def on_users_loaded(self, pagination_result):
        """用户数据加载完成后的处理"""
        try:
            # 隐藏加载指示器，显示用户表格
            self.loading_label.hide()
            self.user_table.show()
            
            # 填充用户数据到表格
            users_data = pagination_result.get('data', [])
            self.populate_user_table(users_data)
            
            # 更新分页信息
            self.current_page = pagination_result.get('page', 1)
            self.total_pages = pagination_result.get('total_pages', 1)
            self.total_count = pagination_result.get('count', 0)
            
            # 更新分页控件
            self.update_pagination_controls()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"填充用户数据失败: {str(e)}")
    
    def update_pagination_controls(self):
        """更新分页控件状态"""
        # 更新分页信息标签
        if hasattr(self, 'pagination_info'):
            start_record = (self.current_page - 1) * self.page_size + 1
            end_record = min(self.current_page * self.page_size, self.total_count)
            self.pagination_info.setText(f"显示第 {start_record}-{end_record} 条，共 {self.total_count} 条记录")
        
        # 更新页码标签
        if hasattr(self, 'page_label'):
            self.page_label.setText(f"第 {self.current_page} 页，共 {self.total_pages} 页")
        
        # 更新按钮状态
        if hasattr(self, 'first_page_btn'):
            self.first_page_btn.setEnabled(self.current_page > 1)
        
        if hasattr(self, 'prev_page_btn'):
            self.prev_page_btn.setEnabled(self.current_page > 1)
        
        if hasattr(self, 'next_page_btn'):
            self.next_page_btn.setEnabled(self.current_page < self.total_pages)
        
        if hasattr(self, 'last_page_btn'):
            self.last_page_btn.setEnabled(self.current_page < self.total_pages)
    
    def on_load_error(self, error_message):
        """用户数据加载失败的处理"""
        self.loading_label.setText(f"加载用户数据失败: {error_message}")
        # 按屏幕比例设置字体大小
        screen_width, screen_height = get_screen_size()
        error_font_size = int(screen_height * 0.018)  # 屏幕高度的1.8%
        self.loading_label.setStyleSheet(f"""
            QLabel {{
                color: #e74c3c;
                font-size: {error_font_size}px;
                font-weight: bold;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }}
        """)
        
        # 创建重试按钮
        retry_button = QPushButton("重试")
        retry_button.setFixedSize(80, 30)
        retry_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        retry_button.clicked.connect(self.load_users_async)
        
        # 将重试按钮显示在加载标签的下方
        try:
            # 尝试获取用户标签页的布局并添加重试按钮
            if hasattr(self, 'tabs') and self.tabs.widget(0) is not None:
                user_tab = self.tabs.widget(0)
                if user_tab.layout() is not None:
                    user_tab.layout().addWidget(retry_button)
        except Exception as e:
            print(f"添加重试按钮失败: {e}")
        
        # 添加网络连接提示
        try:
            network_info = QLabel("\n\n可能的原因:\n1. 网络连接问题\n2. Supabase配置错误\n3. 数据库服务不可用")
            network_info.setStyleSheet(f"""
                QLabel {{
                    color: #666;
                    font-size: {error_font_size - 2}px;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
            """)
            if hasattr(self, 'tabs') and self.tabs.widget(0) is not None:
                user_tab = self.tabs.widget(0)
                if user_tab.layout() is not None:
                    user_tab.layout().addWidget(network_info)
        except Exception as e:
            print(f"添加网络提示失败: {e}")
    
    def populate_user_table(self, users_data):
        """填充用户数据到表格 - 优化版本"""
        self.user_table.setRowCount(len(users_data))
        self.user_table.setSortingEnabled(False)  # 禁用排序提升性能
        
        # 批量处理，避免频繁的UI更新
        for row, user in enumerate(users_data):
            # 直接使用QCheckBox，但通过样式表将其设置为圆形
            checkbox = QCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox {
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    border: none;
                    alignment: center;
                }
                QCheckBox::indicator {
                    width: 24px !important;
                    height: 24px !important;
                    border-radius: 12px !important;
                    background: white !important;
                    border: 2px solid #ccc !important;
                }
                QCheckBox::indicator:checked {
                    background-color: #27AE60 !important;
                    border: 2px solid #27AE60 !important;
                    image: none !important;
                }
                QCheckBox::indicator:hover {
                    border-color: #27AE60 !important;
                }
            """)
            
            checkbox.stateChanged.connect(self.on_checkbox_state_changed)
            
            # 创建容器和布局，实现居中对齐
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(checkbox)
            
            # 添加到表格
            self.user_table.setCellWidget(row, 0, container)
            
            # 批量设置单元格数据
            cells_data = [
                (1, str(user.get('id', row + 1))),  # ID
                (2, user.get('username', '')),      # 用户名
                (3, user.get('email', '')),         # 邮箱
                (4, self.format_datetime(user.get('created_at', ''))),  # 注册时间
                (5, "是" if user.get('is_admin', False) else "否"),      # 管理员
                (6, "启用" if user.get('is_active', True) else "禁用"),  # 状态
                (7, "是" if user.get('is_vip', False) else "否"),        # VIP状态
                (8, self.format_datetime(user.get('vip_end_date', '')) or "非VIP"),  # VIP到期时间
                (9, "是" if user.get('can_replay', True) else "否")       # 回放权限
            ]
            
            for col, text in cells_data:
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.user_table.setItem(row, col, item)
            
            # 移除setUserData，QTableWidget没有这个方法
        
        self.user_table.setSortingEnabled(True)  # 重新启用排序
        
    def init_ui(self):
        """初始化管理员界面"""
        # 获取屏幕尺寸
        screen_width, screen_height = get_screen_size()
        
        # 创建主滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建中央部件
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        layout = QVBoxLayout()
        layout.setSpacing(0)  # 设置布局间距为0
        layout.setContentsMargins(0, 0, 0, 0)  # 设置边距为0
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 用户管理页面
        user_tab = QWidget()
        user_layout = QVBoxLayout(user_tab)
        user_layout.setContentsMargins(0, 0, 0, 0)  # 确保用户管理页面布局没有边距
        user_layout.setSpacing(0)  # 确保用户管理页面布局没有间距
        
        # 用户表格 - 简化配置
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(10)  # 增加一列用于选择指示器
        self.user_table.setHorizontalHeaderLabels(["选择", "ID", "用户名", "邮箱", "注册时间", "管理员", "状态", "VIP状态", "VIP到期时间", "回放权限"])
        
        # 设置列宽策略 - 确保注册时间列有足够宽度
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # 先根据内容调整
        self.user_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # 邮箱列自适应拉伸
        self.user_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # 注册时间列自适应拉伸
        # 增大选择列宽度，确保圆形复选框完整显示
        self.user_table.setColumnWidth(0, 50)
        
        # 隐藏行号，使用自定义选择列
        self.user_table.verticalHeader().setVisible(False)
        
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.user_table.verticalHeader().setDefaultSectionSize(30)  # 固定行高
        # 移除表格最大高度限制，让表格根据内容自适应高度
        
        # 应用表格样式 - 与FolderManager保持一致
        from styles import get_table_style
        
        # 自定义选择列样式
        custom_style = """
            /* 隐藏默认行号列的背景色 */
            QTableWidget::verticalHeader {
                background: transparent;
            }
            
            /* 隐藏单元格焦点矩形和选中状态 */
            QTableWidget::item:focus {
                outline: none;
                selection-background-color: transparent;
                selection-color: #212529;
            }
            
            /* 隐藏表格焦点 */
            QTableWidget:focus {
                outline: none;
            }
            
            /* 禁用单元格选中效果 */
            QTableWidget::item:selected {
                background: transparent;
                color: #212529;
            }
            
            /* 禁用行选中效果 */
            QTableWidget::item:selected:!active {
                background: transparent;
                color: #212529;
            }
        """
        
        self.user_table.setStyleSheet(get_table_style() + custom_style)
        
        # 移除之前设置的布局边距
        user_layout.setContentsMargins(0, 0, 0, 0)
        
        # 设置上下文菜单策略
        self.user_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.user_table.customContextMenuRequested.connect(self.show_user_context_menu)
        
        # 添加单元格点击事件，实现点击行时自动选中复选框
        self.user_table.cellClicked.connect(self.on_cell_clicked)
        
        # 设置表格选择模式为整行选择
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 创建上下文菜单
        self.user_context_menu = QMenu(self)
        
        # 添加菜单项
        self.delete_user_action = QAction("删除用户", self)
        self.toggle_active_action = QAction("禁用用户", self)
        self.toggle_admin_action = QAction("设为管理员", self)
        self.toggle_replay_action = QAction("开启回放", self)
        
        # 连接菜单项到槽函数
        self.delete_user_action.triggered.connect(self.delete_user)
        self.toggle_active_action.triggered.connect(self.toggle_user_active)
        self.toggle_admin_action.triggered.connect(self.toggle_user_admin)
        self.toggle_replay_action.triggered.connect(self.toggle_user_replay)
        
        # 添加菜单项到菜单
        self.user_context_menu.addAction(self.delete_user_action)
        self.user_context_menu.addSeparator()
        self.user_context_menu.addAction(self.toggle_active_action)
        self.user_context_menu.addSeparator()
        self.user_context_menu.addAction(self.toggle_admin_action)
        self.user_context_menu.addSeparator()
        self.user_context_menu.addAction(self.toggle_replay_action)
        
        user_layout.addWidget(self.user_table)
        
        # 分页控件 - 简化布局
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(5)  # 减少控件间距
        pagination_layout.setContentsMargins(0, 5, 0, 5)  # 减少上下边距
        
        # 分页信息标签
        # 按屏幕比例设置字体大小
        screen = QApplication.primaryScreen().geometry()
        pagination_font_size = int(screen.height() * 0.015)  # 屏幕高度的1.5%
        
        self.pagination_info = QLabel("显示第 0-0 条，共 0 条记录")
        self.pagination_info.setStyleSheet(f"color: #666; font-size: {pagination_font_size}px;")
        pagination_layout.addWidget(self.pagination_info)
        
        # 弹性空间
        pagination_layout.addStretch()
        
        # 分页按钮 - 使用create_styled_button直接创建
        self.first_page_btn = QPushButton("首页")
        self.first_page_btn.setFixedSize(60, 30)
        self.first_page_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
            QPushButton:disabled {
                background-color: #007AFF;
                color: #888888;
            }
        """)
        self.first_page_btn.clicked.connect(self.go_to_first_page)
        self.first_page_btn.setEnabled(False)
        pagination_layout.addWidget(self.first_page_btn)
        
        self.prev_page_btn = QPushButton("上一页")
        self.prev_page_btn.setFixedSize(70, 30)
        self.prev_page_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
            QPushButton:disabled {
                background-color: #007AFF;
                color: #888888;
            }
        """)
        self.prev_page_btn.clicked.connect(self.go_to_prev_page)
        self.prev_page_btn.setEnabled(False)
        pagination_layout.addWidget(self.prev_page_btn)
        
        # 当前页码和总页数
        # 按屏幕比例设置字体大小
        screen = QApplication.primaryScreen().geometry()
        page_font_size = int(screen.height() * 0.015)  # 屏幕高度的1.5%
        
        self.page_label = QLabel("第 1 页，共 1 页")
        self.page_label.setStyleSheet(f"color: #333; font-size: {page_font_size}px; margin: 0 10px;")
        pagination_layout.addWidget(self.page_label)
        
        self.next_page_btn = QPushButton("下一页")
        self.next_page_btn.setFixedSize(70, 30)
        self.next_page_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
            QPushButton:disabled {
                background-color: #007AFF;
                color: #888888;
            }
        """)
        self.next_page_btn.clicked.connect(self.go_to_next_page)
        self.next_page_btn.setEnabled(False)
        pagination_layout.addWidget(self.next_page_btn)
        
        self.last_page_btn = QPushButton("末页")
        self.last_page_btn.setFixedSize(60, 30)
        self.last_page_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
            QPushButton:disabled {
                background-color: #007AFF;
                color: #888888;
            }
        """)
        self.last_page_btn.clicked.connect(self.go_to_last_page)
        self.last_page_btn.setEnabled(False)
        pagination_layout.addWidget(self.last_page_btn)
        
        # 每页显示数量选择
        pagination_layout.addWidget(QLabel("每页显示:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["20", "50", "100", "200"])
        self.page_size_combo.setCurrentText(str(self.page_size))  # 使用初始化的页面大小
        self.page_size_combo.currentTextChanged.connect(self.on_page_size_changed)
        pagination_layout.addWidget(self.page_size_combo)
        
        user_layout.addLayout(pagination_layout)
        
        # 用户管理按钮 - 优化布局
        user_buttons = QHBoxLayout()
        user_buttons.setSpacing(5)  # 减少按钮间距，使布局更紧凑
        user_buttons.setContentsMargins(0, 5, 0, 5)  # 减少上下边距
        user_buttons.addStretch()  # 添加弹性空间，让按钮居中显示
        
        # 为所有按钮设置一个合适的最小宽度，确保文本完整显示
        min_button_width = 80  # 减小按钮最小宽度
        
        # 全选/取消全选按钮 - 使用现代化设计
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setFixedSize(min_button_width, 32)
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.select_all_btn.clicked.connect(self.toggle_select_all)
        user_buttons.addWidget(self.select_all_btn)
        
        # 批量操作按钮
        self.batch_delete_btn = QPushButton("批量删除")
        self.batch_delete_btn.setFixedSize(min_button_width, 32)
        self.batch_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.batch_delete_btn.clicked.connect(self.batch_delete_users)
        user_buttons.addWidget(self.batch_delete_btn)
        
        # 批量切换管理员权限按钮
        self.batch_admin_btn = QPushButton("批量切换管理员")
        self.batch_admin_btn.setFixedSize(min_button_width + 20, 40)
        self.batch_admin_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.batch_admin_btn.clicked.connect(self.batch_toggle_admin)
        user_buttons.addWidget(self.batch_admin_btn)

        # 批量切换回放权限按钮
        self.batch_replay_btn = QPushButton("批量切换回放")
        self.batch_replay_btn.setFixedSize(min_button_width + 20, 40)
        self.batch_replay_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.batch_replay_btn.clicked.connect(self.batch_toggle_replay)
        user_buttons.addWidget(self.batch_replay_btn)

        self.batch_enable_btn = QPushButton("批量启用")
        self.batch_enable_btn.setFixedSize(min_button_width, 40)
        self.batch_enable_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.batch_enable_btn.clicked.connect(self.batch_enable_users)
        user_buttons.addWidget(self.batch_enable_btn)
        
        self.refresh_btn = QPushButton("刷新用户列表")
        self.refresh_btn.setFixedSize(min_button_width + 10, 40)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_users)
        user_buttons.addWidget(self.refresh_btn)
        
        self.create_user_btn = QPushButton("创建新用户")
        self.create_user_btn.setFixedSize(min_button_width, 40)
        self.create_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.create_user_btn.clicked.connect(self.create_user)
        user_buttons.addWidget(self.create_user_btn)
        
        user_buttons.addStretch()  # 添加右侧弹性空间，让按钮完全居中
        
        user_layout.addLayout(user_buttons)
        
        # 反馈管理页面
        feedback_tab = QWidget()
        feedback_layout = QVBoxLayout(feedback_tab)
        feedback_layout.setContentsMargins(0, 0, 0, 0)
        feedback_layout.setSpacing(0)
        
        # 反馈表格
        self.feedback_table = QTableWidget()
        self.feedback_table.setColumnCount(7)
        self.feedback_table.setHorizontalHeaderLabels(["ID", "用户名", "类型", "标题", "详细描述", "联系方式", "提交时间"])
        self.feedback_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.feedback_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.feedback_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.feedback_table.verticalHeader().setDefaultSectionSize(25)
        
        # 应用表格样式 - 与FolderManager保持一致
        from styles import get_table_style
        self.feedback_table.setStyleSheet(get_table_style() + """
            QTableWidget::item {
                padding: 10px;
            }
            QHeaderView::section {
                padding: 0px;
                margin: 0px;
            }
        """)
        
        feedback_layout.addWidget(self.feedback_table)
        
        # 反馈管理按钮 - 使用现代化设计
        feedback_buttons = QHBoxLayout()
        feedback_buttons.setSpacing(5)  # 固定间距
        self.refresh_feedback_btn = QPushButton("刷新反馈")
        self.refresh_feedback_btn.setFixedSize(min_button_width, 40)
        self.refresh_feedback_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.refresh_feedback_btn.clicked.connect(self.load_feedback)
        feedback_buttons.addWidget(self.refresh_feedback_btn)
        
        self.mark_processed_btn = QPushButton("标记已处理")
        self.mark_processed_btn.setFixedSize(min_button_width + 20, 40)
        self.mark_processed_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.mark_processed_btn.clicked.connect(self.mark_feedback_processed)
        feedback_buttons.addWidget(self.mark_processed_btn)
        
        self.delete_feedback_btn = QPushButton("删除反馈")
        self.delete_feedback_btn.setFixedSize(min_button_width, 40)
        self.delete_feedback_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        self.delete_feedback_btn.clicked.connect(self.delete_feedback)
        feedback_buttons.addWidget(self.delete_feedback_btn)
        
        feedback_layout.addLayout(feedback_buttons)
        
        # 添加标签页
        self.tabs.addTab(user_tab, "用户管理")
        self.tabs.addTab(feedback_tab, "反馈管理")
        
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        
    def load_users(self):
        """加载用户列表（同步方法，保留用于刷新按钮）"""
        # 使用异步加载方式，重置到第一页
        self.current_page = 1
        self.setup_loading_indicator()
        # 从页面大小选择框获取当前值
        try:
            current_page_size = int(self.page_size_combo.currentText())
        except:
            current_page_size = 20
        self.load_users_async(self.current_page, current_page_size)
            
    def get_selected_user(self):
        """获取选中的用户"""
        current_row = self.user_table.currentRow()
        if current_row < 0:
            self.show_message_box('warning', "提示", "请先选择一个用户")
            return None
        
        try:
            # 获取选中的用户信息
            user_id = self.user_table.item(current_row, 1).text()  # 索引从0改为1，因为增加了复选框列
            username = self.user_table.item(current_row, 2).text()  # 索引从1改为2
            email = self.user_table.item(current_row, 3).text()  # 索引从2改为3
            is_vip = self.user_table.item(current_row, 7).text() == "是"  # 索引从6改为7
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'is_vip': is_vip
            }
        except Exception as e:
            self.show_message_box('critical', "错误", f"获取用户信息失败: {str(e)}")
            return None
    
    def on_cell_clicked(self, row, column):
        """单元格点击事件处理"""
        # 点击任何单元格时，切换对应行的复选框状态
        try:
            # 获取QCheckBox容器
            container = self.user_table.cellWidget(row, 0)
            if container:
                # 从容器布局中获取复选框
                layout = container.layout()
                if layout:
                    checkbox = layout.itemAt(0).widget()
                    if checkbox and isinstance(checkbox, QCheckBox):
                        # 切换复选框状态
                        checkbox.setChecked(not checkbox.isChecked())
        except Exception as e:
            print(f"处理单元格点击事件失败: {str(e)}")
    
    def get_selected_users(self):
        """获取所有选中的用户"""
        selected_users = []
        row_count = self.user_table.rowCount()
        
        print(f"表格总行数: {row_count}")
        
        for row in range(row_count):
            try:
                # 获取QCheckBox容器
                container = self.user_table.cellWidget(row, 0)
                if container:
                    # 从容器布局中获取复选框
                    layout = container.layout()
                    if layout:
                        checkbox = layout.itemAt(0).widget()
                        if checkbox and isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                            # 获取选中的用户信息
                            user_id = self.user_table.item(row, 1).text()
                            username = self.user_table.item(row, 2).text()
                            email = self.user_table.item(row, 3).text()
                            
                            print(f"选中用户: ID={user_id}, 用户名={username}, 邮箱={email}")
                            
                            selected_users.append({
                                'id': user_id,
                                'username': username,
                                'email': email
                            })
            except Exception as e:
                print(f"获取第{row}行用户信息失败: {str(e)}")
                continue
        
        print(f"总共选中 {len(selected_users)} 个用户")
        return selected_users
    
    def on_checkbox_state_changed(self, state):
        """复选框状态变化处理"""
        # 这里可以添加复选框状态变化时的处理逻辑
        # 目前不需要特殊处理，仅作为占位函数
        pass
    
    def toggle_select_all(self):
        """全选/取消全选"""
        row_count = self.user_table.rowCount()
        
        # 检查是否已经全选
        all_selected = True
        for row in range(row_count):
            try:
                # 获取QCheckBox容器
                container = self.user_table.cellWidget(row, 0)
                if container:
                    # 从容器布局中获取复选框
                    layout = container.layout()
                    if layout:
                        checkbox = layout.itemAt(0).widget()
                        if checkbox and isinstance(checkbox, QCheckBox) and not checkbox.isChecked():
                            all_selected = False
                            break
            except Exception as e:
                print(f"检查第{row}行复选框状态失败: {str(e)}")
                all_selected = False
                break
        
        # 根据当前状态设置所有复选框
        for row in range(row_count):
            try:
                # 获取QCheckBox容器
                container = self.user_table.cellWidget(row, 0)
                if container:
                    # 从容器布局中获取复选框
                    layout = container.layout()
                    if layout:
                        checkbox = layout.itemAt(0).widget()
                        if checkbox and isinstance(checkbox, QCheckBox):
                            checkbox.setChecked(not all_selected)
            except Exception as e:
                print(f"设置第{row}行复选框状态失败: {str(e)}")
        
        # 更新按钮文本
        self.select_all_btn.setText("取消全选" if not all_selected else "全选")
    
    def batch_delete_users(self):
        """批量删除用户"""
        selected_users = self.get_selected_users()
        
        if not selected_users:
            self.show_message_box('warning', "警告", "请先选择要删除的用户")
            return
        
        # 确认删除
        usernames = [user['username'] for user in selected_users]
        reply = self.show_message_box(
            'question', "确认删除", 
            f"确定要删除以下用户吗？\n{', '.join(usernames)}\n\n此操作不可恢复！"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for user in selected_users:
            try:
                # 调用数据库删除方法
                success = self.db_helper.delete_user(user['id'])
                if success:
                    # 同时删除本地JSON文件中的用户
                    if self.login_manager:
                        try:
                            users = self.login_manager._load_users()
                            if user['username'] in users:
                                del users[user['username']]
                                self.login_manager._save_users(users)
                                print(f"成功从本地JSON文件中删除用户 {user['username']}")
                        except Exception as local_error:
                            print(f"从本地JSON文件中删除用户 {user['username']} 失败: {str(local_error)}")
                            # 本地删除失败不影响整体成功计数
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f"删除用户 {user['username']} 失败")
            except Exception as e:
                error_count += 1
                error_messages.append(f"删除用户 {user['username']} 时出错: {str(e)}")
        
        # 显示结果
        if error_count == 0:
            QMessageBox.information(self, "成功", f"成功删除 {success_count} 个用户")
        else:
            error_text = "\n".join(error_messages)
            self.show_message_box('warning', "部分失败", 
                               f"成功删除 {success_count} 个用户，失败 {error_count} 个用户\n\n错误详情:\n{error_text}")
        
        # 刷新用户列表
        self.load_users()
    
    def batch_enable_users(self):
        """批量启用用户账户"""
        selected_users = self.get_selected_users()
        
        if not selected_users:
            self.show_message_box('warning', "警告", "请先选择要启用的用户")
            return
        
        # 确认操作
        usernames = [user['username'] for user in selected_users]
        reply = self.show_message_box(
            'question', "确认启用", 
            f"确定要启用以下用户的账户吗？\n{', '.join(usernames)}"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for user in selected_users:
            try:
                # 调用数据库更新方法，使用update_user_by_id而不是update_user
                success = self.db_helper.update_user_by_id(user['id'], {'is_active': True})
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f"启用用户 {user['username']} 的账户失败")
            except Exception as e:
                error_count += 1
                error_messages.append(f"启用用户 {user['username']} 的账户时出错: {str(e)}")
        
        # 显示结果
        if error_count == 0:
            self.show_message_box('information', "成功", f"成功启用 {success_count} 个用户账户")
        else:
            error_text = "\n".join(error_messages)
            self.show_message_box('warning', "部分失败", 
                               f"成功启用 {success_count} 个用户账户，失败 {error_count} 个用户\n\n错误详情:\n{error_text}")
        
        # 刷新用户列表
        self.load_users()
    
    def batch_disable_users(self):
        """批量禁用用户账户"""
        selected_users = self.get_selected_users()
        
        if not selected_users:
            self.show_message_box('warning', "警告", "请先选择要禁用的用户")
            return
        
        # 确认操作
        usernames = [user['username'] for user in selected_users]
        reply = self.show_message_box(
            'question', "确认禁用", 
            f"确定要禁用以下用户的账户吗？\n{', '.join(usernames)}"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for user in selected_users:
            try:
                # 调用数据库更新方法，使用update_user_by_id而不是update_user
                success = self.db_helper.update_user_by_id(user['id'], {'is_active': False})
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f"禁用用户 {user['username']} 的账户失败")
            except Exception as e:
                error_count += 1
                error_messages.append(f"禁用用户 {user['username']} 的账户时出错: {str(e)}")
        
        # 显示结果
        if error_count == 0:
            self.show_message_box('information', "成功", f"成功禁用 {success_count} 个用户账户")
        else:
            error_text = "\n".join(error_messages)
            self.show_message_box('warning', "部分失败", 
                               f"成功禁用 {success_count} 个用户账户，失败 {error_count} 个用户\n\n错误详情:\n{error_text}")
        
        # 刷新用户列表
        self.load_users()

    def batch_toggle_admin(self):
        """批量切换管理员权限"""
        selected_users = self.get_selected_users()
        
        if not selected_users:
            self.show_message_box('warning', "警告", "请先选择要切换的用户")
            return
        
        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("切换管理员权限")
        dialog.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        label = QLabel("请选择要执行的操作：")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # 创建按钮组
        button_layout = QHBoxLayout()
        
        set_admin_btn = QPushButton("设为管理员")
        set_admin_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
        """)
        set_admin_btn.clicked.connect(lambda: self._perform_batch_admin(selected_users, True, dialog))
        button_layout.addWidget(set_admin_btn)
        
        unset_admin_btn = QPushButton("取消管理员")
        unset_admin_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
        """)
        unset_admin_btn.clicked.connect(lambda: self._perform_batch_admin(selected_users, False, dialog))
        button_layout.addWidget(unset_admin_btn)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _perform_batch_admin(self, users, is_admin, dialog):
        """执行批量管理员操作"""
        dialog.accept()
        
        usernames = [user['username'] for user in users]
        action = "设为管理员" if is_admin else "取消管理员"
        
        reply = self.show_message_box(
            'question', f"确认{action}", 
            f"确定要{action}以下用户吗？\n{', '.join(usernames)}"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for user in users:
            try:
                success = self.db_helper.update_user_by_id(user['id'], {'is_admin': is_admin})
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f"{action}用户 {user['username']} 失败")
            except Exception as e:
                error_count += 1
                error_messages.append(f"{action}用户 {user['username']} 时出错: {str(e)}")
        
        # 显示结果
        if error_count == 0:
            self.show_message_box('information', "成功", f"成功{action} {success_count} 个用户")
        else:
            error_text = "\n".join(error_messages)
            self.show_message_box('warning', "部分失败", 
                               f"成功{action} {success_count} 个用户，失败 {error_count} 个用户\n\n错误详情:\n{error_text}")
        
        # 刷新用户列表
        self.load_users()

    def batch_toggle_replay(self):
        """批量切换回放权限"""
        selected_users = self.get_selected_users()
        
        if not selected_users:
            self.show_message_box('warning', "警告", "请先选择要切换的用户")
            return
        
        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("切换回放权限")
        dialog.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        label = QLabel("请选择要执行的操作：")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # 创建按钮组
        button_layout = QHBoxLayout()
        
        enable_replay_btn = QPushButton("开启回放")
        enable_replay_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
        """)
        enable_replay_btn.clicked.connect(lambda: self._perform_batch_replay(selected_users, True, dialog))
        button_layout.addWidget(enable_replay_btn)
        
        disable_replay_btn = QPushButton("关闭回放")
        disable_replay_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
        """)
        disable_replay_btn.clicked.connect(lambda: self._perform_batch_replay(selected_users, False, dialog))
        button_layout.addWidget(disable_replay_btn)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _perform_batch_replay(self, users, can_replay, dialog):
        """执行批量回放权限操作"""
        dialog.accept()
        
        usernames = [user['username'] for user in users]
        action = "开启回放" if can_replay else "关闭回放"
        
        reply = self.show_message_box(
            'question', f"确认{action}", 
            f"确定要{action}以下用户吗？\n{', '.join(usernames)}"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for user in users:
            try:
                success = self.db_helper.update_user_by_id(user['id'], {'can_replay': can_replay})
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f"{action}用户 {user['username']} 失败")
            except Exception as e:
                error_count += 1
                error_messages.append(f"{action}用户 {user['username']} 时出错: {str(e)}")
        
        # 显示结果
        if error_count == 0:
            self.show_message_box('information', "成功", f"成功{action} {success_count} 个用户")
        else:
            error_text = "\n".join(error_messages)
            self.show_message_box('warning', "部分失败", 
                               f"成功{action} {success_count} 个用户，失败 {error_count} 个用户\n\n错误详情:\n{error_text}")
        
        # 刷新用户列表
        self.load_users()

    def delete_user(self):
        """删除用户"""
        user = self.get_selected_user()
        if not user:
            return
            
        if user['username'] == 'admin':
            self.show_message_box('warning', "警告", "不能删除默认管理员账户")
            return
            
        reply = self.show_message_box('question', "确认", 
                                     f"确定要删除用户 {user['username']} 吗？此操作不可恢复！")
        if reply == QMessageBox.Yes:
            try:
                success = self.db_helper.delete_user(user['id'])
                
                if success:
                    self.show_message_box('information', "成功", "用户删除成功")
                    self.load_users()
                else:
                    self.show_message_box('critical', "错误", "操作失败")
            except Exception as e:
                self.show_message_box('critical', "错误", f"操作失败: {str(e)}")

    def create_user(self):
        """创建新用户"""
        print(f"调试: AdminManager.create_user被调用")
        print(f"调试: AdminManager实例ID: {id(self)}")
        print(f"调试: AdminManager类型: {type(self)}")
        print(f"调试: AdminManager有db_helper属性: {hasattr(self, 'db_helper')}")
        dialog = CreateUserDialog(self)
        print(f"调试: CreateUserDialog已创建")
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()
  
    def show_user_context_menu(self, position):
        """显示用户右键菜单"""
        # 获取选中的行
        selected_rows = self.user_table.selectedItems()
        if selected_rows:
            # 获取当前选中用户的信息
            current_row = self.user_table.currentRow()
            if current_row >= 0:
                # 获取用户状态
                status_item = self.user_table.item(current_row, 6)
                is_active = status_item.text() == "启用" if status_item else True
                
                # 获取管理员状态
                admin_item = self.user_table.item(current_row, 5)
                is_admin = admin_item.text() == "是" if admin_item else False
                
                # 获取回放权限状态
                replay_item = self.user_table.item(current_row, 9)
                can_replay = replay_item.text() == "是" if replay_item else True
                
                # 更新菜单文本
                self.toggle_active_action.setText("禁用用户" if is_active else "启用用户")
                self.toggle_admin_action.setText("取消管理员" if is_admin else "设为管理员")
                self.toggle_replay_action.setText("关闭回放" if can_replay else "开启回放")
            
            # 显示菜单
            self.user_context_menu.exec_(self.user_table.mapToGlobal(position))

    def toggle_user_active(self):
        """切换用户启用/禁用状态"""
        user = self.get_selected_user()
        if not user:
            return
        
        # 获取当前状态
        current_row = self.user_table.currentRow()
        status_item = self.user_table.item(current_row, 6)
        is_active = status_item.text() == "启用" if status_item else True
        new_status = not is_active
        
        action = "禁用" if is_active else "启用"
        
        reply = self.show_message_box(
            'question', f"确认{action}", 
            f"确定要{action}用户 {user['username']} 吗？"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            success = self.db_helper.update_user_by_id(user['id'], {'is_active': new_status})
            if success:
                self.show_message_box('information', "成功", f"成功{action}用户 {user['username']}")
                self.load_users()
            else:
                self.show_message_box('warning', "失败", f"{action}用户 {user['username']} 失败")
        except Exception as e:
            self.show_message_box('critical', "错误", f"{action}用户 {user['username']} 时出错: {str(e)}")

    def toggle_user_admin(self):
        """切换用户管理员状态"""
        user = self.get_selected_user()
        if not user:
            return
        
        # 获取当前状态
        current_row = self.user_table.currentRow()
        admin_item = self.user_table.item(current_row, 5)
        is_admin = admin_item.text() == "是" if admin_item else False
        new_admin = not is_admin
        
        action = "取消管理员" if is_admin else "设为管理员"
        
        reply = self.show_message_box(
            'question', f"确认{action}", 
            f"确定要{action}用户 {user['username']} 吗？"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            success = self.db_helper.update_user_by_id(user['id'], {'is_admin': new_admin})
            if success:
                self.show_message_box('information', "成功", f"成功{action}用户 {user['username']}")
                self.load_users()
            else:
                self.show_message_box('warning', "失败", f"{action}用户 {user['username']} 失败")
        except Exception as e:
            self.show_message_box('critical', "错误", f"{action}用户 {user['username']} 时出错: {str(e)}")

    def toggle_user_replay(self):
        """切换用户回放权限"""
        user = self.get_selected_user()
        if not user:
            return
        
        # 获取当前状态
        current_row = self.user_table.currentRow()
        replay_item = self.user_table.item(current_row, 9)
        can_replay = replay_item.text() == "是" if replay_item else True
        new_replay = not can_replay
        
        action = "关闭回放" if can_replay else "开启回放"
        
        reply = self.show_message_box(
            'question', f"确认{action}", 
            f"确定要{action}用户 {user['username']} 吗？"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            success = self.db_helper.update_user_by_id(user['id'], {'can_replay': new_replay})
            if success:
                self.show_message_box('information', "成功", f"成功{action}用户 {user['username']}")
                self.load_users()
            else:
                self.show_message_box('warning', "失败", f"{action}用户 {user['username']} 失败")
        except Exception as e:
            self.show_message_box('critical', "错误", f"{action}用户 {user['username']} 时出错: {str(e)}")

    def load_feedback(self):
        """加载反馈列表"""
        try:
            # 使用DatabaseHelper获取反馈列表
            feedback_data = self.db_helper.get_all_feedback()
            
            self.feedback_table.setRowCount(len(feedback_data))
            for row, item in enumerate(feedback_data):
                # ID
                item_widget = QTableWidgetItem(str(item.get('id', '')))
                item_widget.setTextAlignment(Qt.AlignCenter)
                self.feedback_table.setItem(row, 0, item_widget)
                
                # 用户名
                item_widget = QTableWidgetItem(item.get('username', ''))
                item_widget.setTextAlignment(Qt.AlignCenter)
                self.feedback_table.setItem(row, 1, item_widget)
                
                # 类型
                item_widget = QTableWidgetItem(item.get('feedback_type', ''))
                item_widget.setTextAlignment(Qt.AlignCenter)
                self.feedback_table.setItem(row, 2, item_widget)
                
                # 标题
                item_widget = QTableWidgetItem(item.get('title', ''))
                item_widget.setTextAlignment(Qt.AlignCenter)
                self.feedback_table.setItem(row, 3, item_widget)
                
                # 详细描述
                detail = item.get('detail', '')
                display_text = detail[:100] + "..." if len(detail) > 100 else detail
                item_widget = QTableWidgetItem(display_text)
                item_widget.setToolTip(detail)  # 完整内容在tooltip中
                item_widget.setTextAlignment(Qt.AlignCenter)
                self.feedback_table.setItem(row, 4, item_widget)
                
                # 联系方式
                item_widget = QTableWidgetItem(item.get('contact', ''))
                item_widget.setTextAlignment(Qt.AlignCenter)
                self.feedback_table.setItem(row, 5, item_widget)
                
                # 提交时间
                created_at = item.get('created_at', '')
                item_widget = QTableWidgetItem(self.format_datetime(created_at))
                item_widget.setTextAlignment(Qt.AlignCenter)
                self.feedback_table.setItem(row, 6, item_widget)
                    
        except Exception as e:
            self.show_message_box('critical', "错误", f"加载反馈列表失败: {str(e)}")

    def get_selected_feedback(self):
        """获取选中的反馈"""
        current_row = self.feedback_table.currentRow()
        if current_row < 0:
            self.show_message_box('warning', "提示", "请先选择一条反馈")
            return None
        return {
            'id': self.feedback_table.item(current_row, 0).text()
        }

    def mark_feedback_processed(self):
        """标记反馈为已处理"""
        feedback = self.get_selected_feedback()
        if not feedback:
            return
            
        reply = self.show_message_box('question', "确认", 
                                     "确定要将此反馈标记为已处理吗？")
        if reply == QMessageBox.Yes:
            try:
                success = self.db_helper.update_feedback(feedback['id'], {'status': 'processed'})
                
                if success:
                    self.show_message_box('information', "成功", "反馈已标记为已处理")
                    self.load_feedback()
                else:
                    self.show_message_box('critical', "错误", "操作失败")
            except Exception as e:
                self.show_message_box('critical', "错误", f"操作失败: {str(e)}")

    def delete_feedback(self):
        """删除反馈"""
        feedback = self.get_selected_feedback()
        if not feedback:
            return
            
        reply = self.show_message_box('question', "确认", 
                                     "确定要删除这条反馈吗？此操作不可恢复！")
        if reply == QMessageBox.Yes:
            try:
                success = self.db_helper.delete_feedback(feedback['id'])
                
                if success:
                    self.show_message_box('information', "成功", "反馈删除成功")
                    self.load_feedback()
                else:
                    self.show_message_box('critical', "错误", "操作失败")
            except Exception as e:
                self.show_message_box('critical', "错误", f"操作失败: {str(e)}")

    def update_feedback_field(self, feedback_id, sql):
        """更新反馈字段"""
        try:
            # 首先尝试使用Supabase
            from supabase_db import get_supabase_manager
            supabase_manager = get_supabase_manager()
            if supabase_manager.is_connected():
                # 根据SQL语句判断操作类型
                if "DELETE" in sql.upper():
                    # 删除反馈
                    supabase_manager.delete_feedback(feedback_id)
                    self.show_message_box('information', "成功", "反馈删除成功")
                else:
                    # 更新反馈状态
                    supabase_manager.update_feedback(feedback_id, {'status': 'processed'})
                    self.show_message_box('information', "成功", "反馈已标记为已处理")
            else:
                self.show_message_box('warning', "警告", "Supabase连接失败，无法执行操作")
            
            self.load_feedback()
            
        except Exception as e:
            self.show_message_box('critical', "错误", f"操作失败: {str(e)}")

    def showEvent(self, event):
        """窗口显示时加载数据"""
        super().showEvent(event)
        self.load_feedback()
        
    # 分页相关方法
    def go_to_first_page(self):
        """跳转到第一页"""
        if self.current_page != 1:
            self.current_page = 1
            self.load_users_async(self.current_page, self.page_size)
    
    def go_to_prev_page(self):
        """跳转到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_users_async(self.current_page, self.page_size)
    
    def go_to_next_page(self):
        """跳转到下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_users_async(self.current_page, self.page_size)
    
    def go_to_last_page(self):
        """跳转到最后一页"""
        if self.current_page != self.total_pages:
            self.current_page = self.total_pages
            self.load_users_async(self.current_page, self.page_size)
    
    def on_page_size_changed(self, size_text):
        """每页显示数量改变时的处理"""
        try:
            new_page_size = int(size_text)
            if new_page_size != self.page_size:
                self.page_size = new_page_size
                # 重新计算当前页码，确保不会超出范围
                self.current_page = 1
                self.load_users_async(self.current_page, self.page_size)
        except ValueError:
            pass
        

            

        

            







class CreateUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建新用户")
        
        # 获取屏幕尺寸，设置创建用户窗口为屏幕的35%
        screen_width, screen_height = get_screen_size()
        width = int(screen_width * 0.35)
        height = int(screen_height * 0.45)
        self.resize(width, height)
        
        # 将窗口居中显示
        if parent:
            # 相对于父窗口居中
            parent_geometry = parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - width) // 2
            y = parent_geometry.y() + (parent_geometry.height() - height) // 2
        else:
            # 相对于屏幕居中
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        self.move(x, y)
        
        # 设置窗口标志，移除问号帮助按钮
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        # 使用utils.py中的统一样式应用函数
        apply_styles_to_dialog(self)
        
        layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.is_admin_checkbox = QCheckBox("设为管理员")
        
        layout.addRow("用户名:", self.username_input)
        layout.addRow("邮箱:", self.email_input)
        layout.addRow("密码:", self.password_input)
        layout.addRow("权限:", self.is_admin_checkbox)
        
        buttons = QHBoxLayout()
        create_btn = QPushButton("创建")
        create_btn.setFixedSize(100, 36)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }
            QPushButton:hover {
                background-color: #007AFF;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """)
        
        create_btn.clicked.connect(self.create_user)
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(create_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        
    def keyPressEvent(self, event):
        """处理键盘事件，实现ESC键退出功能"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
        
    def create_user(self):
        """创建用户"""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        is_admin = 1 if self.is_admin_checkbox.isChecked() else 0
        
        if not username or not password:
            # 使用父类的show_message_box方法
            if self.parent and hasattr(self.parent, 'show_message_box'):
                self.parent.show_message_box('warning', "警告", "用户名和密码不能为空")
            else:
                QMessageBox.warning(self, "警告", "用户名和密码不能为空")
            return
            
        password_hash = hash_password(password)
        
        try:
            # 使用DatabaseHelper创建用户
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'is_admin': bool(is_admin),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 确保parent对象存在且有db_helper属性
            print(f"调试: parent对象存在: {self.parent is not None}")
            print(f"调试: parent类型: {type(self.parent)}")
            print(f"调试: parent对象ID: {id(self.parent)}")
            if self.parent:
                print(f"调试: parent有db_helper属性: {hasattr(self.parent, 'db_helper')}")
                if hasattr(self.parent, 'db_helper'):
                    print(f"调试: db_helper值: {self.parent.db_helper}")
                # 检查parent的所有属性
                print(f"调试: parent的所有属性: {[attr for attr in dir(self.parent) if not attr.startswith('_')]}")
            
            if self.parent and hasattr(self.parent, 'db_helper'):
                # 检查用户名是否已存在
                existing_user = self.parent.db_helper.get_user(username)
                if existing_user:
                    # 使用父类的show_message_box方法
                    if self.parent and hasattr(self.parent, 'show_message_box'):
                        self.parent.show_message_box('warning', "警告", "用户名已存在")
                    else:
                        QMessageBox.warning(self, "警告", "用户名已存在")
                    return
                    
                # 使用HybridDatabaseManager的create_user方法，传递单独的参数
                result = self.parent.db_helper.create_user(
                    username,
                    email,
                    password_hash,
                    is_admin
                )
                
                if result:
                    # 使用父类的show_message_box方法
                    if self.parent and hasattr(self.parent, 'show_message_box'):
                        self.parent.show_message_box('information', "成功", f"用户 {username} 创建成功")
                    else:
                        QMessageBox.information(self, "成功", f"用户 {username} 创建成功")
                    self.accept()
                    self.parent.load_users()
                else:
                    # 使用父类的show_message_box方法
                    if self.parent and hasattr(self.parent, 'show_message_box'):
                        self.parent.show_message_box('critical', "错误", "创建用户失败")
                    else:
                        QMessageBox.critical(self, "错误", "创建用户失败")
            else:
                # 使用父类的show_message_box方法
                if self.parent and hasattr(self.parent, 'show_message_box'):
                    self.parent.show_message_box('critical', "错误", "无法访问数据库连接")
                else:
                    QMessageBox.critical(self, "错误", "无法访问数据库连接")
            
        except Exception as e:
            # 使用父类的show_message_box方法
            if self.parent and hasattr(self.parent, 'show_message_box'):
                self.parent.show_message_box('critical', "错误", f"创建用户失败: {str(e)}")
            else:
                QMessageBox.critical(self, "错误", f"创建用户失败: {str(e)}")