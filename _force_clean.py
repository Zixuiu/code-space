import os, shutil, subprocess, time, sys

ROOT = r"D:\code空间"
pc_root = os.path.join(ROOT, "PC-action")
pc_dest = os.path.join(ROOT, "01-开发项目", "PC-action")

def run_pwsh(cmd):
    try:
        r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=30)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return -1, str(e)

def main():
    print("="*60)
    print("Force cleaning PC-action from root...")
    print("="*60)

    print(f"\nRoot PC-action exists: {os.path.exists(pc_root)}")
    print(f"Dest PC-action exists: {os.path.exists(pc_dest)}")

    if not os.path.exists(pc_root):
        print("PC-action already gone from root! ✅")
        print("\nRoot level items:")
        for item in sorted(os.listdir(ROOT)):
            if not item.startswith("."):
                print(f"  {item}")
        print("\n按 Enter 退出...")
        input()
        return

    if not os.path.exists(pc_dest):
        print("WARNING: Destination missing! Will try to move...")
        try:
            shutil.move(pc_root, pc_dest)
            print("Moved successfully!")
            print("\n按 Enter 退出...")
            input()
            return
        except Exception as e:
            print(f"Move failed: {e}")

    # List remaining
    remaining = []
    for dirpath, dirnames, filenames in os.walk(pc_root):
        for f in filenames:
            remaining.append(os.path.join(dirpath, f))
    print(f"\nRemaining files: {len(remaining)}")
    for rf in remaining:
        print(f"  {rf}")

    # Kill git processes
    print("\n[1/4] Killing git-related processes...")
    code, out = run_pwsh("Get-Process git*,code*,SearchIndexer* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue")
    time.sleep(2)

    # Remove readonly
    print("[2/4] Removing readonly attributes...")
    code, out = run_pwsh(f'attrib -R "{pc_root}\\*" /S')

    # Force delete
    print("[3/4] Force deleting...")
    code, out = run_pwsh(f'Remove-Item -Path "{pc_root}" -Force -Recurse -ErrorAction SilentlyContinue')
    print(f"  Exit: {code}")

    # shutil fallback
    if os.path.exists(pc_root):
        print("[4/4] Python fallback delete...")
        try:
            shutil.rmtree(pc_root, ignore_errors=True)
        except:
            pass

    # Result
    if os.path.exists(pc_root):
        still = []
        for dirpath, dirnames, filenames in os.walk(pc_root):
            for f in filenames:
                still.append(os.path.join(dirpath, f))
        print(f"\n⚠️  Still {len(still)} files locked:")
        for s in still:
            print(f"  {s}")
        print("\n💡 关掉VS Code再运行这个脚本就能彻底删除")
    else:
        print("\n✅ PC-action 已成功从根目录删除！")

    print(f"\n{'='*60}")
    print("Root level items:")
    for item in sorted(os.listdir(ROOT)):
        if not item.startswith(".") and item != "_force_clean.py":
            print(f"  {item}")
    print(f"{'='*60}")
    input("\n按 Enter 退出...")

if __name__ == "__main__":
    main()