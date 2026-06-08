import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """    def _execute_action(self, action):
        if not action or action == "end":
            return
        try:
            from utils import get_recordings_path, load_json_data
            folder_path = os.path.join(get_recordings_path(), action)
            json_path = os.path.join(folder_path, "recording.json")
            if not os.path.exists(json_path):
                self.log_signal.emit(f"找不到录制文件: {json_path}")
                return

            recording_data = load_json_data(json_path)
            if not recording_data:
                self.log_signal.emit(f"录制数据为空: {action}")
                return

            # 判断是图像录制还是坐标录制
            has_images = any(op.get("image", "") for op in recording_data)

            from image_recognition import replay_coordinate_operations, replay_coordinates_only

            if has_images:
                replay_coordinate_operations(
                    recording_data, folder_path,
                    replay_interval=0.5, consider_color=False,
                    stop_check=lambda: not self.running
                )
            else:
                replay_coordinates_only(
                    recording_data, replay_interval=0.3,
                    stop_check=lambda: not self.running
                )

            self.log_signal.emit(f"执行完成: {action}")"""

new = """    def _execute_action(self, action):
        if not action or action == "end":
            return True
        try:
            from utils import get_recordings_path, load_json_data
            folder_path = os.path.join(get_recordings_path(), action)
            json_path = os.path.join(folder_path, "recording.json")
            if not os.path.exists(json_path):
                if self._on_log:
                    self._on_log(f"找不到录制文件: {json_path}")
                return False

            recording_data = load_json_data(json_path)
            if not recording_data:
                if self._on_log:
                    self._on_log(f"录制数据为空: {action}")
                return False

            has_images = any(op.get("image", "") for op in recording_data)

            from image_recognition import replay_coordinate_operations, replay_coordinates_only

            if has_images:
                ok, total = replay_coordinate_operations(
                    recording_data, folder_path,
                    replay_interval=0.5, consider_color=False,
                    stop_check=lambda: not (self.running and self._main_app and hasattr(self._main_app, "replay_enabled") and self._main_app.replay_enabled)
                )
            else:
                ok, total = replay_coordinates_only(
                    recording_data, replay_interval=0.3,
                    stop_check=lambda: not (self.running and self._main_app and hasattr(self._main_app, "replay_enabled") and self._main_app.replay_enabled)
                )

            if ok == 0 and total > 0:
                if self._on_log:
                    self._on_log(f"执行失败: {action} 全部 {total} 个步骤均未成功")
                return False

            if self._on_log:
                self._on_log(f"执行完成: {action}")
            return True"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ _execute_action 替换成功，返回布尔值+检测全失败")
else:
    print("❌ 未匹配 _execute_action（内容不符）")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成")
