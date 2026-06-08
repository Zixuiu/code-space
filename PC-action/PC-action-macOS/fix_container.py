# -*- coding: utf-8 -*-
"""用白色容器包裹红点和滚动区，避免红点悬浮"""
import re

with open(r'd:\code空间\PC-action\PC-action-macOS\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换从 layout=QVBoxLayout(dialog) 到 scroll_area=QScrollArea() 的整段代码
old_block = '''        layout = QVBoxLayout(dialog)
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

new_block = '''        layout = QVBoxLayout(dialog)
        # 白色圆角容器（包裹红点+滚动区，避免红点悬浮在透明背景上）
        _container = QWidget()
        _container.setStyleSheet("QWidget{background:white;border-radius:8px;}")
        _cl = QVBoxLayout(_container)
        _cl.setContentsMargins(0,0,0,0)
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
        _cl.addLayout(_dh)
        scroll_area = QScrollArea()'''

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    print('✅ 成功：已用白色容器包裹红点和滚动区')
else:
    print('❌ 失败：未找到匹配代码')
    # 尝试找到不同的格式
    import re as re2
    # 查找 layout = QVBoxLayout(dialog)
    matches = list(re2.finditer(r'(        layout = QVBoxLayout\(dialog\)\s*\n)(.*?)(\n        scroll_area = QScrollArea\(\).*)', content, re2.DOTALL))
    if matches:
        m = matches[0]
        old2 = m.group(1) + m.group(2) + m.group(3)
        new2 = m.group(1) + '''        # 白色圆角容器（包裹红点+滚动区，避免红点悬浮在透明背景上）
        _container = QWidget()
        _container.setStyleSheet("QWidget{background:white;border-radius:8px;}")
        _cl = QVBoxLayout(_container)
        _cl.setContentsMargins(0,0,0,0)''' + m.group(2) + m.group(3)
        content = content.replace(old2, new2, 1)
        
        # 将 layout.addLayout(_dh) 改为 _cl.addLayout(_dh)
        content = content.replace('layout.addLayout(_dh)', '_cl.addLayout(_dh)')
        
        # 将 layout.addWidget(scroll_area) 改为 _cl.addWidget(scroll_area)
        content = content.replace('layout.addWidget(scroll_area)', '_cl.addWidget(scroll_area)')
        
        # 在 layout.addWidget(scroll_area) 前添加 layout.addWidget(_container)
        content = content.replace('_cl.addWidget(scroll_area)', '_cl.addWidget(scroll_area)\n        layout.addWidget(_container)')
        
        print('✅ 成功（备选）：已用白色容器包裹')
    else:
        print('❌ 失败：完全无法匹配')

# 同时将 scroll_area 和 scroll_root 的背景设为透明（让外层容器提供白色背景）
content = content.replace(
    'scroll_area.setStyleSheet("QScrollArea { background: white; border: none; }")',
    'scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")'
)
content = content.replace(
    'scroll_root.setStyleSheet("background: white;")',
    'scroll_root.setStyleSheet("background: transparent;")'
)

with open(r'd:\code空间\PC-action\PC-action-macOS\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n🎉 修复完成！红点现在会显示在白色圆角容器右上角，不再悬浮。')
