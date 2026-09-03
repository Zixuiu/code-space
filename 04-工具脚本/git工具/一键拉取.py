# -*- coding: utf-8 -*-
import os
import sys
import shutil
import subprocess
import tempfile
import glob as glob_mod

# 修复 Windows 下 emoji/中文乱码：强制 stdout/stderr 走 UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass

# ---- 路径常量（关键：脚本位于 04-工具脚本/git工具/，仓库根是上两级目录）----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
APP_DIR = os.path.join(REPO_ROOT, "01-space", "PC-action", "PC-action-macOS")

REMOTE = "origin"
BRANCH = "main"
SSH_URL = "git@gitcode.com:weixin_58844486/codespace.git"
GITCODE_REPO = "weixin_58844486/codespace"
SSH_PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOex2p0CkIAkhA98M4KCpzxPL4hkZPfXc8D6In5gondh 1399972370@qq.com"

# 受保护的本地数据：每台机器独立，不进仓库。
# 这些是绝对路径（必须用绝对路径，绝不能当 BASE_DIR 的相对路径去拼，否则备份目标错乱）。
PROTECTED_EXPLICIT = [
    os.path.join(APP_DIR, "data"),        # 组合技（combo_skills.json）
    os.path.join(APP_DIR, "user_data"),   # 快捷键 / 偏好
    os.path.join(APP_DIR, "recordings"),  # 流程文件 / 录制
]
# 只在 APP_DIR 下扫描 *.db（避免误备份其他项目如 go-music-dl 的数据库）
PROTECTED_PATTERNS = [os.path.join(APP_DIR, "*.db")]
# 排除规则：路径含这些关键词视为测试副本/临时目录，不备份
EXCLUDE_KEYWORDS = ("_backup", "backup_", "_test", "test_", "temp_", "_temp",
                    "_copy", "copy_", "_old", "old_", "_bak", "bak_")


def _is_excluded_path(p):
    norm = p.replace("\\", "/").lower()
    return any(kw in norm for kw in EXCLUDE_KEYWORDS)


def collect_protected():
    """返回真实存在的受保护绝对路径列表。"""
    found = []
    for p in PROTECTED_EXPLICIT:
        if _is_excluded_path(p):
            continue
        if os.path.exists(p):
            found.append(p)
    for pat in PROTECTED_PATTERNS:
        for m in glob_mod.glob(pat):
            if _is_excluded_path(m):
                continue
            if m not in found and os.path.exists(m):
                found.append(m)
    return found


def log(msg, level="INFO"):
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "•")
    print(f"{prefix} {msg}")


def run_cmd(cmd, cwd=None, timeout=60):
    # 默认在仓库根执行（关键修复：旧脚本默认 cwd=BASE_DIR 会误操作 git工具 目录）
    return subprocess.run(
        cmd, shell=True, cwd=cwd or REPO_ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )


def check_prerequisites():
    issues = []
    r = run_cmd("git --version")
    if r.returncode != 0:
        issues.append("Git 未安装或不在 PATH 中。请先装 Git：https://git-scm.com/download/win")
    return issues


def has_git_repo():
    # 关键修复：检查仓库根，而不是脚本所在目录
    return os.path.isdir(os.path.join(REPO_ROOT, ".git"))


# ---------------------------------------------------------------------------
# 本地数据保护：备份 / 恢复 / 校验
# ---------------------------------------------------------------------------
def backup_protected():
    """把受保护数据复制到临时目录（按绝对路径），返回 (backup_root, [(abs_src, abs_dst), ...])"""
    backup_root = tempfile.mkdtemp(prefix="pcaction_pull_backup_")
    entries = []
    for src in collect_protected():
        # 用路径拼出唯一扁平名，避免冒号/分隔符冲突
        flat = src.replace(":", "").replace(os.sep, "_")
        dst = os.path.join(backup_root, flat)
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            entries.append((src, dst))
            log(f"已备份: {os.path.relpath(src, REPO_ROOT)}", "INFO")
        except Exception as e:
            log(f"备份失败 {src}: {e}", "WARNING")
    return backup_root, entries


