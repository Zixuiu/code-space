import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """    def _execute_action(self, action):
        if not action or action == "end":
            return
        try:
            from image_recognition import run_replay_for_folder
            run_replay_for_folder(action)
        except Exception as e:
            self.log_signal.emit(f"执行动作失败: {e}")"""

new = """    def _execute_action(self, action):
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

            self.log_signal.emit(f"执行完成: {action}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log_signal.emit(f"执行动作失败: {e}")"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ _execute_action 已修复，改为加载 recording.json + 真实回放")
else:
    print("❌ 未匹配 _execute_action")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启程序组合技即可正常执行回放")
