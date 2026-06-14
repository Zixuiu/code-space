import os

p1 = r"d:\code空间\PC-action\PC-action-macOS\app_macos.py"
p2 = r"d:\code空间\PC-action\PC-action-macOS\app.py"

with open(p1, "r", encoding="utf-8") as f:
    c1 = f.read()
with open(p2, "r", encoding="utf-8") as f:
    c2 = f.read()

o1 = '        def do_delete():\n            try:\n                trash_dir = os.path.join(os.path.dirname(folder_path), \'trash\')\n                if not os.path.exists(trash_dir):\n                    os.makedirs(trash_dir)\n                import shutil\n                shutil.move(folder_path, os.path.join(trash_dir, os.path.basename(folder_path)))\n                # \u540c\u65f6\u6e05\u7406\u8be5\u6587\u4ef6\u5939\u7684\u5feb\u6377\u952e\n                normalized_path = os.path.normpath(str(folder_path))\n                keys_to_delete = []\n                for key in self.shortcuts.keys():\n                    if os.path.normpath(str(key)).lower() == normalized_path.lower():\n                        keys_to_delete.append(key)\n                for key in keys_to_delete:\n                    del self.shortcuts[key]\n                if keys_to_delete:\n                    self.save_shortcut_config()\n                self.load_folders_to_table(table_widget)\n                dialog.accept()'

n1 = '        def do_delete():\n            try:\n                from datetime import datetime as _dt\n                trash_dir = os.path.join(os.path.dirname(folder_path), \'trash\')\n                if not os.path.exists(trash_dir):\n                    os.makedirs(trash_dir)\n                import shutil\n                timestamp = _dt.now().strftime(\'_%Y%m%d_%H%M%S\')\n                trash_folder_name = os.path.basename(folder_path) + timestamp\n                shutil.move(folder_path, os.path.join(trash_dir, trash_folder_name))\n                self.update_trash_index(trash_folder_name, os.path.basename(folder_path), folder_path)\n                normalized_path = os.path.normpath(str(folder_path))\n                keys_to_delete = []\n                for key in list(self.shortcuts.keys()):\n                    if os.path.normpath(str(key)).lower() == normalized_path.lower():\n                        keys_to_delete.append(key)\n                for key in keys_to_delete:\n                    del self.shortcuts[key]\n                if keys_to_delete:\n                    self.save_shortcut_config()\n                    self.update_shortcuts()\n                self.load_folders_to_table(table_widget)\n                dialog.accept()'

if o1 in c1:
    c1 = c1.replace(o1, n1)
    print("[OK] app_macos.py: do_delete fixed")
else:
    print("[WARN] app_macos.py: do_delete not matched")

o2 = '    def delete_folder_in_tab(self, folder_path, table_widget):\n        """\u5728Tab\u4e2d\u5220\u9664\u6d41\u7a0b"""\n        reply = self.show_beautiful_message(\'question\', "\u786e\u8ba4\u5220\u9664", f"\u786e\u5b9a\u8981\u5220\u9664\u6d41\u7a0b \'{os.path.basename(folder_path)}\'?", buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No)\n        if reply == QMessageBox.Yes:\n            try:\n                # \u79fb\u52a8\u5230\u56de\u6536\u7ad9\n                trash_dir = os.path.join(os.path.dirname(folder_path), \'trash\')\n                if not os.path.exists(trash_dir):\n                    os.makedirs(trash_dir)\n                import shutil\n                shutil.move(folder_path, os.path.join(trash_dir, os.path.basename(folder_path)))\n                # print(f"\u5df2\u5220\u9664\u6d41\u7a0b: {folder_path}")  # [\u65e5\u5fd7\u5df2\u7981\u7528]\n                self.load_folders_to_table(table_widget)\n            except Exception as e:\n                self.show_beautiful_message(\'critical\', \'\u9519\u8bef\', f"\u5220\u9664\u5931\u8d25: {e}")'

n2 = '    def delete_folder_in_tab(self, folder_path, table_widget):\n        """\u5728Tab\u4e2d\u5220\u9664\u6d41\u7a0b"""\n        reply = self.show_beautiful_message(\'question\', "\u786e\u8ba4\u5220\u9664", f"\u786e\u5b9a\u8981\u5220\u9664\u6d41\u7a0b \'{os.path.basename(folder_path)}\'?", buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No)\n        if reply == QMessageBox.Yes:\n            try:\n                from datetime import datetime as _dt\n                trash_dir = os.path.join(os.path.dirname(folder_path), \'trash\')\n                if not os.path.exists(trash_dir):\n                    os.makedirs(trash_dir)\n                import shutil\n                timestamp = _dt.now().strftime(\'_%Y%m%d_%H%M%S\')\n                trash_folder_name = os.path.basename(folder_path) + timestamp\n                shutil.move(folder_path, os.path.join(trash_dir, trash_folder_name))\n                self.update_trash_index(trash_folder_name, os.path.basename(folder_path), folder_path)\n                normalized_path = os.path.normpath(str(folder_path))\n                keys_to_delete = []\n                for key in list(self.shortcuts.keys()):\n                    if os.path.normpath(str(key)).lower() == normalized_path.lower():\n                        keys_to_delete.append(key)\n                for key in keys_to_delete:\n                    del self.shortcuts[key]\n                if keys_to_delete:\n                    self.save_shortcut_config()\n                    self.update_shortcuts()\n                self.load_folders_to_table(table_widget)\n            except Exception as e:\n                self.show_beautiful_message(\'critical\', \'\u9519\u8bef\', f"\u5220\u9664\u5931\u8d25: {e}")'

