import sys
import os
import subprocess
import socket
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QGraphicsOpacityEffect, QLineEdit, QTextEdit,
    QComboBox, QSlider, QSpinBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QProgressBar, QFileDialog, QSplitter, QGroupBox, QGridLayout
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, QThread, pyqtSlot
)
from PyQt5.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QPixmap, QIcon, QImage
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


class ADBConnectionThread(QThread):
    connection_result = pyqtSignal(bool, str)

    def __init__(self, ip, port=5555):
        super().__init__()
        self.ip = ip
        self.port = port

    def run(self):
        try:
            result = subprocess.run(
                ["adb", "connect", f"{self.ip}:{self.port}"],
                capture_output=True, text=True, timeout=10
            )
            if "connected" in result.stdout.lower():
                self.connection_result.emit(True, f"已连接到 {self.ip}:{self.port}")
            else:
                self.connection_result.emit(False, result.stderr or result.stdout)
        except Exception as e:
            self.connection_result.emit(False, str(e))


class ScreenshotThread(QThread):
    screenshot_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            timestamp = int(time.time() * 1000)
            temp_path = f"/sdcard/screen_{timestamp}.png"
            local_path = f"screen_{timestamp}.png"

            subprocess.run(
                ["adb", "shell", "screencap", "-p", temp_path],
                capture_output=True, timeout=10
            )
            subprocess.run(
                ["adb", "pull", temp_path, local_path],
                capture_output=True, timeout=10
            )
            subprocess.run(
                ["adb", "shell", "rm", temp_path],
                capture_output=True, timeout=5
            )

            if os.path.exists(local_path):
                image = QImage(local_path)
                if not image.isNull():
                    self.screenshot_ready.emit(image)
                    os.remove(local_path)
                else:
                    self.error_occurred.emit("无法加载截图")
                    if os.path.exists(local_path):
                        os.remove(local_path)
            else:
                self.error_occurred.emit("截图文件未生成")
        except Exception as e:
            self.error_occurred.emit(str(e))


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
            self.icon_label.setStyleSheet("color: white; font-size: 16px;")
            self.text_label.setStyleSheet("""
                color: white;
                font-size: 16px;
                font-weight: 600;
            """)
        else:
            self.setStyleSheet("""
                MacOSSidebarItem {
                    background-color: transparent;
                    border-radius: 8px;
                }
                MacOSSidebarItem:hover {
                    background-color: #D9D9DE;
                }
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
            MacSSidebar {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border-right: 1px solid {MacOSColors.SEPARATOR};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 28, 12, 16)
        layout.setSpacing(2)

        title = QLabel("\u5bfc\u822a\u83dc\u5355")
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
            ("\U0001f4f1", "\u8bbe\u5907\u8fde\u63a5"),
            ("\U0001f4bc", "\u5c4f\u5e55\u63a7\u5236"),
            ("\u2709\ufe0f", "\u6587\u4ef6\u4f20\u8f93"),
            ("\U0001f3af", "\u5feb\u6377\u64cd\u4f5c"),
            ("\u2699\ufe0f", "\u7cfb\u7edf\u8bbe\u7f6e"),
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

        avatar = QLabel("\U0001f464")
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

        name = QLabel("WiFi\u63a7\u5236\u5668")
        name.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 15px;
            font-weight: 600;
        """)
        user_info.addWidget(name)

        status = QLabel("\u25cf \u672a\u8fde\u63a5")
        status.setStyleSheet(f"""
            color: {MacOSColors.SYSTEM_GRAY};
            font-size: 12px;
        """)
        status.setObjectName("connection_status")
        user_info.addWidget(status)

        user_layout.addLayout(user_info)
        user_layout.addStretch()

        layout.addWidget(user_frame)

        self.status_label = status
        self.set_active_tab(0)

    def set_active_tab(self, index):
        for i, item in enumerate(self.items):
            item.set_selected(i == index)
        self.tab_changed.emit(index)

    def update_status(self, connected, device_info=""):
        if connected:
            self.status_label.setText(f"\u25cf \u5df2\u8fde\u63a5 - {device_info}")
            self.status_label.setStyleSheet(f"""
                color: {MacOSColors.SYSTEM_GREEN};
                font-size: 12px;
            """)
        else:
            self.status_label.setText("\u25cf \u672a\u8fde\u63a5")
            self.status_label.setStyleSheet(f"""
                color: {MacOSColors.SYSTEM_GRAY};
                font-size: 12px;
            """)


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


