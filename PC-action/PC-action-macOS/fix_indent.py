import sys
sys.stdout.reconfigure(encoding="utf-8")
path = "d:\\code空间\\PC-action\\PC-action-macOS\\app_macos.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()
old1 = "        instruction_label.setAlignment(Qt.AlignCenter)\n        instruction_font_size = int(screen_height * 0.022)\n            font-size: {instruction_font_size}px;\n            color: {MacOSColors.TEXT_SECONDARY};\n            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;\n            background: transparent;\n        \"\"\")\n        layout.addWidget(instruction_label)"
new1 = "        instruction_label = QLabel(\"请按下快捷键组合...\")\n        instruction_label.setAlignment(Qt.AlignCenter)\n        instruction_font_size = int(screen_height * 0.022)\n        instruction_label.setStyleSheet(f\"\"\"\n            font-size: {instruction_font_size}px;\n            color: {MacOSColors.TEXT_SECONDARY};\n            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;\n            background: transparent;\n        \"\"\")\n        layout.addWidget(instruction_label)"
if old1 in c:
    c = c.replace(old1, new1)
    print("修复1 成功")
else:
    print("修复1 失败 - 未匹配到 instruction_label 错误代码")
old2 = "        shortcut_label.setAlignment(Qt.AlignCenter)\n        shortcut_font_size = int(screen_height * 0.03)\n            font-size: {shortcut_font_size}px;\n            font-weight: 600;\n            padding: 14px;\n            border: 2px solid {MacOSColors.ACCENT};\n            border-radius: 12px;\n            background-color: {MacOSColors.CARD_BG};\n            min-height: 44px;\n            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;\n            color: {MacOSColors.ACCENT};\n        \"\"\")\n        layout.addWidget(shortcut_label)"
new2 = "        shortcut_label = QLabel(current_shortcut if current_shortcut else \"未设置\")\n        shortcut_label.setAlignment(Qt.AlignCenter)\n        shortcut_font_size = int(screen_height * 0.03)\n        shortcut_label.setStyleSheet(f\"\"\"\n            font-size: {shortcut_font_size}px;\n            font-weight: 600;\n            padding: 14px;\n            border: 2px solid {MacOSColors.ACCENT};\n            border-radius: 12px;\n            background-color: {MacOSColors.CARD_BG};\n            min-height: 44px;\n            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;\n            color: {MacOSColors.ACCENT};\n        \"\"\")\n        layout.addWidget(shortcut_label)"
if old2 in c:
    c = c.replace(old2, new2)
    print("修复2 成功")
else:
    print("修复2 失败 - 未匹配到 shortcut_label 错误代码")
with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("全部完成！")
