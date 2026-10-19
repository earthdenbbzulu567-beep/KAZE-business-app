"""
cleanup_stubs.py — remove the 4 stub features + their sub-routes.

Removes these routes from app.py:
    /scanner, /scanner/batch, /scanner/history
    /voice, /voice/intents, /voice/history
    /batches, /batches/fefo, /batches/risk
    /credit_scores, /credit/limits, /credit/trend

Also removes 4 entries from NAV_GROUPS so the sidebar stops advertising them,
and deletes the 4 template files (with .bak backups).

Run from the folder with app.py:
    python cleanup_stubs.py
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
    print(f"ERROR: {APP} not found. Run from the project root.")
    print(f"Current folder: {os.getcwd()}")
    sys.exit(1)

backup = f"{APP}.bak.{STAMP}"
shutil.copy2(APP, backup)
print(f"Backup saved: {backup}\n")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()
original = src

# ─────────────────────────────────────────────────────────────────────
# 1 — remove the routes
# ─────────────────────────────────────────────────────────────────────
STUB_PATHS = [
    '/scanner', '/scanner/batch', '/scanner/history',
    '/voice', '/voice/intents', '/voice/history',
    '/batches', '/batches/fefo', '/batches/risk',
    '/credit_scores', '/credit/limits', '/credit/trend',
]

ROUTE_PATTERN = re.compile(
    r"@app\.route\('(?:" + "|".join(re.escape(p) for p in STUB_PATHS) + r")'\)\n"
    r"@login_required\n"
    r"def \w+\([^)]*\):\n"
    r".*?"
    r"(?=\n@app\.|\n#|\ndef |\nif __name__|\Z)",
    re.DOTALL,
)

removed_routes = []
def collect_and_remove(match):
    m = re.search(r"@app\.route\('([^']+)'\)", match.group(0))
    removed_routes.append(m.group(1) if m else '???')
    return ''

src = ROUTE_PATTERN.sub(collect_and_remove, src)

print("Routes removed:")
if removed_routes:
    for p in removed_routes:
        print(f"  [DEL] {p}")
else:
    print("  [SKIP] none found (already removed?)")

# collapse 3+ newlines so we don't get huge gaps
src = re.sub(r'\n{3,}', '\n\n\n', src)

# ─────────────────────────────────────────────────────────────────────
# 2 — remove nav entries
# ─────────────────────────────────────────────────────────────────────
NAV_ENTRIES = [
    "        ('QR Scanner', 'scanner', 'scan', 'operations', ('scanner',)),\n",
    "        ('Voice Entry', 'voice', 'mic', 'workspace', ('voice',)),\n",
    "        ('Batch Tracker', 'batches', 'layers', 'stock', ('batches',)),\n",
    "        ('Credit Scores', 'credit_scores', 'shield-check', 'customers', ('credit_scores',)),\n",
]

print("\nNav entries removed:")
for entry in NAV_ENTRIES:
    if entry in src:
        src = src.replace(entry, '')
        label = entry.strip().split("'")[1]
        print(f"  [DEL] {label}")
    else:
        print(f"  [SKIP] not found: {entry.strip()[:60]}")

# ─────────────────────────────────────────────────────────────────────
# 3 — write app.py
# ─────────────────────────────────────────────────────────────────────
if src == original:
    print("\nNo changes to app.py — already clean.")
else:
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print(f"\nWrote {len(src):,} bytes to {APP}")

# ─────────────────────────────────────────────────────────────────────
# 4 — delete template files
# ─────────────────────────────────────────────────────────────────────
TEMPLATES = [
    'templates/scanner.html',
    'templates/voice.html',
    'templates/batches.html',
    'templates/credit_scores.html',
]

print("\nTemplates deleted:")
for tpl in TEMPLATES:
    if os.path.isfile(tpl):
        shutil.copy2(tpl, f"{tpl}.bak.{STAMP}")
        os.remove(tpl)
        print(f"  [DEL] {tpl}")
    else:
        print(f"  [SKIP] {tpl} not found")

# ─────────────────────────────────────────────────────────────────────
# 5 — compile check
# ─────────────────────────────────────────────────────────────────────
print("\nVerifying app.py compiles…")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK]   app.py compiles cleanly.")
else:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)
    print(f"\nRestore with:  copy \"{backup}\" {APP}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────
# 6 — confirm no dangling url_for references in templates
# ─────────────────────────────────────────────────────────────────────
print("\nChecking for dangling references in templates…")
DANGLING = ['scanner', 'voice', 'batches', 'credit_scores']
found = False
for root, _, files in os.walk('templates'):
    for f in files:
        if not f.endswith('.html'):
            continue
        p = os.path.join(root, f)
        with open(p, 'r', encoding='utf-8') as fh:
            c = fh.read()
        for name in DANGLING:
            for pat in (f"url_for('{name}')", f'url_for("{name}")'):
                if pat in c:
                    print(f"  [WARN] {p} references {pat}")
                    found = True
if not found:
    print("  [OK]   no template references the deleted endpoints")

print("\n" + "=" * 60)
print("Stub cleanup complete.")
print("=" * 60)
print("\nRestart Flask, then confirm:")
print("  /scanner /voice /batches /credit_scores  → 404 (that's correct)")
print("  Sidebar no longer shows those 4 entries")