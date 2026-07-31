import os
import shutil
import subprocess
import sys
import tempfile

BASE_DIR = r"d:\codespace"
REMOTE = "origin"
BRANCH = "main"
SSH_PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOex2p0CkIAkhA98M4KCpzxPL4hkZPfXc8D6In5gondh 1399972370@qq.com"

# 受保护的本地数据：这些文件在 .gitignore 中已忽略，但历史原因曾被 git 跟踪。
# 拉取（reset --hard）会删除"被跟踪"的文件，所以必须备份→reset→恢复，
# 让它们在每台机器上各自独立，不受远端影响。
#
# 说明：
# - recordings/ 和 *.db 数据库在 .gitignore 中且从未被跟踪，git 不会动它们，无需备份。
# - 下面的文件曾被跟踪，拉取时会被删除，所以需要保护。
PROTECTED_PATHS = [
    "01-开发项目/PC-action/PC-action-macOS/data/combo_skills.json",   # 组合技
    "01-开发项目/PC-action/PC-action-macOS/user_data",                # 快捷键、录制顺序、UI 偏好等
]


def log(msg, level="INFO"):
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "•")
    print(f"{prefix} {msg}")


def run_cmd(cmd, timeout=60):
    return subprocess.run(
        cmd, shell=True, cwd=BASE_DIR, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=timeout,
    )


def setup_ssh():
    """配置 SSH 公钥与 config，与一键推送脚本保持一致"""
    ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
    pub_key_file = os.path.join(ssh_dir, "id_ed25519.pub")
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
    system_ssh = r"C:\Windows\System32\OpenSSH\ssh.exe"
    if os.path.exists(system_ssh):
        run_cmd(f'git config core.sshCommand "{system_ssh}"')


def backup_protected():
    """备份所有受保护路径到临时目录，返回 (backup_root, [(abs_path, backup_path), ...])"""
    backup_root = tempfile.mkdtemp(prefix="pull_backup_")
    entries = []
    for rel in PROTECTED_PATHS:
        src = os.path.join(BASE_DIR, rel)
        if not os.path.exists(src):
            log(f"本地不存在，跳过备份: {rel}", "INFO")
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
    """从备份恢复受保护路径（覆盖远端拉取时可能删除的文件）"""
    for src, dst in entries:
        try:
            os.makedirs(os.path.dirname(src), exist_ok=True)
            if os.path.isdir(dst):
                # 目录：用 copytree 覆盖（dirs_exist_ok=True）
                shutil.copytree(dst, src, dirs_exist_ok=True)
            else:
                shutil.copy2(dst, src)
        except Exception as e:
            log(f"恢复失败 {src}: {e}", "WARNING")


def cleanup_backup(backup_root):
    try:
        shutil.rmtree(backup_root, ignore_errors=True)
    except Exception:
        pass


def main():
    print("=" * 70)
    print("⬇️  GitCode 一键拉取工具（保护组合技 / 快捷键 / 录制 / 偏好）")
    print("=" * 70)

    # Step 1: 配置 SSH
    log("步骤 1/4: 配置 SSH...")
    setup_ssh()
    log("SSH 配置完成", "SUCCESS")

    # Step 2: 备份受保护的本地数据
    log("\n步骤 2/4: 备份本地数据（组合技 / 快捷键 / 录制顺序 / UI 偏好）...")
    backup_root, entries = backup_protected()
    if entries:
        log(f"已备份 {len(entries)} 项本地数据", "SUCCESS")
    else:
        log("无本地数据需要备份", "INFO")

    # Step 3: 拉取远端最新代码
    log("\n步骤 3/4: 拉取远端最新代码...")
    log(f"目标: {REMOTE}/{BRANCH}", "INFO")

    r = run_cmd(f"git fetch {REMOTE} {BRANCH}", timeout=90)
    if r.returncode != 0:
        err = r.stderr.strip()
        log(f"fetch 失败: {err[:300]}", "ERROR")
        restore_protected(entries)
        log("已恢复本地数据备份", "INFO")
        cleanup_backup(backup_root)
        input("\n按 Enter 键退出...")
        sys.exit(1)

    # 用 reset --hard 同步到远端：只重置被 git 跟踪的文件
    # untracked / ignored 文件（recordings/、*.db、以及已 untrack 的本地数据）不受影响
    r = run_cmd(f"git reset --hard {REMOTE}/{BRANCH}", timeout=60)
    if r.returncode == 0:
        head = run_cmd("git log -1 --oneline")
        if head.returncode == 0:
            log(f"已同步到: {head.stdout.strip()}", "SUCCESS")
        else:
            log("代码已同步", "SUCCESS")
    else:
        err = r.stderr.strip()
        log(f"同步失败: {err[:300]}", "ERROR")
        restore_protected(entries)
        log("已恢复本地数据备份", "INFO")
        cleanup_backup(backup_root)
        input("\n按 Enter 键退出...")
        sys.exit(1)

    # Step 4: 恢复本地数据
    log("\n步骤 4/4: 恢复本地数据...")
    if entries:
        restore_protected(entries)
        log("本地数据已恢复", "SUCCESS")
    else:
        log("无备份需要恢复", "INFO")
    cleanup_backup(backup_root)

    # 总结
    print("\n" + "=" * 70)
    print("📋 拉取总结")
    print("=" * 70)
    print("✅ 代码: 已同步到远端最新版本")
    print("✅ 组合技: 已保留本地版本（data/combo_skills.json）")
    print("✅ 快捷键: 已保留本地配置（user_data/shortcuts_*.json）")
    print("✅ 录制顺序/回放位置/UI 偏好: 已保留本地版本（user_data/）")
    print("✅ 录制文件: 未受影响（recordings/ 已在 .gitignore 中忽略）")
    print("✅ 快捷键数据库: 未受影响（*.db 已在 .gitignore 中忽略）")
    print("=" * 70)
    input("\n按 Enter 键退出...")


if __name__ == "__main__":
    main()
