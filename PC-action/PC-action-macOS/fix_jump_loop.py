import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """                flow_index = 0
                visited_jumps = set()
                while flow_index < len(flows):
                    if not self.running:
                        break
                    self._current_flow_index = flow_index

                    flow = flows[flow_index]
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

                    # 处理跳转动作
                    if action and action.startswith("跳转_"):
                        try:
                            target = int(action.split("_")[1])
                        except (IndexError, ValueError):
                            target = -1
                        if 0 <= target < len(flows) and target not in visited_jumps:
                            visited_jumps.add(target)
                            flow_index = target
                            continue
                        elif target in visited_jumps:
                            self.log_signal.emit(f"检测到循环跳转，停止")
                            break
                        else:
                            flow_index += 1
                            continue"""

new = """                flow_index = 0
                total_jumps = 0
                max_jumps = max(200, len(flows) * 20)
                while flow_index < len(flows):
                    if not self.running:
                        break
                    self._current_flow_index = flow_index

                    flow = flows[flow_index]
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

                    # 处理跳转动作
                    if action and action.startswith("跳转_"):
                        try:
                            target = int(action.split("_")[1])
                        except (IndexError, ValueError):
                            target = -1
                        if 0 <= target < len(flows):
                            total_jumps += 1
                            if total_jumps > max_jumps:
                                self.log_signal.emit(f"跳转次数超过上限({max_jumps})，停止")
                                break
                            flow_index = target
                            continue
                        else:
                            flow_index += 1
                            continue"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ visited_jumps 已替换为 total_jumps 计数防御")
else:
    print("❌ 未匹配跳转逻辑")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启后跳转可无限循环")
