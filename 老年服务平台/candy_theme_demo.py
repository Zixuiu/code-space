import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLineEdit, QCheckBox,
                             QFrame, QLabel, QTabWidget, QGroupBox, QRadioButton,
                             QScrollArea)
from PyQt5.QtCore import Qt


class CandyThemeUI:
    PRIMARY_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6B6B, stop:1 #4ECDC4)"
    SECONDARY = "#FFE66D"
    ACCENT = "#FF6B6B"
    BG = "#FFFFFF"
    CARD = "#FFF9F9"
    TEXT = "#2C3E50"
    MUTED = "#636E72"
    BORDER = "#DFE6E9"

    def get_primary_btn_style(self):
        return f"""
            QPushButton {{
                background: {self.PRIMARY_GRADIENT};
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 28px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                font-size: 22px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFE66D, stop:1 #FF6B6B);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e55a5a, stop:1 #FF6B6B);
            }}
        """

    def get_secondary_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {self.SECONDARY};
                color: {self.TEXT};
                border: none;
                border-radius: 25px;
                padding: 12px 28px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                font-size: 22px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.ACCENT};
                color: white;
            }}
        """

    def get_input_style(self):
        return f"""
            QLineEdit {{
                background-color: {self.BG};
                color: {self.TEXT};
                border: 2px solid {self.BORDER};
                border-radius: 999px;
                padding: 14px 20px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                font-size: 24px;
            }}
            QLineEdit:focus {{
                border-color: {self.ACCENT};
            }}
            QLineEdit::placeholder {{
                color: {self.MUTED};
            }}
        """

    def get_checkbox_style(self):
        return f"""
            QCheckBox {{
                color: {self.TEXT};
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 24px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid {self.BORDER};
                background: {self.BG};
            }}
            QCheckBox::indicator:checked {{
                background: {self.ACCENT};
                border-color: {self.ACCENT};
            }}
        """

    def get_radio_style(self):
        return f"""
            QRadioButton {{
                color: {self.TEXT};
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 24px;
            }}
            QRadioButton::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid {self.BORDER};
                background: {self.BG};
            }}
            QRadioButton::indicator:checked {{
                background: {self.ACCENT};
                border-color: {self.ACCENT};
            }}
        """

    def get_card_style(self):
        return f"""
            QFrame {{
                background-color: {self.CARD};
                border: 1px solid {self.BORDER};
                border-radius: 25px;
            }}
        """

    def get_tab_style(self):
        return f"""
            QTabWidget::pane {{
                border: 1px solid {self.BORDER};
                background-color: {self.BG};
                border-radius: 25px;
            }}
            QTabBar::tab {{
                background: {self.CARD};
                border: 1px solid {self.BORDER};
                padding: 10px 20px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                color: {self.MUTED};
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }}
            QTabBar::tab:selected {{
                background: {self.PRIMARY_GRADIENT};
                color: white;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }}
            QTabBar::tab:hover:!selected {{
                background: {self.CARD};
                color: {self.ACCENT};
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }}
        """

    def get_title_frame_style(self):
        return f"""
            QFrame {{
                background: {self.PRIMARY_GRADIENT};
                border-radius: 25px;
                padding: 25px;
            }}
        """


class MainWindow(QMainWindow, CandyThemeUI):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎀 老年服务平台 - 糖果主题")
        self.setMinimumSize(900, 700)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_frame = QFrame()
        title_frame.setStyleSheet(self.get_title_frame_style())
        title_layout = QVBoxLayout(title_frame)
        title_label = QLabel("🌸 欢迎使用老年服务平台")
        title_label.setStyleSheet("color: white; font-size: 38px; font-weight: bold; font-family: 'Microsoft YaHei UI', sans-serif;")
        title_layout.addWidget(title_label, alignment=Qt.AlignCenter)
        main_layout.addWidget(title_frame)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(self.get_tab_style())
        main_layout.addWidget(self.tabs)

        self.tabs.addTab(self.create_home_tab(), "🏠 首页")
        self.tabs.addTab(self.create_form_tab(), "📝 表单")
        self.tabs.addTab(self.create_cards_tab(), "🎴 卡片")

        color_bar = self.create_color_bar()
        main_layout.addWidget(color_bar)

    def create_home_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        welcome_card = QFrame()
        welcome_card.setStyleSheet(self.get_card_style())
        welcome_layout = QVBoxLayout(welcome_card)
        welcome_label = QLabel("✨ 今日问候")
        welcome_label.setStyleSheet("color: #2C3E50; font-size: 28px; font-weight: bold; font-family: 'Microsoft YaHei UI', sans-serif;")
        welcome_desc = QLabel("亲爱的用户，愿您今天心情愉快，健康如意！")
        welcome_desc.setStyleSheet("color: #636E72; font-size: 22px; font-family: 'Microsoft YaHei UI', sans-serif;")
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addWidget(welcome_desc)
        layout.addWidget(welcome_card)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn1 = QPushButton("🌺 开始使用")
        btn1.setStyleSheet(self.get_primary_btn_style())
        btn1.setMinimumHeight(50)
        btn2 = QPushButton("🌻 了解更多")
        btn2.setStyleSheet(self.get_secondary_btn_style())
        btn2.setMinimumHeight(50)
        btn_layout.addWidget(btn1)
        btn_layout.addWidget(btn2)
        layout.addLayout(btn_layout)

        layout.addStretch()
        return widget

    def create_form_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        group = QGroupBox("📋 个人信息")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 26px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI', sans-serif;
                color: #2C3E50;
                border: 1px solid #DFE6E9;
                border-radius: 25px;
                margin-top: 20px;
                padding: 20px;
                background-color: #FFF9F9;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 5px 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6B6B, stop:1 #4ECDC4);
                color: white;
                border-radius: 15px;
            }}
        """)

        form_layout = QVBoxLayout(group)
        form_layout.setSpacing(15)

        name_layout = QHBoxLayout()
        name_label = QLabel("姓名:")
        name_label.setStyleSheet("font-size: 24px; font-family: 'Microsoft YaHei UI', sans-serif; color: #2C3E50;")
        name_input = QLineEdit()
        name_input.setPlaceholderText("请输入姓名")
        name_input.setStyleSheet(self.get_input_style())
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        form_layout.addLayout(name_layout)

        phone_layout = QHBoxLayout()
        phone_label = QLabel("电话:")
        phone_label.setStyleSheet("font-size: 24px; font-family: 'Microsoft YaHei UI', sans-serif; color: #2C3E50;")
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("请输入电话号码")
        phone_input.setStyleSheet(self.get_input_style())
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(phone_input)
        form_layout.addLayout(phone_layout)

        checkbox_layout = QHBoxLayout()
        checkbox1 = QCheckBox("我同意服务条款")
        checkbox1.setStyleSheet(self.get_checkbox_style())
        checkbox2 = QCheckBox("订阅每日资讯")
        checkbox2.setStyleSheet(self.get_checkbox_style())
        checkbox_layout.addWidget(checkbox1)
        checkbox_layout.addWidget(checkbox2)
        form_layout.addLayout(checkbox_layout)

        radio_layout = QHBoxLayout()
        radio1 = QRadioButton("男")
        radio1.setStyleSheet(self.get_radio_style())
        radio2 = QRadioButton("女")
        radio2.setStyleSheet(self.get_radio_style())
        radio_layout.addWidget(radio1)
        radio_layout.addWidget(radio2)
        form_layout.addLayout(radio_layout)

        submit_btn = QPushButton("🌸 提交")
        submit_btn.setStyleSheet(self.get_primary_btn_style())
        submit_btn.setMinimumHeight(50)
        form_layout.addWidget(submit_btn)

        layout.addWidget(group)
        layout.addStretch()
        return widget

    def create_cards_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        cards_data = [
            ("🏥 健康管理", "实时监测您的健康数据，提供专业建议"),
            ("🍎 营养膳食", "科学搭配每日饮食，保障营养均衡"),
            ("🧘 运动健身", "定制个性化运动方案，保持活力"),
            ("👥 社交活动", "参与社区活动，享受欢乐时光"),
            ("📞 紧急求助", "一键呼叫，全天候守护您的安全"),
        ]

        for title, desc in cards_data:
            card = QFrame()
            card.setStyleSheet(self.get_card_style())
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)

            card_title = QLabel(title)
            card_title.setStyleSheet("color: #2C3E50; font-size: 28px; font-weight: bold; font-family: 'Microsoft YaHei UI', sans-serif;")
            card_desc = QLabel(desc)
            card_desc.setStyleSheet("color: #636E72; font-size: 22px; font-family: 'Microsoft YaHei UI', sans-serif;")

            card_layout.addWidget(card_title)
            card_layout.addWidget(card_desc)

            btn = QPushButton("进入")
            btn.setStyleSheet(self.get_secondary_btn_style())
            btn.setMinimumHeight(40)
            card_layout.addWidget(btn)

            layout.addWidget(card)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(widget)
        main_layout.addWidget(scroll)
        return widget

    def create_color_bar(self):
        bar = QFrame()
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.BG};
                border: 1px solid {self.BORDER};
                border-radius: 20px;
                padding: 15px;
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setSpacing(10)

        colors = [
            ("Primary Gradient", "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6B6B, stop:1 #4ECDC4)"),
            ("Secondary", self.SECONDARY),
            ("Accent", self.ACCENT),
            ("Card", self.CARD),
            ("Border", self.BORDER),
        ]

        for name, color in colors:
            swatch = QFrame()
            swatch.setStyleSheet(f"""
                QFrame {{
                    background: {color};
                    border-radius: 4px;
                    min-width: 40px;
                    min-height: 25px;
                }}
            """)
            label = QLabel(name)
            label.setStyleSheet("font-size: 12px; color: #636E72; font-family: 'Microsoft YaHei UI', sans-serif;")
            layout.addWidget(swatch)
            layout.addWidget(label)

        layout.addStretch()
        return bar


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())