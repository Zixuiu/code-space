"""
文件: styles.py
用途: 提供统一的UI样式管理，避免在各文件中重复定义样式
"""

# 从utils模块导入get_screen_size函数，避免重复定义
from utils import get_screen_size

# ============================================
# 彩虹糖果主题配色方案 - 方案15
# 年轻时尚，渐变彩色系
# ============================================
PRIMARY_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6B6B, stop:1 #4ECDC4)"
SECONDARY = "#FFE66D"
ACCENT = "#FF6B6B"
BG = "#FFFFFF"
CARD = "#FFF9F9"
TEXT = "#2C3E50"
MUTED = "#636E72"
BORDER = "#DFE6E9"

THEME_PRIMARY = PRIMARY_GRADIENT
THEME_SECONDARY = SECONDARY
THEME_ACCENT = ACCENT
THEME_BG = BG
THEME_CARD = CARD
THEME_TEXT = TEXT
THEME_MUTED = MUTED
THEME_BORDER = BORDER

def get_light_theme_styles():
    """获取浅色主题样式字典 - 彩虹糖果风格"""
    return {
        "main_window": {
            "background_color": THEME_BG,
            "color": THEME_TEXT,
            "font_family": "Microsoft YaHei"
        },
        "widget": {
            "background_color": THEME_BG,
            "color": THEME_TEXT,
            "font_family": "Microsoft YaHei"
        },
        "button": {
            "background_color": THEME_PRIMARY,
            "color": "white",
            "border": "none",
            "font_weight": "500",
            "font_size": "14px",
            "font_family": "Microsoft YaHei"
        },
        "button_hover": {
            "background_color": THEME_SECONDARY,
            "border": "none"
        },
        "button_pressed": {
            "background_color": "#e55a5a"
        },
        "button_secondary": {
            "background_color": THEME_SECONDARY,
            "color": THEME_TEXT,
            "border": "none"
        },
        "button_secondary_hover": {
            "background_color": THEME_ACCENT,
            "border_color": THEME_ACCENT,
            "color": THEME_TEXT
        },
        "label": {
            "color": THEME_TEXT,
            "font_family": "Microsoft YaHei"
        },
        "menu_bar": {
            "background_color": THEME_BG,
            "color": THEME_TEXT,
            "border_bottom": f"1px solid {THEME_BORDER}",
            "font_family": "Microsoft YaHei"
        },
        "menu": {
            "background_color": THEME_CARD,
            "color": THEME_TEXT,
            "border": f"1px solid {THEME_BORDER}",
            "font_family": "Microsoft YaHei"
        },
        "status_bar": {
            "background_color": THEME_BG,
            "color": THEME_MUTED,
            "border_top": f"1px solid {THEME_BORDER}",
            "font_family": "Microsoft YaHei"
        },
        "dialog": {
            "background_color": THEME_CARD,
            "color": THEME_TEXT
        },
        "input": {
            "background_color": THEME_BG,
            "color": THEME_TEXT,
            "border": f"1px solid {THEME_BORDER}",
            "font_family": "Microsoft YaHei"
        },
        "table": {
            "background_color": THEME_BG,
            "color": THEME_TEXT,
            "border": f"1px solid {THEME_BORDER}",
            "gridline_color": THEME_BORDER,
            "selection_background_color": "#fff5f5",
            "font_family": "Microsoft YaHei"
        },
        "table_header": {
            "background_color": THEME_CARD,
            "color": THEME_TEXT,
            "font_weight": "bold",
            "font_family": "Microsoft YaHei"
        },
        "card": {
            "background_color": THEME_CARD,
            "border": f"1px solid {THEME_BORDER}"
        },
        "tab_widget": {
            "background_color": THEME_BG,
            "color": THEME_TEXT,
            "border": f"1px solid {THEME_BORDER}"
        },
        "tab_bar": {
            "background_color": THEME_CARD,
            "color": THEME_MUTED,
            "border": f"1px solid {THEME_BORDER}"
        },
        "combo_box": {
            "background_color": THEME_BG,
            "color": THEME_TEXT,
            "border": f"1px solid {THEME_BORDER}",
            "font_family": "Microsoft YaHei"
        },
        "checkbox": {
            "color": THEME_TEXT,
            "font_family": "Microsoft YaHei"
        }
    }

