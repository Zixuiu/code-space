# -*- coding: utf-8 -*-
"""
激活对话框风格预览
- 独立运行：python preview_activation_styles.py
- 模拟设置页背景（浅灰 + 白卡片，即弹窗原本容易"糊"进去的场景），
  点击任意按钮以对应风格打开 ActivationDialog，逐个对比挑喜欢的。
"""
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea,
)

import entitlement

# 预览不触发真实权益/网络逻辑，直接打桩
entitlement.get_pricing = lambda: {
    'plan_1': {'price': 99, 'months': 1},
    'channel_name': 'PayPro',
    'channel_url': 'https://example.com/buy',
}
entitlement.get_entitlement = lambda user: {'has_access': True}

from activation_dialog import ActivationDialog
from activation_styles import STYLES


class StylePreview(QWidget):
    """风格选择面板：模拟设置页背景 + 10 个风格按钮"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("激活弹窗风格预览（共 10 套）")
        self.setFixedSize(560, 640)
        self.setStyleSheet("QWidget{background:#F2F2F4;}")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        tip = QLabel("点击按钮，以该风格打开「账户与激活」弹窗")
        tip.setStyleSheet("font-size:13px;color:#86868B;background:transparent;")
        outer.addWidget(tip)

        # 模拟设置页里会被弹窗压住的白卡片，方便对比边界
        card = QLabel("会员与激活\n\n（弹窗会盖在这张白卡片上方，"
                      "用来检查弹窗边界是否清晰）")
        card.setAlignment(Qt.AlignCenter)
        card.setStyleSheet(
            "QLabel{background:#FFFFFF;border-radius:12px;"
            "font-size:14px;color:#B0B0B6;padding:18px;}")
        outer.addWidget(card)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        panel = QWidget()
        panel.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(10)

        for i, name in enumerate(STYLES, 1):
            btn = QPushButton(f"{i}. {name}")
            btn.setFixedHeight(44)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self._open(n))
            pl.addWidget(btn)
        pl.addStretch()
        area.setWidget(panel)
        outer.addWidget(area, 1)

    def _open(self, name):
        dlg = ActivationDialog(self, username="demo_user", style=name)
        dlg.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = StylePreview()
    w.show()
    sys.exit(app.exec_())
