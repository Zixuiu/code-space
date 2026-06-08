import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 在 run() 开头加日志，并确保 import find_image_with_timeout 不会失败
old = """        self.running = True
        self._consecutive_failures = 0
        try:
            flows = self.skill_data.get("flows", [])
            total_loops = max(1, self._loop_count)
            from image_recognition import find_image_with_timeout"""

new = """        self.running = True
        self._consecutive_failures = 0
        if self._on_log:
            self._on_log(f"组合技开始执行: {self.skill_data.get('name', '')}")
            self._on_log(f"流程数: {len(self.skill_data.get('flows', []))}, 循环次数: {self._loop_count}")
        try:
            flows = self.skill_data.get("flows", [])
            total_loops = max(1, self._loop_count)
            # 预导入
            from image_recognition import find_image_with_timeout
            if self._on_log:
                self._on_log(f"find_image_with_timeout 导入成功")
                if flows:
                    self._on_log(f"流程0数据: {str(flows[0])[:200]}")"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ run() 开头已添加调试日志")
else:
    print("❌ 未匹配 run() 开头")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启后看日志输出定位问题")
