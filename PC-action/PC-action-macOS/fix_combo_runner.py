import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

new_class = '''
class ComboSkillRunner(QObject):
    """组合技执行器 - 在独立线程中运行组合技的各个流程"""
    finished = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str)
    step_signal = pyqtSignal(dict)

    def __init__(self, skill_data, parent=None):
        super().__init__(parent)
        self.skill_data = skill_data
        self.skill_id = ""
        self.running = False
        self.monitor_mode = False
        self.monitor_target_runner = None
        self._exec_thread = None
        self._current_flow_index = 0
        self._total_flows = len(skill_data.get("flows", []))
        self._loop_count = skill_data.get("loop_count", 1)
        self._current_loop = 1
        self._main_app = parent

    def isRunning(self):
        return self.running

    def reset(self):
        """重置执行状态，下次从第一个流程开始"""
        self._current_flow_index = 0
        self._current_loop = 1

    def run(self):
        """执行组合技的所有流程"""
        self.running = True
        try:
            flows = self.skill_data.get("flows", [])
            total_loops = max(1, self._loop_count)

            for loop in range(1, total_loops + 1):
                if not self.running:
                    break
                self._current_loop = loop

                for flow_index, flow in enumerate(flows):
                    if not self.running:
                        break
                    self._current_flow_index = flow_index

                    action = flow.get("action", "")
                    condition = flow.get("condition", "always")

                    step_info = {
                        "step_num": flow_index + 1,
                        "total_steps": len(flows),
                        "condition": condition,
                        "action": action,
                        "branch": "主分支",
                        "loop": loop,
                        "total_loops": total_loops,
                    }
                    self.step_signal.emit(step_info)

                    if condition == "always":
                        self._execute_action(action)
                    elif condition == "delay":
                        import time
                        delay_seconds = flow.get("delay_after", 1)
                        self._wait_interruptible(delay_seconds)
                    elif condition == "wait_for_image":
                        self._execute_action(action)

                    if self.running and flow_index < len(flows) - 1:
                        self._wait_interruptible(0.3)

                self.reset()

            if self.running:
                self.finished.emit(True, f"组合技 '{self.skill_data.get('name', '')}' 执行完成")
            else:
                self.finished.emit(False, "已停止")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, f"执行失败: {str(e)}")
        finally:
            self.running = False

    def _execute_action(self, action):
        if not action or action == "end":
            return
        try:
            from image_recognition import run_replay_for_folder
            run_replay_for_folder(action)
        except Exception as e:
            self.log_signal.emit(f"执行动作失败: {e}")

    def _wait_interruptible(self, seconds):
        import time
        interval = 0.1
        elapsed = 0
        while self.running and elapsed < seconds:
            time.sleep(interval)
            elapsed += interval

'''

old = "class ComboSkillManager:"
new = new_class + "\n\nclass ComboSkillManager:"

if old in content:
    content = content.replace(old, new, 1)
    print("✅ ComboSkillRunner 类已插入")
else:
    print("❌ 未匹配 class ComboSkillManager")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启程序组合技即可正常使用")
