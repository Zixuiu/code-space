import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 替换 _execute_action，返回成功数并检测全失败
old = """    def _execute_action(self, action):
        if not action or action == "end":
            return
        try:
            from utils import get_recordings_path, load_json_data
            folder_path = os.path.join(get_recordings_path(), action)
            json_path = os.path.join(folder_path, "recording.json")
            if not os.path.exists(json_path):
                if self._on_log:
                    self._on_log(f"找不到录制文件: {json_path}")
                return

            recording_data = load_json_data(json_path)
            if not recording_data:
                if self._on_log:
                    self._on_log(f"录制数据为空: {action}")
                return

            # 判断是图像录制还是坐标录制
            has_images = any(op.get("image", "") for op in recording_data)

            from image_recognition import replay_coordinate_operations, replay_coordinates_only

            if has_images:
                replay_coordinate_operations(
                    recording_data, folder_path,
                    replay_interval=0.5, consider_color=False,
                    stop_check=lambda: not (self.running and self._main_app and hasattr(self._main_app, 'replay_enabled') and self._main_app.replay_enabled)
                )
            else:
                replay_coordinates_only(
                    recording_data, replay_interval=0.3,
                    stop_check=lambda: not (self.running and self._main_app and hasattr(self._main_app, 'replay_enabled') and self._main_app.replay_enabled)
                )

            if self._on_log:
                    self._on_log(f"执行完成: {action}")"""

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
                    stop_check=lambda: not (self.running and self._main_app and hasattr(self._main_app, 'replay_enabled') and self._main_app.replay_enabled)
                )
            else:
                ok, total = replay_coordinates_only(
                    recording_data, replay_interval=0.3,
                    stop_check=lambda: not (self.running and self._main_app and hasattr(self._main_app, 'replay_enabled') and self._main_app.replay_enabled)
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
    print("✅ _execute_action 已改为返回布尔值，检测全失败")
else:
    print("❌ 未匹配 _execute_action")

# 2. 在 run() 方法里，执行完流程动作后检查结果，连续失败则停止
old2 = """                    # 执行流程动作
                    if condition == "always":
                        self._execute_action(action)
                    elif condition == "delay":
                        delay_seconds = flow.get("delay_after", 1)
                        self._wait_interruptible(delay_seconds)
                    elif condition == "wait_for_image":
                        self._execute_action(action)"""

new2 = """                    # 执行流程动作 & 连续失败检测
                    _action_ok = True
                    if condition == "always":
                        _action_ok = self._execute_action(action)
                    elif condition == "delay":
                        delay_seconds = flow.get("delay_after", 1)
                        self._wait_interruptible(delay_seconds)
                    elif condition == "wait_for_image":
                        _action_ok = self._execute_action(action)

                    # 如果动作全部失败（如图片找不到），累计失败次数，超过3次停止循环
                    if not _action_ok and action and not action.startswith("跳转_") and action != "end":
                        self._consecutive_failures = getattr(self, '_consecutive_failures', 0) + 1
                        if self._consecutive_failures >= 3:
                            if self._on_log:
                                self._on_log(f"连续 {self._consecutive_failures} 次执行失败，停止组合技")
                            break
                    else:
                        self._consecutive_failures = 0"""

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("✅ run() 中已添加连续失败检测")
else:
    print("❌ 未匹配 run() 中的流程动作执行")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("\n🎯 完成！重启后组合技在找不到图片时会自动停止，不再卡死")
