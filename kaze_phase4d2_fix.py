"""
kaze_phase4d2_fix.py — Phase 4d-2 bug fixes.

1. mode_runtime.py: add month_tickets to sales tracker
2. mode_runtime.py: fix goal gap number formatting
3. dashboard.html: remove redundant "Business Activity Overview" section
4. dashboard.html: verify income/expenses summary is collapsed

Run from the folder with app.py:
    python kaze_phase4d2_fix.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

FAILED = []

# ── [1/3] Patch mode_runtime.py ────────────────────────────────────
print("[1/3] Patching mode_runtime.py...")
RT = 'mode_runtime.py'
if not os.path.isfile(RT):
    print(f"  [FAIL] {RT} not found")
    FAILED.append("mode_runtime.py")
else:
    shutil.copy2(RT, f"{RT}.bak.phase4d2fix_{STAMP}")
    with open(RT, encoding='utf-8') as f:
        rt = f.read()

    # 1a. Add month_tickets to track dict initialization
    OLD_TRACK = """        'month_revenue': 0.0,
        'month_profit': 0.0,
        'last_month_revenue': 0.0,"""
    NEW_TRACK = """        'month_revenue': 0.0,
        'month_profit': 0.0,
        'month_tickets': 0,
        'last_month_revenue': 0.0,"""
    if 'month_tickets' in rt:
        print("  [SKIP] month_tickets already tracked")
    elif OLD_TRACK in rt:
        rt = rt.replace(OLD_TRACK, NEW_TRACK, 1)
        print("  [OK]   month_tickets added to track dict")
    else:
        print("  [FAIL] month_revenue anchor not found")
        FAILED.append("month_revenue anchor")

    # 1b. Increment month_tickets when in month
    OLD_MONTH = """        if day >= month_from:
            track['month_revenue'] += revenue
            track['month_profit'] += profit"""
    NEW_MONTH = """        if day >= month_from:
            track['month_revenue'] += revenue
            track['month_profit'] += profit
            track['month_tickets'] += 1"""
    if "'month_tickets' += 1" in rt:
        print("  [SKIP] month_tickets increment already present")
    elif OLD_MONTH in rt:
        rt = rt.replace(OLD_MONTH, NEW_MONTH, 1)
        print("  [OK]   month_tickets increment added")
    else:
        print("  [FAIL] month_revenue increment anchor not found")
        FAILED.append("month_tickets increment")

    # 1c. Fix goal gap formatting
    OLD_ALERT = """        left = money_round(bits['monthly_goal'] - snap['sales']['month_revenue'])
        push_alert(snap['alerts'], 'info', 'Goal gap', '{} left to hit this month’s sales goal.'.format(left))"""
    NEW_ALERT = """        left = money_round(bits['monthly_goal'] - snap['sales']['month_revenue'])
        left_fmt = '{:,.2f}'.format(left)
        push_alert(snap['alerts'], 'info', 'Goal gap', '{} left to hit this month’s sales goal.'.format(left_fmt))"""
    if 'left_fmt' in rt:
        print("  [SKIP] goal gap formatting already fixed")
    elif OLD_ALERT in rt:
        rt = rt.replace(OLD_ALERT, NEW_ALERT, 1)
        print("  [OK]   goal gap now uses thousands separator")
    else:
        print("  [FAIL] goal gap alert anchor not found")
        FAILED.append("goal gap alert")

    with open(RT, 'w', encoding='utf-8') as f:
        f.write(rt)
    print("  [OK]   mode_runtime.py written")

# ── [2/3] Patch dashboard.html ─────────────────────────────────────
print("\n[2/3] Patching dashboard.html...")
TPL = 'templates/dashboard.html'
if not os.path.isfile(TPL):
    print(f"  [FAIL] {TPL} not found")
    FAILED.append("dashboard.html")
else:
    shutil.copy2(TPL, f"{TPL}.bak.phase4d2fix_{STAMP}")
    with open(TPL, encoding='utf-8') as f:
        html = f.read()

    # 2a. Remove Business Activity Overview section
    OLD_OVERVIEW_RE = re.compile(
        r'<section class="overview-grid".*?</section>',
        re.DOTALL,
    )
    new_html, count = OLD_OVERVIEW_RE.subn('', html, count=1)
    if count == 1:
        html = new_html
        print("  [OK]   redundant Business Activity Overview removed")
    elif 'Business Activity Overview' not in html:
        print("  [SKIP] overview already gone")
    else:
        print("  [FAIL] overview grid pattern not matched")
        FAILED.append("overview grid")

    with open(TPL, 'w', encoding='utf-8') as f:
        f.write(html)
    print("  [OK]   dashboard.html written")

# ── [3/3] Compile + Jinja check ───────────────────────────────────
print("\n[3/3] Verifying...")

r = subprocess.run([sys.executable, '-m', 'py_compile', RT], capture_output=True, text=True)
if r.returncode != 0:
    print(f"  [FAIL] {RT} syntax error:")
    print(r.stderr)
    FAILED.append("mode_runtime compile")
else:
    print(f"  [OK]   {RT} compiles cleanly")

try:
    Environment().parse(html)
    print("  [OK]   dashboard.html parses as valid Jinja")
except Exception as exc:
    print(f"  [FAIL] dashboard.html Jinja error: {exc}")
    FAILED.append("dashboard Jinja")

print("\n" + "=" * 62)
if FAILED:
    print("Some steps failed:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore mode_runtime: copy \"mode_runtime.py.bak.phase4d2fix_{STAMP}\" mode_runtime.py")
    print(f"Restore dashboard:    copy \"templates/dashboard.html.bak.phase4d2fix_{STAMP}\" templates/dashboard.html")
    sys.exit(1)

print("Phase 4d-2 fix complete.")
print("  mode_runtime.py: month_tickets + goal formatting")
print("  dashboard.html:  redundant overview section removed")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart app:  python app.py
2. Hard refresh /dashboard (Ctrl+F5)

3. Verify three things:

   a) KPI "Total Sales" card hint now shows "N tickets this month"
      (previously showed empty line)

   b) Goal gap alert at top shows formatted number:
      "K65,020,800,020.00 left to hit this month's sales goal."
      (previously showed "65020800020.0 left")

   c) "Business Activity Overview" section no longer appears
      at the bottom of the dashboard

4. Regression:
   - Two-column layout still works
   - Activity feed still shows entries with colored icons
   - "More widgets" collapse still works
   - P/L board still shows

5. If all pass:
   git add mode_runtime.py templates/dashboard.html kaze_phase4d2_dashboard.py kaze_phase4d2_fix.py
   git commit -m "Phase 4d-2: dashboard layout + activity feed + fixes"
   git push
""")