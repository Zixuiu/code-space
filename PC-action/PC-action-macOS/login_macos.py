"""
macOS 风格登录/注册/找回密码界面
"""
import os
import sys
import random
import string

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QWidget, QCheckBox, QApplication, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont, QPainter, QColor

from utils import (
    is_valid_email, get_screen_size, generate_random_username,
    validate_password_requirements
)

from app_macos import MacOSColors


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


class MacOSLineEdit(QLineEdit):
    def __init__(self, placeholder="", echo_mode=QLineEdit.Normal, password_mode=False):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setEchoMode(echo_mode)
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 15px;
                font-family: 'Microsoft YaHei';
            }}
            QLineEdit:focus {{
                border: 2px solid {MacOSColors.ACCENT};
                background-color: {MacOSColors.CARD_BG};
            }}
            QLineEdit::placeholder {{
                color: {MacOSColors.TEXT_SECONDARY};
            }}
        """)


class MacOSLabel(QLabel):
    def __init__(self, text="", size=13, color=None, bold=False, align=None):
        super().__init__(text)
        c = color or MacOSColors.TEXT_PRIMARY
        w = "700" if bold else "400"
        self.setStyleSheet(f"""
            color: {c};
            font-size: {size}px;
            font-weight: {w};
            font-family: 'Microsoft YaHei';
        """)


class EmailThread(QThread):
    finished = pyqtSignal(bool, str, str, str)

    def __init__(self, email, login_manager):
        super().__init__()
        self.email = email
        self.login_manager = login_manager

    def run(self):
        try:
            success, msg, code = self.login_manager.send_verification_code(self.email)
            self.finished.emit(success, msg, self.email, code)
        except Exception as e:
            self.finished.emit(False, f"发送验证码时发生错误: {str(e)}", self.email, None)


class MacOSLoginDialog(QDialog):
    login_success = pyqtSignal(str)

    def __init__(self, login_manager, parent=None):
        super().__init__(parent)
        self.login_manager = login_manager
        self.current_user = None
        self.auto_fill_defaults = True
        self.skip_verification = False
        self._register_tab_initialized = False
        self._forgot_password_tab_initialized = False

        self.username, self.password = self.login_manager.load_saved_login()

        self.setWindowTitle("登录")
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowState(Qt.WindowNoState)

        self.initUI()
        self.try_auto_login()

    def initUI(self):
        _, screen_height = get_screen_size()
        w, h = 420, 520
        desktop = QApplication.desktop()
        r = desktop.availableGeometry()
        self.setGeometry(r.x() + (r.width() - w) // 2, r.y() + (r.height() - h) // 2, w, h)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {MacOSColors.WINDOW_BG};
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.login_page = QWidget()
        self.register_page = QWidget()
        self.forgot_page = QWidget()

        self.setup_login_page()
        self.setup_register_page()
        self.setup_forgot_page()

        self.main_layout.addWidget(self.login_page)
        self.main_layout.addWidget(self.register_page)
        self.main_layout.addWidget(self.forgot_page)

        self.register_page.hide()
        self.forgot_page.hide()
        self.login_page.show()

        self._auto_fill_pending = True

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, '_auto_fill_pending') and self._auto_fill_pending:
            self._auto_fill_pending = False
            if self.username and self.password:
                QTimer.singleShot(300, self._fill_saved_credentials)

    def _fill_saved_credentials(self):
        if hasattr(self, 'login_username') and hasattr(self, 'login_password'):
            self.login_username.setText(self.username)
            self.login_password.setText(self.password)
            self.check_login_input()

    def move_to_center(self):
        desktop = QApplication.desktop()
        r = desktop.availableGeometry()
        w, h = self.width(), self.height()
        self.move(r.x() + (r.width() - w) // 2, r.y() + (r.height() - h) // 2)

    def _card_with_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 12))
        shadow.setOffset(0, 6)
        widget.setGraphicsEffect(shadow)

    def _field_label(self, text):
        return MacOSLabel(text, size=14, bold=True)

    def _macos_button(self, text, color=MacOSColors.ACCENT, secondary=False):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(42)
        if secondary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {MacOSColors.ACCENT};
                    border: 1px solid {MacOSColors.SEPARATOR};
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: 500;
                    font-family: 'Microsoft YaHei';
                    padding: 8px 20px;
                }}
                QPushButton:hover {{
                    background-color: {MacOSColors.SIDEBAR_BG};
                }}
                QPushButton:pressed {{
                    background-color: #D9D9DE;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: 600;
                    font-family: 'Microsoft YaHei';
                    padding: 8px 24px;
                }}
                QPushButton:hover {{
                    background-color: {color}DD;
                }}
                QPushButton:pressed {{
                    background-color: {color}BB;
                }}
            """)
        return btn

    def _link_label(self, text, color=MacOSColors.ACCENT):
        label = QLabel(f"<a href='#' style='color: {color}; text-decoration: none; font-weight: 500;'>{text}</a>")
        label.setCursor(Qt.PointingHandCursor)
        label.setStyleSheet(f"font-size: 14px; font-family: 'Microsoft YaHei';")
        return label

    def _switch_row(self, question, link_text, link_slot):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(4)
        rl.addStretch()
        rl.addWidget(MacOSLabel(question, size=14, color=MacOSColors.TEXT_SECONDARY))
        link = self._link_label(link_text)
        link.linkActivated.connect(link_slot)
        rl.addWidget(link)
        rl.addStretch()
        return row

    # ─────────────────────────────────────────────────
    #  Login Page
    # ─────────────────────────────────────────────────
    def setup_login_page(self):
        layout = QVBoxLayout(self.login_page)
        layout.setContentsMargins(40, 50, 40, 40)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        card = MacOSCard()
        self._card_with_shadow(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(6)

        title = MacOSLabel("欢迎回来", size=30, bold=True)
        title.setAlignment(Qt.AlignCenter)
        cl.addWidget(title)

        subtitle = MacOSLabel("请登录以继续使用", size=15, color=MacOSColors.TEXT_SECONDARY)
        subtitle.setAlignment(Qt.AlignCenter)
        cl.addWidget(subtitle)

        cl.addSpacing(18)

        cl.addWidget(self._field_label("用户名"))
        cl.addSpacing(2)
        self.login_username = MacOSLineEdit("请输入用户名")
        cl.addWidget(self.login_username)

        cl.addSpacing(14)

        cl.addWidget(self._field_label("密码"))
        cl.addSpacing(2)
        pwd_container = QWidget()
        pwd_container.setStyleSheet("background: transparent;")
        pwl = QHBoxLayout(pwd_container)
        pwl.setContentsMargins(0, 0, 0, 0)
        pwl.setSpacing(8)
        self.login_password = MacOSLineEdit("请输入密码", QLineEdit.Password)
        pwl.addWidget(self.login_password)

        self.show_pwd_cb = QCheckBox("显示")
        self.show_pwd_cb.setChecked(True)
        self.show_pwd_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 14px;
                font-family: 'Microsoft YaHei';
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px; height: 20px;
                border-radius: 10px;
                border: 2px solid {MacOSColors.SEPARATOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {MacOSColors.ACCENT};
                border-color: {MacOSColors.ACCENT};
            }}
        """)
        self.show_pwd_cb.toggled.connect(lambda c: self.login_password.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password))
        pwl.addWidget(self.show_pwd_cb)
        cl.addWidget(pwd_container)

        cl.addSpacing(10)

        # 记住我 + 忘记密码行
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)

        self.remember_cb = QCheckBox("记住我")
        self.remember_cb.setChecked(True)
        self.remember_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 14px;
                font-family: 'Microsoft YaHei';
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px; height: 20px;
                border-radius: 10px;
                border: 2px solid {MacOSColors.SEPARATOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {MacOSColors.ACCENT};
                border-color: {MacOSColors.ACCENT};
            }}
        """)
        rl.addWidget(self.remember_cb)
        rl.addStretch()

        forgot_link = self._link_label("忘记密码?")
        forgot_link.linkActivated.connect(self.show_forgot_page)
        rl.addWidget(forgot_link)

        cl.addWidget(row)

        cl.addSpacing(14)

        self.login_btn = self._macos_button("登  录")
        self.login_btn.clicked.connect(self.handle_login)
        self.login_btn.setEnabled(False)
        cl.addWidget(self.login_btn)

        cl.addSpacing(6)
        cl.addWidget(self._switch_row("还没有账号?", "立即注册", self.show_register_page))

        layout.addWidget(card)

        self.login_username.textChanged.connect(self.check_login_input)
        self.login_password.textChanged.connect(self.check_login_input)

        QTimer.singleShot(0, self.move_to_center)

    def check_login_input(self):
        u = self.login_username.text().strip()
        p = self.login_password.text().strip()
        self.login_btn.setEnabled(bool(u and p))

    def handle_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()
        success, message = self.login_manager.login(username, password)
        if self.remember_cb.isChecked() and success:
            self.login_manager.save_login_credentials(username, password)
        self.on_login_complete(success, message)

    def on_login_complete(self, success, message):
        if success:
            self.current_user = message
            self.login_success.emit(message)
            self.accept()
        else:
            QMessageBox.warning(self, "登录失败", message)

    # ─────────────────────────────────────────────────
    #  Register Page
    # ─────────────────────────────────────────────────
    def setup_register_page(self):
        layout = QVBoxLayout(self.register_page)
        layout.setContentsMargins(40, 50, 40, 40)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        card = MacOSCard()
        self._card_with_shadow(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(6)

        title = MacOSLabel("创建新账号", size=30, bold=True)
        title.setAlignment(Qt.AlignCenter)
        cl.addWidget(title)

        subtitle = MacOSLabel("注册一个新账户开始使用", size=15, color=MacOSColors.TEXT_SECONDARY)
        subtitle.setAlignment(Qt.AlignCenter)
        cl.addWidget(subtitle)

        cl.addSpacing(14)

        cl.addWidget(self._field_label("用户名"))
        cl.addSpacing(2)
        self.register_username = MacOSLineEdit("请输入用户名")
        cl.addWidget(self.register_username)

        cl.addSpacing(12)

        cl.addWidget(self._field_label("密码"))
        cl.addSpacing(2)
        pwd_container = QWidget()
        pwd_container.setStyleSheet("background: transparent;")
        pwl = QHBoxLayout(pwd_container)
        pwl.setContentsMargins(0, 0, 0, 0)
        pwl.setSpacing(8)
        self.register_password = MacOSLineEdit("请输入密码", QLineEdit.Password)
        pwl.addWidget(self.register_password)

        self.reg_show_cb = QCheckBox("显示")
        self.reg_show_cb.setChecked(True)
        self.reg_show_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 14px;
                font-family: 'Microsoft YaHei';
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px; height: 20px;
                border-radius: 10px;
                border: 2px solid {MacOSColors.SEPARATOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {MacOSColors.ACCENT};
                border-color: {MacOSColors.ACCENT};
            }}
        """)
        self.reg_show_cb.toggled.connect(self._toggle_register_visibility)
        pwl.addWidget(self.reg_show_cb)
        cl.addWidget(pwd_container)

        self.register_pwd_strength = MacOSLabel("", size=12, color=MacOSColors.TEXT_SECONDARY)
        cl.addWidget(self.register_pwd_strength)

        cl.addWidget(self._field_label("确认密码"))
        cl.addSpacing(2)
        self.register_confirm = MacOSLineEdit("请再次输入密码", QLineEdit.Password)
        cl.addWidget(self.register_confirm)

        cl.addSpacing(12)

        cl.addWidget(self._field_label("邮箱"))
        cl.addSpacing(2)
        email_container = QWidget()
        email_container.setStyleSheet("background: transparent;")
        el = QHBoxLayout(email_container)
        el.setContentsMargins(0, 0, 0, 0)
        el.setSpacing(8)
        self.register_email = MacOSLineEdit("请输入邮箱")
        el.addWidget(self.register_email)

        self.get_code_btn = self._macos_button("获取验证码", secondary=True)
        self.get_code_btn.setMinimumWidth(110)
        self.get_code_btn.setMinimumHeight(46)
        self.get_code_btn.clicked.connect(self.handle_get_verification_code)
        el.addWidget(self.get_code_btn)
        cl.addWidget(email_container)

        cl.addWidget(self._field_label("验证码"))
        cl.addSpacing(2)
        self.verification_code_input = MacOSLineEdit("请输入验证码")
        cl.addWidget(self.verification_code_input)

        cl.addSpacing(12)

        reg_btn = self._macos_button("注  册", MacOSColors.SYSTEM_GREEN)
        reg_btn.clicked.connect(self.handle_register)
        cl.addWidget(reg_btn)

        cl.addSpacing(6)
        cl.addWidget(self._switch_row("已有账号?", "返回登录", self.show_login_page))

        layout.addWidget(card)

        self.register_password.textChanged.connect(self.check_password_strength)
        self.register_confirm.textChanged.connect(self.check_password_strength)

        if self.auto_fill_defaults:
            self.register_username.setText(generate_random_username())
            self.register_password.setText("Lsq011219.")
            self.register_confirm.setText("Lsq011219.")
            self.register_email.setText("1399972370@qq.com")

    def _toggle_register_visibility(self, checked):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.register_password.setEchoMode(mode)
        self.register_confirm.setEchoMode(mode)

    def show_register_page(self):
        self.login_page.hide()
        self.forgot_page.hide()
        self.register_page.show()
        self.setWindowTitle("注册")
        QTimer.singleShot(0, self.move_to_center)

    def show_login_page(self):
        self.register_page.hide()
        self.forgot_page.hide()
        self.login_page.show()
        self.setWindowTitle("登录")
        QTimer.singleShot(0, self.move_to_center)
        if hasattr(self, 'registered_username') and hasattr(self, 'registered_password'):
            self.login_username.setText(self.registered_username)
            self.login_password.setText(self.registered_password)

    def handle_register(self):
        username = self.register_username.text().strip()
        password = self.register_password.text().strip()
        confirm = self.register_confirm.text().strip()
        email = self.register_email.text().strip()
        code = self.verification_code_input.text().strip()

        if not username:
            QMessageBox.warning(self, "警告", "请输入用户名"); return
        if not password:
            QMessageBox.warning(self, "警告", "请输入密码"); return
        if password != confirm:
            QMessageBox.warning(self, "警告", "两次输入的密码不一致"); return
        if not email:
            QMessageBox.warning(self, "警告", "请输入邮箱"); return
        if not is_valid_email(email):
            QMessageBox.warning(self, "警告", "请输入有效的邮箱地址"); return

        strength_text, _ = self._calc_strength(password)
        if strength_text == "弱":
            reply = QMessageBox.question(self, "密码强度提示",
                                         "密码强度较弱，建议使用包含大小写字母、数字和特殊字符的密码。\n是否继续注册？",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        if not self.skip_verification and not code:
            QMessageBox.warning(self, "警告", "请输入验证码"); return

        success, message = self.login_manager.register(username, password, email, code)
        if success:
            QMessageBox.information(self, "注册成功", message)
            self.registered_username = username
            self.registered_password = password
            self.show_login_page()
        else:
            QMessageBox.warning(self, "注册失败", message)

    # ─────────────────────────────────────────────────
    #  Forgot Password Page
    # ─────────────────────────────────────────────────
    def setup_forgot_page(self):
        layout = QVBoxLayout(self.forgot_page)
        layout.setContentsMargins(40, 50, 40, 40)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        card = MacOSCard()
        self._card_with_shadow(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(6)

        title = MacOSLabel("找回密码", size=30, bold=True)
        title.setAlignment(Qt.AlignCenter)
        cl.addWidget(title)

        subtitle = MacOSLabel("输入注册邮箱重置密码", size=15, color=MacOSColors.TEXT_SECONDARY)
        subtitle.setAlignment(Qt.AlignCenter)
        cl.addWidget(subtitle)

        cl.addSpacing(14)

        cl.addWidget(self._field_label("邮箱"))
        cl.addSpacing(2)
        email_container = QWidget()
        email_container.setStyleSheet("background: transparent;")
        el = QHBoxLayout(email_container)
        el.setContentsMargins(0, 0, 0, 0)
        el.setSpacing(8)
        self.forgot_email = MacOSLineEdit("请输入注册邮箱")
        el.addWidget(self.forgot_email)

        self.forgot_get_code_btn = self._macos_button("获取验证码", secondary=True)
        self.forgot_get_code_btn.setMinimumWidth(110)
        self.forgot_get_code_btn.setMinimumHeight(46)
        self.forgot_get_code_btn.clicked.connect(self.handle_forgot_get_code)
        el.addWidget(self.forgot_get_code_btn)
        cl.addWidget(email_container)

        cl.addWidget(self._field_label("验证码"))
        cl.addSpacing(2)
        self.forgot_code = MacOSLineEdit("请输入验证码")
        cl.addWidget(self.forgot_code)

        cl.addSpacing(12)

        cl.addWidget(self._field_label("新密码"))
        cl.addSpacing(2)
        pwd_container = QWidget()
        pwd_container.setStyleSheet("background: transparent;")
        pwl = QHBoxLayout(pwd_container)
        pwl.setContentsMargins(0, 0, 0, 0)
        pwl.setSpacing(8)
        self.forgot_new_password = MacOSLineEdit("请输入新密码", QLineEdit.Password)
        pwl.addWidget(self.forgot_new_password)

        self.forgot_show_cb = QCheckBox("显示")
        self.forgot_show_cb.setChecked(True)
        self.forgot_show_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 14px;
                font-family: 'Microsoft YaHei';
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px; height: 20px;
                border-radius: 10px;
                border: 2px solid {MacOSColors.SEPARATOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {MacOSColors.ACCENT};
                border-color: {MacOSColors.ACCENT};
            }}
        """)
        pwl.addWidget(self.forgot_show_cb)
        cl.addWidget(pwd_container)

        self.forgot_pwd_strength = MacOSLabel("", size=12, color=MacOSColors.TEXT_SECONDARY)
        cl.addWidget(self.forgot_pwd_strength)

        cl.addWidget(self._field_label("确认密码"))
        cl.addSpacing(2)
        self.forgot_confirm = MacOSLineEdit("请再次输入新密码", QLineEdit.Password)
        cl.addWidget(self.forgot_confirm)

        cl.addSpacing(12)

        reset_btn = self._macos_button("重  置", MacOSColors.SYSTEM_ORANGE)
        reset_btn.clicked.connect(self.handle_reset_password)
        self.reset_pwd_btn = reset_btn
        cl.addWidget(reset_btn)

        cl.addSpacing(6)
        cl.addWidget(self._switch_row("想起密码了?", "返回登录", self.show_login_page))

        layout.addWidget(card)

        self.forgot_new_password.textChanged.connect(self._check_forgot_strength)

    def show_forgot_page(self):
        self.login_page.hide()
        self.register_page.hide()
        self.forgot_page.show()
        self.setWindowTitle("找回密码")
        QTimer.singleShot(0, self.move_to_center)

    def handle_forgot_get_code(self):
        email = self.forgot_email.text().strip()
        if not email:
            QMessageBox.warning(self, "警告", "请输入注册邮箱"); return
        if not is_valid_email(email):
            QMessageBox.warning(self, "警告", "请输入有效的邮箱地址"); return

        if hasattr(self, 'forgot_timer') and self.forgot_timer and self.forgot_timer.isActive():
            return

        self.forgot_get_code_btn.setEnabled(False)
        self.forgot_get_code_btn.setText("发送中...")

        self.email_thread = EmailThread(email, self.login_manager)
        self.email_thread.finished.connect(self._on_forgot_email_sent)
        self.email_thread.start()

    def _on_forgot_email_sent(self, success, msg, email, code):
        if success:
            if code:
                QMessageBox.information(self, "验证码已生成", f"验证码: {code}")
                self.forgot_code.setText(code)
            else:
                QMessageBox.information(self, "验证码已发送", "验证码已成功发送到您的邮箱")
            self.forgot_countdown = 60
            self.forgot_timer = QTimer(self)
            self.forgot_timer.timeout.connect(self._update_forgot_countdown)
            self.forgot_timer.start(1000)
            self.forgot_get_code_btn.setText(f"重新发送({self.forgot_countdown})")
        else:
            QMessageBox.warning(self, "发送失败", msg)
            self.forgot_get_code_btn.setEnabled(True)
            self.forgot_get_code_btn.setText("获取验证码")

    def _update_forgot_countdown(self):
        self.forgot_countdown -= 1
        if self.forgot_countdown <= 0:
            self.forgot_timer.stop()
            self.forgot_get_code_btn.setText("获取验证码")
            self.forgot_get_code_btn.setEnabled(True)
        else:
            self.forgot_get_code_btn.setText(f"重新发送({self.forgot_countdown})")

    def handle_forgot_password(self):
        self.show_forgot_page()

    def handle_reset_password(self):
        email = self.forgot_email.text().strip()
        new_pwd = self.forgot_new_password.text().strip()
        confirm_pwd = self.forgot_confirm.text().strip()
        code = self.forgot_code.text().strip()

        if not email:
            QMessageBox.warning(self, "警告", "请输入注册邮箱"); return
        if not code:
            QMessageBox.warning(self, "警告", "请输入验证码"); return
        if not new_pwd:
            QMessageBox.warning(self, "警告", "请输入新密码"); return
        if not confirm_pwd:
            QMessageBox.warning(self, "警告", "请确认新密码"); return
        if not is_valid_email(email):
            QMessageBox.warning(self, "警告", "请输入有效的邮箱地址"); return
        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "警告", "两次输入的密码不一致"); return

        is_valid, error_msg = validate_password_requirements(new_pwd)
        if not is_valid:
            QMessageBox.warning(self, "警告", error_msg); return

        self.reset_pwd_btn.setEnabled(False)
        self.reset_pwd_btn.setText("重置中...")

        success, msg = self.login_manager.reset_password(email, new_pwd, code)

        self.reset_pwd_btn.setEnabled(True)
        self.reset_pwd_btn.setText("重置")

        if success:
            QMessageBox.information(self, "重置成功", "密码已重置，请使用新密码登录")
            self.forgot_email.clear()
            self.forgot_new_password.clear()
            self.forgot_confirm.clear()
            self.forgot_code.clear()
            self.forgot_pwd_strength.clear()
            self.show_login_page()
        else:
            QMessageBox.warning(self, "重置失败", msg)

    # ─────────────────────────────────────────────────
    #  Verification Code
    # ─────────────────────────────────────────────────
    def handle_get_verification_code(self):
        email = self.register_email.text().strip()
        if not email:
            QMessageBox.warning(self, "警告", "请输入邮箱地址"); return
        if not is_valid_email(email):
            QMessageBox.warning(self, "警告", "请输入有效的邮箱地址"); return

        if hasattr(self, 'register_timer') and self.register_timer and self.register_timer.isActive():
            return

        self.get_code_btn.setEnabled(False)
        self.get_code_btn.setText("发送中...")

        self.email_thread = EmailThread(email, self.login_manager)
        self.email_thread.finished.connect(self._on_register_email_sent)
        self.email_thread.start()

    def _on_register_email_sent(self, success, msg, email, code):
        if success:
            if code:
                QMessageBox.information(self, "验证码已生成", f"验证码: {code}")
                self.verification_code_input.setText(code)
            else:
                QMessageBox.information(self, "验证码已发送", "验证码已成功发送到您的邮箱")
            self.reg_countdown = 60
            self.register_timer = QTimer(self)
            self.register_timer.timeout.connect(self._update_register_countdown)
            self.register_timer.start(1000)
            self.get_code_btn.setText(f"重新发送({self.reg_countdown})")
        else:
            QMessageBox.warning(self, "发送失败", msg)
            self.get_code_btn.setEnabled(True)
            self.get_code_btn.setText("获取验证码")

    def _update_register_countdown(self):
        self.reg_countdown -= 1
        if self.reg_countdown <= 0:
            self.register_timer.stop()
            self.get_code_btn.setText("获取验证码")
            self.get_code_btn.setEnabled(True)
        else:
            self.get_code_btn.setText(f"重新发送({self.reg_countdown})")

    # ─────────────────────────────────────────────────
    #  Password Strength
    # ─────────────────────────────────────────────────
    def _calc_strength(self, password):
        if not password:
            return "", ""
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?/~`' for c in password)
        if has_special:
            return "强", MacOSColors.SYSTEM_GREEN
        elif has_upper:
            return "中", MacOSColors.SYSTEM_ORANGE
        else:
            return "弱", MacOSColors.SYSTEM_RED

    def check_password_strength(self):
        pwd = self.register_password.text()
        strength, color = self._calc_strength(pwd)
        if strength:
            self.register_pwd_strength.setText(f"密码强度: {strength}")
            self.register_pwd_strength.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600; font-family: 'Microsoft YaHei';")
        else:
            self.register_pwd_strength.clear()

    def _check_forgot_strength(self):
        pwd = self.forgot_new_password.text()
        strength, color = self._calc_strength(pwd)
        if strength:
            self.forgot_pwd_strength.setText(f"密码强度: {strength}")
            self.forgot_pwd_strength.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600; font-family: 'Microsoft YaHei';")
        else:
            self.forgot_pwd_strength.clear()

    def try_auto_login(self):
        if hasattr(self, 'username') and self.username and self.password:
            QTimer.singleShot(300, self._auto_fill_login)

    def _auto_fill_login(self):
        if hasattr(self, 'login_username') and hasattr(self, 'login_password'):
            self.login_username.setText(self.username)
            self.login_password.setText(self.password)
            self.check_login_input()