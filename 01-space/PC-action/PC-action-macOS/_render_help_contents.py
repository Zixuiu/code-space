# -*- coding: utf-8 -*-
"""使用帮助页：10 种「内容方案」+ 原版，Qt 原生渲染对比长图（样式保持程序原风格）"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QFrame, QGridLayout,
                             QVBoxLayout, QHBoxLayout, QSizePolicy)
from PyQt5.QtGui import QImage, QPainter, QFont, QColor
from PyQt5.QtCore import Qt

PAGE_W, PAGE_H = 980, 560
FONT = '"Microsoft YaHei"'

# ---------- 原样式组件（与程序现用风格一致） ----------

def L(text, color='#1D1D1F', size=14, weight=400, wrap=True):
    lbl = QLabel(text)
    lbl.setWordWrap(wrap)
    lbl.setStyleSheet(f"color:{color}; font-size:{size}px; font-weight:{weight};"
                      f"background:transparent; font-family:{FONT};")
    return lbl

def card(inner, pad=14):
    f = QFrame()
    f.setStyleSheet("#c { background-color:#F5F5F7; border:1px solid #E8E8ED;"
                    "border-radius:11px; }")
    f.setObjectName("c")
    cl = QVBoxLayout(f)
    cl.setContentsMargins(16, pad, 16, pad)
    cl.setSpacing(6)
    for w in inner:
        cl.addWidget(w)
    return f

def grid4(items):
    grid = QGridLayout()
    grid.setSpacing(12)
    for ci, w in enumerate(items):
        grid.addWidget(w, ci // 2, ci % 2)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    return grid

def banner(text):
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet("background-color:#0A84FF; color:#FFFFFF; font-size:13px;"
                      "font-weight:700; border:none; border-radius:10px;"
                      "padding:12px 15px; font-family:" + FONT + ";")
    return lbl

def kicker(text="STEP 1 / 6"):
    return L(text, color='#86868B', size=11, weight=700)

def base_page(rows):
    page = QWidget()
    page.setFixedSize(PAGE_W, PAGE_H)
    page.setStyleSheet("background-color:#FFFFFF;")
    lay = QVBoxLayout(page)
    lay.setContentsMargins(28, 24, 28, 24)
    lay.setSpacing(10)
    for r in rows:
        if isinstance(r, QWidget):
            lay.addWidget(r)
        else:  # QLayout → 包一层容器
            holder = QWidget()
            holder.setStyleSheet("background:transparent;")
            holder.setLayout(r)
            lay.addWidget(holder)
    lay.addStretch()
    return page

def title_row(icon, title):
    tr = QHBoxLayout()
    tr.setSpacing(10)
    ic = QLabel(icon)
    ic.setStyleSheet(f"font-size:26px; background:transparent;")
    tr.addWidget(ic)
    tr.addWidget(L(title, size=24, weight=700), 1)
    return tr


# ---------- 0 原版 ----------

def v0():
    rows = [kicker()]
    rows.append(title_row("⌨️", "你每天在当机器人吗？"))
    rows.append(L("问问自己 —— 这些事情是不是每天都在做？", color='#0A84FF', weight=700))
    cards = [("🌅  早上开工", "Chrome → 微信 → 钉钉 → 邮箱 → 办公软件"),
             ("📝  填日报", "复制粘贴 → 改日期 → 改数据 → 发送"),
             ("🔑  登录系统", "输账号 → 输密码 → 点登录"),
             ("📤  导出数据", "点菜单 → 点导出 → 选格式 → 保存")]
    rows.append(grid4([card([L(t, size=15, weight=700), L(d, color='#86868B')])
                       for t, d in cards]))
    rows.append(L("一天两天没什么，但一年两年呢？", weight=700))
    rows.append(L("这些动作你重复了成千上万次，浪费了几百个小时。", color='#86868B', size=12))
    rows.append(banner("💡 这个软件的意义：你只需要做一次，以后它替你干。"))
    return base_page(rows)


# ---------- 1 数字冲击 ----------

def v1():
    stats = [("200+ 次", "你每天的手动点击", "鼠标点到手软"),
             ("47 分钟", "每天花在重复动作上", "还不算走神的时间"),
             ("285 小时", "一年白扔的时间", "≈ 35 个工作日")]
    rows = [kicker(), title_row("⌨️", "你的时间，正在被鼠标吃掉")]
    rows.append(L("先别急着学功能，看看这笔账 ——", color='#0A84FF', weight=700))
    rows.append(grid4([card([L(n, color='#0A84FF', size=26, weight=700),
                             L(t, size=14, weight=700), L(d, color='#86868B', size=12)])
                       for n, t, d in stats]))
    rows.append(L("一天 47 分钟没什么，但一年是 35 个工作日。", weight=700))
    rows.append(L("相当于每年放完年假，又多上了 35 天班 —— 不带工资的那种。", color='#86868B', size=12))
    rows.append(banner("💡 用 PC-action 把这 285 小时拿回来。"))
    return base_page(rows)


# ---------- 2 扎心提问 ----------

def v2():
    qs = ["🤔  开电脑第一件事，是不是点开同一排软件？",
          "🤔  填日报的时候，是不是只改日期和数字？",
          "🤔  登录系统输密码，是不是已经形成肌肉记忆？",
          "🤔  导出报表点的那几下，是不是闭着眼都能点对？"]
    rows = [kicker(), title_row("🪞", "下面几件事，你对了几件？")]
    rows.append(L("不用全对，对 2 件就该往下看了 ——", color='#0A84FF', weight=700))
    rows.append(grid4([card([L(q, size=13, weight=700)]) for q in qs]))
    rows.append(L("对得越多，说明你越适合干这个 —— 也越需要被替代。", weight=700))
    rows.append(L("毕竟机器最擅长的，就是把人从肌肉记忆里解放出来。", color='#86868B', size=12))
    rows.append(banner("💡 全中的话别难过 —— 这正是 PC-action 为你准备的 reason。"))
    return base_page(rows)


# ---------- 3 故事型 ----------

def v3():
    story = ("早上 9:00，小李到工位。打开 Chrome、登录微信、钉钉扫码、清邮箱、开办公软件 —— 这套动作他做了三年，"
             "闭着眼都不会错。9:20，他开始填日报：复制昨天的，改个日期，改两个数字，发送。"
             "10:00，ERP 导报表：点菜单、点导出、选格式、保存，等待，重命名，归档。")
    story2 = ("下午 6 点，小李下班了。今天他又花了 47 分钟在「点来点去」上。"
              "而隔壁工位的老王 5:50 就走了 —— 因为这些活，他的电脑自己会干。")
    rows = [kicker(), title_row("📖", "小李小李，天天重复")]
    rows.append(L("一个真实到扎心的故事 ——", color='#0A84FF', weight=700))
    rows.append(card([L(story, size=13), L(story2, size=13, weight=700)]))
    rows.append(L("小李的 47 分钟和老王的 3 分钟，差的不是手速。", weight=700))
    rows.append(L("差的是：老王录了一遍流程，然后让电脑替他点。", color='#86868B', size=12))
    rows.append(banner("💡 你只需要做一次，以后它替你干 —— 老王早就懂了。"))
    return base_page(rows)


# ---------- 4 对话型 ----------

def v4():
    def bubble(text, me=False):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        bg = '#0A84FF' if me else '#F5F5F7'
        fg = '#FFFFFF' if me else '#1D1D1F'
        align = 'margin-left:80px;' if me else 'margin-right:80px;'
        lbl.setStyleSheet(f"background-color:{bg}; color:{fg}; font-size:13px;"
                          f"border-radius:12px; padding:10px 14px; {align} font-family:{FONT};")
        return lbl
    rows = [kicker("STEP 1 / 6 · 换个方式说"),
            title_row("💬", "你和电脑聊两句？")]
    rows.append(bubble("电脑：听说你每天开工要手动开 5 个软件？"))
    rows.append(bubble("我：对啊，Chrome、微信、钉钉、邮箱、办公软件，一个不能少。"))
    rows.append(bubble("电脑：填日报是不是也复制粘贴改日期？"))
    rows.append(bubble("我：……你怎么知道。你天天在看我干活？"))
    rows.append(bubble("我可以替你干。你演示一遍，以后叫我一声就行。", me=True))
    rows.append(L("这就是 PC-action 的全部工作原理：你看一遍 → 教一遍 → 它记住。", weight=700))
    rows.append(banner("💡 人类负责想，电脑负责点。"))
    return base_page(rows)


# ---------- 5 手动 vs 自动 对比 ----------

def v5():
    pairs = [("🌅  早上开工", "5 个软件挨个点  ≈ 5 分钟", "一条流程  ≈ 10 秒"),
             ("📝  填日报", "复制粘贴改 4 处  ≈ 3 分钟", "自动生成发送  ≈ 5 秒"),
             ("🔑  登录系统", "账号密码逐个输  ≈ 2 分钟", "自动登录  ≈ 3 秒"),
             ("📤  导出数据", "菜单导出归档  ≈ 5 分钟", "自动导出  ≈ 8 秒")]
    rows = [kicker(), title_row("⚖️", "同样的活，两种干法")]
    rows.append(L("左列是你，右列是用了 PC-action 的你 ——", color='#0A84FF', weight=700))
    items = []
    for t, a, b in pairs:
        f = QFrame()
        f.setStyleSheet("#c { background-color:#F5F5F7; border:1px solid #E8E8ED; border-radius:11px; }")
        f.setObjectName("c")
        fl = QHBoxLayout(f)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(10)
        fl.addWidget(L(t, size=13, weight=700))
        fl.addWidget(L(a, color='#86868B', size=12), 1)
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color:#0A84FF; font-size:14px; font-weight:700; background:transparent;")
        fl.addWidget(arrow)
        fl.addWidget(L(b, color='#0A84FF', size=12, weight=700))
        items.append(f)
    wrap = QVBoxLayout()
    wrap.setSpacing(8)
    for it in items:
        wrap.addWidget(it)
    holder = QWidget()
    holder.setLayout(wrap)
    rows.append(holder)
    rows.append(L("每天省下约 47 分钟 —— 够喝两杯咖啡，或早点下班。", weight=700))
    rows.append(banner("💡 不是你变快了，是你不用再干了。"))
    return base_page(rows)


# ---------- 6 速教型 ----------

def v6():
    steps = [("1", "框选", "像截图一样框住按钮，= 左键单击"),
             ("2", "按 K", "弹出录入框，= 模拟键盘按键"),
             ("3", "按 T", "输入文字，= 模拟打字"),
             ("4", "按 ESC", "结束录制，流程自动保存")]
    rows = [kicker(), title_row("🚀", "30 秒学会，就 4 个指令")]
    rows.append(L("不整虚的，直接上手 ——", color='#0A84FF', weight=700))
    rows.append(grid4([card([L(n, color='#0A84FF', size=22, weight=700),
                             L(t, size=15, weight=700), L(d, color='#86868B', size=12)])
                       for n, t, d in steps]))
    rows.append(L("录完的流程会出现在「流程管理」里，点一下名字就回放。", weight=700))
    rows.append(L("之后每天这些活就是电脑的事了。", color='#86868B', size=12))
    rows.append(banner("💡 会截图就会用 PC-action。"))
    return base_page(rows)


# ---------- 7 幽默型 ----------

def v7():
    cards = [("🏆", "人肉宏·十年修炼", "你，就是公司最强外挂，可惜是手动挡"),
             ("🎭", "日报朗诵艺术家", "复制、粘贴、改日期，表演型复键选手"),
             ("🔐", "密码打字机", "账号密码输入速度已突破人类极限"),
             ("📦", "导出点按大师", "「导出→确定→保存」三连，行云流水")]
    rows = [kicker("STEP 1 / 6 · 说点大实话"),
            title_row("🤡", "恭喜，你已是资深「人肉自动化工程师」")]
    rows.append(L("以下奖项，说的就是你 ——", color='#0A84FF', weight=700))
    rows.append(grid4([card([L(t, size=14, weight=700), L(d, color='#86868B', size=12)])
                       for _, t, d in [(i, t, d) for i, t, d in cards]]))
    rows.append(L("奖是玩笑，时间是真没了：这些操作每天吃掉你 47 分钟。", weight=700))
    rows.append(L("要不……把这活外包给电脑？它不要工资，还不摸鱼。", color='#86868B', size=12))
    rows.append(banner("💡 自动化这条路，你早就用身体在走了 —— 就差个工具。"))
    return base_page(rows)


# ---------- 8 极简型 ----------

def v8():
    rows = [kicker("STEP 1 / 6")]
    rows.append(L("每天重复的事，", color='#1D1D1F', size=38, weight=700))
    rows.append(L("就该让电脑替你做。", color='#1D1D1F', size=38, weight=700))
    rows.append(L("你演示一遍，它记住，以后天天替你干。", color='#86868B', size=15))
    rows.append(banner("💡 做一次，之后不用做。"))
    return base_page(rows)


# ---------- 9 价值清单 ----------

def v9():
    gains = [("⏰", "每天省下 47 分钟", "重复操作全部由电脑接管，一年找回 35 个工作日"),
             ("🎯", "零出错", "不会点错、不会漏填，流程怎么录的就怎么跑"),
             ("🙌", "解放双手", "你只管想事，鼠标键盘的活交给它"),
             ("📦", "离职都能带走", "流程就是资产，谁接手都能一键复用")]
    rows = [kicker(), title_row("🎁", "用了之后，你能得到什么")]
    rows.append(L("不讲操作，先说好处 ——", color='#0A84FF', weight=700))
    rows.append(grid4([card([L(f"{i}  {t}", size=14, weight=700),
                             L(d, color='#86868B', size=12)]) for i, t, d in gains]))
    rows.append(L("上面每一条，都只需要你「做一次」来换取。", weight=700))
    rows.append(L("第一次录制多花 1 分钟，之后每天少花 47 分钟。", color='#86868B', size=12))
    rows.append(banner("💡 这笔账怎么算都划算。"))
    return base_page(rows)


# ---------- 10 时间线型 ----------

def v10():
    items = [("09:00 - 09:05", "开机五连：Chrome/微信/钉钉/邮箱/办公软件", "可自动化"),
             ("17:55 - 17:58", "日报：复制 → 改日期 → 改数据 → 发送", "可自动化"),
             ("10:00 - 10:05", "ERP 导报表：菜单 → 导出 → 格式 → 保存", "可自动化"),
             ("14:00 - 14:02", "系统登录：账号 → 密码 → 登录", "可自动化")]
    rows = [kicker(), title_row("🕒", "看你的一天，哪些在被浪费")]
    rows.append(L("这不是日程表，是你的「重复操作清单」——", color='#0A84FF', weight=700))
    for t, d, tag in items:
        f = QFrame()
        f.setStyleSheet("#c { background-color:#F5F5F7; border:1px solid #E8E8ED; border-radius:11px; }")
        f.setObjectName("c")
        fl = QHBoxLayout(f)
        fl.setContentsMargins(16, 9, 16, 9)
        fl.setSpacing(10)
        fl.addWidget(L(t, color='#0A84FF', size=12, weight=700))
        fl.addWidget(L(d, size=12), 1)
        tg = QLabel("⚡ " + tag)
        tg.setStyleSheet(f"color:#34C759; font-size:11px; font-weight:700; background:transparent;")
        fl.addWidget(tg)
        rows.append(f)
    rows.append(L("4 段共约 14 分钟的小事，一天发生不止一轮。", weight=700))
    rows.append(L("把它们录成流程后，这些时间段你就「不在岗」了。", color='#86868B', size=12))
    rows.append(banner("💡 时间轴上每一格，都能变成一条流程。"))
    return base_page(rows)


VARIANTS = [
    ('基准：现用文案', '灰卡+蓝条，现版本', v0),
    ('1 数字冲击型', '用真实数字算账，最直观', v1),
    ('2 扎心提问型', '一连串「是不是你」，共鸣拉满', v2),
    ('3 故事型', '小李 vs 老王，代入感强', v3),
    ('4 对话型', '和电脑聊两句，轻松有趣', v4),
    ('5 对比型', '手动 vs 自动逐条对比，转化率高', v5),
    ('6 速教型', '少煽情直接教，4 指令上手', v6),
    ('7 幽默型', '「人肉自动化工程师」梗，年轻化', v7),
    ('8 极简型', '一句话说完，气场足', v8),
    ('9 价值清单型', '利益点清单，先给好处', v9),
    ('10 时间线型', '一天时间轴标出浪费点', v10),
]


def main():
    app = QApplication(sys.argv)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '帮助页内容方案预览')
    os.makedirs(out_dir, exist_ok=True)

    shots = []
    for name, desc, fn in VARIANTS:
        w = fn()
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
        p.drawText(300, y + 26, desc)
        y += label_h
        p.drawImage(20, y, pix.toImage())
        y += PAGE_H + gap
    p.end()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '帮助页内容方案对比.png')
    canvas.save(out)
    print('对比长图:', out)


if __name__ == '__main__':
    main()
