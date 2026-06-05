import openpyxl
import re

wb = openpyxl.load_workbook(r'd:\code空间\客户xlsx\店铺粉丝量完整清单-2026.xlsx')
ws = wb['店铺粉丝量清单-已确定位置']

addresses = []
for row in ws.iter_rows(min_row=1, values_only=True):
    addr = str(row[1]).strip() if row[1] else ''
    if addr:
        name = str(row[0]).strip() if row[0] else ''
        addresses.append((name, addr))

print(f'B列有地址的行数: {len(addresses)}')
print()

# 分析地址的结尾模式（地址部分之后的内容）
endings = {}
for name, addr in addresses:
    # 用 ,  曾   【  未发布  等分割
    parts = re.split(r'[，,]\s*曾|【|未发布', addr)
    core_addr = parts[0].strip()
    end_marker = addr[len(core_addr):][:20] if len(addr) > len(core_addr) else '(无后缀)'
    endings[end_marker] = endings.get(end_marker, 0) + 1

print('=== 地址后缀模式统计 (前30) ===')
for k, v in sorted(endings.items(), key=lambda x: -x[1])[:30]:
    print(f'  [{k}] -> {v}条')

print()
print('=== 地址不包含"市"或"区"的异常样本 ===')
for name, addr in addresses:
    core = re.split(r'[，,]\s*曾|【|未发布', addr)[0].strip()
    if '市' not in core or '区' not in core:
        print(f'  店铺={name[:20]}, 地址核心={core[:50]}')

print()
print('=== 随机样本展示提取效果 ===')
for i, (name, addr) in enumerate(addresses[:20]):
    core = re.split(r'[，,]\s*曾|【|未发布', addr)[0].strip()
    print(f'  {name[:15]}:')
    print(f'    原始: {addr[:70]}')
    print(f'    提取: {core[:70]}')
    print()