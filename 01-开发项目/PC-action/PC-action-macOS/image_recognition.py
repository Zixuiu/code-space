import os
import json
import time
import re
import pyautogui
import keyboard
from PIL import Image
import sys
import cv2
import numpy as np

# ⚡ 启用 OpenCL GPU 加速 matchTemplate
cv2.ocl.setUseOpenCL(True)
import mss

# 尝试导入CUDA加速的OpenCV
try:
    # 检查OpenCV是否支持CUDA
    _cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
    if _cuda_available:
        print(f"[性能] CUDA加速已启用，检测到 {cv2.cuda.getCudaEnabledDeviceCount()} 个GPU设备")
    else:
        _cuda_available = False
except Exception:
    _cuda_available = False

# 全局停止标志，用于中断回放
_replay_stop_flag = False
# 全局调试模式标志
_debug_mode = False
# 全局日志回调函数
_log_callback = None

def set_debug_mode(enabled):
    """设置调试模式"""
    global _debug_mode
    _debug_mode = enabled

def set_log_callback(callback):
    """设置日志回调函数，用于将日志发送到UI"""
    global _log_callback
    _log_callback = callback

def debug_print(message):
    """调试输出，仅在调试模式下打印，同时发送到日志回调"""
    global _debug_mode, _log_callback
    if _debug_mode:
        print(message)
        # 如果有日志回调，发送日志
        if _log_callback is not None:
            try:
                _log_callback(message)
            except Exception:
                pass

def set_replay_stop_flag(stop=True):
    """设置回放停止标志"""
    global _replay_stop_flag
    _replay_stop_flag = stop
    if stop:
        # 打印停止信号
        debug_print("回放已停止")

def is_replay_stopped():
    """检查是否已设置停止标志"""
    global _replay_stop_flag
    return _replay_stop_flag

def clear_replay_stop_flag():
    """清除回放停止标志"""
    global _replay_stop_flag
    _replay_stop_flag = False

def _interruptible_sleep(duration, stop_check=None):
    """可中断的 sleep：等待 duration 秒，若收到停止信号立即返回
    
    Returns: True=被中断(停止), False=正常等待完成
    """
    if duration <= 0:
        return (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag)
    start = time.time()
    poll_interval = 0.02  # 20ms轮询一次停止信号
    while time.time() - start < duration:
        if (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag):
            return True
        time.sleep(poll_interval)
    return (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag)

