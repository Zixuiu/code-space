import os
import subprocess
import sys
import datetime

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

# 动态 BASE_DIR：脚本所在目录即项目根（不再写死 d:\codespace，新电脑任意路径可跑）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SSH_PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOex2p0CkIAkhA98M4KCpzxPL4hkZPfXc8D6In5gondh 1399972370@qq.com"
SSH_URL = "git@gitcode.com:weixin_58844486/codespace.git"

def log(msg, level="INFO"):
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "•")
    print(f"{prefix} {msg}")

def run_cmd(cmd, cwd=None, timeout=30):
    r = subprocess.run(cmd, shell=True, cwd=cwd or BASE_DIR,
                       capture_output=True, text=True,
                       encoding='utf-8', errors='replace',
                       timeout=timeout)
    return r

def setup_ssh_and_check():
    """
    写公钥 + ssh config + git sshCommand；
    检查私钥 id_ed25519 是否存在——缺失时给出明确指引（从能推送的电脑拷过来）；
    存在再做一次 SSH 认证测试。
    返回 True/False
    """
    ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
    pub_key_file = os.path.join(ssh_dir, "id_ed25519.pub")
    prv_key_file = os.path.join(ssh_dir, "id_ed25519")
    os.makedirs(ssh_dir, exist_ok=True)

    try:
        with open(pub_key_file, 'w', encoding='utf-8') as f:
            f.write(SSH_PUBLIC_KEY + '\n')
        with open(pub_key_file, 'r', encoding='utf-8') as f:
            if f.read().strip() == SSH_PUBLIC_KEY:
                log(f"公钥已写入: {pub_key_file}", "SUCCESS")
    except Exception as e:
        log(f"写入公钥失败: {e}", "ERROR")

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
        log(f"SSH 配置已写入: {config_file}", "SUCCESS")
    except Exception as e:
        log(f"写入SSH配置失败: {e}", "ERROR")

    system_ssh = "C:/Windows/System32/OpenSSH/ssh.exe"
    if os.path.exists(system_ssh):
        run_cmd(f'git config core.sshCommand "{system_ssh}"')
        log("git 已配置使用系统 ssh", "INFO")

    # 缺私钥
    if not os.path.exists(prv_key_file):
        log("SSH 私钥缺失（~/.ssh/id_ed25519 不存在），无法推送", "ERROR")
        print("=" * 60)
        print("操作方法（把能正常推送代码那台电脑的私钥拷过来）：")
        print("-" * 60)
        print(f"1. 在【电脑A】（能正常 git push 的那台）上找到文件:")
        print(f"   C:\\Users\\你的用户名\\.ssh\\id_ed25519")
        print(f"   （例：C:\\Users\\INK\\.ssh\\id_ed25519）")
        print()
        print(f"2. 把这个文件复制到【电脑B】的:")
        print(f"   {prv_key_file}")
        print()
        print(f"3. 复制完成后，重新双击运行本脚本即可。")
        print("-" * 60)
        print("私钥是敏感文件，不要发到公共渠道或上传到任何地方。")
        print("=" * 60)
        return False, pub_key_file, config_file

    # 有私钥，做一次 SSH 认证测试
    r = run_cmd("ssh -o StrictHostKeyChecking=no -T git@gitcode.com", timeout=20)
    out = (r.stdout or "") + (r.stderr or "")
    if "permission denied" in out.lower() or "publickey" in out.lower():
        log("SSH 认证失败：GitCode 上还没添加公钥，或私钥与公钥不匹配", "ERROR")
        print("=" * 60)
        print("两种情况分别处理：")
        print("-" * 60)
        print("A) GitCode 上从没加过这把公钥：")
        print(f"  1) 打开: https://gitcode.com/-/user_settings/keys")
        print(f"  2) 粘贴这把公钥:")
        print(SSH_PUBLIC_KEY)
        print(f"  3) 标题随便填（如 PC-action），保存后重跑脚本。")
        print()
        print("B) 已经加过公钥仍失败：")
        print("  → 私钥与公钥不配对，重新从电脑A拷 id_ed25519 覆盖即可。")
        print("=" * 60)
        return False, pub_key_file, config_file
    return True, pub_key_file, config_file


