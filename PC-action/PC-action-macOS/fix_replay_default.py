import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """        self.replay_enabled = True  # 回放功能开关（默认开启，按钮显示"开始回放"）"""
new = """        self.replay_enabled = False  # 回放功能开关（默认关闭）"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ 回放默认状态已改为关闭")
else:
    print("❌ 未匹配")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启后回放默认关闭")
