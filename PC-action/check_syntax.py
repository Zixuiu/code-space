import py_compile
path = r'd:\code空间\PC-action\PC-action-macOS\app_macos.py'
try:
    py_compile.compile(path, doraise=True)
    print('OK')
except py_compile.PyCompileError as e:
    import re
    m = re.search(r'line (\d+)', str(e))
    if m:
        lines = open(path, encoding='utf-8').readlines()
        print(f'行{m.group(1)}: {lines[int(m.group(1))-1].rstrip()[:100]}')
    else:
        print(str(e)[:200])