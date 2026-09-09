# -*- coding: utf-8 -*-
"""绘制充值页 10 个浅色系样式对比图 -> 一张 PNG"""
from PIL import Image, ImageDraw, ImageFont
import pathlib

W_CARD, H_CARD = 420, 300
COLS, ROWS = 2, 5
PAD = 24
TITLE_H = 110
W = PAD * 3 + W_CARD * COLS
H = TITLE_H + PAD * 2 + (H_CARD + PAD) * ROWS

FONT = "C:/Windows/Fonts/msyh.ttc"

def font(size, bold=False):
    idx = 1 if bold else 0
    try:
        return ImageFont.truetype(FONT, size, index=idx)
    except Exception:
        return ImageFont.truetype(FONT, size)

f_title = font(30, True)
f_sub = font(14)
f_label = font(17, True)
f_ptitle = font(15, True)
f_name = font(13, True)
f_desc = font(11)
f_price = font(24, True)
f_pay = font(13, True)
f_paydesc = font(11)
f_btn = font(14, True)

styles = [
 dict(no=1, name="极简纯白",   label=(58,58,58),      bg=(255,255,255), title=(26,26,26),  prod=(246,247,249), border=(232,234,238), name2=(51,51,51),  desc=(154,160,168), price=(26,26,26),  btn=(26,26,26)),
 dict(no=2, name="清新薄荷",   label=(15,169,126),    bg=(244,251,248), title=(20,80,62),  prod=(255,255,255), border=(211,236,225), name2=(29,92,73),  desc=(123,168,150), price=(15,169,126), btn=(15,169,126)),
 dict(no=3, name="天空蓝",     label=(47,125,246),    bg=(243,248,255), title=(28,61,102), prod=(255,255,255), border=(214,229,251), name2=(36,80,137), desc=(132,165,204), price=(47,125,246), btn=(47,125,246)),
 dict(no=4, name="暖杏奶油",   label=(232,150,74),    bg=(253,248,241), title=(92,67,38),  prod=(255,255,255), border=(240,224,200), name2=(107,79,44), desc=(179,154,118), price=(232,150,74), btn=(232,150,74)),
 dict(no=5, name="樱花粉",     label=(239,123,165),   bg=(253,244,247), title=(107,46,69), prod=(255,255,255), border=(245,217,227), name2=(122,58,82), desc=(194,148,166), price=(239,123,165), btn=(239,123,165)),
 dict(no=6, name="淡雅紫",     label=(139,111,232),   bg=(248,246,254), title=(69,52,112), prod=(255,255,255), border=(226,218,246), name2=(79,61,125), desc=(162,148,196), price=(139,111,232), btn=(139,111,232)),
 dict(no=7, name="柠檬活力",   label=(217,164,0),     bg=(254,251,232), title=(95,84,23),  prod=(255,255,255), border=(241,233,182), name2=(107,95,28), desc=(176,165,103), price=(199,155,0), btn=(217,164,0)),
 dict(no=8, name="青瓷绿",     label=(42,161,152),    bg=(242,250,249), title=(31,77,73),  prod=(255,255,255), border=(210,233,230), name2=(38,91,86),  desc=(127,168,163), price=(42,161,152), btn=(42,161,152)),
 dict(no=9, name="珊瑚暖调",   label=(240,112,90),    bg=(253,245,242), title=(107,53,42), prod=(255,255,255), border=(245,220,212), name2=(122,61,48), desc=(192,154,142), price=(240,112,90), btn=(240,112,90)),
 dict(no=10, name="浅色极光渐变", label=(124,92,224), bg=(247,246,255), title=(51,58,94),  prod=(255,255,255), border=(228,224,242), name2=(64,71,122), desc=(155,151,184), price=(124,92,224), btn=(124,92,224)),
]

img = Image.new("RGB", (W, H), (232, 234, 239))
d = ImageDraw.Draw(img)

t = "PC-Action 充值页 · 浅色系 10 选 1"
d.text(((W - d.textlength(t, f_title)) / 2, 28), t, font=f_title, fill=(51, 51, 51))
s = "都是浅色系 · 选一个告诉我编号，我照着改真页面"
d.text(((W - d.textlength(s, f_sub)) / 2, 70), s, font=f_sub, fill=(136, 136, 136))

def rrect(x, y, w, h, r, fill, outline=None, width=1):
    d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=fill, outline=outline, width=width)

def center_text(cx, y, text, f, fill):
    d.text((cx - d.textlength(text, f) / 2, y), text, font=f, fill=fill)

for i, s in enumerate(styles):
    row, col = divmod(i, COLS)
    x = PAD + col * (W_CARD + PAD)
    y = TITLE_H + PAD + row * (H_CARD + PAD)

    # 卡片主体
    rrect(x, y, W_CARD, H_CARD, 14, s["bg"], outline=(210, 212, 220), width=1)
    # 顶部标签条
    rrect(x, y, W_CARD, 40, 14, s["label"])
    d.rectangle([x, y + 26, x + W_CARD, y + 40], fill=s["label"])
    lab = f"样式 {s['no']} · {s['name']}"
    d.text((x + 16, y + 9), lab, font=f_label, fill=(255, 255, 255))

    # 充值页标题
    center_text(x + W_CARD / 2, y + 56, "PC-Action 会员充值", f_ptitle, s["title"])

    # 商品卡
    py = y + 88
    rrect(x + 18, py, W_CARD - 36, 74, 10, s["prod"], outline=s["border"], width=1)
    d.text((x + 34, py + 12), "VIP会员（月）", font=f_name, fill=s["name2"])
    d.text((x + 34, py + 36), "全功能 1 个月 · 付款后自动发激活码", font=f_desc, fill=s["desc"])
    ptxt = "￥9.9"
    d.text((x + W_CARD - 34 - d.textlength(ptxt, f_price), py + 20), ptxt, font=f_price, fill=s["price"])

    # 微信支付行
    ky = py + 86
    rrect(x + 18, ky, W_CARD - 36, 44, 10, s["prod"], outline=s["border"], width=1)
    cx, cy = x + 40, ky + 22
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(34, 197, 94))
    center_text(cx, cy - 8, "微", font(11, True), (255, 255, 255))
    d.text((x + 58, ky + 12), "微信支付", font=f_pay, fill=s["name2"])
    rd = "需备注 · 自动确认"
    d.text((x + W_CARD - 34 - d.textlength(rd, f_desc), ky + 14), rd, font=f_desc, fill=s["desc"])

    # 发起支付按钮
    by = ky + 56
    rrect(x + 18, by, W_CARD - 36, 42, 9, s["btn"])
    center_text(x + W_CARD / 2, by + 10, "发起支付", f_btn, (255, 255, 255))

# 用脚本自身位置定位输出，避免移动项目后路径失效
out = str(pathlib.Path(__file__).resolve().parent / "ui-10styles.png")
img.save(out)
print("saved:", out, img.size)
