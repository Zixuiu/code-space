import os
import shutil
import subprocess
import sys
import tempfile
#mother fucker
# 修复 Windows PowerShell/cmd 下 emoji/中文乱码
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

# 动态获取当前脚本所在目录作为 BASE_DIR，避免写死 d:\codespace
# 新电脑放到任意路径都能直接跑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REMOTE = "origin"
BRANCH = "main"
SSH_URL = "git@gitcode.com:weixin_58844486/codespace.git"
SSH_PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOex2p0CkIAkhA98M4KCpzxPL4hkZPfXc8D6In5gondh 1399972370@qq.com"

# 受保护的本地数据：每台机器独立，不跟远端走。
# 说明：
# - do_pull 场景（已有 .git 仓库）：recordings/ 和 *.db 在 .gitignore 中未被跟踪，reset 不影响它们。
# - do_clone 场景（首次克隆）：clone 需要搬空目录再下载，所以这些"本地数据"必须搬完再合并回来，否则会丢。
#   因此把它们统一列在保护清单中。
# 重要：扫描范围严格限制在 APP_DIR（PC-action-macOS 应用目录）下，避免误备份
#       其他项目（如 go-music-dl/webview 的浏览器数据库）或测试副本目录的数据。
APP_DIR = "01-开发项目/PC-action/PC-action-macOS"
PROTECTED_EXPLICIT = [
    f"{APP_DIR}/data/combo_skills.json",  # 组合技
    f"{APP_DIR}/user_data",               # 快捷键、录制顺序、UI 偏好等
    f"{APP_DIR}/recordings",              # 录制文件夹
]
# 只在 APP_DIR 下扫描 *.db（避免误备份其他项目的数据库）
PROTECTED_PATTERNS = [f"{APP_DIR}/*.db"]
# 排除规则：路径中包含这些关键词的视为测试副本/临时目录，不备份
EXCLUDE_KEYWORDS = ("_backup", "backup_", "_test", "test_", "temp_", "_temp",
                    "_copy", "copy_", "_old", "old_", "_bak", "bak_")


def _is_excluded_path(rel_path):
    """路径中包含测试副本/临时目录关键词时返回 True（不备份）"""
    norm = rel_path.replace("\\", "/").lower()
    return any(kw in norm for kw in EXCLUDE_KEYWORDS)


def collect_protected_paths(base=None):
    """返回相对于 base 的受保护路径列表。
    只在 APP_DIR 下扫描 *.db，避免误备份其他项目（go-music-dl 等）的数据；
    同时排除明显是测试副本/临时目录的路径。
    """
    import glob as glob_mod
    base = base or BASE_DIR
    found = []
    for rel in PROTECTED_EXPLICIT:
        if _is_excluded_path(rel):
            continue
        found.append(rel)
    for pat in PROTECTED_PATTERNS:
        # 路径分隔符在 Windows 上要替换
        pat_full = os.path.join(base, pat.replace("/", os.sep))
        for m in glob_mod.glob(pat_full):
            rel = os.path.relpath(m, base)
            if _is_excluded_path(rel):
                continue
            if rel not in found and os.path.exists(m):
                found.append(rel)
    return found


def log(msg, level="INFO"):
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "•")
    print(f"{prefix} {msg}")


def run_cmd(cmd, cwd=None, timeout=60):
    return subprocess.run(
        cmd, shell=True, cwd=cwd or BASE_DIR, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=timeout,
    )


def check_prerequisites():
    """检查新电脑是否已装 Python 和 Git"""
    issues = []
    # Python 本身（我们在运行所以肯定在）
    r = run_cmd("git --version")
    if r.returncode != 0:
        issues.append("Git 未安装或不在 PATH 中。请先装 Git：https://git-scm.com/download/win")
    return issues


