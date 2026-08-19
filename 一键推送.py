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
        log("SSH 私钥缺失（~/.ssh/id_ed25519 不存在），自动回退 HTTPS+token 推送", "WARNING")
        return False, pub_key_file, config_file

    # 有私钥，做一次 SSH 认证测试
    r = run_cmd("ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -T git@gitcode.com", timeout=8)
    out = (r.stdout or "") + (r.stderr or "")
    if "permission denied" in out.lower() or "publickey" in out.lower():
        log("SSH 认证失败（公钥未登记或与私钥不匹配），自动回退 HTTPS+token 推送", "WARNING")
        return False, pub_key_file, config_file
    return True, pub_key_file, config_file


def get_gitcode_token():
    """读取 GitCode personal access token：优先级 环境变量 GITCODE_TOKEN > 本地文件 ~/.ssh/gitcode_token（不入库）"""
    env_tok = os.environ.get("GITCODE_TOKEN", "").strip()
    if env_tok:
        return env_tok
    tok_file = os.path.join(os.path.expanduser("~"), ".ssh", "gitcode_token")
    try:
        if os.path.exists(tok_file):
            with open(tok_file, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return None


def push_via_token():
    """HTTPS + personal access token 推送；token 仅在本次命令的 URL 中，不写入 git config"""
    token = get_gitcode_token()
    if not token:
        log("未找到 GitCode token：请设置环境变量 GITCODE_TOKEN，或在 ~/.ssh/gitcode_token 写入 token", "ERROR")
        return False
    os.environ['GIT_TERMINAL_PROMPT'] = '0'
    https_url = f"https://oauth2:{token}@gitcode.com/weixin_58844486/codespace.git"
    log("使用 HTTPS + token 方式推送（token 不写入本地配置）...", "INFO")
    r = run_cmd(f'git -c credential.helper= push "{https_url}" HEAD:main', timeout=90)
    if r.returncode == 0:
        log("🎉 推送成功（HTTPS + token）！代码已上传到 GitCode！", "SUCCESS")
        return True
    err = (r.stdout or "") + (r.stderr or "")
    if "permission denied" in err.lower() or "401" in err or "403" in err:
        log("Token 认证失败：请检查 token 是否有效、是否有 write_repository 权限", "ERROR")
    else:
        err_lines = [l for l in err.split('\n')
                     if not any(x in l for x in ['SAFE_RM', 'otFound', '无法将', 'NotFound',
                                                  '所在位置', 'CategoryInfo', 'FullyQualifiedErrorId'])]
        clean_err = '\n'.join(err_lines).strip()
        log(f"HTTPS 推送失败: {clean_err[:400] or ('返回码 ' + str(r.returncode))}", "WARNING")
    return False


GITHUB_URL = "github.com/Zixuiu/code-space.git"


def get_github_token():
    """读取 GitHub personal access token：环境变量 GITHUB_TOKEN > 本地文件 ~/.ssh/github_token（不入库）"""
    env_tok = os.environ.get("GITHUB_TOKEN", "").strip()
    if env_tok:
        return env_tok
    tok_file = os.path.join(os.path.expanduser("~"), ".ssh", "github_token")
    try:
        if os.path.exists(tok_file):
            with open(tok_file, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return None


def push_github_via_token():
    """HTTPS + GitHub PAT 推送到 GitHub；token 仅在本次命令的 URL 中，不写入 git config"""
    token = get_github_token()
    if not token:
        log("未找到 GitHub token：请设置环境变量 GITHUB_TOKEN，或在 ~/.ssh/github_token 写入 token", "ERROR")
        return False
    os.environ['GIT_TERMINAL_PROMPT'] = '0'
    https_url = f"https://{token}@{GITHUB_URL}"
    log("使用 HTTPS + token 方式推送到 GitHub ...", "INFO")
    r = run_cmd(f'git -c credential.helper= push "{https_url}" HEAD:main', timeout=180)
    if r.returncode == 0:
        log("🎉 推送成功（GitHub HTTPS + token）！代码已上传到 GitHub！", "SUCCESS")
        return True
    err = (r.stdout or "") + (r.stderr or "")
    if "permission denied" in err.lower() or "401" in err or "403" in err:
        log("GitHub Token 认证失败：请检查 token 是否有效、是否有写权限，以及仓库 Zixuiu/codespace 是否存在", "ERROR")
    else:
        err_lines = [l for l in err.split('\n')
                     if not any(x in l for x in ['SAFE_RM', 'otFound', '无法将', 'NotFound',
                                                  '所在位置', 'CategoryInfo', 'FullyQualifiedErrorId'])]
        clean_err = '\n'.join(err_lines).strip()
        log(f"GitHub 推送失败: {clean_err[:400] or ('返回码 ' + str(r.returncode))}", "WARNING")
    return False


def main():
    print("=" * 70)
    print("🚀 GitCode + GitHub 一键推送工具（保护本地组合技/快捷键/录制数据不被上传）")
    print("=" * 70)
    print(f"📁 工作目录: {BASE_DIR}")

    # Step 1+2: 配置 SSH 并检查私钥 + 认证
    log("\n步骤 1-2/6: 配置 SSH 公钥 / 私钥 / 客户端...")
    ssh_ok, pub_key_file, config_file = setup_ssh_and_check()
    use_token = not ssh_ok
    if ssh_ok:
        log("SSH 配置完成，认证通过", "SUCCESS")
    else:
        log("SSH 不可用（缺私钥或认证失败），将回退到 HTTPS + token 方式", "WARNING")

    # Step 3: 暂存并提交所有可提交改动
    # 用 `git diff --cached --quiet` 的退出码作为唯一判断依据（最可靠，不解析文本输出）：
    #   退出码 0 = 暂存区无差异（无需提交）
    #   退出码 1 = 暂存区有差异（需要提交）
    log("\n步骤 3/6: 暂存并提交改动...")
    run_cmd("git add -A")
    r_diff = run_cmd("git diff --cached --quiet")
    if r_diff.returncode == 0:
        # 暂存区为空 = 没有需要提交的新更改（未跟踪/已被 gitignore 忽略的本地数据不会进来）
        log("暂存区为空，没有需要提交的新更改", "INFO")
    else:
        # 退出码非 0（通常为 1）表示有可提交内容
        r2 = run_cmd("git diff --cached --name-only")
        staged = [l.strip() for l in r2.stdout.split('\n') if l.strip()]
        log(f"将提交 {len(staged)} 个文件:", "INFO")
        for f in staged[:10]:
            print(f"   + {f}")
        if len(staged) > 10:
            print(f"   ... 还有 {len(staged)-10} 个文件")
        commit_msg = f"auto push {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        r = run_cmd(f'git -c user.email="1399972370@qq.com" -c user.name="PC-action" commit -m "{commit_msg}"')
        if r.returncode == 0:
            log("文件已提交", "SUCCESS")
        else:
            log("提交失败，错误信息: " + (r.stderr.strip() or r.stdout.strip())[:400], "ERROR")

    # Step 4: 设置远程仓库为 SSH
    log("\n步骤 4/6: 配置远程仓库为 SSH 协议...")
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
    log("\n步骤 5/6: 推送到 GitCode...")
    if ssh_ok:
        os.environ['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes -o StrictHostKeyChecking=no'
        os.environ['GIT_TERMINAL_PROMPT'] = '0'
        log("尝试 SSH 推送...", "INFO")
        r = run_cmd('git -c credential.helper= push -u origin main', timeout=90)
        if r.returncode == 0:
            log("🎉 推送成功（SSH）！代码已上传到 GitCode！", "SUCCESS")
        elif "permission denied" in r.stderr.lower() or "publickey" in r.stderr.lower():
            log("SSH 认证失败，回退到 HTTPS + token 方式", "WARNING")
            use_token = True
        else:
            err_lines = [l for l in r.stderr.split('\n')
                         if not any(x in l for x in ['SAFE_RM', 'otFound', '无法将', 'NotFound',
                                                      '所在位置', 'CategoryInfo', 'FullyQualifiedErrorId'])]
            clean_err = '\n'.join(err_lines).strip()
            if clean_err:
                log(f"SSH 推送结果: {clean_err[:400]}", "WARNING")
            else:
                log(f"返回码: {r.returncode}，请检查网络连接，将回退 token 方式", "WARNING")
            use_token = True

    if use_token:
        ok = push_via_token()
        if not ok:
            sys.exit(1)

    # Step 6: 推送到 GitHub
    log("\n步骤 6/6: 推送到 GitHub...")
    if not push_github_via_token():
        sys.exit(1)

    # 摘要
    print("\n" + "=" * 70)
    print("📋 操作总结")
    print("=" * 70)
    print(f"✅ SSH 公钥: {pub_key_file}")
    print(f"✅ SSH 配置: {config_file}")
    print(f"✅ 项目目录: {BASE_DIR}")
    print(f"✅ 远程仓库: {SSH_URL if ssh_ok else 'https://gitcode.com/weixin_58844486/codespace.git'}")
    print(f"✅ GitHub: https://{GITHUB_URL}")
    print(f"ℹ️  注意: 本地组合技、快捷键、录制文件夹、*.db 数据库不会被推送（已受保护）")
    print("=" * 70)


if __name__ == "__main__":
    main()
