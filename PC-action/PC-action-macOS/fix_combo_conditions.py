import sys
sys.stdout.reconfigure(encoding="utf-8")

path = "d:\\code空间\\PC-action\\PC-action-macOS\\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """    def run(self):
        \"\"\"执行组合技的所有流程（支持跳转）\"\"\"
        self.running = True
        try:
            flows = self.skill_data.get(\"flows\", [])
            total_loops = max(1, self._loop_count)

            for loop in range(1, total_loops + 1):
                if not self.running:
                    break
                self._current_loop = loop

                flow_index = 0
                total_jumps = 0
                max_jumps = max(200, len(flows) * 20)
                while flow_index < len(flows):
                    if not self.running:
                        break
                    self._current_flow_index = flow_index

                    flow = flows[flow_index]
                    action = flow.get(\"action\", \"\")
                    condition = flow.get(\"condition\", \"always\")

                    step_info = {
                        \"step_num\": flow_index + 1,
                        \"total_steps\": len(flows),
                        \"condition\": condition,
                        \"action\": action,
                        \"branch\": \"主分支\",
                        \"loop\": loop,
                        \"total_loops\": total_loops,
                    }
                    self.step_signal.emit(step_info)

                    # 处理跳转动作
                    if action and action.startswith(\"跳转_\"):
                        try:
                            target = int(action.split(\"_\")[1])
                        except (IndexError, ValueError):
                            target = -1
                        if 0 <= target < len(flows):
                            total_jumps += 1
                            if total_jumps > max_jumps:
                                self.log_signal.emit(f\"跳转次数超过上限({max_jumps})，停止\")
                                break
                            flow_index = target
                            continue
                        else:
                            flow_index += 1
                            continue
                    elif action == \"end\":
                        break

                    # 执行流程动作 & 连续失败检测
                    _action_ok = True
                    if condition == \"always\":
                        _action_ok = self._execute_action(action)
                    elif condition == \"delay\":
                        delay_seconds = flow.get(\"delay_after\", 1)
                        self._wait_interruptible(delay_seconds)
                    elif condition == \"wait_for_image\":
                        _action_ok = self._execute_action(action)

                    # 如果动作全部失败（如图片找不到），累计失败次数，超过3次停止循环
                    if not _action_ok and action and not action.startswith(\"跳转_\") and action != \"end\":
                        self._consecutive_failures = getattr(self, '_consecutive_failures', 0) + 1
                        if self._consecutive_failures >= 3:
                            if self._on_log:
                                self._on_log(f\"连续 {self._consecutive_failures} 次执行失败，停止组合技\")
                            break
                    else:
                        self._consecutive_failures = 0

                    if self.running:
                        self._wait_interruptible(0.3)

                    flow_index += 1

                self.reset()

            if self.running:
                self.finished.emit(True, f\"组合技 '{self.skill_data.get('name', '')}' 执行完成\")
            else:
                self.finished.emit(False, \"已停止\")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, f\"执行失败: {str(e)}\")
        finally:
            self.running = False"""

new = """    def run(self):
        \"\"\"执行组合技的所有流程（支持条件、else分支、跳转）\"\"\"
        self.running = True
        self._consecutive_failures = 0
        try:
            flows = self.skill_data.get(\"flows\", [])
            total_loops = max(1, self._loop_count)
            from image_recognition import find_image_with_timeout

            for loop in range(1, total_loops + 1):
                if not self.running:
                    break
                self._current_loop = loop

                flow_index = 0
                total_jumps = 0
                max_jumps = max(200, len(flows) * 20)
                while flow_index < len(flows):
                    if not self.running:
                        break
                    self._current_flow_index = flow_index
                    flow = flows[flow_index]
                    action = flow.get(\"action\", \"\")
                    condition = flow.get(\"condition\", \"always\")
                    else_branch = flow.get(\"else_branch\") or {}

                    # ====== 1. 判断条件 ======
                    condition_met = True   # 主分支是否满足条件
                    condition_image = flow.get(\"condition_image\", \"\")

                    if condition == \"image_found\" and condition_image:
                        loc = find_image_with_timeout(condition_image, confidence=0.8, timeout=0.3, consider_color=False, stop_check=lambda: not self.running)
                        condition_met = loc is not None
                    elif condition == \"image_not_found\" and condition_image:
                        loc = find_image_with_timeout(condition_image, confidence=0.8, timeout=0.3, consider_color=False, stop_check=lambda: not self.running)
                        condition_met = loc is None
                    elif condition == \"wait_for_image\" and condition_image:
                        wait_timeout = flow.get(\"wait_timeout\", 30)
                        loc = find_image_with_timeout(condition_image, confidence=0.8, timeout=float(wait_timeout), consider_color=False, stop_check=lambda: not self.running)
                        condition_met = loc is not None

                    # ====== 2. 决定执行哪个分支的动作 ======
                    use_branch = \"main\" if condition_met else \"else\"
                    branch_label = \"主分支\" if condition_met else \"Else分支\"
                    target_action = action if condition_met else else_branch.get(\"action\", \"\")
                    target_else_branch = else_branch if not condition_met else None

                    step_info = {
                        \"step_num\": flow_index + 1,
                        \"total_steps\": len(flows),
                        \"condition\": condition,
                        \"action\": target_action,
                        \"branch\": branch_label,
                        \"loop\": loop,
                        \"total_loops\": total_loops,
                    }
                    if self._on_step:
                        self._on_step(step_info)

                    # ====== 3. 处理跳转/结束 ======
                    if target_action and target_action.startswith(\"跳转_\"):
                        try:
                            target = int(target_action.split(\"_\")[1])
                        except (IndexError, ValueError):
                            target = -1
                        if 0 <= target < len(flows):
                            total_jumps += 1
                            if total_jumps > max_jumps:
                                if self._on_log:
                                    self._on_log(f\"跳转次数超过上限({max_jumps})，停止\")
                                break
                            flow_index = target
                            continue
                        else:
                            flow_index += 1
                            continue
                    elif target_action == \"end\":
                        break

                    # ====== 4. 执行动作 ======
                    if target_action:
                        _action_ok = self._execute_action(target_action)
                        if not _action_ok:
                            self._consecutive_failures += 1
                            if self._consecutive_failures >= 3:
                                if self._on_log:
                                    self._on_log(f\"连续 {self._consecutive_failures} 次执行失败，停止组合技\")
                                break
                        else:
                            self._consecutive_failures = 0

                    if self.running:
                        self._wait_interruptible(0.3)
                    flow_index += 1

                self.reset()

            if self.running:
                if self._on_finished:
                    self._on_finished(True, f\"组合技 '{self.skill_data.get('name', '')}' 执行完成\")
            else:
                if self._on_finished:
                    self._on_finished(False, \"已停止\")

        except Exception as e:
            import traceback
            traceback.print_exc()
            if self._on_finished:
                self._on_finished(False, f\"执行失败: {str(e)}\")
        finally:
            self.running = False"""

if old in content:
    content = content.replace(old, new, 1)
    print("✅ run() 已完全重写：支持 image_found/image_not_found/wait_for_image + else分支")
else:
    print("❌ 未匹配 run() 方法")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎯 完成！重启后组合技即可正确执行条件判断和else分支")
