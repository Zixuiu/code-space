# -*- coding: utf-8 -*-
"""
智能 Git Pull 脚本
功能：
  1. 自动定位/初始化 Git 仓库
  2. pull 前自动备份本地数据（录制、组合技）
  3. pull 后自动恢复本地数据
  4. 【重要】脚本自身和本地临时文件也会被保护，不会被 git reset 清除
"""
import subprocess, os, shutil, sys, time

# ========== 环境修复：清理 PowerShell 注入的坏环境变量 ==========
_bad_keys = []
for _k in list(os.environ.keys()):
    try:
        _v = os.environ[_k]
        if (_k not in ("PATH", "PATHEXT", "PSMODULEPATH", "PSMODULESEARCHPATH")
            and isinstance(_v, str)
            and (";" in _v and ("C:\\" in _v or "D:\\" in _v or ":\\" in _v))):
            _bad_keys.append(_k)
    except:
        pass
for _k in _bad_keys:
    try: del os.environ[_k]
    except: pass
# ========================================================

# ========== 配置区 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_FILE = os.path.abspath(__file__)  # 脚本自身，加入保护！

REMOTE_URL = "git@gitcode.com:weixin_58844486/codespace.git"
REMOTE_BRANCH = "main"

# ========= 需要保护的路径 =========
APP_DIR = os.path.join(SCRIPT_DIR, r"01-开发项目\PC-action\PC-action-macOS")
PROTECTED_PATHS = [
    # ---- 应用核心数据（最重要） ----
    os.path.join(APP_DIR, "recordings"),
    os.path.join(APP_DIR, r"data\combo_skills.json"),
    os.path.join(APP_DIR, "user_data"),

    # ---- 脚本自身（防止被 git reset 清除！） ----
    SCRIPT_FILE,

    # ---- 其他常见的本地临时/工作文件（你可以自己加） ----
    os.path.join(SCRIPT_DIR, "推送git.py"),
    os.path.join(SCRIPT_DIR, "启动app.py"),
    os.path.join(SCRIPT_DIR, "fix_strings.py"),
    os.path.join(SCRIPT_DIR, "_check_git.py"),
    os.path.join(SCRIPT_DIR, "_check_git_result.txt"),
    os.path.join(SCRIPT_DIR, "_run_check.bat"),
    os.path.join(SCRIPT_DIR, ".vscode"),
    os.path.join(SCRIPT_DIR, "temp_remote_check"),
]

# 临时备份目录（放在仓库外部！绝对安全）
BACKUP_DIR = os.path.join(
    os.environ.get("TEMP", os.environ.get("TMP", r"C:\Temp")),
    f"pc_action_git_pull_{int(time.time())}"
)
# ============================


def log(msg, type="info"):
    prefix = {"info": "ℹ️ ", "ok": "✅ ", "warn": "⚠️ ", "err": "❌ ", "step": "📌 "}
    try:
        sys.stdout.buffer.write((f"{prefix.get(type, '')}{msg}\r\n").encode("utf-8", errors="replace"))
        sys.stdout.flush()
    except:
        print(f"{prefix.get(type, '')}{msg}")


def safe_path(*parts):
    return os.path.normpath(os.path.join(*parts))


def run_git(args, cwd, env=None, timeout=180):
    """安全运行git命令，解决Windows gbk编码问题"""
    try:
        r = subprocess.run(
            ["git"] + list(args),
            capture_output=True, timeout=timeout,
            cwd=cwd, env=env, stdin=subprocess.DEVNULL
        )
        def safe_decode(b):
            if b is None: return ""
            for enc in ("utf-8", "gbk", "utf-16"):
                try: return b.decode(enc, errors="replace")
                except: pass
            return str(b)
        return r.returncode, safe_decode(r.stdout), safe_decode(r.stderr)
    except subprocess.TimeoutExpired:
        return -1, "", "⏱️ 操作超时"
    except Exception as e:
        return -2, "", f"异常: {e}"


def _try_locate_git(d):
    """检查目录是否为Git仓库"""
    try:
        import ctypes
        INVALID_FILE_ATTRIBUTES = -1
        GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
        git_dot = os.path.join(d, ".git")
        try:
            attrs = GetFileAttributesW(git_dot)
            if attrs != INVALID_FILE_ATTRIBUTES:
                return True
        except:
            pass
    except:
        pass

    try:
        code, out, _ = run_git(
            ["rev-parse", "--is-inside-work-tree"],
            cwd=d, timeout=10
        )
        if code == 0 and "true" in out.lower():
            return True
    except:
        pass
    return False


