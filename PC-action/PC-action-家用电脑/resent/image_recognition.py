import os
import json
import time
import re
import pyautogui
import keyboard
from PIL import ImageGrab
import sys
import cv2
import numpy as np

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

def replay_coordinate_operations(recording_data, folder_path, replay_interval=0.5, consider_color=False, region_center=None, match_timeout=1.5):
    """
    根据录制数据回放操作（完全基于图像匹配）
    
    Args:
        recording_data: 录制数据列表，包含步骤、时间戳、操作类型、图像路径和坐标
        folder_path: 录制文件夹路径
        replay_interval: 操作之间的间隔时间（秒）
        consider_color: 是否考虑颜色匹配 (True=同时考虑形状和颜色, False=只考虑形状)
        match_timeout: 图像匹配超时时间（秒），默认1.5秒
    
    Returns:
        tuple: (成功执行的操作数, 总操作数)
    """
    global _replay_stop_flag
    
    success_count = 0
    total_operations = len(recording_data)
    
    # 禁用pyautogui的安全检查
    pyautogui.FAILSAFE = False
    
    # 清除图像缓存，确保使用最新的图像
    clear_image_cache()
    
    # 清除停止标志，确保新回放可以正常开始
    _replay_stop_flag = False
    
    for i, operation in enumerate(recording_data):
        # 检查是否收到停止信号
        if _replay_stop_flag:
            break
        try:
            # 获取操作信息
            step = operation.get('step', i + 1)
            action_type = operation.get('action_type', 'left_click')
            image_name = operation.get('image', '')
            delay = operation.get('delay', 0)  # 获取每个操作的延迟时间，默认为0
            
            # 处理不需要图像的操作类型
            if action_type in ['text_input', 'keyboard', 'keyboard_direct']:
                # 文本输入和键盘操作不需要图像匹配
                
                if action_type == 'text_input':
                    text = operation.get('text', '')
                    if text:
                        # 使用剪贴板方式支持中文输入
                        import pyperclip
                        pyperclip.copy(text)
                        pyautogui.hotkey('ctrl', 'v')
                        success_count += 1
                    else:
                        continue
                        
                elif action_type in ['keyboard', 'keyboard_direct']:
                    key = operation.get('key', 'enter')
                    
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
                            continue
                        
                        # 执行组合键
                        try:
                            # 使用pyautogui的hotkey方法处理组合键
                            pyautogui.hotkey(*modifiers, main_key)
                            success_count += 1
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
                            except Exception as e2:
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
                            if key_lower in special_keys:
                                pyautogui.press(special_keys[key_lower])
                            else:
                                # 普通字符键
                                pyautogui.press(key)
                            success_count += 1
                        except Exception as e:
                            continue
                
                # 操作间隔 - 使用每个操作设置的延迟时间
                if i < total_operations - 1:  # 不是最后一个操作
                    # 如果设置了延迟时间，使用设置的延迟；否则使用默认间隔
                    if delay > 0:
                        time.sleep(delay)
                    elif not image_name:  # 没有图像识别且没有设置延迟，使用默认间隔
                        time.sleep(replay_interval)
                else:
                    # 最后一个操作，如果有延迟则等待
                    if delay > 0:
                        time.sleep(delay)
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
                location = find_image_with_timeout(image_path, confidence=0.7, timeout=match_timeout, consider_color=consider_color, region_center=region_center)
                
                if not location:
                    # 图片未找到，跳过此步骤，继续执行后续步骤
                    continue
                else:
                    # 解析找到的坐标
                    x, y, width, height = location
                    # 计算中心点
                    center_x = x + width // 2
                    center_y = y + height // 2
                    
            else:
                # 如果没有图像文件，跳过此步骤（不再使用坐标作为备用方案）
                continue
            
            # 极速模式：直接移动并点击，不添加任何延迟
            pyautogui.moveTo(center_x, center_y, duration=0.01)
            
            # 根据操作类型执行相应操作
            if action_type == 'left_click':
                pyautogui.click()
            elif action_type == 'right_click':
                pyautogui.rightClick()
            elif action_type == 'double_click':
                pyautogui.doubleClick()
            elif action_type == 'drag':
                pyautogui.mouseDown()
                pyautogui.moveRel(50, 0)
                pyautogui.mouseUp()
            else:
                pyautogui.click()
            
            success_count += 1
            
            # 极速模式：步骤间无延迟，立即执行下一步
            # 注意：如果需要延迟，请在录制时设置，但建议保持为0以获得最快速度
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            continue
    
    # 清理缓存
    clear_image_cache()
    return success_count, total_operations


def replay_coordinates_only(recording_data, replay_interval=0.5):
    """
    根据坐标数据回放操作（仅坐标，无需图像）
    
    Args:
        recording_data: 录制数据列表，包含步骤、操作类型、坐标
        replay_interval: 操作之间的间隔时间（秒）
    
    Returns:
        tuple: (成功执行的操作数, 总操作数)
    """
    global _replay_stop_flag
    
    success_count = 0
    total_operations = len(recording_data)
    
    # 禁用pyautogui的安全检查
    pyautogui.FAILSAFE = False
    
    # 清除停止标志，确保新回放可以正常开始
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
        # 检查是否收到停止信号
        if _replay_stop_flag:
            break
        try:
            # 获取操作信息
            step = operation.get('step', i + 1)
            action_type = operation.get('action_type', 'left_click')
            x = operation.get('x', 0)
            y = operation.get('y', 0)
            delay = operation.get('delay', 0)
            
            
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


