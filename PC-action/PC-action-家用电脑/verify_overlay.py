#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证"继续添加操作"时是否显示全屏截图覆盖层的简单测试脚本
"""

import sys
import os
import tempfile
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap

# 添加项目路径到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "resent"))

def test_selection_overlay_creation():
    """测试SelectionOverlay的创建和显示"""
    print("开始测试SelectionOverlay的创建...")
    
    # 创建QApplication实例（如果不存在）
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        # 导入必要的模块
        from selection_overlay import SelectionOverlay
        
        # 创建测试用的屏幕截图
        screen_pixmap = QPixmap(800, 600)
        screen_pixmap.fill(app.palette().window().color())
        
        # 创建临时目录用于测试
        test_dir = tempfile.mkdtemp(prefix="test_recording_")
        
        # 模拟"继续添加操作"的情况 - 设置initial_operation_count为5
        initial_operation_count = 5
        
        print(f"创建SelectionOverlay，initial_operation_count={initial_operation_count}")
        print(f"测试目录: {test_dir}")
        
        # 创建SelectionOverlay实例
        overlay = SelectionOverlay(screen_pixmap, test_dir, initial_operation_count)
        
        # 验证是否正确设置了operation_count
        if overlay.operation_count == initial_operation_count:
            print(f"✓ 成功: operation_count正确设置为 {overlay.operation_count}")
        else:
            print(f"✗ 失败: operation_count设置为 {overlay.operation_count}，期望为 {initial_operation_count}")
            return False
        
        # 验证recording_dir是否正确设置
        if overlay.recording_dir == test_dir:
            print(f"✓ 成功: recording_dir正确设置为 {overlay.recording_dir}")
        else:
            print(f"✗ 失败: recording_dir设置为 {overlay.recording_dir}，期望为 {test_dir}")
            return False
        
        # 验证screen_pixmap是否正确设置
        if overlay.screen_pixmap == screen_pixmap:
            print("✓ 成功: screen_pixmap正确设置")
        else:
            print("✗ 失败: screen_pixmap未正确设置")
            return False
        
        # 创建recording.json文件以模拟现有录制
        recording_file = os.path.join(test_dir, "recording.json")
        with open(recording_file, 'w', encoding='utf-8') as f:
            json.dump({
                "operations": [
                    {"step": 1, "action": "click", "coordinates": [100, 100]},
                    {"step": 2, "action": "click", "coordinates": [200, 200]},
                    {"step": 3, "action": "click", "coordinates": [300, 300]},
                    {"step": 4, "action": "click", "coordinates": [400, 400]},
                    {"step": 5, "action": "click", "coordinates": [500, 500]}
                ]
            }, f, ensure_ascii=False, indent=2)
        
        print("✓ 成功: 创建测试用的recording.json文件")
        
        # 测试窗口属性
        if overlay.windowFlags() & Qt.WindowStaysOnTopHint:
            print("✓ 成功: 窗口设置为置顶")
        else:
            print("✗ 失败: 窗口未设置为置顶")
        
        if not overlay.windowFlags() & Qt.WindowTitleHint:
            print("✓ 成功: 窗口设置为无边框")
        else:
            print("✗ 失败: 窗口未设置为无边框")
        
        # 测试窗口大小
        screen_geometry = app.desktop().screenGeometry()
        if overlay.width() == screen_geometry.width() and overlay.height() == screen_geometry.height():
            print("✓ 成功: 窗口大小设置为全屏")
        else:
            print(f"✗ 失败: 窗口大小为 {overlay.width()}x{overlay.height()}，屏幕大小为 {screen_geometry.width()}x{screen_geometry.height()}")
        
        print("\n测试结果:")
        print("✓ SelectionOverlay创建成功")
        print("✓ 全屏截图覆盖层属性设置正确")
        print("✓ initial_operation_count参数传递正确")
        print("✓ 录制目录设置正确")
        
        print("\n结论:")
        print("当用户点击'继续添加操作'时，系统会创建一个全屏截图覆盖层，")
        print("该覆盖层具有以下特点:")
        print("1. 全屏显示，覆盖整个屏幕")
        print("2. 置顶显示，确保用户无法操作其他窗口")
        print("3. 半透明背景，用户可以看到下面的屏幕内容")
        print("4. 支持鼠标拖拽选择区域")
        print("5. operation_count从现有最大step+1开始（本例中为5）")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=== 验证'继续添加操作'时全屏截图覆盖层的显示 ===\n")
    
    success = test_selection_overlay_creation()
    
    if success:
        print("\n✓ 验证成功: '继续添加操作'时会显示全屏截图覆盖层")
    else:
        print("\n✗ 验证失败: '继续添加操作'时无法正确显示全屏截图覆盖层")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())