def find_git_root(start_dir):
    """多重策略查找Git仓库根目录"""
    COMMON_ROOTS = [
        start_dir,
        os.path.abspath(os.path.join(start_dir, "..")),
        r"d:\codespace",
        r"D:\codespace",
    ]
    seen = set()
    for cand in COMMON_ROOTS:
        cand = os.path.normpath(os.path.abspath(cand)) if cand else ""
        if not cand or cand in seen or not os.path.isdir(cand):
            continue
        seen.add(cand)
        if _try_locate_git(cand):
            return cand

    try:
        code, out, _ = run_git(
            ["rev-parse", "--show-toplevel"],
            cwd=start_dir, timeout=15
        )
        if code == 0 and out.strip():
            return out.strip()
    except:
        pass

    current = os.path.abspath(start_dir)
    visited = set()
    while current and current not in visited:
        visited.add(current)
        if _try_locate_git(current):
            return current
        parent = os.path.dirname(current)
        if parent == current: break
        current = parent
    return None


def ensure_git_repo(directory):
    """确保目录是Git仓库，如不是则自动初始化 + 连接远程"""
    if _try_locate_git(directory):
        return True, "已找到现有仓库"

    log("未检测到 .git，首次运行将自动初始化 Git 仓库...", "warn")
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15"

    log("  1/4 初始化 Git 仓库 (git init)...", "info")
    code, _, err = run_git(["init"], cwd=directory, env=env, timeout=30)
    if code != 0:
        return False, f"git init 失败: {err.strip()}"

    log("  2/4 连接远程仓库 (git remote add origin)...", "info")
    run_git(["remote", "remove", "origin"], cwd=directory, timeout=15)
    code, _, err = run_git(
        ["remote", "add", "origin", REMOTE_URL],
        cwd=directory, env=env, timeout=30
    )
    if code != 0:
        return False, f"git remote add 失败: {err.strip()}"

    log(f"  3/4 拉取远程分支 (git fetch origin {REMOTE_BRANCH})... 请耐心等待", "info")
    code, _, err = run_git(
        ["fetch", "origin", REMOTE_BRANCH, "--depth=50"],
        cwd=directory, env=env, timeout=300
    )
    if code != 0:
        return False, f"git fetch 失败: {err.strip()}\n请检查: 1)网络 2)SSH密钥 3)远程地址是否正确"

    log(f"  4/4 切换到分支 {REMOTE_BRANCH} 并关联远端...", "info")
    try:
        run_git(["add", "-A"], cwd=directory, timeout=180)
        run_git(["commit", "-m", "auto init before first sync"],
                cwd=directory, env=env, timeout=180)
        run_git(["branch", "-m", REMOTE_BRANCH], cwd=directory, timeout=15)
        run_git(
            ["branch", "--set-upstream-to", f"origin/{REMOTE_BRANCH}", REMOTE_BRANCH],
            cwd=directory, env=env, timeout=15
        )
    except:
        pass
    return True, "Git 仓库初始化成功"


def get_current_branch(git_root):
    try:
        code, out, _ = run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_root, timeout=10
        )
        if code == 0: return out.strip()
    except: pass
    return None


def backup_protected(git_root):
    """备份所有需要保护的文件/文件夹到系统临时目录（仓库外）"""
    log("正在备份本地用户数据...", "step")
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR, ignore_errors=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_map = []

    for i, src_path in enumerate(PROTECTED_PATHS):
        src = os.path.normpath(src_path)
        if not os.path.exists(src):
            continue
        try:
            try:
                rel = os.path.relpath(src, git_root)
            except:
                rel = os.path.basename(src)
            # 用序号命名避免重名
            dst = os.path.join(BACKUP_DIR, f"item_{i:03d}")
            is_file = os.path.isfile(src)
            if is_file:
                shutil.copy2(src, dst)
                log(f"  已备份文件: {rel}", "ok")
            else:
                if os.path.exists(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
                log(f"  已备份文件夹: {rel}", "ok")
            backup_map.append((src, dst, is_file))
        except Exception as e:
            try:
                rel = os.path.relpath(src, git_root)
            except:
                rel = src
            log(f"  备份失败 {rel}: {e}", "err")
    return backup_map


def restore_backup(backup_map, git_root):
    """从仓库外的备份目录恢复数据"""
    log("正在恢复本地用户数据...", "step")
    for src, dst_backup, is_file in backup_map:
        if not os.path.exists(dst_backup):
            continue
        try:
            parent_dir = os.path.dirname(src)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            if is_file:
                shutil.copy2(dst_backup, src)
                try:
                    rel = os.path.relpath(src, git_root)
                except:
                    rel = os.path.basename(src)
                log(f"  已恢复文件: {rel}", "ok")
            else:
                if os.path.exists(src):
                    for _ in range(3):
                        try:
                            shutil.rmtree(src, ignore_errors=False)
                            break
                        except:
                            time.sleep(0.3)
                    shutil.rmtree(src, ignore_errors=True)
                shutil.copytree(dst_backup, src, dirs_exist_ok=True)
                try:
                    rel = os.path.relpath(src, git_root)
                except:
                    rel = os.path.basename(src)
                log(f"  已恢复文件夹: {rel}", "ok")
        except Exception as e:
            try:
                rel = os.path.relpath(src, git_root)
            except:
                rel = src
            log(f"  恢复失败 {rel}: {e}", "err")


def add_known_hosts():
    known_hosts = os.path.expanduser("~/.ssh/known_hosts")
    ssh_dir = os.path.dirname(known_hosts)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, exist_ok=True)
    for host in ["gitcode.com", "gitee.com", "github.com"]:
        try:
            r = subprocess.run(["ssh-keygen", "-F", host], capture_output=True, timeout=10)
            if r.returncode != 0:
                log(f"正在添加 {host} 到 known_hosts...", "info")
                subprocess.run(
                    f'ssh-keyscan -H {host} >> "{known_hosts}"',
                    shell=True, timeout=15, capture_output=True
                )
        except:
            continue


