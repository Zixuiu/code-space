# -*- coding: utf-8 -*-
"""为view_images对话框添加红点关闭按钮"""
import re

with open(r'd:\code空间\PC-action\PC-action-macOS\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在 layout = QVBoxLayout(dialog) 和 scroll_area = QScrollArea() 之间插入红点
old = 'layout = QVBoxLayout(dialog)\n        scroll_area = QScrollArea()'
new = '''layout = QVBoxLayout(dialog)
        # 右上角红点关闭按钮
        _dot = QFrame()
        _dot.setFixedSize(14,14)
        _dot.setStyleSheet("QFrame{background-color:#FF5F57;border:none;border-radius:7px;}QFrame:hover{background-color:#FF3B30;}")
        _dot.setCursor(Qt.PointingHandCursor)
        def _closeD(ev):
            if ev.button()==Qt.LeftButton: dialog.close()
        _dot.mousePressEvent = _closeD
        _dh = QHBoxLayout()
        _dh.addStretch()
        _dh.addWidget(_dot)
        layout.addLayout(_dh)
        scroll_area = QScrollArea()'''

if old in content:
    content = content.replace(old, new, 1)
    print('✅ 成功：view_images 红点关闭按钮已添加')
else:
    print('❌ 失败：未找到匹配代码')
    # 尝试找不同的缩进版本
    for indent in ['    ', '        ', '            ']:
        alt_old = f'{indent}layout = QVBoxLayout(dialog)\n{indent}scroll_area = QScrollArea()'
        if alt_old in content:
            indent_str = indent
            alt_new = f'''{indent}layout = QVBoxLayout(dialog)
{indent}# 右上角红点关闭按钮
{indent}_dot = QFrame()
{indent}_dot.setFixedSize(14,14)
{indent}_dot.setStyleSheet("QFrame{{background-color:#FF5F57;border:none;border-radius:7px;}}QFrame:hover{{background-color:#FF3B30;}}")
{indent}_dot.setCursor(Qt.PointingHandCursor)
{indent}def _closeD(ev):
{indent}    if ev.button()==Qt.LeftButton: dialog.close()
{indent}_dot.mousePressEvent = _closeD
{indent}_dh = QHBoxLayout()
{indent}_dh.addStretch()
{indent}_dh.addWidget(_dot)
{indent}layout.addLayout(_dh)
{indent}scroll_area = QScrollArea()'''
            content = content.replace(alt_old, alt_new, 1)
            print(f'✅ 成功（备选缩进）：view_images 红点关闭按钮已添加')
            break

with open(r'd:\code空间\PC-action\PC-action-macOS\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n🎉 修复完成！重启程序后图片流程右上角将显示红点关闭按钮。')
