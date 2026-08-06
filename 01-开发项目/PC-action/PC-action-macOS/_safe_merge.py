"""
安全合并脚本：拉取两台电脑的远程代码，强制保留本地的录制/组合技/快捷键
"""
import os
import shutil
import subprocess
import datetime
import sys

# ============== 配置 ==============
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(PROJECT_DIR, f"_backup_merge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")

# 必须保护的本地数据（远程改了也不动本地）
PROTECT_PATHS = [
    "recordings",           # 所有录制文件夹
    "data/combo_skills.json",   # 组合技配置
    "data/shortcuts.json",      # 快捷键配置
    "data/key_bindings.json",   # 按键绑定
    "data/combo_skills.json.bak",
    "login_credentials.json",   # 登录凭据
]

# 需要合并的代码文件（允许被远程更新）
MERGE_CODE_EXT = {".py", ".json", ".spec", ".md", ".txt", ".ui", ".qss", ".css", ".html", ".js"}
MERGE_CODE_FILES = {
    "app.py", "app_macos.py", "image_recognition.py", "design_system.py",
    "beautiful_dialog.py", "combo_skill_edit_dialog.py", "combo_skill_manager.py",
    "database_helper.py", "hybrid_db.py", "login_manager.py", "login_ui.py",
    "main.py", "selection_overlay.py", "styles.py", "supabase_db.py",
    "theme_generator.py", "utils.py", "admin_manager.py",
    "opt_speed.py", "_check_combos.py", "simple_push.py",
    ".gitignore", "PC-Action.spec", "PC-action-macOS.spec",
}

def log(msg, level="INFO"):
    prefix = {"INFO": "[ℹ]", "OK": "[✅]", "WARN": "[⚠]", "ERR": "[❌]"}.get(level, "[•]")
    print(f"{prefix} {msg}")

def run_cmd(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, cwd=PROJECT_DIR,
                       capture_output=True, text=True,
                       encoding='utf-8', errors='replace',
                       timeout=timeout)
    return r

# ================== 步骤 1：备份本地保护数据 ==================
log("=" * 60)
log(f"项目目录: {PROJECT_DIR}")
log(f"备份目录: {BACKUP_DIR}")
log("=" * 60)

os.makedirs(BACKUP_DIR, exist_ok=True)
log("步骤 1/5: 备份本地保护数据...")
for rel_path in PROTECT_PATHS:
    abs_src = os.path.join(PROJECT_DIR, rel_path)
    abs_dst = os.path.join(BACKUP_DIR, rel_path)
    if os.path.exists(abs_src):
        os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
        if os.path.isdir(abs_src):
            shutil.copytree(abs_src, abs_dst)
            log(f"  备份文件夹: {rel_path}/", "OK")
        else:
            shutil.copy2(abs_src, abs_dst)
            log(f"  备份文件: {rel_path}", "OK")
    else:
        log(f"  跳过不存在: {rel_path}", "WARN")
log("本地保护数据备份完成！", "OK")

# ================== 步骤 2：抓取远程代码（不合并） ==================
log("\n步骤 2/5: 抓取远程最新代码（fetch）...")
r = run_cmd("git fetch --all")
if r.returncode == 0:
    log("抓取成功", "OK")
else:
    log(f"抓取失败: {r.stderr[:300]}", "ERR")
    log("继续执行...", "WARN")

# 显示远程有哪些分支/提交
r = run_cmd("git remote -v")
log(f"远程仓库:\n{r.stdout}")
r = run_cmd("git log --oneline -5 HEAD")
log(f"本地最近5次提交:\n{r.stdout}")
r = run_cmd("git log --oneline -5 origin/main 2>nul || git log --oneline -5 origin/master 2>nul")
log(f"远程最近5次提交:\n{r.stdout}")

# ================== 步骤 3：临时藏起本地保护数据 ==================
log("\n步骤 3/5: 临时移走本地保护数据（避免合并冲突）...")
TEMP_HIDE_DIR = os.path.join(PROJECT_DIR, "_merge_temp_hide")
if os.path.exists(TEMP_HIDE_DIR):
    shutil.rmtree(TEMP_HIDE_DIR)
os.makedirs(TEMP_HIDE_DIR, exist_ok=True)