if o2 in c2:
    c2 = c2.replace(o2, n2)
    print("[OK] app.py: delete_folder_in_tab fixed")
else:
    print("[WARN] app.py: delete_folder_in_tab not matched")

o3 = '        """)\n        content_layout.addWidget(trash_table)\n\n        btn_row = QHBoxLayout()'

n3_lines = [
    '        """)',
    '        content_layout.addWidget(trash_table)',
    '',
    '        def _load_trash_data():',
    '            from utils import get_recordings_path',
    '            recordings_dir = get_recordings_path()',
    '            trash_dir = os.path.join(recordings_dir, \'trash\')',
    '            index_file = os.path.join(trash_dir, \'trash_index.json\')',
    '            index_data = []',
    '            if os.path.exists(index_file):',
    '                try:',
    '                    with open(index_file, \'r\', encoding=\'utf-8\') as f:',
    '                        index_data = json.load(f)',
    '                except:',
    '                    pass',
    '            trash_table.setRowCount(len(index_data))',
    '            for i, item in enumerate(index_data):',
    '                check_item = QTableWidgetItem("")',
    '                check_item.setData(Qt.UserRole, item)',
    '                check_item.setTextAlignment(Qt.AlignCenter)',
    '                trash_table.setItem(i, 0, check_item)',
    '                name_item = QTableWidgetItem(item.get(\'original_name\', \'\'))',
    '                name_item.setTextAlignment(Qt.AlignCenter)',
    '                name_item.setData(Qt.UserRole, item)',
    '                trash_table.setItem(i, 1, name_item)',
    '                time_item = QTableWidgetItem(item.get(\'deleted_time\', \'\'))',
    '                time_item.setTextAlignment(Qt.AlignCenter)',
    '                trash_table.setItem(i, 2, time_item)',
    '            count_label.setText(f"{len(index_data)} \\u9879")',
    '        _load_trash_data()',
    '',
    '        btn_row = QHBoxLayout()',
]
n3 = '\n'.join(n3_lines)

if o3 in c2:
    c2 = c2.replace(o3, n3)
    print("[OK] app.py: open_trash_dialog data loading added")
else:
    print("[WARN] app.py: open_trash_dialog trash_table block not matched")