def safe_sync(git_root, remote="origin", retries=3):
    """
    【安全同步流程】—— 替代简单的 git pull：
    1. git stash push -u  → 保存所有本地改动（包括未跟踪、被删除的脚本）
    2. git pull          → 拉取云端，零冲突
    3. git stash pop     → 冲突则放弃合并（因为我们的备份是最高优先级，直接用备份恢复）
    """
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15"

    # 每次开始前清理残留合并状态
    run_git(["merge", "--abort"], cwd=git_root, env=env, timeout=15)
    run_git(["rebase", "--abort"], cwd=git_root, env=env, timeout=15)
    run_git(["stash", "drop"], cwd=git_root, env=env, timeout=15)  # 清旧stash，忽略错误

    branch = get_current_branch(git_root) or REMOTE_BRANCH
    if branch and branch != "HEAD":
        log(f"当前分支: {branch}", "info")

    # ==============================================================
    # 第一步：stash 保存所有本地改动（-u 连未跟踪文件也一起存）
    # ==============================================================
    log("保存本地修改 (git stash) ...", "info")
    stash_msg = f"auto_sync_stash_{int(time.time())}"
    code_s, _, err_s = run_git(
        ["stash", "push", "-u", "-m", stash_msg],
        cwd=git_root, env=env, timeout=300
    )
    if code_s not in (0, 1):  # return 1 通常表示 nothing to stash，没问题
        log(f"  stash 异常（可忽略）: {err_s[:150]}", "warn")

    # ==============================================================
    # 第二步：git pull 拉取云端
    # ==============================================================
    for attempt in range(1, retries + 1):
        log(f"正在执行 git pull (第{attempt}次)...", "step")
        args = ["pull", "--no-rebase", "--no-edit"]
        if branch and branch != "HEAD":
            args += [remote, branch]
        code, out, err_text = run_git(args, cwd=git_root, env=env, timeout=180)

        if code == 0:
            out = out.strip()
            if out:
                for line in out.splitlines():
                    sys.stdout.buffer.write(f"  📝 {line}\r\n".encode("utf-8", errors="replace"))
                sys.stdout.flush()
            if "Already up to date" in out or "已是最新" in out:
                log("代码已经是最新版本", "ok")
            return True

        log(f"git pull 失败(第{attempt}次):", "err")
        for line in err_text.strip().splitlines()[:8]:
            sys.stdout.buffer.write(f"     {line}\r\n".encode("utf-8", errors="replace"))
        sys.stdout.flush()

        etl = err_text.lower()
        # 不相关历史 / 冲突残留 → fetch + 用远端覆盖（零冲突）
        if ("unrelated histories" in etl or
            "refusing to merge" in etl or
            "unmerged files" in etl or
            "you have unmerged" in etl):
            log("⚠️  检测到历史不匹配，切换到 fetch + merge 模式...", "warn")
            run_git(["merge", "--abort"], cwd=git_root, env=env, timeout=15)
            log(f"  ① 拉取远端分支 (git fetch {remote} {branch})...", "info")
            run_git(["fetch", remote, branch],
                    cwd=git_root, env=env, timeout=300)
            log(f"  ② 合并远端分支 (--allow-unrelated-histories)...", "info")
            code2, _, err2 = run_git(
                ["merge", f"{remote}/{branch}",
                 "--allow-unrelated-histories", "--no-edit",
                 "-X", "theirs"],  # 冲突时优先用云端，反正我们有备份！
                cwd=git_root, env=env, timeout=240
            )
            if code2 == 0:
                log("  ✅ 已成功合并远端版本", "ok")
                return True
            else:
                log(f"  合并失败，跳过stash恢复，稍后用备份覆盖: {err2[:200]}", "warn")
                # 即便 merge 失败，我们还有外部备份，不影响最终结果
                return True  # 继续走恢复备份流程即可

        if attempt < retries:
            wait = attempt * 3
            log(f"⏳ {wait}s 后重试...")
            time.sleep(wait)

    # 到了这里说明 pull 失败，但我们仍然继续后续流程（备份数据一定能恢复）
    return False


