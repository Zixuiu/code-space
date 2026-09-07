# -*- coding: utf-8 -*-
"""
内嵌登录页（方案 7-7 · 左对齐极简）
====================================
不再使用独立登录弹窗，本页作为主窗口「账户」页内嵌显示（类似 VS Code / Edge）：
- 登录 / 注册 / 忘记密码 三种模式在页内切换
- 登录成功后发出 login_success(username) 信号，由主窗口接管（更新侧边栏徽标并跳回录制控制页）

所有尺寸 = login_style_preview_v7.py 中 build_v77 的原始值 × 统一缩放系数 SCALE，
保证与预览卡片比例完全一致（预览内容区约 526×408 → 真实内容区约 988×668）。
"""
import threading

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget,
)

# ============ 方案 7-7 原始规格（预览壳内 1:1）× 统一缩放 ============
SCALE = 1.75

# 颜色（与预览 build_v77 完全一致）
PAGE_BG = "#FFFFFF"        # CARD —— 预览 7-7 页面背景为纯白
INK = "#1D1D1F"            # 近黑胶囊
INK_HOVER = "#3A3A3C"
PRIMARY = "#5A6069"        # 主色（链接 / 聚焦下划线）
TEXT = "#1D1D1F"
TEXT2 = "#86868B"
TEXT3 = "#AEAEB2"
LINE = "#E8E8ED"           # 下划线（预览用 SEP）
FONT = '"Microsoft YaHei", "Segoe UI Emoji", sans-serif'

# 尺寸（括号内为预览原始值）
BLOCK_W = round(240 * SCALE)     # (240)  表单块宽度
TITLE_SIZE = round(15 * SCALE)   # (15)   页面标题
SUB_SIZE = round(10 * SCALE)     # (10)   副标题
CAPTION_SIZE = round(9 * SCALE)  # (9)    字段标签
FIELD_W = round(240 * SCALE)     # (240)  输入框宽度
FIELD_H = round(30 * SCALE)      # (30)   输入框高度
FIELD_SIZE = round(10 * SCALE)   # (10)   输入框字号
BTN_W = round(240 * SCALE)       # (240)  按钮宽度
BTN_H = round(34 * SCALE)        # (34)   按钮高度
BTN_SIZE = round(10 * SCALE)     # (10)   按钮字号
LINK_SIZE = round(9 * SCALE)     # (9)    页脚链接
VER_SIZE = round(8 * SCALE)      # (8)    版本号
SP_BASE = round(4 * SCALE)       # (4)    块内基础间距
SP_AFTER_SUB = round(14 * SCALE)     # (14) 副标题→用户名
SP_AFTER_FIELD = round(6 * SCALE)    # (6)  用户名→密码
SP_BEFORE_BTN = round(16 * SCALE)    # (16) 密码→按钮
SP_BEFORE_FOOT = round(12 * SCALE)   # (12) 按钮→页脚

VERSION = "v1.0.0"


def _label(text, size, color, bold=False, align=None):
    l = QLabel(text)
    w = "bold" if bold else "500"
    l.setStyleSheet(
        f"color:{color};font-size:{size}px;font-family:{FONT};font-weight:{w};border:none;background:transparent;")
    if align is not None:
        l.setAlignment(align)
    return l


def _field(password=False):
    """下划线输入框 —— 与预览 make_field(underline=True) 同比例"""
    e = QLineEdit()
    if password:
        e.setEchoMode(QLineEdit.Password)
    e.setFixedSize(FIELD_W, FIELD_H)
    e.setStyleSheet(f"""
        QLineEdit {{
            background: transparent;
            border: none;
            /* 必须显式清零：全局主题给 QLineEdit 设了 border-radius，
               会让只有底边的下划线两端沿圆角翘起 */
            border-radius: 0px;
            border-bottom: 2px solid {LINE};
            color: {TEXT};
            padding: 0 3px;
            font-size: {FIELD_SIZE}px;
            font-family: {FONT};
            font-weight: 500;
        }}
        QLineEdit:focus {{ border-bottom: 2px solid {PRIMARY}; }}
    """)
    return e


