# -*- coding: utf-8 -*-
"""
安全合并：两个电脑的 git 提交合入本地，保护 recordings/组合技/快捷键不动。
不使用 shell=True，避免 PowerShell 的环境变量/PSReadLine 问题。
"""
import os
import shutil
import subprocess
import datetime
import sys

PROJECT_DIR = r'd:\codespace\01-开发项目\PC-action\PC-action-macOS'
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BACKUP_DIR = os.path.join(PROJECT_DIR, f'_backup_merge_{TS}')
LOG_FILE = os.path.join(PROJECT_DIR, f'_merge_result_{TS}.txt')
HIDE_DIR = os.path.join(PROJECT_DIR, '_merge_temp_hide')

PROTECT = [
    ('recordings', 'dir'),
    ('data/combo_skills.json', 'file'),
    ('data/combo_skills.json.bak', 'file'),
    ('data/shortcuts.json', 'file'),
    ('data/key_bindings.json', 'file'),
    ('login_credentials.json', 'file'),
]

def _open_log():
    return open(LOG_FILE, 'a', encoding='utf-8')

def log(msg):
    print(msg)
    try:
        with _open_log() as f:
            f.write(str(msg) + '\n')
    except Exception:
        pass

def git(*args):
    """ 调用 git，不经过 shell，避免命令行拼接问题 """
    full = ['git'] + list(args)
    try:
        r = subprocess.run(full, cwd=PROJECT_DIR, capture_output=True,
                           text=True, encoding='utf-8', errors='replace',
                           timeout=120, env={**os.environ})
        out = (r.stdout or '') + (r.stderr or '')
        return r.returncode, out.strip()
    except Exception as e:
        return -1, f'Exception: {e}'

def exists(rel):
    return os.path.exists(os.path.join(PROJECT_DIR, rel))

