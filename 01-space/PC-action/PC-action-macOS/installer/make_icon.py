# -*- coding: utf-8 -*-
"""
用项目自带的 SVG 图标生成 Windows 图标 app.ico（免额外依赖，只用 PyQt5）。
产物：installer/app.ico  —— 供 NSIS 安装包 / 快捷方式 / 卸载入口使用。
"""
import os
import struct
import sys

from PyQt5.QtGui import QGuiApplication, QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtSvg import QSvgRenderer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
SVG = os.path.join(ROOT, 'icons', 'play.svg')
OUT = os.path.join(HERE, 'app.ico')

SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_png_bytes(size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))
    r = QSvgRenderer(SVG)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    r.render(p)
    p.end()
    from PyQt5.QtCore import QBuffer, QByteArray, QIODevice
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, 'PNG')
    buf.close()
    return bytes(ba)


def build_ico(pngs):
    out = bytearray()
    out += struct.pack('<HHH', 0, 1, len(pngs))
    offset = 6 + 16 * len(pngs)
    entries = []
    for size, data in pngs:
        entries.append((size, data, offset))
        offset += len(data)
    for size, data, off in entries:
        w = 0 if size >= 256 else size
        out += struct.pack('<BBBBHHII', w, w, 0, 0, 1, 32, len(data), off)
    for size, data, off in entries:
        out += data
    return bytes(out)


def main():
    app = QGuiApplication(sys.argv)
    pngs = [(s, render_png_bytes(s)) for s in SIZES]
    with open(OUT, 'wb') as f:
        f.write(build_ico(pngs))
    print('ico ->', OUT, os.path.getsize(OUT), 'bytes')


if __name__ == '__main__':
    main()
