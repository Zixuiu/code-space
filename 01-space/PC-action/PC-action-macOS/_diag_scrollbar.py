"""诊断：QTreeWidget 上的 QSS 是否会级联到它的 QScrollBar 子控件。"""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

app = QApplication(sys.argv)

w = QWidget()
lay = QVBoxLayout(w)
tw = QTreeWidget()
tw.setColumnCount(2)
tw.setHeaderLabels(["a", "b"])
for i in range(50):
    QTreeWidgetItem(tw, [f"row{i}", "x"])
lay.addWidget(tw)
w.resize(400, 200)
w.show()
app.processEvents()

vsb = tw.verticalScrollBar()
print("=== 未设样式 ===")
print("vsb.width()  =", vsb.width())
print("vsb.height() =", vsb.height())

# 方案 A：在 QTreeWidget 上用 `QScrollBar:vertical {...}`
tw.setStyleSheet("""
    QScrollBar:vertical { background: transparent; border: none; width: 0px; margin: 0px; }
    QScrollBar::handle:vertical { background: transparent; min-height: 0px; }
""")
app.processEvents()
print("\n=== 方案A：QTreeWidget 上写 QScrollBar:vertical ===")
print("vsb.width()  =", vsb.width())

# 方案 B：直接对滚动条 setStyleSheet
vsb.setStyleSheet("""
    QScrollBar { background: transparent; border: none; width: 0px; margin: 0px; }
    QScrollBar::handle { background: transparent; min-height: 0px; }
    QScrollBar::add-line, QScrollBar::sub-line { height: 0px; background: transparent; }
    QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
""")
app.processEvents()
print("\n=== 方案B：直接对 vsb setStyleSheet ===")
print("vsb.width()  =", vsb.width())
print("tw.viewport().width() =", tw.viewport().width())

# 方案 C：QScrollBar 子类，重写 sizeHint / paintEvent（最彻底）
from PyQt5.QtWidgets import QScrollBar
from PyQt5.QtCore import QSize

class InvisibleScrollBar(QScrollBar):
    def sizeHint(self):
        return QSize(0, 0)
    def minimumSizeHint(self):
        return QSize(0, 0)
    def paintEvent(self, e):
        pass  # 什么都不画 => 完全隐身

w2 = QWidget()
lay2 = QVBoxLayout(w2)
tw2 = QTreeWidget()
tw2.setColumnCount(2)
for i in range(50):
    QTreeWidgetItem(tw2, [f"row{i}", "x"])
lay2.addWidget(tw2)
tw2.setVerticalScrollBar(InvisibleScrollBar(Qt.Vertical, tw2))
w2.resize(400, 200)
w2.show()
app.processEvents()
sb2 = tw2.verticalScrollBar()
print("\n=== 方案C：QScrollBar 子类（sizeHint=0 + paintEvent 空）===")
print("type        =", type(sb2).__name__)
print("sb2.width() =", sb2.width())
print("sb2.maximum()=", sb2.maximum(), " (滚动能力)")
print("tw2.viewport().width() =", tw2.viewport().width())