def generate_dynamic_styles(screen_width=None, screen_height=None):
    """根据屏幕尺寸生成动态样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    # 计算动态尺寸
    main_window_radius = int(screen_height * 0.012)
    widget_radius = int(screen_height * 0.008)
    button_radius = int(screen_height * 0.008)
    menu_radius = int(screen_height * 0.006)
    dialog_border_radius = int(screen_height * 0.012)
    input_border_radius = int(screen_height * 0.006)
    checkbox_border_radius = int(screen_height * 0.004)
    card_radius = int(screen_height * 0.012)
    tab_border_radius = int(screen_height * 0.012)
    table_border_radius = int(screen_height * 0.012)
    header_border_radius = int(screen_height * 0.008)
    menu_border_radius = int(screen_height * 0.012)

    # 获取基础样式
    styles = get_light_theme_styles()

    # 生成完整样式表 - 彩虹糖果风格
    style_sheet = f"""
        QMainWindow {{
            background-color: {styles["main_window"]["background_color"]};
            color: {styles["main_window"]["color"]};
            font-family: "{styles["main_window"]["font_family"]}";
            border-radius: {main_window_radius}px;
        }}
        QWidget {{
            background-color: {styles["widget"]["background_color"]};
            color: {styles["widget"]["color"]};
            font-family: "{styles["widget"]["font_family"]}";
            border-radius: {widget_radius}px;
        }}
        QPushButton {{
            background-color: {styles["button"]["background_color"]};
            color: {styles["button"]["color"]};
            border: {styles["button"]["border"]};
            border-radius: {button_radius}px;
            padding: 8px 16px;
            font-weight: {styles["button"]["font_weight"]};
            font-size: {styles["button"]["font_size"]};
            font-family: "{styles["button"]["font_family"]}";
        }}
        QPushButton:hover {{
            background-color: {styles["button_hover"]["background_color"]};
            border: {styles["button_hover"]["border"]};
        }}
        QPushButton:pressed {{
            background-color: {styles["button_pressed"]["background_color"]};
        }}
        QLabel {{
            color: {styles["label"]["color"]};
            font-family: "{styles["label"]["font_family"]}";
        }}
        QMenuBar {{
            background-color: {styles["menu_bar"]["background_color"]};
            color: {styles["menu_bar"]["color"]};
            border-bottom: {styles["menu_bar"]["border_bottom"]};
            font-family: "{styles["menu_bar"]["font_family"]}";
            border-top-left-radius: {main_window_radius}px;
            border-top-right-radius: {main_window_radius}px;
        }}
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: {menu_radius}px;
        }}
        QMenuBar::item:selected {{
            background-color: #fff5f5;
            border-radius: {menu_radius}px;
        }}
        QMenu {{
            background-color: {styles["menu"]["background_color"]};
            color: {styles["menu"]["color"]};
            border: {styles["menu"]["border"]};
            border-radius: {button_radius}px;
            font-family: "{styles["menu"]["font_family"]}";
        }}
        QMenu::item {{
            padding: 6px 16px;
            border-radius: {menu_radius}px;
        }}
        QMenu::item:selected {{
            background-color: #fff5f5;
            color: {THEME_PRIMARY};
            border-radius: {menu_radius}px;
        }}
        QStatusBar {{
            background-color: {styles["status_bar"]["background_color"]};
            color: {styles["status_bar"]["color"]};
            border-top: {styles["status_bar"]["border_top"]};
            font-family: "{styles["status_bar"]["font_family"]}";
            border-bottom-left-radius: {main_window_radius}px;
            border-bottom-right-radius: {main_window_radius}px;
        }}
        QDialog {{
            background-color: {styles["dialog"]["background_color"]};
            color: {styles["dialog"]["color"]};
            border-radius: {dialog_border_radius}px;
        }}
        QLineEdit {{
            background-color: {styles["input"]["background_color"]};
            color: {styles["input"]["color"]};
            border: {styles["input"]["border"]};
            border-radius: {input_border_radius}px;
            padding: 8px;
            font-family: "{styles["input"]["font_family"]}";
        }}
        QLineEdit:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QTableWidget {{
            background-color: {styles["table"]["background_color"]};
            color: {styles["table"]["color"]};
            border: {styles["table"]["border"]};
            border-radius: {table_border_radius}px;
            gridline-color: {styles["table"]["gridline_color"]};
            selection-background-color: {styles["table"]["selection_background_color"]};
            font-family: "{styles["table"]["font_family"]}";
        }}
        QHeaderView::section {{
            background-color: {styles["table_header"]["background_color"]};
            color: {styles["table_header"]["color"]};
            padding: 8px;
            border: none;
            border-bottom: 1px solid {THEME_BORDER};
            font-weight: {styles["table_header"]["font_weight"]};
            font-family: "{styles["table_header"]["font_family"]}";
        }}
        QTabWidget::pane {{
            border: 1px solid {THEME_BORDER};
            background-color: {styles["tab_widget"]["background_color"]};
            color: {styles["tab_widget"]["color"]};
            border-radius: {tab_border_radius}px;
            margin: 0px;
            padding: 0px;
        }}
        QTabBar::tab {{
            background-color: {styles["tab_bar"]["background_color"]};
            color: {styles["tab_bar"]["color"]};
            border: {styles["tab_bar"]["border"]};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: {tab_border_radius}px;
            border-top-right-radius: {tab_border_radius}px;
        }}
        QTabBar::tab:selected {{
            background-color: {THEME_PRIMARY};
            color: white;
        }}
        QTabWidget {{
            margin: 0px;
        }}
        QTabBar {{
            margin: 0px;
            padding: 0px;
        }}
        QComboBox {{
            background-color: {styles["combo_box"]["background_color"]};
            color: {styles["combo_box"]["color"]};
            border: {styles["combo_box"]["border"]};
            border-radius: {button_radius}px;
            padding: 8px 32px 8px 12px;
            font-weight: bold;
            font-family: "{styles["combo_box"]["font_family"]}";
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
            subcontrol-origin: padding;
            subcontrol-position: center right;
        }}
        QComboBox::down-arrow {{
            border-image: url(data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'><path d='M1 1L6 6L11 1' stroke='{THEME_PRIMARY.replace("#", "%23")}' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>) 0 0 0 0 stretch stretch;
            width: 12px;
            height: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {styles["combo_box"]["background_color"]};
            color: {styles["combo_box"]["color"]};
            border: {styles["combo_box"]["border"]};
            border-radius: {button_radius}px;
            selection-background-color: #fff5f5;
            font-family: "{styles["combo_box"]["font_family"]}";
        }}
        QCheckBox {{
            color: {styles["checkbox"]["color"]};
            font-family: "{styles["checkbox"]["font_family"]}";
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {THEME_BORDER};
            border-radius: {checkbox_border_radius}px;
            background-color: {THEME_BG};
        }}
        QCheckBox::indicator:checked {{
            background-color: {THEME_PRIMARY};
            border: 2px solid {THEME_PRIMARY};
        }}
        QCheckBox::indicator:checked::after {{
            content: "✓";
            color: white;
            font-size: 10px;
        }}
        QTextEdit {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {input_border_radius}px;
            padding: 8px;
            font-family: "Microsoft YaHei";
        }}
        QTextEdit:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QSpinBox, QDoubleSpinBox {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {input_border_radius}px;
            padding: 4px;
            font-family: "Microsoft YaHei";
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QRadioButton {{
            color: {THEME_TEXT};
            font-family: "Microsoft YaHei";
        }}
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {THEME_BORDER};
            border-radius: 8px;
            background-color: {THEME_BG};
        }}
        QRadioButton::indicator:checked {{
            background-color: {THEME_PRIMARY};
            border: 2px solid {THEME_PRIMARY};
        }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: {THEME_BORDER};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 12px;
            height: 12px;
            background: {THEME_PRIMARY};
            border-radius: 6px;
        }}
        QScrollBar:vertical {{
            background: #fafafa;
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: #d0d0d0;
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #b0b0b0;
        }}
        QScrollBar:horizontal {{
            background: #fafafa;
            height: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: #d0d0d0;
            border-radius: 4px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: #b0b0b0;
        }}
    """

    return style_sheet

def apply_dialog_style(dialog, screen_width=None, screen_height=None):
    """为对话框应用样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    # 设置窗口标志：移除帮助按钮，添加最小化按钮
    from PyQt5.QtCore import Qt
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

    # 计算动态尺寸
    dialog_border_radius = int(screen_height * 0.012)
    button_border_radius = int(screen_height * 0.006)
    input_border_radius = int(screen_height * 0.006)
    checkbox_border_radius = int(screen_height * 0.004)

    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {THEME_CARD};
            color: {THEME_TEXT};
            border-radius: {dialog_border_radius}px;
        }}
        QLineEdit {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {input_border_radius}px;
            padding: 8px;
            font-family: "Microsoft YaHei";
        }}
        QLineEdit:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QCheckBox {{
            color: {THEME_TEXT};
            font-family: "Microsoft YaHei";
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {THEME_BORDER};
            border-radius: {checkbox_border_radius}px;
            background-color: {THEME_BG};
        }}
        QCheckBox::indicator:checked {{
            background-color: {THEME_PRIMARY};
            border: 2px solid {THEME_PRIMARY};
        }}
        QCheckBox::indicator:checked::after {{
            content: "✓";
            color: white;
            font-size: 10px;
        }}
        QPushButton {{
            background-color: {THEME_PRIMARY};
            color: white;
            border: none;
            border-radius: {button_border_radius}px;
            padding: 8px 16px;
            font-weight: 500;
            font-family: "Microsoft YaHei";
        }}
        QPushButton:hover {{
            background-color: {THEME_SECONDARY};
        }}
        QPushButton:pressed {{
            background-color: #e55a5a;
        }}
        QLabel {{
            color: {THEME_TEXT};
            font-family: "Microsoft YaHei";
        }}
        QTextEdit {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {input_border_radius}px;
            padding: 8px;
            font-family: "Microsoft YaHei";
        }}
        QTextEdit:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QComboBox {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {button_border_radius}px;
            padding: 8px;
            font-family: "Microsoft YaHei";
        }}
        QComboBox:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QSpinBox, QDoubleSpinBox {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {input_border_radius}px;
            padding: 4px;
            font-family: "Microsoft YaHei";
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QRadioButton {{
            color: {THEME_TEXT};
            font-family: "Microsoft YaHei";
        }}
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {THEME_BORDER};
            border-radius: 8px;
            background-color: {THEME_BG};
        }}
        QRadioButton::indicator:checked {{
            background-color: {THEME_PRIMARY};
            border: 2px solid {THEME_PRIMARY};
        }}
    """)

def apply_app_style(app, screen_width=None, screen_height=None):
    """为应用程序应用全局样式"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()
    
    styles = generate_dynamic_styles(screen_width, screen_height)
    app.setStyleSheet(styles)
    
    # 设置全局字体
    if app is None:
        app = QApplication.instance()
        
    if app is None:
        return
        
    # 动态计算字体大小 - 根据candy theme要求调整为更大更清晰的字体
    font_size = max(16, min(20, int(screen_height * 0.012)))
    font_family = "Microsoft YaHei"
        
    font = app.font()
    font.setFamily(font_family)
    font.setPointSize(font_size)
    app.setFont(font)