hidden_paths = []
for rel_path in PROTECT_PATHS:
    abs_src = os.path.join(PROJECT_DIR, rel_path)
    abs_dst = os.path.join(TEMP_HIDE_DIR, rel_path)
    if os.path.exists(abs_src):
        os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
        try:
            shutil.move(abs_src, abs_dst)
            hidden_paths.append(rel_path)
            log(f"  移走: {rel_path}", "OK")
        except Exception as e:
            log(f"  移走失败 {rel_path}: {e}", "WARN")

# ================== 步骤 4：合并远程代码 ==================
log("\n步骤 4/5: 合并远程代码到本地...")

# 检查分支名
r = run_cmd("git rev-parse --abbrev-ref HEAD")
local_branch = r.stdout.strip()
log(f"当前分支: {local_branch}")

# 确定远程分支名
r = run_cmd("git branch -r")
remote_branches = [b.strip() for b in r.stdout.split('\n') if b.strip() and 'HEAD' not in b]
log(f"远程分支: {remote_branches}")

target_remote = None
for rb in remote_branches:
    if 'main' in rb:
        target_remote = rb
        break
if not target_remote and remote_branches:
    target_remote = remote_branches[0]

if not target_remote:
    log("没有找到远程分支，跳过合并", "WARN")
else:
    log(f"合并目标: {target_remote}")
    # 策略：优先远程代码版本，冲突时用远程（代码文件）
    r = run_cmd(f'git merge -X theirs --no-edit {target_remote}', timeout=120)
    log(f"merge返回码: {r.returncode}")
    if r.stdout.strip():
        log(f"输出: {r.stdout[:500]}")
    if r.stderr.strip():
        err = r.stderr[:500]
        # 过滤无用信息
        if 'Already up to date' in r.stdout or 'Already up to date' in r.stderr:
            log("本地已是最新，无需合并", "OK")
        elif r.returncode == 0:
            log(f"合并成功: {err}", "OK")
        else:
            log(f"合并结果: {err}", "WARN")

    # 重置合并过程中可能被远程改了的保护路径（如果有的话）
    # (即使git认为它们没被跟踪，也强制清掉)
    for rel_path in PROTECT_PATHS:
        abs_p = os.path.join(PROJECT_DIR, rel_path)
        if os.path.exists(abs_p):
            if os.path.isdir(abs_p):
                shutil.rmtree(abs_p)
                log(f"  清除远程版本(文件夹): {rel_path}/", "OK")
            else:
                os.remove(abs_p)
                log(f"  清除远程版本(文件): {rel_path}", "OK")

# ================== 步骤 5：恢复本地保护数据 ==================
log("\n步骤 5/5: 恢复本地保护数据（覆盖远程）...")
for rel_path in hidden_paths:
    abs_src = os.path.join(TEMP_HIDE_DIR, rel_path)
    abs_dst = os.path.join(PROJECT_DIR, rel_path)
    if os.path.exists(abs_src):
        os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
        try:
            shutil.move(abs_src, abs_dst)
            log(f"  恢复: {rel_path}", "OK")
        except Exception as e:
            log(f"  恢复失败 {rel_path}: {e}, 尝试从备份复制...", "WARN")
            back_src = os.path.join(BACKUP_DIR, rel_path)
            if os.path.exists(back_src):
                if os.path.isdir(back_src):
                    shutil.copytree(back_src, abs_dst)
                else:
                    shutil.copy2(back_src, abs_dst)
                log(f"  从备份恢复成功: {rel_path}", "OK")

# 清理临时目录
try:
    if os.path.exists(TEMP_HIDE_DIR):
        shutil.rmtree(TEMP_HIDE_DIR)
except Exception:
    pass

# ================== 最终校验 ==================
log("\n" + "=" * 60)
log("✅ 合并完成！校验结果：")
log("=" * 60)
for rel_path in PROTECT_PATHS:
    abs_p = os.path.join(PROJECT_DIR, rel_path)
    exists = os.path.exists(abs_p)
    tag = "✅" if exists else "❌"
    size = ""
    if exists and os.path.isfile(abs_p):
        size = f" ({os.path.getsize(abs_p)}字节)"
    elif exists and os.path.isdir(abs_p):
        cnt = sum([len(files) for r, d, files in os.walk(abs_p)])
        size = f" ({cnt}个文件)"
    log(f"  {tag} {rel_path}{size}")

log(f"\n📦 备份目录（双重保险，可手动恢复）: {BACKUP_DIR}")
log("\n合并完成！快捷键、录制、组合技均为本地原始版本，代码文件已更新为两台电脑的最新合并版。")
log("=" * 60)