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
        return _replay_stop_flag or (stop_check and stop_check())
    start = time.time()
    poll_interval = 0.02  # 20ms轮询一次停止信号
    while time.time() - start < duration:
        if _replay_stop_flag or (stop_check and stop_check()):
            return True
        time.sleep(poll_interval)
    return _replay_stop_flag or (stop_check and stop_check())

def replay_coordinate_operations(recording_data, folder_path, replay_interval=0.5, consider_color=False, region_center=None, match_timeout=1.5, stop_check=None, skip_cache_clear=False):
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
        tuple: (成功执行的操作数, 总操作数)
    """
    global _replay_stop_flag
    
    success_count = 0
    total_operations = len(recording_data)
    
    # 禁用pyautogui的安全检查 + 去掉默认 100ms 暂停(极速模式)
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    
    # 仅非组合技调用（无stop_check）时清除停止标志
    # 组合技调用时不清除，避免一个runner重置了全局标志导致其他runner无法被正确停止
    if stop_check is None:
        _replay_stop_flag = False
    
    for i, operation in enumerate(recording_data):
        # 检查是否收到停止信号（全局标志 + 各runner独立检查）
        if _replay_stop_flag or (stop_check and stop_check()):
            break
        try:
            # 获取操作信息
            step = operation.get('step', i + 1)
            action_type = operation.get('action_type', 'left_click')
            image_name = operation.get('image', '')
            delay = operation.get('delay', 0)  # 获取每个操作的延迟时间，默认为0
            
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
                # 根据图片大小动态调整置信度：一律使用 0.8
                try:
                    from PIL import Image
                    with Image.open(image_path) as img:
                        img_width, img_height = img.size
                        # 统一使用 0.8，不分大小
                        dynamic_confidence = 0.8
                        if img_width < 50 or img_height < 50:
                            # 小图标同样启用颜色匹配——颜色提供了更多判别特征
                            # 禁用颜色匹配会使 44x22 这样的小模板在灰度下误匹配到相似区域
                            use_color = consider_color
                            debug_print(f"[回放] 步骤 {step}: 小图标检测，尺寸 {img_width}x{img_height}，置信度 {dynamic_confidence}，颜色匹配={'开启' if use_color else '关闭'}")
                        else:
                            use_color = consider_color
                except Exception:
                    dynamic_confidence = 0.8
                    use_color = consider_color
                # 根据 match_timeout 自适应分配匹配时间
                # 第一次尝试：给足 match_timeout 的 60%，确保有充足时间完成截图轮询
                first_attempt_timeout = max(0.5, match_timeout * 0.6)
                location = find_image_with_timeout(image_path, confidence=dynamic_confidence, timeout=first_attempt_timeout, consider_color=use_color, region_center=region_center, stop_check=stop_check)

                if not location:
                    debug_print(f"[回放] ❌ 步骤 {step}: 图片匹配失败，跳过（图片: {image_name}，置信度: {dynamic_confidence}）")
                    continue
                else:
                    debug_print(f"[回放] ✅ 步骤 {step}: 图片匹配成功（位置: {location}）")
                    # 解析找到的坐标
                    x, y, width, height = location
                    # 计算中心点
                    center_x = x + width // 2
                    center_y = y + height // 2
                    
            else:
                # 如果没有图像文件，跳过此步骤（不再使用坐标作为备用方案）
                continue
            
            # 极速模式：直接移动并点击，不添加任何延迟
            # 使用 PyDirectInput 风格的低级 mouseDown/Up,比 click() 快 3-5 倍
            pyautogui.moveTo(center_x, center_y, duration=0)

            # 根据操作类型执行相应操作
            if action_type == 'left_click':
                pyautogui.mouseDown(); pyautogui.mouseUp()
            elif action_type == 'right_click':
                pyautogui.mouseDown(button='right'); pyautogui.mouseUp(button='right')
            elif action_type == 'double_click':
                pyautogui.mouseDown(); pyautogui.mouseUp()
                pyautogui.mouseDown(); pyautogui.mouseUp()
            elif action_type == 'drag':
                pyautogui.mouseDown()
                pyautogui.moveRel(50, 0, duration=0)
                pyautogui.mouseUp()
            else:
                pyautogui.mouseDown(); pyautogui.mouseUp()
            
            success_count += 1
            
            # 极速模式：步骤间无延迟，立即执行下一步
            # 注意：如果需要延迟，请在录制时设置，但建议保持为0以获得最快速度
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            continue
    
    # 清理缓存（有stop_check时表示被组合技runner调用，跳过缓存清理以免影响其他runner）
    if not skip_cache_clear:
        clear_image_cache()
    return success_count, total_operations


def replay_coordinates_only(recording_data, replay_interval=0.5, stop_check=None):
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
    total_operations = len(recording_data)
    
    # 禁用pyautogui的安全检查 + 去掉默认 100ms 暂停(极速模式)
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    
    # 仅非组合技调用（无stop_check）时清除停止标志
    if stop_check is None:
        _replay_stop_flag = False
    
    # 获取屏幕信息
    try:
        import ctypes
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
    except Exception as e:
        # 打印获取屏幕信息失败的错误信息
        debug_print(f"获取屏幕信息失败: {e}")
        return 0, 0
    
    for i, operation in enumerate(recording_data):
        # 检查是否收到停止信号（全局标志 + 各runner独立检查）
        if _replay_stop_flag or (stop_check and stop_check()):
            break
        try:
            # 获取操作信息
            step = operation.get('step', i + 1)
            action_type = operation.get('action_type', 'left_click')
            x = operation.get('x', 0)
            y = operation.get('y', 0)
            delay = operation.get('delay', 0)
            
            # 如果是滚动操作，无需移动鼠标，直接执行滚动
            if action_type == 'scroll':
                scroll_amount = operation.get('scroll_amount', 3)
                pyautogui.scroll(scroll_amount)
                success_count += 1
            else:
                # 移动鼠标到指定坐标
                pyautogui.moveTo(x, y, duration=0.01)
                
                # 获取移动后的实际位置
                actual_x, actual_y = pyautogui.position()
                
                # 根据操作类型执行相应操作
                if action_type == 'left_click':
                    pyautogui.click()
                elif action_type == 'right_click':
                    pyautogui.rightClick()
                elif action_type == 'double_click':
                    pyautogui.doubleClick()
                elif action_type == 'middle_click':
                    pyautogui.middleClick()
                else:
                    pyautogui.click()
                
                success_count += 1
            
            # 操作间隔
            if i < total_operations - 1:
                if delay > 0:
                    time.sleep(delay)
                else:
                    time.sleep(replay_interval)
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
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

def _get_shared_screenshot():
    """获取共享截图（线程安全），3ms内复用同一张截图，避免多线程重复抓屏"""
    global _shared_screenshot, _shared_screenshot_time
    now = time.time()
    with _shared_screenshot_lock:
        if _shared_screenshot is None or (now - _shared_screenshot_time) > _SHARED_SCREENSHOT_INTERVAL:
            _shared_screenshot = _mss_grab_array()
            _shared_screenshot_time = now
        return _shared_screenshot


def find_image_with_timeout(image_path, confidence=0.8, timeout=0.5, consider_color=True, region_center=None, stop_check=None):
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

    # 多尺度间隔从 5 改成 2,反应速度再提升
    multi_scale_interval = 2
    iteration = 0

    # 截图和模板尺寸（用于诊断 "明明有图却匹配不到" 问题）
    template_h, template_w = image_array.shape[:2]
    debug_print(f"[匹配诊断] 模板 {template_w}x{template_h} | 截图 {screenshot_w}x{screenshot_h} | 阈值 {confidence:.2f} | 颜色 {'开启' if consider_color else '关闭'}")

    # 记录所有尺度的最佳分数（用于失败时诊断）
    scale_best_scores = {}  # {scale: (max_val, max_loc)}

    def _try_match(screenshot, skip_multi_scale=False):
        nonlocal iteration
        iteration += 1
        result = _match_template_cuda(screenshot, image_array)
        if result is None:
            result = cv2.matchTemplate(screenshot, image_array, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        scale_best_scores[1.0] = (max_val, max_loc)
        # 调试:打印实际匹配分数,方便诊断"图片在却匹配不到"
        if iteration == 1 or iteration % 20 == 0:
            debug_print(f"[回放匹配] 迭代{iteration}: 最高置信度={max_val:.3f} (阈值={confidence:.2f}) 位置={max_loc}")
        if max_val >= confidence:
            h, w = image_array.shape[:2]
            return (max_loc[0], max_loc[1], w, h)
        # 第一次迭代不触发多尺度（避免卡死！），只在后面的迭代触发
        if not skip_multi_scale and (iteration % multi_scale_interval == 0):
            loc, all_scores = fast_multi_scale_match(screenshot, image_array, confidence, consider_color, image_path, return_scores=True)
            # 记录每个尺度的最佳分数
            for sc, (mv, ml) in all_scores.items():
                if sc not in scale_best_scores or scale_best_scores[sc][0] < mv:
                    scale_best_scores[sc] = (mv, ml)
            if loc:
                return loc
        return None

    if first_screenshot is not None:
        try:
            if _replay_stop_flag or (stop_check and stop_check()):
                return None
            result = _try_match(first_screenshot, skip_multi_scale=True)
            if result is not None:
                return result
        except Exception as e:
            debug_print(f"[匹配诊断] ❗ 首次 _try_match 抛异常: {type(e).__name__}: {e}")
    else:
        debug_print(f"[匹配诊断] ⚠️ 首次 _get_shared_screenshot() 返回 None(截图服务未就绪?)")

    # 优化:轮询间隔从 15ms 降到 5ms,反应速度提升 3 倍
    _POLL_INTERVAL = 0.005
    _screenshot_none_count = 0   # 统计 _get_shared_screenshot 返回 None 的次数
    _exception_count = 0         # 统计 try_match 异常的次数
    while time.time() - start_time < timeout:
        if _replay_stop_flag or (stop_check and stop_check()):
            debug_print(f"[匹配诊断] ⏹ 循环中检测到停止信号,提前退出(timeout 还剩 {max(0, timeout - (time.time() - start_time)):.2f}s)")
            return None
        try:
            screenshot_bgr = _get_shared_screenshot()
            if screenshot_bgr is None:
                _screenshot_none_count += 1
                _interruptible_sleep(_POLL_INTERVAL, stop_check=stop_check)
                continue

            result = _try_match(screenshot_bgr, skip_multi_scale=False)
            if result is not None:
                return result
        except Exception as e:
            _exception_count += 1
            debug_print(f"[匹配诊断] ❗ 循环中 _try_match 抛异常(第 {_exception_count} 次): {type(e).__name__}: {e}")

        _interruptible_sleep(_POLL_INTERVAL, stop_check=stop_check)

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
        if best_score < 0.3:
            debug_print(f"[匹配失败诊断] ⚠️ 最高分仅 {best_score:.3f} < 0.3, 模板可能在屏幕上根本不存在,或完全不同")
        elif best_score < confidence:
            debug_print(f"[匹配失败诊断] ⚠️ 最高分 {best_score:.3f} < 阈值 {confidence:.2f}, 可能是 DPI 缩放/主题切换/部分遮挡")

        # 保存失败时的截图到 debug 目录,方便对比
        try:
            import os
            from datetime import datetime
            debug_dir = os.path.join(os.path.dirname(image_path) or '.', '_debug_failed_match')
            os.makedirs(debug_dir, exist_ok=True)
            ts = datetime.now().strftime("%H%M%S_%f")[:-3]
            base = os.path.splitext(os.path.basename(image_path))[0]
            fail_path = os.path.join(debug_dir, f"fail_{base}_{ts}.png")
            if screenshot_bgr is not None:
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
_shared_screenshot = None
_shared_screenshot_time = 0
_SHARED_SCREENSHOT_INTERVAL = 0.003  # 共享截图刷新间隔3ms（从15ms降到3ms）

# 多尺度匹配的预设尺度 - 覆盖常见 Windows DPI 缩放 (100%/125%/150%/175%/200%)
# 原范围 [1.0, 0.95, 1.05] 太窄，换电脑/换 DPI 就会匹配不到
_SCALES = [1.0, 0.85, 0.9, 0.95, 1.05, 1.1, 1.15, 1.25, 1.5, 1.75, 2.0]

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