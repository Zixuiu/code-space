import re

f = r'd:\code空间\PC-action\PC-action-macOS\app_macos.py'
with open(f, 'r', encoding='utf-8', errors='replace') as fh:
    content = fh.read()

garbled = set('çéåæèàáâãäìíîïðñòóôõöøùúûüýþÿ')
lines = content.split('\n')
result = []
i = 0
while i < len(lines):
    line = lines[i]
    s = line.lstrip()
    indent = line[:len(line)-len(s)]
    has_garbled = any(c in line for c in garbled)

    if has_garbled and s.startswith('"""'):
        cnt = s.count('"""')
        if cnt >= 2:
            result.append(indent + '""""""')
            i += 1
            continue
        else:
            result.append(indent + '""""""')
            depth = 1
            i += 1
            while i < len(lines) and depth > 0:
                if '\"\"\"' in lines[i]:
                    depth -= 1
                i += 1
            continue

    if has_garbled and s.startswith('#'):
        i += 1
        continue

    if has_garbled and '"""' in line:
        result.append(indent + '""""""')
        i += 1
        continue

    if has_garbled and not s.startswith('"""') and not s.startswith("'''"):
        i += 1
        continue

    result.append(line)
    i += 1

with open(f, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(result))
print('Done')