class DeviceConnectPage(QWidget):
    connection_changed = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(22)

        title = QLabel("\U0001f4f1 WiFi\u624b\u673a\u63a7\u5236\u5668")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 32px;
            font-weight: 700;
        """)
        layout.addWidget(title)

        desc = QLabel("\u901a\u8fc7WiFi\u8fdc\u7a0b\u8fde\u63a5\u60a8\u7684Android\u624b\u673a\uff0c\u5b9e\u73b0\u5c4f\u5e55\u63a7\u5236\u3001\u6587\u4ef6\u4f20\u8f93\u7b49\u529f\u80fd")
        desc.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 15px;
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(20)

        connect_card = MacOSCard()
        connect_layout = QVBoxLayout(connect_card)
        connect_layout.setContentsMargins(24, 24, 24, 24)
        connect_layout.setSpacing(18)

        connect_title = QLabel("\U0001f517 \u8bbe\u5907\u8fde\u63a5")
        connect_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 20px;
            font-weight: 600;
        """)
        connect_layout.addWidget(connect_title)

        ip_row = QHBoxLayout()
        ip_row.setSpacing(12)

        ip_label = QLabel("IP\u5730\u5740:")
        ip_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 500;
        """)
        ip_label.setFixedWidth(80)
        ip_row.addWidget(ip_label)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.x.x")
        self.ip_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {MacOSColors.ACCENT};
            }}
        """)
        ip_row.addWidget(self.ip_input)

        port_label = QLabel("\u7aef\u53e3:")
        port_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 500;
        """)
        port_label.setFixedWidth(50)
        ip_row.addWidget(port_label)

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(5555)
        self.port_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
        """)
        self.port_input.setFixedWidth(100)
        ip_row.addWidget(self.port_input)

        connect_layout.addLayout(ip_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.connect_btn = MacOSButton("\U0001f517 \u8fde\u63a5\u8bbe\u5907", MacOSColors.ACCENT)
        self.connect_btn.clicked.connect(self.connect_device)
        btn_row.addWidget(self.connect_btn)

        self.disconnect_btn = MacOSSecondaryButton("\u65ad\u5f00\u8fde\u63a5")
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        btn_row.addWidget(self.disconnect_btn)

        self.scan_btn = MacOSButton("\U0001f50d \u626b\u63cf\u8bbe\u5907", MacOSColors.SYSTEM_GREEN)
        self.scan_btn.clicked.connect(self.scan_devices)
        btn_row.addWidget(self.scan_btn)

        btn_row.addStretch()
        connect_layout.addLayout(btn_row)

        self.status_label = QLabel("\u72b6\u6001: \u7b49\u5f85\u8fde\u63a5...")
        self.status_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 13px;
        """)
        connect_layout.addWidget(self.status_label)

        layout.addWidget(connect_card)

        info_card = MacOSCard()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(24, 24, 24, 24)
        info_layout.setSpacing(16)

        info_title = QLabel("\U0001f4cb \u8fde\u63a5\u8bf4\u660e")
        info_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
        """)
        info_layout.addWidget(info_title)

        steps = [
            "1. \u786e\u4fdd\u624b\u673a\u548c\u7535\u8111\u5728\u540c\u4e00WiFi\u7f51\u7edc",
            "2. \u5728\u624b\u673a\u4e0a\u5f00\u542f\u5f00\u53d1\u8005\u9009\u9879 > USB\u8c03\u8bd5",
            "3. \u70b9\u51fb\"\u65e0\u7ebf\u8c03\u8bd5\"\u6216\u8fde\u63a5USB\u540e\u6267\u884c adb tcpip 5555",
            "4. \u8f93\u5165\u624b\u673aIP\u5730\u5740\u5e76\u70b9\u51fb\u8fde\u63a5",
        ]

        for step in steps:
            step_label = QLabel(step)
            step_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 14px;
                padding: 4px 0;
            """)
            info_layout.addWidget(step_label)

        layout.addWidget(info_card)
        layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: none;
                border-radius: 6px;
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {MacOSColors.ACCENT};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.progress_bar)

    def connect_device(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.value()

        if not ip:
            QMessageBox.warning(self, "\u9519\u8bef", "\u8bf7\u8f93\u5165IP\u5730\u5740")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("\u72b6\u6001: \u6b63\u5728\u8fde\u63a5...")
        self.connect_btn.setEnabled(False)

        self.thread = ADBConnectionThread(ip, port)
        self.thread.connection_result.connect(self.on_connection_result)
        self.thread.start()

    def on_connection_result(self, success, message):
        self.progress_bar.setVisible(False)
        self.connect_btn.setEnabled(True)

        if success:
            self.connected = True
            self.status_label.setText(f"\u72b6\u6001: {message}")
            self.status_label.setStyleSheet(f"""
                color: {MacOSColors.SYSTEM_GREEN};
                font-size: 13px;
                font-weight: 500;
            """)
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.ip_input.setEnabled(False)
            self.port_input.setEnabled(False)
            self.connection_changed.emit(True, message)
            QMessageBox.information(self, "\u6210\u529f", message)
        else:
            self.status_label.setText(f"\u72b6\u6001: \u8fde\u63a5\u5931\u8d25 - {message}")
            self.status_label.setStyleSheet(f"""
                color: {MacOSColors.SYSTEM_RED};
                font-size: 13px;
            """)
            self.connection_changed.emit(False, message)
            QMessageBox.warning(self, "\u8fde\u63a5\u5931\u8d25", message)

    def disconnect_device(self):
        try:
            subprocess.run(["adb", "disconnect"], capture_output=True, timeout=5)
            self.connected = False
            self.status_label.setText("\u72b6\u6001: \u5df2\u65ad\u5f00\u8fde\u63a5")
            self.status_label.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 13px;
            """)
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            self.connection_changed.emit(False, "")
        except Exception as e:
            QMessageBox.warning(self, "\u9519\u8bef", f"\u65ad\u5f00\u8fde\u63a5\u5931\u8d25: {str(e)}")

    def scan_devices(self):
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True, text=True, timeout=10
            )
            devices = []
            lines = result.stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 1 and parts[0].strip():
                        devices.append(parts[0].strip())

            if devices:
                msg = "\u53d1\u73b0\u8bbe\u5907:\n\n" + "\n".join(devices)
                if len(devices) == 1 and ':' in devices[0]:
                    ip_part = devices[0].split(':')[0]
                    self.ip_input.setText(ip_part)
                QMessageBox.information(self, "\u626b\u63cf\u7ed3\u679c", msg)
            else:
                QMessageBox.information(self, "\u626b\u63cf\u7ed3\u679c", "\u672a\u53d1\u73b0\u8bbe\u5907")
        except Exception as e:
            QMessageBox.warning(self, "\u9519\u8bef", f"\u626b\u63cf\u5931\u8d25: {str(e)}")


class ScreenControlPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.auto_refresh = False
        self.current_image = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("\U0001f4bc \u5c4f\u5e55\u63a7\u5236")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        header.addWidget(title)
        header.addStretch()

        self.refresh_btn = MacOSButton("\U0001f504 \u5237\u65b0\u5c4f\u5e55", MacOSColors.ACCENT)
        self.refresh_btn.clicked.connect(self.take_screenshot)
        header.addWidget(self.refresh_btn)

        self.auto_refresh_btn = MacOSSecondaryButton("\U0001f504 \u81ea\u52a8\u5237\u65b0")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        header.addWidget(self.auto_refresh_btn)

        layout.addLayout(header)

        content = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        screen_card = MacOSCard()
        screen_layout = QVBoxLayout(screen_card)
        screen_layout.setContentsMargins(12, 12, 12, 12)

        self.screen_label = QLabel()
        self.screen_label.setAlignment(Qt.AlignCenter)
        self.screen_label.setMinimumSize(360, 640)
        self.screen_label.setStyleSheet(f"""
            background-color: {MacOSColors.SIDEBAR_BG};
            border-radius: 8px;
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 14px;
        """)
        self.screen_label.setText("\U0001f4f1 \u5c4f\u5e55\u753b\u9762")

        screen_layout.addWidget(self.screen_label)
        left_layout.addWidget(screen_card)

        self.screenshot_thread = None
        content.addWidget(left_panel, 2)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        control_card = MacOSCard()
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(20, 18, 20, 18)
        control_layout.setSpacing(14)

        control_title = QLabel("\u270b \u89e6\u6478\u64cd\u4f5c")
        control_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
        """)
        control_layout.addWidget(control_title)

        touch_grid = QGridLayout()
        touch_grid.setSpacing(10)

        actions = [
            ("\U0001f446", "\u70b9\u51fb", self.tap_screen),
            ("\U0001f9ad", "\u957f\u6309", self.long_press),
            ("\u2191", "\u5411\u4e0a\u6ed1", self.swipe_up),
            ("\u2193", "\u5411\u4e0b\u6ed1", self.swipe_down),
            ("\u2190", "\u5411\u5de6\u6ed1", self.swipe_left),
            ("\u2192", "\u5411\u53f3\u6ed1", self.swipe_right),
            ("\u23ce", "Return", self.press_back),
            ("\U0001f3b1", "Home", self.press_home),
            ("\U0001f504", "\u6700\u8fd1\u4efb\u52a1", self.press_recent),
        ]

        for i, (icon, text, func) in enumerate(actions):
            row, col = divmod(i, 3)
            btn = MacOSButton(f"{icon} {text}", MacOSColors.ACCENT if i < 6 else MacOSColors.SYSTEM_PURPLE)
            btn.clicked.connect(func)
            touch_grid.addWidget(btn, row, col)

        control_layout.addLayout(touch_grid)
        right_layout.addWidget(control_card)

        input_card = MacOSCard()
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 18, 20, 18)
        input_layout.setSpacing(12)

        input_title = QLabel("\u2328 \u6587\u5b57\u8f93\u5165")
        input_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
        """)
        input_layout.addWidget(input_title)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("\u8f93\u5165\u8981\u53d1\u9001\u5230\u624b\u673a\u7684\u6587\u5b57...")
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: {MacOSColors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {MacOSColors.ACCENT};
            }}
        """)
        input_layout.addWidget(self.text_input)

        send_btn = MacOSButton("\u2709 \u53d1\u9001\u6587\u5b57", MacOSColors.SYSTEM_GREEN)
        send_btn.clicked.connect(self.send_text)
        input_layout.addWidget(send_btn)

        right_layout.addWidget(input_card)
        right_layout.addStretch()

        content.addWidget(right_panel, 1)
        layout.addWidget(content)

        self.timer = QTimer()
        self.timer.timeout.connect(self.take_screenshot)

    def take_screenshot(self):
        if not self.is_connected:
            return

        if self.screenshot_thread and self.screenshot_thread.isRunning():
            return

        self.screenshot_thread = ScreenshotThread()
        self.screenshot_thread.screenshot_ready.connect(self.update_screen)
        self.screenshot_thread.error_occurred.connect(self.on_screenshot_error)
        self.screenshot_thread.start()

    @pyqtSlot(QImage)
    def update_screen(self, image):
        self.current_image = image
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.screen_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.screen_label.setPixmap(scaled_pixmap)

    @pyqtSlot(str)
    def on_screenshot_error(self, error):
        print(f"\u622a\u56fe\u9519\u8bef: {error}")

    def toggle_auto_refresh(self):
        self.auto_refresh = self.auto_refresh_btn.isChecked()
        if self.auto_refresh:
            self.auto_refresh_btn.setStyleSheet(f"""
                MacOSSecondaryButton {{
                    background-color: {MacOSColors.ACCENT};
                    color: white;
                }}
            """)
            self.timer.start(2000)
        else:
            self.auto_refresh_btn.setStyleSheet("")
            self.timer.stop()

    def execute_adb_command(self, command):
        if not self.is_connected:
            QMessageBox.warning(self, "\u672a\u8fde\u63a5", "\u8bf7\u5148\u8fde\u63a5\u8bbe\u5907")
            return

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print(f"\u547d\u4ee4\u6267\u884c\u5931\u8d25: {result.stderr}")
        except Exception as e:
            print(f"\u6267\u884c\u9519\u8bef: {str(e)}")

    def tap_screen(self):
        self.execute_adb_command("adb shell input tap 540 1200")

    def long_press(self):
        self.execute_adb_command("adb shell input swipe 540 1200 540 1200 1500")

    def swipe_up(self):
        self.execute_adb_command("adb shell input swipe 540 1800 540 600 300")

    def swipe_down(self):
        self.execute_adb_command("adb shell input swipe 540 600 540 1800 300")

    def swipe_left(self):
        self.execute_adb_command("adb shell input swipe 900 1200 180 1200 300")

    def swipe_right(self):
        self.execute_adb_command("adb shell input swipe 180 1200 900 1200 300")

    def press_back(self):
        self.execute_adb_command("adb shell input keyevent KEYCODE_BACK")

    def press_home(self):
        self.execute_adb_command("adb shell input keyevent KEYCODE_HOME")

    def press_recent(self):
        self.execute_adb_command("adb shell input keyevent KEYCODE_APP_SWITCH")

    def send_text(self):
        text = self.text_input.text().strip()
        if not text:
            return

        escaped_text = text.replace(' ', '%s').replace('&', '\\&')
        self.execute_adb_command(f'adb shell input text "{escaped_text}"')
        self.text_input.clear()

    def set_connected(self, connected):
        self.is_connected = connected
        self.refresh_btn.setEnabled(connected)
        self.auto_refresh_btn.setEnabled(connected)


class FileTransferPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("\u2709\ufe0f \u6587\u4ef6\u4f20\u8f93")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        transfer_card = MacOSCard()
        transfer_layout = QVBoxLayout(transfer_card)
        transfer_layout.setContentsMargins(24, 24, 24, 24)
        transfer_layout.setSpacing(18)

        upload_group = QGroupBox("\U0001f4e4 \u4e0a\u4f20\u6587\u4ef6\u5230\u624b\u673a")
        upload_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 17px;
                font-weight: 600;
                color: {MacOSColors.TEXT_PRIMARY};
                border: none;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
            }}
        """)
        upload_layout = QVBoxLayout(upload_group)
        upload_layout.setSpacing(12)

        file_row = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("\u9009\u62e9\u8981\u4e0a\u4f20\u7684\u6587\u4ef6...")
        self.file_path_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
        """)
        file_row.addWidget(self.file_path_edit)

        browse_btn = MacOSSecondaryButton("\u6d4f\u89c8...")
        browse_btn.clicked.connect(self.browse_file)
        file_row.addWidget(browse_btn)
        upload_layout.addLayout(file_row)

        dest_row = QHBoxLayout()
        dest_label = QLabel("\u76ee\u6807\u8def\u5f84:")
        dest_label.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 14px;")
        dest_row.addWidget(dest_label)

        self.dest_path_edit = QLineEdit("/sdcard/Download/")
        self.dest_path_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
        """)
        dest_row.addWidget(self.dest_path_edit)
        upload_layout.addLayout(dest_row)

        upload_btn = MacOSButton("\U0001f4e4 \u5f00\u59cb\u4e0a\u4f20", MacOSColors.SYSTEM_GREEN)
        upload_btn.clicked.connect(self.upload_file)
        upload_layout.addWidget(upload_btn)

        transfer_layout.addWidget(upload_group)

        download_group = QGroupBox("\U0001f4e5 \u4ece\u624b\u673a\u4e0b\u8f7d\u6587\u4ef6")
        download_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 17px;
                font-weight: 600;
                color: {MacOSColors.TEXT_PRIMARY};
                border: none;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
            }}
        """)
        download_layout = QVBoxLayout(download_group)
        download_layout.setSpacing(12)

        phone_path_row = QHBoxLayout()
        phone_label = QLabel("\u624b\u673a\u8def\u5f84:")
        phone_label.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 14px;")
        phone_path_row.addWidget(phone_label)

        self.phone_path_edit = QLineEdit("/sdcard/Download/")
        self.phone_path_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
        """)
        phone_path_row.addWidget(self.phone_path_edit)
        download_layout.addLayout(phone_path_row)

        local_row = QHBoxLayout()
        local_label = QLabel("\u4fdd\u5b58\u5230:")
        local_label.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 14px;")
        local_row.addWidget(local_label)

        self.local_path_edit = QLineEdit("./downloads/")
        self.local_path_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
        """)
        local_row.addWidget(self.local_path_edit)

        local_browse_btn = MacOSSecondaryButton("\u6d4f\u89c8...")
        local_browse_btn.clicked.connect(self.browse_local_dir)
        local_row.addWidget(local_browse_btn)
        download_layout.addLayout(local_row)

        download_btn = MacOSButton("\U0001f4e5 \u5f00\u59cb\u4e0b\u8f7d", MacOSColors.ACCENT)
        download_btn.clicked.connect(self.download_file)
        download_layout.addWidget(download_btn)

        transfer_layout.addWidget(download_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-family: Consolas, monospace;
            }}
        """)
        transfer_layout.addWidget(self.log_text)

        layout.addWidget(transfer_card)

    def browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "\u9009\u62e9\u6587\u4ef6", "", "\u6240\u6709\u6587\u4ef6 (*)"
        )
        if filename:
            self.file_path_edit.setText(filename)

    def browse_local_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "\u9009\u62e9\u76ee\u5f55")
        if directory:
            self.local_path_edit.setText(directory + "/")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def upload_file(self):
        if not self.is_connected:
            QMessageBox.warning(self, "\u672a\u8fde\u63a5", "\u8bf7\u5148\u8fde\u63a5\u8bbe\u5907")
            return

        local_file = self.file_path_edit.text().strip()
        remote_path = self.dest_path_edit.text().strip()

        if not local_file or not os.path.exists(local_file):
            QMessageBox.warning(self, "\u9519\u8bef", "\u8bf7\u9009\u62e9\u6709\u6548\u7684\u6587\u4ef6")
            return

        try:
            self.log_message(f"\u6b63\u5728\u4e0a\u4f20: {local_file} -> {remote_path}")
            result = subprocess.run(
                ["adb", "push", local_file, remote_path],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                self.log_message("\u2705 \u4e0a\u4f20\u6210\u529f!")
                QMessageBox.information(self, "\u6210\u529f", "\u6587\u4ef6\u4e0a\u4f20\u6210\u529f!")
            else:
                self.log_message(f"\u274c \u4e0a\u4f20\u5931\u8d25: {result.stderr}")
                QMessageBox.warning(self, "\u5931\u8d25", f"\u4e0a\u4f20\u5931\u8d25:\n{result.stderr}")
        except Exception as e:
            self.log_message(f"\u274c \u9519\u8bef: {str(e)}")
            QMessageBox.warning(self, "\u9519\u8bef", str(e))

    def download_file(self):
        if not self.is_connected:
            QMessageBox.warning(self, "\u672a\u8fde\u63a5", "\u8bf7\u5148\u8fde\u63a5\u8bbe\u5907")
            return

        phone_file = self.phone_path_edit.text().strip()
        local_dir = self.local_path_edit.text().strip()

        if not phone_file:
            QMessageBox.warning(self, "\u9519\u8bef", "\u8bf7\u8f93\u5165\u624b\u673a\u6587\u4ef6\u8def\u5f84")
            return

        try:
            self.log_message(f"\u6b63\u5728\u4e0b\u8f7d: {phone_file} -> {local_dir}")
            result = subprocess.run(
                ["adb", "pull", phone_file, local_dir],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                self.log_message("\u2705 \u4e0b\u8f7d\u6210\u529f!")
                QMessageBox.information(self, "\u6210\u529f", "\u6587\u4ef6\u4e0b\u8f7d\u6210\u529f!")
            else:
                self.log_message(f"\u274c \u4e0b\u8f7d\u5931\u8d25: {result.stderr}")
                QMessageBox.warning(self, "\u5931\u8d25", f"\u4e0b\u8f7d\u5931\u8d25:\n{result.stderr}")
        except Exception as e:
            self.log_message(f"\u274c \u9519\u8bef: {str(e)}")
            QMessageBox.warning(self, "\u9519\u8bef", str(e))

    def set_connected(self, connected):
        self.is_connected = connected


class QuickActionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel("\U0001f3af \u5feb\u6377\u64cd\u4f5c")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        layout.addWidget(title)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(14)

        action_groups = [
            (
                "\U0001f4da \u7cfb\u7edf\u64cd\u4f5c",
                [
                    ("\U0001f504 \u91cd\u542f\u624b\u673a", "adb reboot", MacOSColors.SYSTEM_RED),
                    ("\U0001f4cb \u6e05\u9664\u6570\u636e", "adb shell pm clear com.android.browser", MacOSColors.SYSTEM_ORANGE),
                    ("\U0001f512 \u9501\u5b9a\u5c4f\u5e55", "adb shell input keyevent KEYCODE_POWER", MacOSColors.ACCENT),
                    ("\U0001f507 \u9759\u97f3\u6a21\u5f0f", "adb shell cmd volume set 0", MacOSColors.SYSTEM_GRAY),
                ]
            ),
            (
                "\U0001f4f1 \u5e94\u7528\u7ba1\u7406",
                [
                    ("\U0001f4e1 \u6253\u5f00\u8bbe\u7f6e", "adb shell am start -a android.settings.SETTINGS", MacOSColors.SYSTEM_GREEN),
                    ("\U0001f43e \u6253\u5f00\u76f8\u518c", "adb shell am start -a android.intent.action.MAIN -t image/*", MacOSColors.SYSTEM_PURPLE),
                    ("\U0001fa90 \u6253\u5f00\u767e\u5ea6", "adb shell am start -n com.baidu.searchbox/.SplashActivity", MacOSColors.ACCENT),
                    ("\U0001f4dd \u6253\u5f00\u5907\u5fd8", "adb shell am start -n com.android.notes/.NotesListActivity", MacOSColors.SYSTEM_ORANGE),
                ]
            ),
        ]

        for group_title, actions in action_groups:
            group_card = MacOSCard()
            group_layout = QVBoxLayout(group_card)
            group_layout.setContentsMargins(20, 18, 20, 18)
            group_layout.setSpacing(12)

            gtitle = QLabel(group_title)
            gtitle.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 6px;
            """)
            group_layout.addWidget(gtitle)

            for btn_text, command, color in actions:
                btn = MacOSButton(btn_text, color)
                btn.clicked.connect(lambda checked, cmd=command: self.execute_action(cmd))
                group_layout.addWidget(btn)

            actions_row.addWidget(group_card)

        layout.addLayout(actions_row)

        custom_card = MacOSCard()
        custom_layout = QVBoxLayout(custom_card)
        custom_layout.setContentsMargins(20, 18, 20, 18)
        custom_layout.setSpacing(14)

        custom_title = QLabel("\u2328 \u81ea\u5b9a\u4e49\u547d\u4ee4")
        custom_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        custom_layout.addWidget(custom_title)

        self.custom_cmd_input = QLineEdit()
        self.custom_cmd_input.setPlaceholderText("\u8f93\u5165ADB\u547d\u4ee4 (例如: adb shell ls /sdcard)")
        self.custom_cmd_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-family: Consolas, monospace;
            }}
            QLineEdit:focus {{
                border-color: {MacOSColors.ACCENT};
            }}
        """)
        custom_layout.addWidget(self.custom_cmd_input)

        cmd_row = QHBoxLayout()
        exec_btn = MacOSButton("\u25b6 \u6267\u884c\u547d\u4ee4", MacOSColors.ACCENT)
        exec_btn.clicked.connect(self.execute_custom_command)
        cmd_row.addWidget(exec_btn)

        cmd_row.addStretch()
        custom_layout.addLayout(cmd_row)

        self.cmd_output = QTextEdit()
        self.cmd_output.setReadOnly(True)
        self.cmd_output.setMaximumHeight(120)
        self.cmd_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-family: Consolas, monospace;
            }}
        """)
        custom_layout.addWidget(self.cmd_output)

        layout.addWidget(custom_card)
        layout.addStretch()

    def execute_action(self, command):
        if not self.is_connected:
            QMessageBox.warning(self, "\u672a\u8fde\u63a5", "\u8bf7\u5148\u8fde\u63a5\u8bbe\u5907")
            return

        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=15
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            self.cmd_output.append(f"$ {command}\n{output}\n{'='*40}\n")
        except Exception as e:
            self.cmd_output.append(f"\u274c \u6267\u884c\u9519\u8bef: {str(e)}\n")

    def execute_custom_command(self):
        command = self.custom_cmd_input.text().strip()
        if not command:
            return
        self.execute_action(command)
        self.custom_cmd_input.clear()

    def set_connected(self, connected):
        self.is_connected = connected


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(22)

        title = QLabel("\u2699\ufe0f \u7cfb\u7edf\u8bbe\u7f6e")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        layout.addWidget(title)

        about_card = MacOSCard()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(24, 24, 24, 24)
        about_layout.setSpacing(16)

        about_title = QLabel("\U0001f4f1 WiFi\u624b\u673a\u63a7\u5236\u5668")
        about_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 22px;
            font-weight: 700;
        """)
        about_layout.addWidget(about_title)

        version = QLabel("\u7248\u672c: 1.0.0")
        version.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 14px;")
        about_layout.addWidget(version)

        desc = QLabel(
            "\u901a\u8fc7WiFi\u8fdc\u7a0b\u63a7\u5236\u60a8\u7684Android\u624b\u673a\u3002"
            "\u652f\u6301\u5c4f\u5e55\u663e\u793a\u3001\u89e6\u6478\u64cd\u4f5c\u3001\u6587\u4ef6\u4f20\u8f93\u7b49\u529f\u80fd\u3002"
        )
        desc.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 14px;")
        desc.setWordWrap(True)
        about_layout.addWidget(desc)

        layout.addWidget(about_card)

        adb_card = MacOSCard()
        adb_layout = QVBoxLayout(adb_card)
        adb_layout.setContentsMargins(24, 24, 24, 24)
        adb_layout.setSpacing(16)

        adb_title = QLabel("\U0001f4bb ADB \u8bbe\u7f6e")
        adb_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
        """)
        adb_layout.addWidget(adb_title)

        check_btn = MacOSButton("\u2713 \u68c0\u67e5 ADB \u5b89\u88c5", MacOSColors.SYSTEM_GREEN)
        check_btn.clicked.connect(self.check_adb)
        adb_layout.addWidget(check_btn)

        self.adb_status = QLabel()
        self.adb_status.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 13px;")
        adb_layout.addWidget(self.adb_status)

        layout.addWidget(adb_card)

        help_card = MacOSCard()
        help_layout = QVBoxLayout(help_card)
        help_layout.setContentsMargins(24, 24, 24, 24)
        help_layout.setSpacing(14)

        help_title = QLabel("\u2753 \u4f7f\u7528\u5e2e\u52a9")
        help_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 19px;
            font-weight: 600;
        """)
        help_layout.addWidget(help_title)

        help_texts = [
            "\u2022 \u786e\u4fdd\u624b\u673a\u548c\u7535\u8111\u5728\u540c\u4e00WiFi\u7f51\u7edc\u4e0b",
            "\u2022 \u624b\u673a\u9700\u8981\u5f00\u542f USB\u8c03\u8bd5\u548c\u65e0\u7ebf\u8c03\u8bd5",
            "\u2022 \u9996\u6b21\u4f7f\u7528\u9700\u8981\u7528USB\u7ebf\u8fde\u63a5\u5e76\u6267\u884c adb tcpip 5555",
            "\u2022 \u4e4b\u540e\u53ef\u4ee5\u65ad\u5f00USB\u7ebf\uff0c\u4ec5\u901a\u8fc7WiFi\u8fde\u63a5",
        ]

        for help_text in help_texts:
            label = QLabel(help_text)
            label.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 13px; padding: 3px 0;")
            label.setWordWrap(True)
            help_layout.addWidget(label)

        layout.addWidget(help_card)
        layout.addStretch()

    def check_adb(self):
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_info = result.stdout.strip()
                self.adb_status.setText(f"\u2705 ADB \u5df2\u5b89\u88c5\n{version_info}")
                self.adb_status.setStyleSheet(f"color: {MacOSColors.SYSTEM_GREEN}; font-size: 13px;")
            else:
                self.adb_status.setText("\u274c ADB \u672a\u6b63\u786e\u5b89\u88c5")
                self.adb_status.setStyleSheet(f"color: {MacOSColors.SYSTEM_RED}; font-size: 13px;")
        except FileNotFoundError:
            self.adb_status.setText(
                "\u274c ADB \u672a\u627e\u5230\n\u8bf7\u5b89\u88c5 Android SDK Platform-Tools"
            )
            self.adb_status.setStyleSheet(f"color: {MacOSColors.SYSTEM_RED}; font-size: 13px;")
        except Exception as e:
            self.adb_status.setText(f"\u274c \u68c0\u67e5\u5931\u8d25: {str(e)}")
            self.adb_status.setStyleSheet(f"color: {MacOSColors.SYSTEM_RED}; font-size: 13px;")