new_methods = '\n    def restore_selected_trash(self, trash_table, count_label):\n        try:\n            rows = set()\n            for item in trash_table.selectedItems():\n                rows.add(item.row())\n            if not rows:\n                self.show_beautiful_message(\'information\', \'\u63d0\u793a\', \'\u8bf7\u5148\u9009\u62e9\u8981\u6062\u590d\u7684\u6d41\u7a0b\')\n                return\n            from utils import get_recordings_path\n            recordings_dir = get_recordings_path()\n            trash_dir = os.path.join(recordings_dir, \'trash\')\n            import shutil\n            for row in sorted(rows, reverse=True):\n                item_data = trash_table.item(row, 0).data(Qt.UserRole)\n                if not item_data:\n                    continue\n                trash_folder_name = item_data[\'trash_folder_name\']\n                original_path = item_data[\'original_path\']\n                original_name = item_data[\'original_name\']\n                trash_folder_path = os.path.join(trash_dir, trash_folder_name)\n                if not os.path.exists(trash_folder_path):\n                    continue\n                restore_path = original_path\n                if os.path.exists(original_path):\n                    from datetime import datetime as _dt\n                    timestamp = _dt.now().strftime(\'_%Y%m%d_%H%M%S\')\n                    restore_path = os.path.join(os.path.dirname(original_path), original_name + timestamp)\n                shutil.move(trash_folder_path, restore_path)\n                self.remove_from_trash_index(trash_folder_name)\n            self._reload_trash_table(trash_table, count_label)\n        except Exception as e:\n            self.show_beautiful_message(\'critical\', \'\u9519\u8bef\', f"\u6062\u590d\u5931\u8d25: {e}")\n\n    def delete_selected_trash(self, trash_table, count_label):\n        try:\n            rows = set()\n            for item in trash_table.selectedItems():\n                rows.add(item.row())\n            if not rows:\n                self.show_beautiful_message(\'information\', \'\u63d0\u793a\', \'\u8bf7\u5148\u9009\u62e9\u8981\u6c38\u4e45\u5220\u9664\u7684\u6d41\u7a0b\')\n                return\n            reply = self.show_beautiful_message(\'question\', \'\u786e\u8ba4\', \'\u786e\u5b9a\u8981\u6c38\u4e45\u5220\u9664\u9009\u4e2d\u7684\u6d41\u7a0b\u5417\uff1f\u6b64\u64cd\u4f5c\u4e0d\u53ef\u64a4\u9500\uff01\', buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No)\n            if reply != QMessageBox.Yes:\n                return\n            from utils import get_recordings_path\n            recordings_dir = get_recordings_path()\n            trash_dir = os.path.join(recordings_dir, \'trash\')\n            import shutil\n            for row in sorted(rows, reverse=True):\n                item_data = trash_table.item(row, 0).data(Qt.UserRole)\n                if not item_data:\n                    continue\n                trash_folder_name = item_data[\'trash_folder_name\']\n                trash_folder_path = os.path.join(trash_dir, trash_folder_name)\n                if os.path.exists(trash_folder_path):\n                    shutil.rmtree(trash_folder_path)\n                self.remove_from_trash_index(trash_folder_name)\n            self._reload_trash_table(trash_table, count_label)\n        except Exception as e:\n            self.show_beautiful_message(\'critical\', \'\u9519\u8bef\', f"\u5220\u9664\u5931\u8d25: {e}")\n\n    def clear_trash_dialog(self, trash_table, count_label):\n        try:\n            reply = self.show_beautiful_message(\'question\', \'\u786e\u8ba4\', \'\u786e\u5b9a\u8981\u6e05\u7a7a\u56de\u6536\u7ad9\u5417\uff1f\u6b64\u64cd\u4f5c\u4e0d\u53ef\u64a4\u9500\uff01\', buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No)\n            if reply != QMessageBox.Yes:\n                return\n            from utils import get_recordings_path\n            recordings_dir = get_recordings_path()\n            trash_dir = os.path.join(recordings_dir, \'trash\')\n            import shutil\n            if os.path.exists(trash_dir):\n                for item in os.listdir(trash_dir):\n                    item_path = os.path.join(trash_dir, item)\n                    if os.path.isdir(item_path):\n                        shutil.rmtree(item_path)\n                    else:\n                        os.remove(item_path)\n            self._reload_trash_table(trash_table, count_label)\n        except Exception as e:\n            self.show_beautiful_message(\'critical\', \'\u9519\u8bef\', f"\u6e05\u7a7a\u5931\u8d25: {e}")\n\n    def _reload_trash_table(self, trash_table, count_label):\n        from utils import get_recordings_path\n        recordings_dir = get_recordings_path()\n        trash_dir = os.path.join(recordings_dir, \'trash\')\n        index_file = os.path.join(trash_dir, \'trash_index.json\')\n        index_data = []\n        if os.path.exists(index_file):\n            try:\n                with open(index_file, \'r\', encoding=\'utf-8\') as f:\n                    index_data = json.load(f)\n            except:\n                pass\n        trash_table.setRowCount(len(index_data))\n        for i, item in enumerate(index_data):\n            check_item = QTableWidgetItem("")\n            check_item.setData(Qt.UserRole, item)\n            check_item.setTextAlignment(Qt.AlignCenter)\n            trash_table.setItem(i, 0, check_item)\n            name_item = QTableWidgetItem(item.get(\'original_name\', \'\'))\n            name_item.setTextAlignment(Qt.AlignCenter)\n            name_item.setData(Qt.UserRole, item)\n            trash_table.setItem(i, 1, name_item)\n            time_item = QTableWidgetItem(item.get(\'deleted_time\', \'\'))\n            time_item.setTextAlignment(Qt.AlignCenter)\n            trash_table.setItem(i, 2, time_item)\n        count_label.setText(f"{len(index_data)} \\u9879")\n\n'

anchor = '    def refresh_floating_window_list(self):'
if anchor in c2 and 'def restore_selected_trash' not in c2:
    c2 = c2.replace(anchor, new_methods + anchor)
    print("[OK] app.py: missing trash methods added")
elif 'def restore_selected_trash' in c2:
    print("[SKIP] app.py: restore_selected_trash already exists")
else:
    print("[WARN] app.py: anchor not found")

with open(p1, "w", encoding="utf-8") as f:
    f.write(c1)
with open(p2, "w", encoding="utf-8") as f:
    f.write(c2)

print("\n=== Done ===")