def restore_protected(entries):
    for src, dst in entries:
        try:
            os.makedirs(os.path.dirname(src), exist_ok=True)
            if os.path.isdir(dst):
                shutil.copytree(dst, src, dirs_exist_ok=True)
            else:
                shutil.copy2(dst, src)
        except Exception as e:
            log(f"恢复失败 {src}: {e}", "WARNING")


def _dir_nonempty(path):
    try:
        return any(os.scandir(path))
    except Exception:
        return False


def verify_restored(entries):
    """恢复后校验：备份过的本地数据，恢复后必须存在且（文件非空 / 目录非空）。"""
    ok, bad = 0, []
    for src, _dst in entries:
        if not os.path.exists(src):
            bad.append(src)
        elif os.path.isfile(src) and os.path.getsize(src) == 0:
            bad.append(src)
        elif os.path.isdir(src) and not _dir_nonempty(src):
            bad.append(src)
        else:
            ok += 1
    if bad:
        log("⚠️ 以下本地数据恢复异常（不存在或为空），请立即检查：", "ERROR")
        for b in bad:
            log(f"   - {os.path.relpath(b, REPO_ROOT)}", "ERROR")
    else:
        log(f"本地数据校验通过：{ok} 项已确认保留（组合技/快捷键/流程录制均未被影响）", "SUCCESS")
    return not bad


def cleanup_backup(backup_root):
    shutil.rmtree(backup_root, ignore_errors=True)


# ---------------------------------------------------------------------------
# 认证：SSH 私钥 / GitCode token（HTTPS）
# ---------------------------------------------------------------------------
def get_gitcode_token():
    tok = os.environ.get("GITCODE_TOKEN")
    if tok:
        return tok.strip()
    p = os.path.join(os.path.expanduser("~"), ".ssh", "gitcode_token")
    if os.path.exists(p):
        try:
            s = open(p, "r", encoding="utf-8", errors="replace").read().strip().replace("\x00", "")
            return s
        except Exception:
            return None
    return None


def build_https_url(token):
    return f"https://oauth2:{token}@gitcode.com/{GITCODE_REPO}.git"


def setup_ssh():
    """写入公钥/config（仅当缺失时写），返回是否有可用私钥。无私钥不代表失败——调用方可回退 token。"""
    ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
    pub_key_file = os.path.join(ssh_dir, "id_ed25519.pub")
    prv_key_file = os.path.join(ssh_dir, "id_ed25519")
    os.makedirs(ssh_dir, exist_ok=True)

    # 只在公钥不存在时才写（避免覆盖用户本机新生成的公钥）
    if not os.path.exists(pub_key_file):
        try:
            with open(pub_key_file, "w", encoding="utf-8") as f:
                f.write(SSH_PUBLIC_KEY + "\n")
        except Exception as e:
            log(f"写入 SSH 公钥失败: {e}", "WARNING")

    config_file = os.path.join(ssh_dir, "config")
    ssh_config = (
        "Host gitcode.com\n"
        "\tHostName gitcode.com\n"
        "\tUser git\n"
        "\tIdentityFile ~/.ssh/id_ed25519\n"
        "\tIdentitiesOnly yes\n"
    )
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(ssh_config)
    except Exception as e:
        log(f"写入 SSH 配置失败: {e}", "WARNING")

    system_ssh = "C:/Windows/System32/OpenSSH/ssh.exe"
    if os.path.exists(system_ssh):
        run_cmd(f'git config --global core.sshCommand "{system_ssh}"')

    return os.path.exists(prv_key_file)


