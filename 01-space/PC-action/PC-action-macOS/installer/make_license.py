# -*- coding: utf-8 -*-
"""从 docs/EULA与隐私政策.md 生成 NSIS 许可页用的 license.txt（UTF-8 BOM + CRLF）。
NSIS Unicode 版按 UTF-8 解析，BOM 必备；许可控件要求 CRLF 换行。"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', 'docs', 'EULA与隐私政策.md'))
DST = os.path.join(HERE, 'license.txt')

t = open(SRC, encoding='utf-8').read()
t = t.replace('**', '')
t = re.sub(r'^#+\s*', '', t, flags=re.M)
t = re.sub(r'^\s*-\s*', '  · ', t, flags=re.M)
t = t.replace('\r\n', '\n').replace('\n', '\r\n')
open(DST, 'w', encoding='utf-8-sig', newline='').write(t)

print('license.txt: %d bytes' % os.path.getsize(DST))
hit = [l for l in t.splitlines() if '9.9' in l or '99' in l and '元' in l]
for l in hit:
    print('  价格行:', l.strip())
