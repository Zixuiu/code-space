import sys
sys.stdout.reconfigure(encoding="utf-8")

# 1. 修复 app_macos.py
path = "d:\\code空间\\PC-action\\PC-action-macOS\\app_macos.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """        # 暂时不加载组合技，避免崩溃
        combo_skills = []"""

new = """        # 从管理器加载组合技
        combo_skills = self._get_combo_manager().combo_skills"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ app_macos.py 已修复 → combo_skills 从管理器加载")
else:
    print("❌ app_macos.py 未匹配")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

# 2. 修复 app.py（父类）
path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old2 = """        # 暂时不加载组合技，避免崩溃
        combo_skills = []"""

new2 = """        # 从管理器加载组合技
        combo_skills = self.combo_skills if hasattr(self, 'combo_skills') else []"""

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("✅ app.py 已修复 → combo_skills 从 self.combo_skills 加载")
else:
    print("❌ app.py 未匹配")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("\n🎯 完成！重启程序后组合技列表就能显示了")
