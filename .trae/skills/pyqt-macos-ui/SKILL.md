---
name: "pyqt-macos-ui"
description: "Generates a complete macOS/iOS-style PyQt5 desktop application with sidebar, toolbar, and 5-page content area. Invoke when user wants to create a PyQt5 GUI application with Apple design language."
---

# PyQt5 macOS Style Desktop Application

Creates a complete macOS-style desktop application using PyQt5. The application features an Apple design language with sidebar navigation, toolbar with window controls, multi-page content area, and elegant card-based UI components.

## When to Use

Invoke this skill when:
- User asks to create a PyQt5/PySide desktop application with macOS/iOS design
- User wants a modern Apple-style GUI in Python
- User needs a desktop app template with multiple pages, navigation, and styled components
- User wants a professional-looking PyQt5 application with sidebar, toolbar, cards, and animations

## Architecture

```
┌──────────────────────────────────────────────────┐
│  MacOSToolbar (52px, window controls + title)    │
├────────┬─────────────────────────────────────────┤
│        │                                         │
│ MacOS  │   QStackedWidget (5 pages)             │
│ Sidebar│   ┌─────────────────────────────────┐   │
│ (260px)│   │ 1. DashboardPage               │   │
│        │   │ 2. FileManagerPage             │   │
│ ────── │   │ 3. SearchPage                  │   │
│ 用户   │   │ 4. MessagesPage                │   │
│ 信息   │   │ 5. SettingsPage                │   │
│        │   └─────────────────────────────────┘   │
└────────┴─────────────────────────────────────────┘
```

## Components

| Component | Description |
|-----------|-------------|
| `MacOSColors` | iOS/macOS system color palette (Accent, Green, Red, Orange, Purple, etc.) |
| `MacOSSidebarItem` | Clickable sidebar navigation item with selection state |
| `MacOSSidebar` | Left sidebar with nav items + user info card at bottom |
| `MacOSCard` | Rounded card with subtle shadow effect (custom paintEvent) |
| `MacOSButton` | Solid color button with hover/press states |
| `MacOSSecondaryButton` | Outlined button with border |
| `MacOSToolbar` | Top bar with macOS window controls (red/yellow/green) + title + search |
| `DashboardPage` | Welcome greeting, stat cards, recent activity list, quick actions |
| `FileManagerPage` | File table with name/size/type/date/actions columns |
| `SearchPage` | Search bar, tags, result cards |
| `MessagesPage` | Message list with unread badges |
| `SettingsPage` | Grouped settings (checkboxes, combos, sliders) |

## Usage

```python
python ios_desktop_app.py
```

## Key Features

- **High DPI Support**: `AA_EnableHighDpiScaling` + `AA_UseHighDpiPixmaps`
- **Page Transitions**: Fade animation (250ms, OutCubic easing) using `QGraphicsOpacityEffect`
- **Card Rendering**: Custom `paintEvent` avoids `QGraphicsDropShadowEffect` painter conflicts
- **Emoji Icons**: Cross-platform compatible icons (no platform-specific font dependency)
- **Custom Scrollbars**: Slim macOS-style scrollbar styling
- **Font**: Microsoft YaHei UI with antialiasing

## Complete Source Code

