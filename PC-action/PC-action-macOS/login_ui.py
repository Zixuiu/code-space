"""
文件: login_ui.py
用途: 提供登录和注册的用户界面组件，包含用户认证相关的交互界面实现。
      实现登录对话框、注册表单、用户验证界面等UI组件，支持用户账户管理的可视化交互。
"""

import random
import string
from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton,
                            QVBoxLayout, QHBoxLayout, QMessageBox,
                            QTabWidget, QWidget, QFormLayout, QInputDialog,
                            QCheckBox, QApplication, QStyleFactory, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont, QIcon, QFontDatabase
from utils import is_valid_email, get_screen_size, apply_styles_to_dialog, get_common_dialog_style, generate_random_username, validate_password_requirements, STYLES_AVAILABLE, create_styled_button, create_styled_input
from beautiful_dialog import StyledMessageDialog

try:
    from styles import generate_dynamic_styles, apply_dialog_style, PRIMARY_GRADIENT, SECONDARY, ACCENT, BG, CARD, TEXT, MUTED, BORDER
except ImportError:
    PRIMARY_GRADIENT = "#007AFF"
    SECONDARY = "#007AFF"
    ACCENT = "#007AFF"
    BG = "#FFFFFF"
    CARD = "#FFFFFF"
    TEXT = "#2C3E50"
    MUTED = "#8E8E93"
    BORDER = "#DFE6E9"

# 使用PyQt5内置样式替代qt_material

def init_default_styles(app):
    try:
        # 设置应用程序样式
        available_styles = QStyleFactory.keys()
        print(f"可用样式: {available_styles}")
        # 选择一个可用的样式
        if 'Fusion' in available_styles:
            app.setStyle('Fusion')
        elif 'Windows' in available_styles:
            app.setStyle('Windows')
        elif available_styles:
            app.setStyle(available_styles[0])
        # 配置字体
        font = QFont()
        font.setFamily('Microsoft YaHei')  # 统一使用微软雅黑字体
        app.setFont(font)
        return True
    except Exception as e:
        print(f"设置样式失败: {e}")
        return False


# 创建同步登录操作
class EmailThread(QThread):
    """用于异步发送验证码的线程类"""
    finished = pyqtSignal(bool, str, str, str)  # 成功标志, 消息, 邮箱地址, 验证码
    
    def __init__(self, email, login_manager):
        super().__init__()
        self.email = email
        self.login_manager = login_manager
    
    def run(self):
        """执行邮件发送操作"""
        try:
            # 调用登录管理器的发送方法，现在返回三个值
            success, msg, code = self.login_manager.send_verification_code(self.email)
            self.finished.emit(success, msg, self.email, code)
        except Exception as e:
            self.finished.emit(False, f"发送验证码时发生错误: {str(e)}", self.email, None)

class LoginThread:
    def __init__(self, login_manager, username, password):
        self.login_manager = login_manager
        self.username = username
        self.password = password

    def start(self):
        # 直接执行登录操作，不使用线程
        success, message = self.login_manager.login(self.username, self.password)
        self.login_result(success, message)

    def login_result(self, success, message):
        # 直接调用结果处理函数
        pass

class RegisterThread:
    def __init__(self, login_manager, username, password, email, verification_code):
        self.login_manager = login_manager
        self.username = username
        self.password = password
        self.email = email
        self.verification_code = verification_code

    def start(self):
        # 直接执行注册操作，不使用线程
        success, msg = self.login_manager.register(
            username=self.username,
            password=self.password,
            email=self.email,
            verification_code=self.verification_code
        )
        self.register_result(success, msg)

    def register_result(self, success, msg):
        # 直接调用结果处理函数
        pass

