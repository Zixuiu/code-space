p = r"d:\code空间\PC-action\PC-action-macOS\app.py"
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # 插入卡片容器代码
    if 'self.input_style = get_input_style()' in line:
        new_lines.append(line)
        new_lines.append('\n')
        new_lines.append('        # 外层布局：对话框透明，卡片容器提供背景\n')
        new_lines.append('        outer_layout = QVBoxLayout(self)\n')
        new_lines.append('        outer_layout.setContentsMargins(0, 0, 0, 0)\n')
        new_lines.append('\n')
        new_lines.append('        # 卡片容器提供白色背景和圆角\n')
        new_lines.append('        self.card_container = QFrame()\n')
        new_lines.append('        self.card_container.setObjectName("folderManagerCard")\n')
        new_lines.append('        self.card_container.setStyleSheet("""\n')
        new_lines.append('            QFrame#folderManagerCard {\n')
        new_lines.append('                background-color: #FFFFFF;\n')
        new_lines.append('                border-radius: 12px;\n')
        new_lines.append('            }\n')
        new_lines.append('        """)\n')
        i += 1
        continue
    
    # 替换 layout = QVBoxLayout(self) -> 设置在 card_container 上
    if 'layout = QVBoxLayout(self)' in line:
        new_lines.append('        layout = QVBoxLayout(self.card_container)\n')
        i += 1
        continue
    
    # 去掉 self.setStyleSheet('QDialog { background... })
    if "self.setStyleSheet('''QDialog { background:" in line:
        i += 1
        continue
    
    # 去掉表格的 border-radius
    if 'border-radius: 12px;' in line and 'QTableWidget' in str(new_lines[-5:-1]) if len(new_lines) >= 5 else '':
        new_lines.append('                border-radius: 12px;\n')
        # Already handled below
        pass
    
    # 替换表格的 border: 1px solid white; border-radius: 12px;
    if 'border: 1px solid white;' in line:
        new_lines.append('                border: none;\n')
        i += 1
        continue
    
    # 最后一处：在 layout.addWidget(self.table) 之后加 outer_layout.addWidget(self.card_container)
    new_lines.append(line)
    i += 1

with open(p, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("OK")
