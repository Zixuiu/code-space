"""
彩虹糖果主题（方案15）示例界面
展示完整的彩虹糖果主题UI效果
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox, QRadioButton,
    QTabWidget, QFrame, QGridLayout, QComboBox, QSlider, QProgressBar,
    QGroupBox, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt


class CandyThemePreview(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 彩虹糖果主题（方案15）预览")
        self.setMinimumSize(900, 700)

        # 彩虹糖果主题颜色
        self.PRIMARY_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6B6B, stop:1 #4ECDC4)"
        self.SECONDARY = "#FFE66D"
        self.ACCENT = "#FF6B6B"
        self.BG = "#FFFFFF"
        self.CARD = "#FFF9F9"
        self.TEXT = "#2C3E50"
        self.MUTED = "#636E72"
        self.BORDER = "#DFE6E9"

        self.init_ui()

    def get_primary_btn_style(self):
        return f"""
            QPushButton {{
                background: {self.PRIMARY_GRADIENT};
                color: white;
                border: none;
                border-radius: 25px;
                padding: 8px 24px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                font-size: 18px;
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
                padding: 8px 24px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                font-size: 18px;
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
                font-size: 20px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {self.BORDER};
                background: {self.BG};
            }}
            QCheckBox::indicator:checked {{
                background: {self.ACCENT};
                border-color: {self.ACCENT};
            }}
        """

    def get_card_style(self):
        return f"""
            QFrame {{
                background-color: {self.CARD};
                border: 1px solid {self.BORDER};
                border-radius: 999px;
            }}
        """

    def get_tab_style(self):
        return f"""
            QTabWidget::pane {{
                border: 1px solid {self.BORDER};
                background-color: {self.BG};
                border-radius: 999px;
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

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题栏
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.PRIMARY_GRADIENT};
                border-radius: 999px;
                padding: 25px;
            }}
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("🎨 彩虹糖果主题预览")
        title_label.setStyleSheet("color: white; font-size: 38px; font-weight: bold; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent; letter-spacing: 2px;")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("方案15 - 年轻时尚，渐变彩色系")
        subtitle_label.setStyleSheet("color: rgba(255,255,255,0.95); font-size: 22px; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent; letter-spacing: 1px;")
        subtitle_label.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        main_layout.addWidget(title_frame)

        # 创建Tab
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(self.get_tab_style())

        # Tab 1: 按钮展示
        self.tabs.addTab(self.create_buttons_tab(), "按钮")
        # Tab 2: 输入控件
        self.tabs.addTab(self.create_inputs_tab(), "输入")
        # Tab 3: 列表卡片
        self.tabs.addTab(self.create_cards_tab(), "卡片")

        main_layout.addWidget(self.tabs)

        # 底部颜色示样
        color_bar = self.create_color_bar()
        main_layout.addWidget(color_bar)

    def create_buttons_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # 主要按钮组
        group1 = QGroupBox("主要按钮（粉红→薄荷绿渐变）")
        group1.setStyleSheet(f"QGroupBox {{ color: {self.TEXT}; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 26px; font-weight: bold; padding-top: 15px; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; }}")
        btn_layout = QHBoxLayout()

        btn1 = QPushButton("主要按钮")
        btn1.setStyleSheet(self.get_primary_btn_style())
        btn1.setFixedHeight(50)

        btn2 = QPushButton("次要按钮")
        btn2.setStyleSheet(self.get_secondary_btn_style())
        btn2.setFixedHeight(50)

        btn3 = QPushButton("禁用按钮")
        btn3.setEnabled(False)
        btn3.setStyleSheet(self.get_primary_btn_style())
        btn3.setFixedHeight(50)

        btn_layout.addWidget(btn1)
        btn_layout.addWidget(btn2)
        btn_layout.addWidget(btn3)
        btn_layout.addStretch()
        group1.setLayout(btn_layout)
        layout.addWidget(group1)

        # 按钮尺寸
        group2 = QGroupBox("不同尺寸")
        group2.setStyleSheet(f"QGroupBox {{ color: {self.TEXT}; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 26px; font-weight: bold; padding-top: 15px; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; }}")
        size_layout = QHBoxLayout()

        small_btn = QPushButton("小按钮")
        small_btn.setStyleSheet(self.get_primary_btn_style())
        small_btn.setFixedSize(100, 50)

        medium_btn = QPushButton("中按钮")
        medium_btn.setStyleSheet(self.get_primary_btn_style())
        medium_btn.setFixedSize(150, 50)

        large_btn = QPushButton("大按钮")
        large_btn.setStyleSheet(self.get_primary_btn_style())
        large_btn.setFixedSize(200, 50)

        size_layout.addWidget(small_btn)
        size_layout.addWidget(medium_btn)
        size_layout.addWidget(large_btn)
        size_layout.addStretch()
        group2.setLayout(size_layout)
        layout.addWidget(group2)

        # 圆角按钮
        group3 = QGroupBox("圆角与椭圆")
        group3.setStyleSheet(f"QGroupBox {{ color: {self.TEXT}; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 26px; font-weight: bold; padding-top: 15px; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; }}")
        round_layout = QHBoxLayout()

        round_btn = QPushButton("圆角按钮")
        round_btn.setStyleSheet(self.get_primary_btn_style())
        round_btn.setFixedSize(150, 50)

        pill_btn = QPushButton("椭圆按钮")
        pill_btn.setStyleSheet(self.get_primary_btn_style())
        pill_btn.setFixedSize(150, 50)

        round_layout.addWidget(round_btn)
        round_layout.addWidget(pill_btn)
        round_layout.addStretch()
        group3.setLayout(round_layout)
        layout.addWidget(group3)

        layout.addStretch()
        return widget

    def create_inputs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # 输入框
        group1 = QGroupBox("输入框")
        group1.setStyleSheet(f"QGroupBox {{ color: {self.TEXT}; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 26px; font-weight: bold; padding-top: 15px; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; }}")
        input_layout = QVBoxLayout()

        line_edit1 = QLineEdit()
        line_edit1.setPlaceholderText("普通输入框...")
        line_edit1.setStyleSheet(self.get_input_style())

        line_edit2 = QLineEdit()
        line_edit2.setPlaceholderText("带内容的输入框")
        line_edit2.setText("示例文字")
        line_edit2.setStyleSheet(self.get_input_style())

        input_layout.addWidget(line_edit1)
        input_layout.addWidget(line_edit2)
        group1.setLayout(input_layout)
        layout.addWidget(group1)

        # 复选框和单选框
        group2 = QGroupBox("选择控件")
        group2.setStyleSheet(f"QGroupBox {{ color: {self.TEXT}; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 26px; font-weight: bold; padding-top: 15px; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; }}")
        check_layout = QVBoxLayout()

        cb1 = QCheckBox("复选框选项 1")
        cb1.setChecked(True)
        cb1.setStyleSheet(self.get_checkbox_style())

        cb2 = QCheckBox("复选框选项 2")
        cb2.setStyleSheet(self.get_checkbox_style())

        rb1 = QRadioButton("单选项 A")
        rb1.setStyleSheet(f"color: {self.TEXT}; font-size: 20px; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;")

        rb2 = QRadioButton("单选项 B")
        rb2.setStyleSheet(f"color: {self.TEXT}; font-size: 20px; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;")

        check_layout.addWidget(cb1)
        check_layout.addWidget(cb2)
        check_layout.addWidget(rb1)
        check_layout.addWidget(rb2)
        group2.setLayout(check_layout)
        layout.addWidget(group2)

        # 进度条
        group3 = QGroupBox("进度条")
        group3.setStyleSheet(f"QGroupBox {{ color: {self.TEXT}; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 26px; font-weight: bold; padding-top: 15px; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; }}")
        progress_layout = QVBoxLayout()

        progress = QProgressBar()
        progress.setValue(60)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background: {self.BORDER};
                border-radius: 6px;
                height: 12px;
            }}
            QProgressBar::chunk {{
                background: {self.PRIMARY_GRADIENT};
                border-radius: 6px;
            }}
        """)

        slider = QSlider(Qt.Horizontal)
        slider.setValue(40)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {self.BORDER};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {self.ACCENT};
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.PRIMARY_GRADIENT};
                border-radius: 3px;
            }}
        """)

        progress_layout.addWidget(progress)
        progress_layout.addWidget(slider)
        group3.setLayout(progress_layout)
        layout.addWidget(group3)

        layout.addStretch()
        return widget

    def create_cards_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(20)

        # 卡片1
        card1 = QFrame()
        card1.setStyleSheet(self.get_card_style())
        card1_layout = QVBoxLayout(card1)
        card1_layout.setContentsMargins(15, 15, 15, 15)

        card1_title = QLabel(" 功能卡片 1")
        card1_title.setStyleSheet(f"color: {self.TEXT}; font-size: 28px; font-weight: bold; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent; padding: 10px 0;")

        card1_desc = QLabel("这是彩虹糖果主题的功能卡片展示，可以放置任何内容。")
        card1_desc.setStyleSheet(f"color: {self.MUTED}; font-size: 22px; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent; padding: 10px 0; line-height: 1.5;")

        card1_btn = QPushButton("查看详情")
        card1_btn.setStyleSheet(self.get_primary_btn_style())
        card1_btn.setFixedSize(180, 50)

        # 按钮容器，让按钮居中
        btn_container1 = QWidget()
        btn_layout1 = QHBoxLayout(btn_container1)
        btn_layout1.setContentsMargins(0, 0, 0, 0)
        btn_layout1.addStretch()
        btn_layout1.addWidget(card1_btn)
        btn_layout1.addStretch()

        card1_layout.addWidget(card1_title)
        card1_layout.addWidget(card1_desc)
        card1_layout.addWidget(btn_container1)

        # 卡片2
        card2 = QFrame()
        card2.setStyleSheet(self.get_card_style())
        card2_layout = QVBoxLayout(card2)
        card2_layout.setContentsMargins(15, 15, 15, 15)

        card2_title = QLabel(" 游戏卡片")
        card2_title.setStyleSheet(f"color: {self.TEXT}; font-size: 28px; font-weight: bold; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent; padding: 10px 0;")

        card2_desc = QLabel("彩虹糖果主题适合游戏和趣味工具界面。")
        card2_desc.setStyleSheet(f"color: {self.MUTED}; font-size: 22px; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent; padding: 10px 0; line-height: 1.5;")

        card2_btn = QPushButton("开始游戏")
        card2_btn.setStyleSheet(self.get_secondary_btn_style())
        card2_btn.setFixedSize(180, 50)

        # 按钮容器，让按钮居中
        btn_container2 = QWidget()
        btn_layout2 = QHBoxLayout(btn_container2)
        btn_layout2.setContentsMargins(0, 0, 0, 0)
        btn_layout2.addStretch()
        btn_layout2.addWidget(card2_btn)
        btn_layout2.addStretch()

        card2_layout.addWidget(card2_title)
        card2_layout.addWidget(card2_desc)
        card2_layout.addWidget(btn_container2)

        # 卡片3
        card3 = QFrame()
        card3.setStyleSheet(self.get_card_style())
        card3_layout = QVBoxLayout(card3)
        card3_layout.setContentsMargins(15, 15, 15, 15)

        card3_title = QLabel(" 教育卡片")
        card3_title.setStyleSheet(f"color: {self.TEXT}; font-size: 28px; font-weight: bold; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent; padding: 10px 0;")

        card3_desc = QLabel("儿童教育工具的理想选择，色彩活泼。")
        card3_desc.setStyleSheet(f"color: {self.MUTED}; font-size: 22px; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent; padding: 10px 0; line-height: 1.5;")

        card3_btn = QPushButton("了解更多")
        card3_btn.setStyleSheet(self.get_primary_btn_style())
        card3_btn.setFixedSize(180, 50)

        # 按钮容器，让按钮居中
        btn_container3 = QWidget()
        btn_layout3 = QHBoxLayout(btn_container3)
        btn_layout3.setContentsMargins(0, 0, 0, 0)
        btn_layout3.addStretch()
        btn_layout3.addWidget(card3_btn)
        btn_layout3.addStretch()

        card3_layout.addWidget(card3_title)
        card3_layout.addWidget(card3_desc)
        card3_layout.addWidget(btn_container3)

        layout.addWidget(card1, 0, 0)
        layout.addWidget(card2, 0, 1)
        layout.addWidget(card3, 1, 0)

        return widget

    def create_color_bar(self):
        frame = QFrame()
        frame.setStyleSheet(self.get_card_style())
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)

        label = QLabel("配色示样：")
        label.setStyleSheet(f"color: {self.TEXT}; font-weight: bold; font-size: 20px; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent;")

        colors = [
            ("#FF6B6B", "主色"),
            ("#4ECDC4", "辅色"),
            ("#FFE66D", "次色"),
            ("#FFFFFF", "背景"),
            ("#FFF9F9", "卡片"),
            ("#2C3E50", "文字"),
            ("#636E72", "次要"),
            ("#DFE6E9", "边框"),
        ]

        for color, name in colors:
            swatch = QFrame()
            swatch.setFixedSize(40, 25)
            swatch.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc; border-radius: 4px;")

            color_label = QLabel(name)
            color_label.setStyleSheet(f"color: {self.MUTED}; font-size: 20px; font-weight: bold; font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; background: transparent;")

            layout.addWidget(swatch)
            layout.addWidget(color_label)

        layout.addStretch()
        return frame


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CandyThemePreview()
    window.show()
    sys.exit(app.exec_())
