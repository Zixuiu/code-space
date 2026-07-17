"""诊断 Alt 键识别问题"""
import keyboard
import time

print("=" * 60)
print("Alt 键诊断脚本")
print("=" * 60)

# 1. 检查 Alt 键的 scan_code
print("\n[1] Alt 键的 scan_code:")
try:
    # keyboard 库中 Alt 键的标准 scan_code
    # 左 Alt = 56, 右 Alt = 57394 (在某些系统上可能不同)
    alt_scan_codes = keyboard._canonical_names.get('alt', [])
    print(f"  Alt 键的 canonical_names: {alt_scan_codes}")
    
    # 检查 keyboard.KEY_NAMES
    if hasattr(keyboard, 'KEY_NAMES'):
        alt_names = [k for k, v in keyboard.KEY_NAMES.items() if 'alt' in k.lower()]
        print(f"  Alt 相关键名: {alt_names[:10]}")
except Exception as e:
    print(f"  获取 Alt 键信息失败: {e}")

# 2. 注册一个测试热键 Alt+M
print("\n[2] 注册测试热键 Alt+M:")
test_triggered = []
def test_callback():
    test_triggered.append(True)
    print("  >>> Alt+M 被触发! <<<")

keyboard.add_hotkey('alt+m', test_callback)
print("  已注册 Alt+M 热键")

# 3. 检查 nonblocking_hotkeys 内容
print("\n[3] nonblocking_hotkeys 状态:")
listener = getattr(keyboard, '_listener', None)
if listener:
    nb_hotkeys = getattr(listener, 'nonblocking_hotkeys', {})
    print(f"  nonblocking_hotkeys 数量: {len(nb_hotkeys)}")
    for key_tuple in list(nb_hotkeys.keys())[:10]:
        print(f"  热键组合 (scan_code元组): {key_tuple}")
else:
    print("  _listener 不存在!")

# 4. 检查 _hotkeys 内容
print("\n[4] _hotkeys 字典状态:")
hotkeys = getattr(keyboard, '_hotkeys', {})
print(f"  _hotkeys 数量: {len(hotkeys)}")
for key_str in list(hotkeys.keys())[:10]:
    if isinstance(key_str, str):
        print(f"  热键字符串: '{key_str}'")

# 5. 检查 Alt 键是否在 scan_code 映射中
print("\n[5] Alt 键 scan_code 映射:")
try:
    # 获取 Alt 键的 scan_code
    from keyboard import _CanonicalName
    alt_canonical = _CanonicalName('alt')
    print(f"  Alt 键 canonical name 对象: {alt_canonical}")
    
    # 检查 scan codes
    if hasattr(keyboard, '_canonical_names'):
        alt_scancodes = keyboard._canonical_names.get('alt', set())
        print(f"  Alt 键 scan_code 集合: {alt_scancodes}")
except Exception as e:
    print(f"  获取失败: {e}")

# 6. 等待用户按下 Alt+M 进行测试
print("\n[6] 请按下 Alt+M 进行测试 (5秒内)...")
print("  (如果程序能识别，会显示 '>>> Alt+M 被触发! <<<')")
start = time.time()
while time.time() - start < 5:
    if test_triggered:
        print("  ✅ Alt+M 热键成功触发!")
        break
    time.sleep(0.1)

if not test_triggered:
    print("  ❌ Alt+M 热键未被触发")
    
    # 检查按下事件状态
    print("\n[7] 检查按下事件状态:")
    pressed_events = getattr(keyboard, '_pressed_events', set())
    print(f"  _pressed_events: {pressed_events}")
    
    phys_pressed = getattr(keyboard, '_physically_pressed_keys', set())
    print(f"  _physically_pressed_keys: {phys_pressed}")
    
    log_pressed = getattr(keyboard, '_logically_pressed_keys', set())
    print(f"  _logically_pressed_keys: {log_pressed}")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)