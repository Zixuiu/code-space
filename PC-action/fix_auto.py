import re

path = r'd:\code空间\PC-action\PC-action-macOS\app_macos.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 自动脚本引入的错误：在 ), ] 或 } 前添加了多余的引号
# 修复模式1: xxx") 在下一字符是换行或空格时 -> xxx)
# 只修复那些确实是被误添加的引号

# 修复 "}) -> })
content = re.sub(r'"}\)', '})', content)
# 修复 "]) -> ])
content = re.sub(r'"\]\)', '])', content)
# 修复 ") 后跟换行 -> 只删除这个引号
# 更安全的方式: 找到所有 ")、"]、"} 的模式并删除多余的引号
content = re.sub(r'"(\s*[\)\]\}])', r'\1', content)

# 修复 :")  -> :)
content = re.sub(r':"\)', ':)', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('批量修复完成')

# 验证
import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('语法正确！')
except py_compile.PyCompileError as e:
    m = re.search(r'line (\d+)', str(e))
    if m:
        lines = open(path, encoding='utf-8').readlines()
        print(f'仍有错误行{m.group(1)}: {lines[int(m.group(1))-1].rstrip()[:100]}')