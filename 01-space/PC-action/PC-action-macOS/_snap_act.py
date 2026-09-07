# -*- coding: utf-8 -*-
"""临时：排除实验 C/D/E —— 定位吃掉圆角的元凶（用完即删）"""
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtWidgets import QApplication, QWidget

import activation_dialog as ad


def grab_to(dlg, path):
    pix = dlg.grab()
    img = QImage(pix.width() + 40, pix.height() + 40, QImage.Format_RGB32)
    p = QPainter(img)
    p.fillRect(img.rect(), QColor("#B8B8BE"))
    p.drawPixmap(20, 20, pix)
    p.end()
    img.save(path)


def main():
    app = QApplication(sys.argv)
    parent = QWidget()
    parent.setFixedSize(900, 600)
    parent.setStyleSheet("background-color:#F5F5F7;")
    parent.show()

    orig_add_shadow = ad.ActivationDialog._add_shadow
    orig_fade_in = ad.ActivationDialog._fade_in

    def run(tag, path, patch):
        ad.ActivationDialog._add_shadow = orig_add_shadow if patch[0] else (lambda self: None)
        ad.ActivationDialog._fade_in = orig_fade_in if patch[1] else (lambda self: None)
        dlg = ad.ActivationDialog(parent, username="tester")
        dlg.show()
        QTimer.singleShot(700, lambda: (grab_to(dlg, path), dlg.close(),
                                        app.processEvents(), next_step()))

    CASES = [
        ("C_无阴影有淡入", r'C:\Users\stk_gb\AppData\Local\Temp\act_c.png', (False, True)),
        ("D_有阴影无淡入", r'C:\Users\stk_gb\AppData\Local\Temp\act_d.png', (True, False)),
        ("E_都无", r'C:\Users\stk_gb\AppData\Local\Temp\act_e.png', (False, False)),
        ("F_都有", r'C:\Users\stk_gb\AppData\Local\Temp\act_f.png', (True, True)),
    ]
    state = {"i": 0}

    def next_step():
        state["i"] += 1
        if state["i"] < len(CASES):
            run(*CASES[state["i"]])
        else:
            print("CDEF OK")
            app.quit()

    run(*CASES[0])
    app.exec_()


if __name__ == "__main__":
    main()
