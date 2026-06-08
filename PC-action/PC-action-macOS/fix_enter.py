# -*- coding: utf-8 -*-
"""给添加坐标的遮罩添加回车键支持"""
import re

with open(r'd:\code空间\PC-action\PC-action-macOS\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在 _kp 函数中添加回车键支持
old_kp = '''                def _kp(ev):
                    if ev.key() == Qt.Key_Escape:
                        _ov.reject()'''

new_kp = '''                def _kp(ev):
                    if ev.key() == Qt.Key_Escape:
                        _ov.reject()
                    elif ev.key() in (Qt.Key_Return, Qt.Key_Enter):
                        # 回车键：用鼠标当前位置作为坐标
                        _cursor = QCursor.pos()
                        _screen = QApplication.primaryScreen(); _dpr = _screen.devicePixelRatio() if _screen else 1.0
                        _x = int(_cursor.x() * _dpr); _y = int(_cursor.y() * _dpr)
                        recording_data.append({"step":len(recording_data)+1,"action_type":"left_click","x":_x,"y":_y,"delay":0.3})
                        for _i,_o in enumerate(recording_data,1): _o["step"]=_i
                        save_json_data(recording_json_path, recording_data)
                        _refresh_table()
                        _ov.accept()'''

if old_kp in content:
    content = content.replace(old_kp, new_kp, 1)
    print('✅ 成功：回车键现在会使用鼠标当前位置记录坐标')
else:
    print('❌ 失败：未找到匹配代码，尝试备选...')
    # 备选：不同缩进
    for indent in ['            ', '                ', '                    ']:
        alt_old = f'{indent}def _kp(ev):\n{indent}    if ev.key() == Qt.Key_Escape:\n{indent}        _ov.reject()'
        if alt_old in content:
            alt_new = f'''{indent}def _kp(ev):
{indent}    if ev.key() == Qt.Key_Escape:
{indent}        _ov.reject()
{indent}    elif ev.key() in (Qt.Key_Return, Qt.Key_Enter):
{indent}        # 回车键：用鼠标当前位置作为坐标
{indent}        _cursor = QCursor.pos()
{indent}        _screen = QApplication.primaryScreen(); _dpr = _screen.devicePixelRatio() if _screen else 1.0
{indent}        _x = int(_cursor.x() * _dpr); _y = int(_cursor.y() * _dpr)
{indent}        recording_data.append({{"step":len(recording_data)+1,"action_type":"left_click","x":_x,"y":_y,"delay":0.3}})
{indent}        for _i,_o in enumerate(recording_data,1): _o["step"]=_i
{indent}        save_json_data(recording_json_path, recording_data)
{indent}        _refresh_table()
{indent}        _ov.accept()'''
            content = content.replace(alt_old, alt_new, 1)
            print(f'✅ 成功（备选）：回车键支持已添加')
            break

with open(r'd:\code空间\PC-action\PC-action-macOS\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n🎉 修复完成！按下回车键会用鼠标当前位置记录坐标。')
