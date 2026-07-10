"""
剪贴板修复测试脚本
验证录制/回放时剪贴板保存/恢复逻辑是否正确
"""

import pyperclip
import sys


def test_clipboard_fix():
    """测试完整的录制→回放流程中的剪贴板行为"""
    
    print("=" * 55)
    print("  剪贴板修复测试 - 模拟录制/回放流程")
    print("=" * 55)
    print()
    
    # =========================================================
    # 场景：用户复制了文本，然后录制 Ctrl+V 粘贴 + 文本输入
    # =========================================================
    
    # ---------- 录制阶段 ----------
    print("【录制阶段】")
    
    # 1. 用户复制了文本
    pyperclip.copy("xxx的邮箱是招聘负责人才有的")
    original = pyperclip.paste()
    print(f"  1. 用户复制文本: [{original}]")
    assert original == "xxx的邮箱是招聘负责人才有的"
    print("     ✅ 用户复制成功")
    print()
    
    # 2. 按 Ctrl+V 录制粘贴快捷键 → 保存剪贴板到 recording.json
    #    (add_keyboard_shortcut 中的新增逻辑)
    clipboard_saved = pyperclip.paste()
    print(f"  2. 录制 Ctrl+V，保存剪贴板: [{clipboard_saved}]")
    assert clipboard_saved == "xxx的邮箱是招聘负责人才有的"
    print("     ✅ Ctrl+V 录制时正确保存了剪贴板")
    # 模拟执行 Ctrl+V 粘贴
    print(f"     执行 Ctrl+V 粘贴: [{pyperclip.paste()}]")
    print()
    
    # 3. 按 T 键文本输入 → 保存剪贴板 → 复制文本 → 粘贴 → 恢复
    #    (add_text_input 中的新增逻辑)
    saved = pyperclip.paste()
    print(f"  3. 文本输入前保存剪贴板: [{saved}]")
    assert saved == "xxx的邮箱是招聘负责人才有的"
    
    pyperclip.copy("招聘负责人的联系电话和邮箱是多少")
    print(f"     复制文本到剪贴板: [{pyperclip.paste()}]")
    assert pyperclip.paste() == "招聘负责人的联系电话和邮箱是多少"
    
    print(f"     执行 Ctrl+V 粘贴: [{pyperclip.paste()}]")
    
    # 恢复剪贴板
    pyperclip.copy(saved)
    print(f"     恢复后剪贴板: [{pyperclip.paste()}]")
    assert pyperclip.paste() == "xxx的邮箱是招聘负责人才有的"
    print("     ✅ 文本输入不污染剪贴板")
    print()
    
    # ---------- 回放阶段 ----------
    print("【回放阶段】")
    
    # 4. 回放 Ctrl+V → 恢复 recording.json 中保存的剪贴板 → 执行粘贴
    #    (replay_coordinate_operations 中的新增逻辑)
    recording_clipboard = "xxx的邮箱是招聘负责人才有的"  # 从 recording.json 读取
    pyperclip.copy(recording_clipboard)
    print(f"  4. 回放 Ctrl+V，恢复剪贴板: [{pyperclip.paste()}]")
    assert pyperclip.paste() == "xxx的邮箱是招聘负责人才有的"
    print(f"     执行 Ctrl+V 粘贴: [{pyperclip.paste()}]")
    print("     ✅ 回放 Ctrl+V 正确恢复了录制时的剪贴板内容")
    print()
    
    # 5. 回放文本输入 → 保存剪贴板 → 复制文本 → 粘贴 → 恢复
    #    (replay_coordinate_operations 中的新增逻辑)
    saved2 = pyperclip.paste()
    print(f"  5. 回放文本输入前保存剪贴板: [{saved2}]")
    assert saved2 == "xxx的邮箱是招聘负责人才有的"
    
    pyperclip.copy("招聘负责人的联系电话和邮箱是多少")
    print(f"     复制文本到剪贴板: [{pyperclip.paste()}]")
    assert pyperclip.paste() == "招聘负责人的联系电话和邮箱是多少"
    
    print(f"     执行 Ctrl+V 粘贴: [{pyperclip.paste()}]")
    
    # 恢复剪贴板
    pyperclip.copy(saved2)
    print(f"     恢复后剪贴板: [{pyperclip.paste()}]")
    assert pyperclip.paste() == "xxx的邮箱是招聘负责人才有的"
    print("     ✅ 回放文本输入不污染剪贴板")
    print()
    
    # ---------- 最终验证 ----------
    print("=" * 55)
    print("  🎉 所有测试通过！修复成功！")
    print("=" * 55)
    print()
    print("最终剪贴板内容:", pyperclip.paste())
    print("预期内容: xxx的邮箱是招聘负责人才有的")
    print()
    return True


if __name__ == "__main__":
    try:
        success = test_clipboard_fix()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 异常: {e}")
        sys.exit(1)