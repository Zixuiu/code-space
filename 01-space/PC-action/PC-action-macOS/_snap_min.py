# -*- coding: utf-8 -*-
"""临时：P 系列 —— QLineEdit 原生化假说验证（用完即删）"""
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QImage, QPainter
from PyQt5.QtWidgets import QApplication, QWidget

import activation_dialog as ad

OUT1 = r'C:\Users\stk_gb\AppData\Local\Temp\p1.png'  # IME 关
OUT2 = r'C:\Users\stk_gb\AppData\Local\Temp\p2.png'  # 对照


def snap(dlg, path):
    pix = dlg.grab()
    img = QImage(pix.width() + 40, pix.height() + 40, QImage.Format_RGB32)
    p = QPainter(img)
    p.fillRect(img.rect(), QColor("#B8B8BE"))
    p.drawPixmap(20, 20, pix)
    p.end()
    img.save(path)


def main():
    app = QApplication(sys.argv)
    anchor = QWidget()
    anchor.setGeometry(3000, 3000, 1, 1)
    anchor.show()

    parent = QWidget()
    parent.setFixedSize(900, 600)
    parent.show()
    state = {"i": 0}

    def nxt():
        state["i"] += 1
        run()

    def run():
        dlg = ad.ActivationDialog(parent, username="tester")
        if state["i"] == 0:
            dlg.code_input.setAttribute(Qt.WA_InputMethodEnabled, False)
            dlg.code_input.setAttribute(Qt.WA_NativeWindow, False)
            dlg.code_input.setAttribute(Qt.WA_DontCreateNativeAncestors, True)
        dlg.show()
        out = OUT1 if state["i"] == 0 else OUT2

        def done():
            print("native(input):", dlg.code_input.testAttribute(Qt.WA_NativeWindow),
                  "native(dlg):", dlg.testAttribute(Qt.WA_NativeWindow))
            snap(dlg, out)
            dlg.close()
            app.processEvents()
            nxt()
        QTimer.singleShot(700, done)

    run()
    app.exec_()
    print("P OK")


if __name__ == "__main__":
    main()
