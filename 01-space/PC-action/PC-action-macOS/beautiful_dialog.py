"""
文件: beautiful_dialog.py
用途: 风格10「彩色标签」弹窗 - 左侧红色装饰条 + 白色卡片
"""

import os

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize, QByteArray
from PyQt5.QtGui import QColor, QCursor, QIcon, QPainter, QPixmap
try:
    from PyQt5.QtSvg import QSvgRenderer
    _SVG_OK = True
except Exception:
    _SVG_OK = False
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGraphicsDropShadowEffect, QApplication,
    QLineEdit, QDoubleSpinBox
)


# 图标统一放大系数（用户反馈图标偏小）——改这一个值即可全局调整所有图标大小
ICON_SCALE = 1.8

def load_svg_icon(name, size=28, color=None):
    """按脚本绝对路径定位 icons/，渲染 SVG → QIcon；异常兜底返回空 QIcon。
    color 为 None 时保留 SVG 原有语义配色；传 color 则统一为指定色。"""
    import re
    size = int(round(size * ICON_SCALE))
    _p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", f"{name}.svg")
    if not _SVG_OK or not os.path.exists(_p):
        return QIcon()
    _pm = QPixmap(QSize(size, size))
    _pm.fill(Qt.transparent)
    if color is None:
        _r = QSvgRenderer(_p)
    else:
        with open(_p, "r", encoding="utf-8") as f:
            svg = f.read()
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
        _r = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    _painter = QPainter(_pm)
    _painter.setRenderHint(QPainter.Antialiasing)
    _r.render(_painter)
    _painter.end()
    return QIcon(_pm)


