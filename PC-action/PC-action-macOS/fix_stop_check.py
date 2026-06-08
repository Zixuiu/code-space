import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 修复 stop_check - 去掉 replay_enabled 判断，只检查 self.running
old = """                    stop_check=lambda: not (self.running and self._main_app and hasattr(self._main_app, "replay_enabled") and self._main_app.replay_enabled)"""

new = """                    stop_check=lambda: not self.running"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ stop_check 已修复 - 去掉 replay_enabled 限制，只检查 self.running")
else:
    print("❌ 未匹配 stop_check（replay_enabled版本）")

# 可能有两个地方（coordinates_only 版本）
old2 = """                    stop_check=lambda: not (self.running and self._main_app and hasattr(self._main_app, "replay_enabled") and self._main_app.replay_enabled)"""
# same as above, replace_all should work

count_before = content.count("stop_check=lambda: not (self.running and self._main_app")
content = content.replace(old2, "                    stop_check=lambda: not self.running")
count_after = content.count("stop_check=lambda: not (self.running and self._main_app")
print(f"✅ 替换了共 {count_before - count_after} 处 stop_check")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启后组合技即可正常运行")
