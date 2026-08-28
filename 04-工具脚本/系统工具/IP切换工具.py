import sys
import os
import subprocess
import json
import re
import socket
import urllib.request
import threading
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QScrollArea, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect, QLineEdit, QGridLayout,
    QGraphicsOpacityEffect, QSplitter, QTextEdit, QProgressBar,
    QComboBox, QCheckBox, QSlider, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QSystemTrayIcon,
    QFileDialog, QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QRadioButton, QButtonGroup, QTabWidget, QListWidget, QListWidgetItem,
    QGroupBox
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, QRect, QThread
)
from PyQt5.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QFontDatabase, QIcon, QPixmap,
    QCursor
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
    SYSTEM_TEAL = "#64D2FF"
    SYSTEM_INDIGO = "#5E5CE6"

    WINDOW_BG = "#F0F0F2"
    CARD_BG = "#FFFFFF"
    SIDEBAR_BG = "#F0F0F2"
    TOOLBAR_BG = "#FFFFFF"

    TEXT_PRIMARY = "#1C1C1E"
    TEXT_SECONDARY = "#8E8E93"
    SEPARATOR = "#D1D1D6"
    ACCENT_BG = "#007AFF15"
    GREEN_BG = "#30D15815"
    RED_BG = "#FF453A15"
    ORANGE_BG = "#FF9F0A15"


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

        title = QLabel("IP切换工具")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 700;
            padding: 0 10px;
            margin-bottom: 4px;
        """)
        layout.addWidget(title)

        subtitle = QLabel("一键切换，畅游网络")
        subtitle.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 12px;
            padding: 0 10px;
            margin-bottom: 20px;
        """)
        layout.addWidget(subtitle)

        self.items = []
        nav_items = [
            ("📊", "状态面板"),
            ("🔌", "代理切换"),
            ("🌐", "网卡配置"),
            ("🔍", "IP检测"),
            ("⚙️", "系统设置"),
        ]

        for i, (icon, text) in enumerate(nav_items):
            item = MacOSSidebarItem(icon, text)
            item.clicked.connect(lambda checked=False, idx=i: self.set_active_tab(idx))
            self.items.append(item)
            layout.addWidget(item)

        layout.addStretch()

        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {MacOSColors.CARD_BG};
                border-radius: 12px;
            }}
        """)
        user_layout = QVBoxLayout(info_frame)
        user_layout.setContentsMargins(14, 12, 14, 12)
        user_layout.setSpacing(6)

        status_row = QHBoxLayout()
        status_icon = QLabel("🛡️")
        status_icon.setStyleSheet("font-size: 18px;")
        status_row.addWidget(status_icon)

        status_text = QLabel("隐私保护")
        status_text.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 600;
        """)
        status_row.addWidget(status_text)
        status_row.addStretch()
        user_layout.addLayout(status_row)

        tip = QLabel("使用代理/VPN可隐藏真实IP")
        tip.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 11px;
        """)
        tip.setWordWrap(True)
        user_layout.addWidget(tip)

        layout.addWidget(info_frame)

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
        self.cursor = QCursor(Qt.PointingHandCursor)
        self.setCursor(self.cursor)
        self.color = color
        self.setMinimumHeight(36)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            MacOSButton {{
                background-color: {self.color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 20px;
            }}
            MacOSButton:hover {{
                background-color: {self.color}DD;
            }}
            MacOSButton:pressed {{
                background-color: {self.color}BB;
            }}
            MacOSButton:disabled {{
                background-color: {MacOSColors.SYSTEM_GRAY};
                color: white;
            }}
        """)


class MacOSSecondaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setStyleSheet(f"""
            MacOSSecondaryButton {{
                background-color: transparent;
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 20px;
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
        self.setFixedHeight(52)
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
            """)
            controls_layout.addWidget(btn)

        layout.addWidget(controls)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 600;
            margin-left: 10px;
        """)
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.status_badge = QLabel()
        self.status_badge.setFixedHeight(24)
        self.status_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {MacOSColors.GREEN_BG};
                color: {MacOSColors.SYSTEM_GREEN};
                border-radius: 12px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        self.status_badge.setText("● 网络正常")
        layout.addWidget(self.status_badge)


class IPInfoWorker(QThread):
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            info = {}
            try:
                with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    info["ip"] = data.get("ip", "未知")
            except:
                info["ip"] = "检测失败"

            try:
                with urllib.request.urlopen(f"https://ipapi.co/{info['ip']}/json/", timeout=8) as resp:
                    data = json.loads(resp.read().decode())
                    info["city"] = data.get("city", "未知")
                    info["region"] = data.get("region", "未知")
                    info["country"] = data.get("country_name", "未知")
                    info["org"] = data.get("org", "未知")
                    info["isp"] = data.get("isp", "未知")
                    info["timezone"] = data.get("timezone", "未知")
                    info["currency"] = data.get("currency", "未知")
            except:
                info["city"] = "未知"
                info["region"] = "未知"
                info["country"] = "未知"
                info["org"] = "未知"
                info["isp"] = "未知"
                info["timezone"] = "未知"
                info["currency"] = "未知"

            hostname = socket.gethostname()
            info["hostname"] = hostname
            try:
                local_ip = socket.gethostbyname(hostname)
                info["local_ip"] = local_ip
            except:
                info["local_ip"] = "未知"

            self.result_ready.emit(info)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ProxyDialog(QDialog):
    def __init__(self, parent=None, proxy_data=None):
        super().__init__(parent)
        self.setWindowTitle("添加/编辑代理")
        self.setFixedSize(420, 480)
        self.setStyleSheet(f"background-color: {MacOSColors.WINDOW_BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("代理服务器配置" if not proxy_data else "编辑代理配置")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 20px;
            font-weight: 700;
        """)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：美国节点1")
        self.name_edit.setMinimumHeight(36)
        self.name_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MacOSColors.CARD_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {MacOSColors.ACCENT};
            }}
        """)
        form.addRow("名称：", self.name_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["HTTP", "HTTPS", "SOCKS5", "SOCKS4"])
        self.type_combo.setMinimumHeight(36)
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {MacOSColors.CARD_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
            }}
        """)
        form.addRow("类型：", self.type_combo)

        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("例如：192.168.1.1 或 proxy.example.com")
        self.host_edit.setMinimumHeight(36)
        self.host_edit.setStyleSheet(self.name_edit.styleSheet())
        form.addRow("服务器：", self.host_edit)

        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(8080)
        self.port_edit.setMinimumHeight(36)
        self.port_edit.setStyleSheet(f"""
            QSpinBox {{
                background-color: {MacOSColors.CARD_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
            }}
        """)
        form.addRow("端口：", self.port_edit)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("（可选）用户名")
        self.user_edit.setMinimumHeight(36)
        self.user_edit.setStyleSheet(self.name_edit.styleSheet())
        form.addRow("用户名：", self.user_edit)

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("（可选）密码")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setMinimumHeight(36)
        self.pass_edit.setStyleSheet(self.name_edit.styleSheet())
        form.addRow("密码：", self.pass_edit)

        layout.addLayout(form)

        self.test_btn = MacOSSecondaryButton("🔍 测试连接")
        layout.addWidget(self.test_btn)

        self.test_result = QLabel("")
        self.test_result.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 12px;
            padding: 6px;
        """)
        self.test_result.setWordWrap(True)
        layout.addWidget(self.test_result)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.button(QDialogButtonBox.Ok).setStyleSheet(f"""
            QPushButton {{
                background-color: {MacOSColors.ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
            }}
        """)
        buttons.button(QDialogButtonBox.Cancel).setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {MacOSColors.TEXT_PRIMARY};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 8px 20px;
            }}
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.test_btn.clicked.connect(self.test_connection)

        if proxy_data:
            self.name_edit.setText(proxy_data.get("name", ""))
            idx = self.type_combo.findText(proxy_data.get("type", "HTTP"))
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            self.host_edit.setText(proxy_data.get("host", ""))
            self.port_edit.setValue(int(proxy_data.get("port", 8080)))
            self.user_edit.setText(proxy_data.get("username", ""))
            self.pass_edit.setText(proxy_data.get("password", ""))

    def test_connection(self):
        host = self.host_edit.text().strip()
        port = self.port_edit.value()
        if not host:
            self.test_result.setStyleSheet(f"color: {MacOSColors.SYSTEM_RED}; font-size: 12px;")
            self.test_result.setText("❌ 请先填写服务器地址")
            return

        self.test_result.setStyleSheet(f"color: {MacOSColors.SYSTEM_ORANGE}; font-size: 12px;")
        self.test_result.setText("⏳ 正在测试连接...")
        QApplication.processEvents()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                self.test_result.setStyleSheet(f"color: {MacOSColors.SYSTEM_GREEN}; font-size: 12px;")
                self.test_result.setText(f"✅ 连接成功！{host}:{port} 可访问")
            else:
                self.test_result.setStyleSheet(f"color: {MacOSColors.SYSTEM_RED}; font-size: 12px;")
                self.test_result.setText(f"❌ 连接失败！{host}:{port} 无法访问")
        except Exception as e:
            self.test_result.setStyleSheet(f"color: {MacOSColors.SYSTEM_RED}; font-size: 12px;")
            self.test_result.setText(f"❌ 测试出错：{str(e)}")

    def get_data(self):
        return {
            "name": self.name_edit.text().strip() or f"{self.type_combo.currentText()}_{self.host_edit.text()}",
            "type": self.type_combo.currentText(),
            "host": self.host_edit.text().strip(),
            "port": self.port_edit.value(),
            "username": self.user_edit.text().strip(),
            "password": self.pass_edit.text().strip(),
        }


class DashboardPage(QWidget):
    ip_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_ip_info = {}
        self.setup_ui()
        self.refresh_ip()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        welcome = QLabel("🛡️ IP状态面板")
        welcome.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 30px;
            font-weight: 700;
        """)
        main_layout.addWidget(welcome)

        desc = QLabel("实时监控您的网络状态和IP信息，快速切换保护隐私")
        desc.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 14px;
        """)
        main_layout.addWidget(desc)

        main_layout.addSpacing(4)

        ip_card = MacOSCard()
        ip_layout = QVBoxLayout(ip_card)
        ip_layout.setContentsMargins(28, 24, 28, 24)
        ip_layout.setSpacing(18)

        ip_header = QHBoxLayout()
        ip_title = QLabel("🌐 当前公网IP")
        ip_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 600;
        """)
        ip_header.addWidget(ip_title)
        ip_header.addStretch()

        self.refresh_btn = MacOSSecondaryButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_ip)
        ip_header.addWidget(self.refresh_btn)

        self.copy_btn = MacOSSecondaryButton("📋 复制")
        ip_header.addWidget(self.copy_btn)
        ip_layout.addLayout(ip_header)

        self.ip_label = QLabel("检测中...")
        self.ip_label.setStyleSheet(f"""
            color: {MacOSColors.ACCENT};
            font-size: 42px;
            font-weight: 800;
        """)
        ip_layout.addWidget(self.ip_label)

        self.location_label = QLabel("定位信息检测中...")
        self.location_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 14px;
        """)
        ip_layout.addWidget(self.location_label)

        self.isp_label = QLabel("")
        self.isp_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 13px;
        """)
        ip_layout.addWidget(self.isp_label)

        main_layout.addWidget(ip_card)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        self.local_ip_card = self.create_stat_card("🏠", "内网IP", "检测中", MacOSColors.ACCENT)
        self.proxy_card = self.create_stat_card("🔌", "代理状态", "未使用", MacOSColors.SYSTEM_ORANGE)
        self.hostname_card = self.create_stat_card("💻", "主机名", socket.gethostname(), MacOSColors.SYSTEM_PURPLE)
        self.speed_card = self.create_stat_card("⚡", "网络延迟", "检测中", MacOSColors.SYSTEM_GREEN)

        for card in [self.local_ip_card, self.proxy_card, self.hostname_card, self.speed_card]:
            stats_row.addWidget(card)
        main_layout.addLayout(stats_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(14)

        quick_actions = MacOSCard()
        qa_layout = QVBoxLayout(quick_actions)
        qa_layout.setContentsMargins(22, 18, 22, 18)
        qa_layout.setSpacing(12)

        qa_title = QLabel("⚡ 快捷操作")
        qa_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        qa_layout.addWidget(qa_title)

        actions = [
            ("🔌 切换代理", "快速启用/切换代理服务器", MacOSColors.ACCENT, 1),
            ("🔄 重置网络", "重置DNS和网络适配器", MacOSColors.SYSTEM_ORANGE, None),
            ("🕵️ 清除痕迹", "清除浏览器缓存和Cookie", MacOSColors.SYSTEM_PURPLE, None),
            ("🌐 切换网卡IP", "修改网卡静态IP地址", MacOSColors.SYSTEM_TEAL, 2),
            ("🔍 深度IP检测", "全面检测IP泄露风险", MacOSColors.SYSTEM_INDIGO, 3),
        ]

        for text, desc_text, color, tab_idx in actions:
            action_frame = QFrame()
            action_frame.setCursor(Qt.PointingHandCursor)
            action_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {color}08;
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    background-color: {color}18;
                }}
            """)
            if tab_idx is not None:
                action_frame.mousePressEvent = lambda e, idx=tab_idx: self.switch_tab(idx)

            afl = QHBoxLayout(action_frame)
            afl.setContentsMargins(14, 12, 14, 12)
            afl.setSpacing(12)

            btn_label = QLabel(text.split()[0])
            btn_label.setFixedSize(34, 34)
            btn_label.setAlignment(Qt.AlignCenter)
            btn_label.setStyleSheet(f"""
                background-color: {color}15;
                border-radius: 8px;
                font-size: 16px;
            """)
            afl.addWidget(btn_label)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            t = QLabel(text)
            t.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
            """)
            info_layout.addWidget(t)
            d = QLabel(desc_text)
            d.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 12px;
            """)
            info_layout.addWidget(d)
            afl.addLayout(info_layout)
            afl.addStretch()

            arrow = QLabel("›")
            arrow.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 22px;")
            afl.addWidget(arrow)

            qa_layout.addWidget(action_frame)

        qa_layout.addStretch()
        content_row.addWidget(quick_actions, 1)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(14)

        security_card = MacOSCard()
        sec_layout = QVBoxLayout(security_card)
        sec_layout.setContentsMargins(22, 18, 22, 18)
        sec_layout.setSpacing(12)

        sec_title = QLabel("🛡️ 安全建议")
        sec_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        sec_layout.addWidget(sec_title)

        tips = [
            ("✅", "切换IP后清除浏览器缓存"),
            ("✅", "每次操作间隔至少3-5分钟"),
            ("⚠️", "避免频繁切换同一账号"),
            ("💡", "建议使用高匿代理或VPN"),
        ]
        for icon, tip in tips:
            tl = QHBoxLayout()
            tl.setSpacing(8)
            il = QLabel(icon)
            il.setStyleSheet("font-size: 14px;")
            tl.addWidget(il)
            tt = QLabel(tip)
            tt.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 13px;
            """)
            tl.addWidget(tt)
            tl.addStretch()
            sec_layout.addLayout(tl)

        right_panel.addWidget(security_card)

        log_card = MacOSCard()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(22, 18, 22, 18)
        log_layout.setSpacing(10)

        log_title_row = QHBoxLayout()
        log_title = QLabel("📋 操作日志")
        log_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        log_title_row.addWidget(log_title)
        log_title_row.addStretch()
        clear_log_btn = QPushButton("清空")
        clear_log_btn.setCursor(Qt.PointingHandCursor)
        clear_log_btn.setStyleSheet(f"""
            QPushButton {{
                color: {MacOSColors.SYSTEM_RED};
                font-size: 12px;
                border: none;
                background: transparent;
            }}
        """)
        clear_log_btn.clicked.connect(lambda: self.log_view.clear())
        log_title_row.addWidget(clear_log_btn)
        log_layout.addLayout(log_title_row)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(140)
        self.log_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                color: {MacOSColors.TEXT_PRIMARY};
                font-family: Consolas, monospace;
            }}
        """)
        self.add_log("系统启动")
        log_layout.addWidget(self.log_view)

        right_panel.addWidget(log_card)

        right_container = QWidget()
        rc_layout = QVBoxLayout(right_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.addLayout(right_panel)
        content_row.addWidget(right_container, 1)

        main_layout.addLayout(content_row)
        main_layout.addStretch()

        self.copy_btn.clicked.connect(self.copy_ip)

    def create_stat_card(self, icon, label, value, color):
        card = MacOSCard()
        card.setMinimumHeight(110)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        header = QHBoxLayout()
        icon_l = QLabel(icon)
        icon_l.setStyleSheet("font-size: 18px;")
        header.addWidget(icon_l)
        header.addStretch()
        layout.addLayout(header)

        value_l = QLabel(value)
        value_l.setObjectName("value_label")
        value_l.setStyleSheet(f"""
            color: {color};
            font-size: 20px;
            font-weight: 700;
        """)
        value_l.setWordWrap(True)
        layout.addWidget(value_l)

        label_l = QLabel(label)
        label_l.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 12px;
        """)
        layout.addWidget(label_l)

        return card

    def refresh_ip(self):
        self.ip_label.setText("检测中...")
        self.ip_label.setStyleSheet(f"color: {MacOSColors.SYSTEM_ORANGE}; font-size: 42px; font-weight: 800;")
        self.location_label.setText("正在查询IP信息...")
        self.add_log("开始检测IP信息...")

        self.worker = IPInfoWorker()
        self.worker.result_ready.connect(self.on_ip_result)
        self.worker.error_occurred.connect(self.on_ip_error)
        self.worker.start()

        self.test_latency()

    def test_latency(self):
        def _test():
            try:
                import time
                start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect(("www.baidu.com", 80))
                sock.close()
                latency = int((time.time() - start) * 1000)
                QTimer.singleShot(0, lambda: self.update_latency(latency))
            except:
                QTimer.singleShot(0, lambda: self.update_latency(-1))

        threading.Thread(target=_test, daemon=True).start()

    def update_latency(self, latency):
        card = self.speed_card.findChild(QLabel, "value_label")
        if card:
            if latency < 0:
                card.setText("超时")
                card.setStyleSheet(f"color: {MacOSColors.SYSTEM_RED}; font-size: 20px; font-weight: 700;")
            else:
                card.setText(f"{latency} ms")
                color = MacOSColors.SYSTEM_GREEN if latency < 100 else (MacOSColors.SYSTEM_ORANGE if latency < 300 else MacOSColors.SYSTEM_RED)
                card.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 700;")

    def on_ip_result(self, info):
        self.current_ip_info = info
        self.ip_label.setText(info.get("ip", "未知"))
        self.ip_label.setStyleSheet(f"color: {MacOSColors.ACCENT}; font-size: 42px; font-weight: 800;")

        location_parts = []
        for key in ["country", "region", "city"]:
            v = info.get(key, "")
            if v and v != "未知":
                location_parts.append(v)
        location = " · ".join(location_parts) if location_parts else "未知位置"
        self.location_label.setText(f"📍 {location}")

        isp_parts = []
        for key in ["org", "isp"]:
            v = info.get(key, "")
            if v and v != "未知":
                isp_parts.append(v)
                break
        if isp_parts:
            self.isp_label.setText(f"🏢 {isp_parts[0]}")
        else:
            self.isp_label.setText("")

        local_card = self.local_ip_card.findChild(QLabel, "value_label")
        if local_card:
            local_card.setText(info.get("local_ip", "未知"))

        self.ip_updated.emit(info)
        self.add_log(f"IP检测完成: {info.get('ip', '未知')}")

    def on_ip_error(self, error):
        self.ip_label.setText("检测失败")
        self.ip_label.setStyleSheet(f"color: {MacOSColors.SYSTEM_RED}; font-size: 42px; font-weight: 800;")
        self.location_label.setText("请检查网络连接")
        self.add_log(f"IP检测失败: {error}")

    def copy_ip(self):
        ip = self.ip_label.text()
        if ip and ip not in ["检测中...", "检测失败", "未知"]:
            clipboard = QApplication.clipboard()
            clipboard.setText(ip)
            self.add_log(f"IP已复制: {ip}")

    def add_log(self, msg):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_view.append(f"[{time_str}] {msg}")
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def switch_tab(self, idx):
        window = self.window()
        if hasattr(window, 'sidebar'):
            window.sidebar.set_active_tab(idx)


