"""
apply_fixes_7.py — catch the last 5 TEXT-vs-DATE comparison bugs.

These are the routes that will 500 the first time someone visits them,
because 'sales.sale_date' and 'expenses.date' are TEXT in the schema
but the SQL compares them directly to CURRENT_DATE / DATE_TRUNC(...).

The rule they all share:
    wrap the RHS of every date comparison in to_char(..., 'YYYY-MM-DD')

Run from the folder with app.py:
    python apply_fixes_7.py

A backup app.py.bak.<timestamp> is created before any change.
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

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()
original = src

APPLIED, SKIPPED, FAILED = [], [], []


def patch(label, old, new):
    global src
    if old not in src:
        if new in src:
            print(f"  [SKIP] {label} — already fixed")
            SKIPPED.append(label)
        else:
            print(f"  [FAIL] {label} — pattern not found")
            FAILED.append(label)
        return
    count = src.count(old)
    if count > 1:
        print(f"  [WARN] {label} — {count} matches, replacing all")
    src = src.replace(old, new)
    print(f"  [OK]   {label}")
    APPLIED.append(label)


# ═════════════════════════════════════════════════════════════════════
# Fix 1 — /sales/margin-alert
#   Two bugs together: TEXT vs DATE, and GROUP BY references the
#   wrong table (s.product_name instead of st.product_name)
# ═════════════════════════════════════════════════════════════════════
print("[1/5] /sales/margin-alert")

patch(
    "margin-alert: to_char(sale_date) + GROUP BY st.product_name",
    """        WHERE s.user_id=%s AND s.sale_date >= CURRENT_DATE - INTERVAL '14 days'
        GROUP BY s.product_name HAVING AVG(s.selling_price_at_time) > 0""",
    """        WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '14 days','YYYY-MM-DD')
        GROUP BY st.product_name HAVING AVG(s.selling_price_at_time) > 0""",
)


# ═════════════════════════════════════════════════════════════════════
# Fix 2 — /stock/reorder-optimizer
# ═════════════════════════════════════════════════════════════════════
print("\n[2/5] /stock/reorder-optimizer")

patch(
    "reorder-optimizer: to_char(sale_date)",
    "    FROM stock st LEFT JOIN sales s ON s.stock_id=st.id AND s.sale_date >= CURRENT_DATE - INTERVAL '14 days'",
    "    FROM stock st LEFT JOIN sales s ON s.stock_id=st.id AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '14 days','YYYY-MM-DD')",
)


# ═════════════════════════════════════════════════════════════════════
# Fix 3 — /stock/aging
# ═════════════════════════════════════════════════════════════════════
print("\n[3/5] /stock/aging")

patch(
    "aging: to_char(sale_date) on 60-day window",
    "            SELECT 1 FROM sales s WHERE s.stock_id=st.id AND s.sale_date >= CURRENT_DATE - INTERVAL '60 days'",
    "            SELECT 1 FROM sales s WHERE s.stock_id=st.id AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD')",
)


# ═════════════════════════════════════════════════════════════════════
# Fix 4 — /tax/estimate
#   Two columns here: sales.sale_date and expenses.date — both TEXT
# ═════════════════════════════════════════════════════════════════════
print("\n[4/5] /tax/estimate")

patch(
    "tax-estimate: to_char(sale_date)",
    """    cur.execute("SELECT COALESCE(SUM(total_amount),0) as s FROM sales WHERE user_id=%s AND sale_date >= DATE_TRUNC('month', CURRENT_DATE)", (current_user.id,))""",
    """    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS s FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')",
        (current_user.id,))""",
)

patch(
    "tax-estimate: to_char(expenses.date)",
    """    cur.execute("SELECT COALESCE(SUM(amount),0) as e FROM expenses WHERE user_id=%s AND date >= DATE_TRUNC('month', CURRENT_DATE)", (current_user.id,))""",
    """    cur.execute(
        "SELECT COALESCE(SUM(amount),0) AS e FROM expenses "
        "WHERE user_id=%s AND date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')",
        (current_user.id,))""",
)


# ═════════════════════════════════════════════════════════════════════
# Fix 5 — /goals/velocity
# ═════════════════════════════════════════════════════════════════════
print("\n[5/5] /goals/velocity")

patch(
    "goals-velocity: to_char(sale_date)",
    """    cur.execute("SELECT COALESCE(SUM(total_amount),0) as m FROM sales WHERE user_id=%s AND sale_date >= DATE_TRUNC('month', CURRENT_DATE)", (current_user.id,))""",
    """    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS m FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')",
        (current_user.id,))""",
)


# ═════════════════════════════════════════════════════════════════════
# Write the patched file (with backup)
# ═════════════════════════════════════════════════════════════════════
if src != original:
    backup = f"{APP}.bak.{STAMP}"
    shutil.copy2(APP, backup)
    print(f"\nBackup saved: {backup}")

    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print(f"Wrote {len(src):,} bytes to {APP}")
else:
    print("\nNo changes — app.py already up to date.")


# ═════════════════════════════════════════════════════════════════════
# Verify with py_compile
# ═════════════════════════════════════════════════════════════════════
print("\nVerifying app.py compiles…")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK]   app.py compiles cleanly.")
else:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)
    if os.path.isfile(f"{APP}.bak.{STAMP}"):
        print(f"\nRestore backup with:")
        print(f"  copy \"{APP}.bak.{STAMP}\" {APP}")


# ═════════════════════════════════════════════════════════════════════
# Bonus safety checks
# ═════════════════════════════════════════════════════════════════════
print("\nBonus checks:")

if 'sale_date=CURRENT_DATE"' in src:
    print("  [WARN] a route still has 'sale_date=CURRENT_DATE\"' — check /day-close/variance")
else:
    print("  [OK]   no bare 'sale_date=CURRENT_DATE\"' found anywhere")

leftovers = re.findall(r"sale_date\s*[<>=]+\s*(?:CURRENT_DATE|DATE_TRUNC|NOW\()", src)
if leftovers:
    print(f"  [WARN] {len(leftovers)} remaining date comparison(s) may still need to_char — run the checker.")
else:
    print("  [OK]   no more bare CURRENT_DATE / DATE_TRUNC / NOW() on sale_date")


# ═════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print(f"Applied: {len(APPLIED)}   Skipped: {len(SKIPPED)}   Failed: {len(FAILED)}")
if FAILED:
    print("\nFailed (pattern not found — you may have edited by hand):")
    for f in FAILED:
        print(f"  - {f}")
    print("\nIf your code has slightly different whitespace, open app.py and")
    print("search for the route name to fix by hand. Every fix is:")
    print("  wrap the RHS of the date comparison in to_char(..., 'YYYY-MM-DD')")
print("=" * 60)

if not FAILED:
    print("\nNext steps:")
    print("  1. Restart Flask (Ctrl+C, then 'python app.py' or 'gunicorn app:app')")
    print("  2. Run the verification script from last time:")
    print("       python apply_fixes_6.py")
    print("  3. Confirm 9 passed, 0 failed")