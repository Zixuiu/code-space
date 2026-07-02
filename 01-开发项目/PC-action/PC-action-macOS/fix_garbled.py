import codecs

file_path = r'd:\code空间\01-开发项目\PC-action\PC-action-macOS\app_macos.py'

with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# Fix the garbled text
old_text = "运行中（{running_count}个组合技锛?)"
new_text = "运行中（{running_count}个组合技）"

if old_text in content:
    content = content.replace(old_text, new_text)
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.write(content)
    print("Fixed successfully!")
else:
    print("Text not found. Trying alternative...")
    # Try to find and fix it differently
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '运行中' in line and '组合技' in line:
            print(f"Found at line {i+1}: {line}")
            if '锛?' in line or '\uff1f' in line:
                new_line = line.replace('锛?', ')').replace('\uff1f', ')')
                lines[i] = new_line
                print(f"Fixed: {new_line}")
                with codecs.open(file_path, 'w', 'utf-8') as f:
                    f.write('\n'.join(lines))
                print("Fixed successfully!")
                break