def apply_window_style(window, screen_width=None, screen_height=None):
    """为窗口应用样式"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()
    
    styles = generate_dynamic_styles(screen_width, screen_height)
    window.setStyleSheet(styles)
    
    # 居中显示窗口
    from PyQt5.QtWidgets import QApplication
    screen_geometry = QApplication.primaryScreen().availableGeometry()
    x = (screen_geometry.width() - window.width()) // 2
    y = (screen_geometry.height() - window.height()) // 2
    window.move(x, y)
    window.current_window_pos = window.pos()

def get_button_style(style_type="primary", screen_width=None, screen_height=None):
    """获取按钮样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    button_radius = int(screen_height * 0.008)
    font_size = 18

    if style_type == "primary":
        return f"""
            QPushButton {{
                background: {PRIMARY_GRADIENT};
                color: white;
                border: none;
                border-radius: {button_radius}px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: {font_size}px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFE66D, stop:1 #FF6B6B);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e55a5a, stop:1 #FF6B6B);
            }}
            QPushButton:disabled {{
                background: {BORDER};
                color: {MUTED};
            }}
        """
    elif style_type == "secondary":
        return f"""
            QPushButton {{
                background-color: {SECONDARY};
                color: {TEXT};
                border: none;
                border-radius: {button_radius}px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: {font_size}px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #e55a5a;
            }}
        """
    elif style_type == "danger":
        return f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: {button_radius}px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: {font_size}px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #ff8787;
            }}
            QPushButton:pressed {{
                background-color: #e55a5a;
            }}
        """
    elif style_type == "success":
        return f"""
            QPushButton {{
                background-color: {SECONDARY};
                color: white;
                border: none;
                border-radius: {button_radius}px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: {font_size}px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #6ee7de;
            }}
            QPushButton:pressed {{
                background-color: #3dbdb5;
            }}
        """
    else:
        return get_button_style("primary", screen_width, screen_height)

def get_input_style(screen_width=None, screen_height=None):
    """获取输入框样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    input_radius = int(screen_height * 0.006)

    return f"""
        QLineEdit {{
            background-color: {BG};
            color: {TEXT};
            border: 2px solid {BORDER};
            border-radius: 999px;
            padding: 8px 16px;
            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            font-size: 24px;
        }}
        QLineEdit:focus {{
            border: 2px solid {ACCENT};
        }}
        QLineEdit::placeholder {{
            color: {MUTED};
        }}
    """

