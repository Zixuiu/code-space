"""
UI配色方案预览器 - 20套主题可视化预览
在应用中添加一个预览窗口，让用户直观选择喜欢的配色方案
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QScrollArea, QWidget, QFrame,
                             QLineEdit, QSlider, QCheckBox, QComboBox, QTabWidget)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPalette, QColor

class ColorSchemePreview(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 UI配色方案预览 - 选择你喜欢的风格")
        self.setMinimumSize(1200, 800)
        self.scheme = None

        self.schemes = self.get_all_schemes()
        self.init_ui()

    def get_all_schemes(self):
        return [
            {"id": 1, "name": "深海科技蓝", "scene": "深夜开发/极客风格",
             "primary": "#0066FF", "secondary": "#00D4FF", "accent": "#FF3366",
             "bg": "#0A1628", "card": "#162236", "text": "#E8F4FF", "muted": "#8BA4C7", "border": "#2A4A6B"},
            {"id": 2, "name": "极光绿野", "scene": "清新自然/环保主题",
             "primary": "#00C853", "secondary": "#69F0AE", "accent": "#FFD600",
             "bg": "#F5F5F5", "card": "#FFFFFF", "text": "#1B5E20", "muted": "#74C69D", "border": "#C8E6C9"},
            {"id": 3, "name": "烈焰火山", "scene": "能量热力/游戏辅助",
             "primary": "#FF5722", "secondary": "#FF8A65", "accent": "#FFEB3B",
             "bg": "#1A1A1A", "card": "#2D2D2D", "text": "#FFFFFF", "muted": "#9E9E9E", "border": "#424242"},
            {"id": 4, "name": "樱花和风", "scene": "女性用户/日系风格",
             "primary": "#E91E63", "secondary": "#F48FB1", "accent": "#00BCD4",
             "bg": "#FFF0F5", "card": "#FFFFFF", "text": "#880E4F", "muted": "#C2185B", "border": "#F8BBD9"},
            {"id": 5, "name": "赛博朋克", "scene": "科技极客/编程工具",
             "primary": "#00FFFF", "secondary": "#FF00FF", "accent": "#FFFF00",
             "bg": "#0D0D0D", "card": "#1A1A2E", "text": "#FFFFFF", "muted": "#B0B0B0", "border": "#6C63FF"},
            {"id": 6, "name": "薄荷清凉", "scene": "清爽夏日/效率工具",
             "primary": "#00BFA5", "secondary": "#64FFDA", "accent": "#FF6E40",
             "bg": "#E0F2F1", "card": "#FFFFFF", "text": "#004D40", "muted": "#26A69A", "border": "#B2DFDB"},
            {"id": 7, "name": "暗夜贵族", "scene": "高端VIP/特权感",
             "primary": "#9C27B0", "secondary": "#BA68C8", "accent": "#FFD700",
             "bg": "#1A1A1A", "card": "#2D2D2D", "text": "#E1BEE7", "muted": "#CE93D8", "border": "#4A148C"},
            {"id": 8, "name": "极地冰晶", "scene": "寒冷地区/冬季主题",
             "primary": "#2196F3", "secondary": "#90CAF9", "accent": "#FF4081",
             "bg": "#ECEFF1", "card": "#FFFFFF", "text": "#0D47A1", "muted": "#64B5F6", "border": "#BBDEFB"},
            {"id": 9, "name": "琥珀暖阳", "scene": "温馨家居/生活记录",
             "primary": "#FF8F00", "secondary": "#FFB300", "accent": "#795548",
             "bg": "#FFF8E1", "card": "#FFFFFF", "text": "#E65100", "muted": "#FFA000", "border": "#FFE082"},
            {"id": 10, "name": "翡翠玉石", "scene": "收藏鉴赏/高雅品味",
             "primary": "#009688", "secondary": "#4DB6AC", "accent": "#FFAB91",
             "bg": "#E0F2F1", "card": "#FAFAFA", "text": "#00695C", "muted": "#26A69A", "border": "#80CBC4"},
            {"id": 11, "name": "烈焰红黑", "scene": "紧急警示/危险操作",
             "primary": "#D32F2F", "secondary": "#EF5350", "accent": "#212121",
             "bg": "#1A1A1A", "card": "#2D2D2D", "text": "#FFCDD2", "muted": "#EF9A9A", "border": "#B71C1C"},
            {"id": 12, "name": "蒂芙尼蓝", "scene": "珠宝奢侈/婚礼记录",
             "primary": "#4DB6AC", "secondary": "#80CBC4", "accent": "#FFD54F",
             "bg": "#E0F7FA", "card": "#FFFFFF", "text": "#00695C", "muted": "#4DB6AC", "border": "#B2DFDB"},
            {"id": 13, "name": "森林探险", "scene": "户外旅行/自然主题",
             "primary": "#558B2F", "secondary": "#8BC34A", "accent": "#FFA000",
             "bg": "#F1F8E9", "card": "#FFFFFF", "text": "#33691E", "muted": "#689F38", "border": "#C5E1A5"},
            {"id": 14, "name": "极简黑白", "scene": "Apple风格/设计师工具",
             "primary": "#000000", "secondary": "#424242", "accent": "#FF3B30",
             "bg": "#FFFFFF", "card": "#F5F5F7", "text": "#1D1D1F", "muted": "#86868B", "border": "#D2D2D7"},
            {"id": 15, "name": "彩虹糖果", "scene": "儿童教育/趣味工具",
             "primary": "#FF6B6B", "secondary": "#4ECDC4", "accent": "#FFE66D",
             "bg": "#FFFFFF", "card": "#FFF9F9", "text": "#2C3E50", "muted": "#636E72", "border": "#DFE6E9"},
            {"id": 16, "name": "紫罗兰之夜", "scene": "夜间使用/创意设计",
             "primary": "#7C4DFF", "secondary": "#B388FF", "accent": "#00E5FF",
             "bg": "#1A1A2E", "card": "#252542", "text": "#E1BEE7", "muted": "#B39DDB", "border": "#651FFF"},
            {"id": 17, "name": "玫瑰金", "scene": "女性时尚/美妆购物",
             "primary": "#E91E63", "secondary": "#F48FB1", "accent": "#FFD700",
             "bg": "#FFF5F7", "card": "#FFFFFF", "text": "#880E4F", "muted": "#C2185B", "border": "#F8BBD0"},
            {"id": 18, "name": "军事迷彩", "scene": "军事游戏/战术工具",
             "primary": "#556B2F", "secondary": "#8FBC8F", "accent": "#CD853F",
             "bg": "#2F2F2F", "card": "#3D3D3D", "text": "#E8E8E8", "muted": "#A9BA9D", "border": "#4A5D23"},
            {"id": 19, "name": "马卡龙甜品", "scene": "烘焙记录/美食主题",
             "primary": "#81D4FA", "secondary": "#F8BBD9", "accent": "#A5D6A7",
             "bg": "#FFFDE7", "card": "#FFFFFF", "text": "#5D4037", "muted": "#8D6E63", "border": "#FFE0B2"},
            {"id": 20, "name": "深空宇宙", "scene": "太空科幻/天文爱好",
             "primary": "#3F51B5", "secondary": "#7986CB", "accent": "#FF4081",
             "bg": "#0D1137", "card": "#1A1A3E", "text": "#C5CAE9", "muted": "#9FA8DA", "border": "#303F9F"},
        ]

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("🎨 点击下方卡片选择你喜欢的UI配色方案")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(20)

        for i, scheme in enumerate(self.schemes):
            row = i // 4
            col = i % 4
            card = self.create_scheme_card(scheme)
            grid.addWidget(card, row, col)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.confirm_btn = QPushButton("应用所选方案")
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)

    def create_scheme_card(self, scheme):
        card = QFrame()
        card.setFixedSize(270, 320)
        card.setCursor(Qt.PointingHandCursor)
        card.scheme = scheme

        def get_text_color(bg_hex):
            hex_v = bg_hex.lstrip('#')
            r, g, b = int(hex_v[0:2], 16), int(hex_v[2:4], 16), int(hex_v[4:6], 16)
            return "#1D1D1F" if (r*299 + g*587 + b*114) / 1000 > 128 else "#FFFFFF"

        def safe_get(key, fallback):
            return scheme.get(key, fallback)

        primary = safe_get("primary", "#1890ff")
        secondary = safe_get("secondary", "#40a9ff")
        accent = safe_get("accent", "#ff5722")
        bg = safe_get("bg", "#ffffff")
        card_bg = safe_get("card", "#ffffff")
        text = safe_get("text", "#262626")
        muted = safe_get("muted", "#8c8c8c")
        border = safe_get("border", "#d9d9d9")

        card.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 2px solid {border};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 2px solid {primary};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QFrame()
        header.setStyleSheet(f"background-color: {bg}; border-radius: 8px;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)

        num_label = QLabel(f"方案 {scheme['id']}")
        num_label.setFont(QFont("Microsoft YaHei", 9))
        num_label.setStyleSheet(f"color: {muted}; background: transparent;")
        header_layout.addWidget(num_label)

        name_label = QLabel(scheme['name'])
        name_label.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        name_label.setStyleSheet(f"color: {text}; background: transparent;")
        header_layout.addWidget(name_label)

        scene_label = QLabel(scheme['scene'])
        scene_label.setFont(QFont("Microsoft YaHei", 8))
        scene_label.setStyleSheet(f"color: {muted}; background: transparent;")
        header_layout.addWidget(scene_label)
        layout.addWidget(header)

        record_btn = QPushButton("⏺")
        record_btn.setFixedSize(50, 50)
        record_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary};
                color: {get_text_color(primary)};
                border: none;
                border-radius: 25px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {secondary};
            }}
        """)
        record_btn_layout = QHBoxLayout()
        record_btn_layout.addStretch()
        record_btn_layout.addWidget(record_btn)
        record_btn_layout.addStretch()
        layout.addLayout(record_btn_layout)

        labels_layout = QHBoxLayout()
        labels_layout.addStretch()
        for color, text_c in [(primary, get_text_color(primary)), (secondary, get_text_color(secondary)), (accent, "#ffffff")]:
            lbl = QLabel("标签")
            lbl.setFixedHeight(20)
            lbl.setStyleSheet(f"background-color: {color}; color: {text_c}; border-radius: 10px; padding: 0 8px; font-size: 10px;")
            labels_layout.addWidget(lbl)
        labels_layout.addStretch()
        layout.addLayout(labels_layout)

        input_field = QLineEdit()
        input_field.setPlaceholderText("输入框...")
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg};
                color: {text};
                border: 2px solid {border};
                border-radius: 6px;
                padding: 6px;
            }}
            QLineEdit:focus {{
                border-color: {primary};
            }}
        """)
        layout.addWidget(input_field)

        slider = QSlider(Qt.Horizontal)
        slider.setValue(60)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {border};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {primary};
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {primary};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(slider)

        check_layout = QHBoxLayout()
        check_layout.addStretch()
        cb = QCheckBox("选项")
        cb.setChecked(True)
        cb.setStyleSheet(f"""
            QCheckBox {{
                color: {text};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {border};
                background: {bg};
            }}
            QCheckBox::indicator:checked {{
                background: {primary};
                border-color: {primary};
            }}
        """)
        check_layout.addWidget(cb)
        check_layout.addStretch()
        layout.addLayout(check_layout)

        btns_layout = QHBoxLayout()
        btns_layout.addStretch()
        for color, tc in [(primary, get_text_color(primary)), (secondary, get_text_color(secondary))]:
            btn = QPushButton("按钮")
            btn.setFixedSize(60, 28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: {tc};
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
            """)
            btns_layout.addWidget(btn)
        btns_layout.addStretch()
        layout.addLayout(btns_layout)

        swatches_layout = QHBoxLayout()
        swatches_layout.addStretch()
        for color in [primary, secondary, accent, bg, card_bg, border]:
            swatch = QFrame()
            swatch.setFixedSize(24, 24)
            swatch.setStyleSheet(f"background-color: {color}; border-radius: 4px; border: 1px solid #ccc;")
            swatches_layout.addWidget(swatch)
        swatches_layout.addStretch()
        layout.addLayout(swatches_layout)

        card.mousePressEvent = lambda e, s=scheme: self.select_scheme(s, card)

        return card

    def select_scheme(self, scheme, card):
        for i in range(self.tab_widget.count() if hasattr(self, 'tab_widget') else 0):
            self.tab_widget.removeTab(0)

        self.scheme = scheme
        self.selected_card = card
        self.accept()

    def get_selected_scheme(self):
        return self.scheme


def show_color_scheme_preview(parent=None):
    dialog = ColorSchemePreview(parent)
    if dialog.exec_() == QDialog.Accepted and dialog.get_selected_scheme():
        return dialog.get_selected_scheme()
    return None


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    scheme = show_color_scheme_preview()
    if scheme:
        print(f"选择了: {scheme['name']}")
        print(f"主色: {scheme['primary']}")
    sys.exit(app.exec_())
