import subprocess, os

BASE = r"d:\codespace\01-开发项目\PC-action\PC-action-macOS"
OUT = os.path.join(BASE, "push_output.txt")

r = subprocess.run("git push -u origin master", shell=True, cwd=BASE,
                   capture_output=True, text=True,
                   encoding='utf-8', errors='replace', timeout=60)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"Return Code: {r.returncode}\n")
    f.write(f"--- STDOUT ---\n{r.stdout}\n")
    f.write(f"--- STDERR ---\n{r.stderr}")

print(f"Done. Output saved to: {OUT}")
print(f"Return code: {r.returncode}")