class StyledMessageDialog(QDialog):
    """风格10: 彩色标签 - 左侧红色竖条 + 白色卡片"""
    
    OK, CANCEL, YES, NO = 1, 2, 3, 4
    
    def __init__(self, parent=None, title="提示", text="",
                 msg_type="information", buttons="ok"):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(420)
        self._result = self.OK
        self._buttons_mode = buttons      # 供 keyPressEvent 判断 Enter/Esc 该走哪个分支
        self._build(title, text, msg_type, buttons)
        self._add_shadow()
        QTimer.singleShot(0, self._center)
        QTimer.singleShot(50, self._fade_in)
        QTimer.singleShot(60, self._focus_primary)
        install_drag_move(self)
    
    def _build(self, title, text, msg_type, buttons):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setObjectName("C")
        container.setStyleSheet("QWidget#C{background:#FFFFFF;border:none;border-radius:12px;}")
        
        row = QHBoxLayout()
        row.setContentsMargins(0,0,0,0)
        row.setSpacing(0)
        
        bar = QLabel()
        bar.setFixedWidth(8)
        bar.setStyleSheet("background:#8E8E93;border-radius:12px 0 0 12px;")
        row.addWidget(bar)
        
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24,28,28,24)
        cl.setSpacing(16)
        
        # 标题
        hr = QHBoxLayout()
        _icon_map = {"information":"info","warning":"warning","critical":"error","question":"question"}
        icon = QLabel()
        icon.setPixmap(load_svg_icon(_icon_map.get(msg_type, "info"), 28).pixmap(int(round(28 * ICON_SCALE)), int(round(28 * ICON_SCALE))))
        icon.setStyleSheet("background:transparent;")
        icon.setFixedSize(56,56)
        icon.setAlignment(Qt.AlignCenter)
        hr.addWidget(icon)
        tl = QLabel(title)
        tl.setStyleSheet("font-size:18px;font-weight:700;color:#1A1A2E;background:transparent;")
        hr.addWidget(tl,1)
        cl.addLayout(hr)
        
        # 正文
        txt = QLabel(text)
        txt.setStyleSheet("font-size:14px;line-height:1.6;color:#4A4A6A;background:transparent;padding:4px 0 8px 0;")
        txt.setWordWrap(True)
        cl.addWidget(txt)
        cl.addStretch()
        
        # 按钮
        bl = QHBoxLayout()
        bl.addStretch()
        
        def mkbtn(text, val, primary=True):
            b = QPushButton(text)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setFixedHeight(32)
            b.setMinimumWidth(80)
            if primary:
                b.setStyleSheet("QPushButton{background:#5A6069;color:#fff;border:none;border-radius:8px;padding:0 12px;font-size:13px;font-weight:600;}QPushButton:hover{background:#6B7178;}QPushButton:pressed{background:#474C54;}")
                # 主按钮：Enter 就走它（用户要求「Enter 默认＝是/确定」）
                b.setDefault(True)
                b.setAutoDefault(True)
            else:
                b.setStyleSheet("QPushButton{background:#FFFFFF;color:#5A6069;border:1px solid #D1D1D6;border-radius:8px;padding:0 12px;font-size:13px;font-weight:600;}QPushButton:hover{background:#F0F0F2;color:#474C54;}QPushButton:pressed{background:#E8E8ED;}")
                # 次按钮：关掉 autoDefault，避免它抢走 Enter
                b.setAutoDefault(False)
                b.setDefault(False)
            b.clicked.connect(lambda: self._done(val))
            return b
        
        if buttons == "ok": bl.addWidget(mkbtn("确 定", self.OK))
        elif buttons == "ok_cancel":
            bl.addWidget(mkbtn("取 消", self.CANCEL, False))
            bl.addWidget(mkbtn("确 定", self.OK))
        elif buttons == "yes_no":
            bl.addWidget(mkbtn("否", self.NO, False))
            bl.addWidget(mkbtn("是", self.YES))
        elif buttons == "yes_no_cancel":
            bl.addWidget(mkbtn("取 消", self.CANCEL, False))
            bl.addWidget(mkbtn("否", self.NO, False))
            bl.addWidget(mkbtn("是", self.YES))
        
        cl.addLayout(bl)
        row.addWidget(content, 1)
        
        cl2 = QVBoxLayout(container)
        cl2.setContentsMargins(0,0,0,0)
        cl2.addLayout(row)
        layout.addWidget(container)

    def keyPressEvent(self, event):
        """Enter / Return = 确认（是/确定）；Esc = 取消（否/取消）。"""
        k = event.key()
        if k in (Qt.Key_Return, Qt.Key_Enter):
            # 有「是」就按「是」，否则按「确定」
            self._done(self.YES if self._has_yes() else self.OK)
            event.accept()
            return
        if k == Qt.Key_Escape:
            # Esc 优先级：能取消就取消，其次「否」；只有一个「确定」按钮时只能按确定
            if self._buttons_mode in ("ok_cancel", "yes_no_cancel"):
                self._done(self.CANCEL)
            elif self._has_yes():
                self._done(self.NO)
            else:
                self._done(self.OK)
            event.accept()
            return
        super().keyPressEvent(event)

    def _has_yes(self):
        return self._buttons_mode in ("yes_no", "yes_no_cancel")

    def _focus_primary(self):
        """把初始焦点放到主按钮（确定/是），让 Enter 与点击行为一致。"""
        for b in self.findChildren(QPushButton):
            if b.isDefault():
                b.setFocus()
                return
    
    def _add_shadow(self):
        c = self.findChild(QWidget, "C")
        if c:
            s = QGraphicsDropShadowEffect()
            s.setBlurRadius(40)
            s.setColor(QColor(142,142,147,30))
            s.setOffset(0,8)
            c.setGraphicsEffect(s)
    
    def _center(self):
        p = self.parent()
        if p:
            r = p.geometry()
            self.move(r.center().x()-self.width()//2, r.center().y()-self.height()//2)
        else:
            s = QApplication.primaryScreen().geometry()
            self.move(s.center().x()-self.width()//2, s.center().y()-self.height()//2)
    
    def _fade_in(self):
        self.a = QPropertyAnimation(self, b"windowOpacity")
        self.a.setDuration(180)
        self.a.setStartValue(0.0)
        self.a.setEndValue(1.0)
        self.a.setEasingCurve(QEasingCurve.OutCubic)
        self.a.start()
    
    def _done(self, r):
        self._result = r
        self.accept()
    
    def get_result(self):
        return self._result


class StyledInputDialog(QDialog):
    """与 StyledMessageDialog 风格统一的输入框弹窗（无边框、白卡、左侧竖条、圆角、阴影）。

    mode="text" 时返回字符串；mode="double" 时使用 QDoubleSpinBox，返回浮点数。
    """

    OK, CANCEL = 1, 2

    def __init__(self, parent=None, title="输入", label="请输入：", text="", placeholder="",
                 mode="text", value=0.0, min_value=0.0, max_value=100.0, decimals=1, step=0.1):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(420)
        self._result = self.CANCEL
        self._mode = mode
        self._text = text
        self._double_value = value
        self._build(title, label, text, placeholder, value, min_value, max_value, decimals, step)
        self._add_shadow()
        QTimer.singleShot(0, self._center)
        QTimer.singleShot(50, self._fade_in)
        install_drag_move(self)

    def _build(self, title, label, text, placeholder, value, min_value, max_value, decimals, step):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setObjectName("C")
        container.setStyleSheet("QWidget#C{background:#FFFFFF;border:none;border-radius:12px;}")

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        bar = QLabel()
        bar.setFixedWidth(8)
        bar.setStyleSheet("background:#8E8E93;border-radius:12px 0 0 12px;")
        row.addWidget(bar)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 28, 28, 24)
        cl.setSpacing(16)

        # 标题
        hr = QHBoxLayout()
        icon = QLabel()
        icon_name = "text" if self._mode == "text" else "edit"
        icon.setPixmap(load_svg_icon(icon_name, 26).pixmap(int(round(26 * ICON_SCALE)), int(round(26 * ICON_SCALE))))
        icon.setStyleSheet("background:transparent;")
        icon.setFixedSize(48, 48)
        icon.setAlignment(Qt.AlignCenter)
        hr.addWidget(icon)
        tl = QLabel(title)
        tl.setStyleSheet("font-size:18px;font-weight:700;color:#1A1A2E;background:transparent;")
        hr.addWidget(tl, 1)
        cl.addLayout(hr)

        # 提示文字
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size:14px;color:#4A4A6A;background:transparent;padding:0 0 4px 0;")
        cl.addWidget(lbl)

        # 输入框
        if self._mode == "double":
            self.spin_box = QDoubleSpinBox()
            self.spin_box.setRange(min_value, max_value)
            self.spin_box.setDecimals(decimals)
            self.spin_box.setSingleStep(step)
            self.spin_box.setValue(value)
            self.spin_box.setStyleSheet("""
                QDoubleSpinBox {
                    background:#FAFAFA;
                    color:#1A1A2E;
                    border:1px solid #D1D1D6;
                    border-radius:8px;
                    padding:8px 12px;
                    font-size:14px;
                    font-family:'PingFang SC','Microsoft YaHei','Helvetica Neue','Segoe UI',sans-serif;
                }
                QDoubleSpinBox:focus {
                    border:2px solid #5A6069;
                }
                QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                    width:0;
                    border:none;
                }
            """)
            self.spin_box.setMinimumHeight(36)
            cl.addWidget(self.spin_box)
            self.line_edit = None
        else:
            self.line_edit = QLineEdit(text)
            self.line_edit.setClearButtonEnabled(True)
            if placeholder:
                self.line_edit.setPlaceholderText(placeholder)
            self.line_edit.setStyleSheet("""
                QLineEdit {
                    background:#FAFAFA;
                    color:#1A1A2E;
                    border:1px solid #D1D1D6;
                    border-radius:8px;
                    padding:8px 12px;
                    font-size:14px;
                    font-family:'PingFang SC','Microsoft YaHei','Helvetica Neue','Segoe UI',sans-serif;
                }
                QLineEdit:focus {
                    border:2px solid #5A6069;
                }
            """)
            self.line_edit.setMinimumHeight(36)
            cl.addWidget(self.line_edit)
            self.spin_box = None

        # 错误/额外提示（预留）
        self._hint = QLabel("")
        self._hint.setStyleSheet("font-size:12px;color:#FF3B30;background:transparent;padding:0;")
        self._hint.hide()
        cl.addWidget(self._hint)

        cl.addStretch()

        # 按钮
        bl = QHBoxLayout()
        bl.addStretch()

        def mkbtn(btn_text, val, primary=True):
            b = QPushButton(btn_text)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setFixedHeight(32)
            b.setMinimumWidth(80)
            if primary:
                b.setStyleSheet("QPushButton{background:#5A6069;color:#fff;border:none;border-radius:8px;padding:0 12px;font-size:13px;font-weight:600;}QPushButton:hover{background:#6B7178;}QPushButton:pressed{background:#474C54;}")
                # 主按钮＝确定：Enter 走它
                b.setDefault(True)
                b.setAutoDefault(True)
            else:
                b.setStyleSheet("QPushButton{background:#FFFFFF;color:#5A6069;border:1px solid #D1D1D6;border-radius:8px;padding:0 12px;font-size:13px;font-weight:600;}QPushButton:hover{background:#F0F0F2;color:#474C54;}QPushButton:pressed{background:#E8E8ED;}")
                b.setAutoDefault(False)
                b.setDefault(False)
            b.clicked.connect(lambda: self._done(val))
            return b

        bl.addWidget(mkbtn("取 消", self.CANCEL, False))
        bl.addWidget(mkbtn("确 定", self.OK))

        cl.addLayout(bl)
        row.addWidget(content, 1)

        cl2 = QVBoxLayout(container)
        cl2.setContentsMargins(0, 0, 0, 0)
        cl2.addLayout(row)
        layout.addWidget(container)

        # 输入框里按 Enter 直接确认（QLineEdit 会吞掉 Enter，不会传给 QDialog）
        if self.line_edit is not None:
            self.line_edit.returnPressed.connect(lambda: self._done(self.OK))
        elif self.spin_box is not None and self.spin_box.lineEdit() is not None:
            # QDoubleSpinBox 没有 returnPressed，只能连它内部的 QLineEdit
            self.spin_box.lineEdit().returnPressed.connect(lambda: self._done(self.OK))

    def keyPressEvent(self, event):
        """Enter / Return = 确定；Esc = 取消。"""
        k = event.key()
        if k in (Qt.Key_Return, Qt.Key_Enter):
            self._done(self.OK)
            event.accept()
            return
        if k == Qt.Key_Escape:
            self._done(self.CANCEL)
            event.accept()
            return
        super().keyPressEvent(event)

    def set_text(self, text):
        if self.line_edit:
            self.line_edit.setText(text)

    def get_text(self):
        if self.line_edit:
            return self.line_edit.text()
        return ""

    def get_value(self):
        if self.spin_box:
            return self.spin_box.value()
        return 0.0

    def set_hint(self, text):
        if text:
            self._hint.setText(text)
            self._hint.show()
        else:
            self._hint.hide()

    def _add_shadow(self):
        c = self.findChild(QWidget, "C")
        if c:
            s = QGraphicsDropShadowEffect()
            s.setBlurRadius(40)
            s.setColor(QColor(142, 142, 147, 30))
            s.setOffset(0, 8)
            c.setGraphicsEffect(s)

    def _center(self):
        p = self.parent()
        if p:
            r = p.geometry()
            self.move(r.center().x() - self.width() // 2, r.center().y() - self.height() // 2)
        else:
            s = QApplication.primaryScreen().geometry()
            self.move(s.center().x() - self.width() // 2, s.center().y() - self.height() // 2)

    def _fade_in(self):
        self.a = QPropertyAnimation(self, b"windowOpacity")
        self.a.setDuration(180)
        self.a.setStartValue(0.0)
        self.a.setEndValue(1.0)
        self.a.setEasingCurve(QEasingCurve.OutCubic)
        self.a.start()

    def _done(self, r):
        self._result = r
        if r == self.OK:
            self.accept()
        else:
            self.reject()

    def get_result(self):
        return self._result


def show_styled_input(parent=None, title="输入", label="请输入：", text="", placeholder=""):
    """封装成类似 QInputDialog.getText 的便捷调用，返回 (text, ok)。"""
    dialog = StyledInputDialog(parent, title, label, text, placeholder, mode="text")
    ok = dialog.exec_() == QDialog.Accepted
    return dialog.get_text(), ok


def show_styled_double(parent=None, title="输入数值", label="请输入数值：", value=0.0,
                       min_value=0.0, max_value=100.0, decimals=1, step=0.1):
    """封装成类似 QInputDialog.getDouble 的便捷调用，返回 (value, ok)。"""
    dialog = StyledInputDialog(parent, title, label, mode="double",
                               value=value, min_value=min_value, max_value=max_value,
                               decimals=decimals, step=step)
    ok = dialog.exec_() == QDialog.Accepted
    return dialog.get_value(), ok


# ============================================
# 「删除确认」同款卡片骨架（自定义弹窗对齐全家桶样式用）
# ============================================

def add_card_shadow(widget):
    """卡片投影（与 StyledMessageDialog 一致）。"""
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(40)
    s.setColor(QColor(142, 142, 147, 30))
    s.setOffset(0, 8)
    widget.setGraphicsEffect(s)


def build_styled_card(dialog, title, icon_name="info"):
    """把任意 QDialog 装进「删除确认」同款卡片：半透明窗口 + 实心白圆角卡
    + 左侧灰竖条 + 图标 + 粗体标题。返回 content QVBoxLayout（往里塞自己的内容）。

    ⚠️ 背景由实心容器绘制——WA_TranslucentBackground 下顶层 QDialog 的
    QSS background-color 不会被绘制（整窗透明教训，2026-09-06）。
    按钮请用 styled_button() 保证配色同族。
    """
    dialog.setWindowFlags(dialog.windowFlags() | Qt.Dialog | Qt.FramelessWindowHint)
    dialog.setAttribute(Qt.WA_TranslucentBackground)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)

    container = QWidget()
    container.setObjectName("C")
    container.setStyleSheet("QWidget#C{background:#FFFFFF;border:none;border-radius:12px;}")

    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(0)

    bar = QLabel()
    bar.setFixedWidth(8)
    bar.setStyleSheet("background:#8E8E93;border-radius:12px 0 0 12px;")
    row.addWidget(bar)

    content = QWidget()
    cl = QVBoxLayout(content)
    cl.setContentsMargins(24, 28, 28, 24)
    cl.setSpacing(16)

    hr = QHBoxLayout()
    icon = QLabel()
    icon.setPixmap(load_svg_icon(icon_name, 28).pixmap(int(round(28 * ICON_SCALE)), int(round(28 * ICON_SCALE))))
    icon.setStyleSheet("background:transparent;")
    icon.setFixedSize(56, 56)
    icon.setAlignment(Qt.AlignCenter)
    hr.addWidget(icon)
    tl = QLabel(title)
    tl.setStyleSheet("font-size:18px;font-weight:700;color:#1A1A2E;background:transparent;")
    hr.addWidget(tl, 1)
    cl.addLayout(hr)

    row.addWidget(content, 1)
    cl2 = QVBoxLayout(container)
    cl2.setContentsMargins(0, 0, 0, 0)
    cl2.addLayout(row)
    layout.addWidget(container)
    add_card_shadow(container)
    install_drag_move(dialog)
    return cl


def styled_button(text, primary=True, danger=False):
    """删除确认同族按钮。primary=深灰主按钮；primary=False=白底描边次按钮；
    danger=True=白底红字（清除等破坏性操作，自动覆盖 primary）。
    一律不设 default（录入型弹窗要自己接管 Enter/按键）。"""
    if danger:
        primary = False
    b = QPushButton(text)
    b.setCursor(QCursor(Qt.PointingHandCursor))
    b.setFixedHeight(32)
    b.setMinimumWidth(80)
    if primary:
        b.setStyleSheet("QPushButton{background:#5A6069;color:#fff;border:none;border-radius:8px;padding:0 12px;font-size:13px;font-weight:600;}QPushButton:hover{background:#6B7178;}QPushButton:pressed{background:#474C54;}")
    elif danger:
        b.setStyleSheet("QPushButton{background:#FFFFFF;color:#FF3B30;border:1px solid #FFD1CC;border-radius:8px;padding:0 12px;font-size:13px;font-weight:600;}QPushButton:hover{background:#FFF0EE;}QPushButton:pressed{background:#FFE3DF;}")
    else:
        b.setStyleSheet("QPushButton{background:#FFFFFF;color:#5A6069;border:1px solid #D1D1D6;border-radius:8px;padding:0 12px;font-size:13px;font-weight:600;}QPushButton:hover{background:#F0F0F2;color:#474C54;}QPushButton:pressed{background:#E8E8ED;}")
    b.setAutoDefault(False)
    b.setDefault(False)
    return b


def center_dialog(dialog):
    """show 后居中到父窗口（无父级则居中到屏幕）。"""
    def _c():
        p = dialog.parent()
        if p:
            r = p.geometry()
            dialog.move(r.center().x() - dialog.width() // 2, r.center().y() - dialog.height() // 2)
        else:
            s = QApplication.primaryScreen().geometry()
            dialog.move(s.center().x() - dialog.width() // 2, s.center().y() - dialog.height() // 2)
    QTimer.singleShot(0, _c)


def fade_in_dialog(dialog):
    """180ms 淡入（与 StyledMessageDialog 一致）。"""
    dialog._fade_anim = QPropertyAnimation(dialog, b"windowOpacity")
    dialog._fade_anim.setDuration(180)
    dialog._fade_anim.setStartValue(0.0)
    dialog._fade_anim.setEndValue(1.0)
    dialog._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
    QTimer.singleShot(50, dialog._fade_anim.start)


def install_drag_move(dialog):
    """让无边框弹窗可拖动：按住窗口空白/标题区（非交互控件）拖拽即移动。

    交互控件（按钮/输入框/下拉框）会自行消费鼠标事件、不会冒泡到弹窗，
    因此从它们上面点按不会触发拖动；标签/标题/留白区域会冒泡上来 → 可拖动。
    采用实例方法覆写，并链式调用原同名方法，互不影响其它逻辑。
    """
    _orig_press = getattr(dialog, "mousePressEvent", None)
    _orig_move = getattr(dialog, "mouseMoveEvent", None)
    _orig_release = getattr(dialog, "mouseReleaseEvent", None)
    _st = {"pos": None}

    def _press(e):
        if e.button() == Qt.LeftButton:
            _st["pos"] = e.globalPos() - dialog.frameGeometry().topLeft()
            e.accept()
            return
        if _orig_press:
            _orig_press(e)

    def _move_event(e):
        if _st["pos"] is not None and (e.buttons() & Qt.LeftButton):
            dialog.move(e.globalPos() - _st["pos"])
            e.accept()
            return
        if _orig_move:
            _orig_move(e)

    def _release(e):
        if _st["pos"] is not None:
            _st["pos"] = None
            e.accept()
            return
        if _orig_release:
            _orig_release(e)

    dialog.mousePressEvent = _press
    dialog.mouseMoveEvent = _move_event
    dialog.mouseReleaseEvent = _release
