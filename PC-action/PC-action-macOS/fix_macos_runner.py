import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app_macos.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """            runner.finished.connect(lambda success, msg, sid=skill_id: self._on_combo_skill_finished(success, msg, sid))
            runner.step_signal.connect(lambda step_info, sid=skill_id: self._on_combo_step_changed(step_info, sid))"""

new = """            runner._on_finished = lambda success, msg, sid=skill_id: self._on_combo_skill_finished(success, msg, sid)
            runner._on_step = lambda step_info, sid=skill_id: self._on_combo_step_changed(step_info, sid)"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ app_macos.py 信号连接已改为回调赋值")
else:
    print("❌ 未匹配")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启即可")