class WifiPhoneController(QMainWindow):
    def __init__(self):
        super().__init__()
       .setWindowTitle("WiFi \u624b\u673a\u63a7\u5236\u5668")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 850)
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

        self.toolbar = MacOSToolbar("\U0001f4f1 \u8bbe\u5907\u8fde\u63a5")
        content_layout.addWidget(self.toolbar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")

        self.device_page = DeviceConnectPage()
        self.screen_page = ScreenControlPage()
        self.file_page = FileTransferPage()
        self.actions_page = QuickActionsPage()
        self.settings_page = SettingsPage()

        self.pages = [self.device_page, self.screen_page, self.file_page, self.actions_page, self.settings_page]

        for page in self.pages:
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack)
        layout.addWidget(content_area, 1)

        self.device_page.connection_changed.connect(self.on_connection_changed)

        self.fade_animation = None

    def on_tab_changed(self, index):
        if self.stack.currentIndex() == index:
            return

        titles = [
            "\U0001f4f1 \u8bbe\u5907\u8fde\u63a5",
            "\U0001f4bc \u5c4f\u5e55\u63a7\u5236",
            "\u2709\ufe0f \u6587\u4ef6\u4f20\u8f93",
            "\U0001f3af \u5feb\u6377\u64cd\u4f5c",
            "\u2699\ufe0f \u7cfb\u7edf\u8bbe\u7f6e",
        ]
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

    def on_connection_changed(self, connected, device_info):
        self.sidebar.update_status(connected, device_info)
        self.screen_page.set_connected(connected)
        self.file_page.set_connected(connected)
        self.actions_page.set_connected(connected)


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

    window = WifiPhoneController()
    window.show()

    print("WiFi Phone Controller started successfully!")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()