```python
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QScrollArea, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect, QLineEdit, QGridLayout,
    QGraphicsOpacityEffect, QSplitter, QTextEdit, QProgressBar,
    QComboBox, QCheckBox, QSlider, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QSystemTrayIcon
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, QRect
)
from PyQt5.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QFontDatabase, QIcon, QPixmap
)


class MacOSColors:
    ACCENT = "#007AFF"
    SYSTEM_GREEN = "#30D158"
    SYSTEM_RED = "#FF453A"
    SYSTEM_ORANGE = "#FF9F0A"
    SYSTEM_PURPLE = "#BF5AF2"
    SYSTEM_PINK = "#FF375F"
    SYSTEM_GRAY = "#8E8E93"
    SYSTEM_GRAY2 = "#636366"
    SYSTEM_GRAY3 = "#48484A"
    SYSTEM_YELLOW = "#FFD60A"

    WINDOW_BG = "#F0F0F2"
    CARD_BG = "#FFFFFF"
    SIDEBAR_BG = "#F0F0F2"
    TOOLBAR_BG = "#FFFFFF"

    TEXT_PRIMARY = "#1C1C1E"
    TEXT_SECONDARY = "#8E8E93"
    SEPARATOR = "#D1D1D6"
    ACCENT_BG = "#007AFF15"


class MacOSSidebarItem(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.is_selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setMaximumHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(12)

        self.icon_label = QLabel(icon)
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(text)
        layout.addWidget(self.text_label)
        layout.addStretch()

        self.update_style()

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet(f"""
                MacOSSidebarItem {{
                    background-color: {MacOSColors.ACCENT};
                    border-radius: 8px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: white; font-size: 16px;")
            self.text_label.setStyleSheet(f"""
                color: white;
                font-size: 16px;
                font-weight: 600;
            """)
        else:
            self.setStyleSheet(f"""
                MacOSSidebarItem {{
                    background-color: transparent;
                    border-radius: 8px;
                }}
                MacOSSidebarItem:hover {{
                    background-color: #D9D9DE;
                }}
            """)
            self.icon_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 16px;
            """)
            self.text_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 400;
            """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class MacOSSidebar(QWidget):
    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setStyleSheet(f"""
            MacOSSidebar {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border-right: 1px solid {MacOSColors.SEPARATOR};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 28, 12, 16)
        layout.setSpacing(2)

        title = QLabel("\\u5bfc\\u822a\\u83dc\\u5355")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 2px;
            padding: 0 10px;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)

        self.items = []
        nav_items = [
            ("\\U0001f4ca", "\\u4eea\\u8868\\u76d8"),
            ("\\U0001f4c1", "\\u6587\\u4ef6\\u7ba1\\u7406"),
            ("\\U0001f50d", "\\u641c\\u7d22\\u53d1\\u73b0"),
            ("\\U0001f4ac", "\\u6d88\\u606f\\u901a\\u77e5"),
            ("\\u2699\\ufe0f", "\\u7cfb\\u7edf\\u8bbe\\u7f6e"),
        ]

        for i, (icon, text) in enumerate(nav_items):
            item = MacOSSidebarItem(icon, text)
            item.clicked.connect(lambda checked=False, idx=i: self.set_active_tab(idx))
            self.items.append(item)
            layout.addWidget(item)

        layout.addStretch()

        user_frame = QFrame()
        user_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {MacOSColors.CARD_BG};
                border-radius: 12px;
            }}
        """)
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(12, 10, 12, 10)
        user_layout.setSpacing(12)

        avatar = QLabel("\\U0001f464")
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {MacOSColors.ACCENT_BG};
            border-radius: 19px;
            font-size: 18px;
        """)
        user_layout.addWidget(avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(2)

        name = QLabel("\\u7528\\u6237\\u540d")
        name.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 15px;
            font-weight: 600;
        """)
        user_info.addWidget(name)

        status = QLabel("\\u25cf \\u5728\\u7ebf")
        status.setStyleSheet(f"""
            color: {MacOSColors.SYSTEM_GREEN};
            font-size: 12px;
        """)
        user_info.addWidget(status)

        user_layout.addLayout(user_info)
        user_layout.addStretch()

        layout.addWidget(user_frame)

        self.set_active_tab(0)

    def set_active_tab(self, index):
        for i, item in enumerate(self.items):
            item.set_selected(i == index)
        self.tab_changed.emit(index)


class MacOSCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            MacOSCard {{
                background-color: {MacOSColors.CARD_BG};
                border-radius: 12px;
            }}
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 5))
        painter.drawRoundedRect(1, 2, self.width() - 3, self.height() - 2, 12, 12)
        painter.setBrush(QColor(MacOSColors.CARD_BG))
        painter.drawRoundedRect(0, 0, self.width() - 2, self.height() - 2, 12, 12)
        painter.end()


class MacOSButton(QPushButton):
    def __init__(self, text="", color=MacOSColors.ACCENT, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(34)
        self.setStyleSheet(f"""
            MacOSButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                padding: 6px 18px;
            }}
            MacOSButton:hover {{
                background-color: {color}DD;
            }}
            MacOSButton:pressed {{
                background-color: {color}BB;
            }}
        """)


class MacOSSecondaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(34)
        self.setStyleSheet(f"""
            MacOSSecondaryButton {{
                background-color: transparent;
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 400;
                padding: 6px 18px;
            }}
            MacOSSecondaryButton:hover {{
                background-color: {MacOSColors.SIDEBAR_BG};
            }}
            MacOSSecondaryButton:pressed {{
                background-color: #D9D9DE;
            }}
        """)


class MacOSToolbar(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(f"""
            MacOSToolbar {{
                background-color: {MacOSColors.TOOLBAR_BG};
                border-bottom: 1px solid {MacOSColors.SEPARATOR};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        for color in [MacOSColors.SYSTEM_RED, MacOSColors.SYSTEM_YELLOW, MacOSColors.SYSTEM_GREEN]:
            btn = QPushButton()
            btn.setFixedSize(11, 11)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {color}; border: none; border-radius: 5px; }}
                QPushButton:hover {{ background-color: {color}CC; }}
            """)
            controls_layout.addWidget(btn)

        layout.addWidget(controls)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(self.title_label)
        layout.addStretch()

        search = QLineEdit()
        search.setPlaceholderText("\\U0001f50d \\u641c\\u7d22")
        search.setFixedWidth(200)
        search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                background-color: {MacOSColors.CARD_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
            }}
        """)
        layout.addWidget(search)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(22)

        welcome = QLabel("\\u6b22\\u8fce\\u56de\\u6765 \\U0001f44b")
        welcome.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 32px;
            font-weight: 700;
        """)
        layout.addWidget(welcome)

        date_label = QLabel("2026\\u5e745\\u670824\\u65e5 \\u661f\\u671f\\u65e5")
        date_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 15px;
        """)
        layout.addWidget(date_label)

        layout.addSpacing(8)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        stats = [
            ("1,234", "\\u603b\\u8bbf\\u95ee\\u91cf", MacOSColors.ACCENT),
            ("567", "\\u6d3b\\u8dc3\\u7528\\u6237", MacOSColors.SYSTEM_GREEN),
            ("89%", "\\u5b8c\\u6210\\u7387", MacOSColors.SYSTEM_ORANGE),
            ("12", "\\u65b0\\u6d88\\u606f", MacOSColors.SYSTEM_PURPLE),
        ]

        for value, label, color in stats:
            card = MacOSCard()
            card.setMinimumHeight(110)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 18, 18, 18)
            card_layout.setSpacing(6)

            value_label = QLabel(value)
            value_label.setStyleSheet(f"""
                color: {color};
                font-size: 32px;
                font-weight: 700;
            """)
            card_layout.addWidget(value_label)

            text_label = QLabel(label)
            text_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 14px;
            """)
            card_layout.addWidget(text_label)

            stats_row.addWidget(card)

        layout.addLayout(stats_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(14)

        left_card = MacOSCard()
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(22, 18, 22, 18)
        left_layout.setSpacing(12)

        left_title = QLabel("\\U0001f4cb \\u6700\\u8fd1\\u6d3b\\u52a8")
        left_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
        """)
        left_layout.addWidget(left_title)

        activities = [
            ("\\U0001f4c4", "\\u4e0a\\u4f20\\u4e86\\u65b0\\u6587\\u4ef6", "2\\u5206\\u949f\\u524d", MacOSColors.ACCENT),
            ("\\u2705", "\\u5b8c\\u6210\\u4e86\\u4efb\\u52a1", "15\\u5206\\u949f\\u524d", MacOSColors.SYSTEM_GREEN),
            ("\\U0001f4ac", "\\u6536\\u5230\\u65b0\\u6d88\\u606f", "1\\u5c0f\\u65f6\\u524d", MacOSColors.SYSTEM_ORANGE),
            ("\\U0001f504", "\\u7cfb\\u7edf\\u66f4\\u65b0", "\\u6628\\u5929", MacOSColors.SYSTEM_GRAY),
        ]

        for icon, text, time, color in activities:
            item = QFrame()
            item.setStyleSheet("background-color: transparent;")
            item_layout = QHBoxLayout(item)
            item_layout.setContentsMargins(4, 8, 4, 8)
            item_layout.setSpacing(12)

            icon_label = QLabel(icon)
            icon_label.setFixedSize(32, 32)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(f"""
                background-color: {color}12;
                border-radius: 8px;
                font-size: 14px;
            """)
            item_layout.addWidget(icon_label)

            text_label = QLabel(text)
            text_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 14px;
            """)
            item_layout.addWidget(text_label)
            item_layout.addStretch()

            time_label = QLabel(time)
            time_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 12px;
            """)
            item_layout.addWidget(time_label)

            left_layout.addWidget(item)

        left_layout.addStretch()
        content_row.addWidget(left_card, 2)

        right_card = MacOSCard()
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(22, 18, 22, 18)
        right_layout.setSpacing(12)

        right_title = QLabel("\\u26a1 \\u5feb\\u901f\\u64cd\\u4f5c")
        right_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
        """)
        right_layout.addWidget(right_title)

        for text, color in [
            ("\\U0001f4dd \\u65b0\\u5efa\\u6587\\u6863", MacOSColors.ACCENT),
            ("\\U0001f4e4 \\u4e0a\\u4f20\\u6587\\u4ef6", MacOSColors.SYSTEM_GREEN),
            ("\\U0001f4cb \\u521b\\u5efa\\u4efb\\u52a1", MacOSColors.SYSTEM_ORANGE),
            ("\\u2709\\ufe0f \\u53d1\\u9001\\u6d88\\u606f", MacOSColors.SYSTEM_PURPLE),
        ]:
            btn = MacOSButton(text, color)
            right_layout.addWidget(btn)

        right_layout.addStretch()
        content_row.addWidget(right_card, 1)

        layout.addLayout(content_row)
        layout.addStretch()


class FileManagerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("\\U0001f4c1 \\u6587\\u4ef6\\u7ba1\\u7406")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        header.addWidget(title)
        header.addStretch()

        header.addWidget(MacOSButton("+ \\u65b0\\u5efa\\u6587\\u4ef6\\u5939", MacOSColors.ACCENT))
        header.addWidget(MacOSSecondaryButton("\\U0001f4e4 \\u4e0a\\u4f20\\u6587\\u4ef6"))
        layout.addLayout(header)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["\\u540d\\u79f0", "\\u5927\\u5c0f", "\\u7c7b\\u578b", "\\u4fee\\u6539\\u65e5\\u671f", "\\u64cd\\u4f5c"])
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {MacOSColors.CARD_BG};
                border-radius: 12px;
                font-size: 13px;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 12px 10px;
                border: none;
                font-size: 13px;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QTableWidget::item:selected {{
                background-color: {MacOSColors.ACCENT_BG};
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: {MacOSColors.TEXT_SECONDARY};
                padding: 10px;
                border: none;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setShowGrid(False)

        files = [
            ("\\U0001f4c4 \\u9879\\u76ee\\u62a5\\u544a.pdf", "2.5 MB", "PDF", "2026-05-20"),
            ("\\U0001f5bc\\ufe0f \\u98ce\\u666f\\u7167\\u7247.png", "1.8 MB", "\\u56fe\\u7247", "2026-05-19"),
            ("\\U0001f3ac \\u6f14\\u793a\\u89c6\\u9891.mp4", "15.2 MB", "\\u89c6\\u9891", "2026-05-18"),
            ("\\U0001f3b5 \\u80cc\\u666f\\u97f3\\u4e50.mp3", "5.1 MB", "\\u97f3\\u9891", "2026-05-17"),
            ("\\U0001f4dd \\u6e90\\u4ee3\\u7801.py", "12 KB", "\\u4ee3\\u7801", "2026-05-16"),
        ]

        table.setRowCount(len(files))
        for i, (name, size, ftype, date) in enumerate(files):
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(i, 1, QTableWidgetItem(size))
            table.setItem(i, 2, QTableWidgetItem(ftype))
            table.setItem(i, 3, QTableWidgetItem(date))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(8)

            open_btn = QPushButton("\\u6253\\u5f00")
            open_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {MacOSColors.ACCENT};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 11px;
                }}
            """)
            action_layout.addWidget(open_btn)

            delete_btn = QPushButton("\\u5220\\u9664")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {MacOSColors.SYSTEM_RED};
                    border: none;
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 11px;
                }}
            """)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()

            table.setCellWidget(i, 4, action_widget)

        layout.addWidget(table)


class SearchPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(22)
        layout.setAlignment(Qt.AlignTop)

        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background-color: {MacOSColors.CARD_BG};
                border-radius: 12px;
            }}
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(22, 16, 22, 16)
        search_layout.setSpacing(12)

        search_icon = QLabel("\\U0001f50d")
        search_icon.setStyleSheet(f"font-size: 20px;")
        search_layout.addWidget(search_icon)

        search_input = QLineEdit()
        search_input.setPlaceholderText("\\u641c\\u7d22\\u6587\\u4ef6\\u3001\\u6d88\\u606f\\u3001\\u8bbe\\u7f6e...")
        search_input.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background: transparent;
                font-size: 18px;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
        """)
        search_layout.addWidget(search_input)

        shadow = QGraphicsDropShadowEffect(search_container)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 8))
        shadow.setOffset(0, 3)
        search_container.setGraphicsEffect(shadow)

        layout.addWidget(search_container)

        hot_title = QLabel("\\U0001f3f7\\ufe0f \\u70ed\\u95e8\\u641c\\u7d22")
        hot_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
            margin-top: 8px;
        """)
        layout.addWidget(hot_title)

        tags_widget = QWidget()
        tags_layout = QHBoxLayout(tags_widget)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(10)

        for tag, color in [
            ("\\U0001f3a8 \\u8bbe\\u8ba1", MacOSColors.ACCENT),
            ("\\U0001f4bb \\u5f00\\u53d1", MacOSColors.SYSTEM_GREEN),
            ("\\U0001f4c4 \\u6587\\u6863", MacOSColors.SYSTEM_ORANGE),
            ("\\U0001f5bc\\ufe0f \\u56fe\\u7247", MacOSColors.SYSTEM_PURPLE),
            ("\\U0001f3ac \\u89c6\\u9891", MacOSColors.SYSTEM_PINK),
        ]:
            btn = QPushButton(tag)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}10;
                    color: {color};
                    border: none;
                    border-radius: 16px;
                    padding: 8px 22px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ background-color: {color}20; }}
            """)
            tags_layout.addWidget(btn)

        tags_layout.addStretch()
        layout.addWidget(tags_widget)

        results_title = QLabel("\\U0001f4cc \\u6700\\u8fd1\\u8bbf\\u95ee")
        results_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
            margin-top: 16px;
        """)
        layout.addWidget(results_title)

        for i in range(5):
            card = MacOSCard()
            card.setMinimumHeight(76)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(18, 10, 18, 10)
            card_layout.setSpacing(16)

            icon = QLabel("\\U0001f4c4")
            icon.setFixedSize(36, 36)
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet(f"""
                background-color: {MacOSColors.ACCENT_BG};
                border-radius: 10px;
                font-size: 16px;
            """)
            card_layout.addWidget(icon)

            info = QVBoxLayout()
            info.setSpacing(4)

            name = QLabel(f"\\u641c\\u7d22\\u7ed3\\u679c\\u9879\\u76ee {i+1}")
            name.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 500;
            """)
            info.addWidget(name)

            desc = QLabel("\\u8fd9\\u662f\\u4e00\\u4e2a\\u641c\\u7d22\\u7ed3\\u679c\\u7684\\u63cf\\u8ff0\\u6587\\u672c...")
            desc.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 13px;
            """)
            info.addWidget(desc)

            card_layout.addLayout(info)
            card_layout.addStretch()

            arrow = QLabel("\\u203a")
            arrow.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 20px;
            """)
            card_layout.addWidget(arrow)

            layout.addWidget(card)

        layout.addStretch()


class MessagesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("\\U0001f4ac \\u6d88\\u606f\\u901a\\u77e5")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        header.addWidget(title)
        header.addStretch()

        mark_all = QPushButton("\\u2705 \\u5168\\u90e8\\u5df2\\u8bfb")
        mark_all.setCursor(Qt.PointingHandCursor)
        mark_all.setStyleSheet(f"""
            QPushButton {{
                color: {MacOSColors.ACCENT};
                font-size: 13px;
                border: none;
                background: transparent;
            }}
        """)
        header.addWidget(mark_all)

        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background-color: transparent;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)

        messages = [
            ("\\U0001f464", "\\u5f20\\u4e09", "\\u9879\\u76ee\\u8fdb\\u5ea6\\u66f4\\u65b0", "\\u4f60\\u597d\\uff0c\\u9879\\u76ee\\u8fdb\\u5ea6\\u5df2\\u7ecf\\u66f4\\u65b0\\u4e86\\uff0c\\u8bf7\\u67e5\\u770b\\u6700\\u65b0\\u7248\\u672c...", "10:30", MacOSColors.ACCENT, True),
            ("\\U0001f464", "\\u674e\\u56db", "\\u4f1a\\u8bae\\u9080\\u8bf7", "\\u660e\\u5929\\u4e0b\\u53483\\u70b9\\u6709\\u4e2a\\u4f1a\\u8bae\\uff0c\\u8bf7\\u51c6\\u65f6\\u53c2\\u52a0", "\\u6628\\u5929", MacOSColors.SYSTEM_GREEN, True),
            ("\\U0001f464", "\\u738b\\u4e94", "\\u6587\\u4ef6\\u5171\\u4eab", "\\u6211\\u5206\\u4eab\\u4e86\\u4e00\\u4e2a\\u6587\\u4ef6\\u7ed9\\u4f60\\uff0c\\u8bf7\\u67e5\\u6536", "\\u6628\\u5929", MacOSColors.SYSTEM_ORANGE, False),
            ("\\U0001f464", "\\u7cfb\\u7edf\\u901a\\u77e5", "\\u8d26\\u6237\\u5b89\\u5168\\u63d0\\u9192", "\\u4f60\\u7684\\u5bc6\\u7801\\u5373\\u5c06\\u8fc7\\u671f\\uff0c\\u8bf7\\u53ca\\u65f6\\u66f4\\u65b0", "\\u5468\\u4e00", MacOSColors.SYSTEM_GRAY, False),
        ]

        for icon, name, title_text, content_text, time, color, unread in messages:
            card = MacOSCard()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(18, 12, 18, 12)
            card_layout.setSpacing(16)

            avatar = QLabel(icon)
            avatar.setFixedSize(42, 42)
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet(f"""
                background-color: {color}12;
                border-radius: 21px;
                font-size: 18px;
            """)
            card_layout.addWidget(avatar)

            msg_content = QVBoxLayout()
            msg_content.setSpacing(4)

            top = QHBoxLayout()
            name_label = QLabel(name)
            name_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: {'700' if unread else '600'};
            """)
            top.addWidget(name_label)
            top.addStretch()

            time_label = QLabel(time)
            time_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 12px;
            """)
            top.addWidget(time_label)
            msg_content.addLayout(top)

            title_l = QLabel(title_text)
            title_l.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: {'600' if unread else '400'};
            """)
            msg_content.addWidget(title_l)

            content_l = QLabel(content_text)
            content_l.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 13px;
            """)
            content_l.setWordWrap(True)
            msg_content.addWidget(content_l)

            card_layout.addLayout(msg_content)

            if unread:
                badge = QLabel()
                badge.setFixedSize(11, 11)
                badge.setStyleSheet(f"""
                    background-color: {MacOSColors.SYSTEM_RED};
                    border-radius: 5px;
                """)
                card_layout.addWidget(badge)

            content_layout.addWidget(card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(22)

        title = QLabel("\\u2699\\ufe0f \\u7cfb\\u7edf\\u8bbe\\u7f6e")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        layout.addWidget(title)

        groups = [
            ("\\u2699\\ufe0f \\u901a\\u7528\\u8bbe\\u7f6e", [
                ("\\U0001f504 \\u81ea\\u52a8\\u542f\\u52a8", "check", True),
                ("\\U0001f4cc \\u6700\\u5c0f\\u5316\\u5230\\u6258\\u76d8", "check", False),
                ("\\U0001f310 \\u8bed\\u8a00", "combo", ["\\u7b80\\u4f53\\u4e2d\\u6587", "English", "\\u65e5\\u672c\\u8a9e"]),
            ]),
            ("\\U0001f3a8 \\u5916\\u89c2\\u8bbe\\u7f6e", [
                ("\\U0001f3ad \\u4e3b\\u9898", "combo", ["\\u6d45\\u8272\\u6a21\\u5f0f", "\\u6df1\\u8272\\u6a21\\u5f0f", "\\u8ddf\\u968f\\u7cfb\\u7edf"]),
                ("\\U0001f4cf \\u5b57\\u4f53\\u5927\\u5c0f", "slider", (10, 24, 13)),
                ("\\u2728 \\u663e\\u793a\\u52a8\\u753b", "check", True),
            ]),
            ("\\U0001f514 \\u901a\\u77e5\\u8bbe\\u7f6e", [
                ("\\U0001f514 \\u542f\\u7528\\u901a\\u77e5", "check", True),
                ("\\U0001f50a \\u58f0\\u97f3\\u63d0\\u793a", "check", True),
                ("\\u23f0 \\u901a\\u77e5\\u9891\\u7387", "combo", ["\\u5b9e\\u65f6\\u63a8\\u9001", "\\u6bcf\\u5c0f\\u65f6\\u6c47\\u603b", "\\u6bcf\\u5929\\u6c47\\u603b"]),
            ]),
        ]

        for group_name, settings in groups:
            group_card = MacOSCard()
            group_layout = QVBoxLayout(group_card)
            group_layout.setContentsMargins(22, 18, 22, 18)
            group_layout.setSpacing(18)

            group_title = QLabel(group_name)
            group_title.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 19px;
                font-weight: 600;
            """)
            group_layout.addWidget(group_title)

            for i, (setting_name, setting_type, setting_value) in enumerate(settings):
                if i > 0:
                    spacer = QWidget()
                    spacer.setFixedHeight(1)
                    spacer.setStyleSheet(f"background-color: {MacOSColors.SEPARATOR};")
                    group_layout.addWidget(spacer)

                setting_row = QHBoxLayout()
                setting_row.setSpacing(12)

                name_label = QLabel(setting_name)
                name_label.setStyleSheet(f"""
                    color: {MacOSColors.TEXT_PRIMARY};
                    font-size: 14px;
                """)
                setting_row.addWidget(name_label)
                setting_row.addStretch()

                if setting_type == "check":
                    checkbox = QCheckBox()
                    checkbox.setChecked(setting_value)
                    checkbox.setStyleSheet(f"""
                        QCheckBox::indicator {{
                            width: 20px;
                            height: 20px;
                            border-radius: 10px;
                            border: 2px solid {MacOSColors.SYSTEM_GRAY3};
                        }}
                        QCheckBox::indicator:checked {{
                            background-color: {MacOSColors.ACCENT};
                            border-color: {MacOSColors.ACCENT};
                        }}
                    """)
                    setting_row.addWidget(checkbox)

                elif setting_type == "combo":
                    combo = QComboBox()
                    combo.addItems(setting_value)
                    combo.setStyleSheet(f"""
                        QComboBox {{
                            background-color: {MacOSColors.SIDEBAR_BG};
                            border: none;
                            border-radius: 8px;
                            padding: 8px 14px;
                            font-size: 13px;
                            min-width: 140px;
                        }}
                    """)
                    setting_row.addWidget(combo)

                elif setting_type == "slider":
                    min_val, max_val, default = setting_value
                    slider = QSlider(Qt.Horizontal)
                    slider.setRange(min_val, max_val)
                    slider.setValue(default)
                    slider.setFixedWidth(180)
                    slider.setStyleSheet(f"""
                        QSlider::groove:horizontal {{
                            height: 5px;
                            background: {MacOSColors.SEPARATOR};
                            border-radius: 2px;
                        }}
                        QSlider::handle:horizontal {{
                            width: 18px;
                            height: 18px;
                            margin: -7px 0;
                            background: {MacOSColors.CARD_BG};
                            border: 2px solid {MacOSColors.SYSTEM_GRAY3};
                            border-radius: 9px;
                        }}
                        QSlider::sub-page:horizontal {{
                            background: {MacOSColors.ACCENT};
                            border-radius: 2px;
                        }}
                    """)
                    setting_row.addWidget(slider)

                group_layout.addLayout(setting_row)

            layout.addWidget(group_card)

        layout.addStretch()


class MacOSDesktopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS \\u684c\\u9762\\u98ce\\u683c\\u5e94\\u7528")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {MacOSColors.WINDOW_BG};
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = MacOSSidebar()
        self.sidebar.tab_changed.connect(self.on_tab_changed)
        layout.addWidget(self.sidebar)

        content_area = QWidget()
        content_area.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.toolbar = MacOSToolbar("\\U0001f4ca \\u4eea\\u8868\\u76d8")
        content_layout.addWidget(self.toolbar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")

        self.pages = [
            DashboardPage(),
            FileManagerPage(),
            SearchPage(),
            MessagesPage(),
            SettingsPage(),
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack)
        layout.addWidget(content_area, 1)

        self.fade_animation = None

    def on_tab_changed(self, index):
        if self.stack.currentIndex() == index:
            return

        titles = ["\\U0001f4ca \\u4eea\\u8868\\u76d8", "\\U0001f4c1 \\u6587\\u4ef6\\u7ba1\\u7406", "\\U0001f50d \\u641c\\u7d22\\u53d1\\u73b0", "\\U0001f4ac \\u6d88\\u606f\\u901a\\u77e5", "\\u2699\\ufe0f \\u7cfb\\u7edf\\u8bbe\\u7f6e"]
        self.toolbar.title_label.setText(titles[index])

        new_page = self.pages[index]

        opacity_effect = QGraphicsOpacityEffect(new_page)
        new_page.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0)

        self.stack.setCurrentIndex(index)

        self.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_animation.setDuration(250)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)

    font = QFont("Microsoft YaHei UI", 12)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    app.setStyle("Fusion")

    app.setStyleSheet(f"""
        QToolTip {{
            background-color: {MacOSColors.CARD_BG};
            color: {MacOSColors.TEXT_PRIMARY};
            border: none;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 11px;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 7px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {MacOSColors.SYSTEM_GRAY3}30;
            border-radius: 3px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {MacOSColors.SYSTEM_GRAY2}50;
        }}
    """)

    window = MacOSDesktopApp()
    window.show()

    print("macOS Desktop Style App started successfully!")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
```