"""
kaze_batch3b1_fix2.py — restore app.py and delete old placeholder routes.

The problem:
  Batch 3b part 1 tried to add @app.route('/settings/audit') with
  def settings_audit(), but an OLD placeholder with the same endpoint
  name already existed in app.py. Flask refuses to boot when two routes
  share an endpoint name.

The fix:
  1. Restore app.py from the batch3b1 backup (or git HEAD)
  2. Delete the 3 old placeholder routes by string surgery (safer than
     the broken regex from fix1)
  3. Then you re-run the batch script, which now adds the routes cleanly

Run from the folder with app.py:
    python kaze_batch3b1_fix2.py
"""

import glob
import os
import shutil
import subprocess
import sys

APP = 'app.py'

# ── Step 1: Restore app.py ──────────────────────────────────────────
backups = sorted(glob.glob(f'{APP}.bak.batch3b1_*'), reverse=True)
if backups:
    backup = backups[0]
    print(f"Restoring app.py from {backup}")
    shutil.copy2(backup, APP)
    print("[OK] app.py restored from backup")
else:
    print("No backup file found. Trying git restore from HEAD...")
    r = subprocess.run(['git', 'checkout', 'HEAD', '--', APP], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] git restore failed: {r.stderr}")
        print("        You may need to restore app.py manually.")
        sys.exit(1)
    print("[OK] app.py restored from git HEAD")

# ── Step 2: Delete old placeholder routes (string-based, robust) ───
with open(APP, encoding='utf-8') as f:
    src = f.read()

DELETE_ROUTES = [
    ('/settings/audit', 'settings_audit'),
    ('/whatsapp/templates', 'whatsapp_templates'),
    ('/whatsapp/log', 'whatsapp_log'),
]

for path, funcname in DELETE_ROUTES:
    marker = f"@app.route('{path}'"
    idx = src.find(marker)
    if idx < 0:
        print(f"  [SKIP] {path} — old route not found (already deleted?)")
        continue
    # Find the end: next @app.route, # === marker, or if __name__
    end_idx = len(src)
    for end_marker in ['\n@app.route', '\n# ===', '\nif __name__']:
        pos = src.find(end_marker, idx + len(marker))
        if pos > 0 and pos < end_idx:
            end_idx = pos
    # Trim trailing blank lines at the boundary
    while end_idx > 0 and src[end_idx-1] == '\n':
        end_idx -= 1
    src = src[:idx] + src[end_idx:]
    print(f"  [DEL]  {path} (old placeholder removed)")

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)

# ── Step 3: Verify no more duplicate route definitions ─────────────
print("\nScanning for remaining duplicate endpoint definitions...")
seen = {}
dupes = []
for match in __import__('re').finditer(r"def\s+(\w+)\s*\(", src):
    name = match.group(1)
    seen[name] = seen.get(name, 0) + 1
for name, count in seen.items():
    if count > 1 and name.startswith(('settings_audit', 'whatsapp_templates', 'whatsapp_log')):
        dupes.append((name, count))

if dupes:
    print("  [WARN] Still found duplicates:")
    for name, count in dupes:
        print(f"         def {name}() appears {count} times")
else:
    print("  [OK] No duplicate endpoint functions found for the 3 routes")

# ── Step 4: Compile check ──────────────────────────────────────────
print("\nCompiling app.py...")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    sys.exit(1)
print("  [OK] app.py compiles cleanly")

print()
print("=" * 62)
print("READY.")
print("=" * 62)
print()
print("Now run in this order:")
print()
print("  1. python kaze_batch3b_part1.py")
print("     (should complete without [FAIL])")
print()
print("  2. python app.py")
print("     (should start without AssertionError)")
print()
print("  3. If app.py starts, test in browser:")
print("     - /settings/audit")
print("     - /whatsapp/templates")
print("     - /whatsapp/log")
print()
print("If you still get the AssertionError after step 1, paste the")
print("exact error and the output of:")
print("  Select-String -Path app.py -Pattern 'def settings_audit'")