def setup_ssh():
    """
    配置 SSH：
    - 私钥 id_ed25519 **绝不能硬编码在脚本里**（安全），必须由用户从已配置的电脑手动拷过来。
    - 公钥 id_ed25519.pub 脚本里有，写入即可。
    - SSH config / git sshCommand 正常写入。
    认证失败时，先判断缺私钥还是缺公钥，给出对应指引。
    """
    ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
    pub_key_file = os.path.join(ssh_dir, "id_ed25519.pub")
    prv_key_file = os.path.join(ssh_dir, "id_ed25519")
    os.makedirs(ssh_dir, exist_ok=True)

    try:
        with open(pub_key_file, 'w', encoding='utf-8') as f:
            f.write(SSH_PUBLIC_KEY + '\n')
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
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(ssh_config)
    except Exception as e:
        log(f"写入 SSH 配置失败: {e}", "WARNING")

    # 配置 git 使用系统 OpenSSH（Git 自带 ssh 可能认证失败）
    system_ssh = "C:/Windows/System32/OpenSSH/ssh.exe"
    if os.path.exists(system_ssh):
        r = run_cmd(f'git config --global core.sshCommand "{system_ssh}"')
        if r.returncode == 0:
            log("git 已配置使用系统 ssh", "INFO")

    # 先检查私钥是否存在——没私钥 100% 认证失败
    if not os.path.exists(prv_key_file):
        log("SSH 私钥缺失（~/.ssh/id_ed25519 不存在）", "ERROR")
        print("=" * 60)
        print("操作方法（把能正常推送代码那台电脑的私钥拷过来）：")
        print("-" * 60)
        print(f"1. 在【电脑A】（能正常 git push 的那台）上找到文件:")
        print(f"   C:\\Users\\你的用户名\\.ssh\\id_ed25519")
        print(f"   （例：C:\\Users\\INK\\.ssh\\id_ed25519）")
        print()
        print(f"2. 把这个文件用 U盘/微信 复制到【电脑B】的:")
        print(f"   {prv_key_file}")
        print(f"   （~ 就是 C:\\Users\\你的用户名）")
        print()
        print(f"3. 复制完成后，重新双击运行本脚本即可。")
        print("-" * 60)
        print("注意：只需要复制 id_ed25519，不要复制 id_ed25519.pub（脚本会自动写）。")
        print("私钥是敏感文件，不要发到公共渠道或上传到任何地方。")
        print("=" * 60)
        return False

    # 有私钥才去做真正的 SSH 认证测试
    r = run_cmd("ssh -o StrictHostKeyChecking=no -T git@gitcode.com", timeout=20)
    out = (r.stdout or "") + (r.stderr or "")
    if "permission denied" in out.lower() or "publickey" in out.lower():
        log("SSH 认证失败：GitCode 上还没添加公钥，或私钥与公钥不匹配", "ERROR")
        print("=" * 60)
        print("两种情况分别处理：")
        print("-" * 60)
        print("A) 如果 GitCode 上从没加过这把公钥：")
        print(f"  1) 打开: https://gitcode.com/-/user_settings/keys")
        print(f"  2) 粘贴这把公钥:")
        print(SSH_PUBLIC_KEY)
        print(f"  3) 标题随便填（如 PC-action），保存后重跑脚本。")
        print()
        print("B) 如果 GitCode 上已经加过公钥，仍失败：")
        print("  → 说明电脑B这把私钥和公钥不配对，重新从电脑A拷 id_ed25519 覆盖即可。")
        print("=" * 60)
        return False
    return True


def has_git_repo():
    return os.path.isdir(os.path.join(BASE_DIR, ".git"))


def has_any_files():
    """BASE_DIR 是否已有任意文件（非空目录），用于判断场景B"""
    for name in os.listdir(BASE_DIR):
        # 忽略自身脚本
        if name == os.path.basename(__file__):
            continue
        return True
    return False


def backup_protected():
    """备份受保护路径到临时目录，返回 (backup_root, [(abs_path, backup_path), ...])"""
    backup_root = tempfile.mkdtemp(prefix="pull_backup_")
    entries = []
    paths = collect_protected_paths()
    for rel in paths:
        src = os.path.join(BASE_DIR, rel)
        if not os.path.exists(src):
            continue
        dst = os.path.join(backup_root, rel.replace(os.sep, "_"))
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        entries.append((src, dst))
        log(f"已备份: {rel}", "INFO")
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


def cleanup_backup(backup_root):
    shutil.rmtree(backup_root, ignore_errors=True)


