"""
apply_fixes_8.py — fix the /tax/estimate and /tax/calendar template
variable mismatch.

Both routes render 'tax.html', which expects 11 variables:
    rate, symbol,
    sales_rev, other_inc, expenses, purchases,
    taxable_out, output_tax, taxable_in, input_tax, net_tax

But /tax/estimate was only passing (estimate, profit), and
/tax/calendar was only passing (deadlines) — so every money cell
rendered as $0.00.

Fix:
  * /tax/estimate  → recomputes the same block as /tax_summary but
                     restricted to the current month, and passes
                     every variable tax.html actually reads.
  * /tax/calendar  → redirect to tax_summary (its original body
                     didn't render anything useful).

Run from the folder with app.py:
    python apply_fixes_8.py

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


def apply_regex(label, pattern, replacement):
    global src
    match = pattern.search(src)
    if not match:
        # Either already fixed (new code present) or pattern drift
        if 'def tax_estimate():' in src and 'sales_rev=sales_rev' in src and 'def tax_estimate' in src:
            print(f"  [SKIP] {label} — already fixed")
            SKIPPED.append(label)
        else:
            print(f"  [FAIL] {label} — pattern not found")
            FAILED.append(label)
        return
    src = src[:match.start()] + replacement + src[match.end():]
    print(f"  [OK]   {label}")
    APPLIED.append(label)


# ═════════════════════════════════════════════════════════════════════
# Fix 1 — /tax/estimate: pass every variable tax.html needs
# ═════════════════════════════════════════════════════════════════════
print("[1/2] /tax/estimate — real variables for tax.html")

TAX_ESTIMATE_PATTERN = re.compile(
    r"@app\.route\('/tax/estimate'\)"
    r"\s*\n@login_required"
    r"\s*\ndef tax_estimate\(\):"
    r".*?"
    r"return render_template\('tax\.html', estimate=max\(0,\(sales-exp\)\*0\.22\), profit=sales-exp\)",
    re.DOTALL,
)

TAX_ESTIMATE_NEW = '''@app.route('/tax/estimate')
@login_required
def tax_estimate():
    """Month-to-date tax estimate — same shape as tax_summary."""
    uid = current_user.id
    settings_row = _get_settings_row(uid)
    rate = (settings_row['tax_rate'] if settings_row else 0) or 0
    symbol = (settings_row['currency_symbol'] if settings_row else '$') or '$'
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS s FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')",
        (uid,))
    sales_rev = float((cur.fetchone() or {}).get('s') or 0)
    cur.execute(
        "SELECT COALESCE(SUM(amount),0) AS e FROM income "
        "WHERE user_id=%s AND date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')",
        (uid,))
    other_inc = float((cur.fetchone() or {}).get('e') or 0)
    cur.execute(
        "SELECT COALESCE(SUM(amount),0) AS e FROM expenses "
        "WHERE user_id=%s AND date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')",
        (uid,))
    expenses = float((cur.fetchone() or {}).get('e') or 0)
    cur.execute(
        "SELECT COALESCE(SUM(total_cost),0) AS p FROM purchase_orders "
        "WHERE user_id=%s AND order_date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')",
        (uid,))
    purchases = float((cur.fetchone() or {}).get('p') or 0)
    cur.close()
    conn.close()
    taxable_out = sales_rev + other_inc
    output_tax = taxable_out * rate / 100 if rate else 0
    taxable_in = expenses + purchases
    input_tax = taxable_in * rate / 100 if rate else 0
    return render_template(
        'tax.html',
        rate=rate, symbol=symbol,
        sales_rev=sales_rev, other_inc=other_inc,
        expenses=expenses, purchases=purchases,
        taxable_out=taxable_out, output_tax=output_tax,
        taxable_in=taxable_in, input_tax=input_tax,
        net_tax=output_tax - input_tax,
    )'''

apply_regex("/tax/estimate — full variable set", TAX_ESTIMATE_PATTERN, TAX_ESTIMATE_NEW)


# ═════════════════════════════════════════════════════════════════════
# Fix 2 — /tax/calendar: was rendering tax.html with a useless
#          'deadlines' kwarg. Redirect to the working /tax page.
# ═════════════════════════════════════════════════════════════════════
print("\n[2/2] /tax/calendar — redirect to tax_summary")

TAX_CALENDAR_PATTERN = re.compile(
    r"@app\.route\('/tax/calendar'\)"
    r"\s*\n@login_required"
    r"\s*\ndef tax_calendar\(\):"
    r"\s*\n    return render_template\('tax\.html', deadlines=\['VAT return: 21st', 'PAYE: 10th'\]\)",
    re.DOTALL,
)

TAX_CALENDAR_NEW = '''@app.route('/tax/calendar')
@login_required
def tax_calendar():
    """Old route kept for bookmark compatibility."""
    return redirect(url_for('tax_summary'))'''

apply_regex("/tax/calendar — redirect", TAX_CALENDAR_PATTERN, TAX_CALENDAR_NEW)


# ═════════════════════════════════════════════════════════════════════
# Write with backup
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
# Verify compile
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
        print(f"\nRestore with:")
        print(f"  copy \"{APP}.bak.{STAMP}\" {APP}")


# ═════════════════════════════════════════════════════════════════════
# Bonus: verify tax.html uses only variables we now pass
# ═════════════════════════════════════════════════════════════════════
print("\nBonus: tax.html variable audit")

html_path = os.path.join('templates', 'tax.html')
if not os.path.isfile(html_path):
    print("  [SKIP] templates/tax.html not found")
else:
    with open(html_path, 'r', encoding='utf-8') as fh:
        html = fh.read()
    used = set(re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)', html))
    # money() is a registered Jinja filter / context helper
    # url_for is a Jinja built-in
    allowed = {
        'rate', 'symbol',
        'sales_rev', 'other_inc', 'expenses', 'purchases',
        'taxable_out', 'output_tax', 'taxable_in', 'input_tax', 'net_tax',
        'money', 'url_for',
    }
    missing = used - allowed
    if missing:
        print(f"  [WARN] tax.html references variables the route does not pass:")
        for v in sorted(missing):
            print(f"         {{ {v} }}")
        print("         (these will render as empty strings)")
    else:
        print(f"  [OK]   tax.html uses {len(used)} variables — all supplied")


# ═════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print(f"Applied: {len(APPLIED)}   Skipped: {len(SKIPPED)}   Failed: {len(FAILED)}")
if FAILED:
    print("\nFailed (pattern not found — whitespace may differ from the guide):")
    for f in FAILED:
        print(f"  - {f}")
    print("\nIf a fix failed, open app.py and search for the route name.")
    print("Both routes must pass these 11 vars to render_template('tax.html', ...):")
    print("  rate, symbol, sales_rev, other_inc, expenses, purchases,")
    print("  taxable_out, output_tax, taxable_in, input_tax, net_tax")
print("=" * 60)