def replay_coordinate_operations(recording_data, folder_path, replay_interval=0.5, consider_color=False, region_center=None, match_timeout=0.3, stop_check=None, skip_cache_clear=False):
    """
    根据录制数据回放操作（完全基于图像匹配）
    
    Args:
        recording_data: 录制数据列表，包含步骤、时间戳、操作类型、图像路径和坐标
        folder_path: 录制文件夹路径
        replay_interval: 操作之间的间隔时间（秒）
        consider_color: 是否考虑颜色匹配 (True=同时考虑形状和颜色, False=只考虑形状)
        match_timeout: 图像匹配超时时间（秒），默认1.5秒
        stop_check: 可选的停止检查函数，返回True时停止执行（用于多组合技并行时各runner独立停止）
    
    Returns:
        tuple: (成功执行的操作数, 总操作数, 图片匹配失败次数)
    """
    global _replay_stop_flag
    
    success_count = 0
    image_match_fail_count = 0  # 追踪图片匹配失败次数
    recording_data = sorted(recording_data, key=lambda op: op.get('step', 0))
    total_operations = len(recording_data)
    
    # 禁用pyautogui的安全检查 + 去掉默认 100ms 暂停(极速模式)
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    # 缓存Win32 API函数引用（极速点击，比pyautogui快5-10倍）
    import ctypes
    _user32 = ctypes.windll.user32
    _MOUSEEVENTF_LEFTDOWN = 0x0002
    _MOUSEEVENTF_LEFTUP = 0x0004
    _MOUSEEVENTF_RIGHTDOWN = 0x0008
    _MOUSEEVENTF_RIGHTUP = 0x0010
    _MOUSEEVENTF_MIDDLEDOWN = 0x0020
    _MOUSEEVENTF_MIDDLEUP = 0x0040
    _MOUSEEVENTF_WHEEL = 0x0800

    def _fc(btn):
        if btn == 'left':
            _user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            _user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif btn == 'right':
            _user32.mouse_event(_MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            _user32.mouse_event(_MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        elif btn == 'middle':
            _user32.mouse_event(_MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
            _user32.mouse_event(_MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
        else:
            _user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            _user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def _fast_move(x, y):
        _user32.SetCursorPos(x, y)
    
    # 仅非组合技调用（无stop_check）时清除停止标志
    # 组合技调用时不清除，避免一个runner重置了全局标志导致其他runner无法被正确停止
    if stop_check is None:
        _replay_stop_flag = False
    
    _replay_start = time.time()
    for i, operation in enumerate(recording_data):
        _step_start = time.time()
        if (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag):
            break
        try:
            # 获取操作信息
            step = operation.get('step', i + 1)
            action_type = operation.get('action_type', 'left_click')
            image_name = operation.get('image', '')
            delay = operation.get('delay', 0)
            
            # 处理不需要图像的操作类型
            if action_type in ['text_input', 'keyboard', 'keyboard_direct', 'scroll']:
                # 文本输入、键盘操作和滚动操作不需要图像匹配

                if action_type == 'text_input':
                    text = operation.get('text', '')
                    if text:
                        preview = text[:20] + ('...' if len(text) > 20 else '')
                        debug_print(f"[回放] 步骤 {step}: 文本输入 '{preview}' (共 {len(text)} 字符)")
                        # 使用剪贴板方式支持中文输入
                        import pyperclip
                        pyperclip.copy(text)
                        if _interruptible_sleep(0.15, stop_check=stop_check):
                            break
                        pyautogui.hotkey('ctrl', 'v')
                        success_count += 1
                        debug_print(f"[回放] 步骤 {step}: 文本输入完成")
                    else:
                        debug_print(f"[回放] 步骤 {step}: 文本输入 - 内容为空，跳过")
                        continue

                elif action_type == 'scroll':
                    scroll_amount = operation.get('scroll_amount', 3)
                    debug_print(f"[回放] 步骤 {step}: 滚动 {scroll_amount} 像素")
                    # 执行滚动操作
                    pyautogui.scroll(scroll_amount)
                    success_count += 1
                    debug_print(f"[回放] 步骤 {step}: 滚动完成")
                    continue

                elif action_type in ['keyboard', 'keyboard_direct']:
                    key = operation.get('key', 'enter')
                    debug_print(f"[回放] 步骤 {step}: 按键 '{key}' (action_type={action_type})")

                    # 解析组合键
                    if '+' in key:
                        # 分割组合键
                        key_parts = key.lower().split('+')
                        
                        # 确定修饰键和主键
                        modifiers = []
                        main_key = None
                        
                        for part in key_parts:
                            part = part.strip()
                            if part in ['ctrl', 'control']:
                                modifiers.append('ctrl')
                            elif part == 'shift':
                                modifiers.append('shift')
                            elif part == 'alt':
                                modifiers.append('alt')
                            elif part in ['win', 'windows', 'cmd', 'command']:
                                modifiers.append('win')
                            elif not main_key:
                                main_key = part
                        
                        if not main_key:
                            debug_print(f"[回放] 步骤 {step}: 组合键 '{key}' 解析失败（无主键），跳过")
                            continue

                        # 执行组合键
                        try:
                            # 使用pyautogui的hotkey方法处理组合键
                            pyautogui.hotkey(*modifiers, main_key)
                            success_count += 1
                            debug_print(f"[回放] 步骤 {step}: 组合键 '{key}' 完成")
                            continue  # 组合键执行完毕，跳过后续图片匹配
                        except Exception as e:
                            # 尝试手动按下和释放
                            try:
                                # 按下修饰键
                                for mod in modifiers:
                                    pyautogui.keyDown(mod)

                                # 按下和释放主键
                                pyautogui.press(main_key)

                                # 释放修饰键
                                for mod in reversed(modifiers):
                                    pyautogui.keyUp(mod)

                                success_count += 1
                                debug_print(f"[回放] 步骤 {step}: 组合键 '{key}' 完成（手动回退）")
                                continue  # 组合键执行完毕，跳过后续图片匹配
                            except Exception as e2:
                                debug_print(f"[回放] 步骤 {step}: 组合键 '{key}' 失败: {e2}")
                                continue
                    else:
                        # 处理单个按键
                        try:
                            # 特殊键映射
                            special_keys = {
                                'space': 'space',
                                'enter': 'enter',
                                'return': 'enter',
                                'tab': 'tab',
                                'esc': 'esc',
                                'escape': 'esc',
                                'backspace': 'backspace',
                                'delete': 'delete',
                                'del': 'delete',
                                'home': 'home',
                                'end': 'end',
                                'pageup': 'pageup',
                                'pagedown': 'pagedown',
                                'up': 'up',
                                'down': 'down',
                                'left': 'left',
                                'right': 'right',
                                'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4', 'f5': 'f5',
                                'f6': 'f6', 'f7': 'f7', 'f8': 'f8', 'f9': 'f9', 'f10': 'f10',
                                'f11': 'f11', 'f12': 'f12', 'f13': 'f13', 'f14': 'f14', 'f15': 'f15',
                                'capslock': 'capslock', 'numlock': 'numlock', 'scrolllock': 'scrolllock',
                                'pause': 'pause', 'break': 'break', 'insert': 'insert',
                                'printscreen': 'printscreen', 'sysrq': 'printscreen',
                                'win': 'winleft', 'cmd': 'winleft', 'command': 'winleft',
                                'menu': 'menu', 'apps': 'menu'
                            }
                            
                            # 转换为小写并检查是否为特殊键
                            key_lower = key.lower()
                            debug_print(f"[回放] 步骤 {step}: 准备调用 pyautogui.press('{key_lower}')")
                            if key_lower in special_keys:
                                pyautogui.press(special_keys[key_lower])
                                debug_print(f"[回放] 步骤 {step}: pyautogui.press('{special_keys[key_lower]}') 调用完成")
                            else:
                                # 普通字符键
                                pyautogui.press(key)
                                debug_print(f"[回放] 步骤 {step}: pyautogui.press('{key}') 调用完成")
                            success_count += 1
                            debug_print(f"[回放] 步骤 {step}: 按键 '{key}' 完成")
                            continue  # 按键执行完毕，跳过后续图片匹配
                        except Exception as e:
                            debug_print(f"[回放] 步骤 {step}: 按键 '{key}' 失败: {e}")
                            continue

                # 操作间隔 - 使用每个操作设置的延迟时间
                if i < total_operations - 1:  # 不是最后一个操作
                    # 如果设置了延迟时间，使用设置的延迟；否则使用默认间隔
                    if delay > 0:
                        if _interruptible_sleep(delay, stop_check=stop_check):
                            break
                    elif not image_name:  # 没有图像识别且没有设置延迟，使用默认间隔
                        if _interruptible_sleep(replay_interval, stop_check=stop_check):
                            break
                else:
                    # 最后一个操作，如果有延迟则等待
                    if delay > 0:
                        if _interruptible_sleep(delay, stop_check=stop_check):
                            break
                # 如果不是图片操作，跳过直接继续下一轮循环
                if not image_name:
                    continue
            
            # 对于需要图像的操作，检查图像文件
            if image_name:
                # 构建图像完整路径
                image_path = os.path.join(folder_path, image_name)
                
                # 检查图像文件是否存在
                if not os.path.exists(image_path):
                    # 尝试用操作编号查找对应的图片文件
                    # 查找操作编号对应的图片文件
                    for f in os.listdir(folder_path):
                        if f.lower().endswith('.png'):
                            match = re.search(r'操作(\d+)\.png', f)
                            if match and int(match.group(1)) == step:
                                image_path = os.path.join(folder_path, f)
                                break
                    
                    # 如果还是找不到，跳过此步骤
                    if not os.path.exists(image_path):
                        continue
                
                # 使用图像匹配查找位置
                debug_print(f"[回放] 步骤 {step}: 开始匹配图片 {image_name}")
                # 直接使用缓存的图像数组获取尺寸，避免重复打开文件
                dynamic_confidence = 0.8
                use_color = consider_color
                try:
                    from image_recognition import get_cached_image
                    cached_img = get_cached_image(image_path)
                    if cached_img is not None:
                        img_height, img_width = cached_img.shape[:2]
                        if img_width < 50 or img_height < 50:
                            use_color = consider_color
                            debug_print(f"[回放] 步骤 {step}: 小图标检测，尺寸 {img_width}x{img_height}，置信度 {dynamic_confidence}，颜色匹配={'开启' if use_color else '关闭'}")
                except Exception:
                    pass
                # 根据 match_timeout 自适应分配匹配时间
                # 首次匹配给一半时间，快的 UI 0.01s 就返回，慢的 UI 后续轮询继续等
                single_attempt_timeout = match_timeout * 0.5
                _match_t0 = time.time()
                _roi_hint = None
                if 'x' in operation and 'y' in operation:
                    _roi_hint = (operation['x'], operation['y'])
                if single_attempt_timeout <= 0.03:
                    location = find_image_with_timeout(image_path, confidence=dynamic_confidence, timeout=0.001, consider_color=use_color, region_center=region_center, stop_check=stop_check, roi_hint=_roi_hint)
                else:
                    location = find_image_with_timeout(image_path, confidence=dynamic_confidence, timeout=single_attempt_timeout, consider_color=use_color, region_center=region_center, stop_check=stop_check, roi_hint=_roi_hint)
                _match_t1 = time.time()

                if not location:
                    debug_print(f"[回放] ❌ 步骤 {step}: 图片匹配失败，立即停止回放（图片: {image_name}）")
                    image_match_fail_count += 1
                    break
                else:
                    debug_print(f"[回放] ✅ 步骤 {step}: 图片匹配成功（位置: {location}）")
                    x, y, width, height = location
                    center_x = x + width // 2
                    center_y = y + height // 2
                    
            else:
                # 如果没有图像文件，跳过此步骤（不再使用坐标作为备用方案）
                continue
            
            # 极速模式：Win32 API 直接移动并点击（比pyautogui快5-10倍）
            _fast_move(center_x, center_y)

            # 根据操作类型执行相应操作
            if action_type == 'left_click':
                _fc('left')
            elif action_type == 'right_click':
                _fc('right')
            elif action_type == 'double_click':
                _fc('left'); _fc('left')
            elif action_type == 'drag':
                _user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                _user32.mouse_event(0x0001, 50, 0, 0, 0)  # MOUSEEVENTF_MOVE
                _user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            else:
                _fc('left')
            
            success_count += 1

            # 如果设置了延迟时间，等待指定时间后再执行下一步（让界面有时间更新）
            if delay > 0:
                if _interruptible_sleep(delay, stop_check=stop_check):
                    break

            # 极小延迟（1ms+stop_check），几乎不等待
            if _interruptible_sleep(0.001, stop_check=stop_check):
                break
        except Exception:
            import traceback; traceback.print_exc()
            continue
    
    _replay_elapsed = time.time() - _replay_start
    if not skip_cache_clear:
        clear_image_cache()
    return success_count, total_operations, image_match_fail_count


def replay_coordinates_only(recording_data, replay_interval=0, stop_check=None):
    """
    根据坐标数据回放操作（仅坐标，无需图像）
    
    Args:
        recording_data: 录制数据列表，包含步骤、操作类型、坐标
        replay_interval: 操作之间的间隔时间（秒）
        stop_check: 可选的停止检查函数，返回True时停止执行（用于多组合技并行时各runner独立停止）
    
    Returns:
        tuple: (成功执行的操作数, 总操作数)
    """
    global _replay_stop_flag
    
    success_count = 0
    recording_data = sorted(recording_data, key=lambda op: op.get('step', 0))
    total_operations = len(recording_data)
    
    # 禁用pyautogui的安全检查 + 去掉默认 100ms 暂停(极速模式)
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    # 缓存Win32 API函数引用（极速点击，比pyautogui快5-10倍）
    import ctypes
    _user32 = ctypes.windll.user32
    _MOUSEEVENTF_LEFTDOWN = 0x0002
    _MOUSEEVENTF_LEFTUP = 0x0004
    _MOUSEEVENTF_RIGHTDOWN = 0x0008
    _MOUSEEVENTF_RIGHTUP = 0x0010
    _MOUSEEVENTF_MIDDLEDOWN = 0x0020
    _MOUSEEVENTF_MIDDLEUP = 0x0040
    _MOUSEEVENTF_WHEEL = 0x0800

    def _fc(btn):
        if btn == 'left':
            _user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            _user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif btn == 'right':
            _user32.mouse_event(_MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            _user32.mouse_event(_MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        elif btn == 'middle':
            _user32.mouse_event(_MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
            _user32.mouse_event(_MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
        else:
            _user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            _user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    if stop_check is None:
        _replay_stop_flag = False
    
    for i, operation in enumerate(recording_data):
        # 检查是否收到停止信号（有stop_check时只用自己的，不影响其他组合技）
        if (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag):
            break
        try:
            # 获取操作信息
            action_type = operation.get('action_type', 'left_click')
            x = operation.get('x', 0)
            y = operation.get('y', 0)

            if action_type == 'scroll':
                _user32.mouse_event(_MOUSEEVENTF_WHEEL, 0, 0, operation.get('scroll_amount', 3), 0)
                success_count += 1
                continue

            # 极速移动+点击
            _user32.SetCursorPos(x, y)
            if action_type in ('left_click', 'click'):
                _fc('l')
            elif action_type == 'right_click':
                _fc('r')
            elif action_type == 'double_click':
                _fc('l'); _fc('l')
            elif action_type == 'middle_click':
                _fc('m')
            else:
                _fc('l')
            success_count += 1

            # 只有明确指定 delay>0 才等，否则不等
            if i < total_operations - 1:
                delay = operation.get('delay', 0)
                if delay > 0:
                    time.sleep(delay)
                elif replay_interval > 0:
                    time.sleep(replay_interval)
                    
        except Exception:
            import traceback; traceback.print_exc()
            continue
    
    return success_count, total_operations


def _match_template_cuda(screenshot_bgr, image_array):
    """使用CUDA加速模板匹配（如果可用）"""
    global _cuda_available
    if not _cuda_available:
        return None
    try:
        # 上传数据到GPU
        screenshot_gpu = cv2.cuda_GpuMat()
        image_gpu = cv2.cuda_GpuMat()
        screenshot_gpu.upload(screenshot_bgr)
        image_gpu.upload(image_array)
        
        # 执行CUDA模板匹配
        matcher = cv2.cuda.createTemplateMatching(cv2.CV_8UC3, cv2.TM_CCOEFF_NORMED)
        result_gpu = matcher.match(screenshot_gpu, image_gpu)
        result = result_gpu.download()
        return result
    except Exception:
        return None

_shared_screenshot = None
_shared_screenshot_time = 0
_shared_gray_screenshot = None      # 缓存的灰度截图（绿色通道）
_shared_small_gray_screenshot = None  # 缓存的 0.5x 缩小灰度截图
_SHARED_SCREENSHOT_INTERVAL = 0.003  # 共享截图刷新间隔3ms

def _get_shared_screenshot():
    """获取共享截图（线程安全），3ms内复用同一张截图，同时缓存灰度和缩小版本"""
    global _shared_screenshot, _shared_screenshot_time, _shared_gray_screenshot, _shared_small_gray_screenshot
    now = time.time()
    with _shared_screenshot_lock:
        if _shared_screenshot is None or (now - _shared_screenshot_time) > _SHARED_SCREENSHOT_INTERVAL:
            _shared_screenshot = _mss_grab_array()
            if _shared_screenshot is not None:
                # 用 cvtColor 保证匹配精度（绿色通道会导致误匹配）
                _shared_gray_screenshot = cv2.cvtColor(_shared_screenshot, cv2.COLOR_BGR2GRAY)
                # ⚡ 同时缓存缩小版（避免轮询时重复 resize）
                _shared_small_gray_screenshot = cv2.resize(_shared_gray_screenshot, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            _shared_screenshot_time = now
        return _shared_screenshot

def _get_shared_gray():
    """获取缓存的灰度截图（绿色通道）"""
    _get_shared_screenshot()
    return _shared_gray_screenshot

def _get_shared_small_gray():
    """获取缓存的 0.5x 缩小灰度截图"""
    _get_shared_screenshot()
    return _shared_small_gray_screenshot


def _find_image_flash(image_path, confidence=0.8, consider_color=True, stop_check=None):
    try:
        arr = get_cached_image(image_path)
        if arr is None:
            return None
        if (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag):
            return None
        screenshot = _mss_grab_array()
        if screenshot is None:
            return None
        if consider_color:
            result = cv2.matchTemplate(screenshot, arr, cv2.TM_CCOEFF_NORMED)
        else:
            gray_s = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            gray_t = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(gray_s, gray_t, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= confidence:
            h, w = arr.shape[:2]
            return (max_loc[0], max_loc[1], w, h)
    except:
        pass
    return None

def _find_image_flash(image_path, confidence=0.8, consider_color=True, stop_check=None):
    try:
        arr = get_cached_image(image_path)
        if arr is None:
            return None
        if (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag):
            return None
        screenshot = _mss_grab_array()
        if screenshot is None:
            return None
        if consider_color:
            result = cv2.matchTemplate(screenshot, arr, cv2.TM_CCOEFF_NORMED)
        else:
            gray_s = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            gray_t = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(gray_s, gray_t, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= confidence:
            h, w = arr.shape[:2]
            return (max_loc[0], max_loc[1], w, h)
    except:
        pass
    return None

def find_image_with_timeout(image_path, confidence=0.8, timeout=0.5, consider_color=True, region_center=None, stop_check=None, roi_hint=None, strict=False):
    """
    在屏幕上查找指定图像，支持超时等待，支持可中断停止
    
    Args:
        image_path: 图像文件路径
        confidence: 匹配置信度 (0-1)
        timeout: 最长等待时间（秒），默认0.5秒
        consider_color: 是否考虑颜色匹配
        region_center: 框选区域的中心坐标
        stop_check: 可选的停止检查函数，返回True时立即返回None
    
    Returns:
        tuple: (x, y, width, height) 或 None
    """
    import numpy as np
    import cv2
    
    def _basename(p):
        return p.replace('\\', '/').split('/')[-1] if p else ''
    
    if timeout <= 0.01:
        return _find_image_flash(image_path, confidence, consider_color, stop_check)

    _func_start = time.time()
    start_time = time.time()
    
    image_array = get_cached_image(image_path)
    if image_array is None:
        debug_print(f"[匹配诊断] ⚠️ get_cached_image 返回 None: {image_path}")
        return None
    debug_print(f"[匹配诊断] 图片加载成功 {image_array.shape} | 阈值 {confidence:.2f} | 超时 {timeout:.2f}s")

    # 必须先获取截图，后面诊断信息要用到 first_screenshot
    first_screenshot = _get_shared_screenshot()
    screenshot_h = first_screenshot.shape[0] if first_screenshot is not None else 0
    screenshot_w = first_screenshot.shape[1] if first_screenshot is not None else 0

    # 多尺度间隔：减少多尺度运行频率（每次多尺度太耗时）
    # 策略：只有 1:1 分数接近阈值时才跑多尺度，且间隔为 3 次
    multi_scale_interval = 3
    multi_scale_threshold_ratio = 0.75  # 1:1 分数达到阈值的 75% 以上才跑多尺度
    iteration = 0

    # 截图和模板尺寸（用于诊断 "明明有图却匹配不到" 问题）
    template_h, template_w = image_array.shape[:2]
    debug_print(f"[匹配诊断] 模板 {template_w}x{template_h} | 截图 {screenshot_w}x{screenshot_h} | 阈值 {confidence:.2f} | 颜色 {'开启' if consider_color else '关闭'}")

    # 记录所有尺度的最佳分数（用于失败时诊断）
    scale_best_scores = {}  # {scale: (max_val, max_loc)}

    # ⚡ 预计算灰度模板（cvtColor 保证精度）
    _gray_template = None
    _gray_first_screenshot = None
    _small_gray_template = None  # 0.5x 缩小模板
    _small_gray_screenshot = None  # 0.5x 缩小截图
    if not consider_color:
        _gray_template = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        if first_screenshot is not None:
            _gray_first_screenshot = cv2.cvtColor(first_screenshot, cv2.COLOR_BGR2GRAY)
            # ⚡ 预计算 0.5x 缩小版
            if template_w >= 20 and template_h >= 20:
                _small_gray_template = cv2.resize(_gray_template, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
                _small_gray_screenshot = cv2.resize(_gray_first_screenshot, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)

    def _fast_match(screen_bgr, template_bgr, gray_screen=None):
        """快速匹配：灰度比BGR快3倍。可传入预计算的gray_screen避免重复cvtColor"""
        if _gray_template is not None:
            if gray_screen is not None:
                gs = gray_screen
            elif screen_bgr is first_screenshot and _gray_first_screenshot is not None:
                gs = _gray_first_screenshot
            else:
                gs = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            return cv2.matchTemplate(gs, _gray_template, cv2.TM_CCOEFF_NORMED)
        else:
            return cv2.matchTemplate(screen_bgr, template_bgr, cv2.TM_CCOEFF_NORMED)

    def _fast_match_small():
        """⚡ 0.5x 缩小匹配，比全屏快4倍。返回 (x, y, w, h) 或 None"""
        if _small_gray_template is None or _small_gray_screenshot is None:
            return None
        result = cv2.matchTemplate(_small_gray_screenshot, _small_gray_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= confidence:
            h, w = image_array.shape[:2]
            return (max_loc[0] * 2, max_loc[1] * 2, w, h)
        if not scale_best_scores or scale_best_scores.get(1.0, (0,))[0] < max_val:
            scale_best_scores[1.0] = (max_val, (max_loc[0] * 2, max_loc[1] * 2))
        return None

    def _try_match(screenshot, skip_multi_scale=False):
        nonlocal iteration
        iteration += 1
        _tm0 = time.time()
        result = _fast_match(screenshot, image_array)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        scale_best_scores[1.0] = (max_val, max_loc)
        if iteration == 1 or iteration % 20 == 0:
            debug_print(f"[回放匹配] 迭代{iteration}: 最高置信度={max_val:.3f} (阈值={confidence:.2f}) 位置={max_loc}")
        if max_val >= confidence:
            h, w = image_array.shape[:2]
            return (max_loc[0], max_loc[1], w, h)
        # 智能多尺度：只有 1:1 分数接近阈值时才跑多尺度，节省时间
        if not skip_multi_scale and (iteration % multi_scale_interval == 0) and (max_val >= confidence * multi_scale_threshold_ratio):
            _ms0 = time.time()
            loc, all_scores = fast_multi_scale_match(screenshot, image_array, confidence, consider_color, image_path, return_scores=True)
            for sc, (mv, ml) in all_scores.items():
                if sc not in scale_best_scores or scale_best_scores[sc][0] < mv:
                    scale_best_scores[sc] = (mv, ml)
            if loc:
                return loc
        return None

    if first_screenshot is not None:
        try:
            if (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag):
                return None
            _first0 = time.time()

            # ⚡ 最快路径：0.5x 缩小匹配（1280x800，比全屏快4倍，约0.04s）
            _small_result = _fast_match_small()
            if _small_result is not None:
                debug_print(f"[匹配诊断] ⚡ 0.5x缩小命中(score={scale_best_scores.get(1.0, (0,))[0]:.3f})")
                iteration = 1
                return _small_result

            # ⚡ 次快路径：如果有 roi_hint，从全屏截图切片 ROI + 灰度匹配
            if roi_hint is not None:
                try:
                    rx, ry = int(roi_hint[0]), int(roi_hint[1])
                    img_h, img_w = image_array.shape[:2]
                    pad = 300
                    x1 = max(0, rx - pad)
                    y1 = max(0, ry - pad)
                    x2 = min(first_screenshot.shape[1], rx + img_w + pad)
                    y2 = min(first_screenshot.shape[0], ry + img_h + pad)
                    roi = first_screenshot[y1:y2, x1:x2].copy()
                    if roi.shape[0] >= img_h and roi.shape[1] >= img_w:
                        result = _fast_match(roi, image_array)
                        _, roi_max_val, _, roi_max_loc = cv2.minMaxLoc(result)
                        scale_best_scores[1.0] = (roi_max_val, roi_max_loc)
                        iteration = 1
                        if roi_max_val >= confidence:
                            h, w = image_array.shape[:2]
                            debug_print(f"[匹配诊断] ⚡ ROI灰度命中(score={roi_max_val:.3f}) 区域({x1},{y1},{x2},{y2})")
                            return (roi_max_loc[0] + x1, roi_max_loc[1] + y1, w, h)
                        debug_print(f"[匹配诊断] ROI未命中(score={roi_max_val:.3f}), 尝试全屏灰度1:1")
                except Exception as _roi_e:
                    debug_print(f"[匹配诊断] ROI切片异常: {_roi_e}, 尝试全屏1:1")

            # ⚡ 次快路径：全屏灰度 1:1 匹配（灰度比BGR快3倍）
            _fast_result = _fast_match(first_screenshot, image_array)
            _, _fast_max_val, _, _fast_max_loc = cv2.minMaxLoc(_fast_result)
            if not scale_best_scores or scale_best_scores.get(1.0, (0,))[0] < _fast_max_val:
                scale_best_scores[1.0] = (_fast_max_val, _fast_max_loc)
            if iteration == 0:
                iteration = 1
            if _fast_max_val >= confidence:
                h, w = image_array.shape[:2]
                debug_print(f"[匹配诊断] ⚡ 全屏1:1快速命中(score={_fast_max_val:.3f}) 位置={_fast_max_loc}")
                return (_fast_max_loc[0], _fast_max_loc[1], w, h)
            debug_print(f"[匹配诊断] 全屏1:1未命中(score={_fast_max_val:.3f}<{confidence:.2f})")

            # ⚡ 如果分数很低（< 阈值60%），图片大概率不在屏幕上，跳过粗匹配/多尺度，直接轮询
            _skip_complex = _fast_max_val < confidence * 0.6
            if _skip_complex:
                debug_print(f"[匹配诊断] ⏭ 分数过低({_fast_max_val:.3f}<{confidence*0.6:.2f})，跳过复杂匹配直接轮询")

            # 1:1 没命中，才走粗匹配、多尺度等复杂逻辑
            _coarse_scale = 0.5
            _coarse_thresh = confidence * 0.80
            if not _skip_complex and screenshot_w > 1200 and screenshot_h > 800:
                try:
                    _cs0 = time.time()
                    _small_screen = cv2.resize(first_screenshot, None, fx=_coarse_scale, fy=_coarse_scale, interpolation=cv2.INTER_AREA)
                    _small_template = cv2.resize(image_array, None, fx=_coarse_scale, fy=_coarse_scale, interpolation=cv2.INTER_AREA)
                    _small_h, _small_w = _small_template.shape[:2]
                    if _small_screen.shape[0] >= _small_h and _small_screen.shape[1] >= _small_w:
                        _cr = cv2.matchTemplate(_small_screen, _small_template, cv2.TM_CCOEFF_NORMED)
                        _, _cv, _, _cl = cv2.minMaxLoc(_cr)
                        if _cv >= _coarse_thresh:
                            _fx = int(_cl[0] / _coarse_scale) - 100
                            _fy = int(_cl[1] / _coarse_scale) - 100
                            _fw = int(_small_w / _coarse_scale) + 200
                            _fh = int(_small_h / _coarse_scale) + 200
                            _fx = max(0, _fx)
                            _fy = max(0, _fy)
                            _fx2 = min(screenshot_w, _fx + _fw)
                            _fy2 = min(screenshot_h, _fy + _fh)
                            _roi_full = first_screenshot[_fy:_fy2, _fx:_fx2]
                            if _roi_full.shape[0] >= template_h and _roi_full.shape[1] >= template_w:
                                _rr = cv2.matchTemplate(_roi_full, image_array, cv2.TM_CCOEFF_NORMED)
                                _, _rv, _, _rl = cv2.minMaxLoc(_rr)
                                if _rv >= confidence:
                                    h, w = image_array.shape[:2]
                                    return (_rl[0] + _fx, _rl[1] + _fy, w, h)
                                debug_print(f"[匹配诊断] 精匹配未命中(score={_rv:.3f}<{confidence:.2f}), 尝试区域多尺度")
                                try:
                                    for _ms_scale in _SCALES:
                                        if _ms_scale == 1.0:
                                            continue
                                        _new_w = int(template_w * _ms_scale)
                                        _new_h = int(template_h * _ms_scale)
                                        if _new_w < 10 or _new_h < 10:
                                            continue
                                        _resized = cv2.resize(image_array, (_new_w, _new_h), interpolation=cv2.INTER_LINEAR)
                                        if _roi_full.shape[0] >= _new_h and _roi_full.shape[1] >= _new_w:
                                            _msr = cv2.matchTemplate(_roi_full, _resized, cv2.TM_CCOEFF_NORMED)
                                            _, _msv, _, _msl = cv2.minMaxLoc(_msr)
                                            if _msv >= confidence:
                                                h, w = _resized.shape[:2]
                                                debug_print(f"[匹配诊断] ⚡ 精匹配区域多尺度命中(scale={_ms_scale}, score={_msv:.3f})")
                                                return (_msl[0] + _fx, _msl[1] + _fy, w, h)
                                    debug_print(f"[匹配诊断] 精匹配区域多尺度未命中, 回退全屏")
                                except Exception as _cme2:
                                    debug_print(f"[匹配诊断] 精匹配区域多尺度异常: {_cme2}, 回退全屏")
                            else:
                                debug_print(f"[匹配诊断] 精匹配ROI太小, 回退全屏")
                        else:
                            debug_print(f"[匹配诊断] 粗匹配未命中(score={_cv:.3f}<{_coarse_thresh:.2f}), 回退全屏")
                            if _cv >= 0.6:
                                try:
                                    _fx = int(_cl[0] / _coarse_scale) - 150
                                    _fy = int(_cl[1] / _coarse_scale) - 150
                                    _fw = int(_small_w / _coarse_scale) + 300
                                    _fh = int(_small_h / _coarse_scale) + 300
                                    _fx = max(0, _fx)
                                    _fy = max(0, _fy)
                                    _fx2 = min(screenshot_w, _fx + _fw)
                                    _fy2 = min(screenshot_h, _fy + _fh)
                                    _roi_coarse = first_screenshot[_fy:_fy2, _fx:_fx2]
                                    for _ms_scale in _SCALES:
                                        if _ms_scale == 1.0:
                                            continue
                                        _new_w = int(template_w * _ms_scale)
                                        _new_h = int(template_h * _ms_scale)
                                        if _new_w < 10 or _new_h < 10:
                                            continue
                                        _resized = cv2.resize(image_array, (_new_w, _new_h), interpolation=cv2.INTER_LINEAR)
                                        if _roi_coarse.shape[0] >= _new_h and _roi_coarse.shape[1] >= _new_w:
                                            _msr = cv2.matchTemplate(_roi_coarse, _resized, cv2.TM_CCOEFF_NORMED)
                                            _, _msv, _, _msl = cv2.minMaxLoc(_msr)
                                            if _msv >= confidence:
                                                h, w = _resized.shape[:2]
                                                debug_print(f"[匹配诊断] ⚡ 粗匹配区域多尺度命中(scale={_ms_scale}, score={_msv:.3f})")
                                                return (_msl[0] + _fx, _msl[1] + _fy, w, h)
                                    debug_print(f"[匹配诊断] 粗匹配区域多尺度未命中, 回退全屏")
                                except Exception as _cme:
                                    debug_print(f"[匹配诊断] 粗匹配区域多尺度异常: {_cme}, 回退全屏")
                            else:
                                debug_print(f"[匹配诊断] 粗匹配仅 {_cv:.3f} < 0.6，跳过区域多尺度，走全屏匹配")
                except Exception as _ce:
                    debug_print(f"[匹配诊断] 粗匹配异常: {_ce}, 回退全屏")

            # 1:1 已经在上面做过了，这里跳过多尺度直接进入轮询
            debug_print(f"[匹配诊断] 首次全屏1:1+复杂匹配均未命中, 进入轮询")
        except Exception as e:
            debug_print(f"[匹配诊断] ❗ 首次 _try_match 抛异常: {type(e).__name__}: {e}")
    else:
        debug_print(f"[匹配诊断] ⚠️ 首次 _get_shared_screenshot() 返回 None(截图服务未就绪?)")

    # 预计算 ROI 坐标（轮询时复用）
    _roi_x1 = _roi_y1 = _roi_w = _roi_h = 0
    _has_roi = False
    if roi_hint is not None:
        try:
            _rx, _ry = int(roi_hint[0]), int(roi_hint[1])
            _ih, _iw = image_array.shape[:2]
            _pad = 300
            _roi_x1 = max(0, _rx - _pad)
            _roi_y1 = max(0, _ry - _pad)
            _roi_x2 = min(2560, _rx + _iw + _pad)
            _roi_y2 = min(1600, _ry + _ih + _pad)
            _roi_w = _roi_x2 - _roi_x1
            _roi_h = _roi_y2 - _roi_y1
            if _roi_w >= _iw and _roi_h >= _ih:
                _has_roi = True
        except:
            pass

    # ⏭ 智能提前退出：首次截图已跑完所有匹配仍失败，最佳分数远低于阈值则跳过轮询
    if scale_best_scores and timeout > 0.15:
        _best_score = max(v[0] for v in scale_best_scores.values())
        _early_threshold = max(confidence * 0.45, 0.20)
        if _best_score < _early_threshold:
            debug_print(f"[匹配诊断] ⏭ 首次最高分 {_best_score:.3f} < {_early_threshold:.2f}，图片不存在，跳过轮询(节省{timeout:.2f}s)")
            return None

    # 优化:轮询间隔设为 15ms，更快响应
    _POLL_INTERVAL = 0.015
    _screenshot_none_count = 0
    _exception_count = 0
    _loop_iter = 0
    _max_poll_iters = 40  # 可轮询最多40次
    while time.time() - start_time < timeout and _loop_iter < _max_poll_iters:
        if (stop_check and stop_check()) or (stop_check is None and _replay_stop_flag):
            return None
        _loop_iter += 1
        try:
            # ⚡ 用缓存的灰度/缩小截图，省去 cvtColor(5-10ms) + resize(2-5ms)
            if _gray_template is not None and _small_gray_template is not None and _loop_iter % 3 != 0:
                # 缩小匹配（用缓存的小图）
                small_s = _get_shared_small_gray()
                if small_s is None:
                    _screenshot_none_count += 1
                    _interruptible_sleep(_POLL_INTERVAL, stop_check=stop_check)
                    continue
                result = cv2.matchTemplate(small_s, _small_gray_template, cv2.TM_CCOEFF_NORMED)
                _, _rv, _, _rl = cv2.minMaxLoc(result)
                if _rv >= confidence:
                    h, w = image_array.shape[:2]
                    return (_rl[0] * 2, _rl[1] * 2, w, h)
                if not scale_best_scores or scale_best_scores.get(1.0, (0,))[0] < _rv:
                    scale_best_scores[1.0] = (_rv, (_rl[0] * 2, _rl[1] * 2))
            elif _gray_template is not None:
                # 每3次做一次原始尺寸（用缓存的灰度图）
                gray_s = _get_shared_gray()
                if gray_s is None:
                    _screenshot_none_count += 1
                    _interruptible_sleep(_POLL_INTERVAL, stop_check=stop_check)
                    continue
                if _has_roi:
                    gray_roi = gray_s[_roi_y1:_roi_y1+_roi_h, _roi_x1:_roi_x1+_roi_w]
                    if gray_roi.shape[0] >= template_h and gray_roi.shape[1] >= template_w:
                        result = cv2.matchTemplate(gray_roi, _gray_template, cv2.TM_CCOEFF_NORMED)
                        _, _rv, _, _rl = cv2.minMaxLoc(result)
                        if _rv >= confidence:
                            h, w = image_array.shape[:2]
                            return (_rl[0] + _roi_x1, _rl[1] + _roi_y1, w, h)
                else:
                    result = cv2.matchTemplate(gray_s, _gray_template, cv2.TM_CCOEFF_NORMED)
                    _, _rv, _, _rl = cv2.minMaxLoc(result)
                    if _rv >= confidence:
                        h, w = image_array.shape[:2]
                        return (_rl[0], _rl[1], w, h)
            else:
                screenshot_bgr = _get_shared_screenshot()
                if screenshot_bgr is None:
                    _screenshot_none_count += 1
                    _interruptible_sleep(_POLL_INTERVAL, stop_check=stop_check)
                    continue
                result = _fast_match(screenshot_bgr, image_array)
                _, _rv, _, _rl = cv2.minMaxLoc(result)
                if _rv >= confidence:
                    h, w = image_array.shape[:2]
                    return (_rl[0], _rl[1], w, h)
        except Exception as e:
            _exception_count += 1

        _interruptible_sleep(_POLL_INTERVAL, stop_check=stop_check)

    if _loop_iter >= _max_poll_iters:
        debug_print(f"[匹配诊断] ⏭ 轮询已达上限({_max_poll_iters}次)，提前结束(节省{max(0, timeout-(time.time()-start_time)):.2f}s)")

    _func_elapsed = time.time() - _func_start

    # ========== 匹配失败的诊断信息 ==========
    # 关键:即使 scale_best_scores 为空,也要告诉用户为什么(截图全 None? 全部异常?)
    if _screenshot_none_count > 0 or _exception_count > 0:
        debug_print(
            f"[匹配诊断] ⚠️ 循环统计: 截图=None 出现 {_screenshot_none_count} 次, "
            f"异常 {_exception_count} 次, 模板尺寸 {template_w}x{template_h}, 阈值 {confidence:.2f}"
        )
    if not scale_best_scores:
        debug_print(
            f"[匹配诊断] ❌ 完全未触发任何 _try_match 成功,scale_best_scores 为空 "
            f"(timeout={timeout}s 内没有任何有效的截图或全部异常)"
        )
    if scale_best_scores:
        # 按分数排序，输出 top-3 尺度
        sorted_scales = sorted(scale_best_scores.items(), key=lambda x: x[1][0], reverse=True)
        top3 = sorted_scales[:3]
        scale_info = " | ".join([f"scale={s:.2f} score={v[0]:.3f}@{v[1]}" for s, v in top3])
        debug_print(f"[匹配失败诊断] 共尝试 {len(scale_best_scores)} 个尺度,最佳: {scale_info}")
        # 给出可能的原因
        best_score = top3[0][1][0] if top3 else 0
        best_loc = top3[0][1][1] if top3 else None
        if best_score < 0.3:
            debug_print(f"[匹配失败诊断] ⚠️ 最高分仅 {best_score:.3f} < 0.3, 模板可能在屏幕上根本不存在,或完全不同")
        elif best_score < confidence:
            debug_print(f"[匹配失败诊断] ⚠️ 最高分 {best_score:.3f} < 阈值 {confidence:.2f}, 可能是 DPI 缩放/主题切换/部分遮挡")
        # 已移除低于阈值的兜底返回（会导致 wait_for_image 误判图片已出现）

        # 保存失败时的截图到 debug 目录,方便对比
        try:
            from datetime import datetime
            debug_dir = os.path.join(os.path.dirname(image_path) or '.', '_debug_failed_match')
            os.makedirs(debug_dir, exist_ok=True)
            ts = datetime.now().strftime("%H%M%S_%f")[:-3]
            base = os.path.splitext(os.path.basename(image_path))[0]
            fail_path = os.path.join(debug_dir, f"fail_{base}_{ts}.png")
            if 'screenshot_bgr' in dir() and screenshot_bgr is not None:
                cv2.imwrite(fail_path, screenshot_bgr)
                debug_print(f"[匹配失败诊断] 📸 失败截图已保存: {fail_path}")
                debug_print(f"[匹配失败诊断] 💡 对比: 模板={os.path.basename(image_path)}, 截图={fail_path}")
        except Exception as _e:
            debug_print(f"[匹配失败诊断] 保存截图失败: {_e}")

    return None


# 全局缓存
_screenshot_cache = None
_screenshot_time = 0
_screenshot_array_cache = None
_image_cache = {}  # 图像缓存，避免重复加载
_scaled_image_cache = {}  # 多尺度模板缓存 {path: {scale: array}}
_image_access_order = []  # LRU访问顺序记录
_MAX_CACHED_IMAGES = 20  # 最大缓存图像数量，限制内存占用
_mss_instance = None

# 共享截图缓存 - 多线程间复用，避免重复截图
import threading
_shared_screenshot_lock = threading.Lock()

# 多尺度匹配的预设尺度 - 覆盖常见 Windows DPI 缩放 (100%/125%/150%/175%/200%)
# 原范围 [1.0, 0.95, 1.05] 太窄，换电脑/换 DPI 就会匹配不到
_SCALES = [1.0, 0.95, 1.05, 1.1]

# 线程局部的MSS实例（解决多线程问题）
_mss_local = threading.local()

def _get_mss():
    """获取当前线程的 mss 实例（线程安全）"""
    if not hasattr(_mss_local, 'instance'):
        try:
            import mss
            _mss_local.instance = mss.mss()
        except ImportError:
            _mss_local.instance = None
    return _mss_local.instance

def _mss_grab_array():
    """使用 mss 截取全屏并直接返回 numpy BGR 数组（最快路径，零拷贝）"""
    sct = _get_mss()
    if sct is None:
        return None
    monitor = sct.monitors[1]  # 主显示器
    screenshot = sct.grab(monitor)
    # numpy 视图直接取前3通道，再复制为连续数组（OpenCV 要求连续内存）
    img = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(screenshot.height, screenshot.width, 4)
    return img[:, :, :3].copy()

def _mss_grab_roi_array(x, y, w, h):
    """使用 mss 截取指定区域并返回 numpy BGR 数组（比全屏快10倍）"""
    sct = _get_mss()
    if sct is None:
        return None
    monitor = {"left": int(x), "top": int(y), "width": int(w), "height": int(h)}
    screenshot = sct.grab(monitor)
    img = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(screenshot.height, screenshot.width, 4)
    return img[:, :, :3].copy()

def _mss_screenshot():
    """使用 mss 截取全屏并返回 PIL Image（兼容旧接口）"""
    sct = _get_mss()
    if sct is None:
        return None
    monitor = sct.monitors[1]  # 主显示器
    screenshot = sct.grab(monitor)
    from PIL import Image
    return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

def get_cached_screenshot_array():
    """获取缓存的截图数组（BGR格式），如果超过3ms则重新截图（仅使用MSS）"""
    global _screenshot_cache, _screenshot_time, _screenshot_array_cache
    current_time = time.time()
    if _screenshot_array_cache is None or (current_time - _screenshot_time) > 0.003:
        # 只使用MSS，不允许回退
        arr = _mss_grab_array()
        if arr is None:
            raise RuntimeError("MSS截图失败，请检查MSS是否正常工作")
        _screenshot_array_cache = arr
        
        _screenshot_time = current_time
        _screenshot_cache = None  # 标记PIL缓存失效，按需生成
    return _screenshot_array_cache

def get_cached_screenshot():
    """获取缓存的截图，如果超过3ms则重新截图（仅使用MSS）"""
    global _screenshot_cache, _screenshot_time
    current_time = time.time()
    if _screenshot_cache is None or (current_time - _screenshot_time) > 0.003:
        # 只使用MSS，不允许回退
        img = _mss_screenshot()
        if img is None:
            raise RuntimeError("MSS截图失败，请检查MSS是否正常工作")
        _screenshot_cache = img
        
        _screenshot_time = current_time
    return _screenshot_cache

def get_fresh_screenshot():
    """获取最新的屏幕截图，不使用缓存（仅使用MSS）"""
    global _screenshot_cache, _screenshot_time
    # 只使用MSS，不允许回退
    img = _mss_screenshot()
    if img is None:
        raise RuntimeError("MSS截图失败，请检查MSS是否正常工作")
    
    _screenshot_cache = img
    _screenshot_time = time.time()
    return _screenshot_cache

def get_cached_image(image_path):
    """获取缓存的图像，同时预计算并缓存多尺度版本，失败返回None（LRU淘汰限制内存）"""
    global _image_cache, _scaled_image_cache, _image_access_order
    if image_path in _image_cache:
        if image_path in _image_access_order:
            _image_access_order.remove(image_path)
        _image_access_order.append(image_path)
        return _image_cache[image_path]
    
    try:
        from PIL import Image
        import cv2
        pil_image = Image.open(image_path)
        image_array = np.array(pil_image)
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_array = image_array[:, :, ::-1]
        
        target_h, target_w = image_array.shape[:2]
        scaled_versions = {}
        for scale in _SCALES:
            new_w = int(target_w * scale)
            new_h = int(target_h * scale)
            if new_w >= 10 and new_h >= 10:
                scaled_versions[scale] = cv2.resize(
                    image_array, (new_w, new_h), interpolation=cv2.INTER_LINEAR
                )
        
        _image_cache[image_path] = image_array
        _scaled_image_cache[image_path] = scaled_versions
        _image_access_order.append(image_path)
        
        while len(_image_cache) > _MAX_CACHED_IMAGES:
            old_path = _image_access_order.pop(0)
            if old_path in _image_cache:
                arr = _image_cache.pop(old_path)
                del arr
            if old_path in _scaled_image_cache:
                for scale_key, scaled_arr in list(_scaled_image_cache.pop(old_path).items()):
                    del scaled_arr
        
        import gc
        gc.collect()
        
        return image_array
    except Exception as e:
        return None

def clear_image_cache():
    """清除图像缓存"""
    global _image_cache, _screenshot_cache, _scaled_image_cache, _image_access_order
    _image_cache = {}
    _scaled_image_cache = {}
    _image_access_order = []
    _screenshot_cache = None
    import gc
    gc.collect()

def preprocess_image(image_array):
    """
    预处理图像以提高匹配精度 - 优化版本，减少过度处理
    
    Args:
        image_array: 输入图像数组
        
    Returns:
        处理后的图像数组
    """
    try:
        import cv2
        import numpy as np
        
        # 只在必要时进行轻微降噪，保持原始特征
        if len(image_array.shape) == 3:
            # 使用更小的核进行轻微模糊，保留更多细节
            processed = cv2.GaussianBlur(image_array, (1, 1), 0)
            # 适度增强对比度，避免过度处理
            lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            l = clahe.apply(l)
            processed = cv2.merge([l, a, b])
            processed = cv2.cvtColor(processed, cv2.COLOR_LAB2BGR)
        else:
            processed = cv2.GaussianBlur(image_array, (1, 1), 0)
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            processed = clahe.apply(processed)
        
        return processed
    except Exception as e:
        return image_array


def find_image_on_screen(image_path, confidence=0.8, consider_color=True, region_center=None, use_cache=True):
    """
    在屏幕上查找指定图像，增强对纯色图像的识别能力
    
    Args:
        image_path: 图像文件路径
        confidence: 匹配置信度 (0-1)
        consider_color: 是否考虑颜色匹配 (True=同时考虑形状和颜色, False=只考虑形状)
        use_cache: 是否使用截图缓存，默认为True。在需要实时更新的场景设为False
    
    Returns:
        tuple: (x, y, width, height) 或 None (如果未找到)
    """
    # 确保路径使用正确的编码
    if isinstance(image_path, str):
        # 在Windows上处理中文路径
        if sys.platform == "win32":
            # 尝试使用短路径名格式
            try:
                import ctypes
                from ctypes import wintypes
                
                # 获取短路径名
                buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
                ctypes.windll.kernel32.GetShortPathNameW(ctypes.c_wchar_p(image_path), buffer, wintypes.MAX_PATH)
                short_path = buffer.value
                image_path = short_path
            except:
                # 如果获取短路径失败，继续使用原路径
                pass
    
    # 使用 PIL + OpenCV 进行图像识别，避免中文路径问题
    try:
        import numpy as np
        import cv2
        from PIL import Image
        
        # 方法1: 使用 PIL 加载图像（支持中文路径），然后用 OpenCV 匹配
        try:
            # 使用 PIL 加载图像（支持中文路径）
            pil_image = Image.open(image_path)
            image_array = np.array(pil_image)
            # 转换 RGB 到 BGR
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = image_array[:, :, ::-1]
            
            # 获取屏幕截图（直接获取BGR数组，跳过PIL转换）
            if use_cache:
                screenshot_bgr = get_cached_screenshot_array()
            else:
                screenshot_bgr = _mss_grab_array()
            
            # 优先尝试CUDA加速匹配
            result = _match_template_cuda(screenshot_bgr, image_array)
            if result is None:
                # 回退到CPU匹配
                result = cv2.matchTemplate(screenshot_bgr, image_array, cv2.TM_CCOEFF_NORMED)
            
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                height, width = image_array.shape[:2]
                debug_print(f"[匹配] 成功: {os.path.basename(image_path)} 置信度={max_val:.3f}")
                return (max_loc[0], max_loc[1], width, height)
            else:
                debug_print(f"[匹配] 失败: {os.path.basename(image_path)} 置信度={max_val:.3f} (阈值{confidence})")
                # 保存调试截图
                _save_debug_screenshot(screenshot_bgr, f"fail_{os.path.basename(image_path).replace('.', '_')}")
            
            # 方法2: 彩色匹配失败，尝试多尺度匹配
            location = fast_multi_scale_match(screenshot_bgr, image_array, confidence, consider_color=True)
            if location:
                debug_print(f"[匹配] 多尺度匹配成功: {os.path.basename(image_path)}")
                return location
        except Exception as e:
            debug_print(f"[匹配] 异常: {os.path.basename(image_path)} - {e}")
        
        return None
    except Exception as e:
        return None

def is_solid_color_image(image_array, tolerance=0.9):
    """
    检测图像是否为纯色图像，使用更灵活的方法
    
    Args:
        image_array: 图像数组
        tolerance: 纯色判断的容差，0-1之间，越接近1要求越严格
    
    Returns:
        bool: 如果是纯色图像返回True，否则返回False
    """
    try:
        import numpy as np
        
        # 如果是灰度图像
        if len(image_array.shape) == 2:
            # 计算标准差，如果标准差很小，认为是纯色图像
            std_dev = np.std(image_array)
            # 调整标准差阈值，使其更严格
            return std_dev < 20 * (1 - tolerance + 0.1)
        
        # 如果是彩色图像
        # 获取图像尺寸
        height, width = image_array.shape[:2]
        
        # 对于小图像，使用更宽松的标准
        if height * width < 10000:  # 小于100x100的图像
            # 计算每个通道的标准差
            std_devs = []
            for i in range(3):
                std_dev = np.std(image_array[:, :, i])
                std_devs.append(std_dev)
            
            # 如果所有通道的标准差都很小，认为是纯色图像
            max_std_dev = max(std_devs)
            # 对于小图像，调整标准
            return max_std_dev < 60 * (1 - tolerance + 0.1)
        
        # 对于大图像，使用中心区域进行判断，避免边缘抗锯齿影响
        margin = min(height, width) // 10  # 取10%作为边缘 margins
        if margin > 0:
            center_region = image_array[margin:height-margin, margin:width-margin]
            # 计算中心区域的标准差
            std_devs = []
            for i in range(3):
                std_dev = np.std(center_region[:, :, i])
                std_devs.append(std_dev)
            
            # 如果中心区域的标准差很小，认为是纯色图像
            max_std_dev = max(std_devs)
            # 中心区域使用更合理的标准
            if max_std_dev < 25 * (1 - tolerance + 0.1):
                return True
        
        # 如果中心区域检查失败，再检查整个图像
        std_devs = []
        for i in range(3):
            std_dev = np.std(image_array[:, :, i])
            std_devs.append(std_dev)
        
        # 如果所有通道的标准差都很小，认为是纯色图像
        max_std_dev = max(std_devs)
        # 使用更合理的标准差阈值
        return max_std_dev < 35 * (1 - tolerance + 0.1)
    except Exception as e:
        return False

def find_solid_color_region(screenshot_bgr, image_array, consider_color=True, region_center=None):
    """
    在屏幕上查找纯色区域，优化版
    
    Args:
        screenshot_bgr: 屏幕截图的BGR格式
        image_array: 要查找的图像数组
        consider_color: 是否考虑颜色匹配
        region_center: 框选区域的中心坐标 (x, y)，如果提供则选择离此点最近的区域
    
    Returns:
        tuple: (x, y, width, height) 或 None
    """
    try:
        import numpy as np
        import cv2
        
        # 获取目标图像的主要颜色（使用中心区域计算，避免边缘抗锯齿影响）
        if len(image_array.shape) == 3:
            # 彩色图像
            if consider_color:
                # 使用中心区域计算主要颜色，避免边缘抗锯齿影响
                h, w = image_array.shape[:2]
                center_h, center_w = h // 2, w // 2
                margin = min(h, w) // 4  # 取四分之一作为边缘 margins
                center_region = image_array[margin:h-margin, margin:w-margin]
                
                # 使用中位数计算主要颜色
                main_color = np.median(center_region, axis=(0, 1)).astype(np.uint8)
                # 颜色匹配范围 - 自适应容差
                color_tolerance = 8  # 适当增加容差，适应屏幕色彩差异
                lower_bound = np.zeros(3, dtype=np.uint8)
                upper_bound = np.zeros(3, dtype=np.uint8)
                for i in range(3):
                    lower_bound[i] = max(0, int(main_color[i]) - color_tolerance)
                    upper_bound[i] = min(255, int(main_color[i]) + color_tolerance)
                
                mask = cv2.inRange(screenshot_bgr, lower_bound, upper_bound)
            else:
                # 转换为灰度图
                gray_screenshot = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
                gray_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
                
                # 使用中心区域计算主要颜色
                h, w = gray_image.shape
                center_h, center_w = h // 2, w // 2
                margin = min(h, w) // 4
                center_region = gray_image[margin:h-margin, margin:w-margin]
                
                main_color = np.median(center_region).astype(np.uint8)
                # 缩小颜色匹配范围
                color_tolerance = 3  # 降低到3，提高颜色匹配精确度
                lower_bound = max(main_color - color_tolerance, 0)
                upper_bound = min(main_color + color_tolerance, 255)
                # 确保lower_bound和upper_bound是标量值
                lower_bound = int(lower_bound)
                upper_bound = int(upper_bound)
                mask = cv2.inRange(gray_screenshot, lower_bound, upper_bound)
        else:
            # 灰度图像
            h, w = image_array.shape
            center_h, center_w = h // 2, w // 2
            margin = min(h, w) // 4
            center_region = image_array[margin:h-margin, margin:w-margin]
            
            main_color = np.median(center_region).astype(np.uint8)
            color_tolerance = 10  # 适当增加容差，适应屏幕色彩差异
            lower_bound = max(main_color - color_tolerance, 0)
            upper_bound = min(main_color + color_tolerance, 255)
            # 确保lower_bound和upper_bound是标量值
            lower_bound = int(lower_bound)
            upper_bound = int(upper_bound)
            # 对于灰度图像，需要先转换为单通道
            if len(screenshot_bgr.shape) == 3:
                gray_screenshot = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
                mask = cv2.inRange(gray_screenshot, lower_bound, upper_bound)
            else:
                mask = cv2.inRange(screenshot_bgr, lower_bound, upper_bound)
        
        # 进一步减小形态学操作的强度，避免区域过度扩大
        kernel = np.ones((1, 1), np.uint8)  # 从2x2减小到1x1，最小化形态学操作影响
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        # 不使用CLOSE操作，避免过度连接相似颜色区域
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 获取目标图像的尺寸
        target_height, target_width = image_array.shape[:2]
        target_area = target_width * target_height
        target_aspect_ratio = target_width / target_height if target_height > 0 else 1
        
        # 筛选合适的轮廓
        best_contour = None
        if region_center:
            best_distance = float('inf')
        else:
            best_score = 0
        
        for contour in contours:
            # 获取轮廓的边界矩形
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # 更宽松的面积匹配条件：面积必须在目标面积的50%-150%之间
            area_ratio = min(area, target_area) / max(area, target_area)
            if area < target_area * 0.5 or area > target_area * 1.5:
                continue
                
            # 计算宽高比匹配度
            aspect_ratio = w / h if h > 0 else 1
            aspect_ratio_diff = abs(aspect_ratio - target_aspect_ratio) / max(aspect_ratio, target_aspect_ratio)
            aspect_ratio_score = max(0, 1 - aspect_ratio_diff * 2)  # 稍微放宽宽高比匹配
            
            # 计算尺寸匹配度
            width_ratio = min(w, target_width) / max(w, target_width)
            height_ratio = min(h, target_height) / max(h, target_height)
            
            # 计算轮廓填充度（轮廓面积与其边界矩形面积的比值）
            contour_area = cv2.contourArea(contour)
            fill_ratio = contour_area / area if area > 0 else 0
            
            # 增加颜色一致性检查
            # 检查轮廓内的颜色是否与主要颜色一致
            roi = screenshot_bgr[y:y+h, x:x+w]
            if len(image_array.shape) == 3 and consider_color:
                roi_mean_color = np.mean(roi, axis=(0, 1)).astype(np.uint8)
                color_diff = np.mean(np.abs(roi_mean_color.astype(int) - main_color.astype(int)))
                color_consistency = max(0, 1 - color_diff / 255)  # 颜色一致性得分
            else:
                roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                roi_mean_color = np.mean(roi_gray).astype(np.uint8)
                color_diff = abs(roi_mean_color.astype(int) - main_color.astype(int))
                color_consistency = max(0, 1 - color_diff / 255)  # 颜色一致性得分
            
            # 综合评分，调整权重，增加颜色一致性权重
            score = (area_ratio * 0.2 + width_ratio * 0.15 + height_ratio * 0.15 + 
                    aspect_ratio_score * 0.1 + fill_ratio * 0.1 + color_consistency * 0.3)
            
            # 只有当综合评分足够高时才考虑
            if score > 0.55:  # 降低阈值，确保不错过正确匹配
                if region_center:
                    # 计算轮廓中心点到region_center的距离
                    contour_center_x = x + w // 2
                    contour_center_y = y + h // 2
                    distance = ((contour_center_x - region_center[0]) ** 2 + 
                               (contour_center_y - region_center[1]) ** 2) ** 0.5
                    # 如果是第一个轮廓或者距离更近，则更新最佳轮廓
                    if best_contour is None or distance < best_distance:
                        best_contour = contour
                        best_distance = distance
                else:
                    # 没有region_center时，使用综合评分
                    if score > best_score:
                        best_score = score
                        best_contour = contour
        
        if best_contour is not None:
            x, y, w, h = cv2.boundingRect(best_contour)
            return (x, y, w, h)
        
        return None
    except Exception as e:
        return None

def fast_multi_scale_match(screenshot_bgr, image_array, confidence, consider_color=True, image_path=None, return_scores=False):
    """
    超快速多尺度匹配 - 优先使用预缓存的尺度，无法命中时实时resize

    Args:
        return_scores: 如果为 True, 同时返回每个尺度的 (max_val, max_loc), 用于失败诊断
    Returns:
        tuple: (loc, scores_dict) 当 return_scores=True
        tuple: (x, y, w, h) 当 return_scores=False
    """
    all_scores = {}  # {scale: (max_val, max_loc)}
    try:
        import numpy as np
        import cv2

        target_height, target_width = image_array.shape[:2]

        if image_path and image_path in _scaled_image_cache:
            cached = _scaled_image_cache[image_path]
            for scale in _SCALES:
                if scale not in cached:
                    continue
                if scale == 1.0:  # 跳过1.0，刚才已经匹配过了
                    continue
                scaled_img = cached[scale]
                result = cv2.matchTemplate(screenshot_bgr, scaled_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                all_scores[scale] = (max_val, max_loc)
                if max_val >= confidence:
                    h, w = scaled_img.shape[:2]
                    if return_scores:
                        return (max_loc[0], max_loc[1], w, h), all_scores
                    return (max_loc[0], max_loc[1], w, h)
            if return_scores:
                return None, all_scores
            return None

        for scale in _SCALES:
            if scale == 1.0:  # 跳过1.0，刚才已经匹配过了
                continue
            new_width = int(target_width * scale)
            new_height = int(target_height * scale)

            if new_width < 10 or new_height < 10:
                continue

            if new_width == target_width and new_height == target_height:
                continue

            resized_image = cv2.resize(image_array, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            result = cv2.matchTemplate(screenshot_bgr, resized_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            all_scores[scale] = (max_val, max_loc)
            if max_val >= confidence:
                if return_scores:
                    return (max_loc[0], max_loc[1], new_width, new_height), all_scores
                return (max_loc[0], max_loc[1], new_width, new_height)

        if return_scores:
            return None, all_scores
        return None
    except Exception as e:
        if return_scores:
            return None, all_scores
        return None


def multi_scale_template_matching(screenshot_bgr, image_array, confidence, consider_color=True, region_center=None):
    """
    多尺度模板匹配，提高对不同尺寸图像的识别能力 - 性能优化版本
    
    Args:
        screenshot_bgr: 屏幕截图的BGR格式
        image_array: 要查找的图像数组
        confidence: 匹配置信度
        consider_color: 是否考虑颜色匹配
        region_center: 框选区域的中心坐标 (x, y)，如果提供则选择离此点最近的区域
    
    Returns:
        tuple: (x, y, width, height) 或 None
    """
    try:
        import numpy as np
        import cv2
        
        # 获取目标图像尺寸
        target_height, target_width = image_array.shape[:2]
        
        # 优化：减少尺度数量，优先尝试接近1.0的尺度
        # 1:1匹配失败后，最可能是轻微缩放，优先尝试0.9-1.1范围
        scales = [1.0, 0.95, 1.05, 0.9, 1.1]
        
        best_match = None
        if region_center:
            best_distance = float('inf')
        else:
            best_score = 0
        
        # 预转换屏幕截图为灰度（如果需要），避免重复转换
        if not consider_color:
            gray_screenshot = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
        
        for scale in scales:
            # 计算缩放后的尺寸
            new_width = int(target_width * scale)
            new_height = int(target_height * scale)
            
            # 跳过太小的图像
            if new_width < 10 or new_height < 10:
                continue
            
            # 优化：使用更快的INTER_LINEAR插值算法
            resized_image = cv2.resize(image_array, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # 执行模板匹配
            if consider_color and len(resized_image.shape) == 3:
                result = cv2.matchTemplate(screenshot_bgr, resized_image, cv2.TM_CCOEFF_NORMED)
            else:
                # 转换为灰度图像
                if len(resized_image.shape) == 3:
                    gray_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
                else:
                    gray_image = resized_image
                    
                result = cv2.matchTemplate(gray_screenshot, gray_image, cv2.TM_CCOEFF_NORMED)
            
            # 快速检查是否有匹配（使用max_val）
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 如果没有达到置信度，跳过详细计算
            if max_val < confidence:
                continue
            
            # 如果提供了region_center，找到所有匹配度高于阈值的点
            if region_center:
                # 找到所有匹配度大于阈值的点
                locations = np.where(result >= confidence)
                
                if len(locations[0]) > 0:
                    # 计算每个匹配点到region_center的距离
                    for pt in zip(*locations[::-1]):  # 切换x和y坐标
                        match_value = result[pt[1], pt[0]]
                        # 计算中心点坐标
                        center_x = pt[0] + new_width // 2
                        center_y = pt[1] + new_height // 2
                        # 计算欧几里得距离
                        distance = ((center_x - region_center[0]) ** 2 + 
                                   (center_y - region_center[1]) ** 2) ** 0.5
                        
                        # 更新全局最佳匹配
                        if best_match is None or distance < best_distance:
                            best_match = (pt[0], pt[1], new_width, new_height)
                            best_distance = distance
                            best_score = match_value
            else:
                # 没有region_center时，使用传统方法
                # 如果当前匹配度更好，更新最佳匹配
                if max_val > best_score:
                    best_score = max_val
                    best_match = (max_loc[0], max_loc[1], new_width, new_height)
        
        # 如果最佳匹配度满足要求，返回结果
        if best_match and best_score >= confidence:
            return best_match
        
        return None
    except Exception as e:
        return None

def click_image(image_path, confidence=0.8, action='left_click', consider_color=True, region_center=None):
    """
    在屏幕上查找并点击指定图像（完全基于图像识别）
    
    Args:
        image_path: 图像文件路径
        confidence: 匹配置信度 (0-1)
        action: 点击类型 ('left_click', 'right_click', 'double_click')
        consider_color: 是否考虑颜色匹配 (True=同时考虑形状和颜色, False=只考虑形状)
    
    Returns:
        bool: 是否成功找到并点击图像
    """
    try:
        location = find_image_on_screen(image_path, confidence, consider_color, region_center)
        if location:
            x, y, width, height = location
            center_x = x + width // 2
            center_y = y + height // 2
            
            # 移动到图像中心并点击
            pyautogui.moveTo(center_x, center_y, duration=0.01)
            
            if action == 'left_click':
                pyautogui.click()
            elif action == 'right_click':
                pyautogui.rightClick()
            elif action == 'double_click':
                pyautogui.doubleClick()
            
            return True
        return False
    except Exception as e:
        return False

def save_screenshot(file_path):
    """
    保存屏幕截图
    
    Args:
        file_path: 保存截图的文件路径
    
    Returns:
        bool: 是否成功保存截图
    """
    try:
        screenshot = _mss_screenshot()
        screenshot.save(file_path)
        return True
    except Exception as e:
        return False

def find_image_with_akaze(image_path, confidence=0.75, region_center=None):
    """
    使用AKAZE特征匹配在屏幕上查找图像
    
    Args:
        image_path: 图像文件路径
        confidence: 匹配置信度 (0-1)
        region_center: 框选区域中心坐标
    
    Returns:
        tuple: (x, y, width, height) 或 None (如果未找到)
    """
    try:
        import pyautogui
        from PIL import Image
        
        # 加载模板图像
        pil_image = Image.open(image_path)
        template = np.array(pil_image)
        
        # 转换为灰度图
        if len(template.shape) == 3:
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            template_gray = template
        
        # 获取屏幕截图（直接获取BGR数组）
        screenshot_bgr = _mss_grab_array()
        
        # 转换为灰度图
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
        
        # 创建AKAZE检测器 - 优化参数，提高速度
        akaze = cv2.AKAZE_create(
            descriptor_type=cv2.AKAZE_DESCRIPTOR_MLDB,
            descriptor_size=0,
            descriptor_channels=3,
            threshold=0.001,  # 提高阈值，减少特征点数量，提高速度
            nOctaves=3,       # 减少octave层数
            nOctaveLayers=3,  # 减少每层layer数
            diffusivity=cv2.KAZE_DIFF_PM_G2
        )
        
        # 提取特征点和描述符
        kp1, des1 = akaze.detectAndCompute(template_gray, None)
        kp2, des2 = akaze.detectAndCompute(screenshot_gray, None)
        
        if des1 is None or des2 is None:
            return None
        
        # 使用BFMatcher进行匹配
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        
        # 使用KNN匹配获取前2个最佳匹配
        matches = bf.knnMatch(des1, des2, k=2)
        
        # 应用Lowe's ratio test筛选好的匹配点
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.75 * n.distance:  # Lowe's ratio test
                    good_matches.append(m)
        
        # 如果匹配点数量太少，返回None
        if len(good_matches) < 4:  # 降低匹配点数量要求
            return None
        
        # 提取匹配点坐标
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # 使用RANSAC计算单应性矩阵
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        if M is None:
            return None
        
        # 检查RANSAC内点比例
        inliers_ratio = np.sum(mask) / len(mask) if mask is not None else 0
        if inliers_ratio < 0.2:  # 至少20%的内点
            return None
        
        # 获取模板图像的四个角点 [x, y] 格式
        h, w = template_gray.shape
        pts = np.float32([[0, 0], [w-1, 0], [0, h-1], [w-1, h-1]]).reshape(-1, 1, 2)
        
        # 计算变换后的四个角点
        dst = cv2.perspectiveTransform(pts, M)
        
        # 计算边界框
        x_min = int(min(dst[:, 0, 0]))
        y_min = int(min(dst[:, 0, 1]))
        x_max = int(max(dst[:, 0, 0]))
        y_max = int(max(dst[:, 0, 1]))
        
        width = x_max - x_min
        height = y_max - y_min
        
        # 验证尺寸合理性
        expected_area = h * w
        actual_area = width * height
        area_ratio = min(actual_area, expected_area) / max(actual_area, expected_area) if max(actual_area, expected_area) > 0 else 0
        
        if area_ratio < 0.3:  # 面积差异过大
            return None
        
        
        return (x_min, y_min, width, height)
        
    except Exception as e:
        return None