import os
import json
import re
import random
import string
import hashlib
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

# 样式可用标志
STYLES_AVAILABLE = True


def hash_password(password):
    """对密码进行哈希处理"""
    return hashlib.sha256(password.encode()).hexdigest()


def is_valid_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_random_username(length=8):
    """生成随机用户名"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def validate_password_requirements(password):
    """验证密码要求"""
    if len(password) < 6:
        return False, "密码长度至少6位"
    return True, "密码符合要求"


def apply_styles_to_dialog(dialog):
    """应用样式到对话框"""
    dialog.setStyleSheet(get_common_dialog_style())


def get_screen_size(scale=None):
    """获取屏幕尺寸"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    screen = QDesktopWidget().screenGeometry()
    width = screen.width()
    height = screen.height()
    if scale is not None:
        width = int(width * scale)
        height = int(height * scale)
    return width, height


def center_window(window):
    """将窗口居中显示"""
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())


def load_json_data(file_path, default=None):
    """加载JSON数据"""
    if default is None:
        default = {}
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载JSON数据失败: {e}")
    return default


def save_json_data(file_path, data):
    """保存JSON数据"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存JSON数据失败: {e}")
        return False


def load_qpixmap(image_path):
    """加载图片为QPixmap"""
    pixmap = QPixmap()
    if os.path.exists(image_path):
        pixmap.load(image_path)
    return pixmap


def load_qimage(image_path):
    """加载图片为QImage"""
    image = QImage()
    if os.path.exists(image_path):
        image.load(image_path)
    return image


def get_common_styles(screen_width=None, screen_height=None):
    """获取通用样式"""
    return """
        QPushButton {
            background-color: #1890ff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #40a9ff;
        }
        QPushButton:pressed {
            background-color: #096dd9;
        }
    """


def create_styled_button(text, color="#1890ff"):
    """创建样式化按钮"""
    return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: #40a9ff;
        }}
    """


def create_styled_input():
    """创建样式化输入框"""
    return """
        QLineEdit {
            border: 1px solid #d9d9d9;
            padding: 8px;
            border-radius: 4px;
        }
        QLineEdit:focus {
            border-color: #1890ff;
        }
    """


def get_common_dialog_style():
    """获取通用对话框样式"""
    return """
        QDialog {
            background-color: white;
        }
    """


def get_dynamic_radius(width, height):
    """获取动态圆角半径"""
    # 如果传入的是字符串，返回默认值
    if isinstance(width, str) or isinstance(height, str):
        return 8  # 默认圆角半径
    return min(width, height) // 20


def get_recordings_path():
    """获取录制文件夹路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    recordings_dir = os.path.normpath(os.path.join(
        base_dir, "recordings"
    ))
    if not os.path.exists(recordings_dir):
        os.makedirs(recordings_dir)
    return recordings_dir


def get_user_data_path():
    """获取用户数据文件夹路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.normpath(os.path.join(
        base_dir, "user_data"
    ))
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    return user_data_dir


def configure_window(window, width_ratio=0.5, height_ratio=0.6, center=True, modal=False, title=""):
    """
    统一配置窗口的大小、位置和样式
    
    Args:
        window: 窗口对象（QDialog/QWidget）
        width_ratio: 宽度占屏幕比例（默认0.5）
        height_ratio: 高度占屏幕比例（默认0.6）
        center: 是否居中显示（默认True）
        modal: 是否为模态对话框（默认False）
        title: 窗口标题（可选）
    """
    from PyQt5.QtCore import Qt
    
    # 设置窗口标题
    if title:
        window.setWindowTitle(title)
    
    # 计算窗口大小
    screen_width, screen_height = get_screen_size()
    window_width = int(screen_width * width_ratio)
    window_height = int(screen_height * height_ratio)
    
    # 设置窗口大小
    window.resize(window_width, window_height)
    
    # 设置窗口标志
    if isinstance(window, QDialog):
        # 对话框：移除帮助按钮，添加最小化和关闭按钮
        window.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        if modal:
            window.setModal(True)
    
    # 居中显示
    if center:
        center_window(window)
    
    return window


# 窗口尺寸配置常量
WINDOW_SIZES = {
    'main_control': (0.45, 0.7),      # 录制控制窗口
    'folder_manager': (0.45, 0.7),    # 管理录制窗口
    'view_images': (0.6, 0.6),        # 查看图片窗口
    'combo_skill_edit': (0.5, 0.55),  # 组合技编辑窗口
    'combo_skill_manager': (0.4, 0.5), # 组合技管理窗口
    'settings': (0.4, 0.5),           # 设置窗口
    'login': (0.35, 0.45),            # 登录窗口
}


def configure_window_by_type(window, window_type, title="", center=True, modal=False):
    """
    根据窗口类型统一配置
    
    Args:
        window: 窗口对象
        window_type: 窗口类型，必须是 WINDOW_SIZES 中的键
        title: 窗口标题
        center: 是否居中
        modal: 是否为模态
    """
    if window_type in WINDOW_SIZES:
        width_ratio, height_ratio = WINDOW_SIZES[window_type]
    else:
        width_ratio, height_ratio = 0.5, 0.6  # 默认大小
    
    return configure_window(window, width_ratio, height_ratio, center, modal, title)


def save_screenshot(region=None, file_path=None):
    """
    保存屏幕截图

    Args:
        region: 截图区域 (left, top, right, bottom)，为None则截取全屏
        file_path: 保存截图的文件路径，为None则自动生成

    Returns:
        str: 保存的文件路径，失败返回None
    """
    try:
        import datetime
        from PIL import Image

        # 使用 mss 截图
        import mss
        sct = mss.mss()
        if region:
            left, top, right, bottom = region
            monitor = {"left": left, "top": top, "width": right - left, "height": bottom - top}
        else:
            monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        if file_path is None:
            # 自动生成文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(get_recordings_path(), f"screenshot_{timestamp}.png")

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        image.save(file_path)
        return file_path
    except Exception as e:
        print(f"保存截图失败: {e}")
        return None
