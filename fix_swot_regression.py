"""
fix_swot_regression.py — re-enable /swot + fix tutorial + fix verify_app.py path.

The rollback to 9a9150f undid the SWOT fixes from earlier. This restores them.
Run from the app folder:
    python fix_swot_regression.py
"""
import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

if not os.path.isfile('app.py'):
    print("ERROR: app.py not found.")
    sys.exit(1)

shutil.copy2('app.py', f'app.py.bak.{STAMP}')
print(f"Backup: app.py.bak.{STAMP}\n")

with open('app.py', 'r', encoding='utf-8') as f:
    src = f.read()
original_size = len(src)

# ─────────────────────────────────────────────────────────────────────
# 1. Re-enable /swot route
# ─────────────────────────────────────────────────────────────────────
print("[1/3] Re-enable /swot route")

OLD_SWOT = """# DELETED FEATURE: @app.route('/swot')
# @login_required
def swot():"""

NEW_SWOT = """@app.route('/swot')
@login_required
def swot():"""

if "@app.route('/swot')" in src and "# DELETED FEATURE: @app.route('/swot')" not in src:
    print("  [SKIP] /swot already enabled")
elif OLD_SWOT in src:
    src = src.replace(OLD_SWOT, NEW_SWOT, 1)
    print("  [OK] /swot route re-enabled")
else:
    print("  [WARN] Exact comment pattern not found — checking variants")
    # Try any commented-out swot
    pattern = re.compile(r"#\s*@app\.route\('/swot'\)\n#\s*@login_required\ndef swot\(\):", re.MULTILINE)
    if pattern.search(src):
        src = pattern.sub("@app.route('/swot')\n@login_required\ndef swot():", src, count=1)
        print("  [OK] /swot re-enabled (variant match)")
    else:
        print("  [FAIL] Could not find commented swot route")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────
# 2. Fix SWOT link in business_plan.html
# ─────────────────────────────────────────────────────────────────────
print("\n[2/3] Fix SWOT link in templates/business_plan.html")
bplan = 'templates/business_plan.html'
if os.path.isfile(bplan):
    with open(bplan, 'r', encoding='utf-8') as f:
        content = f.read()
    old_link = "url_for('business_plan')\">SWOT Analysis"
    new_link = "url_for('swot')\">SWOT Analysis"
    if old_link in content:
        shutil.copy2(bplan, f'{bplan}.bak.{STAMP}')
        content = content.replace(old_link, new_link, 1)
        with open(bplan, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  [OK] business_plan.html SWOT link fixed")
    elif new_link in content:
        print("  [SKIP] already fixed")
    else:
        print("  [WARN] SWOT link pattern not found — check manually")

# ─────────────────────────────────────────────────────────────────────
# 3. Fix verify_app.py — /shortcuts → /tools/shortcuts
# ─────────────────────────────────────────────────────────────────────
print("\n[3/3] Fix verify_app.py /shortcuts path")
if os.path.isfile('verify_app.py'):
    with open('verify_app.py', 'r', encoding='utf-8') as f:
        v = f.read()
    if "'/shortcuts'" in v and "'/tools/shortcuts'" not in v:
        shutil.copy2('verify_app.py', f'verify_app.py.bak.{STAMP}')
        v = v.replace("'/shortcuts',", "'/tools/shortcuts',", 1)
        with open('verify_app.py', 'w', encoding='utf-8') as f:
            f.write(v)
        print("  [OK] verify_app.py updated")
    else:
        print("  [SKIP] already fixed or pattern not found")

# ─────────────────────────────────────────────────────────────────────
# WRITE + VERIFY
# ─────────────────────────────────────────────────────────────────────
print(f"\n[WRITE] Writing app.py ({len(src):,} bytes, was {original_size:,})")
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(src)

print("\n[VERIFY] Re-reading from disk...")
with open('app.py', 'r', encoding='utf-8') as f:
    on_disk = f.read()

checks = {
    '/swot enabled': "@app.route('/swot')" in on_disk and "# DELETED FEATURE: @app.route('/swot')" not in on_disk,
    'swot function present': 'def swot():' in on_disk,
}
all_ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present: all_ok = False
if not all_ok:
    print(f"\n[FATAL] Restore: Copy-Item \"app.py.bak.{STAMP}\" app.py")
    sys.exit(1)

print("\n[COMPILE] Verifying compile...")
r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    sys.exit(1)
print("  [OK] app.py compiles cleanly")

print("\n" + "=" * 60)
print("Regression fixed.")
print("=" * 60)
print("\nNow:")
print("  1. python verify_app.py    (should show 48/0)")
print("  2. git add app.py templates/ verify_app.py")
print("  3. git commit -m 'Supreme hub + fix swot regression + verifier'")
print("  4. git push")
print("  5. Render → Clear build cache & deploy")