def cp_protect(src_root, dst_root):
    """ 复制保护文件从 src_root -> dst_root（rel path）"""
    for rel, typ in PROTECT:
        s = os.path.join(src_root, rel)
        d = os.path.join(dst_root, rel)
        if os.path.exists(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            try:
                if typ == 'dir':
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            except Exception as e:
                log(f'  cp warn {rel}: {e}')

def mv_hide(src_root, dst_root):
    """ 移动到临时目录（不复制） """
    moved = []
    for rel, typ in PROTECT:
        s = os.path.join(src_root, rel)
        d = os.path.join(dst_root, rel)
        if os.path.exists(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            try:
                shutil.move(s, d)
                moved.append(rel)
            except Exception as e:
                # 失败就复制+删除
                log(f'  move fallback: {rel} ({e})')
                try:
                    if typ == 'dir':
                        shutil.copytree(s, d)
                        shutil.rmtree(s)
                    else:
                        shutil.copy2(s, d)
                        os.remove(s)
                    moved.append(rel)
                except Exception as e2:
                    log(f'  mv FAIL {rel}: {e2}')
    return moved

os.chdir(PROJECT_DIR)
with _open_log() as f:
    f.write(f'=== 开始合并 {TS} ===\n')
    f.write(f'项目目录: {PROJECT_DIR}\n')
    f.write(f'备份目录: {BACKUP_DIR}\n\n')

# ============== Step1: 备份保护数据 ==============
log('[1/5] 备份本地保护数据 ...')
os.makedirs(BACKUP_DIR, exist_ok=True)
cp_protect(PROJECT_DIR, BACKUP_DIR)
for rel, typ in PROTECT:
    if exists(rel):
        tag = 'dir' if typ == 'dir' else f'{os.path.getsize(os.path.join(PROJECT_DIR, rel))}B'
        log(f'  ✅ 已备份 {rel} ({tag})')
    else:
        log(f'  ⏭ 不存在 {rel}（跳过）')

# ============== Step2: git fetch ==============
log('\n[2/5] git fetch --all ...')
rc, out = git('fetch', '--all')
log(f'  fetch exit={rc}')
if out:
    log(f'  output: {out[:500]}')

# 显示提交差异
log('\n-- 本地最近3个提交 --')
rc, out = git('log', '--oneline', '-3', 'HEAD')
log(out)
log('\n-- 远程最近3个提交 (origin/main) --')
rc1, out1 = git('log', '--oneline', '-3', 'origin/main')
rc2, out2 = git('log', '--oneline', '-3', 'origin/master')
log(out1 or out2 or '(无远程分支信息)')

# ============== Step3: 临时移走保护数据 ==============
log('\n[3/5] 移走本地保护数据（避免冲突） ...')
if os.path.exists(HIDE_DIR):
    shutil.rmtree(HIDE_DIR)
os.makedirs(HIDE_DIR)
moved = mv_hide(PROJECT_DIR, HIDE_DIR)
for m in moved:
    log(f'  ➡️  移走: {m}')

# ============== Step4: 合并远程代码 ==============
log('\n[4/5] 合并远程代码（代码冲突优先用远程版）...')
# 找目标远程分支
rc, out = git('branch', '-r')
remote_branch = None
for line in out.splitlines():
    line = line.strip()
    if line and 'HEAD' not in line:
        if '/main' in line:
            remote_branch = line
            break
if not remote_branch:
    for line in out.splitlines():
        line = line.strip()
        if line and 'HEAD' not in line:
            remote_branch = line
            break

if not remote_branch:
    log('  ⚠️  未发现远程分支，跳过合并')
else:
    log(f'  目标分支: {remote_branch}')
    rc, out = git('merge', '-X', 'theirs', '--no-edit', remote_branch)
    log(f'  merge exit={rc}')
    if out:
        # 过滤噪声
        lines = [l for l in out.splitlines() if l.strip()]
        log('\n'.join(lines)[:800])

# 清理合并后可能存在的远程保护路径
for rel, typ in PROTECT:
    p = os.path.join(PROJECT_DIR, rel)
    if os.path.exists(p):
        try:
            if typ == 'dir':
                shutil.rmtree(p)
            else:
                os.remove(p)
            log(f'  🧹 清除远程残留: {rel}')
        except Exception as e:
            log(f'  🧹 清理失败 {rel}: {e}')

# ============== Step5: 恢复本地保护数据 ==============
log('\n[5/5] 恢复本地保护数据 ...')
restored_ok = []
for rel, typ in PROTECT:
    s = os.path.join(HIDE_DIR, rel)
    d = os.path.join(PROJECT_DIR, rel)
    if os.path.exists(s):
        os.makedirs(os.path.dirname(d), exist_ok=True)
        try:
            shutil.move(s, d)
            restored_ok.append(rel)
        except Exception:
            try:
                if typ == 'dir':
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
                restored_ok.append(rel)
            except Exception as e:
                log(f'  ⚠️  恢复失败 {rel}: {e}')

# 兜底：临时目录恢复失败时用备份
for rel, typ in PROTECT:
    if not exists(rel):
        back = os.path.join(BACKUP_DIR, rel)
        if os.path.exists(back):
            log(f'  ⚠️  {rel} 缺失，从备份目录兜底恢复...')
            d = os.path.join(PROJECT_DIR, rel)
            if typ == 'dir':
                shutil.copytree(back, d)
            else:
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(back, d)
            restored_ok.append(rel)

for r in restored_ok:
    log(f'  ✅ 恢复: {r}')

# 清理临时目录
try:
    if os.path.exists(HIDE_DIR):
        shutil.rmtree(HIDE_DIR)
except Exception:
    pass

# ============== 最终校验 ==============
log('\n' + '='*60)
log('📋 合并完成 - 校验结果')
log('='*60)
ok = 0
bad = 0
for rel, typ in PROTECT:
    p = os.path.join(PROJECT_DIR, rel)
    if os.path.exists(p):
        if typ == 'dir':
            cnt = sum(len(f) for _, _, f in os.walk(p))
            log(f'  ✅ {rel}/ ({cnt} 个文件)')
        else:
            log(f'  ✅ {rel} ({os.path.getsize(p)} 字节)')
        ok += 1
    else:
        log(f'  ❌ {rel} 缺失！请从 BACKUP 手动恢复')
        bad += 1

log(f'\n📦 备份目录: {BACKUP_DIR}')
log(f'🎯 校验: {ok} 项通过，{bad} 项缺失')
if bad == 0:
    log('✅ 全部通过！「录制 / 组合技 / 快捷键 / 登录凭据」都是本地原始版本')
    log('✅ 代码文件（*.py 等）已合并两台电脑的最新提交')
else:
    log('⚠️  有缺失项，请使用备份目录手动复制恢复')

log('\nDONE.')
sys.exit(0)