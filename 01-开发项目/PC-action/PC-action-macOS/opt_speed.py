# -*- coding: utf-8 -*-
"""回放速度优化脚本"""
import os
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'image_recognition.py')
with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = 0
# ================================================================
# 🔴 速度瓶颈 1：每次点击(left_click/right_click等)后都强制等 80ms + 读剪贴板
#    80ms * 100步点击 = 8秒浪费！（实际上复制按钮点击场景极少，默认不该等）
# ================================================================
# 第846行附近（图片匹配成功后点击）
for i, line in enumerate(lines):
    if '_wait_click = 0.02 if turbo_match else 0.08' in line and i > 800:
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        # 80ms -> 10ms（只有剪贴板日志开启时才读+等，否则完全跳过等待）
        lines[i] = indent + '_wait_click = 0.01 if _clipboard_log_enabled else (0.005 if turbo_match else 0.01)\n'
        lines[i+1] = indent + 'if _wait_click > 0 and _clipboard_log_enabled:\n'
        # 后面的 paste() 也必须用 _clipboard_log_enabled 包起来，否则 pyperclip.paste() 本身就慢
        for j in range(i+2, min(i+15, len(lines))):
            if 'import pyperclip as _pcb' in lines[j] or '_cb_after_click = _pcb.paste()' in lines[j] or 'if _cb_after_click and _cb_after_click != ' in lines[j]:
                inner_indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                lines[j] = '    ' + lines[j] if not lines[j].startswith('    '+inner_indent) else lines[j]
            if lines[j].strip() == 'except Exception:':
                lines[j] = indent + '    except Exception:\n'
                lines[j+1] = indent + '        pass\n'
                break
        fixed += 1
        print(f'✅ 优化1: 点击后等待 80ms -> 10ms，剪贴板非必要不读取 (line {i+1})')
        break

# 同样第二处：第775行附近（坐标回退点击）
for i, line in enumerate(lines):
    if '_wait_click2 = 0.02 if turbo_match else 0.08' in line:
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        lines[i] = indent + '_wait_click2 = 0.01 if _clipboard_log_enabled else (0.005 if turbo_match else 0.01)\n'
        lines[i+1] = indent + 'if _wait_click2 > 0 and _clipboard_log_enabled:\n'
        for j in range(i+2, min(i+15, len(lines))):
            if lines[j].strip() == 'except Exception:':
                lines[j] = indent + '    except Exception:\n'
                lines[j+1] = indent + '        pass\n'
                break
        fixed += 1
        print(f'✅ 优化2: 坐标回退点击后等待 80ms -> 10ms，非必要不读剪贴板 (line {i+1})')
        break

# ================================================================
# 🔴 速度瓶颈 2：每次 Ctrl+V 前都 _force_clipboard 强制恢复(max_retry=2+delay=0.2)
#    一次 Ctrl+V = 最多 2 次 retry * (pyperclip.copy + sleep 0.2s + paste验证) = 超过 400ms
# ================================================================
for i, line in enumerate(lines):
    if '_force_clipboard(_first_paste_clipboard, label="Ctrl+V前恢复", max_retry=2, delay=0.2)' in line:
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        # max_retry 2→1, delay 0.2s→0.05s，且只在剪贴板实际被修改过时才强制恢复
        new_block = indent + 'if _first_paste_clipboard is not None:\n'
        new_block += indent + '    try:\n'
        new_block += indent + '        import pyperclip as _pcbv\n'
        new_block += indent + '        _cur_cb = _pcbv.paste()\n'
        new_block += indent + '        # ★ 速度优化：剪贴板内容已经是目标值就不强制恢复(省 0.2~0.4s)\n'
        new_block += indent + '        if _cur_cb != _first_paste_clipboard:\n'
        new_block += indent + '            _force_clipboard(_first_paste_clipboard, label="Ctrl+V前恢复", max_retry=1, delay=0.05)\n'
        new_block += indent + '    except Exception: pass\n'
        lines[i] = new_block
        fixed += 1
        print(f'✅ 优化3: Ctrl+V前恢复剪贴板 max_retry 2→1, delay 0.2→0.05s,先判断是否真的需要 (line {i+1})')
        break

# ================================================================
# 🔴 速度瓶颈 3：debug_mode=True 时大量 debug_print 输出（控制台I/O是毫秒级的）
#    但用户反馈"明显变慢"，这里其实是 _log_clipboard 被每步前后调用了4-8次（8ms/次 * 8次 *50步 = 3.2秒）
# ================================================================
# 其实已经在 _log_clipboard 顶部有判断，OK 不用动。但下面一处：Ctrl+V 前诊断读剪贴板也要判断
for i, line in enumerate(lines):
    if 'Ctrl+V 即将粘贴: len=' in line:
        # 这一段已经被 _clipboard_log_enabled 包住了吗？往上找
        for j in range(i-10, i):
            if "if _clipboard_log_enabled and 'v' == main_key and 'ctrl' in modifiers:" in lines[j]:
                print(f'✅ 优化4: Ctrl+V前诊断已经由 _clipboard_log_enabled 控制，OK (line {j+1})')
                break
        break

# ================================================================
# 🔴 速度瓶颈 4：大图模板判断 get_cached_image 每个失败步骤都做一次（其实可以缓存结果）
#    临时优化：匹配失败时，如果有 best_score > 0.3 就跳过完整 get_cached_image
# ================================================================
for i, line in enumerate(lines):
    if "_is_large_template = False" in line and i > 700:
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        # 在前面加一行快速判断：如果 best_score 已经 >=0.5 就没必要浪费时间读图片大小
        insert = indent + '# 速度优化：如果匹配分数已经足够接近阈值，没必要再读图片文件判断大小\n'
        insert += indent + 'if _best_score >= _safe_fallback_threshold:\n'
        insert += indent + '    _fallback_reason = f"score接近阈值({_best_score:.3f}≥{_safe_fallback_threshold:.2f})"\n'
        insert += indent + 'else:\n'
        # 把原来接下来的几行(到 _is_large_template 判断大图)缩进一层
        old_line = lines[i]
        lines[i] = insert + '    ' + old_line
        fixed += 1
        print(f'✅ 优化5: 分数达标时跳过 get_cached_image 大图检测 (line {i+1})')
        break

with open(FILE, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f'\n🎯 总计优化 {fixed} 处')
print('预计加速效果（50步典型流程，20步点击+5步Ctrl+V）：')
print('  - 点击等待：20*(80ms→10ms)   ≈ 节省 1.4s')
print('  - 剪贴板读：20*(15ms→0ms)    ≈ 节省 0.3s（日志关闭时）')
print('  - Ctrl+V恢复：5*(400ms→50ms) ≈ 节省 1.75s')
print('  合计单流程 ≈ 快 3~5 秒（视具体步骤数量） ✨')