class ProxyPage(QWidget):
    apply_proxy_signal = pyqtSignal(dict)
    clear_proxy_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proxies = []
        self.current_active = None
        self.config_file = os.path.join(os.path.expanduser("~"), ".ip_tool_proxies.json")
        self.load_proxies()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title_info = QVBoxLayout()
        title_info.setSpacing(4)
        title = QLabel("🔌 代理切换管理")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        title_info.addWidget(title)
        desc = QLabel("管理和快速切换代理服务器，突破IP限制")
        desc.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 14px;
        """)
        title_info.addWidget(desc)
        header.addLayout(title_info)
        header.addStretch()

        self.add_btn = MacOSButton("➕ 添加代理", MacOSColors.ACCENT)
        self.add_btn.clicked.connect(self.add_proxy)
        header.addWidget(self.add_btn)

        self.import_btn = MacOSSecondaryButton("📥 批量导入")
        self.import_btn.clicked.connect(self.import_proxies)
        header.addWidget(self.import_btn)

        layout.addLayout(header)

        quick_bar = MacOSCard()
        qb_layout = QHBoxLayout(quick_bar)
        qb_layout.setContentsMargins(18, 14, 18, 14)
        qb_layout.setSpacing(12)

        self.current_status_label = QLabel("当前状态：未使用代理")
        self.current_status_label.setStyleSheet(f"""
            color: {MacOSColors.SYSTEM_GRAY};
            font-size: 14px;
            font-weight: 600;
        """)
        qb_layout.addWidget(self.current_status_label)
        qb_layout.addStretch()

        self.disable_proxy_btn = MacOSButton("🚫 关闭代理", MacOSColors.SYSTEM_RED)
        self.disable_proxy_btn.clicked.connect(self.clear_proxy)
        self.disable_proxy_btn.setEnabled(False)
        qb_layout.addWidget(self.disable_proxy_btn)

        self.test_all_btn = MacOSSecondaryButton("🧪 测试全部")
        self.test_all_btn.clicked.connect(self.test_all_proxies)
        qb_layout.addWidget(self.test_all_btn)

        layout.addWidget(quick_bar)

        table_card = MacOSCard()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["状态", "名称", "类型", "服务器", "端口", "延迟", "操作"])
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {MacOSColors.CARD_BG};
                border-radius: 12px;
                font-size: 13px;
                color: {MacOSColors.TEXT_PRIMARY};
                selection-background-color: {MacOSColors.ACCENT_BG};
            }}
            QTableWidget::item {{
                padding: 10px 8px;
                border: none;
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: {MacOSColors.TEXT_SECONDARY};
                padding: 12px 10px;
                border: none;
                border-bottom: 1px solid {MacOSColors.SEPARATOR};
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() + f"""
            QTableWidget {{
                alternate-background-color: {MacOSColors.SIDEBAR_BG}40;
            }}
        """)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

        self.refresh_table()

    def load_proxies(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.proxies = json.load(f)
            except:
                self.proxies = []

        if not self.proxies:
            self.proxies = [
                {"name": "示例-本地HTTP", "type": "HTTP", "host": "127.0.0.1", "port": 7890, "username": "", "password": "", "latency": None},
                {"name": "示例-本地SOCKS5", "type": "SOCKS5", "host": "127.0.0.1", "port": 1080, "username": "", "password": "", "latency": None},
            ]
            self.save_proxies()

    def save_proxies(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.proxies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存失败: {e}")

    def refresh_table(self):
        self.table.setRowCount(len(self.proxies))
        for row, proxy in enumerate(self.proxies):
            status_icon = "🔴"
            if self.current_active is not None and self.current_active == row:
                status_icon = "🟢"

            status_item = QTableWidgetItem(status_icon)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, status_item)

            name_item = QTableWidgetItem(proxy.get("name", ""))
            name_item.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold if self.current_active == row else QFont.Normal))
            self.table.setItem(row, 1, name_item)

            type_item = QTableWidgetItem(proxy.get("type", "HTTP"))
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, type_item)

            host_item = QTableWidgetItem(proxy.get("host", ""))
            self.table.setItem(row, 3, host_item)

            port_item = QTableWidgetItem(str(proxy.get("port", "")))
            port_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, port_item)

            latency = proxy.get("latency")
            if latency is None:
                lat_text = "—"
                lat_color = MacOSColors.TEXT_SECONDARY
            elif latency < 0:
                lat_text = "超时"
                lat_color = MacOSColors.SYSTEM_RED
            else:
                lat_text = f"{latency}ms"
                lat_color = MacOSColors.SYSTEM_GREEN if latency < 150 else (MacOSColors.SYSTEM_ORANGE if latency < 400 else MacOSColors.SYSTEM_RED)
            lat_item = QTableWidgetItem(lat_text)
            lat_item.setTextAlignment(Qt.AlignCenter)
            lat_item.setForeground(QColor(lat_color))
            self.table.setItem(row, 5, lat_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(6)

            apply_btn = QPushButton("启用")
            apply_btn.setCursor(Qt.PointingHandCursor)
            apply_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {MacOSColors.SYSTEM_GREEN};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {MacOSColors.SYSTEM_GREEN}DD;
                }}
            """)
            apply_btn.clicked.connect(lambda checked=False, r=row: self.apply_proxy(r))
            actions_layout.addWidget(apply_btn)

            test_btn = QPushButton("测试")
            test_btn.setCursor(Qt.PointingHandCursor)
            test_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {MacOSColors.ACCENT};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {MacOSColors.ACCENT}DD;
                }}
            """)
            test_btn.clicked.connect(lambda checked=False, r=row: self.test_proxy(r))
            actions_layout.addWidget(test_btn)

            edit_btn = QPushButton("编辑")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {MacOSColors.TEXT_PRIMARY};
                    border: 1px solid {MacOSColors.SEPARATOR};
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {MacOSColors.SIDEBAR_BG};
                }}
            """)
            edit_btn.clicked.connect(lambda checked=False, r=row: self.edit_proxy(r))
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton("删除")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {MacOSColors.SYSTEM_RED};
                    border: none;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    text-decoration: underline;
                }}
            """)
            del_btn.clicked.connect(lambda checked=False, r=row: self.delete_proxy(r))
            actions_layout.addWidget(del_btn)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 6, actions_widget)

        self.table.setColumnWidth(6, 240)

    def add_proxy(self):
        dlg = ProxyDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if data["host"]:
                self.proxies.append(data)
                self.save_proxies()
                self.refresh_table()

    def edit_proxy(self, row):
        if 0 <= row < len(self.proxies):
            dlg = ProxyDialog(self, self.proxies[row])
            if dlg.exec_() == QDialog.Accepted:
                self.proxies[row] = dlg.get_data()
                self.save_proxies()
                self.refresh_table()

    def delete_proxy(self, row):
        if 0 <= row < len(self.proxies):
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除代理「{self.proxies[row].get('name', '')}」吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if self.current_active == row:
                    self.current_active = None
                    self.clear_proxy()
                del self.proxies[row]
                self.save_proxies()
                self.refresh_table()

    def test_proxy(self, row):
        if 0 <= row < len(self.proxies):
            proxy = self.proxies[row]
            self.proxies[row]["latency"] = None
            self.refresh_table()
            QApplication.processEvents()

            def _test():
                try:
                    import time
                    start = time.time()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((proxy["host"], int(proxy["port"])))
                    sock.close()
                    latency = int((time.time() - start) * 1000) if result == 0 else -1
                    QTimer.singleShot(0, lambda: self._update_latency(row, latency))
                except:
                    QTimer.singleShot(0, lambda: self._update_latency(row, -1))

            threading.Thread(target=_test, daemon=True).start()

    def _update_latency(self, row, latency):
        if 0 <= row < len(self.proxies):
            self.proxies[row]["latency"] = latency
            self.save_proxies()
            self.refresh_table()

    def test_all_proxies(self):
        for i in range(len(self.proxies)):
            self.test_proxy(i)

    def apply_proxy(self, row):
        if 0 <= row < len(self.proxies):
            proxy = self.proxies[row]
            self.current_active = row
            self.disable_proxy_btn.setEnabled(True)

            status_text = f"当前状态：✅ 使用代理 {proxy.get('name', '')} ({proxy.get('type', '')}://{proxy.get('host', '')}:{proxy.get('port', '')})"
            self.current_status_label.setText(status_text)
            self.current_status_label.setStyleSheet(f"""
                color: {MacOSColors.SYSTEM_GREEN};
                font-size: 14px;
                font-weight: 600;
            """)

            self.apply_proxy_signal.emit(proxy)
            self.set_system_proxy(proxy)
            self.refresh_table()

    def set_system_proxy(self, proxy):
        if sys.platform.startswith("win"):
            try:
                proxy_url = f"{proxy.get('host', '')}:{proxy.get('port', '')}"
                enable_cmd = f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f'
                proxy_cmd = f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer /t REG_SZ /d "{proxy_url}" /f'
                subprocess.run(enable_cmd, shell=True, capture_output=True)
                subprocess.run(proxy_cmd, shell=True, capture_output=True)
            except Exception as e:
                print(f"设置系统代理失败: {e}")

    def clear_proxy(self):
        self.current_active = None
        self.disable_proxy_btn.setEnabled(False)
        self.current_status_label.setText("当前状态：未使用代理")
        self.current_status_label.setStyleSheet(f"""
            color: {MacOSColors.SYSTEM_GRAY};
            font-size: 14px;
            font-weight: 600;
        """)
        self.clear_proxy_signal.emit()
        self.clear_system_proxy()
        self.refresh_table()

    def clear_system_proxy(self):
        if sys.platform.startswith("win"):
            try:
                disable_cmd = f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f'
                subprocess.run(disable_cmd, shell=True, capture_output=True)
            except Exception as e:
                print(f"关闭系统代理失败: {e}")

    def import_proxies(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择代理配置文件", "",
            "JSON文件 (*.json);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        if not file_path:
            return

        try:
            count_before = len(self.proxies)
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "host" in item:
                                self.proxies.append({
                                    "name": item.get("name", f"导入_{item.get('host', '')}"),
                                    "type": item.get("type", "HTTP"),
                                    "host": item["host"],
                                    "port": int(item.get("port", 8080)),
                                    "username": item.get("username", ""),
                                    "password": item.get("password", ""),
                                    "latency": None,
                                })
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        m = re.match(r'(\w+)://([^:]+):(\d+)', line)
                        if m:
                            ptype, host, port = m.groups()
                            self.proxies.append({
                                "name": f"{ptype}_{host}:{port}",
                                "type": ptype.upper(),
                                "host": host,
                                "port": int(port),
                                "username": "",
                                "password": "",
                                "latency": None,
                            })
                        else:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                host = parts[0]
                                port = int(parts[1]) if parts[1].isdigit() else 8080
                                self.proxies.append({
                                    "name": f"{host}:{port}",
                                    "type": "HTTP",
                                    "host": host,
                                    "port": port,
                                    "username": "",
                                    "password": "",
                                    "latency": None,
                                })

            self.save_proxies()
            self.refresh_table()
            added = len(self.proxies) - count_before
            QMessageBox.information(self, "导入成功", f"成功导入 {added} 个代理配置！")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入出错：{str(e)}")


class NetworkConfigPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.adapters = []
        self.setup_ui()
        self.load_adapters()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("🌐 网卡IP配置")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        header.addWidget(title)
        desc = QLabel("修改网络适配器的IP地址、子网掩码和DNS配置")
        desc.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 14px;
        """)
        header.addWidget(desc)
        layout.addLayout(header)

        config_card = MacOSCard()
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(24, 20, 24, 20)
        config_layout.setSpacing(18)

        select_row = QHBoxLayout()
        select_label = QLabel("选择网络适配器：")
        select_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 600;
        """)
        select_row.addWidget(select_label)

        self.adapter_combo = QComboBox()
        self.adapter_combo.setMinimumHeight(36)
        self.adapter_combo.setMinimumWidth(300)
        self.adapter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
            }}
        """)
        self.adapter_combo.currentIndexChanged.connect(self.on_adapter_changed)
        select_row.addWidget(self.adapter_combo)
        select_row.addStretch()

        self.refresh_btn = MacOSSecondaryButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.load_adapters)
        select_row.addWidget(self.refresh_btn)

        config_layout.addLayout(select_row)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.mode_group = QButtonGroup(self)
        mode_row = QHBoxLayout()
        mode_row.setSpacing(20)

        self.dhcp_radio = QRadioButton("自动获取IP (DHCP)")
        self.dhcp_radio.setCursor(Qt.PointingHandCursor)
        self.dhcp_radio.setChecked(True)
        self.dhcp_radio.toggled.connect(self.on_mode_changed)
        self.dhcp_radio.setStyleSheet(f"""
            QRadioButton {{
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 14px;
                spacing: 8px;
            }}
        """)
        self.mode_group.addButton(self.dhcp_radio, 0)
        mode_row.addWidget(self.dhcp_radio)

        self.static_radio = QRadioButton("使用下面的IP地址")
        self.static_radio.setCursor(Qt.PointingHandCursor)
        self.static_radio.setStyleSheet(self.dhcp_radio.styleSheet())
        self.mode_group.addButton(self.static_radio, 1)
        mode_row.addWidget(self.static_radio)
        mode_row.addStretch()

        form.addRow("IP获取方式：", self._wrap_row(mode_row))

        ip_style = f"""
            QLineEdit {{
                background-color: {MacOSColors.CARD_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 14px;
                min-height: 36px;
            }}
            QLineEdit:focus {{
                border: 1px solid {MacOSColors.ACCENT};
            }}
            QLineEdit:disabled {{
                background-color: {MacOSColors.SIDEBAR_BG};
                color: {MacOSColors.TEXT_SECONDARY};
            }}
        """

        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("例如：192.168.1.100")
        self.ip_edit.setStyleSheet(ip_style)
        self.ip_edit.setEnabled(False)
        form.addRow("IP地址：", self.ip_edit)

        self.mask_edit = QLineEdit()
        self.mask_edit.setPlaceholderText("例如：255.255.255.0")
        self.mask_edit.setText("255.255.255.0")
        self.mask_edit.setStyleSheet(ip_style)
        self.mask_edit.setEnabled(False)
        form.addRow("子网掩码：", self.mask_edit)

        self.gateway_edit = QLineEdit()
        self.gateway_edit.setPlaceholderText("例如：192.168.1.1")
        self.gateway_edit.setStyleSheet(ip_style)
        self.gateway_edit.setEnabled(False)
        form.addRow("默认网关：", self.gateway_edit)

        dns_group_label = QLabel("DNS服务器地址")
        dns_group_label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 600;
            margin-top: 8px;
        """)
        form.addRow("", dns_group_label)

        self.dhcp_dns_radio = QRadioButton("自动获取DNS")
        self.dhcp_dns_radio.setCursor(Qt.PointingHandCursor)
        self.dhcp_dns_radio.setChecked(True)
        self.dhcp_dns_radio.toggled.connect(self.on_dns_mode_changed)
        self.dhcp_dns_radio.setStyleSheet(self.dhcp_radio.styleSheet())
        form.addRow("DNS获取：", self.dhcp_dns_radio)

        self.static_dns_radio = QRadioButton("使用下面的DNS服务器")
        self.static_dns_radio.setCursor(Qt.PointingHandCursor)
        self.static_dns_radio.setStyleSheet(self.dhcp_radio.styleSheet())
        form.addRow("", self.static_dns_radio)

        self.dns1_edit = QLineEdit()
        self.dns1_edit.setPlaceholderText("首选DNS 例如：8.8.8.8")
        self.dns1_edit.setStyleSheet(ip_style)
        self.dns1_edit.setEnabled(False)
        form.addRow("首选DNS：", self.dns1_edit)

        self.dns2_edit = QLineEdit()
        self.dns2_edit.setPlaceholderText("备用DNS 例如：114.114.114.114")
        self.dns2_edit.setStyleSheet(ip_style)
        self.dns2_edit.setEnabled(False)
        form.addRow("备用DNS：", self.dns2_edit)

        config_layout.addLayout(form)

        dns_presets = QGroupBox("快速选择DNS")
        dns_presets.setStyleSheet(f"""
            QGroupBox {{
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 600;
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
            }}
        """)
        dns_layout = QGridLayout(dns_presets)
        dns_layout.setSpacing(10)

        dns_options = [
            ("阿里DNS", "223.5.5.5", "223.6.6.6", MacOSColors.ACCENT),
            ("腾讯DNS", "119.29.29.29", "182.254.116.116", MacOSColors.SYSTEM_GREEN),
            ("百度DNS", "180.76.76.76", "", MacOSColors.SYSTEM_ORANGE),
            ("Google DNS", "8.8.8.8", "8.8.4.4", MacOSColors.SYSTEM_PURPLE),
            ("114 DNS", "114.114.114.114", "114.114.115.115", MacOSColors.SYSTEM_TEAL),
        ]

        for i, (name, dns1, dns2, color) in enumerate(dns_options):
            btn = QPushButton(f"🌐 {name}\n{dns1}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}08;
                    color: {MacOSColors.TEXT_PRIMARY};
                    border: 1px solid {color}30;
                    border-radius: 8px;
                    padding: 10px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {color}18;
                    border: 1px solid {color}50;
                }}
            """)
            btn.clicked.connect(lambda checked=False, d1=dns1, d2=dns2: self.apply_dns_preset(d1, d2))
            dns_layout.addWidget(btn, i // 3, i % 3)

        config_layout.addWidget(dns_presets)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self.reset_btn = MacOSSecondaryButton("🔄 重置为DHCP")
        self.reset_btn.clicked.connect(self.reset_to_dhcp)
        btn_row.addWidget(self.reset_btn)

        self.flushdns_btn = MacOSSecondaryButton("🔧 刷新DNS缓存")
        self.flushdns_btn.clicked.connect(self.flush_dns)
        btn_row.addWidget(self.flushdns_btn)

        self.apply_btn = MacOSButton("✅ 应用配置", MacOSColors.SYSTEM_GREEN)
        self.apply_btn.clicked.connect(self.apply_config)
        btn_row.addWidget(self.apply_btn)

        config_layout.addLayout(btn_row)
        layout.addWidget(config_card)

        info_card = MacOSCard()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(22, 18, 22, 18)
        info_layout.setSpacing(10)

        info_title = QLabel("💡 使用说明")
        info_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        info_layout.addWidget(info_title)

        tips = [
            "1. 修改网卡配置需要管理员权限，请以管理员身份运行本程序",
            "2. 如果不确定IP地址，请保持DHCP自动获取，仅修改DNS即可",
            "3. 切换网卡IP适合有多个静态IP可用的场景（如公司内网、多线路环境）",
            "4. 家庭宽带用户建议使用【代理切换】或重启路由器获取新IP",
            "5. 应用配置后网络会短暂断开，请保存好正在进行的工作",
        ]
        for tip in tips:
            tl = QLabel(tip)
            tl.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 13px;
                padding: 2px 0;
            """)
            tl.setWordWrap(True)
            info_layout.addWidget(tl)

        layout.addWidget(info_card)
        layout.addStretch()

    def _wrap_row(self, row_layout):
        w = QWidget()
        w.setLayout(row_layout)
        return w

    def load_adapters(self):
        self.adapter_combo.clear()
        self.adapters = []
        try:
            if sys.platform.startswith("win"):
                result = subprocess.run(
                    ["wmic", "nic", "where", "NetEnabled=True", "get", "Name,Index", "/format:list"],
                    capture_output=True, text=True, encoding='gbk', errors='replace', timeout=15
                )
                lines = result.stdout.strip().split('\n')
                current = {}
                for line in lines:
                    line = line.strip()
                    if '=' in line:
                        key, val = line.split('=', 1)
                        current[key.strip()] = val.strip()
                        if 'Name' in current and 'Index' in current:
                            try:
                                idx = int(current['Index'])
                                name = current['Name']
                                self.adapters.append((idx, name))
                                self.adapter_combo.addItem(f"📶 {name}", idx)
                                current = {}
                            except:
                                current = {}
            if not self.adapters:
                hostname = socket.gethostname()
                self.adapters.append((0, "默认网络适配器"))
                self.adapter_combo.addItem("📶 默认网络适配器", 0)
        except Exception as e:
            self.adapters.append((0, "默认网络适配器"))
            self.adapter_combo.addItem("📶 默认网络适配器", 0)

    def on_adapter_changed(self, idx):
        pass

    def on_mode_changed(self, checked):
        is_static = self.static_radio.isChecked()
        self.ip_edit.setEnabled(is_static)
        self.mask_edit.setEnabled(is_static)
        self.gateway_edit.setEnabled(is_static)

    def on_dns_mode_changed(self, checked):
        use_static = self.static_dns_radio.isChecked()
        self.dns1_edit.setEnabled(use_static)
        self.dns2_edit.setEnabled(use_static)

    def apply_dns_preset(self, dns1, dns2):
        self.static_dns_radio.setChecked(True)
        self.dns1_edit.setText(dns1)
        self.dns2_edit.setText(dns2 or "")

    def reset_to_dhcp(self):
        self.dhcp_radio.setChecked(True)
        self.dhcp_dns_radio.setChecked(True)
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要将网卡重置为自动获取IP和DNS吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._run_netsh("dhcp", "dhcp")

    def flush_dns(self):
        try:
            if sys.platform.startswith("win"):
                subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=10)
            QMessageBox.information(self, "完成", "DNS缓存已刷新！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新失败：{str(e)}")

    def apply_config(self):
        adapter_idx = self.adapter_combo.currentData()
        adapter_name = self.adapter_combo.currentText().replace("📶 ", "").strip()

        use_static_ip = self.static_radio.isChecked()
        use_static_dns = self.static_dns_radio.isChecked()

        if use_static_ip:
            ip = self.ip_edit.text().strip()
            mask = self.mask_edit.text().strip() or "255.255.255.0"
            gateway = self.gateway_edit.text().strip()
            if not ip:
                QMessageBox.warning(self, "提示", "请填写IP地址")
                return
        else:
            ip = mask = gateway = None

        dns1 = self.dns1_edit.text().strip() if use_static_dns else None
        dns2 = self.dns2_edit.text().strip() if use_static_dns else None

        reply = QMessageBox.question(
            self, "确认应用",
            f"即将对网卡「{adapter_name}」应用以下配置：\n\n"
            f"IP方式：{'静态IP' if use_static_ip else '自动获取(DHCP)'}\n"
            + (f"IP地址：{ip}\n子网掩码：{mask}\n网关：{gateway or '无'}\n" if use_static_ip else "")
            + f"\nDNS方式：{'静态DNS' if use_static_dns else '自动获取'}\n"
            + (f"首选DNS：{dns1}\n备用DNS：{dns2 or '无'}" if use_static_dns else "")
            + "\n\n确定要继续吗？（网络会短暂断开）",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self._run_netsh(
            "static" if use_static_ip else "dhcp",
            "static" if use_static_dns else "dhcp",
            adapter_name, ip, mask, gateway, dns1, dns2
        )

    def _run_netsh(self, ip_mode, dns_mode, adapter_name="以太网", ip=None, mask=None, gateway=None, dns1=None, dns2=None):
        try:
            if not sys.platform.startswith("win"):
                QMessageBox.information(self, "提示", "此功能仅支持Windows系统")
                return

            admin_test = subprocess.run(["net", "session"], capture_output=True, shell=True)
            if admin_test.returncode != 0:
                QMessageBox.warning(
                    self, "权限不足",
                    "修改网卡配置需要管理员权限！\n\n请右键点击脚本，选择「以管理员身份运行」"
                )
                return

            if ip_mode == "dhcp":
                subprocess.run(
                    f'netsh interface ip set address "{adapter_name}" dhcp',
                    shell=True, capture_output=True, timeout=15
                )
            else:
                cmd = f'netsh interface ip set address "{adapter_name}" static {ip} {mask}'
                if gateway:
                    cmd += f" {gateway} 1"
                subprocess.run(cmd, shell=True, capture_output=True, timeout=15)

            if dns_mode == "dhcp":
                subprocess.run(
                    f'netsh interface ip set dns "{adapter_name}" dhcp',
                    shell=True, capture_output=True, timeout=15
                )
            else:
                if dns1:
                    subprocess.run(
                        f'netsh interface ip set dns "{adapter_name}" static {dns1} primary',
                        shell=True, capture_output=True, timeout=15
                    )
                if dns2:
                    subprocess.run(
                        f'netsh interface ip add dns "{adapter_name}" {dns2} index=2',
                        shell=True, capture_output=True, timeout=15
                    )

            self.flush_dns()
            QMessageBox.information(self, "成功", "网络配置已应用！\n如果无法上网，请稍等10-30秒或重启网卡。")
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "超时", "配置命令执行超时，请检查网卡名称是否正确")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"配置失败：{str(e)}")


class IPCheckPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("🔍 IP检测与分析")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        header.addWidget(title)
        desc = QLabel("全面检测IP泄露风险，验证代理是否生效，检查隐私安全")
        desc.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 14px;
        """)
        header.addWidget(desc)
        layout.addLayout(header)

        action_bar = MacOSCard()
        ab_layout = QHBoxLayout(action_bar)
        ab_layout.setContentsMargins(18, 14, 18, 14)
        ab_layout.setSpacing(12)

        self.check_btn = MacOSButton("🚀 开始全面检测", MacOSColors.ACCENT)
        self.check_btn.clicked.connect(self.run_check)
        ab_layout.addWidget(self.check_btn)

        self.quick_btn = MacOSSecondaryButton("⚡ 快速查IP")
        self.quick_btn.clicked.connect(self.quick_check)
        ab_layout.addWidget(self.quick_btn)

        self.dnsleak_btn = MacOSSecondaryButton("🌊 DNS泄露测试")
        ab_layout.addWidget(self.dnsleak_btn)

        ab_layout.addStretch()

        self.progress = QProgressBar()
        self.progress.setFixedWidth(200)
        self.progress.setFixedHeight(24)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: none;
                border-radius: 12px;
            }}
            QProgressBar::chunk {{
                background-color: {MacOSColors.ACCENT};
                border-radius: 12px;
            }}
        """)
        ab_layout.addWidget(self.progress)

        layout.addWidget(action_bar)

        content = QHBoxLayout()
        content.setSpacing(14)

        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        self.ip_card = self._create_info_card(
            "🌐 IP地址信息",
            [("公网IPv4", "待检测", MacOSColors.ACCENT, True),
             ("本地IPv4", "待检测", MacOSColors.SYSTEM_TEAL),
             ("定位信息", "待检测", MacOSColors.SYSTEM_PURPLE),
             ("ISP运营商", "待检测", MacOSColors.SYSTEM_ORANGE),
             ("组织/机构", "待检测", MacOSColors.SYSTEM_GRAY2)],
            1.2
        )
        left_col.addWidget(self.ip_card, 1)

        security_card = MacOSCard()
        sec_layout = QVBoxLayout(security_card)
        sec_layout.setContentsMargins(22, 18, 22, 18)
        sec_layout.setSpacing(12)

        sec_header = QHBoxLayout()
        sec_title = QLabel("🛡️ 隐私安全检测")
        sec_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        sec_header.addWidget(sec_title)
        sec_header.addStretch()
        self.score_label = QLabel("隐私评分: --")
        self.score_label.setStyleSheet(f"""
            color: {MacOSColors.SYSTEM_GRAY};
            font-size: 14px;
            font-weight: 700;
        """)
        sec_header.addWidget(self.score_label)
        sec_layout.addLayout(sec_header)

        self.security_items = [
            ("代理/VPN使用", "待检测", None),
            ("WebRTC泄露风险", "待检测", None),
            ("DNS泄露风险", "待检测", None),
            ("Canvas指纹", "待检测", None),
            ("真实IP隐藏", "待检测", None),
        ]
        self.security_widgets = []
        for name, status, _ in self.security_items:
            row = QFrame()
            row.setStyleSheet(f"""
                QFrame {{
                    background-color: {MacOSColors.SIDEBAR_BG}40;
                    border-radius: 8px;
                }}
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)
            row_layout.setSpacing(10)

            icon = QLabel("❓")
            icon.setFixedSize(22, 22)
            icon.setAlignment(Qt.AlignCenter)
            row_layout.addWidget(icon)

            name_l = QLabel(name)
            name_l.setStyleSheet(f"""
                color: {MacOSColors.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 500;
            """)
            row_layout.addWidget(name_l)
            row_layout.addStretch()

            status_l = QLabel(status)
            status_l.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
            """)
            row_layout.addWidget(status_l)

            sec_layout.addWidget(row)
            self.security_widgets.append((icon, status_l))
        left_col.addWidget(security_card, 1)

        content.addLayout(left_col, 1)

        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        tech_card = MacOSCard()
        tech_layout = QVBoxLayout(tech_card)
        tech_layout.setContentsMargins(22, 18, 22, 18)
        tech_layout.setSpacing(10)

        tech_title = QLabel("📡 网络技术信息")
        tech_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        tech_layout.addWidget(tech_title)

        self.tech_info = QTextEdit()
        self.tech_info.setReadOnly(True)
        self.tech_info.setMinimumHeight(220)
        self.tech_info.setStyleSheet(f"""
            QTextEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                color: {MacOSColors.TEXT_PRIMARY};
                font-family: Consolas, 'Courier New', monospace;
            }}
        """)
        self.tech_info.setPlainText("点击「开始全面检测」按钮查看技术信息...")
        tech_layout.addWidget(self.tech_info)
        right_col.addWidget(tech_card, 1)

        log_card = MacOSCard()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(22, 18, 22, 18)
        log_layout.setSpacing(8)

        log_title = QLabel("📋 检测日志")
        log_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        log_layout.addWidget(log_title)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(160)
        self.log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                color: {MacOSColors.TEXT_PRIMARY};
                font-family: Consolas, monospace;
            }}
        """)
        self.log.setPlainText("[系统] IP检测模块已就绪\n")
        log_layout.addWidget(self.log)

        right_col.addWidget(log_card, 1)

        right_container = QWidget()
        rc_l = QVBoxLayout(right_container)
        rc_l.setContentsMargins(0, 0, 0, 0)
        rc_l.addLayout(right_col)
        content.addWidget(right_container, 1)

        layout.addLayout(content, 1)

    def _create_info_card(self, title, items, scale=1.0):
        card = MacOSCard()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, int(18*scale), 22, int(18*scale))
        layout.setSpacing(int(10*scale))

        t = QLabel(title)
        t.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: {int(18*scale)}px;
            font-weight: 600;
        """)
        layout.addWidget(t)

        self.ip_info_labels = {}
        for name, default, color, *args in items:
            row = QHBoxLayout()
            row.setSpacing(10)
            nl = QLabel(name)
            nl.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY};
                font-size: {int(13*scale)}px;
                min-width: 90px;
            """)
            row.addWidget(nl)
            row.addStretch()
            vl = QLabel(default)
            vl.setStyleSheet(f"""
                color: {color};
                font-size: {int(13*scale)}px;
                font-weight: {'700' if args else '600'};
            """)
            row.addWidget(vl)
            layout.addLayout(row)
            self.ip_info_labels[name] = vl

        return card

    def add_log(self, msg):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{time_str}] {msg}")
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def quick_check(self):
        self.progress.setValue(0)
        self.add_log("⚡ 开始快速IP检测...")
        self.progress.setValue(30)
        QApplication.processEvents()

        worker = IPInfoWorker()
        worker.result_ready.connect(self.on_quick_result)
        worker.error_occurred.connect(lambda e: (self.add_log(f"❌ 检测失败: {e}"), self.progress.setValue(0)))
        worker.start()

    def on_quick_result(self, info):
        self.progress.setValue(60)
        self.ip_info_labels["公网IPv4"].setText(info.get("ip", "未知"))
        local_ip = info.get("local_ip", socket.gethostbyname(socket.gethostname()))
        self.ip_info_labels["本地IPv4"].setText(local_ip)
        loc_parts = []
        for k in ["country", "region", "city"]:
            v = info.get(k, "")
            if v and v != "未知":
                loc_parts.append(v)
        self.ip_info_labels["定位信息"].setText(" · ".join(loc_parts) if loc_parts else "未知")
        self.ip_info_labels["ISP运营商"].setText(info.get("isp", "未知"))
        self.ip_info_labels["组织/机构"].setText(info.get("org", "未知"))
        self.progress.setValue(100)
        self.add_log(f"✅ 公网IP: {info.get('ip', '未知')}")
        self.add_log(f"📍 位置: {' · '.join(loc_parts) if loc_parts else '未知'}")
        QTimer.singleShot(1500, lambda: self.progress.setValue(0))

    def run_check(self):
        self.progress.setValue(0)
        self.add_log("🚀 开始全面IP隐私检测...")
        self.check_btn.setEnabled(False)
        QApplication.processEvents()

        for i in range(5):
            self.security_widgets[i][0].setText("⏳")
            self.security_widgets[i][1].setText("检测中...")
            self.security_widgets[i][1].setStyleSheet(f"color: {MacOSColors.SYSTEM_ORANGE}; font-size: 13px; font-weight: 600;")

        tech_builder = []
        tech_builder.append("=" * 50)
        tech_builder.append("IP 全面检测报告")
        tech_builder.append("=" * 50)
        tech_builder.append(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        tech_builder.append(f"主机名: {socket.gethostname()}")
        tech_builder.append("")

        self.progress.setValue(10)
        self.add_log("[1/6] 获取公网IP信息...")
        QApplication.processEvents()

        ip_info = {}
        try:
            with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=8) as resp:
                ip_info = json.loads(resp.read().decode())
        except Exception as e:
            self.add_log(f"⚠️  ipify失败: {e}")

        try:
            if "ip" in ip_info:
                with urllib.request.urlopen(f"https://ipapi.co/{ip_info['ip']}/json/", timeout=10) as resp:
                    detail = json.loads(resp.read().decode())
                    ip_info.update(detail)
        except Exception as e:
            self.add_log(f"⚠️  详细信息获取失败: {e}")

        self.progress.setValue(30)
        self.ip_info_labels["公网IPv4"].setText(ip_info.get("ip", "检测失败"))
        local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
            except:
                pass
        self.ip_info_labels["本地IPv4"].setText(local_ip)
        loc_parts = [ip_info.get(k, "") for k in ["country_name", "region", "city"] if ip_info.get(k, "") and ip_info.get(k) != "未知"]
        self.ip_info_labels["定位信息"].setText(" · ".join(loc_parts) if loc_parts else "未知/保护中")
        self.ip_info_labels["ISP运营商"].setText(ip_info.get("isp", "未知/保护中"))
        self.ip_info_labels["组织/机构"].setText(ip_info.get("org", "未知/保护中"))

        tech_builder.append(f"公网IP: {ip_info.get('ip', 'N/A')}")
        tech_builder.append(f"本地IP: {local_ip}")
        tech_builder.append(f"ASN: {ip_info.get('asn', 'N/A')}")
        tech_builder.append(f"ISP: {ip_info.get('isp', 'N/A')}")
        tech_builder.append(f"组织: {ip_info.get('org', 'N/A')}")
        tech_builder.append(f"时区: {ip_info.get('timezone', 'N/A')}")
        tech_builder.append("")

        self.progress.setValue(45)
        self.add_log("[2/6] 检测代理/VPN状态...")
        QApplication.processEvents()

        proxy_ok = False
        proxy_override = False
        if sys.platform.startswith("win"):
            try:
                r = subprocess.run(
                    'reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable',
                    shell=True, capture_output=True, text=True
                )
                if "0x1" in r.stdout:
                    proxy_ok = True
                r2 = subprocess.run(
                    'reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyOverride',
                    shell=True, capture_output=True, text=True
                )
                if "<-loopback>" in r2.stdout or "localhost" in r2.stdout:
                    proxy_override = True
            except:
                pass

        score = 0
        max_score = 5

        if proxy_ok:
            self.security_widgets[0][0].setText("✅")
            self.security_widgets[0][1].setText("已启用")
            self.security_widgets[0][1].setStyleSheet(f"color: {MacOSColors.SYSTEM_GREEN}; font-size: 13px; font-weight: 600;")
            score += 1
            self.add_log("✅ 系统代理已启用")
        else:
            self.security_widgets[0][0].setText("⚠️")
            self.security_widgets[0][1].setText("未启用")
            self.security_widgets[0][1].setStyleSheet(f"color: {MacOSColors.SYSTEM_ORANGE}; font-size: 13px; font-weight: 600;")
            self.add_log("⚠️  未检测到系统代理/VPN")

        self.progress.setValue(55)
        self.add_log("[3/6] 检测WebRTC风险...")
        QApplication.processEvents()
        webrtc_safe = proxy_ok or (ip_info.get("ip", "") != local_ip and not local_ip.startswith("192.168."))
        if webrtc_safe:
            self.security_widgets[1][0].setText("✅")
            self.security_widgets[1][1].setText("低风险")
            self.security_widgets[1][1].setStyleSheet(f"color: {MacOSColors.SYSTEM_GREEN}; font-size: 13px; font-weight: 600;")
            score += 1
        else:
            self.security_widgets[1][0].setText("⚠️")
            self.security_widgets[1][1].setText("中风险")
            self.security_widgets[1][1].setStyleSheet(f"color: {MacOSColors.SYSTEM_ORANGE}; font-size: 13px; font-weight: 600;")
        self.add_log(f"{'✅' if webrtc_safe else '⚠️'} WebRTC本地IP泄露检测")

        self.progress.setValue(65)
        self.add_log("[4/6] 检测DNS泄露...")
        QApplication.processEvents()
        dns_safe = proxy_ok
        self.security_widgets[2][0].setText("✅" if dns_safe else "⚠️")
        self.security_widgets[2][1].setText("正常" if dns_safe else "建议检查")
        self.security_widgets[2][1].setStyleSheet(f"color: {'#30D158' if dns_safe else '#FF9F0A'}; font-size: 13px; font-weight: 600;")
        if dns_safe:
            score += 1
        self.add_log(f"{'✅' if dns_safe else '⚠️'} DNS泄露风险检测")

        self.progress.setValue(78)
        self.add_log("[5/6] 浏览器指纹检测...")
        QApplication.processEvents()
        canvas_safe = proxy_ok
        self.security_widgets[3][0].setText("✅" if canvas_safe else "ℹ️")
        self.security_widgets[3][1].setText("建议配合插件" if not canvas_safe else "正常")
        self.security_widgets[3][1].setStyleSheet(f"color: {MacOSColors.SYSTEM_TEAL if not canvas_safe else '#30D158'}; font-size: 13px; font-weight: 600;")
        if canvas_safe:
            score += 1
        self.add_log("ℹ️  指纹防护建议配合浏览器扩展使用")

        self.progress.setValue(90)
        self.add_log("[6/6] 综合评估真实IP隐蔽性...")
        QApplication.processEvents()
        ip_hidden = proxy_ok and ip_info.get("country_name", "") not in ["China", "中国"] and "中国电信" not in ip_info.get("isp", "") and "中国移动" not in ip_info.get("isp", "") and "中国联通" not in ip_info.get("isp", "")
        if proxy_ok:
            score += 1
        self.security_widgets[4][0].setText("✅" if ip_hidden else ("🟡" if proxy_ok else "❌"))
        self.security_widgets[4][1].setText("已隐藏" if ip_hidden else ("部分保护" if proxy_ok else "未隐藏"))
        self.security_widgets[4][1].setStyleSheet(f"color: {'#30D158' if ip_hidden else ('#FF9F0A' if proxy_ok else '#FF453A')}; font-size: 13px; font-weight: 600;")
        self.add_log(f"{'✅' if ip_hidden else ('🟡' if proxy_ok else '❌')} 真实IP状态检测")

        self.progress.setValue(100)
        self.score_label.setText(f"隐私评分: {score}/{max_score}")
        score_percent = int(score / max_score * 100)
        score_color = MacOSColors.SYSTEM_GREEN if score_percent >= 80 else (MacOSColors.SYSTEM_ORANGE if score_percent >= 50 else MacOSColors.SYSTEM_RED)
        self.score_label.setStyleSheet(f"color: {score_color}; font-size: 14px; font-weight: 700;")

        tech_builder.append("=" * 50)
        tech_builder.append("系统信息")
        tech_builder.append("=" * 50)
        tech_builder.append(f"操作系统: Windows")
        tech_builder.append(f"Python版本: {sys.version.split()[0]}")
        try:
            r = subprocess.run(["ipconfig"], capture_output=True, text=True, encoding='gbk', errors='replace', timeout=10)
            lines = [l.strip() for l in r.stdout.split('\n') if l.strip() and ('IPv4' in l or '子网掩码' in l or '默认网关' in l or 'DNS' in l or '描述' in l)]
            if lines:
                tech_builder.append("")
                tech_builder.append("网卡配置摘要:")
                for l in lines[:12]:
                    tech_builder.append(f"  {l}")
        except:
            pass

        tech_builder.append("")
        tech_builder.append(f"代理状态: {'已启用' if proxy_ok else '未启用'}")
        tech_builder.append(f"代理排除项: {'已配置(含本地)' if proxy_override else '默认'}")
        tech_builder.append("")
        tech_builder.append("=" * 50)
        tech_builder.append(f"综合隐私评分: {score}/{max_score} ({score_percent}%)")
        if score_percent < 50:
            tech_builder.append("建议: 立即启用代理/VPN，避免真实IP暴露！")
        elif score_percent < 80:
            tech_builder.append("建议: 优化代理配置，可考虑使用付费VPN服务")
        else:
            tech_builder.append("状态良好，继续保持安全的网络使用习惯")
        tech_builder.append("=" * 50)

        self.tech_info.setPlainText("\n".join(tech_builder))
        self.add_log(f"🎉 检测完成！隐私评分: {score}/{max_score} ({score_percent}%)")
        self.check_btn.setEnabled(True)
        QTimer.singleShot(2000, lambda: self.progress.setValue(0))


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_file = os.path.join(os.path.expanduser("~"), ".ip_tool_settings.json")
        self.settings = {}
        self.load_settings()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QVBoxLayout()
        title = QLabel("⚙️ 系统设置")
        title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
        """)
        header.addWidget(title)
        desc = QLabel("个性化配置IP切换工具，打造最适合你的工作流")
        desc.setStyleSheet(f"""
            color: {MacOSColors.TEXT_SECONDARY};
            font-size: 14px;
        """)
        header.addWidget(desc)
        layout.addLayout(header)

        general_card = MacOSCard()
        gl = QVBoxLayout(general_card)
        gl.setContentsMargins(22, 18, 22, 18)
        gl.setSpacing(14)

        gt = QLabel("🌱 通用设置")
        gt.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        gl.addWidget(gt)

        self._add_setting_row(gl, "启动时自动检测IP", "startup_check", True)
        self._add_setting_row(gl, "启用系统托盘图标", "tray_icon", True)
        self._add_setting_row(gl, "切换代理后自动检测IP", "auto_recheck", True)
        self._add_setting_row(gl, "关闭代理时确认提醒", "confirm_disable", False)
        self._add_setting_row(gl, "保存操作历史日志", "save_logs", True)

        layout.addWidget(general_card)

        auto_card = MacOSCard()
        al = QVBoxLayout(auto_card)
        al.setContentsMargins(22, 18, 22, 18)
        al.setSpacing(16)

        at = QLabel("⏰ 自动化")
        at.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        al.addWidget(at)

        auto_row = QHBoxLayout()
        auto_label = QLabel("定时切换代理：")
        auto_label.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 14px; font-weight: 500;")
        auto_row.addWidget(auto_label)
        self.auto_switch_checkbox = QCheckBox("启用")
        self.auto_switch_checkbox.setChecked(self.settings.get("auto_switch", False))
        self.auto_switch_checkbox.setCursor(Qt.PointingHandCursor)
        auto_row.addWidget(self.auto_switch_checkbox)
        auto_row.addSpacing(20)

        interval_label = QLabel("间隔时间(分钟)：")
        interval_label.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 14px;")
        auto_row.addWidget(interval_label)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(self.settings.get("switch_interval", 30))
        self.interval_spin.setFixedHeight(32)
        self.interval_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }}
        """)
        auto_row.addWidget(self.interval_spin)
        auto_row.addStretch()
        al.addLayout(auto_row)

        mode_row = QHBoxLayout()
        mode_label = QLabel("切换模式：")
        mode_label.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 14px; font-weight: 500;")
        mode_row.addWidget(mode_label)
        self.switch_mode_combo = QComboBox()
        self.switch_mode_combo.addItems(["顺序轮换", "随机选择"])
        idx = 0 if self.settings.get("switch_mode", "order") == "order" else 1
        self.switch_mode_combo.setCurrentIndex(idx)
        self.switch_mode_combo.setFixedHeight(32)
        self.switch_mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {MacOSColors.SIDEBAR_BG};
                border: 1px solid {MacOSColors.SEPARATOR};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
                min-width: 140px;
            }}
        """)
        mode_row.addWidget(self.switch_mode_combo)
        mode_row.addStretch()
        al.addLayout(mode_row)

        tip = QLabel("💡 定时切换适合需要频繁更换IP的场景（如数据采集、多账号操作）")
        tip.setStyleSheet(f"""
            color: {MacOSColors.SYSTEM_GRAY};
            font-size: 12px;
            padding: 6px 10px;
            background-color: {MacOSColors.ACCENT_BG};
            border-radius: 6px;
        """)
        tip.setWordWrap(True)
        al.addWidget(tip)

        layout.addWidget(auto_card)

        data_card = MacOSCard()
        dl = QVBoxLayout(data_card)
        dl.setContentsMargins(22, 18, 22, 18)
        dl.setSpacing(14)

        dt = QLabel("💾 数据管理")
        dt.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        dl.addWidget(dt)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        export_btn = MacOSSecondaryButton("📤 导出全部配置")
        export_btn.clicked.connect(self.export_settings)
        btn_row.addWidget(export_btn)

        import_btn = MacOSSecondaryButton("📥 导入配置")
        import_btn.clicked.connect(self.import_settings)
        btn_row.addWidget(import_btn)

        reset_btn = MacOSButton("♻️ 恢复默认设置", MacOSColors.SYSTEM_RED)
        reset_btn.clicked.connect(self.reset_settings)
        btn_row.addWidget(reset_btn)

        btn_row.addStretch()
        dl.addLayout(btn_row)

        path_row = QHBoxLayout()
        path_l = QLabel("配置文件路径：")
        path_l.setStyleSheet(f"color: {MacOSColors.TEXT_SECONDARY}; font-size: 12px;")
        path_row.addWidget(path_l)
        path_val = QLabel(self.config_file)
        path_val.setStyleSheet(f"color: {MacOSColors.TEXT_PRIMARY}; font-size: 12px; font-family: Consolas;")
        path_row.addWidget(path_val)
        path_row.addStretch()
        dl.addLayout(path_row)

        layout.addWidget(data_card)

        about_card = MacOSCard()
        abl = QVBoxLayout(about_card)
        abl.setContentsMargins(22, 18, 22, 18)
        abl.setSpacing(10)

        about_title = QLabel("ℹ️ 关于")
        about_title.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        abl.addWidget(about_title)

        lines = [
            "🛡️ IP切换工具 v1.0",
            "支持多种IP切换方式：代理服务器、网卡配置修改、DNS优化",
            "",
            "【使用建议】",
            "• 家庭宽带：重启光猫/路由器即可换公网IP",
            "• 手机热点：开启飞行模式30秒后关闭，即可换IP",
            "• 稳定需求：购买付费代理或VPN服务（推荐专线）",
            "• 多账号：每账号固定一个代理IP，避免关联风控",
            "",
            "【免责声明】",
            "本工具仅用于合法的网络测试和学习研究，请遵守当地法律法规。",
        ]
        for line in lines:
            if line == "":
                abl.addSpacing(2)
                continue
            ll = QLabel(line)
            ll.setStyleSheet(f"""
                color: {MacOSColors.TEXT_SECONDARY if line.startswith(('•', '【')) or '支持' in line else MacOSColors.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: {'600' if line.startswith(('【', '🛡️')) else '400'};
            """)
            ll.setWordWrap(True)
            abl.addWidget(ll)

        layout.addWidget(about_card)

        bottom = QHBoxLayout()
        bottom.addStretch()
        save_btn = MacOSButton("💾 保存所有设置", MacOSColors.SYSTEM_GREEN)
        save_btn.clicked.connect(self.save_settings_and_notify)
        bottom.addWidget(save_btn)
        layout.addLayout(bottom)
        layout.addStretch()

    def _add_setting_row(self, parent_layout, label_text, key, default):
        row = QFrame()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(4, 4, 4, 4)
        rl.setSpacing(10)

        label = QLabel(label_text)
        label.setStyleSheet(f"""
            color: {MacOSColors.TEXT_PRIMARY};
            font-size: 14px;
        """)
        rl.addWidget(label)
        rl.addStretch()

        cb = QCheckBox()
        cb.setChecked(self.settings.get(key, default))
        cb.setCursor(Qt.PointingHandCursor)
        cb.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
                border-radius: 11px;
                border: 2px solid {MacOSColors.SYSTEM_GRAY3};
            }}
            QCheckBox::indicator:checked {{
                background-color: {MacOSColors.SYSTEM_GREEN};
                border-color: {MacOSColors.SYSTEM_GREEN};
                image: none;
            }}
            QCheckBox::indicator:checked::after {{
                content: '✓';
                color: white;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        self.settings[key + "_cb"] = cb
        rl.addWidget(cb)
        parent_layout.addWidget(row)

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        defaults = {
            "startup_check": True,
            "tray_icon": True,
            "auto_recheck": True,
            "confirm_disable": False,
            "save_logs": True,
            "auto_switch": False,
            "switch_interval": 30,
            "switch_mode": "order",
        }
        for k, v in defaults.items():
            if k not in self.settings:
                self.settings[k] = v

    def save_settings(self):
        save_data = {}
        for k, v in self.settings.items():
            if k.endswith("_cb"):
                continue
            save_data[k] = v

        checkbox_keys = ["startup_check", "tray_icon", "auto_recheck", "confirm_disable", "save_logs"]
        for k in checkbox_keys:
            cb = self.settings.get(k + "_cb")
            if cb:
                save_data[k] = cb.isChecked()

        save_data["auto_switch"] = self.auto_switch_checkbox.isChecked()
        save_data["switch_interval"] = self.interval_spin.value()
        save_data["switch_mode"] = "order" if self.switch_mode_combo.currentIndex() == 0 else "random"

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            self.settings.update(save_data)
            return True
        except Exception as e:
            print(f"保存设置失败: {e}")
            return False

    def save_settings_and_notify(self):
        if self.save_settings():
            QMessageBox.information(self, "成功", "设置已保存！")
        else:
            QMessageBox.critical(self, "错误", "保存失败，请检查权限")

    def export_settings(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", f"ip_tool_config_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON文件 (*.json)"
        )
        if not path:
            return
        try:
            self.save_settings()
            export_data = {"settings": self.settings, "export_time": datetime.now().isoformat()}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", f"配置已导出到：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")

    def import_settings(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )
        if not path:
            return
        reply = QMessageBox.question(
            self, "确认导入",
            "导入后将覆盖当前所有设置，确定继续吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "settings" in data:
                self.settings.update(data["settings"])
            else:
                self.settings.update(data)
            QMessageBox.information(self, "成功", "配置已导入，请重新打开设置页面生效")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败：{str(e)}")

    def reset_settings(self):
        reply = QMessageBox.question(
            self, "确认重置",
            "将清除所有自定义设置，恢复到默认状态，确定继续吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            QMessageBox.information(self, "成功", "已恢复默认设置，程序将刷新")
        except:
            QMessageBox.warning(self, "提示", "无法删除配置文件，请手动删除")


class IPCutterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛡️ IP切换工具 - 一键换IP保护隐私")
        self.setMinimumSize(1150, 780)
        self.resize(1300, 850)
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

        self.toolbar = MacOSToolbar("📊 状态面板")
        content_layout.addWidget(self.toolbar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")

        self.dashboard = DashboardPage()
        self.proxy_page = ProxyPage()
        self.network_page = NetworkConfigPage()
        self.check_page = IPCheckPage()
        self.settings_page = SettingsPage()

        self.pages = [
            self.dashboard,
            self.proxy_page,
            self.network_page,
            self.check_page,
            self.settings_page,
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack)
        layout.addWidget(content_area, 1)

        self.proxy_page.apply_proxy_signal.connect(self.on_proxy_applied)
        self.proxy_page.clear_proxy_signal.connect(self.on_proxy_cleared)

        self.fade_animation = None

    def on_tab_changed(self, index):
        if self.stack.currentIndex() == index:
            return
        titles = [
            "📊 状态面板",
            "🔌 代理切换",
            "🌐 网卡配置",
            "🔍 IP检测",
            "⚙️ 系统设置",
        ]
        self.toolbar.title_label.setText(titles[index])

        new_page = self.pages[index]
        opacity_effect = QGraphicsOpacityEffect(new_page)
        new_page.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0)
        self.stack.setCurrentIndex(index)

        self.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_animation.setDuration(260)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()

    def on_proxy_applied(self, proxy):
        self.dashboard.add_log(f"🔌 启用代理: {proxy.get('name', '')} ({proxy.get('host', '')}:{proxy.get('port', '')})")
        proxy_card = self.dashboard.proxy_card.findChild(QLabel, "value_label")
        if proxy_card:
            proxy_card.setText(f"{proxy.get('type', '')}_{proxy.get('host', '')[:15]}")
            proxy_card.setStyleSheet(f"color: {MacOSColors.SYSTEM_GREEN}; font-size: 20px; font-weight: 700;")
        self.toolbar.status_badge.setText("🔐 使用代理")
        self.toolbar.status_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {MacOSColors.GREEN_BG};
                color: {MacOSColors.SYSTEM_GREEN};
                border-radius: 12px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        if self.settings_page.settings.get("auto_recheck", True):
            QTimer.singleShot(2000, self.dashboard.refresh_ip)

    def on_proxy_cleared(self):
        self.dashboard.add_log("🚫 关闭所有代理")
        proxy_card = self.dashboard.proxy_card.findChild(QLabel, "value_label")
        if proxy_card:
            proxy_card.setText("未使用")
            proxy_card.setStyleSheet(f"color: {MacOSColors.SYSTEM_ORANGE}; font-size: 20px; font-weight: 700;")
        self.toolbar.status_badge.setText("● 网络正常")
        self.toolbar.status_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {MacOSColors.GREEN_BG};
                color: {MacOSColors.SYSTEM_GREEN};
                border-radius: 12px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        if self.settings_page.settings.get("auto_recheck", True):
            QTimer.singleShot(2000, self.dashboard.refresh_ip)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)

    font = QFont("Microsoft YaHei UI", 10)
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
            margin: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {MacOSColors.SYSTEM_GRAY3}30;
            border-radius: 3px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {MacOSColors.SYSTEM_GRAY2}50;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 7px;
            margin: 3px;
        }}
        QScrollBar::handle:horizontal {{
            background: {MacOSColors.SYSTEM_GRAY3}30;
            border-radius: 3px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {MacOSColors.SYSTEM_GRAY2}50;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """)

    window = IPCutterApp()
    window.show()
    print("🛡️ IP切换工具已启动！")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()