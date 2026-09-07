# -*- coding: utf-8 -*-
"""
临时校验脚本：比对 PyInstaller 产物 dist\PC-Action 与安装后的目录，
逐个文件校验 MD5，确认安装包释放的内容完整且字节一致。验证完即删除。
"""
import hashlib
import os
import sys

SKIP_DIRS = {'user_data', 'recordings', '__pycache__'}
SKIP_FILES = {'uninstall.exe'}


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def scan(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name in SKIP_FILES:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            out[rel] = md5(full)
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    a, b = scan(src), scan(dst)

    only_src = sorted(set(a) - set(b))
    only_dst = sorted(set(b) - set(a))
    diff = sorted(k for k in set(a) & set(b) if a[k] != b[k])

    lines = []
    lines.append(f'源文件数: {len(a)}   安装目录文件数(不含卸载程序/用户数据): {len(b)}')
    lines.append(f'仅在源目录(未安装): {len(only_src)}')
    for k in only_src[:10]:
        lines.append('   - ' + k)
    lines.append(f'仅在安装目录(多出来): {len(only_dst)}')
    for k in only_dst[:10]:
        lines.append('   + ' + k)
    lines.append(f'内容不一致(MD5 不同): {len(diff)}')
    for k in diff[:10]:
        lines.append('   * ' + k)

    # 关键文件存在性
    key = ['PC-Action.exe', 'pricing.json', 'icons/play.svg', 'data/combo_skills.json']
    lines.append('关键文件:')
    for k in key:
        k2 = k.replace('/', os.sep)
        lines.append(f'   {k}: {"OK" if k2 in b else "缺失"}')
    icons = [p for p in b if p.startswith('icons' + os.sep)]
    lines.append(f'icons 资源文件数: {len(icons)}')

    ok = (not only_src) and (not diff)
    lines.append('结论: ' + ('完全一致 ✔' if ok else '存在差异 ✘'))
    text = '\n'.join(lines)
    print(text)
    open(sys.argv[3], 'w', encoding='utf-8').write(text)


if __name__ == '__main__':
    main()
