import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app_macos.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._finish_recording()
            return
        if event.button() == Qt.LeftButton:
            self.step_counter += 1
            screen = QApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            global_logical = self.mapToGlobal(event.pos())
            px = int(global_logical.x() * dpr)
            py = int(global_logical.y() * dpr)
            rec = {"step": self.step_counter, "action_type": "click", "x": px, "y": py, "delay": 0.3}
            self.records.append(rec)
            if self.parent and hasattr(self.parent, 'coordinate_records'):
                self.parent.coordinate_records = self.records

            # WS_EX_TRANSPARENT 设透明 → click → 函数返回（样式保持透明）
            # Qt 事件循环处理 pyautogui 事件时，透明期内事件穿透到目标→不计数
            # 下一轮事件循环再恢复样式
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x20
            old_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, old_style | WS_EX_TRANSPARENT)
            self._restore_data = (hwnd, old_style)
            QApplication.processEvents()
            import pyautogui
            pyautogui.click(px, py)
            # mousePressEvent 立即返回，不排干、不恢复样式
            # 延迟恢复：Qt 处理完所有残余事件后再恢复
            QTimer.singleShot(0, self._deferred_restore)

    def _deferred_restore(self):
        hwnd, old_style = getattr(self, '_restore_data', (None, None))
        if hwnd is None:
            return
        import ctypes
        GWL_EXSTYLE = -20
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, old_style)
        self._restore_data = None
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)
        self.update()"""

new = """    def _send_click_to_target(self, px, py):
        # PostMessage 直接发送点击到目标窗口，零残余事件
        import ctypes
        from ctypes import wintypes
        pt = wintypes.POINT(px, py)
        target_hwnd = ctypes.windll.user32.WindowFromPoint(pt)
        if not target_hwnd:
            return
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(target_hwnd, ctypes.byref(rect))
        cx = px - rect.left
        cy = py - rect.top
        lparam = (cy << 16) | (cx & 0xFFFF)
        ctypes.windll.user32.PostMessageW(target_hwnd, 0x201, 1, lparam)
        ctypes.windll.user32.PostMessageW(target_hwnd, 0x202, 0, lparam)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._finish_recording()
            return
        if event.button() == Qt.LeftButton:
            self.step_counter += 1
            screen = QApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            global_logical = self.mapToGlobal(event.pos())
            px = int(global_logical.x() * dpr)
            py = int(global_logical.y() * dpr)
            rec = {"step": self.step_counter, "action_type": "click", "x": px, "y": py, "delay": 0.3}
            self.records.append(rec)
            if self.parent and hasattr(self.parent, 'coordinate_records'):
                self.parent.coordinate_records = self.records

            # hide -> PostMessage -> show (零残余事件)
            self.hide()
            QApplication.processEvents()
            self._send_click_to_target(px, py)
            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus(Qt.ActiveWindowFocusReason)
            QApplication.processEvents()
            self.update()"""

if old in content:
    content = content.replace(old, new, 1)
    print("OK PostMessage zero residual events")
else:
    print("FAIL no match")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("DONE!")