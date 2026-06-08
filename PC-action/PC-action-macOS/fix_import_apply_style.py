import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\combo_skill_edit_dialog.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = "from beautiful_dialog import StyledMessageDialog"
new = "from beautiful_dialog import StyledMessageDialog\nfrom styles import apply_dialog_style"

if old in content:
    content = content.replace(old, new, 1)
    print("✅ apply_dialog_style 导入已添加")
else:
    print("❌ 未匹配导入行")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启后即可正常查看条件图片")
