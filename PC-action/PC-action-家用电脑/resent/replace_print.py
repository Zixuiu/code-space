import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换未注释的 print 语句为 pass，保持缩进
def replace_print(match):
    indent = match.group(1)
    return indent + 'pass'

# 使用正则替换：行首空白后紧跟 print(
new_content = re.sub(r'^(\s*)print\s*\(.*\)\s*$', replace_print, content, flags=re.MULTILINE)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done')