class LoginDialog(QDialog):
    """登录对话框，处理用户登录和注册界面"""

    # 定义登录成功信号
    login_success = pyqtSignal(str)

    def __init__(self, login_manager, parent=None):
        super().__init__(parent)
        self.login_manager = login_manager
        self.current_user = None
        self.auto_fill_defaults = True  # 控制是否填充默认数据
        self.skip_verification = False  # 添加 skip_verification 属性
        
        # 添加延迟初始化标记
        self._register_tab_initialized = False
        self._forgot_password_tab_initialized = False
        
        # 获取屏幕尺寸，设置登录窗口为屏幕的25%
        width, height = get_screen_size(0.25)
        # 移除setMinimumSize，避免覆盖initUI中的resize设置

        # 不再隐藏窗口，避免闪烁
        # self.hide()  # 移除此行，避免窗口闪烁
        
        # 添加自动填充登录信息功能
        self.username, self.password = self.login_manager.load_saved_login()
        self._log_debug(f"LoginDialog __init__ - 加载的登录信息: 用户名={self.username}, 密码={'*' * len(self.password) if self.password else ''}")
        self.initUI()

    def create_styled_input(self, placeholder, echo_mode=QLineEdit.Normal, icon='📝', height=None, font_size=None, width=None):
        """创建带样式和图标的输入框

        Args:
            placeholder: 占位文本
            echo_mode: 输入模式
            icon: 前缀图标
            height: 输入框高度
            font_size: 字体大小
            width: 输入框宽度

        Returns:
            QLineEdit: 返回输入框
        """
        # 创建一个新的QLineEdit对象
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setEchoMode(echo_mode)
        
        # 获取屏幕尺寸
        _, screen_height = get_screen_size()
        
        # 设置默认值，进一步增大输入框高度
        if height is None:
            height = int(screen_height * 0.08)  # 从0.06增加到0.08，增大输入框大小
        else:
            # 确保验证码输入框有足够高度
            height = max(height, int(screen_height * 0.040))  # 增大验证码输入框的最小高度
        if font_size is None:
            font_size = max(16, int(screen_height * 0.025))  # 相应增大字体大小
        
        # 设置输入框固定高度
        input_field.setFixedHeight(height)
        
        # 设置统一的输入框样式，确保不被遮挡 - macOS风格
        input_style = f"""
            QLineEdit {{
                background-color: {BG};
                color: {TEXT};
                border: 2px solid {BORDER};
                border-radius: {int(height/2)}px;
                padding: 8px 15px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: {font_size}px;
                min-width: 200px;
                outline: none;
            }}
            QLineEdit:focus {{
                border: 2px solid {ACCENT};
                background-color: {BG};
            }}
            QLineEdit::placeholder {{
                color: {MUTED};
            }}
        """
        input_field.setStyleSheet(input_style)
        
        # 创建一个容器来放置图标和输入框
        container = QWidget()
        container.setFixedHeight(height)
        container.setStyleSheet("background: transparent; border: none;")
        
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)
        
        # 使用不同的图标表示不同类型
        icon_map = {
            '📝': '👤',  # 用户名图标
            '🔒': '🔒',  # 密码图标
            '📧': '📧',  # 邮箱图标
            '🔑': '🔑',  # 验证码图标
            '✓': '✓',  # 勾选图标
            '✗': '✗',  # 错误图标
            '👤': '👤',  # 用户图标
            '🔐': '🔒',  # 锁图标
        }
        
        display_icon = icon_map.get(icon, '📝')
        
        # 创建图标容器（无背景）
        icon_container = QWidget()
        icon_container.setFixedSize(height, height)
        icon_container.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border-radius: {int(height/2)}px;
            }}
        """)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        # 图标标签
        icon_label = QLabel(display_icon)
        # 设置合适的图标字体大小，避免过大
        icon_size = min(font_size + 8, int(height * 0.6))  # 限制图标大小，确保不遮挡输入框
        icon_label.setStyleSheet(f"color: {ACCENT}; font-size: {icon_size}px;")
        icon_label.setAlignment(Qt.AlignCenter)
        # 确保图标在容器中正确布局
        icon_layout.addWidget(icon_label)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        # 移除边距限制，让图标有足够空间显示
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加部件到主容器
        container_layout.addWidget(icon_container)
        container_layout.addWidget(input_field, 1)
        
        # 保存容器引用
        input_field._icon_container = container
        
        # 设置容器为输入框的父对象
        input_field.setParent(container)
        
        return input_field

    def create_button(self, text, style_sheet, min_width=None, min_height=None, max_width=None, clicked_handler=None, icon=None):
        """创建带样式的按钮

        Args:
            text: 按钮文本
            style_sheet: 样式表
            min_width: 最小宽度（如果为None，将使用屏幕宽度的8%）
            min_height: 最小高度（如果为None，将使用屏幕高度的4%）
            max_width: 最大宽度
            clicked_handler: 点击事件处理函数
            icon: 图标

        Returns:
            QPushButton: 创建的按钮
        """
        # 从style_sheet中提取背景色
        bg_color = "#4CAF50"  # 默认颜色
        if "background-color:" in style_sheet:
            import re
            match = re.search(r'background-color:\s*([^;]+)', style_sheet)
            if match:
                bg_color = match.group(1).strip()
        
        # 创建自定义按钮
        button = QPushButton(text)
        button.setFixedSize(100, 36)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #007AFF;
            }}
            QPushButton:pressed {{
                background-color: #007AFF;
            }}
        """)
        
        # 设置尺寸
        if min_width is not None:
            button.setMinimumWidth(min_width)
        if min_height is not None:
            button.setMinimumHeight(min_height)
        if max_width is not None:
            button.setMaximumWidth(max_width)
            
        if clicked_handler:
            button.clicked.connect(clicked_handler)
        if icon:
            button.setText(f"{icon} {text}")
        return button

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle('办公操作复刻大师 - 登录')
        
        # 使用屏幕比例大小，避免固定像素值
        width, _ = get_screen_size(0.35)  # 窗口宽度比例
        _, height = get_screen_size(0.65)  # 窗口高度比例，与所有页面一致
        self.resize(width, height)  # 使用正常的高度比例，避免界面过长
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)  # 移除最大化按钮和问号帮助按钮
        self.setWindowState(Qt.WindowNoState)  # 确保窗口为普通状态，不最大化
        
        # 应用统一的对话框样式，确保UI一致性
        try:
            apply_dialog_style(self, 0.3, 0.25)
        except NameError:
            # 如果apply_dialog_style不可用，使用基本样式
            _, screen_height = get_screen_size()
            border_radius = int(screen_height * 0.015)  # 动态计算圆角
            padding = int(screen_height * 0.01)  # 动态计算内边距
            self.setStyleSheet(f"""
                QDialog {{ 
                    background-color: white; 
                    color: #262626;
                    font-family: 'Microsoft YaHei';
                }}
                QLabel {{ 
                    color: #262626; 
                    font-family: 'Microsoft YaHei'; 
                }}
                QLineEdit {{ 
                    border: 1px solid white; 
                    border-radius: {border_radius}px; 
                    padding: {padding}px; 
                    font-family: 'Microsoft YaHei';
                    background-color: white;
                    color: #262626;
                }}
                QPushButton {{ 
                    background-color: #1890ff; 
                    color: white; 
                    border-radius: {border_radius}px; 
                    padding: {padding}px; 
                    font-family: 'Microsoft YaHei'; 
                }}
                QPushButton:hover {{ 
                    background-color: #40a9ff; 
                }}
            """)
        
        self.setup_styles()

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)  # 统一间距
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距，让内容占满整个窗口

        # 移除顶部标题，避免与登录卡片内部标题重复

        # 创建主要窗口部件
        self.login_tab = QWidget()
        self.register_tab = QWidget()
        self.forgot_password_tab = QWidget()

        # 只初始化登录页面，其他页面延迟初始化
        self.setup_login_tab()
        # 注册和找回密码页面延迟初始化，提升启动速度
        # self.setup_register_tab()
        # self.setup_forgot_password_tab()

        # 启用自动登录功能，让用户可以选择是否自动登录
        self.try_auto_login()

        # 将布局设置到主窗口
        self.login_tab.setLayout(self.login_layout)
        # 注册和找回密码页面的布局延迟设置
        # self.register_tab.setLayout(self.register_layout)
        # self.forgot_password_tab.setLayout(self.forgot_password_layout)

        # 将三个页面都添加到主布局，默认显示登录页面
        main_layout.addWidget(self.login_tab)
        main_layout.addWidget(self.register_tab)
        main_layout.addWidget(self.forgot_password_tab)
        self.register_tab.hide()  # 隐藏注册页面
        self.forgot_password_tab.hide()  # 隐藏找回密码页面
        self.login_tab.show()  # 显示登录页面
        self.forgot_password_tab.hide()
        
        # 移除不必要的拉伸因子，避免底部空白
        # main_layout.addStretch()

        self.setLayout(main_layout)

        # 自动填充将在showEvent中执行，确保窗口显示后才填充
        self._auto_fill_pending = True

    def _log_debug(self, message):
        """写入调试日志到文件"""
        import os
        from datetime import datetime
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except:
            pass
    
    def showEvent(self, event):
        """窗口显示事件 - 在这里执行自动填充"""
        super().showEvent(event)
        
        self._log_debug(f"showEvent被调用")
        self._log_debug(f"_auto_fill_pending: {hasattr(self, '_auto_fill_pending')}")
        self._log_debug(f"username: {self.username}, password: {'有' if self.password else '无'}")
        
        # 检查是否需要自动填充
        if hasattr(self, '_auto_fill_pending') and self._auto_fill_pending:
            self._auto_fill_pending = False
            
            # 如果有保存的登录信息，延迟填充
            if self.username and self.password:
                self._log_debug(f"窗口显示，准备自动填充: 用户名={self.username}")
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(300, self._fill_saved_credentials)
            else:
                self._log_debug(f"没有保存的登录信息，跳过自动填充")
    
    def _fill_saved_credentials(self):
        """填充保存的登录信息 - 只填充，不自动登录"""
        self._log_debug(f"尝试填充登录信息...")
        self._log_debug(f"当前用户名: {self.username}")
        
        # 检查输入框是否存在
        has_username = hasattr(self, 'login_username')
        has_password = hasattr(self, 'login_password')
        self._log_debug(f"输入框存在状态: login_username={has_username}, login_password={has_password}")
        
        if has_username and has_password:
            self._log_debug(f"找到输入框，开始填充...")
            self.login_username.setText(self.username)
            self.login_password.setText(self.password)
            self._log_debug(f"填充完成: 用户名={self.login_username.text()}")
            
            # 触发一次输入检查，确保登录按钮状态正确
            self.check_login_input()
        else:
            self._log_debug(f"输入框未找到，延迟重试...")
            # 如果输入框还未创建，延迟重试
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(300, self._fill_saved_credentials)



    def setup_styles(self):
        """设置界面样式"""
        # 使用utils.py中的统一样式应用函数
        apply_styles_to_dialog(self)
        
        # 确保标题和副标题使用正确的字体
        screen_width, screen_height = get_screen_size()
        title_font_size = max(16, int(screen_height * 0.022))
        subtitle_font_size = max(8, int(screen_height * 0.018))
        
        if hasattr(self, 'title_label') and self.title_label:
            title_font = QFont()
            title_font.setPointSize(title_font_size)
            title_font.setBold(True)
            title_font.setFamily('Microsoft YaHei')
            self.title_label.setFont(title_font)
            
        if hasattr(self, 'subtitle_label') and self.subtitle_label:
            subtitle_font = QFont()
            subtitle_font.setPointSize(subtitle_font_size)
            subtitle_font.setFamily('Microsoft YaHei')
            self.subtitle_label.setFont(subtitle_font)
    def update_subtitle(self, index):
        if index == 0:  # 登录标签页
            self.subtitle_label.setText("→1")
            # 按屏幕比例设置字体大小
            screen = QApplication.primaryScreen().geometry()
            subtitle_font_size = int(screen.height() * 0.018)  # 屏幕高度的1.8%
            self.subtitle_label.setStyleSheet(f"font-size: {subtitle_font_size}px; color: #262626; margin-bottom: 5px; font-family: 'Microsoft YaHei' !important;")  # 缩小字体并减少底部空白
        else:  # 注册标签页
            self.subtitle_label.setText("")
            self.subtitle_label.setStyleSheet("border: none;")

    def setup_login_tab(self):
        """设置登录表单 - 使用现代化设计风格"""
        # 获取屏幕尺寸
        screen_width, screen_height = get_screen_size()
        
        # 计算动态尺寸
        card_width = int(screen_width * 0.35)  # 减小卡片宽度，从0.45减少到0.35，使界面更紧凑
        card_height = int(screen_height * 0.45)  # 卡片高度
        margin = int(screen_height * 0.02)  # 边距
        font_size = max(10, int(screen_height * 0.02))  # 字体大小
        input_height = int(screen_height * 0.06)  # 增加输入框高度，从0.05增加到0.06
        button_height = int(screen_height * 0.05)  # 按钮高度
        button_font_size = max(9, int(screen_height * 0.018))  # 按钮字体大小
        
        # 创建主容器，使用渐变背景
        main_container = QWidget()
        main_container.setObjectName("main_container")
        main_container.setStyleSheet("""
            QWidget#main_container {
                background-color: #007AFF;
                border-radius: 0px;
            }
        """)
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建顶部装饰区域 - macOS渐变风格
        top_decoration = QFrame()
        top_decoration.setFixedHeight(int(card_height * 0.25))
        top_decoration.setStyleSheet(f"""
            QFrame {{
                background: {PRIMARY_GRADIENT};
                border-radius: 0px;
            }}
        """)
        
        # 在顶部装饰区域添加应用图标和标题
        top_layout = QVBoxLayout(top_decoration)
        top_layout.setContentsMargins(0, int(card_height * 0.05), 0, 0)
        top_layout.setSpacing(5)
        top_layout.setAlignment(Qt.AlignCenter)
        
        # 应用图标
        app_icon = QLabel("🏢")
        app_icon.setAlignment(Qt.AlignCenter)
        # 按屏幕比例设置字体大小
        app_icon_font_size = int(screen_height * 0.05)  # 屏幕高度的5%
        app_icon.setStyleSheet(f"font-size: {app_icon_font_size}px; color: white;")
        top_layout.addWidget(app_icon)
        
        # 应用名称
        app_name = QLabel("办公操作复刻大师")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {int(font_size * 1.2)}px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }}
        """)
        top_layout.addWidget(app_name)
        
        main_layout.addWidget(top_decoration)
        
        # 创建表单区域
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0px;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(int(card_width * 0.08), int(card_height * 0.04), int(card_width * 0.08), int(card_height * 0.06))
        form_layout.setSpacing(0)  # 与注册界面保持一致，间距为0
        
        # 移除不必要的拉伸因子，避免顶部空白
        # form_layout.addStretch()
        
        # 欢迎信息 - macOS风格
        welcome_label = QLabel("欢迎回来")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT};
                font-size: {int(font_size * 1.1)}px;
                font-weight: bold;
                margin-bottom: 10px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
        """)
        form_layout.addWidget(welcome_label)
        
        # 用户名输入区域
        username_section = self._create_modern_input_section("用户名", "请输入用户名", "👨", font_size, input_height, card_width)
        form_layout.addWidget(username_section["container"])
        self.login_username = username_section["input"]
        
        # 密码输入区域
        password_section = self._create_modern_password_section("密码", "请输入密码", "🔒", font_size, input_height, button_font_size, show_checkbox=True, card_width=card_width)
        form_layout.addWidget(password_section["container"])
        self.login_password = password_section["input"]
        self.show_password_checkbox = password_section["checkbox"]
        
        # 记住我选项
        remember_container = QWidget()
        remember_layout = QHBoxLayout(remember_container)
        remember_layout.setContentsMargins(0, 0, 0, 0)
        
        self.remember_me = QCheckBox()
        self.remember_me.setChecked(True)
        self.remember_me.setStyleSheet(f"""
            QCheckBox {{
                spacing: 8px;
                color: {TEXT};
                font-size: {button_font_size}px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {BORDER};
                background-color: {BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ACCENT};
                border-color: {ACCENT};
            }}
        """)
        remember_layout.addWidget(self.remember_me)
        
        remember_label = QLabel("记住我")
        remember_label.setStyleSheet(f"color: #595959; font-size: {button_font_size}px; font-family: 'Microsoft YaHei';")
        remember_layout.addWidget(remember_label)
        remember_layout.addStretch()

        # 忘记密码链接 - macOS强调色
        forgot_link = QLabel(f"<a href='#' style='color: {ACCENT}; text-decoration: none;'>忘记密码?</a>")
        forgot_link.setCursor(Qt.PointingHandCursor)
        forgot_link.setStyleSheet(f"font-size: {button_font_size}px; font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;")
        forgot_link.linkActivated.connect(self.handle_forgot_password)
        remember_layout.addWidget(forgot_link)
        
        form_layout.addWidget(remember_container)
        
        # 登录按钮 - macOS渐变风格
        login_button = QPushButton("登 录")
        login_button.setFixedHeight(button_height)
        login_button.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY_GRADIENT};
                color: white;
                border: none;
                border-radius: {int(button_height/2)}px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #007AFF;
            }}
            QPushButton:pressed {{
                background-color: #007AFF;
            }}
            QPushButton:disabled {{
                background-color: {BORDER};
                color: {MUTED};
            }}
        """)
        login_button.clicked.connect(self.handle_login)
        form_layout.addWidget(login_button)
        self.login_btn = login_button  # 保存登录按钮引用
        
        # 注册链接 - 统一蓝色风格
        register_container = QWidget()
        register_layout = QHBoxLayout(register_container)
        register_layout.setContentsMargins(0, 0, 0, 0)

        register_label = QLabel("还没有账号?")
        register_label.setStyleSheet(f"color: {TEXT}; font-size: {button_font_size}px; font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;")
        register_layout.addWidget(register_label)

        register_link = QLabel(f"<a href='#' style='color: {ACCENT}; text-decoration: none; font-weight: bold;'>立即注册</a>")
        register_link.setCursor(Qt.PointingHandCursor)
        register_link.setStyleSheet(f"font-size: {button_font_size}px; font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;")
        register_link.linkActivated.connect(self.show_register_page)
        register_layout.addWidget(register_link)
        
        register_layout.addStretch()
        form_layout.addWidget(register_container)
        
        main_layout.addWidget(form_container)
        
        # 创建主布局并添加卡片
        self.login_layout = QVBoxLayout()
        self.login_layout.setContentsMargins(0, 0, 0, 0)
        self.login_layout.setSpacing(0)
        self.login_layout.addWidget(main_container)
        
        # 移除不必要的拉伸因子，避免底部空白
        # self.login_layout.addStretch()
        
        # 连接信号
        self.login_username.textChanged.connect(self.check_login_input)
        self.login_password.textChanged.connect(self.check_login_input)
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        self.toggle_password_visibility(True)  # 默认显示密码

        # 初始化登录按钮状态
        self.check_login_input()

    def adjust_window_height(self):
        """根据当前页面调整窗口高度"""
        # 获取屏幕尺寸
        screen_width, screen_height = get_screen_size()
        
        # 计算动态基础高度 - 减小各页面高度比例
        login_base_height = int(screen_height * 0.55)  # 登录页基础高度为屏幕高度的55%
        register_base_height = int(screen_height * 0.55)  # 注册页基础高度为屏幕高度的55%
        forgot_base_height = int(screen_height * 0.55)  # 忘记密码页基础高度为屏幕高度的55%
        
        # 根据当前可见页面设置合适的高度
        if self.login_tab.isVisible():
            base_height = login_base_height
        elif self.register_tab.isVisible():
            base_height = register_base_height
        elif self.forgot_password_tab.isVisible():
            base_height = forgot_base_height
        else:
            base_height = login_base_height
            
        # 获取当前窗口宽度并应用新的高度
        current_width = self.width()
        self.resize(current_width, base_height)


    def toggle_password_visibility(self, checked):
        """切换登录密码可见性"""
        if checked:
            self.login_password.setEchoMode(QLineEdit.Normal)
        else:
            self.login_password.setEchoMode(QLineEdit.Password)

    def check_login_input(self):
        """检查登录输入是否为空，决定登录按钮状态"""
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()
        self.login_btn.setEnabled(bool(username and password))

    def handle_register(self):
        """处理注册逻辑"""
        username = self.register_username.text().strip()
        password = self.register_password.text().strip()
        confirm_password = self.register_confirm.text().strip()
        email = self.register_email.text().strip()
        verification_code = self.verification_code_input.text().strip()

        # 基本验证
        if not username:
            StyledMessageDialog(self, title="警告", text="请输入用户名", msg_type="warning", buttons="ok").exec_()
            return

        if not password:
            StyledMessageDialog(self, title="警告", text="请输入密码", msg_type="warning", buttons="ok").exec_()
            return

        if password != confirm_password:
            StyledMessageDialog(self, title="警告", text="两次输入的密码不一致", msg_type="warning", buttons="ok").exec_()
            return

        if not email:
            StyledMessageDialog(self, title="警告", text="请输入邮箱", msg_type="warning", buttons="ok").exec_()
            return

        if not is_valid_email(email):
            StyledMessageDialog(self, title="警告", text="请输入有效的邮箱地址", msg_type="warning", buttons="ok").exec_()
            return

        # 密码强度检查
        strength_text, _ = self._calculate_password_strength(password)
        if strength_text == "弱":
            reply = StyledMessageDialog(self, title="密码强度提示", text="您的密码强度较弱，建议使用包含大小写字母、数字和特殊字符的密码。\n是否继续注册？", msg_type="question", buttons="yes_no").exec_()
            if dlg.get_result() == StyledMessageDialog.NO:
                return

        # 验证码检查（如果需要）
        if not self.skip_verification and not verification_code:
            StyledMessageDialog(self, title="警告", text="请输入验证码", msg_type="warning", buttons="ok").exec_()
            return

        # 执行注册
        success, message = self.login_manager.register(username, password, email, verification_code)
        
        if success:
            StyledMessageDialog(self, title="注册成功", text=message, msg_type="information", buttons="ok").exec_()
            # 保存注册信息以便登录时自动填充
            self.registered_username = username
            self.registered_password = password
            # 跳转到登录页面
            self.show_login_page()
        else:
            StyledMessageDialog(self, title="注册失败", text=message, msg_type="warning", buttons="ok").exec_()

    def toggle_register_password_visibility(self, checked):
        """切换注册密码可见性"""
        if checked:
            self.register_password.setEchoMode(QLineEdit.Normal)
            self.register_confirm.setEchoMode(QLineEdit.Normal)
        else:
            self.register_password.setEchoMode(QLineEdit.Password)
            self.register_confirm.setEchoMode(QLineEdit.Password)

    def toggle_both_password_visibility(self, checked):
        """同时切换登录和注册页面的密码可见性"""
        # 切换登录页面密码可见性
        if hasattr(self, 'login_password'):
            self.login_password.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        
        # 切换注册页面密码可见性
        if hasattr(self, 'register_password') and hasattr(self, 'register_confirm'):
            self.register_password.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
            self.register_confirm.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        
        # 切换忘记密码页面密码可见性
        if hasattr(self, 'forgot_new_password'):
            self.forgot_new_password.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
            self.forgot_confirm_password.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def toggle_forgot_password_visibility(self, checked):
        """切换忘记密码页面的密码可见性"""
        if checked:
            self.forgot_new_password.setEchoMode(QLineEdit.Normal)
            self.forgot_confirm_password.setEchoMode(QLineEdit.Normal)
        else:
            self.forgot_new_password.setEchoMode(QLineEdit.Password)
            self.forgot_confirm_password.setEchoMode(QLineEdit.Password)

    def handle_login(self):
        """处理登录逻辑"""
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()

        # 同步执行登录操作
        success, message = self.login_manager.login(username, password)
        
        # 记住我状态单独处理 - 在on_login_complete之前保存，避免对话框关闭后无法保存
        if self.remember_me.isChecked() and success:
            # 使用LoginManager的save_login_credentials方法保存登录信息
            self.login_manager.save_login_credentials(username, password)
        
        self.on_login_complete(success, message)

    def move_to_center(self):
        """将窗口移动到屏幕中央"""
        # 获取屏幕几何信息
        screen_geometry = QApplication.desktop().screenGeometry()
        # 获取窗口几何信息
        window_geometry = self.frameGeometry()
        # 计算屏幕中心点
        center_point = screen_geometry.center()
        # 移动窗口几何中心到屏幕中心
        window_geometry.moveCenter(center_point)
        # 移动窗口到计算出的位置
        self.move(window_geometry.topLeft())

    def show_register_page(self):
        """显示注册页面"""
        # 延迟初始化注册页面
        if not self._register_tab_initialized:
            self.setup_register_tab()
            self.register_tab.setLayout(self.register_layout)
            self._register_tab_initialized = True
        
        # 隐藏登录页面，显示注册页面
        self.login_tab.hide()
        self.register_tab.show()
        # 设置窗口标题
        self.setWindowTitle("注册")
        # 调用统一的窗口高度调整方法
        self.adjust_window_height()
        # 确保窗口居中显示
        self.move_to_center()
        # 强制刷新界面
        self.register_tab.update()
        self.update()

    def on_login_complete(self, success, message):
        """登录完成后的回调"""
        if success:
            self.current_user = message
            self.login_success.emit(message)
            self.accept()  # 自动关闭登录对话框
        else:
            # 显示来自服务器的实际错误信息
            StyledMessageDialog(self, title="登录失败", text=message, msg_type="warning", buttons="ok").exec_()

    def get_current_user(self):
        """获取当前用户名

        Returns:
            str: 当前用户名
        """
        return self.current_user

    def handle_get_verification_code(self):
        """处理获取验证码"""
        email = self.register_email.text().strip()

        if not email:
            StyledMessageDialog(self, title="警告", text="请输入邮箱地址", msg_type="warning", buttons="ok").exec_()
            return

        if not is_valid_email(email):
            StyledMessageDialog(self, title="警告", text="请输入有效的邮箱地址", msg_type="warning", buttons="ok").exec_()
            return

        # 防止重复点击
        if hasattr(self, 'register_timer') and self.register_timer and self.register_timer.isActive():
            return

        # 禁用按钮并显示加载状态
        self.get_code_button.setEnabled(False)
        self.get_code_button.setText("发送中...")

        # 创建工作线程
        self.email_thread = EmailThread(email, self.login_manager)
        self.email_thread.finished.connect(self.on_register_email_sent)
        self.email_thread.start()

    def on_register_email_sent(self, success, msg, email, code):
        """处理注册页面验证码发送结果"""
        if success:
            if code:
                # 显示验证码在对话框中
                StyledMessageDialog(self, title="验证码已生成", text=f"验证码: {code}\n\n验证码有效期为10分钟，请及时使用。", msg_type="information", buttons="ok").exec_()
                # 自动填充验证码
                self.verification_code_input.setText(code)
            else:
                StyledMessageDialog(self, title="验证码已发送", text="验证码已成功发送到您的邮箱，请查收", msg_type="information", buttons="ok").exec_()
            # 设置60秒倒计时
            self.countdown = 60
            self.register_timer = QTimer(self)
            self.register_timer.timeout.connect(self.update_register_countdown)
            self.register_timer.start(1000)  # 每秒触发一次
            self.get_code_button.setText(f"重新发送({self.countdown})")
        else:
            StyledMessageDialog(self, title="发送失败", text=msg, msg_type="warning", buttons="ok").exec_()
            self.get_code_button.setEnabled(True)
            self.get_code_button.setText("获取验证码")

    def update_countdown(self, button, timer, countdown):
        """通用倒计时更新函数"""
        countdown -= 1
        if countdown <= 0:
            timer.stop()
            button.setText("获取验证码")
            button.setEnabled(True)
        else:
            button.setText(f"重新发送({countdown})")
        return countdown

    def update_register_countdown(self):
        """更新注册页面倒计时"""
        self.countdown = self.update_countdown(self.get_code_button, self.register_timer, self.countdown)

    def update_forgot_countdown(self):
        """更新忘记密码页面的倒计时显示"""
        self.forgot_countdown = self.update_countdown(self.forgot_get_code_button, self.forgot_timer, self.forgot_countdown)

    def show_privacy_policy(self):
        """显示隐私条款详细内容"""
        privacy_text = """详细隐私条款内容：
