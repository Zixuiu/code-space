"""
文件: beautiful_dialog.py
用途: 风格10「彩色标签」弹窗 - 左侧红色装饰条 + 白色卡片
"""

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QColor, QCursor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGraphicsDropShadowEffect, QApplication
)


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
        self._build(title, text, msg_type, buttons)
        self._add_shadow()
        QTimer.singleShot(0, self._center)
        QTimer.singleShot(50, self._fade_in)
    
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
        icon = QLabel({"information":"ℹ️","warning":"⚠️","critical":"❌","question":"❓"}[msg_type])
        icon.setStyleSheet("font-size:24px;background:transparent;")
        icon.setFixedSize(36,36)
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
            b.setFixedHeight(38)
            b.setMinimumWidth(88)
            if primary:
                b.setStyleSheet("QPushButton{background:#8E8E93;color:#fff;border:none;border-radius:8px;padding:8px 20px;font-size:14px;font-weight:600;}QPushButton:hover{background:#6E6E73;}")
            else:
                b.setStyleSheet("QPushButton{background:#F5F5F7;color:#4A4A6A;border:1px solid #E0E0E5;border-radius:8px;padding:8px 20px;font-size:14px;font-weight:500;}QPushButton:hover{background:#E8E8ED;}")
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
