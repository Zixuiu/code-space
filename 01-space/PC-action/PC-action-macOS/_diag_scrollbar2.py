"""诊断2：如何让 QScrollBar 既看不见又不占空间。用截图像素判断视觉。"""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtWidgets import (QApplication, QTreeWidget, QTreeWidgetItem, QWidget,
                             QVBoxLayout, QScrollBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor

app = QApplication(sys.argv)


def make_tree(n=50):
    tw = QTreeWidget()
    tw.setColumnCount(2)
    for i in range(n):
        QTreeWidgetItem(tw, [f"row{i}", "x"])
    return tw


def probe(tw, label):
    """统计滚动条区域是否有非透明像素（判断灰块是否可见）"""
    tw.ensurePolished()
    app.processEvents()
    pm = tw.grab()
    img = pm.toImage()
    w, h = img.width(), img.height()
    # 取最右侧 20px 竖带，统计有多少像素 alpha>0 且不是纯背景
    opaque = 0
    for x in range(max(0, w - 20), w):
        for y in range(0, h, 3):
            c = QColor(img.pixel(x, y))
            if c.alpha() > 0:
                opaque += 1
    print(f"{label:38s} 右20px带非透明像素={opaque:5d}  img={w}x{h}")
    return opaque


print("=== 基线：完全不处理 ===")
w0 = QWidget(); l0 = QVBoxLayout(w0)
t0 = make_tree(); l0.addWidget(t0); w0.resize(400, 200); w0.show(); app.processEvents()
base = probe(t0, "baseline")
print("  viewport 宽 =", t0.viewport().width())

print("\n=== 方案D：QSS 只让 handle/轨道/箭头透明（不设 width）===")
w1 = QWidget(); l1 = QVBoxLayout(w1)
t1 = make_tree(); l1.addWidget(t1); w1.resize(400, 200); w1.show(); app.processEvents()
t1.setStyleSheet("""
    QScrollBar:vertical { background: transparent; border: none; margin: 0px; }
    QScrollBar::handle:vertical { background: transparent; border: none; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: transparent; border: none; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent; }
""")
d = probe(t1, "QSS transparent only")
print("  viewport 宽 =", t1.viewport().width(), "(基线", t0.viewport().width(), ")")

print("\n=== 方案E：InvisibleScrollBar + setFixedWidth(0) ===")


class InvisibleScrollBar(QScrollBar):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.setFixedWidth(0)

    def sizeHint(self):
        return QSize(0, 0)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def paintEvent(self, e):
        pass


w2 = QWidget(); l2 = QVBoxLayout(w2)
t2 = make_tree(); l2.addWidget(t2)
t2.setVerticalScrollBar(InvisibleScrollBar(Qt.Vertical, t2))
w2.resize(400, 200); w2.show(); app.processEvents()
e = probe(t2, "InvisibleScrollBar fixedWidth(0)")
print("  viewport 宽 =", t2.viewport().width(), "(基线", t0.viewport().width(), ")")
print("  sb.width()  =", t2.verticalScrollBar().width())
print("  sb.maximum()=", t2.verticalScrollBar().maximum(), "(滚动能力必须 >0)")

print("\n=== 方案F：QSS transparent + 容器 QScrollArea 式 padding-right 补偿 ===")
w3 = QWidget(); l3 = QVBoxLayout(w3)
t3 = make_tree(); l3.addWidget(t3); w3.resize(400, 200); w3.show(); app.processEvents()
t3.setStyleSheet("""
    QTreeWidget { padding-right: 0px; }
    QScrollBar:vertical { background: transparent; border: none; margin: 0px;
                          width: 6px; }
    QScrollBar::handle:vertical { background: transparent; border: none; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: transparent; border: none; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent; }
""")
f = probe(t3, "QSS transparent + width:6px")
print("  viewport 宽 =", t3.viewport().width())

print("\n=== 结论 ===")
print("基线非透明像素:", base)
print("方案D(纯透明):", d, "->", "✅ 隐身" if d < base * 0.3 else "❌ 仍可见")
print("方案E(子类0宽):", e, "->", "✅ 隐身" if e < base * 0.3 else "❌ 仍可见")
