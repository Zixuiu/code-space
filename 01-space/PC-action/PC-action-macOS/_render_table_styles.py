# -*- coding: utf-8 -*-
"""用 Qt 原生渲染 10+1 种表格风格，输出真实截图拼成对比长图"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (QApplication, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView)
from PyQt5.QtGui import QColor, QImage, QPainter, QFont
from PyQt5.QtCore import Qt

ROWS = [
    ('09-03 16:02', '流程_20260903_160225_317', 'alt+c'),
    ('09-02 17:52', '往左', None),
    ('09-03 14:06', '流程_20260903_140615_023', None),
    ('09-03 10:39', '往右', None),
    ('09-04 11:04', '流程_20260904_110448_762', 'alt+x'),
]
COLS = ['时间', '流程名称', '快捷键', '重命名', '删除']
WIDTHS = [110, 400, 110, 90, 48]
TBL_W, TBL_H = 1000, 330


def make_table(style_qss=None, row_height=50, dark_text=False, delegate=None):
    t = QTableWidget()
    t.setColumnCount(5)
    t.setHorizontalHeaderLabels(COLS)
    if delegate:
        t.setItemDelegate(delegate)
    if style_qss:
        t.setStyleSheet(style_qss)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setMouseTracking(True)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setHighlightSections(False)
    t.horizontalHeader().setStretchLastSection(False)
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
    t.setFixedSize(TBL_W, TBL_H)
    return t


def base_qss(**kw):
    """在程序现有 get_table_stylesheet 基础上调参的简化版"""
    g = dict(bg='#FFFFFF', header_bg='#FFFFFF', header_color='#86868B',
             text='#1D1D1F', border='#E8E8ED', hover='#F0F0F2',
             selected='#E8F0FE', alt='#F5F5F5', radius=12,
             hfs=12, cfs=14, pad_v=12, pad_h=16)
    g.update(kw)
    return f"""
    QTableWidget {{ background:{g['bg']}; border:1px solid {g['border']};
        border-radius:{g['radius']}px; outline:none; gridline-color:transparent;
        font-size:{g['cfs']}px; font-family:"Microsoft YaHei"; color:{g['text']}; }}
    QTableWidget::item {{ padding:{g['pad_v']}px {g['pad_h']}px;
        border-bottom:1px solid rgba(0,0,0,0.05); color:{g['text']}; }}
    QTableWidget::item:hover {{ background:{g['hover']}; }}
    QTableWidget::item:selected {{ background:{g['selected']}; color:{g['text']}; }}
    QTableWidget::item:alternate {{ background:{g['alt']}; }}
    QHeaderView::section {{ background:{g['header_bg']}; color:{g['header_color']};
        padding:10px {g['pad_h']}px; border:none; border-right:1px solid {g['border']};
        border-bottom:1px solid {g['border']}; font-weight:700;
        font-size:{g['hfs']}px; font-family:"Microsoft YaHei"; }}
    QHeaderView::section:first {{ border-top-left-radius:{g['radius']}px; }}
    QHeaderView::section:last {{ border-right:none; border-top-right-radius:{g['radius']}px; }}
    """


STYLES = []  # (名称, 说明, 构造函数)

# 0 当前原生样式（基准）
STYLES.append(('基准：当前程序样式', '程序现用 get_table_stylesheet 默认参数',
               lambda: make_table(base_qss())))

# 1 SaaS 现代风
STYLES.append(('1 SaaS 现代风', '浅蓝表头+行悬浮淡蓝+快捷键蓝字，去竖线，主流桌面软件感',
               lambda: make_table(base_qss(header_bg='#F4F6FB', header_color='#667085',
                                           border='#E5E9F2', hover='#F5F8FF', pad_v=14))))

# 2 极简留白
STYLES.append(('2 极简留白', '无底色无边框，只留表头粗线与行细线',
               lambda: make_table(f"""
    QTableWidget {{ background:#FFFFFF; border:none; outline:none;
        gridline-color:transparent; font-size:14px; font-family:"Microsoft YaHei"; }}
    QTableWidget::item {{ border-bottom:1px solid #EFEFEF; color:#333; padding:15px 14px; }}
    QTableWidget::item:hover {{ background:#FCFCFC; }}
    QTableWidget::item:selected {{ background:#F5F5F5; color:#333; }}
    QHeaderView::section {{ background:#FFF; color:#222; border:none;
        border-bottom:2px solid #222; padding:12px 14px; font-weight:600;
        font-size:12px; font-family:"Microsoft YaHei"; }}
    """, row_height=54)))

# 3 暗黑模式
STYLES.append(('3 暗黑模式', '深色底，适合夜间/深色主题',
               lambda: make_table(f"""
    QTableWidget {{ background:#17181C; border:none; border-radius:12px;
        gridline-color:transparent; outline:none; font-size:14px; font-family:"Microsoft YaHei"; color:#D6D8DE; }}
    QTableWidget::item {{ border-bottom:1px solid #24262C; color:#D6D8DE; padding:13px 14px; }}
    QTableWidget::item:hover {{ background:#1F2127; }}
    QTableWidget::item:selected {{ background:#2A2F45; color:#FFF; }}
    QHeaderView::section {{ background:#22242A; color:#8B90A0; border:none;
        border-bottom:1px solid #2E3138; padding:11px 14px; font-weight:600;
        font-size:12px; font-family:"Microsoft YaHei"; }}
    QHeaderView::section:first {{ border-top-left-radius:12px; }}
    QHeaderView::section:last {{ border-top-right-radius:12px; }}
    """)))

# 4 渐变表头
STYLES.append(('4 渐变表头', 'Qt 原生 qlineargradient 表头，层级鲜明',
               lambda: make_table(f"""
    QTableWidget {{ background:#FFFFFF; border:1px solid #E5E9F2; border-radius:12px;
        gridline-color:transparent; outline:none; font-size:14px; font-family:"Microsoft YaHei"; }}
    QTableWidget::item {{ border-bottom:1px solid #EEF0F6; color:#333; padding:13px 14px; }}
    QTableWidget::item:alternate {{ background:#F7F8FF; }}
    QTableWidget::item:hover {{ background:#EEF1FF; }}
    QTableWidget::item:selected {{ background:#E0E6FF; color:#333; }}
    QHeaderView::section {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #4F6EF2, stop:1 #7C5CF0); color:#FFF; border:none;
        padding:12px 14px; font-weight:600; font-size:12px; font-family:"Microsoft YaHei"; }}
    QHeaderView::section:first {{ border-top-left-radius:12px; }}
    QHeaderView::section:last {{ border-top-right-radius:12px; }}
    """)))

# 5 玻璃拟态（近似）
STYLES.append(('5 玻璃拟态（近似）', '半透明卡片+浅紫底纹，Qt 用半透明色近似',
               lambda: make_table(f"""
    QTableWidget {{ background:rgba(255,255,255,0.55); border:1px solid rgba(255,255,255,0.8);
        border-radius:14px; gridline-color:transparent; outline:none;
        font-size:14px; font-family:"Microsoft YaHei"; color:#3D3D55; }}
    QTableWidget::item {{ border-bottom:1px solid rgba(255,255,255,0.5);
        color:#3D3D55; padding:13px 14px; background:rgba(255,255,255,0.35); }}
    QTableWidget::item:hover {{ background:rgba(255,255,255,0.65); }}
    QTableWidget::item:selected {{ background:rgba(120,110,255,0.25); color:#3D3D55; }}
    QHeaderView::section {{ background:rgba(255,255,255,0.6); color:#4A4A68; border:none;
        border-bottom:1px solid rgba(255,255,255,0.7); padding:12px 14px;
        font-weight:600; font-size:12px; font-family:"Microsoft YaHei"; }}
    """, row_height=50)))

# 6 紧凑高密度
STYLES.append(('6 紧凑高密度', '小字号窄行高，流程多时一屏更多',
               lambda: make_table(base_qss(header_bg='#F2F3F5', header_color='#555',
                                           border='#DDDDDD', hover='#F0F6FF',
                                           cfs=12, pad_v=5, pad_h=10, radius=8),
                                  row_height=30)))

# 7 硬朗风
STYLES.append(('7 Neo-Brutalism 硬朗风', '黑粗边框+黄色表头+撞色',
               lambda: make_table(f"""
    QTableWidget {{ background:#FFF; border:3px solid #111; border-radius:4px;
        gridline-color:#111; outline:none; font-size:13px; font-weight:500;
        font-family:"Microsoft YaHei"; }}
    QTableWidget::item {{ border-bottom:2px solid #111; border-right:2px solid #111;
        color:#111; padding:11px 14px; background:#FFF; }}
    QTableWidget::item:alternate {{ background:#F3F1EA; }}
    QTableWidget::item:hover {{ background:#DBE7FF; }}
    QTableWidget::item:selected {{ background:#FFD83D; color:#111; }}
    QHeaderView::section {{ background:#FFD83D; color:#111; border:none;
        border-bottom:3px solid #111; border-right:2px solid #111;
        padding:11px 14px; font-weight:700; font-size:12px; font-family:"Microsoft YaHei"; }}
    """)))

# 8 行卡片式
STYLES.append(('8 行卡片式', '行间透缝+白卡圆角观感（QSS border-bottom 透底实现）',
               lambda: make_table(f"""
    QTableWidget {{ background:#EEF1F7; border:none; border-radius:12px;
        gridline-color:transparent; outline:none; font-size:14px; font-family:"Microsoft YaHei"; }}
    QTableWidget::item {{ background:#FFF; border-bottom:6px solid #EEF1F7;
        color:#333; padding:12px 14px; }}
    QTableWidget::item:hover {{ background:#FAFBFF; }}
    QTableWidget::item:selected {{ background:#E8F0FE; color:#333; }}
    QHeaderView::section {{ background:#E3E7F0; color:#7A8399; border:none;
        padding:11px 14px; font-weight:600; font-size:12px; font-family:"Microsoft YaHei"; }}
    QHeaderView::section:first {{ border-top-left-radius:12px; }}
    QHeaderView::section:last {{ border-top-right-radius:12px; }}
    """, row_height=52)))

# 9 终端风
STYLES.append(('9 终端极客风', '黑底绿字等宽字体，呼应自动化工具属性',
               lambda: make_table(f"""
    QTableWidget {{ background:#0C1016; border:1px solid #233; border-radius:8px;
        gridline-color:transparent; outline:none; font-size:13px;
        font-family:Consolas,"Courier New",monospace; color:#C8D3DE; }}
    QTableWidget::item {{ border-bottom:1px solid #12181F; color:#C8D3DE;
        padding:8px 12px; }}
    QTableWidget::item:hover {{ background:#131A23; }}
    QTableWidget::item:selected {{ background:#1B2A3A; color:#FFF; }}
    QHeaderView::section {{ background:#0C1016; color:#3DDC84; border:none;
        border-bottom:1px dashed #233; padding:8px 12px; font-weight:400;
        font-size:12px; font-family:Consolas,monospace; }}
    """, row_height=38)))

# 10 软 UI 大圆角（当前已实现的委托版）
from design_system import SoftCardDelegate
STYLES.append(('10 软 UI 大圆角（当前已应用）', '白卡圆角行+灰底透缝，委托绘制',
               lambda: make_table(None, row_height=48, delegate=SoftCardDelegate())))


def main():
    app = QApplication(sys.argv)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '表格风格原生预览')
    os.makedirs(out_dir, exist_ok=True)

    shots = []
    for name, desc, fn in STYLES:
        t = fn()
        t.show()
        app.processEvents()
        pix = t.grab()
        path = os.path.join(out_dir, f'{name.split(" ")[0]}_{name.replace(" ", "_")}.png')
        pix.save(path)
        shots.append((name, desc, pix))
        t.close()
        print('渲染:', name)

    # 拼接对比长图
    label_h, gap = 46, 26
    total_h = sum(label_h + TBL_H + gap for _ in shots) + gap
    canvas = QImage(TBL_W + 40, total_h, QImage.Format_RGB32)
    canvas.fill(QColor('#EEF0F4'))
    p = QPainter(canvas)
    p.setRenderHint(QPainter.Antialiasing)
    y = gap
    for name, desc, pix in shots:
        p.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        p.setPen(QColor('#333'))
        p.drawText(24, y + 24, name)
        p.setFont(QFont('Microsoft YaHei', 8))
        p.setPen(QColor('#999'))
        p.drawText(24 + p.fontMetrics().horizontalAdvance(name) * 2 + 120, y + 24, desc)
        y += label_h
        p.drawImage(20, y, pix.toImage())
        y += TBL_H + gap
    p.end()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '表格风格原生对比.png')
    canvas.save(out)
    print('对比长图:', out)


if __name__ == '__main__':
    main()
