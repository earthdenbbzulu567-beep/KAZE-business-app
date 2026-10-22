"""
fix_final_batch.py — fix /turnover + /snapshot SQL, add SWOT to nav,
add Tutorial/Shortcuts/SWOT to user dropdown.

Same safe pattern: write to disk, re-read to verify, exit non-zero on failure.
"""
import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

if not os.path.isfile('app.py'):
    print("ERROR: app.py not found.")
    sys.exit(1)

shutil.copy2('app.py', f'app.py.bak.{STAMP}')
if os.path.isfile('templates/base.html'):
    shutil.copy2('templates/base.html', f'templates/base.html.bak.{STAMP}')
print(f"Backups: app.py.bak.{STAMP}, templates/base.html.bak.{STAMP}\n")

with open('app.py', 'r', encoding='utf-8') as f:
    src = f.read()
orig = len(src)

# ─────────────────────────────────────────────────────────────────────
# 1. Fix /turnover SQL
# ─────────────────────────────────────────────────────────────────────
print("[1/4] /turnover SQL")

TURNOVER_OLD = 'SELECT name, quantity, COALESCE(cost_price,0) as cost FROM stock WHERE user_id=%s ORDER BY quantity DESC LIMIT 20'
TURNOVER_NEW = "SELECT product_name AS name, quantity, COALESCE(cost_price,0) AS cost FROM stock WHERE user_id=%s ORDER BY quantity DESC LIMIT 20"

if TURNOVER_OLD in src:
    src = src.replace(TURNOVER_OLD, TURNOVER_NEW, 1)
    print("  [OK] turnover: name → product_name AS name")
elif TURNOVER_NEW in src:
    print("  [SKIP] turnover already fixed")
else:
    print("  [WARN] turnover pattern not matched — check manually")

# ─────────────────────────────────────────────────────────────────────
# 2. Fix /snapshot SQL (likely also broken from same rollback)
# ─────────────────────────────────────────────────────────────────────
print("\n[2/4] /snapshot SQL")

SNAP_OLD_1 = 'SELECT COALESCE(SUM(total),0) as sales FROM sales WHERE user_id=%s AND date >= DATE_TRUNC(\'month\', CURRENT_DATE)'
SNAP_NEW_1 = "SELECT COALESCE(SUM(total_amount),0) AS sales FROM sales WHERE user_id=%s AND sale_date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')"

SNAP_OLD_2 = "SELECT COALESCE(SUM(amount),0) as expenses FROM cashbook WHERE user_id=%s AND type='expense' AND date >= DATE_TRUNC('month', CURRENT_DATE)"
SNAP_NEW_2 = "SELECT COALESCE(SUM(amount),0) AS expenses FROM cash_books WHERE user_id=%s AND entry_type='out' AND date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')"

fixed_snap = 0
if SNAP_OLD_1 in src:
    src = src.replace(SNAP_OLD_1, SNAP_NEW_1, 1)
    fixed_snap += 1
    print("  [OK] snapshot sales: total→total_amount, date→sale_date")
if SNAP_OLD_2 in src:
    src = src.replace(SNAP_OLD_2, SNAP_NEW_2, 1)
    fixed_snap += 1
    print("  [OK] snapshot expenses: cashbook→cash_books, type→entry_type")
if fixed_snap == 0:
    print("  [SKIP] snapshot already fixed or pattern differs")

# ─────────────────────────────────────────────────────────────────────
# 3. Add SWOT to nav
# ─────────────────────────────────────────────────────────────────────
print("\n[3/4] Add SWOT to NAV_GROUPS")

BP_MARKER = "('Business plan', 'business_plan', 'map', 'planning', ('business_plan',)),"

if "'swot'" in src[src.find("NAV_GROUPS"):src.find("NAV_GROUPS") + 8000]:
    print("  [SKIP] SWOT already in nav")
elif BP_MARKER in src:
    SWOT_LINE = "\n        ('SWOT', 'swot', 'compass', 'planning', ('swot',)),"
    src = src.replace(BP_MARKER, BP_MARKER + SWOT_LINE, 1)
    print("  [OK] SWOT added after Business Plan")
else:
    print("  [WARN] Business Plan nav entry not found — add SWOT manually:")
    print("        ('SWOT', 'swot', 'compass', 'planning', ('swot',)),")

# ─────────────────────────────────────────────────────────────────────
# 4. Add Tutorial/Shortcuts/SWOT to user dropdown in base.html
# ─────────────────────────────────────────────────────────────────────
print("\n[4/4] User dropdown additions in base.html")

HELP_LINK = '''<a href="#" onclick="openModal('tutorialModal'); return false;">Help / Tutorial</a>'''
NEW_LINKS = '''<a href="#" onclick="openModal('tutorialModal'); return false;">Help / Tutorial</a>
                        <a href="{{ url_for('tutorial') }}">📖 Practical guide</a>
                        <a href="{{ url_for('shortcuts') }}">⌨️ Shortcuts</a>
                        <a href="{{ url_for('swot') }}">🧭 SWOT Analysis</a>'''

if os.path.isfile('templates/base.html'):
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        bhtml = f.read()
    if "url_for('tutorial')" in bhtml and "Help / Tutorial" in bhtml and "📖 Practical guide" in bhtml:
        print("  [SKIP] dropdown already has these links")
    elif HELP_LINK in bhtml:
        bhtml = bhtml.replace(HELP_LINK, NEW_LINKS, 1)
        with open('templates/base.html', 'w', encoding='utf-8') as f:
            f.write(bhtml)
        print("  [OK] added Practical guide / Shortcuts / SWOT to dropdown")
    else:
        print("  [WARN] 'Help / Tutorial' link not found in base.html")
        print("        Add these manually inside .dropdown-content:")
        print("          <a href=\"{{ url_for('tutorial') }}\">📖 Practical guide</a>")
        print("          <a href=\"{{ url_for('shortcuts') }}\">⌨️ Shortcuts</a>")
        print("          <a href=\"{{ url_for('swot') }}\">🧭 SWOT Analysis</a>")
else:
    print("  [WARN] templates/base.html not found")

# ─────────────────────────────────────────────────────────────────────
# WRITE + VERIFY
# ─────────────────────────────────────────────────────────────────────
print(f"\n[WRITE] Writing app.py ({len(src):,} bytes, was {orig:,})")
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(src)

print("\n[VERIFY] Re-reading from disk...")
with open('app.py', 'r', encoding='utf-8') as f:
    on_disk = f.read()

checks = {
    'turnover SQL fixed': 'product_name AS name, quantity, COALESCE(cost_price,0) AS cost' in on_disk,
    'swot in nav': "'SWOT', 'swot', 'compass'" in on_disk,
}

if os.path.isfile('templates/base.html'):
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        bh = f.read()
    checks['dropdown has tutorial'] = "📖 Practical guide" in bh
    checks['dropdown has swot'] = "🧭 SWOT Analysis" in bh
    checks['dropdown has shortcuts'] = "⌨️ Shortcuts" in bh

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
print("Done.")
print("=" * 60)
print("\nNow:")
print("  python verify_app.py  (routes should be ok)")
print("  git add app.py templates/base.html")
print("  git commit -m 'Fix turnover+snapshot SQL, add SWOT to nav, add tutorial/shortcuts/swot to dropdown'")
print("  git push")
print("  Render → Clear build cache & deploy")