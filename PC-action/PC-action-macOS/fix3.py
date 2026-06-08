path = "d:\\code空间\\PC-action\\PC-action-macOS\\app_macos.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

old = '        input_field = QLineEdit(old_name)\n        input_field.selectAll()\n            QLineEdit {{\n                border: 1px solid {MacOSColors.SEPARATOR};\n                border-radius: 8px;\n                padding: 10px 14px;\n                font-size: 14px;\n                background: {MacOSColors.CARD_BG};\n                color: {MacOSColors.TEXT_PRIMARY};\n                font-family: \x27PingFang SC\x27, \x27SimHei\x27, \x27Helvetica Neue\x27, \x27Segoe UI\x27, sans-serif;\n            }}\n            QLineEdit:focus {{\n                border-color: {MacOSColors.ACCENT};\n            }}\n        """)\n        layout.addWidget(input_field)'

new = '        input_field = QLineEdit(old_name)\n        input_field.selectAll()\n        input_field.setStyleSheet(f"""\n            QLineEdit {{\n                border: 1px solid {MacOSColors.SEPARATOR};\n                border-radius: 8px;\n                padding: 10px 14px;\n                font-size: 14px;\n                background: {MacOSColors.CARD_BG};\n                color: {MacOSColors.TEXT_PRIMARY};\n                font-family: \x27PingFang SC\x27, \x27SimHei\x27, \x27Helvetica Neue\x27, \x27Segoe UI\x27, sans-serif;\n            }}\n            QLineEdit:focus {{\n                border-color: {MacOSColors.ACCENT};\n            }}\n        """)\n        layout.addWidget(input_field)'

if old in c:
    c = c.replace(old, new)
    print("修复成功！")
else:
    print("未匹配到错误代码，请检查")

with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("完成！")