def move_existing_files_to_temp_for_clone():
    """
    场景B：BASE_DIR 不是 git 仓库但已有文件（旧代码拷过来的、或只有一键拉取.py）。
    clone 必须到空目录，所以把现有文件先搬到临时目录，clone 完后再对受保护数据做合并。
    返回 (temp_dir, moved_count, moved_root_abs)
    """
    tmp = tempfile.mkdtemp(prefix="pull_move_")
    count = 0
    for name in os.listdir(BASE_DIR):
        src = os.path.join(BASE_DIR, name)
        dst = os.path.join(tmp, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
            shutil.rmtree(src)
        else:
            shutil.copy2(src, dst)
            os.remove(src)
        count += 1
    log(f"已将 {count} 项现有文件暂时挪到临时目录（clone 后会合并回本地数据）", "INFO")
    return tmp, count


def merge_moved_back(tmp_dir):
    """
    clone 完成后把临时目录里的本地数据合并回来：
    - 只合并受保护路径（保留用户自己的本地快捷键/组合技/recordings/db）
    - 其他文件以 clone 的远端代码为准（不恢复旧代码文件，避免覆盖新版本）
    """
    merged = 0
    paths = collect_protected_paths(tmp_dir)
    for rel in paths:
        src = os.path.join(tmp_dir, rel)
        if not os.path.exists(src):
            continue
        dst = os.path.join(BASE_DIR, rel)
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            merged += 1
            log(f"已合并回本地数据: {rel}", "INFO")
        except Exception as e:
            log(f"合并回 {rel} 失败: {e}", "WARNING")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return merged


def do_clone():
    """
    首次在空目录 clone 远端仓库。
    场景 A：BASE_DIR 为空 → 直接 clone
    场景 B：BASE_DIR 有旧文件 → 先搬空 → clone → 合并回受保护的本地数据
    """
    moved_tmp = None
    backup_entries = []

    # 先备份当前受保护数据（搬空后也还在 moved_tmp 里，但双保险）
    backup_root, backup_entries = backup_protected()

    if has_any_files():
        # 场景 B：已有文件，先搬空
        moved_tmp, moved_n = move_existing_files_to_temp_for_clone()

    log(f"首次克隆远端仓库: {SSH_URL}", "INFO")
    # 克隆到临时子目录再移出来（避免 clone 时要求目录必须不存在）
    clone_tmp = os.path.join(BASE_DIR, "_clone_tmp_" + str(os.getpid()))
    try:
        r = run_cmd(f'git clone "{SSH_URL}" "{clone_tmp}"', cwd=BASE_DIR, timeout=180)
        if r.returncode != 0:
            err = r.stderr.strip()
            log(f"克隆失败: {err[:400]}", "ERROR")
            # 回滚：把 move 走的文件搬回来
            if moved_tmp:
                for name in os.listdir(moved_tmp):
                    s = os.path.join(moved_tmp, name)
                    d = os.path.join(BASE_DIR, name)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
                shutil.rmtree(moved_tmp, ignore_errors=True)
            restore_protected(backup_entries)
            cleanup_backup(backup_root)
            return False

        # 把 clone 出的内容移到 BASE_DIR 根
        for name in os.listdir(clone_tmp):
            s = os.path.join(clone_tmp, name)
            d = os.path.join(BASE_DIR, name)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        # 清理 clone_tmp 中的 .git（上面已经复制过去，再覆盖整个 .git 避免合并问题）
        shutil.rmtree(clone_tmp, ignore_errors=True)

        # clone 完后，远端清了 combo_skills.json 和 user_data 的跟踪，
        # 所以 clone 出来的目录里这两个路径是空/缺的。需要把用户原来的本地数据合并回来。
        if moved_tmp:
            merge_moved_back(moved_tmp)
        else:
            # 场景 A 空白目录：没有本地数据要恢复
            pass

        # 双保险：用备份再覆盖一次（以防 moved_tmp 的合并没覆盖到）
        restore_protected(backup_entries)
        log("首次克隆完成", "SUCCESS")

        # 初始化 git 仓库级 sshCommand（全局已设过，再补一次仓库级更保险）
        system_ssh = "C:/Windows/System32/OpenSSH/ssh.exe"
        if os.path.exists(system_ssh):
            run_cmd(f'git config core.sshCommand "{system_ssh}"')
        return True
    finally:
        shutil.rmtree(clone_tmp, ignore_errors=True)
        cleanup_backup(backup_root)


def do_pull():
    """已有 git 仓库：fetch + reset --hard，覆盖本地所有改动，仅保留受保护数据"""
    backup_root, entries = backup_protected()
    if entries:
        log(f"已备份 {len(entries)} 项本地数据", "SUCCESS")
    else:
        log("无本地数据需要备份（首次使用？）", "INFO")

    log(f"目标: {REMOTE}/{BRANCH}", "INFO")
    r = run_cmd(f"git fetch {REMOTE} {BRANCH}", timeout=120)
    if r.returncode != 0:
        err = r.stderr.strip()
        log(f"fetch 失败: {err[:400]}", "ERROR")
        restore_protected(entries)
        cleanup_backup(backup_root)
        return False

    # reset --hard 丢弃所有本地改动，完全对齐远端（保护数据已备份，之后恢复）
    r = run_cmd(f"git reset --hard {REMOTE}/{BRANCH}", timeout=90)
    if r.returncode != 0:
        err = r.stderr.strip()
        log(f"同步失败: {err[:400]}", "ERROR")
        restore_protected(entries)
        cleanup_backup(backup_root)
        return False

    head = run_cmd("git log -1 --oneline")
    log(f"已同步到: {head.stdout.strip() or '(unknown)'}", "SUCCESS")

    # 恢复本地受保护数据
    if entries:
        restore_protected(entries)
        log("本地数据已恢复", "SUCCESS")
    cleanup_backup(backup_root)
    return True


def main():
    print("=" * 70)
    print("⬇️  GitCode 一键拉取 / 首次部署（保护组合技 / 快捷键 / 录制 / 偏好）")
    print("=" * 70)
    print(f"📁 工作目录: {BASE_DIR}")

    # Step 0: 环境检查
    log("\n步骤 0/5: 检查运行环境...")
    issues = check_prerequisites()
    if issues:
        for it in issues:
            log(it, "ERROR")
        input("\n按 Enter 退出...")
        sys.exit(1)
    log("环境检查通过（Git 已安装）", "SUCCESS")

    # Step 1: 配置 SSH
    log("\n步骤 1/5: 配置 SSH...")
    ssh_ok = setup_ssh()
    if not ssh_ok:
        log("SSH 认证失败（见上方提示），请先到 GitCode 添加公钥后再运行", "ERROR")
        input("\n按 Enter 退出...")
        sys.exit(1)
    log("SSH 配置完成", "SUCCESS")

    # Step 2: 根据目录情况自动选择 clone 或 pull
    log("\n步骤 2/5: 检测仓库状态...")
    need_clone = not has_git_repo()
    if need_clone:
        log("检测到还没有 git 仓库 → 执行首次克隆流程", "INFO")
    else:
        log("检测到已有 git 仓库 → 执行拉取同步流程", "INFO")

    # Step 3-4: 同步远端代码
    log("\n步骤 3-4/5: 同步远端代码...")
    if need_clone:
        ok = do_clone()
    else:
        ok = do_pull()

    if not ok:
        log("同步失败，所有本地数据已自动恢复", "ERROR")
        input("\n按 Enter 退出...")
        sys.exit(1)

    # Step 5: 总结
    print("\n" + "=" * 70)
    print("📋 同步完成总结")
    print("=" * 70)
    print("✅ 代码: 已同步到远端最新版本（GitCode main 分支）")
    print("✅ 组合技: 已保留本地版本（data/combo_skills.json）")
    print("✅ 快捷键: 已保留本地配置（user_data/shortcuts_*.json）")
    print("✅ 录制顺序/回放位置/UI 偏好: 已保留本地版本（user_data/）")
    print("✅ 录制文件夹: 未受影响（recordings/ 已忽略）")
    print("✅ 快捷键数据库: 未受影响（*.db 已忽略）")
    print("=" * 70)
    print("\n💡 下一步：")
    print("   1. 双击「启动app.py」运行程序")
    print("   2. 如启动报错，安装依赖: pip install -r requirements.txt")
    print("   3. 改完代码想上传 → 双击「一键推送.py」")
    print("   4. 想拉最新代码 → 双击「一键拉取.py」")
    print("=" * 70)
    input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()
