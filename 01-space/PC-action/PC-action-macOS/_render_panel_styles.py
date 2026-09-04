# -*- coding: utf-8 -*-
"""用 Qt 原生渲染流程管理【整个界面】（按钮行+表格+容器）的 10+1 种风格，拼成对比长图"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (QApplication, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton, QLabel, QFrame)
from PyQt5.QtGui import QColor, QImage, QPainter, QFont
from PyQt5.QtCore import Qt

ROWS = [
    ('09-03 16:02', '流程_20260903_160225_317', 'alt+c'),
    ('09-02 17:52', '往左', None),
    ('09-03 14:06', '流程_20260903_140615_023', None),
    ('09-04 11:04', '流程_20260904_110448_762', 'alt+x'),
    ('09-03 10:39', '往右', None),
]
COLS = ['时间', '流程名称', '快捷键', '重命名', '删除']
WIDTHS = [110, 400, 110, 90, 48]
PANEL_W, PANEL_H = 980, 620


def btn(text, qss):
    b = QPushButton(text)
    b.setStyleSheet(qss)
    b.setCursor(Qt.PointingHandCursor)
    return b


def make_table(style_qss, row_height=50):
    t = QTableWidget()
    t.setColumnCount(5)
    t.setHorizontalHeaderLabels(COLS)
    t.setStyleSheet(style_qss)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setMouseTracking(True)
    t.setShowGrid(False)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setHighlightSections(False)
    for i, w in enumerate(WIDTHS):
        t.setColumnWidth(i, w)
    t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    t.verticalHeader().setDefaultSectionSize(row_height)
    t.setRowCount(len(ROWS))
    for r, (ctime, name, key) in enumerate(ROWS):
        t.setItem(r, 0, QTableWidgetItem(ctime))
        t.setItem(r, 1, QTableWidgetItem(name))
        s = QTableWidgetItem(key if key else '未设置')
        s.setForeground(QColor('#1890ff') if key else QColor('#999999'))
        t.setItem(r, 2, s)
        e = QTableWidgetItem('✏️'); e.setTextAlignment(Qt.AlignCenter)
        d = QTableWidgetItem('🗑️'); d.setTextAlignment(Qt.AlignCenter)
        t.setItem(r, 3, e); t.setItem(r, 4, d)
    return t


def panel(page_qss, btn_qss, table_qss, row_height=50, gap=16):
    """完整界面：外层页面 + 按钮行 + 表格"""
    page = QWidget()
    page.setFixedSize(PANEL_W, PANEL_H)
    page.setStyleSheet(page_qss)
    lay = QVBoxLayout(page)
    lay.setContentsMargins(24, 20, 24, 24)
    lay.setSpacing(gap)

    top = QHBoxLayout()
    top.setSpacing(12)
    top.addWidget(btn('🔄 刷新', btn_qss))
    top.addWidget(btn('🗑️ 回收站', btn_qss))
    top.addStretch()
    lay.addLayout(top)

    lay.addWidget(make_table(table_qss, row_height))
    lay.addStretch()
    return page


def qss_btn(bg, color, border, radius=10, pad='8px 18px', hover=None):
    h = hover or bg
    return (f"QPushButton {{ background:{bg}; color:{color}; border:1px solid {border};"
            f" border-radius:{radius}px; padding:{pad}; font-size:13px;"
            f' font-family:"Microsoft YaHei","Segoe UI Emoji"; font-weight:600; }}'
            f" QPushButton:hover {{ background:{h}; }}")


STYLES = []

# 0 基准（当前程序样式 = 行卡片式）
STYLES.append(('基准：当前程序样式', '刷新/回收站白底胶囊按钮 + 灰底白卡行表格',
               lambda: panel(
                   "QWidget { background:#F5F6F8; }",
                   qss_btn('#FFFFFF', '#333333', '#E3E5EA', hover='#F2F3F6'),
                   """
    QTableWidget { background:#EEF1F7; border:none; border-radius:12px; outline:none;
        gridline-color:transparent; font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#333; }
    QTableWidget::item { background:#FFFFFF; border-bottom:6px solid #EEF1F7; color:#333; padding:10px 14px; }
    QTableWidget::item:hover { background:#FAFBFF; }
    QTableWidget::item:selected { background:#E8F0FE; color:#333; }
    QHeaderView::section { background:#E3E7F0; color:#7A8399; padding:11px 14px;
        border:none; font-weight:600; font-size:12px; font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    QHeaderView::section:first { border-top-left-radius:12px; }
    QHeaderView::section:last { border-top-right-radius:12px; }
    """)))

# 1 SaaS 现代风
STYLES.append(('1 SaaS 现代风', '靛蓝主按钮+白卡浮层表格，Notion/Linear 感',
               lambda: panel(
                   "QWidget { background:#FAFBFC; }",
                   qss_btn('#4F6EF2', '#FFFFFF', '#4F6EF2', hover='#3F5BE0') + ' ' +
                   qss_btn('#FFFFFF', '#4F6EF2', '#C9D4F5', hover='#F0F4FF'),
                   """
    QTableWidget { background:#FFFFFF; border:1px solid #E5E9F2; border-radius:14px; outline:none;
        gridline-color:transparent; font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#333; }
    QTableWidget::item { border-bottom:1px solid #F0F2F7; color:#333; padding:12px 14px; }
    QTableWidget::item:hover { background:#F5F8FF; }
    QTableWidget::item:selected { background:#E8F0FE; color:#333; }
    QHeaderView::section { background:#F4F6FB; color:#667085; padding:12px 14px;
        border:none; border-bottom:1px solid #E5E9F2; font-weight:600; font-size:12px;
        font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    QHeaderView::section:first { border-top-left-radius:14px; }
    QHeaderView::section:last { border-top-right-radius:14px; }
    """)))

# 2 极简留白
STYLES.append(('2 极简留白', '无按钮边框，表格只留一条表头粗线',
               lambda: panel(
                   "QWidget { background:#FFFFFF; }",
                   qss_btn('#FFFFFF', '#222222', '#222222', radius=6, hover='#F5F5F5'),
                   """
    QTableWidget { background:#FFFFFF; border:none; outline:none; gridline-color:transparent;
        font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    QTableWidget::item { border-bottom:1px solid #EFEFEF; color:#333; padding:15px 14px; }
    QTableWidget::item:hover { background:#FCFCFC; }
    QTableWidget::item:selected { background:#F5F5F5; color:#333; }
    QHeaderView::section { background:#FFF; color:#222; border:none; border-bottom:2px solid #222;
        padding:12px 14px; font-weight:600; font-size:12px; font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    """, row_height=54, gap=20)))

# 3 暗黑模式
STYLES.append(('3 暗黑模式', '深色面板+发光蓝主按钮，夜间主题',
               lambda: panel(
                   "QWidget { background:#17181C; }",
                   qss_btn('#0A84FF', '#FFFFFF', '#0A84FF', hover='#2492FF') + ' ' +
                   qss_btn('#24262C', '#D6D8DE', '#33363E', hover='#2C2F37'),
                   """
    QTableWidget { background:#1D1F24; border:1px solid #2A2D34; border-radius:12px; outline:none;
        gridline-color:transparent; font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#D6D8DE; }
    QTableWidget::item { border-bottom:1px solid #26282E; color:#D6D8DE; padding:12px 14px; }
    QTableWidget::item:hover { background:#24262C; }
    QTableWidget::item:selected { background:#2A3B52; color:#FFF; }
    QHeaderView::section { background:#22242A; color:#8B90A0; border:none; border-bottom:1px solid #2E3138;
        padding:12px 14px; font-weight:600; font-size:12px; font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    QHeaderView::section:first { border-top-left-radius:12px; }
    QHeaderView::section:last { border-top-right-radius:12px; }
    """)))

# 4 渐变强调
STYLES.append(('4 渐变强调', '紫蓝渐变主按钮+渐变表头，活力最强',
               lambda: panel(
                   "QWidget { background:#F7F8FE; }",
                   qss_btn('#7C5CF0', '#FFFFFF', '#7C5CF0', hover='#6B4BE0') + ' ' +
                   qss_btn('#FFFFFF', '#7C5CF0', '#D9CFF7', hover='#F3EEFF'),
                   """
    QTableWidget { background:#FFFFFF; border:1px solid #E5E0F5; border-radius:14px; outline:none;
        gridline-color:transparent; font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#333; }
    QTableWidget::item { border-bottom:1px solid #F0EDFA; color:#333; padding:12px 14px; }
    QTableWidget::item:hover { background:#F5F2FF; }
    QTableWidget::item:selected { background:#EBE4FF; color:#333; }
    QHeaderView::section { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4F6EF2, stop:1 #7C5CF0);
        color:#FFF; border:none; padding:12px 14px; font-weight:600; font-size:12px;
        font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    QHeaderView::section:first { border-top-left-radius:14px; }
    QHeaderView::section:last { border-top-right-radius:14px; }
    """)))

# 5 玻璃拟态
STYLES.append(('5 玻璃拟态', '彩色渐变底+半透明白卡+半透明按钮',
               lambda: panel(
                   "QWidget { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #DCE4FF, stop:0.5 #EADFFF, stop:1 #FFE9F2); }",
                   qss_btn('rgba(255,255,255,0.75)', '#3A4A8A', 'rgba(255,255,255,0.9)', hover='rgba(255,255,255,0.95)'),
                   """
    QTableWidget { background:rgba(255,255,255,0.6); border:1px solid rgba(255,255,255,0.9);
        border-radius:16px; outline:none; gridline-color:transparent;
        font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#3A3F52; }
    QTableWidget::item { background:rgba(255,255,255,0.55); border-bottom:5px solid transparent; color:#3A3F52; padding:11px 14px; }
    QTableWidget::item:hover { background:rgba(255,255,255,0.9); }
    QTableWidget::item:selected { background:rgba(120,140,255,0.25); color:#2A2F52; }
    QHeaderView::section { background:rgba(255,255,255,0.45); color:#5A5F7A; border:none;
        padding:12px 14px; font-weight:600; font-size:12px; font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    QHeaderView::section:first { border-top-left-radius:16px; }
    QHeaderView::section:last { border-top-right-radius:16px; }
    """)))

# 6 紧凑高密度
STYLES.append(('6 紧凑高密度', '小按钮小行高，一屏看更多流程',
               lambda: panel(
                   "QWidget { background:#F5F6F8; }",
                   qss_btn('#FFFFFF', '#333333', '#E3E5EA', radius=8, pad='5px 12px', hover='#F2F3F6'),
                   """
    QTableWidget { background:#FFFFFF; border:1px solid #E5E7EC; border-radius:10px; outline:none;
        gridline-color:transparent; font-size:12px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#333; }
    QTableWidget::item { border-bottom:1px solid #F0F1F4; color:#333; padding:5px 12px; }
    QTableWidget::item:hover { background:#F5F8FF; }
    QTableWidget::item:selected { background:#E8F0FE; color:#333; }
    QHeaderView::section { background:#F4F6FB; color:#667085; padding:6px 12px; border:none;
        border-bottom:1px solid #E5E9F2; font-weight:600; font-size:11px;
        font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    QHeaderView::section:first { border-top-left-radius:10px; }
    QHeaderView::section:last { border-top-right-radius:10px; }
    """, row_height=34, gap=10)))

# 7 硬朗风 (Neo-Brutalism)
STYLES.append(('7 硬朗风', '黑粗边+黄主按钮+硬投影，个性最强',
               lambda: panel(
                   "QWidget { background:#F5F1E8; }",
                   qss_btn('#FFD43B', '#111111', '#111111', radius=6, hover='#FFC800') + ' ' +
                   qss_btn('#FFFFFF', '#111111', '#111111', radius=6, hover='#F5F0E0'),
                   """
    QTableWidget { background:#FFFFFF; border:2px solid #111111; border-radius:0px; outline:none;
        gridline-color:transparent; font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#111; }
    QTableWidget::item { border-bottom:1px solid #111111; color:#111; padding:12px 14px; }
    QTableWidget::item:hover { background:#FFF8E1; }
    QTableWidget::item:selected { background:#FFD43B; color:#111; }
    QHeaderView::section { background:#FFD43B; color:#111; border:none; border-bottom:2px solid #111111;
        border-right:1px solid #111111; padding:12px 14px; font-weight:700; font-size:12px;
        font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    """, row_height=50)))

# 8 行卡片式·统一版
STYLES.append(('8 行卡片式·按钮也卡片化', '灰底透缝贯穿按钮区和表格，全界面统一设计语言',
               lambda: panel(
                   "QWidget { background:#EEF1F7; }",
                   qss_btn('#FFFFFF', '#333333', 'transparent', radius=12, hover='#F6F8FF'),
                   """
    QTableWidget { background:transparent; border:none; outline:none; gridline-color:transparent;
        font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#333; }
    QTableWidget::item { background:#FFFFFF; border-bottom:6px solid #EEF1F7; color:#333; padding:10px 14px; }
    QTableWidget::item:hover { background:#FAFBFF; }
    QTableWidget::item:selected { background:#E8F0FE; color:#333; }
    QHeaderView::section { background:#E3E7F0; color:#7A8399; padding:11px 14px; border:none;
        font-weight:600; font-size:12px; font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    QHeaderView::section:first { border-top-left-radius:12px; }
    QHeaderView::section:last { border-top-right-radius:12px; }
    """)))

# 9 终端极客风
STYLES.append(('9 终端极客风', '黑底绿字等宽，主按钮荧光绿',
               lambda: panel(
                   "QWidget { background:#101210; }",
                   "QPushButton { background:#101210; color:#4AF626; border:1px solid #2E5E2E;"
                   " border-radius:4px; padding:8px 18px; font-size:13px;"
                   ' font-family:Consolas,"Microsoft YaHei"; font-weight:600; }'
                   "QPushButton:hover { background:#1A241A; }",
                   """
    QTableWidget { background:#0C0E0C; border:1px solid #23301F; border-radius:6px; outline:none;
        gridline-color:transparent; font-size:13px; font-family:Consolas,"Microsoft YaHei"; color:#4AF626; }
    QTableWidget::item { border-bottom:1px dashed #23301F; color:#4AF626; padding:11px 14px; }
    QTableWidget::item:hover { background:#141914; }
    QTableWidget::item:selected { background:#1E3320; color:#7CFF9A; }
    QHeaderView::section { background:#121512; color:#3E8E41; border:none; border-bottom:1px solid #2E5E2E;
        padding:11px 14px; font-weight:600; font-size:12px; font-family:Consolas,"Microsoft YaHei"; }
    """)))

# 10 杂志编辑风
STYLES.append(('10 杂志编辑风', '米白底+衬线大标题感+细线分隔，安静高级',
               lambda: panel(
                   "QWidget { background:#FAF7F2; }",
                   qss_btn('#FAF7F2', '#2A2620', '#D8D2C6', radius=0, hover='#F0EBE0'),
                   """
    QTableWidget { background:transparent; border:none; border-top:2px solid #2A2620; outline:none;
        gridline-color:transparent; font-size:14px; font-family:"Microsoft YaHei","Segoe UI Emoji"; color:#2A2620; }
    QTableWidget::item { border-bottom:1px solid #E2DCD0; color:#2A2620; padding:14px 10px; }
    QTableWidget::item:hover { background:#F3EEE4; }
    QTableWidget::item:selected { background:#EFE7D8; color:#2A2620; }
    QHeaderView::section { background:transparent; color:#8A8272; border:none; border-bottom:1px solid #D8D2C6;
        padding:12px 10px; font-weight:600; font-size:11px; font-family:"Microsoft YaHei","Segoe UI Emoji"; }
    """, row_height=54, gap=18)))


def main():
    app = QApplication(sys.argv)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '流程页风格原生预览')
    os.makedirs(out_dir, exist_ok=True)

    shots = []
    for name, desc, fn in STYLES:
        w = fn()
        w.show()
        app.processEvents()
        pix = w.grab()
        path = os.path.join(out_dir, f"{name.split(' ')[0]}_{name.replace(' ', '_')}.png")
        pix.save(path)
        shots.append((name, desc, pix))
        w.close()
        print('渲染:', name)

    label_h, gap = 46, 26
    total_h = sum(label_h + PANEL_H + gap for _ in shots) + gap
    canvas = QImage(PANEL_W + 40, total_h, QImage.Format_RGB32)
    canvas.fill(QColor('#E8EAEF'))
    p = QPainter(canvas)
    y = gap
    for name, desc, pix in shots:
        p.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        p.setPen(QColor('#333'))
        p.drawText(24, y + 24, name)
        p.setFont(QFont('Microsoft YaHei', 8))
        p.setPen(QColor('#999'))
        p.drawText(320, y + 24, desc)
        y += label_h
        p.drawImage(20, y, pix.toImage())
        y += PANEL_H + gap
    p.end()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '流程页整界风格原生对比.png')
    canvas.save(out)
    print('对比长图:', out)


if __name__ == '__main__':
    main()
