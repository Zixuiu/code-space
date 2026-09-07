# -*- coding: utf-8 -*-
"""探针：验证 apply_dialog_style 修复后 QSS 可解析、对话框背景为实心白卡。"""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QImage

app = QApplication(sys.argv)

import styles

# 1) 语法层面：所有大 QSS 字符串引号/花括号必须配平
qss_sources = {}
for name in dir(styles):
    if name.startswith(("get_", "apply_")):
        fn = getattr(styles, name)
        if not callable(fn):
            continue
        try:
            v = fn(1920, 1080) if name.startswith("get_") else None
        except Exception as e:
            print(f"[SKIP] {name}: {e}")
            continue
        if isinstance(v, str) and "{" in v:
            qss_sources[name] = v

bad = 0
for name, qss in qss_sources.items():
    if qss.count('"') % 2 != 0:
        print(f"[FAIL] {name}: 双引号不配对 ({qss.count(chr(34))})")
        bad += 1
    if qss.count("{") != qss.count("}"):
        print(f"[FAIL] {name}: 花括号不配对 {{={qss.count('{')} }}={qss.count('}')}")
        bad += 1
print(f"语法检查：{len(qss_sources)} 个 QSS，坏 {bad} 个")

# 2) 渲染层面：apply_dialog_style 后对话框应为实心白卡
d = QDialog()
styles.apply_dialog_style(d)
d.resize(300, 200)
d.show()
app.processEvents()
img = d.grab().toImage()
c = img.pixelColor(150, 100)
print(f"中心像素 RGBA: ({c.red()},{c.green()},{c.blue()},{c.alpha()}) -> {'白卡OK' if (c.red()>250 and c.green()>250 and c.blue()>250 and c.alpha()>250) else '仍然异常!'}")
print(f"QDialog 规则生效(样式表非空): {len(d.styleSheet()) > 100}")
