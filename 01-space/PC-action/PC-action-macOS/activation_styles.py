# -*- coding: utf-8 -*-
"""
激活对话框风格预设（10 套）
- 与 activation_dialog.ActivationDialog 配合使用：ActivationDialog(parent, style="dark")
- 每套预设只改外观（QSS / 阴影 / 容器背景），不改布局与逻辑
- 关键字段：
    container   弹窗容器 QSS（QWidget#C）
    title       标题 QSS
    close       关闭按钮 QSS（普通 + hover）
    muted       次要文字颜色（账户行 / 提示 / 消息）
    status      状态卡 QSS 模板，{bg}{fg} 为动态状态色占位
    input       激活码输入框 QSS
    button      激活按钮 QSS（normal/hover/pressed/disabled）
    link        购买链接颜色
    shadow      (模糊半径, QColor 元组)
"""

STYLES = {
    # 1) macOS 原版：白卡 + 嵌套灰面板（默认）
    "macos": {
        "container": ("QFrame#C{background:#FFFFFF;border:1px solid #D1D1D6;"
                      "border-radius:18px;}"),
        "title": "font-size:17px;font-weight:700;color:#1A1A2E;background:transparent;",
        "close": ("QPushButton{background:#FF3B30;border:none;border-radius:8px;"
                  "min-width:0px;min-height:0px;padding:0px;}"
                  "QPushButton:hover{background:#FF6B5E;}"),
        "chip": "#F5F5F7",
        "panel": "QFrame#Panel{background:#F5F5F7;border:none;border-radius:14px;}",
        "muted": "#86868B",
        "status": ("QLabel{{background:{bg};border-radius:10px;"
                   "font-size:15px;font-weight:700;color:{fg};padding:10px 12px;}}"),
        "input": ("QLineEdit{{background:#FFFFFF;border:1px solid #E5E5EA;border-radius:12px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}}"
                  "QLineEdit:focus{{border-color:#111114;}}"),
        "button": ("QPushButton{{background:#111114;color:#fff;border:none;border-radius:21px;"
                   "font-size:16px;font-weight:700;min-height:0px;padding:0px;}}"
                   "QPushButton:hover{{background:#2C2C31;}}"
                   "QPushButton:pressed{{background:#000000;}}"
                   "QPushButton:disabled{{background:#C7C7CC;}}"),
        "link": "#0A84FF",
        "shadow": (50, (0, 0, 0, 80)),
    },

    # 2) 深夜碳黑：全暗色 + 描边，暗色桌面上不再与背景糊在一起
    "carbon": {
        "container": ("QWidget#C{background:#1E1F24;border:1px solid #3A3B42;"
                      "border-radius:14px;}"),
        "title": "font-size:18px;font-weight:700;color:#F2F2F7;background:transparent;",
        "close": ("QPushButton{background:transparent;color:#98989F;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:#2F3037;color:#FFFFFF;}"),
        "muted": "#98989F",
        "status": ("QLabel{{background:{bg};border:1px solid #3A3B42;border-radius:10px;"
                   "font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:#2A2B31;border:2px solid #3A3B42;border-radius:10px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#F2F2F7;}}"
                  "QLineEdit:focus{{border-color:#0A84FF;}}"),
        "button": ("QPushButton{{background:#0A84FF;color:#fff;border:none;border-radius:10px;"
                   "font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#2A95FF;}}"
                   "QPushButton:pressed{{background:#0069D9;}}"
                   "QPushButton:disabled{{background:#48484E;}}"),
        "link": "#64A8FF",
        "shadow": (50, (0, 0, 0, 120)),
    },

    # 3) 极光渐变：顶部品牌色渐变条 + 白卡，边界一眼可见
    "aurora": {
        "container": ("QWidget#C{background:#FFFFFF;border:none;border-radius:16px;"
                      "border-top:6px solid #5E5CE6;}"),
        "title": "font-size:18px;font-weight:700;color:#1D1D3F;background:transparent;",
        "close": ("QPushButton{background:transparent;color:#9A9AB0;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:#EEF0FF;color:#5E5CE6;}"),
        "muted": "#8A8AA3",
        "status": ("QLabel{{background:{bg};border-radius:12px;"
                   "font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:#F7F7FE;border:2px solid #E3E3F5;border-radius:12px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#1D1D3F;}}"
                  "QLineEdit:focus{{border-color:#5E5CE6;}}"),
        "button": ("QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                   "stop:0 #5E5CE6, stop:1 #0A84FF);color:#fff;border:none;border-radius:12px;"
                   "font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#6E6CF0;}}"
                   "QPushButton:pressed{{background:#4B49D6;}}"
                   "QPushButton:disabled{{background:#C9C9E8;}}"),
        "link": "#5E5CE6",
        "shadow": (48, (94, 92, 230, 60)),
    },

    # 4) 薄荷清新：浅绿底 + 绿按钮，状态卡带描边
    "mint": {
        "container": ("QWidget#C{background:#F7FBF8;border:1px solid #D8ECDD;"
                      "border-radius:14px;}"),
        "title": "font-size:18px;font-weight:700;color:#1B4332;background:transparent;",
        "close": ("QPushButton{background:transparent;color:#6B9080;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:#E3F2E8;color:#1B4332;}"),
        "muted": "#6B9080",
        "status": ("QLabel{{background:{bg};border:1px solid #CDE5D6;border-radius:10px;"
                   "font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:#FFFFFF;border:2px solid #CDE5D6;border-radius:10px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#1B4332;}}"
                  "QLineEdit:focus{{border-color:#2D6A4F;}}"),
        "button": ("QPushButton{{background:#2D6A4F;color:#fff;border:none;border-radius:10px;"
                   "font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#40916C;}}"
                   "QPushButton:pressed{{background:#1B4332;}}"
                   "QPushButton:disabled{{background:#B7CCBF;}}"),
        "link": "#2D6A4F",
        "shadow": (44, (45, 106, 79, 45)),
    },

    # 5) 落日暖橙：奶油底 + 橙色主按钮，活泼
    "sunset": {
        "container": ("QWidget#C{background:#FFF9F2;border:1px solid #F5DFC8;"
                      "border-radius:16px;}"),
        "title": "font-size:18px;font-weight:700;color:#4A2C17;background:transparent;",
        "close": ("QPushButton{background:transparent;color:#B08968;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:#FBEADB;color:#4A2C17;}"),
        "muted": "#B08968",
        "status": ("QLabel{{background:{bg};border-radius:12px;"
                   "font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:#FFFFFF;border:2px solid #F0D9C0;border-radius:12px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#4A2C17;}}"
                  "QLineEdit:focus{{border-color:#E8590C;}}"),
        "button": ("QPushButton{{background:#E8590C;color:#fff;border:none;border-radius:12px;"
                   "font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#F76707;}}"
                   "QPushButton:pressed{{background:#D9480F;}}"
                   "QPushButton:disabled{{background:#F1C4A6;}}"),
        "link": "#E8590C",
        "shadow": (46, (232, 89, 12, 45)),
    },

    # 6) 极简线框：无填充色，靠 2px 描边 + 粗左侧色条区分层次
    "minimal": {
        "container": ("QWidget#C{background:#FFFFFF;border:2px solid #1A1A2E;"
                      "border-radius:6px;}"),
        "title": ("font-size:18px;font-weight:700;color:#1A1A2E;background:transparent;"
                  "border-left:4px solid #1A1A2E;padding-left:10px;"),
        "close": ("QPushButton{background:transparent;color:#6C6C80;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:#1A1A2E;color:#FFFFFF;}"),
        "muted": "#6C6C80",
        "status": ("QLabel{{background:{bg};border:1px solid #1A1A2E;border-radius:4px;"
                   "font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:#FFFFFF;border:2px solid #1A1A2E;border-radius:4px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#1A1A2E;}}"
                  "QLineEdit:focus{{border-color:#0A84FF;}}"),
        "button": ("QPushButton{{background:#1A1A2E;color:#fff;border:none;border-radius:4px;"
                   "font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#33334D;}}"
                   "QPushButton:pressed{{background:#0D0D17;}}"
                   "QPushButton:disabled{{background:#B9B9C6;}}"),
        "link": "#0A84FF",
        "shadow": (0, (0, 0, 0, 0)),
    },

    # 7) 科技蓝：深海蓝容器 + 青色高亮，暗色科技感
    "tech": {
        "container": ("QWidget#C{background:#0B2545;border:1px solid #1D4E89;"
                      "border-radius:12px;}"),
        "title": "font-size:18px;font-weight:700;color:#E8F1FF;background:transparent;",
        "close": ("QPushButton{background:transparent;color:#7FA8D9;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:#13375F;color:#E8F1FF;}"),
        "muted": "#7FA8D9",
        "status": ("QLabel{{background:{bg};border:1px solid #1D4E89;border-radius:8px;"
                   "font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:#13375F;border:2px solid #1D4E89;border-radius:8px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#E8F1FF;}}"
                  "QLineEdit:focus{{border-color:#00D4FF;}}"),
        "button": ("QPushButton{{background:#00D4FF;color:#04264B;border:none;border-radius:8px;"
                   "font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#33DEFF;}}"
                   "QPushButton:pressed{{background:#00B2D9;}}"
                   "QPushButton:disabled{{background:#3E5E7E;}}"),
        "link": "#00D4FF",
        "shadow": (52, (0, 100, 180, 90)),
    },

    # 8) 玫瑰粉金：浅粉底 + 玫红按钮，柔和
    "rose": {
        "container": ("QWidget#C{background:#FFF5F7;border:1px solid #F5C9D4;"
                      "border-radius:16px;}"),
        "title": "font-size:18px;font-weight:700;color:#4A1D2B;background:transparent;",
        "close": ("QPushButton{background:transparent;color:#C2808F;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:#FBE3E9;color:#4A1D2B;}"),
        "muted": "#C2808F",
        "status": ("QLabel{{background:{bg};border-radius:12px;"
                   "font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:#FFFFFF;border:2px solid #F2CBD6;border-radius:12px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#4A1D2B;}}"
                  "QLineEdit:focus{{border-color:#D6336C;}}"),
        "button": ("QPushButton{{background:#D6336C;color:#fff;border:none;border-radius:12px;"
                   "font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#E64980;}}"
                   "QPushButton:pressed{{background:#B02A5B;}}"
                   "QPushButton:disabled{{background:#EDB7C8;}}"),
        "link": "#D6336C",
        "shadow": (46, (214, 51, 108, 40)),
    },

    # 9) 毛玻璃暗夜：半透明深色容器，透出底层内容但仍有清晰边界
    "glass": {
        "container": ("QWidget#C{background:rgba(24,26,32,0.92);border:1px solid rgba(255,255,255,0.14);"
                      "border-radius:16px;}"),
        "title": "font-size:18px;font-weight:700;color:#F5F5FA;background:transparent;",
        "close": ("QPushButton{background:transparent;color:#A8A8B8;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:rgba(255,255,255,0.10);color:#FFFFFF;}"),
        "muted": "#A8A8B8",
        "status": ("QLabel{{background:{bg};border:1px solid rgba(255,255,255,0.10);"
                   "border-radius:12px;font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:rgba(255,255,255,0.08);border:2px solid rgba(255,255,255,0.16);"
                  "border-radius:12px;padding:0 12px;font-size:15px;font-weight:600;"
                  "letter-spacing:1px;color:#F5F5FA;}}"
                  "QLineEdit:focus{{border-color:#7C7CF0;}}"),
        "button": ("QPushButton{{background:#7C7CF0;color:#fff;border:none;border-radius:12px;"
                   "font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#9090F5;}}"
                   "QPushButton:pressed{{background:#6262D8;}}"
                   "QPushButton:disabled{{background:#4A4A66;}}"),
        "link": "#9A9AFF",
        "shadow": (56, (0, 0, 0, 150)),
    },

    # 10) 新拟态（Neumorphism）：同色系凹凸质感，输入框内凹、按钮外凸
    "neu": {
        "container": ("QWidget#C{background:#E8ECF3;border:1px solid #D5DBE6;"
                      "border-radius:18px;}"),
        "title": "font-size:18px;font-weight:700;color:#2D3A52;background:transparent;",
        "close": ("QPushButton{background:#E8ECF3;color:#7C89A3;border:none;"
                  "border-radius:14px;font-size:18px;font-weight:600;}"
                  "QPushButton:hover{background:#DDE3EE;color:#2D3A52;}"),
        "muted": "#7C89A3",
        "status": ("QLabel{{background:{bg};border-radius:12px;"
                   "font-size:14px;font-weight:600;color:{fg};padding:12px 16px;}}"),
        "input": ("QLineEdit{{background:#E8ECF3;border:none;border-radius:12px;"
                  "padding:0 12px;font-size:15px;font-weight:600;letter-spacing:1px;color:#2D3A52;}}"
                  "QLineEdit:focus{{border:2px solid #5B7BBD;}}"),
        "button": ("QPushButton{{background:#E8ECF3;color:#3D5A9E;border:1px solid #D0D8E6;"
                   "border-radius:12px;font-size:15px;font-weight:700;}}"
                   "QPushButton:hover{{background:#DFE6F1;}}"
                   "QPushButton:pressed{{background:#D2DAE9;color:#2D3A52;}}"
                   "QPushButton:disabled{{color:#AEB8CB;}}"),
        "link": "#3D5A9E",
        "shadow": (60, (120, 135, 165, 70)),
    },
}

DEFAULT_STYLE = "macos"


def get_style(name=None):
    """按名称取预设，未知名称回退默认"""
    return STYLES.get(name or DEFAULT_STYLE, STYLES[DEFAULT_STYLE])
