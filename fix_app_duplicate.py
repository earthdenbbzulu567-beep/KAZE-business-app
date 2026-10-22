"""
fix_app_duplicate.py — remove the duplicate customer_statement route.

Run from the folder with app.py:
    python fix_app_duplicate.py
"""
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found. Run from the folder with app.py.")
    sys.exit(1)

backup = f"{APP}.bak.{STAMP}"
shutil.copy2(APP, backup)
print(f"Backup: {backup}\n")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

# Find the specific duplicate route
PATTERN = re.compile(
    r"@app\.route\('/customer_statement/<int:cid>'[^\n]*\)\n"
    r"(?:@login_required\n)?"
    r"def customer_statement\([^)]*\):\n"
    r".*?"
    r"(?=\n@app\.route|\n@app\.errorhandler|\n# ====|\nif __name__|\Z)",
    re.DOTALL,
)

match = PATTERN.search(src)
if match:
    removed = match.group(0)
    src = src[:match.start()] + src[match.end():]
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print(f"[OK] Removed /customer_statement/<int:cid> route")
    print(f"     ({len(removed):,} chars deleted)\n")
else:
    print("[SKIP] Pattern not found — might already be removed.")
    print("       Checking for OTHER duplicates anyway...\n")

# Scan for any remaining duplicate function names
route_re = re.compile(
    r"@app\.route\([^)]+\)\s*\n"
    r"(?:@login_required\s*\n)?"
    r"def (\w+)\(",
    re.DOTALL,
)
defs = route_re.findall(src)
seen = {}
dupes = {}
for name in defs:
    seen[name] = seen.get(name, 0) + 1
for name, count in seen.items():
    if count > 1:
        dupes[name] = count

if dupes:
    print(f"[WARN] Found {len(dupes)} MORE duplicate endpoint(s):")
    for name, count in sorted(dupes.items()):
        print(f"       - def {name} appears {count} times")
    print("\n       These will ALSO crash Flask at boot.")
    print("       Fix them before deploying — same pattern:")
    print("       delete or rename the older/duplicate one.\n")
else:
    print("[OK] No other duplicates found.\n")

# Compile check
print("Verifying app.py compiles...")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK] app.py compiles cleanly.\n")
else:
    print("  [FAIL] syntax error:")
    print(r.stderr)

print("=" * 60)
if dupes:
    print("⚠  Fix the remaining duplicates before deploying.")
    print("   Otherwise Flask will crash on a DIFFERENT endpoint next.")
else:
    print("Ready to deploy.")
    print("  git add app.py")
    print("  git commit -m 'Remove duplicate customer_statement route'")
    print("  git push")
print("=" * 60)