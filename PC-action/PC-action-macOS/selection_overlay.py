"""
选择覆盖层模块
用于屏幕截图和区域选择
"""
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QDoubleSpinBox
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QEvent
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QFont, QGuiApplication
import pyautogui
import time
from beautiful_dialog import StyledMessageDialog

try:
    from styles import PRIMARY_GRADIENT, SECONDARY, ACCENT, TEXT, BORDER, BG, CARD, MUTED
except ImportError:
    PRIMARY_GRADIENT = "#007AFF"
    SECONDARY = "#007AFF"
    ACCENT = "#007AFF"
    TEXT = "#2C3E50"
    BORDER = "#D1D1D6"
    BG = "#FFFFFF"
    CARD = "#FFFFFF"
    MUTED = "#8E8E93"

class SelectionOverlay(QWidget):
    """选择覆盖层，用于屏幕截图和区域选择"""
    
    closed = pyqtSignal()  # 窗口关闭信号
    win_key_detected = pyqtSignal(str)  # Win+key 系统钩子捕获信号
    win_key_detected = pyqtSignal(str)  # Win+key 系统钩子捕获信号
    
    def __init__(self, parent=None, screen_pixmap=None, recording_dir=None, initial_operation_count=0):
        super().__init__()
        self.parent = parent
        self.screen_pixmap = screen_pixmap
        self.recording_dir = recording_dir
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.selecting_button = None  # 记录是哪个按键开始的选择
        self.right_click_pressed = False  # 记录右键是否被按下
        self.right_click_dragged = False  # 记录右键是否被拖动
        self.operation_count = initial_operation_count  # 使用传入的初始操作计数
        self._win_poll_timer = None  # Win键轮询定时器
        self._win_last_recorded = ''  # 防重复
        
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        # 如果提供了屏幕截图，则使用它
        if screen_pixmap:
            # 获取设备像素比，将物理尺寸转换为逻辑尺寸
            screen = QGuiApplication.primaryScreen()
            device_pixel_ratio = screen.devicePixelRatio() if screen else 1.0
            self.screen_size = screen_pixmap.size()
            # 窗口使用逻辑尺寸
            logical_width = int(self.screen_size.width() / device_pixel_ratio)
            logical_height = int(self.screen_size.height() / device_pixel_ratio)
            self.resize(logical_width, logical_height)
            self.move(0, 0)
        else:
            # 获取屏幕尺寸
            screen = self.parent.screen() if self.parent else None
            if screen:
                self.screen_size = screen.size()
                self.resize(self.screen_size)
                self.move(0, 0)
            else:
                # 使用默认尺寸
                screen_size = pyautogui.size()
                self.screen_size = screen_size
                self.resize(screen_size.width, screen_size.height)
                self.move(0, 0)
    
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        print("SelectionOverlay: showEvent触发")
        
        # 延迟一点时间再显示和置顶，确保主窗口已经最小化
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._delayed_show)
    
    def _delayed_show(self):
        """延迟显示和置顶操作"""
        # 立即显示并置顶
        self.raise_()
        self.activateWindow()
        
        # 强制设置焦点，确保键盘事件能被捕获
        self.setFocus(Qt.ActiveWindowFocusReason)
        
        print("SelectionOverlay: 窗口置顶和激活完成")
        
        # 强制刷新显示
        self.repaint()
        
        # 强制处理所有待处理的事件，确保窗口完全显示
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        print("SelectionOverlay: 事件处理完成")
        
        # 再次设置焦点，确保键盘事件能被捕获
        self.setFocus(Qt.ActiveWindowFocusReason)
        
        # 使用定时器持续确保焦点
        from PyQt5.QtCore import QTimer
        self.focus_timer = QTimer()
        self.focus_timer.timeout.connect(self.ensure_focus)
        # 如果刚刚录了 Win+key（可能打开了系统对话框），先不抢焦点
        if getattr(self, '_win_last_recorded', '') == '':
            self.focus_timer.start(100)  # 每100毫秒检查一次焦点
        else:
            print("[WinAPI] Win 刚被录制，延迟启动焦点定时器")
        
        print(f"SelectionOverlay: 窗口大小: {self.width()}x{self.height()}")
        print(f"SelectionOverlay: 窗口位置: {self.x()},{self.y()}")
        print(f"SelectionOverlay: 窗口状态: visible={self.isVisible()}, minimized={self.isMinimized()}")
        print(f"SelectionOverlay: 焦点状态: hasFocus={self.hasFocus()}")
        # 启动 Win+key 轮询检测（GetAsyncKeyState 直读硬件状态）
        self._start_win_hook()
    
    def ensure_focus(self):
        """确保窗口始终有焦点"""
        if not self.hasFocus():
            self.raise_()
            self.activateWindow()
            self.setFocus(Qt.ActiveWindowFocusReason)
            print("SelectionOverlay: 重新获取焦点")
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制半透明背景，无论是否有屏幕截图都使用相同的样式
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        
        # 如果有屏幕截图，在覆盖层上方绘制它
        if self.screen_pixmap:
            painter.drawPixmap(0, 0, self.screen_pixmap)
        
        # 只在第一次录制时显示引导提示文字
        if self.operation_count == 0:
            font = QFont("Arial", 18)
            painter.setFont(font)
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            
            # 在屏幕中央显示提示
            text = "点击鼠标左键选择区域进行录制 | ESC键取消 | T键添加文本 | K键添加按键"
            metrics = painter.fontMetrics()
            text_width = metrics.width(text)
            text_height = metrics.height()
            
            center_x = self.width() // 2
            center_y = self.height() // 2
            
            # 绘制文字背景以提高可读性
            painter.fillRect(center_x - text_width // 2 - 10, center_y - text_height, 
                            text_width + 20, text_height + 10, QColor(0, 0, 0, 200))
            
            painter.drawText(center_x - text_width // 2, center_y, text)
        
        # 如果有选择区域，绘制它
        if self.selection_start and self.selection_end:
            # 计算选择区域
            x = min(self.selection_start.x(), self.selection_end.x())
            y = min(self.selection_start.y(), self.selection_end.y())
            width = abs(self.selection_end.x() - self.selection_start.x())
            height = abs(self.selection_end.y() - self.selection_start.y())
            
            # 绘制选择区域边框（更细的线）
            pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(x, y, width, height)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.selecting = True
            self.selecting_button = event.button()  # 记录是哪个按键开始的选择
            self.update()
        elif event.button() == Qt.RightButton:
            # 右键按下时，记录状态但不立即执行操作
            self.right_click_pressed = True
            self.right_click_dragged = False
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.selecting = True
            self.selecting_button = event.button()  # 记录是哪个按键开始的选择
            self.update()
        elif event.button() == Qt.MiddleButton:
            # 中键取消选择 - 添加确认对话框避免意外关闭
            reply = QMessageBox.question(self, "确认退出", 
                                       "确定要退出选择模式吗？\n(ESC键也可以退出)", 
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.close()
            else:
                # 重新激活窗口
                self.raise_()
                self.activateWindow()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.selecting and (event.buttons() & Qt.LeftButton or event.buttons() & Qt.RightButton):
            self.selection_end = event.pos()
            # 如果是右键拖动，标记为已拖动
            if event.buttons() & Qt.RightButton and self.right_click_pressed:
                self.right_click_dragged = True
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            
            # 确保选择区域有效
            if self.selection_start and self.selection_end:
                x1 = min(self.selection_start.x(), self.selection_end.x())
                y1 = min(self.selection_start.y(), self.selection_end.y())
                x2 = max(self.selection_start.x(), self.selection_end.x())
                y2 = max(self.selection_start.y(), self.selection_end.y())
                
                # 确保选择区域有实际大小
                if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                    # 保存选择区域
                    self.save_selection(x1, y1, x2, y2, button=event.button())
                else:
                    # 选择区域太小，忽略
                    self.selection_start = None
                    self.selection_end = None
                    self.update()
        elif event.button() == Qt.RightButton:
            self.right_click_pressed = False
            
            # 如果是右键拖动，执行框选
            if self.right_click_dragged and self.selecting:
                self.selecting = False
                self.right_click_dragged = False
                
                # 确保选择区域有效
                if self.selection_start and self.selection_end:
                    x1 = min(self.selection_start.x(), self.selection_end.x())
                    y1 = min(self.selection_start.y(), self.selection_end.y())
                    x2 = max(self.selection_start.x(), self.selection_end.x())
                    y2 = max(self.selection_start.y(), self.selection_end.y())
                    
                    # 确保选择区域有实际大小
                    if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                        # 保存选择区域
                        self.save_selection(x1, y1, x2, y2, button=event.button())
                    else:
                        # 选择区域太小，忽略
                        self.selection_start = None
                        self.selection_end = None
                        self.update()
            else:
                # 如果是右键单击，显示上下文菜单
                self.show_context_menu(event.pos())
                self.selecting = False
                self.selection_start = None
                self.selection_end = None
                self.update()
    
    def show_context_menu(self, position):
        """显示右键上下文菜单"""
        from PyQt5.QtWidgets import QMenu, QAction
        
        menu = QMenu(self)
        
        # 添加菜单项
        cancel_action = QAction("取消选择", self)
        cancel_action.triggered.connect(self.close)
        menu.addAction(cancel_action)
        
        add_text_action = QAction("添加文本输入", self)
        add_text_action.triggered.connect(self.add_text_input)
        menu.addAction(add_text_action)
        
        # 添加组合操作菜单项
        add_sequence_action = QAction("添加操作序列", self)
        add_sequence_action.triggered.connect(self.add_operation_sequence)
        menu.addAction(add_sequence_action)
        
        # 显示菜单
        menu.exec_(self.mapToGlobal(position))
    
    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == Qt.Key_Escape:
            # ESC键取消选择
            print(f"[DEBUG] ESC键被按下，准备关闭SelectionOverlay，当前recording_dir: {self.recording_dir}")
            self.close()
        elif event.key() == Qt.Key_T:
            # T键添加文本输入
            self.add_text_input()
        elif event.key() == Qt.Key_K:
            # K键添加按键操作
            self.add_keyboard_input()
        elif event.modifiers() & Qt.ControlModifier:
            # 处理Ctrl组合键
            key = event.key()
            if key == Qt.Key_A:
                self.add_keyboard_shortcut('ctrl+a')
            elif key == Qt.Key_Z:
                self.add_keyboard_shortcut('ctrl+z')
            elif key == Qt.Key_X:
                self.add_keyboard_shortcut('ctrl+x')
            elif key == Qt.Key_C:
                self.add_keyboard_shortcut('ctrl+c')
            elif key == Qt.Key_V:
                self.add_keyboard_shortcut('ctrl+v')
            elif key == Qt.Key_S:
                self.add_keyboard_shortcut('ctrl+s')
            # 阻止事件传播，避免系统快捷键触发
            event.accept()
    
    def save_selection(self, x1, y1, x2, y2, button=Qt.LeftButton):
        """保存选择区域"""
        try:
            # 确保导入必要的模块
            import os
            from datetime import datetime
            from PyQt5.QtGui import QGuiApplication
            
            # 获取主屏幕和设备像素比
            screen = QGuiApplication.primaryScreen()
            device_pixel_ratio = screen.devicePixelRatio()
            
            # 截取选择区域
            if not self.screen_pixmap:
                # 如果没有预先提供的截图，则使用PyQt5截取当前屏幕
                self.screen_pixmap = screen.grabWindow(0)
            
            # 考虑DPI缩放，将逻辑坐标转换为物理坐标
            # 在高DPI屏幕上，需要将坐标乘以设备像素比
            x1_phys = int(x1 * device_pixel_ratio)
            y1_phys = int(y1 * device_pixel_ratio)
            x2_phys = int(x2 * device_pixel_ratio)
            y2_phys = int(y2 * device_pixel_ratio)
            
            # 截取选择区域（使用物理坐标）
            selected_pixmap = self.screen_pixmap.copy(x1_phys, y1_phys, x2_phys-x1_phys, y2_phys-y1_phys)
            
            # 如果还没有录制目录，则创建它（用户实际框选了区域）
            if not self.recording_dir:
                # 创建录制目录，按流程_时间戳格式命名
                from utils import get_recordings_path
                recordings_dir = get_recordings_path()
                os.makedirs(recordings_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                folder_name = f"流程_{timestamp}"
                self.recording_dir = os.path.join(recordings_dir, folder_name)
                os.makedirs(self.recording_dir, exist_ok=True)
                
                # 更新父对象的录制目录
                if hasattr(self.parent, 'current_recording_dir'):
                    self.parent.current_recording_dir = self.recording_dir
            
            # 保存截图
            if self.recording_dir:
                # 确保目录存在
                os.makedirs(self.recording_dir, exist_ok=True)
                
                # 生成文件名
                self.operation_count += 1
                filename = f"操作{self.operation_count}.png"
                filepath = os.path.join(self.recording_dir, filename)
                
                # 保存图片
                selected_pixmap.save(filepath)
                
                # 创建点击操作数据
                # 根据按键设置不同的点击类型
                action_type = 'left_click' if button == Qt.LeftButton else 'right_click'
                
                operation = {
                    'step': self.operation_count,
                    'image': filename,
                    'x': x1,
                    'y': y1,
                    'width': x2 - x1,
                    'height': y2 - y1,
                    'action_type': action_type,  # 根据按键设置点击类型
                    'delay': 0  # 默认无延迟
                }
                
                # 保存操作
                self.save_operation_to_json(operation)
                
                # 点击截取区域的中心点（使用图像识别）
                self.click_selection_center(x1, y1, x2, y2, button, filepath)
                
                # 不再调用continue_selection，因为click_selection_center已经处理了窗口的显示
            else:
                # 如果没有指定目录，只显示截图
                self.show_screenshot_dialog(selected_pixmap)
                
        except Exception as e:
            print(f"保存选择区域失败: {e}")
            StyledMessageDialog(self, title="错误", text=f"保存选择区域失败: {str(e)}", msg_type="critical", buttons="ok").exec_()
    
    def click_selection_center(self, x1, y1, x2, y2, button=Qt.LeftButton, image_path=None):
        """点击截取区域的中心点（基于图像识别）"""
        try:
            # 隐藏SelectionOverlay窗口，让点击事件能够传递到下面的应用程序
            self.hide()
            
            # 短暂延迟，确保窗口完全隐藏
            import time
            time.sleep(0.3)  # 增加延迟时间，确保界面更新
            
            # 获取设备像素比（DPI缩放因子）
            from PyQt5.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            device_pixel_ratio = screen.devicePixelRatio()
            
            action = 'left_click' if button == Qt.LeftButton else 'right_click'
            
            # 如果有图像路径，使用图像识别来找到点击位置
            click_x = None
            click_y = None
            
            if image_path and os.path.exists(image_path):
                try:
                    # 导入图像识别模块
                    from image_recognition import find_image_on_screen
                    
                    # 计算框选区域的中心点（作为优先搜索区域）
                    center_x_phys = x1 + (x2 - x1) // 2
                    center_y_phys = y1 + (y2 - y1) // 2
                    center_x = int(center_x_phys / device_pixel_ratio)
                    center_y = int(center_y_phys / device_pixel_ratio)
                    
                    print(f"使用图像识别查找图片: {image_path}")
                    print(f"优先搜索区域中心: ({center_x}, {center_y})")
                    
                    # 在屏幕上查找图像
                    location = find_image_on_screen(
                        image_path, 
                        confidence=0.8,  # 置信度阈值
                        consider_color=True,
                        region_center=(center_x, center_y)  # 优先在框选区域附近搜索
                    )
                    
                    if location:
                        # 找到图像，使用图像位置点击
                        img_x, img_y, img_w, img_h = location
                        click_x = img_x + img_w // 2
                        click_y = img_y + img_h // 2
                        print(f"图像识别成功: 找到图像在 ({img_x}, {img_y}), 点击中心: ({click_x}, {click_y})")
                    else:
                        # 图像识别失败，不执行点击
                        print("图像识别失败: 未在屏幕上找到匹配的图片，跳过点击操作")
                except Exception as e:
                    print(f"图像识别出错: {e}，跳过点击操作")
            else:
                # 没有图像路径，不执行点击
                print(f"无图像路径，跳过点击操作")
            
            # 只有在找到点击位置时才执行点击
            if click_x is not None and click_y is not None:
                # 执行点击操作
                import pyautogui
                # 确保pyautogui安全设置不会阻止点击
                pyautogui.FAILSAFE = False
                
                # 先移动鼠标到目标位置，再执行点击
                pyautogui.moveTo(click_x, click_y, duration=0.01)
                
                if button == Qt.LeftButton:
                    pyautogui.click()
                else:
                    pyautogui.rightClick()
                    
                print(f"执行点击 ({action}): ({click_x}, {click_y})")
            else:
                print(f"未执行点击 ({action}): 图像识别未找到目标，停止录制")
                # 图像识别失败，关闭录制窗口并停止录制
                self.close()
                return
            
            # 点击完成后间隔0.5秒再继续
            time.sleep(0.5)
            
            # 重新截取屏幕，获取点击后的屏幕内容
            screen = QGuiApplication.primaryScreen()
            self.screen_pixmap = screen.grabWindow(0)
            
            # 获取设备像素比，将物理尺寸转换为逻辑尺寸
            device_pixel_ratio = screen.devicePixelRatio()
            logical_width = int(self.screen_pixmap.width() / device_pixel_ratio)
            logical_height = int(self.screen_pixmap.height() / device_pixel_ratio)
            self.resize(logical_width, logical_height)
            
            # 重新显示SelectionOverlay窗口
            self.show()
            self.raise_()
            self.activateWindow()
            
            # 强制设置焦点，确保键盘事件能被捕获
            self.setFocus(Qt.ActiveWindowFocusReason)
            
            # 强制重绘窗口，确保显示最新的屏幕内容
            self.update()
            
        except Exception as e:
            print(f"点击截取区域中心点失败: {e}")
            # 确保在出错时也重新显示窗口
            try:
                self.show()
                self.raise_()
                self.activateWindow()
                
                # 强制设置焦点，确保键盘事件能被捕获
                self.setFocus(Qt.ActiveWindowFocusReason)
                
                self.update()
            except:
                pass
    
    def save_operation_to_json(self, operation_data):
        """保存操作信息到JSON文件"""
        try:
            # 检查是否有录制目录
            if not self.recording_dir:
                print("错误: 没有录制目录，无法保存操作信息")
                return
                
            recording_json_path = os.path.join(self.recording_dir, 'recording.json')
            
            # 加载现有数据
            if os.path.exists(recording_json_path):
                operations = json.load(open(recording_json_path, 'r', encoding='utf-8'))
            else:
                operations = []
            
            # 添加新操作
            operations.append(operation_data)
            
            # 保存到文件
            with open(recording_json_path, 'w', encoding='utf-8') as f:
                json.dump(operations, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存操作信息失败: {e}")
    
    # ---- 全局键盘钩子管理: 避免干扰输入法IME ----
    def _start_win_hook(self):
        """启动 Win+key 检测：Windows API GetAsyncKeyState 直接读硬件状态（无需权限，无视拦截）"""
        from PyQt5.QtCore import QTimer

        # 先停掉旧定时器，避免重复创建
        if self._win_poll_timer is not None:
            try:
                self._win_poll_timer.stop()
            except Exception:
                pass
            try:
                self._win_poll_timer.deleteLater()
            except Exception:
                pass
            self._win_poll_timer = None

        # 连接信号（只连一次）
        try:
            self.win_key_detected.disconnect()
        except TypeError:
            pass
        self.win_key_detected.connect(self._on_win_key_detected)

        self._win_last_recorded = ''
        self._win_poll_timer = QTimer(self)
        self._win_poll_timer.timeout.connect(self._poll_win_key)
        self._win_poll_timer.start(50)
        print("[WinAPI] 轮询已启动 (GetAsyncKeyState)")

    def _poll_win_key(self):
        """每 50ms 查询 Win+key 状态（主线程，直接调 Windows API）"""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # VK_LWIN=0x5B  VK_RWIN=0x5C
            win_down = (user32.GetAsyncKeyState(0x5B) & 0x8000) != 0
            if not win_down:
                win_down = (user32.GetAsyncKeyState(0x5C) & 0x8000) != 0
            if win_down:
                # Win 按住时暂停焦点争夺（让系统对话框正常工作）
                if hasattr(self, 'focus_timer') and self.focus_timer is not None:
                    if self.focus_timer.isActive():
                        self.focus_timer.stop()
                # 扫描 A-Z (0x41-0x5A)
                for vk in range(0x41, 0x5B):
                    if (user32.GetAsyncKeyState(vk) & 0x8000) != 0:
                        letter = chr(vk + 0x20)  # 大写→小写
                        key_str = f'win+{letter}'
                        if self._win_last_recorded != key_str:
                            self._win_last_recorded = key_str
                            print(f"[WinAPI] win+{letter}")
                            self.win_key_detected.emit(key_str)
                        return
                # 扫描 0-9 (0x30-0x39)
                for vk in range(0x30, 0x3A):
                    if (user32.GetAsyncKeyState(vk) & 0x8000) != 0:
                        digit = chr(vk)
                        key_str = f'win+{digit}'
                        if self._win_last_recorded != key_str:
                            self._win_last_recorded = key_str
                            print(f"[WinAPI] win+{digit}")
                            self.win_key_detected.emit(key_str)
                        return
            else:
                self._win_last_recorded = ''
                # Win 松开后，如果焦点定时器没在跑且窗口可见，立即启动
                if hasattr(self, 'focus_timer') and self.focus_timer is not None:
                    if not self.focus_timer.isActive() and self.isVisible():
                        self.focus_timer.start(100)
        except Exception as e:
            print(f"[WinAPI] 轮询错误: {e}")

    def _on_win_key_detected(self, key_str):
        """主线程处理 Win+key 录制"""
        try:
            if not self.recording_dir:
                from utils import get_recordings_path
                from datetime import datetime
                import os
                recordings_dir = get_recordings_path()
                os.makedirs(recordings_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                folder_name = f"流程_{timestamp}"
                self.recording_dir = os.path.join(recordings_dir, folder_name)
                os.makedirs(self.recording_dir, exist_ok=True)
                if hasattr(self.parent, 'current_recording_dir'):
                    self.parent.current_recording_dir = self.recording_dir
                print(f"[WinAPI] 自动创建录制目录: {self.recording_dir}")
            self.add_keyboard_shortcut(key_str)
        except Exception as e:
            print(f"[WinAPI] 错误: {e}")

    def _stop_win_hook(self):
        """停止轮询定时器"""
        if hasattr(self, '_win_poll_timer') and self._win_poll_timer is not None:
            try:
                self._win_poll_timer.stop()
            except Exception:
                pass
            try:
                self._win_poll_timer.deleteLater()
            except Exception:
                pass
            self._win_poll_timer = None
        self._win_last_recorded = ''
        print("[WinAPI] 轮询已停止")

    def _disable_global_hooks(self):
        """彻底停止键盘监听线程 + 卸载系统钩子，让输入法能正常工作"""
        import keyboard as _kb
        import time as _time
        parent = self.parent
        self._saved_grave_id = getattr(parent, 'grave_hotkey_id', None)
        self._saved_stop_id = getattr(parent, 'stop_replay_hotkey_id', None)
        self._saved_shortcuts = getattr(parent, 'registered_shortcuts', [])[:]
        
        # 1. 取消所有系统级钩子 (UnhookWindowsHookEx)
        try: _kb.unhook_all()
        except: pass
        # 短暂等待，确保钩子线程退出
        _time.sleep(0.05)
        
        # 2. 重置监听器状态，使其能被重新启动
        if hasattr(_kb, '_listener') and _kb._listener:
            _kb._listener.listening = False
            _kb._listener.handlers.clear()

    def _reenable_global_hooks(self):
        """重新注册所有键盘钩子 (会重启监听线程)"""
        parent = self.parent
        if hasattr(parent, 'reenable_grave_hotkey'):
            parent.reenable_grave_hotkey()
        if self._saved_stop_id and hasattr(parent, 'register_stop_replay_hotkey'):
            parent.register_stop_replay_hotkey()
        if self._saved_shortcuts and hasattr(parent, 'update_shortcuts'):
            parent.update_shortcuts()
        self._saved_grave_id = self._saved_stop_id = None
        self._saved_shortcuts = []

    def add_text_input(self):
        """添加文本输入操作"""
        try:
            # 先隐藏选择窗口，让用户能看到后面的界面
            self.hide()
            
            # 短暂延迟确保窗口完全隐藏
            import time
            time.sleep(0.2)
            
            # 获取用户输入的文本
            from PyQt5.QtWidgets import QInputDialog, QLineEdit, QPushButton
            from PyQt5.QtCore import Qt
            
            # 创建自定义输入对话框
            input_dialog = QInputDialog(self)
            input_dialog.setWindowTitle("输入文本")
            input_dialog.setLabelText("请输入要添加的文本内容:")
            input_dialog.setInputMode(QInputDialog.TextInput)
            
            # 获取输入框并启用清除按钮
            line_edit = input_dialog.findChild(QLineEdit)
            if line_edit:
                line_edit.setClearButtonEnabled(True)
            
            input_dialog.setOkButtonText("确定")
            input_dialog.setCancelButtonText("取消")
            
            # 停止焦点抢夺定时器，让输入法能正常工作
            if hasattr(self, 'focus_timer') and self.focus_timer:
                self.focus_timer.stop()
            
            if input_dialog.exec_() == QInputDialog.Accepted:
                text = input_dialog.textValue()
                ok = True
            else:
                text = ""
                ok = False
            
            # 重新启动焦点抢夺定时器
            if hasattr(self, 'focus_timer') and self.focus_timer:
                self.focus_timer.start(100)
            
            if ok and text:
                # 如果还没有录制目录，则创建它（用户实际执行了操作）
                if not self.recording_dir:
                    # 创建录制目录，按流程_时间戳格式命名
                    from utils import get_recordings_path
                    recordings_dir = get_recordings_path()
                    import os
                    os.makedirs(recordings_dir, exist_ok=True)
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    folder_name = f"流程_{timestamp}"
                    self.recording_dir = os.path.join(recordings_dir, folder_name)
                    os.makedirs(self.recording_dir, exist_ok=True)
                    
                    # 更新父对象的录制目录
                    if hasattr(self.parent, 'current_recording_dir'):
                        self.parent.current_recording_dir = self.recording_dir
                
                # 先保存当前屏幕状态作为操作图片（在增加计数之前，这样截图对应操作前的状态）
                try:
                    from utils import save_screenshot
                    import os
                    # 获取屏幕尺寸
                    screen = QGuiApplication.primaryScreen()
                    screen_size = screen.size()
                    # 构建文件路径（使用下一个操作序号）
                    next_step = self.operation_count + 1
                    file_path = os.path.join(self.recording_dir, f"操作{next_step}.png")
                    # 保存整个屏幕截图
                    save_path = save_screenshot((0, 0, screen_size.width(), screen_size.height()), file_path)
                    print(f"已保存文本输入操作截图: {save_path}")
                except Exception as e:
                    print(f"保存文本输入操作截图失败: {e}")
                
                # 增加操作计数
                self.operation_count += 1
                
                # 创建操作数据
                operation = {
                    'step': self.operation_count,
                    'action_type': 'text_input',
                    'text': text,
                    'delay': 0  # 默认无延迟
                }
                
                # 保存操作
                self.save_operation_to_json(operation)
                print(f"添加文本输入操作: '{text}'")
                
                # 执行文本输入 - 使用剪贴板方式支持中文
                import pyperclip
                import pyautogui
                
                # 将文本复制到剪贴板
                pyperclip.copy(text)
                
                # 使用Ctrl+V粘贴文本
                pyautogui.hotkey('ctrl', 'v')
                print(f"执行文本输入(通过剪贴板): '{text}'")
                
                # 短暂延迟等待文本输入完成
                time.sleep(0.5)
                
                # 重新截取屏幕作为新的选择图层
                self.start_new_selection()
            else:
                # 如果用户取消了输入，重新显示选择窗口
                self.show()
                self.raise_()
                self.activateWindow()
                
                # 强制设置焦点，确保键盘事件能被捕获
                self.setFocus(Qt.ActiveWindowFocusReason)
                
        except Exception as e:
            print(f"添加文本输入失败: {e}")
            # 确保在出错时也重新显示窗口
            try:
                self.show()
                self.raise_()
                self.activateWindow()
                
                # 强制设置焦点，确保键盘事件能被捕获
                self.setFocus(Qt.ActiveWindowFocusReason)
            except:
                pass

    def add_keyboard_shortcut(self, key_str):
        """添加键盘快捷键操作"""
        try:
            # 确保有录制目录
            if not self.recording_dir:
                print("[DEBUG] 没有录制目录，无法添加键盘操作")
                return
                
            # 创建操作数据
            operation = {
                "action_type": "keyboard",
                "key": key_str,
                "delay": 0.2
            }
            
            # 保存操作
            self.save_operation_to_json(operation)
            print(f"✅ 已录制快捷键: {key_str}")
            
            # 短暂延迟后重新开始选择
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(200, self.start_new_selection)
            
        except Exception as e:
            print(f"添加键盘快捷键操作失败: {e}")
            import traceback
            traceback.print_exc()
    
    def add_keyboard_input(self):
        """添加按键操作"""
        try:
            # 先隐藏选择窗口，让用户能看到后面的界面
            self.hide()
            
            # 短暂延迟确保窗口完全隐藏
            import time
            time.sleep(0.2)
            
            # 创建自定义输入对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
            from PyQt5.QtCore import Qt, pyqtSignal
            
            class KeyInputDialog(QDialog):
                key_pressed = pyqtSignal(str)
                
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("输入按键或滚动滚轮")
                    self.setModal(True)
                    
                    # 设置窗口标志：Dialog 才能正确模态 + 置顶
                    self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
                    self.setAttribute(Qt.WA_TranslucentBackground)
                    
                    # 应用统一的对话框样式
                    from styles import apply_dialog_style
                    apply_dialog_style(self, 0.3, 0.2)
                    
                    layout = QVBoxLayout()
                    
                    label = QLabel("请按下要添加的按键(支持组合键)\n或者直接滚动鼠标滚轮记录滚动操作:")
                    layout.addWidget(label)
                    
                    self.line_edit = QLineEdit()
                    self.line_edit.setClearButtonEnabled(True)
                    self.line_edit.setReadOnly(True)
                    layout.addWidget(self.line_edit)
                    
                    button_layout = QHBoxLayout()
                    
                    self.ok_btn = QPushButton("确定")
                    self.ok_btn.setFocusPolicy(Qt.StrongFocus)
                    self.ok_btn.setDefault(True)
                    self.ok_btn.clicked.connect(self.accept)
                    self.ok_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {PRIMARY_GRADIENT};
                            color: white;
                            border: none;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: bold;
                            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                        }}
                        QPushButton:hover {{
                            background-color: #007AFF;
                        }}
                        QPushButton:pressed {{
                            background-color: #007AFF;
                        }}
                    """)
                    button_layout.addWidget(self.ok_btn)

                    self.cancel_btn = QPushButton("取消")
                    self.cancel_btn.setFocusPolicy(Qt.StrongFocus)
                    self.cancel_btn.clicked.connect(self.reject)
                    self.cancel_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: #FFFFFF;
                            color: #8E8E93;
                            border: 1px solid #D1D1D6;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                        }}
                        QPushButton:hover {{
                            background-color: #F0F0F2;
                            color: #6E6E73;
                        }}
                    """)
                    button_layout.addWidget(self.cancel_btn)
                    
                    layout.addLayout(button_layout)
                    self.setLayout(layout)
                    
                    self.current_keys = []
                    self.key_map = {
                        Qt.Key_Return: 'enter',
                        Qt.Key_Enter: 'enter',
                        Qt.Key_Escape: 'esc',
                        Qt.Key_Tab: 'tab',
                        Qt.Key_Backspace: 'backspace',
                        Qt.Key_Delete: 'delete',
                        Qt.Key_Space: 'space',
                        Qt.Key_Up: 'up',
                        Qt.Key_Down: 'down',
                        Qt.Key_Left: 'left',
                        Qt.Key_Right: 'right',
                        Qt.Key_F1: 'f1',
                        Qt.Key_F2: 'f2',
                        Qt.Key_F3: 'f3',
                        Qt.Key_F4: 'f4',
                        Qt.Key_F5: 'f5',
                        Qt.Key_F6: 'f6',
                        Qt.Key_F7: 'f7',
                        Qt.Key_F8: 'f8',
                        Qt.Key_F9: 'f9',
                        Qt.Key_F10: 'f10',
                        Qt.Key_F11: 'f11',
                        Qt.Key_F12: 'f12',
                    }
                    
                    # 用于标识是否是滚动操作
                    self.is_scroll = False
                    self.scroll_amount = 0
                    
                def showEvent(self, event):
                    """重写showEvent，确保对话框显示时立即获取焦点"""
                    super().showEvent(event)
                    # 强制获取焦点
                    self.activateWindow()
                    self.raise_()
                    self.setFocus()
                    
                def wheelEvent(self, event):
                    """处理滚轮事件，记录滚动操作"""
                    # 获取滚动量（正数向上，负数向下）
                    delta = event.angleDelta().y()
                    if delta > 0:
                        self.scroll_amount = 3  # 向上滚动3格
                        self.line_edit.setText("🔄 向上滚动")
                    else:
                        self.scroll_amount = -3  # 向下滚动3格
                        self.line_edit.setText("🔄 向下滚动")
                    self.is_scroll = True
                    # 滚轮操作已记录，自动确认关闭对话框
                    self.accept()
                    event.accept()
                    
                def keyPressEvent(self, event):
                    key = event.key()
                    
                    # 处理Enter键：如果有文本就直接确认，否则填入'enter'并确认
                    if key in [Qt.Key_Return, Qt.Key_Enter]:
                        if self.line_edit.text():
                            # 已经有文本，直接确认
                            self.accept()
                            event.accept()
                            return
                        else:
                            # 没有文本，填入'enter'后自动确认
                            self.line_edit.setText('enter')
                            self.is_scroll = False
                            self.accept()
                            event.accept()
                            return
                    
                    # 处理修饰键
                    if key in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]:
                        return
                    
                    # 获取按键名称
                    self.is_scroll = False
                    if key in self.key_map:
                        key_name = self.key_map[key]
                    else:
                        # 直接从按键码获取字符，不依赖event.text()
                        if key >= Qt.Key_A and key <= Qt.Key_Z:
                            key_name = chr(key + 32)  # 转换为小写
                        elif key >= Qt.Key_0 and key <= Qt.Key_9:
                            key_name = chr(key)
                        else:
                            key_name = event.text() or ''
                            if not key_name:
                                return
                    
                    # 处理组合键
                    modifiers = []
                    if event.modifiers() & Qt.ControlModifier:
                        modifiers.append('ctrl')
                    if event.modifiers() & Qt.ShiftModifier:
                        modifiers.append('shift')
                    if event.modifiers() & Qt.AltModifier:
                        modifiers.append('alt')
                    if event.modifiers() & Qt.MetaModifier:
                        modifiers.append('meta')
                    
                    if modifiers:
                        key_str = '+'.join(modifiers + [key_name])
                    else:
                        key_str = key_name
                    
                    self.line_edit.setText(key_str)
                    
                    # 按键已设置，自动确认关闭对话框，无需用户再点击"确定"按钮
                    self.accept()
                    event.accept()
                    return
                    
            input_dialog = KeyInputDialog(self)
            
            # 停止焦点抢夺定时器，让按键输入对话框不被打扰
            if hasattr(self, 'focus_timer') and self.focus_timer:
                self.focus_timer.stop()
            
            if input_dialog.exec_() == QDialog.Accepted:
                # 检查是否是滚动操作
                if input_dialog.is_scroll:
                    # 处理滚动操作
                    scroll_amount = input_dialog.scroll_amount
                    ok = True
                    key = ""
                else:
                    key = input_dialog.line_edit.text()
                    ok = True
            else:
                key = ""
                ok = False
            
            # 重新启动焦点抢夺定时器
            if hasattr(self, 'focus_timer') and self.focus_timer:
                self.focus_timer.start(100)
            
            if ok:
                # 如果还没有录制目录，则创建它（用户实际执行了操作）
                if not self.recording_dir:
                    from utils import get_recordings_path
                    recordings_dir = get_recordings_path()
                    import os
                    os.makedirs(recordings_dir, exist_ok=True)
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    folder_name = f"流程_{timestamp}"
                    self.recording_dir = os.path.join(recordings_dir, folder_name)
                    os.makedirs(self.recording_dir, exist_ok=True)
                    if hasattr(self.parent, 'current_recording_dir'):
                        self.parent.current_recording_dir = self.recording_dir
                
                # 保存当前屏幕状态作为操作图片
                try:
                    from utils import save_screenshot
                    import os
                    screen = QGuiApplication.primaryScreen()
                    screen_size = screen.size()
                    next_step = self.operation_count + 1
                    file_path = os.path.join(self.recording_dir, f"操作{next_step}.png")
                    save_path = save_screenshot((0, 0, screen_size.width(), screen_size.height()), file_path)
                    if input_dialog.is_scroll:
                        print(f"已保存滚动操作截图: {save_path}")
                    else:
                        print(f"已保存按键操作截图: {save_path}")
                except Exception as e:
                    print(f"保存操作截图失败: {e}")
                
                # 增加操作计数
                self.operation_count += 1
                
                # 创建操作数据
                if input_dialog.is_scroll:
                    operation = {
                        'step': self.operation_count,
                        'action_type': 'scroll',
                        'scroll_amount': scroll_amount,
                        'delay': 0
                    }
                    self.save_operation_to_json(operation)
                    print(f"添加滚动操作: {'向上' if scroll_amount > 0 else '向下'} {abs(scroll_amount)} 格")
                    
                    # 执行滚动操作
                    import pyautogui
                    pyautogui.scroll(scroll_amount)
                    print(f"执行滚动操作: {'向上' if scroll_amount > 0 else '向下'} {abs(scroll_amount)} 格")
                else:
                    operation = {
                        'step': self.operation_count,
                        'action_type': 'keyboard',
                        'key': key,
                        'delay': 0
                    }
                    self.save_operation_to_json(operation)
                    print(f"添加按键操作: '{key}'")
                    
                    # 执行按键操作
                    import pyautogui
                    pyautogui.hotkey(*key.split('+'))
                    print(f"执行按键操作: '{key}'")
                
                time.sleep(0.5)
                self.start_new_selection()
            else:
                # 如果用户取消了输入，重新显示选择窗口
                self.show()
                self.raise_()
                self.activateWindow()
                
                # 强制设置焦点，确保键盘事件能被捕获
                self.setFocus(Qt.ActiveWindowFocusReason)
                
        except Exception as e:
            print(f"添加按键操作失败: {e}")
            # 确保在出错时也重新显示窗口
            try:
                self.show()
                self.raise_()
                self.activateWindow()
                
                # 强制设置焦点，确保键盘事件能被捕获
                self.setFocus(Qt.ActiveWindowFocusReason)
            except:
                pass
    
    def start_new_selection(self):
        """开始新的选择流程，重新截取屏幕"""
        try:
            # 重新截取屏幕
            screen = QGuiApplication.primaryScreen()
            self.screen_pixmap = screen.grabWindow(0)
            
            # 获取设备像素比
            device_pixel_ratio = screen.devicePixelRatio()
            
            # 设置窗口大小为屏幕逻辑尺寸（考虑DPI缩放）
            # grabWindow 返回的是物理像素尺寸，需要转换为逻辑尺寸
            logical_width = int(self.screen_pixmap.width() / device_pixel_ratio)
            logical_height = int(self.screen_pixmap.height() / device_pixel_ratio)
            self.resize(logical_width, logical_height)
            
            print(f"重新截图: 物理尺寸={self.screen_pixmap.width()}x{self.screen_pixmap.height()}, "
                  f"逻辑尺寸={logical_width}x{logical_height}, DPI缩放={device_pixel_ratio}")
            
            # 重置选择区域
            self.selection_start = None
            self.selection_end = None
            self.selecting = False
            self.right_click_pressed = False
            self.right_click_dragged = False
            
            # 确保窗口显示
            self.show()
            
            # 确保窗口置顶并获取焦点
            self.raise_()
            self.activateWindow()
            
            # 强制设置焦点，确保键盘事件能被捕获
            self.setFocus(Qt.ActiveWindowFocusReason)
            
            # 强制重绘窗口，确保显示最新的屏幕内容
            self.update()
            
            print("已重新截取屏幕并开始新的选择流程")
            
        except Exception as e:
            print(f"开始新选择流程失败: {e}")
            # 确保在出错时也保持窗口焦点
            try:
                self.show()
                self.raise_()
                self.activateWindow()
                
                # 强制设置焦点，确保键盘事件能被捕获
                self.setFocus(Qt.ActiveWindowFocusReason)
            except:
                pass
    
    def continue_selection(self):
        """继续选择下一个区域"""
        # 重置选择区域
        self.selection_start = None
        self.selection_end = None
        
        # 不再重新截取屏幕，因为click_selection_center方法已经获取了点击后的屏幕状态
        # 直接使用当前的self.screen_pixmap，它已经是操作执行后的屏幕状态
        
        # 确保窗口大小与最新的屏幕截图匹配
        if self.screen_pixmap:
            self.resize(self.screen_pixmap.size())
        
        # 确保窗口置顶并获取焦点，让用户继续选择
        self.raise_()
        self.activateWindow()
        
        # 强制设置焦点，确保键盘事件能被捕获
        self.setFocus(Qt.ActiveWindowFocusReason)
        
        # 强制重绘窗口，确保显示最新的屏幕内容
        self.update()
        
        # 直接继续选择，不询问用户
        # 用户可以通过按ESC键来结束选择过程
    
    def show_screenshot_dialog(self, pixmap):
        """显示截图对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("截图")
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(dialog)
        
        # 显示截图
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)
        
        # 按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # 连接信号
        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 保存截图
            filename = f"screenshot_{int(time.time())}.png"
            filepath = os.path.join(self.recording_dir or ".", filename)
            pixmap.save(filepath)
            StyledMessageDialog(self, title="成功", text=f"截图已保存到: {filepath}", msg_type="information", buttons="ok").exec_()
        
        self.close()
    
    def save_condition_step(self, condition_type, image_path, action_data, image_index):
        """保存条件步骤"""
        try:
            recording_json_path = os.path.join(self.recording_dir, 'recording.json')
            
            # 加载现有数据
            if os.path.exists(recording_json_path):
                operations = json.load(open(recording_json_path, 'r', encoding='utf-8'))
            else:
                operations = []
            
            # 添加条件步骤
            condition_step = {
                'step': image_index + 1,
                'type': 'condition',
                'condition_type': condition_type,
                'image_path': image_path,
                'action_data': action_data
            }
            operations.insert(image_index, condition_step)
            
            # 保存到文件
            with open(recording_json_path, 'w', encoding='utf-8') as f:
                json.dump(operations, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存条件步骤失败: {e}")
    
    def add_operation_sequence(self):
        """添加操作序列"""
        try:
            # 创建操作序列对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QRadioButton, QCheckBox, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QSpinBox, QTabWidget, QWidget, QComboBox, QGroupBox
            from PyQt5.QtCore import Qt
            
            dialog = QDialog(self)
            dialog.setWindowTitle("添加操作序列")
            dialog.setModal(True)
            dialog.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # 创建选项卡
            tab_widget = QTabWidget()
            
            # 第一个选项卡：预定义序列
            predefined_tab = QWidget()
            predefined_layout = QVBoxLayout(predefined_tab)
            
            # 预定义序列列表
            predefined_list = QListWidget()
            
            # 添加预定义序列
            predefined_sequences = [
                {
                    "name": "登录流程",
                    "description": "用户名输入 -> Tab键 -> 密码输入 -> 回车键",
                    "operations": [
                        {"action_type": "text_input", "text": "用户名", "delay": 0.5},
                        {"action_type": "keyboard", "key": "tab", "delay": 0.2},
                        {"action_type": "text_input", "text": "密码", "delay": 0.5},
                        {"action_type": "keyboard", "key": "enter", "delay": 1.0}
                    ]
                },
                {
                    "name": "复制粘贴",
                    "description": "Ctrl+A全选 -> Ctrl+C复制 -> 点击目标位置 -> Ctrl+V粘贴",
                    "operations": [
                        {"action_type": "keyboard", "key": "ctrl+a", "delay": 0.2},
                        {"action_type": "keyboard", "key": "ctrl+c", "delay": 0.5},
                        {"action_type": "left_click", "delay": 0.5},
                        {"action_type": "keyboard", "key": "ctrl+v", "delay": 0.5}
                    ]
                },
                {
                    "name": "新建文件",
                    "description": "右键点击 -> 新建 -> 文件夹 -> 输入名称 -> 回车",
                    "operations": [
                        {"action_type": "right_click", "delay": 0.5},
                        {"action_type": "keyboard", "key": "down", "delay": 0.2},
                        {"action_type": "keyboard", "key": "down", "delay": 0.2},
                        {"action_type": "keyboard", "key": "enter", "delay": 0.5},
                        {"action_type": "text_input", "text": "新文件夹", "delay": 0.5},
                        {"action_type": "keyboard", "key": "enter", "delay": 0.5}
                    ]
                },
                {
                    "name": "截图保存",
                    "description": "Win+Shift+S截图 -> Ctrl+S保存 -> 输入文件名 -> 回车",
                    "operations": [
                        {"action_type": "keyboard", "key": "win+shift+s", "delay": 1.0},
                        {"action_type": "keyboard", "key": "ctrl+s", "delay": 0.5},
                        {"action_type": "text_input", "text": "截图", "delay": 0.5},
                        {"action_type": "keyboard", "key": "enter", "delay": 0.5}
                    ]
                }
            ]
            
            for seq in predefined_sequences:
                item = QListWidgetItem(f"{seq['name']}: {seq['description']}")
                item.setData(Qt.UserRole, seq)
                predefined_list.addItem(item)
            
            predefined_layout.addWidget(predefined_list)
            tab_widget.addTab(predefined_tab, "预定义序列")
            
            # 第二个选项卡：自定义序列
            custom_tab = QWidget()
            custom_layout = QVBoxLayout(custom_tab)
            
            # 操作序列列表
            operations_list = QListWidget()
            operations_list.setMaximumHeight(200)
            
            # 添加操作按钮组
            add_buttons_layout = QHBoxLayout()
            
            # 添加点击操作按钮
            add_click_btn = QPushButton("添加点击")
            add_click_btn.clicked.connect(lambda: self.add_operation_to_list(operations_list, "click"))
            
            # 添加文本输入按钮
            add_text_btn = QPushButton("添加文本")
            add_text_btn.clicked.connect(lambda: self.add_operation_to_list(operations_list, "text"))
            
            # 添加延迟按钮
            add_delay_btn = QPushButton("添加延迟")
            add_delay_btn.clicked.connect(lambda: self.add_operation_to_list(operations_list, "delay"))
            
            add_buttons_layout.addWidget(add_click_btn)
            add_buttons_layout.addWidget(add_text_btn)
            add_buttons_layout.addWidget(add_delay_btn)
            
            # 操作编辑区域
            edit_group = QGroupBox("操作详情")
            edit_layout = QVBoxLayout(edit_group)
            
            # 操作类型
            type_layout = QHBoxLayout()
            type_label = QLabel("操作类型:")
            type_combo = QPushButton("左键点击")
            type_combo.setCursor(Qt.PointingHandCursor)
            type_combo.currentText = lambda: type_combo.text()
            type_combo.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #1D1D1F;
                    border: 1px solid #D1D1D6;
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-size: 13px;
                    font-weight: 500;
                    text-align: left;
                    min-width: 100px;
                }
                QPushButton:hover {
                    border-color: #007AFF;
                }
                QPushButton::menu-indicator {
                    image: none;
                    width: 8px;
                    subcontrol-position: right center;
                    subcontrol-origin: padding;
                    padding-right: 10px;
                }
            """)
            self._type_menu = QMenu(type_combo)
            self._type_menu.setStyleSheet("""
                QMenu {
                    background-color: #FFFFFF;
                    border: 1px solid #E8E8ED;
                    border-radius: 10px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 8px 18px;
                    border-radius: 6px;
                    min-height: 22px;
                    font-size: 13px;
                }
                QMenu::item:selected {
                    background-color: #007AFF;
                    color: white;
                }
            """)
            for t in ["左键点击", "右键点击", "双击", "中键点击", "文本输入", "延迟"]:
                self._type_menu.addAction(t)
            self._type_menu.triggered.connect(lambda action: type_combo.setText(action.text()))
            type_combo.setMenu(self._type_menu)
            type_layout.addWidget(type_label)
            type_layout.addWidget(type_combo)
            edit_layout.addLayout(type_layout)
            
            # 操作参数
            param_layout = QHBoxLayout()
            param_label = QLabel("参数:")
            param_edit = QLineEdit()
            param_layout.addWidget(param_label)
            param_layout.addWidget(param_edit)
            edit_layout.addLayout(param_layout)
            
            # 延迟时间
            delay_layout = QHBoxLayout()
            delay_label = QLabel("延迟(秒):")
            delay_spin = QDoubleSpinBox()
            delay_spin.setRange(0, 60)
            delay_spin.setSingleStep(0.1)
            delay_spin.setDecimals(1)
            delay_spin.setValue(0.5)
            delay_layout.addWidget(delay_label)
            delay_layout.addWidget(delay_spin)
            edit_layout.addLayout(delay_layout)
            
            # 操作序列操作按钮
            seq_buttons_layout = QHBoxLayout()
            
            # 更新操作按钮
            update_btn = QPushButton("更新操作")
            update_btn.clicked.connect(lambda: self.update_operation_in_list(operations_list, type_combo, param_edit, delay_spin))
            
            # 删除操作按钮
            delete_btn = QPushButton("删除操作")
            delete_btn.clicked.connect(lambda: self.delete_operation_from_list(operations_list))
            
            # 上移操作按钮
            move_up_btn = QPushButton("上移")
            move_up_btn.clicked.connect(lambda: self.move_operation_up(operations_list))
            
            # 下移操作按钮
            move_down_btn = QPushButton("下移")
            move_down_btn.clicked.connect(lambda: self.move_operation_down(operations_list))
            
            seq_buttons_layout.addWidget(update_btn)
            seq_buttons_layout.addWidget(delete_btn)
            seq_buttons_layout.addWidget(move_up_btn)
            seq_buttons_layout.addWidget(move_down_btn)
            
            custom_layout.addWidget(QLabel("操作序列:"))
            custom_layout.addWidget(operations_list)
            custom_layout.addLayout(add_buttons_layout)
            custom_layout.addWidget(edit_group)
            custom_layout.addLayout(seq_buttons_layout)
            
            tab_widget.addTab(custom_tab, "自定义序列")
            
            layout.addWidget(tab_widget)
            
            # 对话框按钮
            button_layout = QHBoxLayout()
            
            # 保存按钮
            save_btn = QPushButton("保存序列")
            
            def save_sequence():
                current_tab = tab_widget.currentIndex()
                
                if current_tab == 0:  # 预定义序列
                    selected_item = predefined_list.currentItem()
                    if selected_item:
                        sequence = selected_item.data(Qt.UserRole)
                        self.save_operation_sequence(sequence)
                        dialog.accept()
                else:  # 自定义序列
                    operations = []
                    for i in range(operations_list.count()):
                        item = operations_list.item(i)
                        operations.append(item.data(Qt.UserRole))
                    
                    if operations:
                        sequence = {
                            "name": "自定义序列",
                            "description": f"包含{len(operations)}个操作",
                            "operations": operations
                        }
                        self.save_operation_sequence(sequence)
                        dialog.accept()
                    else:
                        StyledMessageDialog(dialog, title="警告", text="请至少添加一个操作", msg_type="warning", buttons="ok").exec_()
            
            save_btn.clicked.connect(save_sequence)
            
            # 取消按钮
            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(save_btn)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # 显示对话框
            dialog.exec_()
            
        except Exception as e:
            print(f"添加操作序列失败: {e}")
            StyledMessageDialog(self, title="错误", text=f"添加操作序列失败: {str(e)}", msg_type="critical", buttons="ok").exec_()
    
    def add_operation_to_list(self, operations_list, operation_type):
        """添加操作到列表"""
        from PyQt5.QtWidgets import QListWidgetItem
        from PyQt5.QtCore import Qt
        
        if operation_type == "click":
            operation = {
                "action_type": "left_click",
                "delay": 0.5
            }
            item = QListWidgetItem("左键点击")
        elif operation_type == "text":
            # 获取文本输入
            from PyQt5.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, "输入文本", "请输入要输入的文本:")
            if ok and text:
                operation = {
                    "action_type": "text_input",
                    "text": text,
                    "delay": 0.5
                }
                item = QListWidgetItem(f"文本输入: '{text}'")
            else:
                return
        elif operation_type == "delay":
            # 获取延迟时间
            from PyQt5.QtWidgets import QInputDialog
            delay, ok = QInputDialog.getDouble(self, "设置延迟", "请输入延迟时间(秒):", 0.5, 0, 60, 1)
            if ok:
                operation = {
                    "action_type": "delay",
                    "delay": delay
                }
                item = QListWidgetItem(f"延迟: {delay}秒")
            else:
                return
        else:
            return
        
        item.setData(Qt.UserRole, operation)
        operations_list.addItem(item)
        operations_list.setCurrentItem(item)
    
    def update_operation_in_list(self, operations_list, type_combo, param_edit, delay_spin):
        """更新列表中的操作"""
        from PyQt5.QtCore import Qt
        
        current_item = operations_list.currentItem()
        if not current_item:
            return
        
        # 获取操作类型
        type_text = type_combo.currentText()
        param_text = param_edit.text()
        delay = delay_spin.value()
        
        # 根据类型创建操作
        if type_text == "左键点击":
            operation = {
                "action_type": "left_click",
                "delay": delay
            }
            item_text = "左键点击"
        elif type_text == "右键点击":
            operation = {
                "action_type": "right_click",
                "delay": delay
            }
            item_text = "右键点击"
        elif type_text == "双击":
            operation = {
                "action_type": "double_click",
                "delay": delay
            }
            item_text = "双击"
        elif type_text == "中键点击":
            operation = {
                "action_type": "middle_click",
                "delay": delay
            }
            item_text = "中键点击"
        elif type_text == "文本输入":
            operation = {
                "action_type": "text_input",
                "text": param_text,
                "delay": delay
            }
            item_text = f"文本输入: '{param_text}'"
        elif type_text == "键盘操作":
            operation = {
                "action_type": "keyboard",
                "key": param_text,
                "delay": delay
            }
            item_text = f"键盘操作: '{param_text}'"
        elif type_text == "延迟":
            operation = {
                "action_type": "delay",
                "delay": delay
            }
            item_text = f"延迟: {delay}秒"
        else:
            return
        
        # 更新项目
        current_item.setText(item_text)
        current_item.setData(Qt.UserRole, operation)
    
    def delete_operation_from_list(self, operations_list):
        """从列表中删除操作"""
        current_row = operations_list.currentRow()
        if current_row >= 0:
            operations_list.takeItem(current_row)
    
    def move_operation_up(self, operations_list):
        """上移操作"""
        current_row = operations_list.currentRow()
        if current_row > 0:
            item = operations_list.takeItem(current_row)
            operations_list.insertItem(current_row - 1, item)
            operations_list.setCurrentRow(current_row - 1)
    
    def move_operation_down(self, operations_list):
        """下移操作"""
        current_row = operations_list.currentRow()
        if current_row >= 0 and current_row < operations_list.count() - 1:
            item = operations_list.takeItem(current_row)
            operations_list.insertItem(current_row + 1, item)
            operations_list.setCurrentRow(current_row + 1)
    
    def save_operation_sequence(self, sequence):
        """保存操作序列"""
        try:
            # 如果还没有录制目录，则创建它（用户实际执行了操作）
            if not self.recording_dir:
                # 创建录制目录，按流程_时间戳格式命名
                from utils import get_recordings_path
                recordings_dir = get_recordings_path()
                import os
                os.makedirs(recordings_dir, exist_ok=True)
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                folder_name = f"流程_{timestamp}"
                self.recording_dir = os.path.join(recordings_dir, folder_name)
                os.makedirs(self.recording_dir, exist_ok=True)
                
                # 更新父对象的录制目录
                if hasattr(self.parent, 'current_recording_dir'):
                    self.parent.current_recording_dir = self.recording_dir
            
            operations = sequence.get("operations", [])
            for operation in operations:
                # 增加操作计数
                self.operation_count += 1
                
                # 添加步骤编号
                operation["step"] = self.operation_count
                
                # 保存操作
                self.save_operation_to_json(operation)
            
            print(f"添加操作序列: {sequence['name']}")
            
        except Exception as e:
            print(f"保存操作序列失败: {e}")
            StyledMessageDialog(self, title="错误", text=f"保存操作序列失败: {str(e)}", msg_type="critical", buttons="ok").exec_()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self._stop_win_hook()
        
        # 停止焦点检查定时器
        if hasattr(self, 'focus_timer'):
            if self.focus_timer.isActive():
                self.focus_timer.stop()
            self.focus_timer.deleteLater()
            self.focus_timer = None
        
        # 清理屏幕截图 pixmap
        if self.screen_pixmap:
            self.screen_pixmap = None
        
        # 清理父窗口引用
        self.parent = None
        
        # 触发关闭信号
        self.closed.emit()
        
        # 调用父类的关闭事件
        super().closeEvent(event)
        
        # 强制垃圾回收
        import gc
        gc.collect()