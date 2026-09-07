# -*- coding: utf-8 -*-
"""探针：build_styled_card + styled_button 渲染验证（删除确认同款卡片家族）。"""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
app = QApplication(sys.argv)

from beautiful_dialog import build_styled_card, styled_button

d = QDialog()
content = build_styled_card(d, "设置快捷键", "keyboard")

hint = QLabel("问终端")
hint.setAlignment(Qt.AlignCenter)
hint.setStyleSheet("font-size: 13px; color: #8E8E93; background: transparent; padding: 0 8px;")
content.addWidget(hint)

keycap = QLabel("未设置")
keycap.setAlignment(Qt.AlignCenter)
keycap.setStyleSheet("""
    font-size: 18px; font-weight: 600; letter-spacing: 2px;
    padding: 18px 14px;
    border: 1.5px dashed #D1D1D6;
    border-radius: 10px;
    background-color: #FAFAFA;
    color: #8E8E93;
    min-height: 44px;
""")
content.addWidget(keycap)

bl = QHBoxLayout()
bl.setSpacing(10)
bl.addStretch()
bl.addWidget(styled_button("清除", danger=True))
bl.addWidget(styled_button("确定", primary=True))
bl.addWidget(styled_button("取消", primary=False))
content.addLayout(bl)

d.setFixedWidth(420)
d.show()
app.processEvents()

img = d.grab().toImage()
w, h = img.width(), img.height()
c_center = img.pixelColor(w // 2, h // 2)
c_bar = img.pixelColor(3, h // 2)
c_corner = img.pixelColor(0, 0)
print(f"尺寸: {w}x{h}")
print(f"中心像素: ({c_center.red()},{c_center.green()},{c_center.blue()},{c_center.alpha()}) -> {'白卡OK' if c_center.red() > 250 and c_center.alpha() > 250 else '异常!'}")
print(f"左竖条像素: ({c_bar.red()},{c_bar.green()},{c_bar.blue()}) -> {'灰条OK' if abs(c_bar.red()-142) < 25 and abs(c_bar.green()-142) < 25 else '异常!'}")
print(f"左上角像素 alpha: {c_corner.alpha()} -> {'圆角透明OK' if c_corner.alpha() < 50 else '异常!'}")
img.save("_probe_card_render.png")
print("已保存 _probe_card_render.png")
