import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """class ComboSkillRunner(QObject):
    \"\"\"组合技执行器 - 在独立线程中运行组合技的各个流程\"\"\"
    finished = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str)
    step_signal = pyqtSignal(dict)

    def __init__(self, skill_data, parent=None):
        super().__init__(parent)
        self.skill_data = skill_data
        self.skill_id = \"\"
        self.running = False
        self.monitor_mode = False
        self.monitor_target_runner = None
        self._exec_thread = None
        self._current_flow_index = 0
        self._total_flows = len(skill_data.get(\"flows\", []))
        self._loop_count = skill_data.get(\"loop_count\", 1)
        self._current_loop = 1
        self._main_app = parent"""

new = """class ComboSkillRunner:
    \"\"\"组合技执行器 - 在独立线程中运行组合技的各个流程（纯Python回调）\"\"\"

    def __init__(self, skill_data, parent=None):
        self.skill_data = skill_data
        self.skill_id = \"\"
        self.running = False
        self.monitor_mode = False
        self.monitor_target_runner = None
        self._exec_thread = None
        self._current_flow_index = 0
        self._total_flows = len(skill_data.get(\"flows\", []))
        self._loop_count = skill_data.get(\"loop_count\", 1)
        self._current_loop = 1
        self._main_app = parent
        # 回调函数（线程安全，由主线程设置）
        self._on_finished = None
        self._on_log = None
        self._on_step = None"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ ComboSkillRunner 类定义已修复，添加了 _on_log 等回调属性")
else:
    print("❌ 未匹配类定义")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启即可")
