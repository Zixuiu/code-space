import re
f = r'd:\code空间\PC-action\PC-action-macOS\app_macos.py'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# Fix all dialog.setStyleSheet(f""" missing lines
c = c.replace('dialog.setWindowModality(Qt.WindowModal)\n            QDialog {{', 'dialog.setWindowModality(Qt.WindowModal)\n        dialog.setStyleSheet(f"""\n            QDialog {{')
c = c.replace('dialog.setWindowModality(Qt.WindowModal)\n        dialog.setStyleSheet(f"""\n            QDialog {{\n        dialog.setStyleSheet(f"""\n            QDialog {{', 'dialog.setWindowModality(Qt.WindowModal)\n        dialog.setStyleSheet(f"""\n            QDialog {{')

open(f, 'w', encoding='utf-8').write(c)
print('Done')