class PillButton(QPushButton):
    """手绘胶囊按钮：paintEvent 直接画圆角矩形。

    主窗口挂着 theme_generator 的全局 QPushButton QSS（min-height/padding/border-radius），
    会导致 QSS 圆角在本程序内渲染成直角；这里完全自己绘制背景，不依赖 QSS 圆角。
    """

    def __init__(self, text, width=BTN_W, height=BTN_H,
                 color=INK, hover_color=INK_HOVER):
        super().__init__(text)
        self._base_color = QColor(color)
        self._hover_color = QColor(hover_color)
        self._disabled_color = QColor(TEXT3)
        self._hovered = False
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)
        font = QFont()
        font.setFamilies(["Microsoft YaHei", "Segoe UI Emoji", "PingFang SC"])
        font.setPixelSize(BTN_SIZE)
        font.setWeight(QFont.Medium)
        self.setFont(font)
        # 仅让 QSS 不绘制任何背景/边框（背景由 paintEvent 负责）
        self.setStyleSheet(
            "QPushButton { background: transparent; border: none; }")

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        if not self.isEnabled():
            p.setBrush(self._disabled_color)
        elif self._hovered:
            p.setBrush(self._hover_color)
        else:
            p.setBrush(self._base_color)
        radius = self.height() / 2.0
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), radius, radius)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignCenter, self.text())


def _pill(text, width=BTN_W):
    return PillButton(text, width=width)


def _text_btn(text, color=PRIMARY, size=LINK_SIZE):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            border: none;
            padding: 0px;
            min-height: 0px;
            color: {color};
            font-size: {size}px;
            font-family: {FONT};
            font-weight: 500;
        }}
        QPushButton:hover {{ color: {INK}; }}
    """)
    return b


class _ModePage(QWidget):
    """单个模式页：居中的左对齐极简块（方案 7-7 原始布局 × SCALE）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch()

        block = QWidget()
        block.setFixedWidth(BLOCK_W)
        self.col = QVBoxLayout(block)
        self.col.setContentsMargins(0, 0, 0, 0)
        self.col.setSpacing(SP_BASE)
        outer.addWidget(block, 0, Qt.AlignHCenter)
        outer.addStretch()

    def add_title(self, title, sub):
        self.col.addWidget(_label(title, TITLE_SIZE, TEXT, bold=True))
        self.col.addWidget(_label(sub, SUB_SIZE, TEXT2))
        self.col.addSpacing(SP_AFTER_SUB)

    def add_field(self, caption, password=False, extra=None):
        self.col.addWidget(_label(caption, CAPTION_SIZE, TEXT3))
        f = _field(password=password)
        if extra is not None:
            # 下划线随行伸展，尾部放「发送验证码」
            f.setFixedWidth(FIELD_W - 180)
            row = QWidget()
            rh = QHBoxLayout(row)
            rh.setContentsMargins(0, 0, 0, 0)
            rh.setSpacing(SP_BASE)
            rh.addWidget(f)
            rh.addStretch()
            rh.addWidget(extra)
            self.col.addWidget(row)
        else:
            self.col.addWidget(f)
        return f

    def add_status(self):
        self.status = _label("", LINK_SIZE, "#FF3B30")
        self.status.setWordWrap(True)
        self.status.hide()
        self.col.addWidget(self.status)
        return self.status

    def add_button(self, text):
        btn = _pill(text)
        self.col.addSpacing(SP_BEFORE_BTN)
        self.col.addWidget(btn)
        return btn

    def add_footer(self, links):
        """links: [(text, callback), ...] 左对齐排列，右侧版本号（同预览 7-7 页脚）"""
        self.col.addSpacing(SP_BEFORE_FOOT)
        row = QWidget()
        rh = QHBoxLayout(row)
        rh.setContentsMargins(0, 0, 0, 0)
        rh.setSpacing(SP_BEFORE_FOOT)
        for text, cb in links:
            link = _text_btn(text)
            if cb is not None:
                link.clicked.connect(cb)
            rh.addWidget(link)
        rh.addStretch()
        rh.addWidget(_label(VERSION, VER_SIZE, TEXT3))
        self.col.addWidget(row)


