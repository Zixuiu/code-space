p = "d:/code空间/PC-action/PC-action-macOS/app.py"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace(
    'tw_w = QLabel(f"📝 {at.replace(\'文本: \', \'\')}")',
    'tw_w = QLabel("📝 文本")'
)
with open(p, "w", encoding="utf-8") as f:
    f.write(c)
print("OK")
