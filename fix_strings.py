# -*- coding: utf-8 -*-
"""Fix unterminated string literals in selection_overlay.py"""
import re

filepath = 'd:\\codespace\\01-开发项目\\PC-action\\PC-action-macOS\\selection_overlay.py'

with open(filepath, 'rb') as f:
    raw_bytes = f.read()

# Check line 195 raw bytes
lines = raw_bytes.split(b'\n')
print(f'Total lines: {len(lines)}')
print(f'Line 195 raw (first 200 bytes): {lines[194][:200]}')
print(f'Line 195 ends with: {lines[194][-20:]}')
print()

# Check if line 195 ends with a double quote
line195 = lines[194].decode('utf-8', errors='replace')
print(f'Line 195 decoded: {line195[:120]}')
print(f'Line 195 last char: {repr(line195[-1])}')

# Check lines around 517 and 594
for ln in [516, 517, 593, 594, 720, 721]:
    if ln < len(lines):
        decoded = lines[ln].decode('utf-8', errors='replace')
        print(f'Line {ln+1}: {decoded[:120]}')
        print(f'  ends with: {repr(decoded.strip()[-5:])}')