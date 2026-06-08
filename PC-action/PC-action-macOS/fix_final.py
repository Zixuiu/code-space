path = r'd:\code空间\PC-action\PC-action-macOS\app_macos.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 instruction_label 部分
old1 = content[content.index('instruction_label.setAlignment'):content.index('layout.addWidget(instruction_label)') + len('layout.addWidget(instruction_label)')]
# 但更可靠的方式是用 find 定位

# 直接精确替换
idx1 = content.find('instruction_label.setAlignment(Qt.AlignCenter)')
if idx1 > 0:
    # 找到这一行前面的换行位置
    line_start = content.rfind('\n', 0, idx1) + 1
    # 找到 layout.addWidget(instruction_label) 后面的换行
    idx1_end = content.find('layout.addWidget(instruction_label)', idx1) + len('layout.addWidget(instruction_label)')
    line_end = content.find('\n', idx1_end) + 1
    
    block1 = content[line_start:line_end]
    
    indent = '        '
    new_block1 = indent + 'instruction_label = QLabel(\"请按下快捷键组合...\")\n'
    new_block1 += indent + 'instruction_label.setAlignment(Qt.AlignCenter)\n'
    new_block1 += indent + 'instruction_font_size = int(screen_height * 0.022)\n'
    new_block1 += indent + 'instruction_label.setStyleSheet(f\"\"\"\n'
    new_block1 += indent + '    font-size: {instruction_font_size}px;\n'
    new_block1 += indent + '    color: {MacOSColors.TEXT_SECONDARY};\n'
    new_block1 += indent + '    font-family: \'PingFang SC\', \'SimHei\', \'Helvetica Neue\', \'Segoe UI\', sans-serif;\n'
    new_block1 += indent + '    background: transparent;\n'
    new_block1 += indent + '\"\"\")\n'
    new_block1 += indent + 'layout.addWidget(instruction_label)\n'
    
    content = content[:line_start] + new_block1 + content[line_end:]
    print('✅ 修复 1 成功')
else:
    print('❌ 修复 1 未匹配')

# 修复 shortcut_label 部分
idx2 = content.find('shortcut_label.setAlignment(Qt.AlignCenter)')
if idx2 > 0:
    line_start = content.rfind('\n', 0, idx2) + 1
    idx2_end = content.find('layout.addWidget(shortcut_label)', idx2) + len('layout.addWidget(shortcut_label)')
    line_end = content.find('\n', idx2_end) + 1
    
    block2 = content[line_start:line_end]
    
    indent = '        '
    new_block2 = indent + 'shortcut_label = QLabel(current_shortcut if current_shortcut else \"未设置\")\n'
    new_block2 += indent + 'shortcut_label.setAlignment(Qt.AlignCenter)\n'
    new_block2 += indent + 'shortcut_font_size = int(screen_height * 0.03)\n'
    new_block2 += indent + 'shortcut_label.setStyleSheet(f\"\"\"\n'
    new_block2 += indent + '    font-size: {shortcut_font_size}px;\n'
    new_block2 += indent + '    font-weight: 600;\n'
    new_block2 += indent + '    padding: 14px;\n'
    new_block2 += indent + '    border: 2px solid {MacOSColors.ACCENT};\n'
    new_block2 += indent + '    border-radius: 12px;\n'
    new_block2 += indent + '    background-color: {MacOSColors.CARD_BG};\n'
    new_block2 += indent + '    min-height: 44px;\n'
    new_block2 += indent + '    font-family: \'PingFang SC\', \'SimHei\', \'Helvetica Neue\', \'Segoe UI\', sans-serif;\n'
    new_block2 += indent + '    color: {MacOSColors.ACCENT};\n'
    new_block2 += indent + '\"\"\")\n'
    new_block2 += indent + 'layout.addWidget(shortcut_label)\n'
    
    content = content[:line_start] + new_block2 + content[line_end:]
    print('✅ 修复 2 成功')
else:
    print('❌ 修复 2 未匹配')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('🎯 完成！')
