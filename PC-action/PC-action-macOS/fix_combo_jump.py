import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """    def run(self):
        \"""执行组合技的所有流程\"""
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
            self.running = False"""

new = """    def run(self):
        \"""执行组合技的所有流程（支持跳转）\"""
        self.running = True
        try:
            flows = self.skill_data.get("flows", [])
            total_loops = max(1, self._loop_count)

            for loop in range(1, total_loops + 1):
                if not self.running:
                    break
                self._current_loop = loop

                flow_index = 0
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
                            continue
                    elif action == "end":
                        break

                    # 执行流程动作
                    if condition == "always":
                        self._execute_action(action)
                    elif condition == "delay":
                        delay_seconds = flow.get("delay_after", 1)
                        self._wait_interruptible(delay_seconds)
                    elif condition == "wait_for_image":
                        self._execute_action(action)

                    if self.running:
                        self._wait_interruptible(0.3)

                    flow_index += 1

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
            self.running = False"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ run() 已重写为 while 循环，支持跳转动作")
else:
    print("❌ 未匹配 run() 方法")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启后组合技即可正常执行跳转")
