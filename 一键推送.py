import os
import subprocess
import sys

BASE_DIR = r"d:\codespace"
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

print("=" * 70)
print("🚀 GitCode 一键推送工具")
print("=" * 70)

# Step 1: 配置 SSH 公钥
log("步骤 1/5: 配置 SSH 公钥...")
ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
pub_key_file = os.path.join(ssh_dir, "id_ed25519.pub")

try:
    os.makedirs(ssh_dir, exist_ok=True)
    
    with open(pub_key_file, 'w', encoding='utf-8') as f:
        f.write(SSH_PUBLIC_KEY + '\n')
    
    with open(pub_key_file, 'r', encoding='utf-8') as f:
        verify = f.read().strip()
    
    if verify == SSH_PUBLIC_KEY:
        log(f"公钥已写入: {pub_key_file}", "SUCCESS")
    else:
        log("公钥验证失败", "ERROR")
except Exception as e:
    log(f"写入公钥失败: {e}", "ERROR")

# Step 2: 配置 SSH config
log("\n步骤 2/5: 配置 SSH 客户端...")
config_file = os.path.join(ssh_dir, "config")

ssh_config = """Host gitcode.com
\tHostName gitcode.com
\tUser git
\tIdentityFile ~/.ssh/id_ed25519
\tIdentitiesOnly yes
"""

try:
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(ssh_config)
    log(f"SSH 配置已写入: {config_file}", "SUCCESS")
except Exception as e:
    log(f"写入配置失败: {e}", "ERROR")

# 配置 git 使用系统 OpenSSH（Git 自带 ssh 可能认证失败）
system_ssh = r"C:\Windows\System32\OpenSSH\ssh.exe"
if os.path.exists(system_ssh):
    run_cmd(f'git config core.sshCommand "{system_ssh}"')
    log("git 已配置使用系统 ssh", "INFO")

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
        
        # 自动添加并提交
        log("正在添加所有文件...", "INFO")
        run_cmd("git add .")
        
        import datetime
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

# 验证
r = run_cmd("git remote -v")
if r.returncode == 0 and SSH_URL in r.stdout:
    for line in r.stdout.strip().split('\n'):
        if 'origin' in line:
            print(f"   {line.strip()}")

# Step 5: 推送代码
log("\n步骤 5/5: 推送到 GitCode (SSH)...")
log("这可能需要几秒钟...", "INFO")

r = run_cmd("git push -u origin main", timeout=60)

if r.returncode == 0:
    log("🎉 推送成功！代码已上传到 GitCode！", "SUCCESS")
elif "successfully authenticated" in r.stdout.lower() or "welcome" in r.stdout.lower():
    log("✅ 认证成功，但可能已有更新", "SUCCESS")
elif "permission denied" in r.stderr.lower() or "publickey" in r.stderr.lower():
    log("❌ SSH 认证失败！", "ERROR")
    print("\n" + "=" * 70)
    print("需要手动添加公钥到 GitCode：")
    print("=" * 70)
    print(f"\n1. 访问: https://gitcode.com/-/user_settings/keys")
    print(f"\n2. 粘贴以下公钥:")
    print("-" * 50)
    print(SSH_PUBLIC_KEY)
    print("-" * 50)
    print(f"\n3. 标题填写: PC-action-macOS")
    print(f"\n4. 添加完成后，再次运行此脚本即可推送")
    print("=" * 70)
else:
    err_lines = [l for l in r.stderr.split('\n') 
                 if not any(x in l for x in ['SAFE_RM', 'otFound', '无法将', 'NotFound', 
                                              '所在位置', 'CategoryInfo', 'FullyQualifiedErrorId'])]
    clean_err = '\n'.join(err_lines).strip()
    if clean_err:
        log(f"推送结果: {clean_err[:300]}", "WARNING")
    else:
        log(f"返回码: {r.returncode}，请检查网络连接", "WARNING")

# 显示结果摘要
print("\n" + "=" * 70)
print("📋 操作总结")
print("=" * 70)
print(f"✅ SSH 公钥位置: {pub_key_file}")
print(f"✅ SSH 配置位置: {config_file}")
print(f"✅ 项目目录: {BASE_DIR}")
print(f"✅ 远程仓库: {SSH_URL}")

if os.path.exists(pub_key_file):
    print("\n💡 如果是首次使用，请确保已将公钥添加到 GitCode:")
    print("   https://gitcode.com/-/user_settings/keys")

print("\n" + "=" * 70)
