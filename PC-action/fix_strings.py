import py_compile
import re

path = r'd:\code空间\PC-action\PC-action-macOS\app_macos.py'

round_num = 0
while round_num < 100:
    try:
        py_compile.compile(path, doraise=True)
        print(f'第{round_num+1}轮: 语法完全正确！')
        break
    except py_compile.PyCompileError as e:
        m = re.search(r'line (\d+)', str(e))
        if not m:
            print(f'无法解析错误: {e}')
            break
        lineno = int(m.group(1))
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if lineno < 1 or lineno > len(lines):
            print(f'行号越界: {lineno}')
            break
        
        line = lines[lineno - 1]
        print(f'第{round_num+1}轮 行{lineno}: {line.rstrip()[:100]}')
        
        # 自动修复
        original = line
        
        # 修复 "内容)  -> "内容") 
        line = re.sub(r'"([^"\n]*?)\)', r'"\1")', line)
        # 修复 '内容)  -> '内容')
        line = re.sub(r"'([^'\n]*?)\)", r"'\1')", line)
        # 修复 "内容,  -> "内容",
        line = re.sub(r'"([^"\n]*?),', r'"\1",', line)
        # 修复 '内容,  -> '内容',
        line = re.sub(r"'([^'\n]*?),", r"'\1',", line)
        # 修复 "内容]  -> "内容"]
        line = re.sub(r'"([^"\n]*?)\]', r'"\1"]', line)
        # 修复 '内容]  -> '内容']
        line = re.sub(r"'([^'\n]*?)\]", r"'\1']", line)
        
        if line == original:
            print(f'  -> 无法自动修复此行的引号问题')
            break
        
        lines[lineno - 1] = line
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f'  -> 已修复')
        round_num += 1

print('修复完成')