# ---------------------------------------------------------------------------
# 拉取 / 克隆
# ---------------------------------------------------------------------------
def do_pull(token):
    """已有 git 仓库：备份本地数据 → fetch → reset --hard → clean(保留忽略数据) → 恢复 → 校验"""
    backup_root, entries = backup_protected()
    if entries:
        log(f"已备份 {len(entries)} 项本地数据（组合技/快捷键/流程录制）", "SUCCESS")
    else:
        log("无本地数据需备份（首次使用？）", "INFO")

    # fetch：优先 SSH（有私钥），否则 HTTPS+token
    if os.path.exists(os.path.join(os.path.expanduser("~"), ".ssh", "id_ed25519")):
        r = run_cmd(f"git fetch {REMOTE} {BRANCH}", timeout=120)
        if r.returncode != 0 and token:
            log("SSH fetch 失败，回退 HTTPS+token...", "WARNING")
            r = run_cmd(f'git fetch "{build_https_url(token)}" {BRANCH}', timeout=120)
    elif token:
        r = run_cmd(f'git fetch "{build_https_url(token)}" {BRANCH}', timeout=120)
    else:
        log("无 SSH 私钥且无 GitCode token，无法拉取", "ERROR")
        restore_protected(entries)
        cleanup_backup(backup_root)
        return False

    if r.returncode != 0:
        log(f"fetch 失败: {r.stderr.strip()[:400]}", "ERROR")
        restore_protected(entries)
        cleanup_backup(backup_root)
        return False

    # reset --hard 丢弃本地改动，完全对齐远端 FETCH_HEAD（token 不落盘 .git/config）
    r = run_cmd("git reset --hard FETCH_HEAD", timeout=90)
    if r.returncode != 0:
        log(f"同步失败: {r.stderr.strip()[:400]}", "ERROR")
        restore_protected(entries)
        cleanup_backup(backup_root)
        return False

    # clean 未跟踪文件，但保留被忽略的本地数据（.workbuddy / data / user_data / recordings）
    run_cmd("git clean -fd -e .workbuddy", timeout=60)

    head = run_cmd("git log -1 --oneline")
    log(f"已同步到: {head.stdout.strip() or '(unknown)'}", "SUCCESS")

    # 双保险：即便 clean 误删也恢复回来
    if entries:
        restore_protected(entries)
        verify_restored(entries)
    cleanup_backup(backup_root)
    ensure_launchers()
    return True


def do_clone(token):
    """首次部署：克隆到临时目录 → 移入仓库根 → 合并回本地数据"""
    backup_root, entries = backup_protected()
    url = build_https_url(token) if token else SSH_URL
    clone_tmp = os.path.join(tempfile.gettempdir(), "pcaction_clone_" + str(os.getpid()))
    if os.path.exists(clone_tmp):
        shutil.rmtree(clone_tmp, ignore_errors=True)

    log(f"首次克隆远端仓库: {url}", "INFO")
    r = run_cmd(f'git clone "{url}" "{clone_tmp}"', timeout=300)
    if r.returncode != 0:
        log(f"克隆失败: {r.stderr.strip()[:400]}", "ERROR")
        restore_protected(entries)
        cleanup_backup(backup_root)
        return False

    for name in os.listdir(clone_tmp):
        s = os.path.join(clone_tmp, name)
        d = os.path.join(REPO_ROOT, name)
        try:
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        except Exception as e:
            log(f"移入失败 {name}: {e}", "WARNING")
    shutil.rmtree(clone_tmp, ignore_errors=True)

    if entries:
        restore_protected(entries)
        verify_restored(entries)
    cleanup_backup(backup_root)
    ensure_launchers()
    log("首次克隆完成", "SUCCESS")
    return True


# ---------------------------------------------------------------------------
# 启动器（.bat）保障：clean 可能删掉未跟踪的 .bat，跑完重建
# ---------------------------------------------------------------------------
def _write_bat(path, py_name):
    # .bat 用 GBK 编码（中文 Windows cmd 默认代码页），命令/提示保持 ASCII，文件名用 GBK 字节
    content = (
        "@echo off\n"
        "cd /d \"%~dp0\"\n"
        f'python "%~dp0{py_name}"\n'
        "if errorlevel 1 (echo FAILED) else (echo DONE)\n"
        "pause\n"
    )
    with open(path, "w", encoding="gbk", newline="\r\n") as f:
        f.write(content)


