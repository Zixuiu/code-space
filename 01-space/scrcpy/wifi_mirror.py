# -*- coding: utf-8 -*-
"""
wifi_mirror.py —— 免敲 adb 的手机无线投屏助手（基于 scrcpy）

用法：
  1. 手机打开：开发者选项 -> 无线调试，记下「设备 IP 和端口」与「配对码和配对端口」
  2. 双击 start_wifi.bat 启动本工具
  3. 把手机上的 IP / 配对端口 / 配对码 / 连接端口 填进去，点「配对并连接」
  4. 连上后点「启动投屏」，弹出的窗口就是手机实时画面，鼠标可直接点击操作

本工具替你执行：
  adb pair  <IP>:<配对端口>      （自动喂入配对码，无需手敲）
  adb connect <IP>:<连接端口>
  adb devices                    （确认连接状态）
  scrcpy --serial <IP>:<连接端口> （拉起投屏）
"""

import os
import sys
import subprocess

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QGroupBox, QFrame,
)
from PyQt5.QtGui import QColor, QFont


HERE = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(HERE, "adb.exe")
SCRCPY = os.path.join(HERE, "scrcpy.exe")


# ----------------------------- 后台执行线程（不卡 UI） -----------------------------
class AdbWorker(QThread):
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, kind, params):
        super().__init__()
        self.kind = kind          # "pair" / "connect" / "devices" / "mirror" / "disconnect"
        self.params = params

    def run(self):
        try:
            if self.kind == "pair":
                self._pair()
            elif self.kind == "connect":
                self._connect()
            elif self.kind == "devices":
                self._devices()
            elif self.kind == "mirror":
                self._mirror()
            elif self.kind == "disconnect":
                self._disconnect()
        except Exception as e:
            self.log.emit(f"✗ 异常：{e}")
            self.finished.emit(False, str(e))

    # ---- 执行 adb 命令，返回 (returncode, stdout+stderr) ----
    def _run(self, args, input_text=None, timeout=25):
        self.log.emit("› " + " ".join(args))
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE if input_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=HERE,
        )
        try:
            out, _ = proc.communicate(
                input=(input_text + "\n") if input_text is not None else None,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
            out += "\n[命令超时，已终止]"
        for line in out.strip().splitlines():
            if line.strip():
                self.log.emit("  " + line)
        return proc.returncode, out

    def _pair(self):
        ip, pport, code = self.params["ip"], self.params["pair_port"], self.params["code"]
        rc, out = self._run([ADB, "pair", f"{ip}:{pport}"], input_text=code)
        ok = rc == 0 and ("Successfully" in out or "paired" in out.lower())
        if ok:
            self.log.emit("✓ 配对成功")
            self.finished.emit(True, "配对成功，请点「连接」")
        else:
            self.log.emit("✗ 配对失败（检查 IP/端口/配对码是否正确，手机需在同一 WiFi）")
            self.finished.emit(False, "配对失败")

    def _connect(self):
        ip, cport = self.params["ip"], self.params["conn_port"]
        rc, out = self._run([ADB, "connect", f"{ip}:{cport}"])
        # adb connect 成功时输出 "connected to IP:PORT" 或 "already connected"
        ok = rc == 0 and ("connected to" in out.lower() or "already connected" in out.lower())
        self._run([ADB, "devices"])
        if ok:
            self.log.emit("✓ 已连接，可以点「启动投屏」了")
            self.finished.emit(True, "已连接")
        else:
            self.log.emit("✗ 连接失败（请先完成配对，或确认连接端口正确）")
            self.finished.emit(False, "连接失败")

    def _devices(self):
        rc, out = self._run([ADB, "devices"])
        self.finished.emit(rc == 0, "已刷新设备列表")

    def _disconnect(self):
        ip, cport = self.params["ip"], self.params["conn_port"]
        self._run([ADB, "disconnect", f"{ip}:{cport}"])
        self._run([ADB, "devices"])
        self.finished.emit(True, "已断开")

    def _mirror(self):
        ip, cport = self.params["ip"], self.params["conn_port"]
        self.log.emit(f"› 启动 scrcpy 投屏 {ip}:{cport} ...")
        # 前台拉起 scrcpy（窗口由 scrcpy 自己管）；用 start 不阻塞本线程
        try:
            subprocess.Popen(
                [SCRCPY, "--serial", f"{ip}:{cport}", "--stay-awake",
                 "--show-touches", "--window-title", "手机投屏"],
                cwd=HERE,
            )
            self.log.emit("✓ 已拉起 scrcpy 窗口（若手机界面未出现，检查连接状态）")
            self.finished.emit(True, "投屏已启动")
        except Exception as e:
            self.log.emit(f"✗ 启动 scrcpy 失败：{e}")
            self.finished.emit(False, str(e))


# ----------------------------- 主窗口 -----------------------------
class WifiMirrorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("手机无线投屏助手")
        self.setMinimumWidth(460)
        self.setStyleSheet("""
            QWidget { background: #F5F5F7; color: #1D1D1F;
                      font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; }
            QGroupBox { border: 1px solid #D2D2D7; border-radius: 10px;
                        margin-top: 10px; padding: 12px 12px 14px; font-weight: 600; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px;
                               padding: 0 6px; color: #6E6E73; }
            QLineEdit { background: #FFFFFF; border: 1px solid #C7C7CC;
                        border-radius: 8px; padding: 7px 10px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #34C759; }
            QPushButton { background: #34C759; color: white; border: none;
                          border-radius: 9px; padding: 9px 14px; font-size: 14px;
                          font-weight: 600; }
            QPushButton:hover { background: #2FBF50; }
            QPushButton:pressed { background: #28A745; }
            QPushButton#ghost { background: #FFFFFF; color: #007AFF;
                                border: 1px solid #C7C7CC; }
            QPushButton#ghost:hover { background: #F0F0F3; }
            QPushButton#danger { background: #FF3B30; }
            QPushButton#danger:hover { background: #E0342B; }
            QTextEdit { background: #1D1D1F; color: #D1D1D6; border-radius: 8px;
                        padding: 8px; font-family: Consolas, 'Courier New', monospace;
                        font-size: 12px; }
            QLabel#hint { color: #8E8E93; font-size: 12px; }
        """)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        # 标题
        title = QLabel("📱 手机无线投屏助手")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1D1D1F;")
        root.addWidget(title)

        subtitle = QLabel("手机：开发者选项 → 无线调试，把界面上的信息填进来即可，无需敲命令")
        subtitle.setObjectName("hint")
        root.addWidget(subtitle)

        # 输入区
        box = QGroupBox("手机无线调试信息")
        g = QVBoxLayout(box)
        g.setSpacing(10)

        self.ed_ip = self._field(g, "手机 IP", "例如 192.168.1.100")
        self.ed_pport = self._field(g, "配对端口", "无线调试里的「配对端口」如 37000")
        self.ed_code = self._field(g, "配对码", "无线调试里的 6 位配对码")
        self.ed_cport = self._field(g, "连接端口", "无线调试里的「设备端口」如 39000")

        root.addWidget(box)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.bt_pair = QPushButton("1. 配对并连接")
        self.bt_pair.clicked.connect(self.do_pair_connect)
        self.bt_mirror = QPushButton("2. 启动投屏")
        self.bt_mirror.clicked.connect(self.do_mirror)
        self.bt_mirror.setObjectName("ghost")
        self.bt_devices = QPushButton("刷新设备")
        self.bt_devices.setObjectName("ghost")
        self.bt_devices.clicked.connect(lambda: self._run_worker("devices", {}))
        self.bt_disconnect = QPushButton("断开")
        self.bt_disconnect.setObjectName("danger")
        self.bt_disconnect.clicked.connect(self.do_disconnect)
        btn_row.addWidget(self.bt_pair)
        btn_row.addWidget(self.bt_mirror)
        btn_row.addWidget(self.bt_devices)
        btn_row.addWidget(self.bt_disconnect)
        root.addLayout(btn_row)

        # 日志
        log_label = QLabel("运行日志")
        log_label.setObjectName("hint")
        root.addWidget(log_label)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(150)
        root.addWidget(self.log)

        self._log("就绪。请先填写手机无线调试信息，然后点「1. 配对并连接」。")

    def _field(self, layout, label, placeholder):
        row = QHBoxLayout()
        row.setSpacing(8)
        lab = QLabel(label)
        lab.setFixedWidth(64)
        lab.setStyleSheet("font-size: 13px; color: #1D1D1F;")
        ed = QLineEdit()
        ed.setPlaceholderText(placeholder)
        row.addWidget(lab)
        row.addWidget(ed, 1)
        layout.addLayout(row)
        return ed

    # --------------------------- 动作 ---------------------------
    def _params(self):
        return {
            "ip": self.ed_ip.text().strip(),
            "pair_port": self.ed_pport.text().strip(),
            "code": self.ed_code.text().strip(),
            "conn_port": self.ed_cport.text().strip(),
        }

    def _validate(self, need_code=False):
        p = self._params()
        if not p["ip"] or not p["conn_port"]:
            self._log("✗ 请先填「手机 IP」和「连接端口」")
            return None
        if need_code and (not p["pair_port"] or not p["code"]):
            self._log("✗ 配对需要「配对端口」和「配对码」")
            return None
        return p

    def do_pair_connect(self):
        p = self._validate(need_code=True)
        if not p:
            return
        # 配对完成后自动连接
        self.bt_pair.setEnabled(False)
        self.worker = AdbWorker("pair", p)
        self.worker.log.connect(self._log)
        self.worker.finished.connect(self._on_pair_done)
        self.worker.start()

    def _on_pair_done(self, ok, msg):
        if ok:
            p = self._params()
            self.worker = AdbWorker("connect", p)
            self.worker.log.connect(self._log)
            self.worker.finished.connect(lambda *_: self.bt_pair.setEnabled(True))
            self.worker.start()
        else:
            self.bt_pair.setEnabled(True)

    def do_mirror(self):
        p = self._validate()
        if not p:
            return
        self._run_worker("mirror", p)

    def do_disconnect(self):
        p = self._validate()
        if not p:
            return
        self._run_worker("disconnect", p)

    def _run_worker(self, kind, params):
        self.worker = AdbWorker(kind, params)
        self.worker.log.connect(self._log)
        self.worker.finished.connect(lambda *_: None)
        self.worker.start()

    def _log(self, text):
        self.log.append(text)
        # 自动滚到底
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.End)
        self.log.setTextCursor(cursor)


def main():
    if not os.path.exists(ADB) or not os.path.exists(SCRCPY):
        print("错误：未找到 adb.exe / scrcpy.exe，请确认本工具位于 scrcpy 目录下")
        sys.exit(1)
    app = QApplication(sys.argv)
    w = WifiMirrorWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
