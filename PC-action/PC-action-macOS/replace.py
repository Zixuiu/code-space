import os

file_path = r"app.py"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修改1: _execute_action 返回 (success, img_fail_count)
old1 = '''    def _execute_action(self, action):
        import time as _time
        if not action or action == "end":
            return True
        try:
            _ea_start = _time.time()
            from utils import get_recordings_path, load_json_data
            folder_path = os.path.join(get_recordings_path(), action)
            json_path = os.path.join(folder_path, "recording.json")
            if not os.path.exists(json_path):
                if self._on_log:
                    self._on_log(f"[耗时] 找不到录制文件: {json_path} ({_time.time()-_ea_start:.3f}s)")
                return False

            _t_load0 = _time.time()
            recording_data = load_json_data(json_path)
            _t_load1 = _time.time()
            if self._on_log:
                self._on_log(f"[耗时] load_json_data: {_t_load1-_t_load0:.3f}s 步骤数={len(recording_data) if recording_data else 0}")
            if not recording_data:
                if self._on_log:
                    self._on_log(f"录制数据为空: {action}")
                return False

            has_images = any(op.get("image", "") for op in recording_data)
            if self._on_log:
                self._on_log(f"[耗时] 动作 '{action}' 含图片={has_images}, 步骤数={len(recording_data)}")

            from image_recognition import replay_coordinate_operations, replay_coordinates_only

            if has_images:
                _t_replay0 = _time.time()
                replay_result = replay_coordinate_operations(
                    recording_data, folder_path,
                    replay_interval=0.01, consider_color=False,
                    match_timeout=0.5,
                    stop_check=lambda: not self.running,
                    skip_cache_clear=True
                )
                # 兼容新旧返回值
                if len(replay_result) == 3:
                    ok, total, _ = replay_result
                else:
                    ok, total = replay_result
                _t_replay1 = _time.time()
                if self._on_log:
                    self._on_log(f"[耗时] replay_coordinate_operations: {_t_replay1-_t_replay0:.3f}s 成功={ok}/{total}")
            else:
                _t_replay0 = _time.time()
                ok, total = replay_coordinates_only(
                    recording_data, replay_interval=0.2,
                    stop_check=lambda: not self.running
                )
                _t_replay1 = _time.time()
                if self._on_log:
                    self._on_log(f"[耗时] replay_coordinates_only: {_t_replay1-_t_replay0:.3f}s 成功={ok}/{total}")

            # 如果全部步骤都失败，返回 False
            if ok == 0 and total > 0:
                if self._on_log:
                    self._on_log(f"执行失败: {action} 全部 {total} 个步骤均未成功")
                return False

            if self._on_log:
                self._on_log(f"[耗时] 执行动作 '{action}' 总耗时: {_time.time()-_ea_start:.3f}s")
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            if self._on_log:
                self._on_log(f"[耗时] 执行动作失败: {e}")
            return False'''

new1 = '''    def _execute_action(self, action):
        import time as _time
        if not action or action == "end":
            return True, 0
        try:
            _ea_start = _time.time()
            from utils import get_recordings_path, load_json_data
            folder_path = os.path.join(get_recordings_path(), action)
            json_path = os.path.join(folder_path, "recording.json")
            if not os.path.exists(json_path):
                if self._on_log:
                    self._on_log(f"[耗时] 找不到录制文件: {json_path} ({_time.time()-_ea_start:.3f}s)")
                return False, 0

            _t_load0 = _time.time()
            recording_data = load_json_data(json_path)
            _t_load1 = _time.time()
            if self._on_log:
                self._on_log(f"[耗时] load_json_data: {_t_load1-_t_load0:.3f}s 步骤数={len(recording_data) if recording_data else 0}")
            if not recording_data:
                if self._on_log:
                    self._on_log(f"录制数据为空: {action}")
                return False, 0

            has_images = any(op.get("image", "") for op in recording_data)
            if self._on_log:
                self._on_log(f"[耗时] 动作 '{action}' 含图片={has_images}, 步骤数={len(recording_data)}")

            from image_recognition import replay_coordinate_operations, replay_coordinates_only

            if has_images:
                _t_replay0 = _time.time()
                replay_result = replay_coordinate_operations(
                    recording_data, folder_path,
                    replay_interval=0.01, consider_color=False,
                    match_timeout=0.5,
                    stop_check=lambda: not self.running,
                    skip_cache_clear=True
                )
                # 兼容新旧返回值
                if len(replay_result) == 3:
                    ok, total, img_fail_count = replay_result
                else:
                    ok, total = replay_result
                    img_fail_count = 0
                _t_replay1 = _time.time()
                if self._on_log:
                    self._on_log(f"[耗时] replay_coordinate_operations: {_t_replay1-_t_replay0:.3f}s 成功={ok}/{total} 图片匹配失败={img_fail_count}")
            else:
                _t_replay0 = _time.time()
                ok, total = replay_coordinates_only(
                    recording_data, replay_interval=0.2,
                    stop_check=lambda: not self.running
                )
                img_fail_count = 0
                _t_replay1 = _time.time()
                if self._on_log:
                    self._on_log(f"[耗时] replay_coordinates_only: {_t_replay1-_t_replay0:.3f}s 成功={ok}/{total}")

            # 如果全部步骤都失败，返回 False
            if ok == 0 and total > 0:
                if self._on_log:
                    self._on_log(f"执行失败: {action} 全部 {total} 个步骤均未成功")
                return False, img_fail_count

            if self._on_log:
                self._on_log(f"[耗时] 执行动作 '{action}' 总耗时: {_time.time()-_ea_start:.3f}s")
            return True, img_fail_count
        except Exception as e:
            import traceback
            traceback.print_exc()
            if self._on_log:
                self._on_log(f"[耗时] 执行动作失败: {e}")
            return False, 0'''

