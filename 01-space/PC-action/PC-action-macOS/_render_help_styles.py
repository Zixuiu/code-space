# -*- coding: utf-8 -*-
"""用 Qt 原生渲染使用帮助页（STEP 1）的 10+1 种风格，输出真实截图对比长图"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QFrame, QGridLayout,
                             QVBoxLayout, QHBoxLayout)
from PyQt5.QtGui import QImage, QPainter, QFont, QColor
from PyQt5.QtCore import Qt

PAGE_W, PAGE_H = 980, 560

S = dict(
    icon="⌨️", title="你每天在当机器人吗？",
    ask="问问自己 —— 这些事情是不是每天都在做？",
    cards=[
        ("🌅", "早上开工", "Chrome → 微信 → 钉钉 → 邮箱 → 办公软件"),
        ("📝", "填日报", "复制粘贴 → 改日期 → 改数据 → 发送"),
        ("🔑", "登录系统", "输账号 → 输密码 → 点登录"),
        ("📤", "导出数据", "点菜单 → 点导出 → 选格式 → 保存"),
    ],
    pain="一天两天没什么，但一年两年呢？",
    gray="这些动作你重复了成千上万次，浪费了几百个小时。",
    point="💡 这个软件的意义：你只需要做一次，以后它替你干。",
)


def build_page(g):
    """g: 风格 token 字典，全部走 QSS，与真实页面同样的控件结构"""
    page = QWidget()
    page.setFixedSize(PAGE_W, PAGE_H)
    page.setStyleSheet(f"background-color: {g['page_bg']};")
    lay = QVBoxLayout(page)
    lay.setContentsMargins(g['page_margin'], 24, g['page_margin'], 24)
    lay.setSpacing(g['spacing'])

    kicker = QLabel("STEP 1 / 6")
    kicker.setStyleSheet(f"color:{g['kicker']}; font-size:{g['kicker_size']}px; "
                         f"font-weight:700; background:transparent; "
                         f"font-family:{g['font']};")
    lay.addWidget(kicker)

    tr = QHBoxLayout()
    tr.setSpacing(10)
    icon_lbl = QLabel(S['icon'])
    icon_lbl.setStyleSheet(f"font-size:{g['icon_size']}px; background:transparent;")
    tr.addWidget(icon_lbl)
    title_lbl = QLabel(S['title'])
    title_lbl.setWordWrap(True)
    title_lbl.setStyleSheet(f"color:{g['title']}; font-size:{g['title_size']}px; "
                            f"font-weight:{g['title_weight']}; padding:4px 0; "
                            f"background:transparent; font-family:{g['font']};")
    tr.addWidget(title_lbl, 1)
    lay.addLayout(tr)

    ask_lbl = QLabel(S['ask'])
    ask_lbl.setStyleSheet(f"color:{g['ask']}; font-size:{g['body_size']}px; "
                          f"font-weight:700; background:transparent; font-family:{g['font']};")
    lay.addWidget(ask_lbl)
    lay.addSpacing(6)

    grid = QGridLayout()
    grid.setSpacing(g['card_gap'])
    for ci, (gicon, gtitle, gdesc) in enumerate(S['cards']):
        card = QFrame()
        card.setObjectName("sceneCard")
        card.setStyleSheet(
            f"#sceneCard {{ background-color:{g['card_bg']}; "
            f"border:{g['card_border_w']}px solid {g['card_border']}; "
            f"border-radius:{g['card_radius']}px; "
            f"border-left:{g['card_left_bar']}px solid {g['card_left_color']}; }}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, g['card_pad_v'], 16, g['card_pad_v'])
        cl.setSpacing(6)
        gt = QLabel(f"{gicon}  {gtitle}")
        gt.setStyleSheet(f"color:{g['card_title']}; font-size:{g['card_title_size']}px; "
                         f"font-weight:700; background:transparent; font-family:{g['font']};")
        gd = QLabel(gdesc)
        gd.setWordWrap(True)
        gd.setStyleSheet(f"color:{g['card_desc']}; font-size:{g['card_desc_size']}px; "
                         f"background:transparent; font-family:{g['font']};")
        cl.addWidget(gt)
        cl.addWidget(gd)
        grid.addWidget(card, ci // 2, ci % 2)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    lay.addLayout(grid)

    lay.addSpacing(4)
    pain_lbl = QLabel(S['pain'])
    pain_lbl.setStyleSheet(f"color:{g['pain']}; font-size:{g['body_size']}px; "
                           f"font-weight:700; background:transparent; font-family:{g['font']};")
    lay.addWidget(pain_lbl)
    gray_lbl = QLabel(S['gray'])
    gray_lbl.setStyleSheet(f"color:{g['gray']}; font-size:12px; "
                           f"background:transparent; font-family:{g['font']};")
    lay.addWidget(gray_lbl)
    lay.addStretch()

    point_lbl = QLabel(S['point'])
    point_lbl.setWordWrap(True)
    point_lbl.setStyleSheet(
        f"background-color:{g['point_bg']}; color:{g['point_color']}; "
        f"font-size:13px; font-weight:700; border-radius:{g['point_radius']}px; "
        f"padding:12px 15px; font-family:{g['font']};")
    lay.addWidget(point_lbl)
    return page


def tok(**kw):
    g = dict(
        page_bg='#FFFFFF', page_margin=28, spacing=10,
        kicker='#86868B', kicker_size=11,
        title='#1D1D1F', title_size=24, title_weight=700, icon_size=26,
        ask='#0A84FF', body_size=14,
        card_bg='#F5F5F7', card_border='#E8E8ED', card_border_w=1,
        card_radius=11, card_left_bar=0, card_left_color='transparent',
        card_title='#1D1D1F', card_title_size=15,
        card_desc='#86868B', card_desc_size=14,
        card_pad_v=14, card_gap=12,
        pain='#1D1D1F', gray='#86868B',
        point_bg='#0A84FF', point_color='#FFFFFF', point_radius=10,
        font='"Microsoft YaHei"',
    )
    g.update(kw)
    return g


STYLES = []
STYLES.append(('基准：当前程序样式', '灰卡+蓝色结论条，现用样式',
               tok()))
STYLES.append(('1 SaaS 现代风', '纯白底+细边框卡+靛蓝结论条，Linear/Notion 感',
               tok(card_bg='#FFFFFF', card_border='#E5E9F2', ask='#4F6EF2',
                   point_bg='#4F6EF2', kicker='#667085')))
STYLES.append(('2 暗黑模式', '深色全适配，夜间友好',
               tok(page_bg='#17181C', kicker='#8B90A0', title='#F0F1F5',
                   ask='#7C93FF', card_bg='#22242A', card_border='#2E3138',
                   card_title='#E8EAF0', card_desc='#8B90A0',
                   pain='#E8EAF0', gray='#6C717D',
                   point_bg='#2A2F45', point_color='#C9D4FF')))
STYLES.append(('3 渐变强调', '渐变结论条+渐变标题点缀，层级醒目',
               tok(card_bg='#F7F8FF', card_border='#E4E8FF', ask='#7C5CF0',
                   point_bg='qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #4F6EF2, stop:1 #7C5CF0)',
                   point_color='#FFFFFF')))
STYLES.append(('4 极简留白', '去卡片化，仅左侧细线分组，安静克制',
               tok(page_bg='#FFFFFF', card_bg='#FFFFFF', card_border='#FFFFFF',
                   card_left_bar=3, card_left_color='#1D1D1F', card_radius=0,
                   ask='#1D1D1F', point_bg='#1D1D1F', point_radius=0)))
STYLES.append(('5 玻璃拟态（近似）', '彩色底+半透明白卡',
               tok(page_bg='#C9D8FF', card_bg='rgba(255,255,255,0.55)',
                   card_border='rgba(255,255,255,0.8)', card_radius=14,
                   ask='#3D3D68', card_title='#33334D', card_desc='#55556E',
                   pain='#33334D', gray='#55556E', point_bg='rgba(255,255,255,0.75)',
                   point_color='#3D3D68', point_radius=14)))
STYLES.append(('6 Neo-Brutalism 硬朗风', '黑粗边+黄底高亮卡，个性强烈',
               tok(page_bg='#FFFDF5', card_bg='#FFD83D', card_border='#111111',
                   card_border_w=2, card_radius=4, card_title='#111111',
                   card_desc='#333333', ask='#111111', pain='#111111',
                   gray='#555555', point_bg='#111111', point_radius=4)))
STYLES.append(('7 紧凑高密度', '小字号小间距，一屏看更多内容',
               tok(title_size=19, icon_size=20, kicker_size=10, body_size=12,
                   card_title_size=13, card_desc_size=12, card_pad_v=9,
                   card_gap=8, spacing=6, point_radius=8)))
STYLES.append(('8 行卡片风（与表格统一）', '灰底容器+白卡+6px 透缝，和流程管理表格同一语言',
               tok(page_bg='#EEF1F7', card_bg='#FFFFFF', card_border='#EEF1F7',
                   card_border_w=6, card_radius=10, kicker='#7A8399',
                   ask='#3A6FF0', pain='#333333', card_title='#333333',
                   card_desc='#7A8399', point_bg='#3A6FF0', point_radius=8)))
STYLES.append(('9 终端极客风', '黑底等宽绿字，呼应自动化工具属性',
               tok(page_bg='#0C1016', kicker='#3DDC84', kicker_size=12,
                   title='#3DDC84', title_size=22, icon_size=22,
                   ask='#FFD866', card_bg='#11161D', card_border='#23303C',
                   card_radius=4, card_title='#C8D3DE', card_desc='#5E7285',
                   pain='#C8D3DE', gray='#5E7285',
                   point_bg='#11161D', point_color='#3DDC84', point_radius=4,
                   font='Consolas, "Courier New", monospace')))
STYLES.append(('10 杂志编辑风', '衬线大标题+编号卡片，优雅耐看',
               tok(page_bg='#FAF8F3', kicker='#B08D57', kicker_size=12,
                   title='#2A2620', title_size=26, card_bg='#FFFFFF',
                   card_border='#E8E2D6', card_radius=6,
                   card_title='#2A2620', card_desc='#8A8375',
                   ask='#B08D57', pain='#2A2620', gray='#8A8375',
                   point_bg='#2A2620', point_color='#F5EFE2', point_radius=2)))


def main():
    app = QApplication(sys.argv)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '帮助页风格原生预览')
    os.makedirs(out_dir, exist_ok=True)

    shots = []
    for name, desc, g in STYLES:
        w = build_page(g)
        w.show()
        app.processEvents()
        pix = w.grab()
        pix.save(os.path.join(out_dir, f'{name.split(" ")[0]}_{name.replace(" ", "_")}.png'))
        shots.append((name, desc, pix))
        w.close()
        print('渲染:', name)

    label_h, gap = 46, 24
    total_h = sum(label_h + PAGE_H + gap for _ in shots) + gap
    canvas = QImage(PAGE_W + 40, total_h, QImage.Format_RGB32)
    canvas.fill(QColor('#EEF0F4'))
    p = QPainter(canvas)
    y = gap
    for name, desc, pix in shots:
        p.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        p.setPen(QColor('#333333'))
        p.drawText(24, y + 26, name)
        p.setFont(QFont('Microsoft YaHei', 8))
        p.setPen(QColor('#999999'))
        p.drawText(320, y + 26, desc)
        y += label_h
        p.drawImage(20, y, pix.toImage())
        y += PAGE_H + gap
    p.end()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '帮助页风格原生对比.png')
    canvas.save(out)
    print('对比长图:', out)


if __name__ == '__main__':
    main()
