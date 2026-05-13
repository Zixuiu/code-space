import os
import json
import sys

config_path = r'e:\code\PC-action\resent\dist\PC-action\user_data\shortcuts_admin.json'
with open(config_path, 'r', encoding='utf-8') as f:
    shortcuts = json.load(f)

print('shortcuts:', shortcuts)
recordings = r'e:\code\PC-action\resent\dist\PC-action\recordings'
print('recordings:', recordings)

for item in os.listdir(recordings):
    if os.path.isdir(os.path.join(recordings, item)) and item != 'trash':
        path = os.path.join(recordings, item)
        norm = os.path.normpath(path)
        norm_lower = norm.lower()
        print(f'\nitem: {item}')
        print(f'  norm: {norm}')
        print(f'  norm_lower: {norm_lower}')
        
        for stored_path, shortcut in shortcuts.items():
            stored_norm = os.path.normpath(stored_path).lower()
            print(f'  stored: {stored_path}')
            print(f'    stored_norm: {stored_norm}')
            print(f'    match: {stored_norm == norm_lower}')