def get_checkbox_style(screen_width=None, screen_height=None):
    """获取复选框样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    checkbox_radius = int(screen_height * 0.004)

    return f"""
        QCheckBox {{
            color: {TEXT};
            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            font-size: 20px;
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid {BORDER};
            background-color: {BG};
        }}
        QCheckBox::indicator:checked {{
            background-color: {ACCENT};
            border-color: {ACCENT};
        }}
    """

def get_card_style(screen_width=None, screen_height=None):
    """获取卡片样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    card_radius = int(screen_height * 0.012)

    return f"""
        QFrame {{
            background-color: {CARD};
            border: 1px solid {BORDER};
            border-radius: {card_radius}px;
        }}
    """

def get_table_style(screen_width=None, screen_height=None):
    """获取表格样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    return f"""
        QTableWidget {{
            background: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: 8px;
            gridline-color: {THEME_BORDER};
            selection-background-color: #fff5f5;
            font-family: "Microsoft YaHei";
            alternate-background-color: {THEME_CARD};
        }}
        QHeaderView::section {{
            background: {THEME_CARD};
            color: {THEME_TEXT};
            padding: 10px 12px;
            border: none;
            border-right: 1px solid {THEME_BORDER};
            border-bottom: 2px solid {THEME_BORDER};
            font-weight: 600;
            font-family: "Microsoft YaHei";
            font-size: 13px;
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
        QTableWidget::item {{
            padding: 10px 12px;
            border: none;
            border-bottom: 1px solid {THEME_BORDER};
            text-align: center;
        }}
        QTableWidget::item:hover {{
            background: {THEME_CARD};
        }}
        QTableWidget::item:selected {{
            color: {THEME_TEXT};
            background: #fff5f5;
        }}
        QTableWidget::horizontalHeader {{
            background: {THEME_CARD};
        }}
        QTableCornerButton::section {{
            background: {THEME_CARD};
            border: none;
            border-bottom: 2px solid {THEME_BORDER};
        }}
    """

def get_message_box_style(screen_width=None, screen_height=None):
    """获取消息框样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    dialog_radius = int(screen_height * 0.012)
    button_radius = int(screen_height * 0.006)
    font_size = max(12, min(16, int(screen_width * 0.005)))

    return f"""
        QMessageBox {{
            background-color: {THEME_CARD};
            color: {THEME_TEXT};
            border-radius: {dialog_radius}px;
        }}
        QMessageBox QLabel {{
            color: {THEME_TEXT};
            font-family: "Microsoft YaHei";
        }}
        QMessageBox QPushButton {{
            background-color: {THEME_PRIMARY};
            color: white;
            border: none;
            border-radius: {button_radius}px;
            padding: 8px 16px;
            font-weight: 500;
            font-family: "Microsoft YaHei";
            font-size: {font_size}px;
            min-width: 70px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {THEME_SECONDARY};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: #e55a5a;
        }}
    """

def get_dynamic_radius(radius_type="default", screen_height=None):
    """根据屏幕高度和类型获取动态圆角半径"""
    if not screen_height:
        from utils import get_screen_size
        _, screen_height = get_screen_size()
    
    radius_map = {
        "default": int(screen_height * 0.012),
        "small": int(screen_height * 0.006),
        "button": int(screen_height * 0.006),
        "image": int(screen_height * 0.008),
        "card": int(screen_height * 0.012),
        "menu": int(screen_height * 0.006),
        "msg_box": int(screen_height * 0.012),
        "input_dialog": int(screen_height * 0.012),
        "file_dialog": int(screen_height * 0.012),
        "combo_box": int(screen_height * 0.006),
        "spin_box": int(screen_height * 0.006),
        "check_box": int(screen_height * 0.004),
    }
    
    return radius_map.get(radius_type, int(screen_height * 0.012))


def get_file_dialog_style(screen_width=None, screen_height=None):
    """获取文件对话框样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    dialog_radius = int(screen_height * 0.012)
    button_radius = int(screen_height * 0.006)
    font_size = max(12, min(16, int(screen_width * 0.005)))

    return f"""
        QFileDialog {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border-radius: {dialog_radius}px;
        }}
        QFileDialog QLabel {{
            color: {THEME_TEXT};
            font-family: "Microsoft YaHei";
        }}
        QFileDialog QLineEdit {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {int(screen_height * 0.006)}px;
            padding: 6px;
            font-family: "Microsoft YaHei";
            font-size: {font_size}px;
        }}
        QFileDialog QLineEdit:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QFileDialog QPushButton {{
            background-color: {THEME_PRIMARY};
            color: white;
            border: none;
            border-radius: {button_radius}px;
            padding: 8px 16px;
            font-weight: 500;
            font-family: "Microsoft YaHei";
            font-size: {font_size}px;
        }}
        QFileDialog QPushButton:hover {{
            background-color: {THEME_SECONDARY};
        }}
        QFileDialog QPushButton:pressed {{
            background-color: #e55a5a;
        }}
        QFileDialog QListWidget {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {int(screen_height * 0.006)}px;
            font-family: "Microsoft YaHei";
            font-size: {font_size}px;
        }}
        QFileDialog QTreeView {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {int(screen_height * 0.006)}px;
            font-family: "Microsoft YaHei";
            font-size: {font_size}px;
        }}
    """

def get_input_dialog_style(screen_width=None, screen_height=None):
    """获取输入对话框样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    dialog_radius = int(screen_height * 0.012)
    button_radius = int(screen_height * 0.006)
    font_size = max(12, min(16, int(screen_width * 0.005)))

    return f"""
        QInputDialog {{
            background-color: {THEME_CARD};
            color: {THEME_TEXT};
            border-radius: {dialog_radius}px;
        }}
        QInputDialog QLabel {{
            color: {THEME_TEXT};
            font-family: "Microsoft YaHei";
        }}
        QInputDialog QLineEdit {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border: 1px solid {THEME_BORDER};
            border-radius: {int(screen_height * 0.006)}px;
            padding: 6px;
            font-family: "Microsoft YaHei";
            font-size: {font_size}px;
        }}
        QInputDialog QLineEdit:focus {{
            border: 2px solid {THEME_PRIMARY};
        }}
        QInputDialog QPushButton {{
            background-color: {THEME_PRIMARY};
            color: white;
            border: none;
            border-radius: {button_radius}px;
            padding: 8px 16px;
            font-weight: 500;
            font-family: "Microsoft YaHei";
            font-size: {font_size}px;
        }}
        QInputDialog QPushButton:hover {{
            background-color: {THEME_SECONDARY};
        }}
        QInputDialog QPushButton:pressed {{
            background-color: #e55a5a;
        }}
    """

def get_color_dialog_style(screen_width=None, screen_height=None):
    """获取颜色对话框样式 - 彩虹糖果风格"""
    if not screen_width or not screen_height:
        screen_width, screen_height = get_screen_size()

    dialog_radius = int(screen_height * 0.012)
    button_radius = int(screen_height * 0.006)
    font_size = max(12, min(16, int(screen_width * 0.005)))

    return f"""
        QColorDialog {{
            background-color: {THEME_BG};
            color: {THEME_TEXT};
            border-radius: {dialog_radius}px;
        }}
        QColorDialog QLabel {{
            color: {THEME_TEXT};
            font-family: "Microsoft YaHei";
        }}
        QColorDialog QPushButton {{
            background-color: {THEME_PRIMARY};
            color: white;
            border: none;
            border-radius: {button_radius}px;
            padding: 8px 16px;
            font-weight: 500;
            font-family: "Microsoft YaHei";
            font-size: {font_size}px;
        }}
        QColorDialog QPushButton:hover {{
            background-color: {THEME_SECONDARY};
        }}
        QColorDialog QPushButton:pressed {{
            background-color: #e55a5a;
        }}
    """
