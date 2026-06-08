# -*- coding: utf-8 -*-
"""修复坐标表格3列问题"""
import re

with open(r'd:\code空间\PC-action\PC-action-macOS\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修改1：列宽设置 - 添加第3列Fixed模式
content = re.sub(
    r'(# 设置列宽)\s+'
    r'(table\.horizontalHeader\(\)\.setSectionResizeMode\(0, QHeaderView\.Stretch\))\s+'
    r'(table\.horizontalHeader\(\)\.setSectionResizeMode\(1, QHeaderView\.Stretch\))\s+'
    r'(table\.horizontalHeader\(\)\.setSectionResizeMode\(2, QHeaderView\.Stretch\))\s+'
    r'(layout\.addWidget\(table\))',
    lambda m: m.group(1) + '\n            ' + m.group(2) + '\n            ' + m.group(3) + '\n            ' + m.group(4) + '\n            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)\n            table.setColumnWidth(3, 50)\n\n            ' + m.group(5),
    content
)
print('✅ 修改1：列宽设置已修复')

# 修改2：在数据填充循环后添加删除按钮和_refresh_table函数
insert_code = '''
                # 删除按钮（第3列）
                _del_w = QWidget()
                _del_l = QHBoxLayout(_del_w)
                _del_l.setContentsMargins(0,0,0,0)
                _del_l.setAlignment(Qt.AlignCenter)
                _del_b = QPushButton("✕")
                _del_b.setFixedSize(26,26)
                _del_b.setStyleSheet("QPushButton{background:#FF3B30;color:white;border:none;border-radius:13px;font-size:13px;font-weight:bold;}QPushButton:hover{background:#E0342A;}")
                _del_b.setCursor(Qt.PointingHandCursor)
                _row_idx = i
                def _del_row_cb(checked=False, idx=_row_idx):
                    del recording_data[idx]
                    for _ii,_oo in enumerate(recording_data,1): _oo["step"]=_ii
                    save_json_data(recording_json_path, recording_data)
                    _refresh_table()
                _del_b.clicked.connect(_del_row_cb)
                _del_l.addWidget(_del_b)
                table.setCellWidget(i, 3, _del_w)

            # 表格刷新函数（删除后调用）
            def _refresh_table():
                table.setRowCount(len(recording_data))
                for _i,_o in enumerate(recording_data):
                    _tm = {"left_click":"左键点击","right_click":"右键点击","double_click":"双击","middle_click":"中键点击"}
                    table.setItem(_i,0,QTableWidgetItem(str(_o.get("step",_i+1)))); table.item(_i,0).setTextAlignment(Qt.AlignCenter)
                    table.setItem(_i,1,QTableWidgetItem(_tm.get(_o.get("action_type"),_o.get("action_type")))); table.item(_i,1).setTextAlignment(Qt.AlignCenter)
                    table.setItem(_i,2,QTableWidgetItem("("+str(_o.get("x",0))+", "+str(_o.get("y",0))+")")); table.item(_i,2).setTextAlignment(Qt.AlignCenter)
                    # 重新添加删除按钮
                    _dww = QWidget()
                    _dll = QHBoxLayout(_dww)
                    _dll.setContentsMargins(0,0,0,0)
                    _dll.setAlignment(Qt.AlignCenter)
                    _dbb = QPushButton("✕")
                    _dbb.setFixedSize(26,26)
                    _dbb.setStyleSheet("QPushButton{background:#FF3B30;color:white;border:none;border-radius:13px;font-size:13px;font-weight:bold;}QPushButton:hover{background:#E0342A;}")
                    _dbb.setCursor(Qt.PointingHandCursor)
                    _rii = _i
                    def _drr(checked=False, idx2=_rii):
                        del recording_data[idx2]
                        for _ii2,_oo2 in enumerate(recording_data,1): _oo2["step"]=_ii2
                        save_json_data(recording_json_path, recording_data)
                        _refresh_table()
                    _dbb.clicked.connect(_drr)
                    _dll.addWidget(_dbb)
                    table.setCellWidget(_i, 3, _dww)

            # 设置列宽'''

content = re.sub(
    r'(                table\.setItem\(i, 2, coord_item\))\s*\n(\s+)# 设置列宽',
    lambda m: m.group(1) + insert_code,
    content
)
print('✅ 修改2：删除按钮和刷新函数已添加')

# 修改3：修复_add_op回调中的刷新代码
content = re.sub(
    r'(save_json_data\(recording_json_path, recording_data\))\s*'
    r'table\.setRowCount\(len\(recording_data\)\)\s*'
    r'for _i,_o in enumerate\(recording_data\):\s*'
    r'_tm = \{"left_click":"左键点击","right_click":"右键点击","double_click":"双击","middle_click":"中键点击"\}\s*'
    r'table\.setItem\(_i,0,QTableWidgetItem\(str\(_o\.get\("step",_i\+1\)\)\)\); table\.item\(_i,0\)\.setTextAlignment\(Qt\.AlignCenter\)\s*'
    r'table\.setItem\(_i,1,QTableWidgetItem\(_tm\.get\(_o\.get\("action_type"\),_o\.get\("action_type"\)\)\)\); table\.item\(_i,1\)\.setTextAlignment\(Qt\.AlignCenter\)\s*'
    r'table\.setItem\(_i,2,QTableWidgetItem\("\("\+str\(_o\.get\("x",0\)\)\+", "\+str\(_o\.get\("y",0\)\)\+"\)"\)\); table\.item\(_i,2\)\.setTextAlignment\(Qt\.AlignCenter\)\s*'
    r'(_ov\.accept\(\))',
    lambda m: m.group(1) + '\n                        _refresh_table()\n                        ' + m.group(2),
    content
)
print('✅ 修改3：添加操作回调已修复')

with open(r'd:\code空间\PC-action\PC-action-macOS\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n🎉 全部修复完成！请重启程序')