class LoginPane(QWidget):
    """主窗口内嵌的账户页（登录 / 注册 / 忘记密码）"""

    login_success = pyqtSignal(str)
    _code_sent = pyqtSignal(bool, str, object, object)
    _register_done = pyqtSignal(bool, str)

    MODE_LOGIN, MODE_REGISTER, MODE_RESET = 0, 1, 2

    def __init__(self, login_manager, parent=None):
        super().__init__(parent)
        self.login_manager = login_manager
        # 方案 7-7 页面背景为纯白（CARD）；自定义 QWidget 需要 WA_StyledBackground 才会绘制 QSS 背景。
        # 圆角：左侧两角 12px（与其它页面 MacOSCard 一致），右下角 28px 跟随窗口外框曲线，
        # 避免白色方角盖住窗口圆角（QSS 顺序：左上 右上 右下 左下）
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            f"background: {PAGE_BG}; border-radius: 12px 12px 28px 12px;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        root.addWidget(self.stack)

        self._build_login_page()
        self._build_register_page()
        self._build_reset_page()

        self._code_sent.connect(self._on_code_sent)
        self._register_done.connect(self._on_register_done)

        # 预填已保存的登录信息（与旧版「记住我」行为一致）
        try:
            saved_user, saved_pwd = self.login_manager.load_saved_login()
            if saved_user:
                self.login_username.setText(saved_user)
            if saved_pwd:
                self.login_password.setText(saved_pwd)
        except Exception:
            pass

        self.stack.setCurrentIndex(self.MODE_LOGIN)

    # ---------- 页面构建 ----------

    def _build_login_page(self):
        page = _ModePage()
        page.add_title("欢迎回来", "登录你的账户以继续")
        self.login_username = page.add_field("用户名")
        self.login_password = page.add_field("密码", password=True)
        self.login_status = page.add_status()
        self.login_btn = page.add_button("登录  →")
        self.login_btn.clicked.connect(self._do_login)
        page.add_footer([
            ("创建账户", lambda: self._switch(self.MODE_REGISTER)),
            ("忘记密码?", lambda: self._switch(self.MODE_RESET)),
        ])
        self.stack.addWidget(page)

    def _build_register_page(self):
        page = _ModePage()
        page.add_title("创建账户", "注册后可同步你的流程数据")
        self.reg_username = page.add_field("用户名")
        self.reg_password = page.add_field("密码", password=True)
        self.reg_email = page.add_field("邮箱")
        self.reg_send_btn = _text_btn("发送验证码")
        self.reg_send_btn.clicked.connect(
            lambda: self._send_code(self.reg_email, self.reg_status, self.reg_send_btn, self.reg_code))
        self.reg_code = page.add_field("验证码", extra=self.reg_send_btn)
        self.reg_status = page.add_status()
        self.register_btn = page.add_button("注册  →")
        self.register_btn.clicked.connect(self._do_register)
        page.add_footer([("返回登录", lambda: self._switch(self.MODE_LOGIN))])
        self.stack.addWidget(page)

    def _build_reset_page(self):
        page = _ModePage()
        page.add_title("重置密码", "通过注册邮箱验证身份")
        self.reset_email = page.add_field("邮箱")
        self.reset_send_btn = _text_btn("发送验证码")
        self.reset_send_btn.clicked.connect(
            lambda: self._send_code(self.reset_email, self.reset_status, self.reset_send_btn, self.reset_code))
        self.reset_code = page.add_field("验证码", extra=self.reset_send_btn)
        self.reset_new_password = page.add_field("新密码", password=True)
        self.reset_status = page.add_status()
        self.reset_btn = page.add_button("重置密码  →")
        self.reset_btn.clicked.connect(self._do_reset)
        page.add_footer([("返回登录", lambda: self._switch(self.MODE_LOGIN))])
        self.stack.addWidget(page)

    # ---------- 通用 ----------

    def _switch(self, mode):
        self.stack.setCurrentIndex(mode)

    @staticmethod
    def _show(label, text, error=True):
        label.setText(text)
        label.setStyleSheet(
            f"color:{'#FF3B30' if error else '#34C759'};font-size:{LINK_SIZE}px;"
            f"font-family:{FONT};font-weight:500;border:none;background:transparent;")
        label.show()

    # ---------- 登录 ----------

    def _do_login(self):
        u = self.login_username.text().strip()
        p = self.login_password.text()
        if not u or not p:
            self._show(self.login_status, "请输入用户名和密码")
            return
        self.login_status.hide()
        ok, result = self.login_manager.login(u, p)
        if ok:
            try:
                self.login_manager.save_login_credentials(u, p)
            except Exception:
                pass
            self.login_success.emit(u)
        else:
            self._show(self.login_status, str(result))

    # ---------- 注册 ----------

    def _do_register(self):
        u = self.reg_username.text().strip()
        p = self.reg_password.text()
        email = self.reg_email.text().strip()
        code = self.reg_code.text().strip()
        if not u or not p or not email:
            self._show(self.reg_status, "请填写用户名、密码和邮箱")
            return
        if not code:
            self._show(self.reg_status, "请先获取并输入验证码")
            return
        self.register_btn.setEnabled(False)
        self._show(self.reg_status, "正在注册…", error=False)

        def work():
            try:
                ok, msg = self.login_manager.register(u, p, email, code)
            except Exception as e:
                ok, msg = False, f"注册出错: {e}"
            self._register_done.emit(bool(ok), str(msg))

        threading.Thread(target=work, daemon=True).start()

    def _on_register_done(self, ok, msg):
        self.register_btn.setEnabled(True)
        self._show(self.reg_status, msg, error=not ok)
        if ok:
            username = self.reg_username.text().strip()
            self._switch(self.MODE_LOGIN)
            self.login_username.setText(username)
            self.login_password.clear()
            self._show(self.login_status, "注册成功，请登录", error=False)

    # ---------- 忘记密码 ----------

    def _do_reset(self):
        email = self.reset_email.text().strip()
        code = self.reset_code.text().strip()
        pwd = self.reset_new_password.text()
        if not email or not code or not pwd:
            self._show(self.reset_status, "请填写邮箱、验证码和新密码")
            return
        ok, msg = self.login_manager.reset_password(email, pwd, code)
        self._show(self.reset_status, msg, error=not ok)
        if ok:
            self._switch(self.MODE_LOGIN)
            self._show(self.login_status, "密码已重置，请使用新密码登录", error=False)

    # ---------- 验证码（注册/重置共用） ----------

    def _send_code(self, email_field, status, btn, fill_field):
        email = email_field.text().strip()
        if not email:
            self._show(status, "请先填写邮箱")
            return
        btn.setEnabled(False)
        btn.setText("发送中…")

        def work():
            try:
                ok, msg, code = self.login_manager.send_verification_code(email)
            except Exception as e:
                ok, msg, code = False, f"发送出错: {e}", None
            self._code_sent.emit(bool(ok), str(msg), code, (btn, fill_field))

        threading.Thread(target=work, daemon=True).start()

    def _on_code_sent(self, ok, msg, code, targets):
        btn, fill_field = targets
        text = msg
        if ok and code:
            # SMTP 未配置时的回退：验证码直接返回，自动填入
            if fill_field is not None:
                fill_field.setText(str(code))
            text = f"{msg}（已自动填入）"
        self._show(status, text, error=not ok)
        if ok:
            # 发送成功后进入 60 秒冷却倒计时，期间不可再发
            self._start_send_countdown(btn, 60)
        else:
            btn.setEnabled(True)
            btn.setText("发送验证码")

    def _start_send_countdown(self, btn, seconds):
        """验证码冷却倒计时：按钮禁用并每秒倒计时，期间不可重发"""
        if not hasattr(self, "_send_countdowns"):
            self._send_countdowns = {}
        self._send_countdowns[btn] = max(1, seconds)
        btn.setEnabled(False)
        btn.setText(f"{seconds}s 后可重发")
        if getattr(self, "_send_countdown_timer", None) is None:
            self._send_countdown_timer = QTimer(self)
            self._send_countdown_timer.setInterval(1000)
            self._send_countdown_timer.timeout.connect(self._on_send_countdown_tick)
            self._send_countdown_timer.start()

    def _on_send_countdown_tick(self):
        cds = getattr(self, "_send_countdowns", {})
        for btn, left in list(cds.items()):
            cds[btn] = left - 1
            if cds[btn] > 0:
                btn.setText(f"{cds[btn]}s 后可重发")
            else:
                btn.setEnabled(True)
                btn.setText("发送验证码")
                del cds[btn]
        if not cds and getattr(self, "_send_countdown_timer", None) is not None:
            self._send_countdown_timer.stop()
