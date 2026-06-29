import os, shutil, subprocess

p = r"D:\code空间\PC-action"
d = r"D:\code空间\01-开发项目\PC-action"

if not os.path.exists(d):
    print("ERROR: Destination missing!")
    exit()

if not os.path.exists(p):
    print("PC-action already gone from root! ✅")
    for item in sorted(os.listdir(r"D:\code空间")):
        if not item.startswith("."):
            print(f"  {item}")
    exit()

# Step 1: Take ownership
print("[1/5] Taking ownership...")
subprocess.run(["takeown.exe", "/F", p, "/R", "/D", "Y"], capture_output=True, text=True)

# Step 2: Grant full control to current user
print("[2/5] Granting permissions...")
subprocess.run(["icacls.exe", p, "/grant", f"{os.environ['USERNAME']}:F", "/T", "/Q"], capture_output=True, text=True)

# Step 3: Kill all Code and git processes via PowerShell
print("[3/5] Killing locking processes...")
ps_script = '''
$procs = @()
$procs += Get-Process -Name "Code*","git*","perl*","sh*" -ErrorAction SilentlyContinue
$procs | ForEach-Object { 
    try { $_.Kill() } catch {} 
}
Write-Host "Done killing processes"
'''
subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=10)

# Step 4: Delete via PowerShell
print("[4/5] Deleting...")
for attempt in range(3):
    cmd = f'Remove-Item -Path "{p}" -Force -Recurse -ErrorAction SilentlyContinue'
    subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=30)
    if not os.path.exists(p):
        break
    import time
    time.sleep(2)

# Step 5: Python fallback
if os.path.exists(p):
    print("[5/5] Python fallback...")
    try:
        shutil.rmtree(p, ignore_errors=True)
    except:
        pass

# Final check
if not os.path.exists(p):
    print("\n✅ SUCCESS: PC-action deleted from root!")
else:
    print(f"\n⚠️  Could not delete: {os.path.exists(p)}")
    try:
        items = os.listdir(p)
        print(f"   Remaining items: {items}")
    except:
        print("   Cannot access directory (locked by VS Code)")

print("\nFinal root directory:")
for item in sorted(os.listdir(r"D:\code空间")):
    if not item.startswith(".") and item not in ("_do_it.py", "_force_clean.py"):
        print(f"  {item}")