1. 本软件仅收集必要的用户信息用于账号验证
2. 所有用户数据将严格保密，不会泄露给第三方
3. 用户操作记录仅存储在本地，不会上传至服务器
4. 开发者承诺保护用户隐私安全
"""
        StyledMessageDialog(self, title="隐私条款", text=privacy_text, msg_type="information", buttons="ok").exec_()

    def handle_forgot_password(self):
        """处理忘记密码逻辑 - 直接跳转到忘记密码页面"""
        self.show_forgot_password()

    def handle_forgot_get_code(self):
        """处理忘记密码时的验证码获取"""
        email = self.forgot_email_input.text().strip()

        if not email:
            StyledMessageDialog(self, title="警告", text="请输入注册邮箱", msg_type="warning", buttons="ok").exec_()
            self.forgot_email_input.setFocus()
            return

        if not is_valid_email(email):
            QMessageBox.warning(self, "警告", "请输入有效的邮箱地址")
            self.forgot_email_input.setFocus()
            self.forgot_email_input.selectAll()
            return

        # 防止重复点击
        if hasattr(self, 'forgot_timer') and self.forgot_timer and self.forgot_timer.isActive():
            return

        # 禁用按钮并显示加载状态
        self.forgot_get_code_button.setEnabled(False)
        self.forgot_get_code_button.setText("发送中...")

        # 创建工作线程
        self.email_thread = EmailThread(email, self.login_manager)
        self.email_thread.finished.connect(self.on_email_sent)
        self.email_thread.start()

    def on_email_sent(self, success, msg, email, code):
        """邮件发送完成后的回调函数"""
        if success:
            if code:
                # 显示验证码在对话框中
                QMessageBox.information(self, "验证码已生成", f"验证码: {code}\n\n验证码有效期为10分钟，请及时使用。")
                # 自动填充验证码
                self.forgot_code_input.setText(code)
            else:
                StyledMessageDialog(self, title="发送成功", text="验证码已发送至您的邮箱，请查收", msg_type="information", buttons="ok").exec_()
            
            # 设置60秒倒计时
            self.forgot_countdown = 60
            self.forgot_timer = QTimer(self)
            self.forgot_timer.timeout.connect(self.update_forgot_countdown)
            self.forgot_timer.start(1000)  # 每秒触发一次
            self.forgot_get_code_button.setText(f"重新发送({self.forgot_countdown})")
        else:
            QMessageBox.warning(self, "发送失败", msg)
            self.forgot_get_code_button.setEnabled(True)
            self.forgot_get_code_button.setText("获取验证码")
            return

    def show_login_page(self):
        """显示登录页面"""
        # 隐藏注册页面和忘记密码页面，显示登录页面
        self.register_tab.hide()
        self.forgot_password_tab.hide()
        self.login_tab.show()
        # 设置窗口标题
        self.setWindowTitle("办公操作复刻大师 - 登录")
        self.adjust_window_height()

        # 如果是从注册页面跳转过来的，自动填充用户名和密码
        if hasattr(self, 'registered_username') and hasattr(self, 'registered_password'):
            self.login_username.setText(self.registered_username)
            self.login_password.setText(self.registered_password)

    def _calculate_password_strength(self, password):
        """计算密码强度，返回强度文本和颜色"""
        if not password:
            return "", ""
            
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        # 扩展特殊字符集合
        has_special = any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?/~`' for c in password)
        
        # 简化的密码强度判断逻辑
        # 弱：全是小写字母或全是数字或小写字母+数字
        # 中：包含大写字母
        # 强：包含特殊字符
        
        if has_special:
            return "强", "#6bcf7f"
        elif has_upper:
            return "中", "#ffd93d"
        else:
            return "弱", "#FF453A"

    def check_password_strength(self):
        """检查密码强度并更新标签"""
        # 根据当前活动的页面选择相应的密码输入框和标签
        if hasattr(self, 'forgot_password_tab') and self.forgot_password_tab.isVisible():
            # 忘记密码页面
            password = self.forgot_new_password.text()
            strength_label = self.forgot_pwd_strength_label
        else:
            # 注册页面
            password = self.register_password.text()
            strength_label = self.register_pwd_strength_label
            
        strength, color = self._calculate_password_strength(password)
        strength_label.setText(f"密码强度: <span style='color: {color}; font-weight: bold;'>{strength}</span>")

    def show_forgot_password(self):
        """显示忘记密码页面"""
        # 延迟初始化找回密码页面
        if not self._forgot_password_tab_initialized:
            self.setup_forgot_password_tab()
            self.forgot_password_tab.setLayout(self.forgot_password_layout)
            self._forgot_password_tab_initialized = True
        
        self.login_tab.hide()
        self.register_tab.hide()
        self.forgot_password_tab.show()
        self.setWindowTitle("办公操作复刻大师 - 找回密码")
        self.adjust_window_height()

    def setup_forgot_password_tab(self):
        """设置忘记密码表单 - 使用与登录界面一致的macOS渐变风格"""
        screen_width, screen_height = get_screen_size()
        
        card_width = int(screen_width * 0.35)
        card_height = int(screen_height * 0.55)
        margin = int(screen_height * 0.02)
        font_size = max(10, int(screen_height * 0.02))
        input_height = int(screen_height * 0.06)
        button_height = int(screen_height * 0.05)
        button_font_size = max(9, int(screen_height * 0.018))
        
        main_container = QWidget()
        main_container.setObjectName("main_container")
        main_container.setStyleSheet("""
            QWidget#main_container {
                background-color: #007AFF;
                border-radius: 0px;
            }
        """)
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        top_decoration = QFrame()
        top_decoration.setFixedHeight(int(card_height * 0.25))
        top_decoration.setStyleSheet(f"""
            QFrame {{
                background: {PRIMARY_GRADIENT};
                border-radius: 0px;
            }}
        """)
        
        top_layout = QVBoxLayout(top_decoration)
        top_layout.setContentsMargins(0, int(card_height * 0.05), 0, 0)
        top_layout.setSpacing(5)
        top_layout.setAlignment(Qt.AlignCenter)
        
        app_icon = QLabel("🔑")
        app_icon.setAlignment(Qt.AlignCenter)
        app_icon_font_size = int(screen_height * 0.05)
        app_icon.setStyleSheet(f"font-size: {app_icon_font_size}px; color: white;")
        top_layout.addWidget(app_icon)
        
        app_name = QLabel("找回密码")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {int(font_size * 1.2)}px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }}
        """)
        top_layout.addWidget(app_name)
        
        main_layout.addWidget(top_decoration)
        
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0px;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(int(card_width * 0.08), int(card_height * 0.04), int(card_width * 0.08), int(card_height * 0.06))
        form_layout.setSpacing(0)
        
        welcome_label = QLabel("重置您的密码")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT};
                font-size: {int(font_size * 1.1)}px;
                font-weight: bold;
                margin-bottom: 10px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
        """)
        form_layout.addWidget(welcome_label)
        
        email_section = self._create_modern_input_section("邮箱", "请输入注册时使用的邮箱", "✉️", font_size, input_height, card_width)
        form_layout.addWidget(email_section["container"])
        self.forgot_email_input = email_section["input"]
        
        code_section = self._create_register_code_section("验证码", "请输入验证码", "🔐", font_size, input_height, screen_width, button_font_size)
        form_layout.addWidget(code_section["container"])
        self.forgot_code_input = code_section["input"]
        self.forgot_get_code_button = code_section["button"]
        
        new_pwd_section = self._create_modern_password_section("新密码", "请输入新密码（至少8位）", "🔐", font_size, input_height, button_font_size, show_checkbox=True, card_width=card_width)
        form_layout.addWidget(new_pwd_section["container"])
        self.forgot_new_password = new_pwd_section["input"]
        self.forgot_show_password_checkbox = new_pwd_section["checkbox"]
        
        confirm_pwd_section = self._create_modern_input_section("确认密码", "请再次输入新密码", "🔄", font_size, input_height, card_width)
        form_layout.addWidget(confirm_pwd_section["container"])
        self.forgot_confirm_password = confirm_pwd_section["input"]
        self.forgot_confirm_password.setEchoMode(QLineEdit.Password)
        
        self.forgot_pwd_strength_label = QLabel()
        self.forgot_pwd_strength_label.setStyleSheet(f"font-size: {max(9, int(screen_height * 0.012))}px; margin: 0px; padding: 0px; color: #262626;")
        form_layout.addWidget(self.forgot_pwd_strength_label)
        
        button_section = self._create_forgot_password_button_section(screen_width, screen_height, input_height, button_font_size)
        form_layout.addWidget(button_section["container"])
        
        main_layout.addWidget(form_container)
        
        self.forgot_password_layout = QVBoxLayout()
        self.forgot_password_layout.setContentsMargins(0, 30, 0, 30)
        self.forgot_password_layout.setSpacing(0)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        h_layout.addStretch(1)
        h_layout.addWidget(main_container)
        h_layout.addStretch(1)
        
        self.forgot_password_layout.addLayout(h_layout)

        # 连接信号
        self.forgot_new_password.textChanged.connect(self.check_password_strength)
        self.forgot_confirm_password.textChanged.connect(self.check_password_strength)
        
        # 设置布局
        self.forgot_password_tab.setLayout(self.forgot_password_layout)
    
    def _create_modern_input_section(self, label_text, placeholder_text, icon, font_size, input_height, card_width):
        """创建现代化的输入区域"""
        # 创建容器 - 移除灰色背景和边框
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)  # 与注册界面保持一致
        container_layout.setSpacing(2)  # 与注册界面保持一致

        # 创建标签 - macOS风格
        label = QLabel(label_text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT};
                font-size: {int(font_size * 0.9)}px;
                font-weight: 600;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                margin-bottom: 5px;
                padding-top: 5px;
            }}
        """)
        container_layout.addWidget(label)
        
        # 创建输入框
        input_widget = self.create_styled_input(
            placeholder=placeholder_text,
            icon=icon,
            height=input_height,
            font_size=font_size,
            width=int(card_width * 0.8)  # 使用卡片宽度的80%作为输入框宽度，确保在窗口缩小时有足够空间
        )
        
        # 添加输入框的容器到布局
        container_layout.addWidget(input_widget._icon_container)
        
        return {
            "container": container,
            "input": input_widget
        }
    
    def _create_modern_password_section(self, label_text, placeholder_text, icon, font_size, input_height, button_font_size, show_checkbox=True, card_width=None):
        """创建现代化的密码输入区域"""
        # 创建容器 - 移除灰色背景和边框
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)  # 与注册界面保持一致
        container_layout.setSpacing(0)  # 与注册界面保持一致

        # 创建标签 - macOS风格
        label = QLabel(label_text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT};
                font-size: {int(font_size * 0.9)}px;
                font-weight: 600;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                margin-bottom: 5px;
                padding-top: 5px;
            }}
        """)
        container_layout.addWidget(label)
        
        # 创建输入框容器
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(15)  # 大幅增加输入框和复选框之间的间距
        
        # 创建密码输入框
        password_input = self.create_styled_input(
            placeholder=placeholder_text,
            icon=icon,
            height=input_height,
            font_size=font_size,
            width=int(card_width * 0.8) if card_width else int(input_height * 6)  # 使用卡片宽度的80%或默认值
        )
        password_input.setEchoMode(QLineEdit.Password)
        
        # 添加输入框的容器到布局
        input_layout.addWidget(password_input._icon_container)
        
        # 创建显示密码复选框
        show_password_checkbox = QCheckBox("显示")
        show_password_checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 5px;
                color: {TEXT};
                font-size: {button_font_size}px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid {BORDER};
                background-color: {BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ACCENT};
                border-color: {ACCENT};
            }}
        """)
        input_layout.addWidget(show_password_checkbox)
        
        container_layout.addWidget(input_container)
        
        return {
            "container": container,
            "input": password_input,
            "checkbox": show_password_checkbox
        }
    
    def _create_login_input_section(self, label_text, placeholder_text, icon, font_size, input_height, echo_mode=QLineEdit.Normal):
        """创建登录界面输入区域"""
        section_container = QWidget()
        section_layout = QVBoxLayout(section_container)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(16)  # 增加标签和输入框之间的间距，使界面更长

        # 标签 - 调整边距，确保不被遮挡
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {TEXT}; font-size: {font_size + 2}px; font-weight: bold; margin-bottom: 4px; padding-top: 2px; font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;")
        label.setContentsMargins(0, 2, 0, 0)  # 保持上边距
        section_layout.addWidget(label)
        
        # 输入框容器
        input_container, input_field = self.create_styled_input(placeholder_text, echo_mode, icon)
        input_field.setFixedHeight(input_height)
        # 不再覆盖样式，使用create_styled_input中已设置的样式
        section_layout.addWidget(input_container)
        
        return {
            "container": section_container,
            "input": input_field
        }
    
    def _create_login_password_section(self, label_text, placeholder_text, icon, font_size, input_height, button_font_size, show_checkbox=False):
        """创建登录界面密码输入区域"""
        section_container = QWidget()
        section_layout = QVBoxLayout(section_container)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(8)  # 统一标签和输入框之间的间距

        # 标签 - 进一步减小边距和字体大小
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {TEXT}; font-size: {font_size + 1}px; font-weight: bold; margin-bottom: 1px; padding: 1px 0; font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;")
        label.setContentsMargins(0, 1, 0, 0)  # 进一步减少边距
        section_layout.addWidget(label)
        
        # 输入框和复选框容器
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(4)  # 极小输入框和复选框之间的间距
        
        # 密码输入框
        pwd_input_container, input_field = self.create_styled_input(placeholder_text, QLineEdit.Password, icon)
        input_field.setFixedHeight(input_height)
        # 不再覆盖样式，使用create_styled_input中已设置的样式
        input_layout.addWidget(pwd_input_container)
        
        # 显示密码复选框
        checkbox = None
        if show_checkbox:
            checkbox = QCheckBox("显示密码")
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: #262626;
                    font-size: {button_font_size}px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                }}
                QCheckBox::indicator:unchecked {{
                    border: 1px solid white;
                    background-color: white;
                    border-radius: 3px;
                }}
                QCheckBox::indicator:checked {{
                    border: 1px solid #1890ff;
                    background-color: #1890ff;
                    border-radius: 3px;
                }}
            """)
            input_layout.addWidget(checkbox)
        
        section_layout.addWidget(input_container)
        
        return {
            "container": section_container,
            "input": input_field,
            "checkbox": checkbox
        }
    
    def _create_login_button_section(self, screen_width, screen_height, button_height, font_size):
        """创建登录界面按钮区域"""
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)  # 减小按钮之间的间距

        # 登录按钮 - macOS渐变风格
        login_button = self.create_button(
            "登录",
            f"background: {PRIMARY_GRADIENT}; color: white; font-size: {font_size}px;",
            min_width=int(screen_width * 0.12),
            min_height=button_height,
            clicked_handler=self.handle_login
        )
        login_button.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY_GRADIENT};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {font_size}px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #007AFF;
            }}
            QPushButton:pressed {{
                background-color: #007AFF;
            }}
        """)

        # 注册按钮 - macOS渐变风格
        register_button = self.create_button(
            "注册",
            f"background: {PRIMARY_GRADIENT}; color: white; font-size: {font_size}px;",
            min_width=int(screen_width * 0.12),
            min_height=button_height,
            clicked_handler=self.show_register_page
        )
        register_button.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY_GRADIENT};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {font_size}px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #007AFF;
            }}
            QPushButton:pressed {{
                background-color: #007AFF;
            }}
        """)
        
        button_layout.addWidget(login_button)
        button_layout.addStretch()
        button_layout.addWidget(register_button)
        
        return {
            "container": button_container,
            "login_button": login_button,
            "register_button": register_button
        }

    def _create_input_section(self, label_text, placeholder_text, icon, font_size, input_height, echo_mode=QLineEdit.Normal):
        """创建输入区域 - macOS风格"""
        section_container = QWidget()
        section_layout = QVBoxLayout(section_container)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(2)  # 减小标签和输入框之间的间距

        # 标签 - 减少上边距，确保不被遮挡
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {TEXT}; font-size: {font_size - 2}px; font-weight: bold; margin: 0px; padding: 0px; font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;")
        label.setContentsMargins(0, 0, 0, 0)  # 减小标签边距
        section_layout.addWidget(label)
        
        # 使用create_styled_input创建输入框
        input_field = self.create_styled_input(
            placeholder=placeholder_text,
            icon=icon,
            height=input_height,
            font_size=font_size
        )
        input_field.setEchoMode(echo_mode)
        
        # 添加输入框的容器到布局
        section_layout.addWidget(input_field._icon_container)
        
        return {
            "container": section_container,
            "input": input_field
        }
    
    def _create_code_section(self, label_text, placeholder_text, icon, font_size, input_height, screen_width, button_font_size):
        """创建验证码输入区域 - macOS风格"""
        section_container = QWidget()
        section_layout = QVBoxLayout(section_container)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(12)  # 统一标签和输入框之间的间距

        # 标签 - 增加上边距，确保不被遮挡
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {TEXT}; font-size: {font_size + 2}px; font-weight: bold; margin-bottom: 3px; padding-top: 2px; font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;")
        label.setContentsMargins(0, 5, 0, 0)  # 减小上边距
        section_layout.addWidget(label)
        
        # 输入框和按钮容器
        input_button_container = QWidget()
        input_button_layout = QHBoxLayout(input_button_container)
        input_button_layout.setContentsMargins(0, 0, 0, 0)
        input_button_layout.setSpacing(8)  # 减小输入框和按钮之间的间距
        
        # 使用create_styled_input创建输入框
        input_field = self.create_styled_input(
            placeholder=placeholder_text,
            icon=icon,
            height=input_height,
            font_size=font_size
        )
        
        # 添加输入框的容器到布局
        input_button_layout.addWidget(input_field._icon_container)
        
        # 获取验证码按钮 - macOS渐变风格
        get_code_button = self.create_button("获取验证码",
                                           f"background: {PRIMARY_GRADIENT}; color: white; font-size: {button_font_size}px;",
                                           min_width=int(screen_width * 0.08),
                                           min_height=input_height,
                                           clicked_handler=self.handle_forgot_get_code)
        get_code_button.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY_GRADIENT};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #007AFF;
            }}
            QPushButton:pressed {{
                background-color: #007AFF;
            }}
        """)
        input_button_layout.addWidget(get_code_button)
        
        section_layout.addWidget(input_button_container)
        
        return {
            "container": section_container,
            "input": input_field,
            "button": get_code_button
        }
    
    def _create_password_section(self, label_text, placeholder_text, icon, font_size, input_height, screen_width, button_font_size, show_checkbox=False):
        """创建密码输入区域 - 与登录界面保持一致的样式"""
        section_container = QWidget()
        section_layout = QVBoxLayout(section_container)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(12)  # 统一标签和输入框之间的间距
        
        # 标签 - 增加上边距，确保不被遮挡
        label = QLabel(label_text)
        label.setStyleSheet(f"color: #262626; font-size: {font_size + 2}px; font-weight: bold; margin-bottom: 5px; padding-top: 5px;")
        label.setContentsMargins(0, 10, 0, 0)  # 增加上边距
        section_layout.addWidget(label)
        
        # 输入框和复选框容器
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)  # 减少输入框和复选框之间的间距
        
        # 使用create_styled_input创建密码输入框
        input_field = self.create_styled_input(
            placeholder=placeholder_text,
            icon=icon,
            height=input_height,
            font_size=font_size
        )
        input_field.setEchoMode(QLineEdit.Password)
        
        # 添加输入框的容器到布局
        input_layout.addWidget(input_field._icon_container)
        
        # 显示密码复选框
        checkbox = None
        if show_checkbox:
            checkbox = QCheckBox("显示密码")
            checkbox.stateChanged.connect(self.toggle_forgot_password_visibility)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: #262626;
                    font-size: {button_font_size}px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                }}
                QCheckBox::indicator:unchecked {{
                    border: 1px solid white;
                    background-color: white;
                    border-radius: 3px;
                }}
                QCheckBox::indicator:checked {{
                    border: 1px solid #1890ff;
                    background-color: #1890ff;
                    border-radius: 3px;
                }}
            """)
            input_layout.addWidget(checkbox)
        
        section_layout.addWidget(input_container)
        
        return {
            "container": section_container,
            "input": input_field,
            "checkbox": checkbox
        }
    
    def _create_button_section(self, screen_width, screen_height, button_height, font_size):
        """创建按钮区域 - 与登录界面保持一致的样式"""
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15)
        
        # 返回登录按钮
        back_button = self.create_button(
            "返回登录",
            f"background-color: #1890ff; color: white; font-size: {font_size}px;",
            min_width=int(screen_width * 0.12),
            min_height=button_height,
            clicked_handler=self.show_login_page
        )
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QPushButton:pressed {{
                background-color: #096dd9;
            }}
        """)
        
        # 重置密码按钮
        reset_button = self.create_button(
            "重置密码",
            f"background-color: #1890ff; color: white; font-size: {font_size}px;",
            min_width=int(screen_width * 0.12),
            min_height=button_height,
            clicked_handler=self.handle_reset_password
        )
        reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QPushButton:pressed {{
                background-color: #096dd9;
            }}
        """)
        
        button_layout.addWidget(back_button)
        button_layout.addStretch()
        button_layout.addWidget(reset_button)
        
        return {
            "container": button_container,
            "back_button": back_button,
            "reset_button": reset_button
        }

    def setup_register_tab(self):
        """设置注册表单 - 使用与登录界面一致的macOS渐变风格"""
        screen_width, screen_height = get_screen_size()
        
        card_width = int(screen_width * 0.35)
        card_height = int(screen_height * 0.55)
        margin = int(screen_height * 0.02)
        font_size = max(10, int(screen_height * 0.02))
        input_height = int(screen_height * 0.06)
        button_height = int(screen_height * 0.05)
        button_font_size = max(9, int(screen_height * 0.018))
        
        main_container = QWidget()
        main_container.setObjectName("main_container")
        main_container.setStyleSheet("""
            QWidget#main_container {
                background-color: #007AFF;
                border-radius: 0px;
            }
        """)
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        top_decoration = QFrame()
        top_decoration.setFixedHeight(int(card_height * 0.25))
        top_decoration.setStyleSheet(f"""
            QFrame {{
                background: {PRIMARY_GRADIENT};
                border-radius: 0px;
            }}
        """)
        
        top_layout = QVBoxLayout(top_decoration)
        top_layout.setContentsMargins(0, int(card_height * 0.05), 0, 0)
        top_layout.setSpacing(5)
        top_layout.setAlignment(Qt.AlignCenter)
        
        app_icon = QLabel("📝")
        app_icon.setAlignment(Qt.AlignCenter)
        app_icon_font_size = int(screen_height * 0.05)
        app_icon.setStyleSheet(f"font-size: {app_icon_font_size}px; color: white;")
        top_layout.addWidget(app_icon)
        
        app_name = QLabel("用户注册")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {int(font_size * 1.2)}px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }}
        """)
        top_layout.addWidget(app_name)
        
        main_layout.addWidget(top_decoration)
        
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0px;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(int(card_width * 0.08), int(card_height * 0.04), int(card_width * 0.08), int(card_height * 0.06))
        form_layout.setSpacing(0)
        
        welcome_label = QLabel("创建新账号")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT};
                font-size: {int(font_size * 1.1)}px;
                font-weight: bold;
                margin-bottom: 10px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
        """)
        form_layout.addWidget(welcome_label)
        
        username_section = self._create_modern_input_section("用户名", "请输入用户名", "🧑", font_size, input_height, card_width)
        form_layout.addWidget(username_section["container"])
        self.register_username = username_section["input"]
        
        password_section = self._create_modern_password_section("密码", "请输入密码", "🔐", font_size, input_height, button_font_size, show_checkbox=True, card_width=card_width)
        form_layout.addWidget(password_section["container"])
        self.register_password = password_section["input"]
        self.register_show_password_checkbox = password_section["checkbox"]
        
        confirm_section = self._create_modern_input_section("确认密码", "请再次输入密码", "🔄", font_size, input_height, card_width)
        form_layout.addWidget(confirm_section["container"])
        self.register_confirm = confirm_section["input"]
        self.register_confirm.setEchoMode(QLineEdit.Password)
        
        email_section = self._create_register_code_section("邮箱", "请输入邮箱", "✉️", font_size, input_height, screen_width, button_font_size)
        form_layout.addWidget(email_section["container"])
        self.register_email = email_section["input"]
        self.get_code_button = email_section["button"]
        
        code_section = self._create_modern_input_section("验证码", "请输入验证码", "🔐", font_size, input_height, card_width)
        form_layout.addWidget(code_section["container"])
        self.verification_code_input = code_section["input"]
        
        self.register_pwd_strength_label = QLabel()
        self.register_pwd_strength_label.setStyleSheet(f"font-size: {max(14, int(screen_height * 0.018))}px; margin: 0px; padding: 0px; color: #262626;")
        form_layout.addWidget(self.register_pwd_strength_label)
        
        button_section = self._create_register_button_section(screen_width, screen_height, input_height, button_font_size)
        form_layout.addWidget(button_section["container"])
        
        main_layout.addWidget(form_container)
        
        self.register_layout = QVBoxLayout()
        self.register_layout.setContentsMargins(0, 30, 0, 30)
        self.register_layout.setSpacing(0)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        h_layout.addStretch(1)
        h_layout.addWidget(main_container)
        h_layout.addStretch(1)
        
        self.register_layout.addLayout(h_layout)
        
        # 连接信号
        self.register_password.textChanged.connect(self.check_password_strength)
        self.register_confirm.textChanged.connect(self.check_password_strength)
        self.register_show_password_checkbox.stateChanged.connect(self.toggle_both_password_visibility)
        
        # 设置布局
        self.register_tab.setLayout(self.register_layout)
        
        # 填充默认数据
        if self.auto_fill_defaults:
            self.register_username.setText(generate_random_username())
            self.register_password.setText("Lsq011219.")
            self.register_confirm.setText("Lsq011219.")
            self.register_email.setText("1399972370@qq.com")
        
        # 连接返回登录按钮信号
        self.back_to_login_button.clicked.connect(self.show_login_page)
        
    def _create_register_password_section(self, label_text, placeholder, icon, font_size, input_height, button_font_size, show_checkbox=False):
        """创建注册界面密码输入区域 - 与登录界面保持一致的样式"""
        section = {}
        
        # 创建容器
        section["container"] = QWidget()
        layout = QVBoxLayout(section["container"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # 更小的标签和输入框之间的间距
        
        # 创建标签 - 与其他输入框保持一致的样式
        label = QLabel(label_text)
        label.setStyleSheet(f"color: #262626; font-size: {font_size - 2}px; font-weight: bold; margin: 0px; padding: 0px;")
        label.setContentsMargins(0, 0, 0, 0)  # 与其他输入框一致的边距
        layout.addWidget(label)
        
        # 使用create_styled_input创建密码输入框
        password_input = self.create_styled_input(
            placeholder=placeholder,
            icon=icon,
            height=input_height,
            font_size=font_size
        )
        password_input.setEchoMode(QLineEdit.Password)
        
        # 直接添加输入框的容器到布局，与其他输入框保持一致
        layout.addWidget(password_input._icon_container)
        
        # 添加显示密码复选框（移到密码输入框下方）
        if show_checkbox:
            section["checkbox"] = QCheckBox("显示密码")
            section["checkbox"].setChecked(True)
            section["checkbox"].setStyleSheet(f"""
                QCheckBox {{ 
                    color: #262626;
                    font-size: {button_font_size}px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                }}
                QCheckBox::indicator:unchecked {{
                    border: 1px solid white;
                    background-color: white;
                    border-radius: 3px;
                }}
                QCheckBox::indicator:checked {{
                    border: 1px solid #1890ff;
                    background-color: #1890ff;
                    border-radius: 3px;
                }}
            """)
            # 创建一个水平布局来右对齐复选框
            checkbox_layout = QHBoxLayout()
            checkbox_layout.setContentsMargins(0, 0, 0, 0)  # 最小边距
            checkbox_layout.setSpacing(0)  # 最小间距
            checkbox_layout.addStretch()  # 左侧添加拉伸空间
            checkbox_layout.addWidget(section["checkbox"])
            layout.addLayout(checkbox_layout)
        
        # 保存输入框引用
        section["input"] = password_input
        
        return section
    
    def _create_register_code_section(self, label_text, placeholder, icon, font_size, input_height, screen_width, button_font_size):
        """创建注册界面邮箱和验证码区域 - 与登录界面保持一致的样式"""
        section = {}
        
        # 创建容器 - 与其他输入框保持一致
        section["container"] = QWidget()
        layout = QVBoxLayout(section["container"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # 极小标签和输入框之间的间距
        
        # 创建标签 - 与其他输入框保持一致的样式
        label = QLabel(label_text)
        label.setStyleSheet(f"color: #262626; font-size: {font_size - 2}px; font-weight: bold; margin: 0px; padding: 0px;")
        label.setContentsMargins(0, 0, 0, 0)  # 与其他输入框一致的边距
        layout.addWidget(label)
        
        # 输入框和按钮容器
        input_button_container = QFrame()
        input_button_layout = QHBoxLayout(input_button_container)
        input_button_layout.setContentsMargins(0, 0, 0, 0)
        input_button_layout.setSpacing(2)  # 极小输入框和按钮之间的间距
        
        # 使用create_styled_input创建输入框
        input_field = self.create_styled_input(
            placeholder=placeholder,
            icon=icon,
            height=input_height,
            font_size=font_size
        )
        
        # 添加输入框的容器到布局
        input_button_layout.addWidget(input_field._icon_container)
        
        # 添加获取验证码按钮
        section["button"] = QPushButton("获取验证码")
        section["button"].setStyleSheet(f"""
            QPushButton {{
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {button_font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QPushButton:pressed {{
                background-color: #096dd9;
            }}
            QPushButton:disabled {{
                background-color: white;
                color: #262626;
            }}
        """)
        section["button"].setMinimumWidth(int(screen_width * 0.025))  # 减小按钮宽度
        section["button"].setMaximumWidth(120)  # 添加最大宽度限制
        section["button"].setMinimumHeight(int(input_height * 0.9))
        section["button"].clicked.connect(self.handle_get_verification_code)
        input_button_layout.addWidget(section["button"])
        
        layout.addWidget(input_button_container)
        
        # 保存输入框引用
        section["input"] = input_field
        
        return section
    
    def _create_register_button_section(self, screen_width, screen_height, input_height, button_font_size):
        """创建注册界面按钮区域 - 与登录界面保持一致的样式"""
        section = {}
        
        # 创建容器
        section["container"] = QFrame()
        section["container"].setStyleSheet("QFrame { background-color: transparent; }")
        layout = QHBoxLayout(section["container"])
        layout.setContentsMargins(0, 0, 0, 20)  # 底部留白
        layout.setSpacing(1)  # 最小按钮间距
        
        # 创建注册按钮 - 与登录界面的登录按钮样式一致
        register_button = QPushButton("注册")
        register_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {button_font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QPushButton:pressed {{
                background-color: #096dd9;
            }}
        """)
        register_button.setMinimumWidth(int(screen_width * 0.12))
        register_button.setMinimumHeight(int(input_height * 0.9))
        register_button.clicked.connect(self.handle_register)
        layout.addWidget(register_button)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 创建返回登录按钮 - 与登录界面的注册按钮样式一致
        back_button = QPushButton("返回登录")
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {button_font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QPushButton:pressed {{
                background-color: #096dd9;
            }}
        """)
        back_button.setMinimumWidth(int(screen_width * 0.12))
        back_button.setMinimumHeight(int(input_height * 0.9))
        self.back_to_login_button = back_button
        layout.addWidget(back_button)
        
        return section
    
    def _create_forgot_password_button_section(self, screen_width, screen_height, input_height, button_font_size):
        """创建找回密码界面按钮区域 - 与注册界面保持一致的样式"""
        section = {}
        
        # 创建容器
        section["container"] = QFrame()
        section["container"].setStyleSheet("QFrame { background-color: transparent; }")
        layout = QHBoxLayout(section["container"])
        layout.setContentsMargins(0, 0, 0, 0)  # 最小边距
        layout.setSpacing(1)  # 最小按钮间距
        
        # 创建重置密码按钮 - 与注册界面的注册按钮样式一致
        reset_button = QPushButton("重置")
        reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {button_font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QPushButton:pressed {{
                background-color: #096dd9;
            }}
        """)
        reset_button.setMinimumWidth(int(screen_width * 0.12))
        reset_button.setMinimumHeight(input_height)
        reset_button.clicked.connect(self.handle_reset_password)
        self.reset_password_button = reset_button  # 添加这行以设置属性
        layout.addWidget(reset_button)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 创建返回登录按钮 - 与注册界面的返回登录按钮样式一致
        back_button = QPushButton("返回登录")
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {button_font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QPushButton:pressed {{
                background-color: #096dd9;
            }}
        """)
        back_button.setMinimumWidth(int(screen_width * 0.12))
        back_button.setMinimumHeight(input_height)
        self.back_to_login_button = back_button
        layout.addWidget(back_button)
        
        # 连接返回登录按钮信号
        self.back_to_login_button.clicked.connect(self.show_login_page)
        
        return section
    
    def try_auto_login(self):
        """尝试自动填充登录信息"""
        # 检查是否有保存的登录信息
        if hasattr(self, 'username') and hasattr(self, 'password') and self.username and self.password:
            # 延迟执行，确保输入框已创建
            QTimer.singleShot(300, self._auto_fill_login)

    def _auto_fill_login(self):
        """自动填充登录信息到输入框"""
        if hasattr(self, 'login_username') and hasattr(self, 'login_password'):
            self.login_username.setText(self.username)
            self.login_password.setText(self.password)
            print(f"自动填充完成: 用户名={self.login_username.text()}, 密码={'*' * len(self.password)}")
            # 触发输入检查，确保登录按钮状态正确
            self.check_login_input()

    def _auto_login(self):
        """执行自动登录"""
        # 检查输入框是否存在
        if hasattr(self, 'login_username') and hasattr(self, 'login_password'):
            # 填充登录信息
            self.login_username.setText(self.username)
            self.login_password.setText(self.password)
            print(f"自动填充完成: 用户名={self.login_username.text()}, 密码={self.login_password.text()}")
            
            # 触发一次输入检查，确保登录按钮状态正确
            self.check_login_input()
            
            # 延迟500ms后自动点击登录按钮
            QTimer.singleShot(500, lambda: self.login_btn.click())
            print("已触发自动登录")
        else:
            print("输入框未找到，延迟重试...")
            # 如果输入框还未创建，延迟重试
            QTimer.singleShot(500, self._auto_login)

    def toggle_both_password_visibility(self, state):
        """切换两个密码框的可见性"""
        if state == Qt.Checked:
            self.register_password.setEchoMode(QLineEdit.Normal)
            self.register_confirm.setEchoMode(QLineEdit.Normal)
        else:
            self.register_password.setEchoMode(QLineEdit.Password)
            self.register_confirm.setEchoMode(QLineEdit.Password)

    def handle_reset_password(self):
        """处理密码重置逻辑"""
        email = self.forgot_email_input.text().strip()
        new_password = self.forgot_new_password.text().strip()
        confirm_password = self.forgot_confirm_password.text().strip()
        verification_code = self.forgot_code_input.text().strip()
        
        # 验证所有字段
        if not email:
            QMessageBox.warning(self, "警告", "请输入注册邮箱")
            self.forgot_email_input.setFocus()
            return
        
        if not verification_code:
            StyledMessageDialog(self, title="警告", text="请输入验证码", msg_type="warning", buttons="ok").exec_()
            self.forgot_code_input.setFocus()
            return
        
        if not new_password:
            StyledMessageDialog(self, title="警告", text="请输入新密码", msg_type="warning", buttons="ok").exec_()
            self.forgot_new_password.setFocus()
            return
        
        if not confirm_password:
            StyledMessageDialog(self, title="警告", text="请确认新密码", msg_type="warning", buttons="ok").exec_()
            self.forgot_confirm_password.setFocus()
            return
        
        # 验证邮箱格式
        if not is_valid_email(email):
            QMessageBox.warning(self, "警告", "请输入有效的邮箱地址")
            self.forgot_email_input.setFocus()
            return
        
        # 验证密码匹配
        if new_password != confirm_password:
            StyledMessageDialog(self, title="警告", text="两次输入的密码不一致", msg_type="warning", buttons="ok").exec_()
            self.forgot_confirm_password.setFocus()
            self.forgot_confirm_password.selectAll()
            return
        
        # 验证密码强度
        is_valid, error_msg = validate_password_requirements(new_password)
        if not is_valid:
            QMessageBox.warning(self, "警告", error_msg)
            self.forgot_new_password.setFocus()
            self.forgot_new_password.selectAll()
            return
        
        # 显示加载状态
        self.reset_password_button.setEnabled(False)
        self.reset_password_button.setText("重置中...")
        
        # 调用登录管理器的重置密码方法
        success, msg = self.login_manager.reset_password(email, new_password, verification_code)
        
        # 恢复按钮状态
        self.reset_password_button.setEnabled(True)
        self.reset_password_button.setText("重置密码")
        
        if success:
            StyledMessageDialog(self, title="重置成功", text="密码已重置，请使用新密码登录", msg_type="information", buttons="ok").exec_()
            # 清空输入框
            self.forgot_email_input.clear()
            self.forgot_new_password.clear()
            self.forgot_confirm_password.clear()
            self.forgot_code_input.clear()
            self.forgot_pwd_strength_label.clear()
            # 返回登录页面
            self.show_login_page()
        else:
            StyledMessageDialog(self, title="重置失败", text=msg, msg_type="warning", buttons="ok").exec_()
            if "验证码" in msg:
                self.forgot_code_input.setFocus()
                self.forgot_code_input.selectAll()
            elif "邮箱" in msg:
                self.forgot_email_input.setFocus()
                self.forgot_email_input.selectAll()

