# -*- coding: utf-8 -*-
"""
一键拉取（镜像同步版）
======================
以远端为准，强制对齐 GitCode 的 codespace 根仓库，让它与远端完全一致；
同时只保留 PC-Action 的本地数据目录（组合技/快捷键/流程录制）和本工具脚本目录。

行为：
  fetch origin main
   → reset --hard FETCH_HEAD   （丢弃本地所有已跟踪改动）
   → clean -fd                 （删除本地所有未跟踪文件）
   → 还原 PC-Action 本地数据    （组合技/快捷键/流程录制，绝不丢失）
   → 还原本脚本所在目录         （防止把自己和 bat 删掉）
"""
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 让 git 的 SSH 全程免交互：遇到 host 指纹确认或需要 passphrase 时
# 直接失败而不是停在原地等你按 Enter，随后自动回退到 GitCode token。
os.environ["GIT_SSH_COMMAND"] = (
    "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"
)
# 关闭 git 交互式凭据提示，避免等待输入
os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")

# 脚本位于 04-工具脚本/git工具/，仓库根是上两级目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))   # = d:\codespace
REMOTE = "origin"
BRANCH = "main"

GITCODE_HOST = "gitcode.com"
GITCODE_REPO = "weixin_58844486/codespace"


def run(cmd, cwd=None, timeout=600):
    try:
        return subprocess.run(
            cmd, shell=True, cwd=cwd or REPO_ROOT, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return type("R", (), {"returncode": 1, "stdout": "", "stderr": f"超时(>{timeout}s)"})()
    except Exception as e:
        return type("R", (), {"returncode": 1, "stdout": "", "stderr": str(e)})()


def log(msg, level="INFO"):
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "•")
    print(f"{prefix} {msg}")


# ---------------------------------------------------------------------------
# 受保护目录：PC-Action 本地数据 + 工具脚本目录
# ---------------------------------------------------------------------------
def collect_protect():
    """返回必须保留的绝对路径列表。"""
    protect = []
    # 1. PC-Action 本地数据
    app = os.path.join(REPO_ROOT, "01-space", "PC-action", "PC-action-macOS")
    if os.path.isdir(app):
        for p in ("data", "user_data", "recordings"):
            sp = os.path.join(app, p)
            if os.path.exists(sp):
                protect.append(sp)
    # 2. 工具脚本目录：★ 绝不做整目录"快照→还原"（2026-09-10 修复）
    #    代价说明：本目录 5 个文件（一键拉取.py / 一键推送.py / 两个 .bat / _probe_ent.py）
    #    都已被 git 跟踪，`git clean -fd` 不会删除已跟踪文件，本就不需要整目录保护；
    #    而旧的整目录快照还原会在 `reset --hard` 之后，用拉取前的旧内容把远端新版本覆盖回去，
    #    结果就是"这个目录永远拉不到远端更新"，还会让 `git status` 显示假 M（被误判成本地有新改动）。
    #    本地残留（__pycache__ 等）已被 .gitignore 忽略，`clean -fd`（不带 -x）默认不清理 ignored 文件。
    return protect


def snapshot_protect():
    """把受保护目录完整快照进临时区，返回 {abs_src: abs_dst}。"""
    snaps = {}
    for p in collect_protect():
        tmp = os.path.join(
            tempfile.gettempdir(),
            f"pcaction_protect_{os.path.basename(p)}_{datetime.now():%Y%m%d_%H%M%S}")
        if os.path.isdir(p):
            if os.path.exists(tmp):
                shutil.rmtree(tmp, ignore_errors=True)
            shutil.copytree(p, tmp)
        else:
            os.makedirs(os.path.dirname(tmp), exist_ok=True)
            shutil.copy2(p, tmp)
        snaps[p] = tmp
    return snaps


def restore_protect(snaps):
    for src, dst in snaps.items():
        if not os.path.exists(dst):
            continue
        os.makedirs(src, exist_ok=True)
        if os.path.isdir(dst):
            for root, dirs, files in os.walk(dst):
                rel = os.path.relpath(root, dst)
                tgt = src if rel == "." else os.path.join(src, rel)
                os.makedirs(tgt, exist_ok=True)
                for f in files:
                    shutil.copy2(os.path.join(root, f), os.path.join(tgt, f))
        else:
            shutil.copy2(dst, src)


# ---------------------------------------------------------------------------
# 认证：SSH / GitCode token(HTTPS)
# ---------------------------------------------------------------------------
def get_gitcode_credential():
    import re as _re
    m = _re.search(r"gitcode\.com[:/]([\w.\-]+/[\w.\-]+?)(?:\.git)?$", GITCODE_REPO and GITCODE_REPO)
    gcode_repo = "weixin_58844486/codespace"
    tok = os.environ.get("GITCODE_TOKEN")
    if not tok:
        p = os.path.join(os.path.expanduser("~"), ".ssh", "gitcode_token")
        if os.path.exists(p):
            tok = open(p, "r", encoding="utf-8", errors="replace").read().strip().replace("\x00", "")
    if not tok:
        return None
    return f"https://oauth2:{tok}@{GITCODE_HOST}/{gcode_repo}.git"