if old1 in content:
    content = content.replace(old1, new1)
    print("✓ 修改1: _execute_action 返回 (success, img_fail_count)")
else:
    print("✗ 修改1: 未找到目标代码")

# 修改2: 组合技循环中根据条件类型判断是否停止
old2 = '''                    # ====== 4. 执行动作 ======
                    if target_action:
                        _exec_start = _time.time()
                        if self._on_log:
                            self._on_log(f"Flow {flow_index+1}: 开始执行动作 '{target_action}'")
                        _action_result = self._execute_action(target_action)
                        if isinstance(_action_result, tuple):
                            _action_ok, _img_fail_count = _action_result
                        else:
                            _action_ok, _img_fail_count = _action_result, 0
                        _exec_elapsed = _time.time() - _exec_start
                        if self._on_log:
                            self._on_log(f"[耗时] Flow{flow_index+1} 执行动作 '{target_action}': {_exec_elapsed:.3f}s 结果={'成功' if _action_ok else '失败'} 图片匹配失败={_img_fail_count}")
                        if not _action_ok:
                            self._consecutive_failures += 1
                            if self._consecutive_failures >= 3:
                                if self._on_log:
                                    self._on_log(f"连续 {self._consecutive_failures} 次执行失败，停止组合技")
                                break
                        else:
                            self._consecutive_failures = 0
                        # 图片匹配失败时，根据条件类型决定是否停止
                        # always / image_found: 图片匹配失败则停止组合技
                        # wait_for_image / image_not_found: 允许图片匹配失败，继续执行
                        if _img_fail_count > 0 and condition in ("always", "image_found"):
                            if self._on_log:
                                self._on_log(f"Flow {flow_index+1}: 条件为 '{condition}'，图片匹配失败 {_img_fail_count} 次，停止组合技")
                            break'''

new2 = '''                    # ====== 4. 执行动作 ======
                    if target_action:
                        _exec_start = _time.time()
                        if self._on_log:
                            self._on_log(f"Flow {flow_index+1}: 开始执行动作 '{target_action}'")
                        _action_result = self._execute_action(target_action)
                        if isinstance(_action_result, tuple):
                            _action_ok, _img_fail_count = _action_result
                        else:
                            _action_ok, _img_fail_count = _action_result, 0
                        _exec_elapsed = _time.time() - _exec_start
                        if self._on_log:
                            self._on_log(f"[耗时] Flow{flow_index+1} 执行动作 '{target_action}': {_exec_elapsed:.3f}s 结果={'成功' if _action_ok else '失败'} 图片匹配失败={_img_fail_count}")
                        if not _action_ok:
                            self._consecutive_failures += 1
                            if self._consecutive_failures >= 3:
                                if self._on_log:
                                    self._on_log(f"连续 {self._consecutive_failures} 次执行失败，停止组合技")
                                break
                        else:
                            self._consecutive_failures = 0
                        # 图片匹配失败时，根据条件类型决定是否停止
                        if _img_fail_count > 0 and condition in ("always", "image_found"):
                            if self._on_log:
                                self._on_log(f"Flow {flow_index+1}: 条件为 '{condition}'，图片匹配失败 {_img_fail_count} 次，停止组合技")
                            break'''

if old2 in content:
    content = content.replace(old2, new2)
    print("✓ 修改2: 组合技循环中根据条件类型判断是否停止")
else:
    print("✗ 修改2: 未找到目标代码")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✓ 已保存到 {file_path}")