def main():
    print("=" * 70)
    print("🚀 GitCode 一键推送工具（保护本地组合技/快捷键/录制数据不被上传）")
    print("=" * 70)
    print(f"📁 工作目录: {BASE_DIR}")

    # Step 1+2: 配置 SSH 并检查私钥 + 认证
    log("\n步骤 1-2/5: 配置 SSH 公钥 / 私钥 / 客户端...")
    ssh_ok, pub_key_file, config_file = setup_ssh_and_check()
    if not ssh_ok:
        input("\n按 Enter 退出...")
        sys.exit(1)
    log("SSH 配置完成，认证通过", "SUCCESS")

    # Step 3: 检查 Git 状态
    log("\n步骤 3/5: 检查 Git 状态...")
    r = run_cmd("git status --short")
    if r.returncode == 0:
        if not r.stdout.strip():
            log("工作区干净，无需提交", "INFO")
        else:
            files = [line.strip() for line in r.stdout.split('\n') if line.strip()]
            log(f"有 {len(files)} 个文件需要提交:", "INFO")
            for f in files[:10]:
                print(f"   - {f}")
            if len(files) > 10:
                print(f"   ... 还有 {len(files)-10} 个文件")

            log("正在添加所有文件...", "INFO")
            run_cmd("git add .")

            commit_msg = f"auto push {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            r = run_cmd(f'git commit -m "{commit_msg}"')
            if r.returncode == 0:
                log("文件已提交", "SUCCESS")
            else:
                log("提交失败（可能没有更改）", "WARNING")
    else:
        log("无法获取 Git 状态", "ERROR")

    # Step 4: 设置远程仓库为 SSH
    log("\n步骤 4/5: 配置远程仓库为 SSH 协议...")
    r = run_cmd(f'git remote set-url origin "{SSH_URL}"')
    if r.returncode == 0:
        log(f"远程仓库已设置为: {SSH_URL}", "SUCCESS")
    else:
        log(f"设置失败: {r.stderr}", "ERROR")
    r = run_cmd("git remote -v")
    if r.returncode == 0 and SSH_URL in r.stdout:
        for line in r.stdout.strip().split('\n'):
            if 'origin' in line:
                print(f"   {line.strip()}")

    # Step 5: 推送代码
    log("\n步骤 5/5: 推送到 GitCode (SSH)...")
    log("这可能需要几秒钟...", "INFO")
    r = run_cmd("git push -u origin main", timeout=90)

    if r.returncode == 0:
        log("🎉 推送成功！代码已上传到 GitCode！", "SUCCESS")
    elif "successfully authenticated" in r.stdout.lower() or "welcome" in r.stdout.lower():
        log("✅ 认证成功，但可能已有更新", "SUCCESS")
    elif "permission denied" in r.stderr.lower() or "publickey" in r.stderr.lower():
        log("SSH 认证失败（具体原因请见上方步骤 1-2 的诊断）", "ERROR")
    else:
        err_lines = [l for l in r.stderr.split('\n')
                     if not any(x in l for x in ['SAFE_RM', 'otFound', '无法将', 'NotFound',
                                                  '所在位置', 'CategoryInfo', 'FullyQualifiedErrorId'])]
        clean_err = '\n'.join(err_lines).strip()
        if clean_err:
            log(f"推送结果: {clean_err[:400]}", "WARNING")
        else:
            log(f"返回码: {r.returncode}，请检查网络连接", "WARNING")

    # 摘要
    print("\n" + "=" * 70)
    print("📋 操作总结")
    print("=" * 70)
    print(f"✅ SSH 公钥: {pub_key_file}")
    print(f"✅ SSH 配置: {config_file}")
    print(f"✅ 项目目录: {BASE_DIR}")
    print(f"✅ 远程仓库: {SSH_URL}")
    print(f"ℹ️  注意: 本地组合技、快捷键、录制文件夹、*.db 数据库不会被推送（已受保护）")
    print("=" * 70)
    input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()
