"""测试脚本：模拟打开流程文件夹"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QDialog, QScrollArea, QMainWindow
from PyQt5.QtCore import Qt

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = QApplication(sys.argv)

# 创建一个mock主窗口
class MockParent(QMainWindow):
    def _get_usage_counts(self):
        return {}
    def show_beautiful_message(self, *a, **kw):
        print(f"show_beautiful_message: {a}")
    def temporarily_disable_grave_hotkey(self):
        pass
    def reenable_grave_hotkey(self):
        pass
    @property
    def shortcuts(self):
        return {}

mw = MockParent()
mw.hide()

# 创建FolderManager
from app import FolderManager
fm = FolderManager(mw)
fm.hide()

# 测试打开一个文件夹
test_folder = r"D:\codespace\01-开发项目\PC-action\PC-action-macOS\recordings\一个个领取"
print(f"测试打开文件夹: {test_folder}")
print(f"文件夹存在: {os.path.isdir(test_folder)}")

# 调用view_images
try:
    fm.view_images(test_folder)
    print("view_images 调用成功!")
except Exception as e:
    import traceback
    print(f"view_images 调用失败: {e}")
    traceback.print_exc()

print("\n测试完成!")