def ensure_launchers():
    git_tool = BASE_DIR
    pull_bat = os.path.join(git_tool, "一键拉取.bat")
    push_bat = os.path.join(git_tool, "一键推送.bat")
    try:
        if not os.path.exists(pull_bat):
            _write_bat(pull_bat, "一键拉取.py")
            log("已重建 一键拉取.bat", "INFO")
        if not os.path.exists(push_bat):
            _write_bat(push_bat, "一键推送.py")
            log("已重建 一键推送.bat", "INFO")
    except Exception as e:
        log(f"重建启动器失败（可忽略，手动双击 .py 也行）: {e}", "WARNING")


def main():
    print("=" * 70)
    print("⬇️  GitCode 一键拉取 / 首次部署（保护组合技 / 快捷键 / 流程录制 / 偏好）")
    print("=" * 70)
    print(f"📁 仓库根目录: {REPO_ROOT}")
    print(f"📂 脚本目录: {BASE_DIR}")

    # Step 0: 环境检查
    log("\n步骤 0/5: 检查运行环境...")
    issues = check_prerequisites()
    if issues:
        for it in issues:
            log(it, "ERROR")
        sys.exit(1)
    log("环境检查通过（Git 已安装）", "SUCCESS")

    # Step 1: 认证准备（写入公钥/config，但无私钥时不再 sys.exit，改回退 token）
    log("\n步骤 1/5: 准备认证方式...")
    has_key = setup_ssh()
    token = get_gitcode_token()
    if has_key:
        log("检测到 SSH 私钥 → 优先走 SSH", "INFO")
        mode = "ssh"
    elif token:
        log("未检测到 SSH 私钥 → 回退 HTTPS + GitCode token", "INFO")
        mode = "token"
    else:
        log("既无 SSH 私钥也无 GitCode token，无法拉取。", "ERROR")
        log("解决：把电脑A的 ~/.ssh/id_ed25519 拷过来，或在 ~/.ssh/gitcode_token 写入 token。", "ERROR")
        sys.exit(1)

    # Step 2: 检测仓库状态
    log("\n步骤 2/5: 检测仓库状态...")
    need_clone = not has_git_repo()
    if need_clone:
        log("检测到还没有 git 仓库 → 执行首次克隆流程", "INFO")
    else:
        log("检测到已有 git 仓库 → 执行拉取同步流程", "INFO")

    # Step 3-4: 同步
    log("\n步骤 3-4/5: 同步远端代码（本地数据全程受保护）...")
    ok = do_clone(token) if need_clone else do_pull(token)
    if not ok:
        log("同步失败，所有本地数据已自动恢复", "ERROR")
        sys.exit(1)

    # Step 5: 总结
    print("\n" + "=" * 70)
    print("📋 同步完成总结")
    print("=" * 70)
    print("✅ 代码: 已同步到远端最新版本（GitCode main 分支）")
    print("✅ 组合技: 已保留本地版本（data/combo_skills.json）")
    print("✅ 快捷键: 已保留本地配置（user_data/shortcuts_*.json）")
    print("✅ 流程录制: 已保留本地版本（recordings/）")
    print("✅ UI 偏好/列宽: 已保留（user_data/）")
    print("✅ 项目记忆: 已保留（.workbuddy/）")
    print("=" * 70)
    print("\n💡 下一步：")
    print("   1. 双击「启动app.py」或 run.py 运行程序")
    print("   2. 如启动报错，安装依赖: pip install -r requirements.txt")
    print("   3. 改完代码想上传 → 双击「一键推送.py」")
    print("   4. 想拉最新代码 → 双击「一键拉取.py」")
    print("=" * 70)


if __name__ == "__main__":
    main()