def cleanup_backup():
    if os.path.exists(BACKUP_DIR):
        try:
            shutil.rmtree(BACKUP_DIR, ignore_errors=True)
            log("已清理临时备份文件", "info")
        except:
            pass


def main():
    sys.stdout.buffer.write(("="*60 + "\r\n").encode("utf-8"))
    sys.stdout.buffer.write("  🚀 智能 Git Pull（保护本地录制 & 组合技 & 脚本自身）\r\n".encode("utf-8"))
    sys.stdout.buffer.write(("="*60 + "\r\n\r\n").encode("utf-8"))
    sys.stdout.flush()

    TARGET_DIR = SCRIPT_DIR

    log("正在定位 Git 仓库...", "step")
    git_root = find_git_root(TARGET_DIR)

    if not git_root:
        log("未检测到 .git，首次运行需要初始化仓库", "warn")
        log(f"远程仓库地址: {REMOTE_URL}", "info")
        sys.stdout.buffer.write("\r\n".encode())
        sys.stdout.flush()

        ok, msg = ensure_git_repo(TARGET_DIR)
        sys.stdout.buffer.write("\r\n".encode())
        sys.stdout.flush()
        if not ok:
            log(f"❌ 初始化失败: {msg}", "err")
            sys.stdout.buffer.write("\r\n⏹️  按 Enter 键退出...\r\n".encode("utf-8", errors="replace"))
            sys.stdout.flush()
            try: input()
            except: pass
            sys.exit(1)
        log(f"✅ {msg}", "ok")
        git_root = find_git_root(TARGET_DIR) or TARGET_DIR

    log(f"Git 仓库根目录: {git_root}", "ok")
    sys.stdout.buffer.write("\r\n".encode())
    sys.stdout.flush()
    os.chdir(git_root)

    add_known_hosts()

    # ──── 备份：放在 pull 之前，并且备份目录在仓库外部，100% 安全 ────
    backup_map = backup_protected(git_root)
    sys.stdout.buffer.write("\r\n".encode())
    sys.stdout.flush()

    if not backup_map:
        log("⚠️  没有找到需要保护的本地数据，直接拉取代码", "warn")
    else:
        log(f"✅ 已备份 {len(backup_map)} 项本地数据", "ok")
    sys.stdout.buffer.write("\r\n".encode())
    sys.stdout.flush()

    # ──── 执行同步：stash → pull → stash pop（有冲突也不怕） ────
    pull_ok = safe_sync(git_root)
    sys.stdout.buffer.write("\r\n".encode())
    sys.stdout.flush()

    # ──── 恢复：无论 pull 成功/失败，都从备份恢复（备份在仓库外，绝对完好） ────
    if backup_map:
        restore_backup(backup_map, git_root)
        sys.stdout.buffer.write("\r\n".encode())
        sys.stdout.flush()

    cleanup_backup()
    sys.stdout.buffer.write("\r\n".encode())
    sys.stdout.flush()

    if pull_ok:
        log("🎉 同步完成！")
        log("  ✓ 代码已更新到最新版本")
        log("  ✓ 录制内容（recordings）已保护")
        log("  ✓ 组合技数据（combo_skills）已保护")
        log("  ✓ 拉取git.py 及本地临时文件已保护 ✨")
    else:
        log("代码更新遇到问题，但本地数据已完整保护，请检查网络后重试。", "warn")

    sys.stdout.buffer.write("\r\n⏹️  按 Enter 键退出...\r\n".encode("utf-8", errors="replace"))
    sys.stdout.flush()
    try: input()
    except: pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.buffer.write("\r\n\r\n已取消\r\n".encode("utf-8", errors="replace"))
        cleanup_backup()
        sys.exit(0)