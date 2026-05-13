import os
import json

config_path = r'e:\code\PC-action\resent\dist\PC-action\user_data\shortcuts_admin.json'
with open(config_path, 'r', encoding='utf-8') as f:
    loaded_shortcuts = json.load(f)

print('loaded_shortcuts:', loaded_shortcuts)

shortcuts = {}
for folder_path, shortcut in loaded_shortcuts.items():
    normalized_path = os.path.normpath(folder_path)
    print(f'\nfolder_path: {folder_path}')
    print(f'normalized_path: {normalized_path}')
    print(f'exists: {os.path.exists(normalized_path)}')
    
    if os.path.exists(normalized_path):
        shortcuts[normalized_path.lower()] = shortcut
        print(f'  saved: {normalized_path.lower()} -> {shortcut}')

print(f'\nfinal shortcuts: {shortcuts}')