def find_image_with_timeout(image_path, confidence=0.8, timeout=0.5, consider_color=True, region_center=None):
    """
    在屏幕上查找指定图像，支持超时等待（使用截图缓存加速）
    
    Args:
        image_path: 图像文件路径
        confidence: 匹配置信度 (0-1)
        timeout: 最长等待时间（秒），默认0.5秒
        consider_color: 是否考虑颜色匹配 (True=同时考虑形状和颜色, False=只考虑形状)
    
    Returns:
        tuple: (x, y, width, height) 或 None (如果未找到)
    """
    import numpy as np
    import cv2
    
    start_time = time.time()
    
    # 使用缓存的图像，避免重复从磁盘加载
    image_array = get_cached_image(image_path)
    if image_array is None:
        return None
    
    # 极速轮询（使用截图缓存，避免每次重新截屏）
    while time.time() - start_time < timeout:
        try:
            # 使用缓存的截图（100ms内复用同一张截图，大幅减少截屏开销）
            screenshot = get_cached_screenshot()
            screenshot_array = np.array(screenshot)
            if len(screenshot_array.shape) == 3 and screenshot_array.shape[2] == 3:
                screenshot_bgr = screenshot_array[:, :, ::-1]
            else:
                screenshot_bgr = screenshot_array
            
            # OpenCV 模板匹配
            result = cv2.matchTemplate(screenshot_bgr, image_array, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                height, width = image_array.shape[:2]
                return (max_loc[0], max_loc[1], width, height)
        except Exception as e:
            pass
        
        time.sleep(0.005)  # 每5ms检查一次
    
    return None


# 全局缓存
_screenshot_cache = None
_screenshot_time = 0
_image_cache = {}  # 图像缓存，避免重复加载

def get_cached_screenshot():
    """获取缓存的截图，如果超过100ms则重新截图"""
    global _screenshot_cache, _screenshot_time
    current_time = time.time()
    if _screenshot_cache is None or (current_time - _screenshot_time) > 0.1:
        _screenshot_cache = pyautogui.screenshot()
        _screenshot_time = current_time
    return _screenshot_cache

def get_fresh_screenshot():
    """获取最新的屏幕截图，不使用缓存"""
    global _screenshot_cache, _screenshot_time
    _screenshot_cache = pyautogui.screenshot()
    _screenshot_time = time.time()
    return _screenshot_cache

def get_cached_image(image_path):
    """获取缓存的图像，避免重复从磁盘加载，失败返回None"""
    global _image_cache
    if image_path not in _image_cache:
        try:
            from PIL import Image
            pil_image = Image.open(image_path)
            image_array = np.array(pil_image)
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = image_array[:, :, ::-1]
            _image_cache[image_path] = image_array
        except Exception as e:
            return None
    return _image_cache.get(image_path)

def clear_image_cache():
    """清除图像缓存"""
    global _image_cache, _screenshot_cache
    _image_cache = {}
    _screenshot_cache = None
    # 强制垃圾回收
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


def find_image_on_screen(image_path, confidence=0.85, consider_color=True, region_center=None, use_cache=True):
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
            
            # 获取屏幕截图
            if use_cache:
                screenshot = get_cached_screenshot()
            else:
                screenshot = get_fresh_screenshot()
                
            screenshot_array = np.array(screenshot)
            if len(screenshot_array.shape) == 3 and screenshot_array.shape[2] == 3:
                screenshot_bgr = screenshot_array[:, :, ::-1]  # RGB to BGR
            else:
                screenshot_bgr = screenshot_array
            
            # OpenCV 模板匹配
            result = cv2.matchTemplate(screenshot_bgr, image_array, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                height, width = image_array.shape[:2]
                return (max_loc[0], max_loc[1], width, height)
            
            # 方法2: 彩色匹配失败，尝试多尺度匹配
            location = fast_multi_scale_match(screenshot_bgr, image_array, confidence, consider_color=True)
            if location:
                return location
        except Exception as e:
            pass
        
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

def fast_multi_scale_match(screenshot_bgr, image_array, confidence, consider_color=True):
    """
    超快速多尺度匹配 - 只尝试最关键的3个尺度，优先彩色匹配
    
    Args:
        screenshot_bgr: 屏幕截图的BGR格式
        image_array: 要查找的图像数组 (BGR格式)
        confidence: 匹配置信度
        consider_color: 是否考虑颜色匹配
    
    Returns:
        tuple: (x, y, width, height) 或 None
    """
    try:
        import numpy as np
        import cv2
        
        target_height, target_width = image_array.shape[:2]
        
        # 只尝试3个最关键的尺度：1.0, 0.95, 1.05
        scales = [1.0, 0.95, 1.05]
        
        for scale in scales:
            new_width = int(target_width * scale)
            new_height = int(target_height * scale)
            
            if new_width < 10 or new_height < 10:
                continue
            
            # 使用更快的INTER_LINEAR插值
            resized_image = cv2.resize(image_array, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # 执行彩色模板匹配（更准确）
            result = cv2.matchTemplate(screenshot_bgr, resized_image, cv2.TM_CCOEFF_NORMED)
            
            # 快速检查
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                # 返回匹配位置和缩放后的尺寸
                return (max_loc[0], max_loc[1], new_width, new_height)
        
        return None
    except Exception as e:
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
        screenshot = ImageGrab.grab()
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
        
        # 获取屏幕截图
        screenshot = pyautogui.screenshot()
        screenshot_array = np.array(screenshot)
        
        # 转换为灰度图
        if len(screenshot_array.shape) == 3:
            screenshot_gray = cv2.cvtColor(screenshot_array, cv2.COLOR_BGR2GRAY)
        else:
            screenshot_gray = screenshot_array
        
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