def do_fetch(remote, branch):
    """fetch：正常走 SSH/已配好的 origin；失败且是 GitCode 时回退 HTTPS+token。"""
    r = run(f"git fetch {remote} {branch}")
    if r.returncode == 0:
        return r
    auth = get_gitcode_credential()
    if auth:
        log("SSH 不可用，回退 HTTPS+GitCode token ...")
        return run(f'git fetch "{auth}" {branch}')
    return r


# ---------------------------------------------------------------------------
# 启动器（.bat）保障：clean 可能删掉未跟踪的 .bat，跑完重建
# ---------------------------------------------------------------------------
def _write_bat(path, py_name):
    content = (
        "@echo off\n"
        "cd /d \"%~dp0.\"\n"
        "\n"
        "set \"PY=\"\n"
        "where python >nul 2>nul\n"
        "if not errorlevel 1 set \"PY=python\"\n"
        "\n"
        "if not defined PY (\n"
        "    where py >nul 2>nul\n"
        "    if not errorlevel 1 set \"PY=py\"\n"
        ")\n"
        "\n"
        "if not defined PY (\n"
        "    where python3 >nul 2>nul\n"
        "    if not errorlevel 1 set \"PY=python3\"\n"
        ")\n"
        "\n"
        "if not defined PY (\n"
        "    echo [ERROR] Python not found. Install Python and add it to PATH.\n"
        "    echo Or double-click the .py file if it is associated with python.exe.\n"
        "    goto :PAUSE\n"
        ")\n"
        "\n"
        f"%PY% \"%~dp0{py_name}\"\n"
        "\n"
        ":PAUSE\n"
        "if errorlevel 1 (echo FAILED) else (echo DONE)\n"
        "pause\n"
    )
    with open(path, "w", encoding="gbk", newline="\r\n") as f:
        f.write(content)


def _fix_bat_eol(path):
    try:
        if not os.path.exists(path):
            return False
        with open(path, "rb") as f:
            data = f.read()
        bare_lf = data.count(b"\n") - data.count(b"\r\n")
        if bare_lf <= 0:
            return False
        fixed = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        with open(path, "wb") as f:
            f.write(fixed)
        log(f"已修复 {os.path.basename(path)} 换行（LF→CRLF）", "WARNING")
        return True
    except Exception:
        return False


def ensure_launchers():
    pull_bat = os.path.join(BASE_DIR, "一键拉取.bat")
    push_bat = os.path.join(BASE_DIR, "一键推送.bat")
    for _p in (pull_bat, push_bat):
        _fix_bat_eol(_p)
    if not os.path.exists(pull_bat):
        _write_bat(pull_bat, "一键拉取.py")
    if not os.path.exists(push_bat):
        _write_bat(push_bat, "一键推送.py")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    print("=" * 68)
    print("⬇️  一键拉取（镜像同步）—— 以远端为准，强制对齐")
    print("=" * 68)
    print(f"📁 仓库根目录: {REPO_ROOT}")

    if not os.path.isdir(os.path.join(REPO_ROOT, ".git")):
        log("未检测到 git 仓库", "ERROR")
        return 1

    # 1. 快照受保护目录（PC-Action 数据 + 工具脚本目录）
    snaps = snapshot_protect()
    log(f"已快照 {len(snaps)} 个本地数据目录（组合技/快捷键/流程录制）")
    for p in collect_protect():
        log(f"   保留: {os.path.relpath(p, REPO_ROOT)}", "INFO")

    # 0. 确保 origin 固定为 HTTPS + token（避免 SSH 无密钥导致拉取失真、与远端不一致）
    try:
        https_url = auth()
        if https_url and "gitcode.com" in https_url and "oauth2:" in https_url:
            run(f'git remote set-url origin "{https_url}"')
            log("origin 已固定为 HTTPS + token", "INFO")
    except Exception:
        pass

    # 2. fetch
    log("步骤 1/3: 拉取远端最新代码 ...")
    r = do_fetch(REMOTE, BRANCH)
    if r.returncode != 0:
        log(f"fetch 失败: {r.stderr.strip()[:400]}", "ERROR")
        restore_protect(snaps)
        return 1

    # 3. reset --hard 强制对齐远端
    log("步骤 2/3: 强制对齐远端（丢弃本地改动）...")
    r = run("git reset --hard FETCH_HEAD")
    if r.returncode != 0:
        log(f"同步失败: {r.stderr.strip()[:400]}", "ERROR")
        restore_protect(snaps)
        return 1

    # 4. clean 未跟踪文件（跳过受保护目录，保证不误删 PC-Action 数据）
    log("步骤 3/3: 清理本地多余文件（跳过受保护目录）...")
    clean_cmd = "git clean -fd"
    for p in collect_protect():
        rel = os.path.relpath(p, REPO_ROOT).replace("\\", "/")
        clean_cmd += f' --exclude="{rel}/"'
    r = run(clean_cmd, timeout=900)
    if r.returncode != 0:
        log(f"清理未完全成功（通常不影响结果）: {(r.stderr or '').strip()[:300]}", "WARNING")

    # 5. 还原受保护目录
    restore_protect(snaps)
    log(f"已还原 {len(snaps)} 个本地数据目录")

    head = (run("git log -1 --oneline").stdout or "").strip()
    log(f"已对齐远端: {head}", "SUCCESS")
    ensure_launchers()
    print("=" * 68)
    print("✅ 拉取完成，本地已与远端完全一致（PC-Action 数据保留）")
    return 0


if __name__ == "__main__":
    sys.exit(main())