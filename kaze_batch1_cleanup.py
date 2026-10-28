"""
kaze_batch1_cleanup.py — Batch 1 of route cleanup.

  Fix:     5 broken routes get real implementations
  Delete:  28 broken/duplicate/low-value routes removed entirely
  Disable: 47 rebuild-pending routes get a "coming soon" page (200, not 500)
  New:     coming_soon.html, stock_aging.html, stock_reorder.html

Run from the folder with app.py:
    python kaze_batch1_cleanup.py
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
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

with open(APP, encoding='utf-8') as f:
    src = f.read()

initial_routes = src.count('@app.route')

# Backup FIRST (before modifications)
backup_path = f"{APP}.bak.batch1_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}\n")

APPLIED = []
FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("[1/4] Fix 5 broken routes")
# ═══════════════════════════════════════════════════════════════════

FIXES = [
    ("/tax/estimate → real month-to-date tax view",
     """@app.route('/tax/estimate')
@login_required
def tax_estimate():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(total_amount),0) as s FROM sales WHERE user_id=%s AND sale_date >= DATE_TRUNC('month', CURRENT_DATE)", (current_user.id,))
    sales = float((cur.fetchone() or {}).get('s') or 0)
    cur.execute("SELECT COALESCE(SUM(amount),0) as e FROM expenses WHERE user_id=%s AND date >= DATE_TRUNC('month', CURRENT_DATE)", (current_user.id,))
    exp = float((cur.fetchone() or {}).get('e') or 0)
    cur.close(); conn.close()
    return render_template('tax.html', estimate=max(0,(sales-exp)*0.22), profit=sales-exp)""",
     """@app.route('/tax/estimate')
@login_required
def tax_estimate():
    uid = current_user.id
    settings_row = _get_settings_row(uid)
    rate = (settings_row['tax_rate'] if settings_row else 0) or 0
    symbol = (settings_row['currency_symbol'] if settings_row else '$') or '$'
    month_start = "to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD')"
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS s FROM sales WHERE user_id=%s AND sale_date >= " + month_start, (uid,))
    sales_rev = float((cur.fetchone() or {}).get('s') or 0)
    cur.execute("SELECT COALESCE(SUM(amount),0) AS e FROM income WHERE user_id=%s AND date >= " + month_start, (uid,))
    other_inc = float((cur.fetchone() or {}).get('e') or 0)
    cur.execute("SELECT COALESCE(SUM(amount),0) AS e FROM expenses WHERE user_id=%s AND date >= " + month_start, (uid,))
    expenses_total = float((cur.fetchone() or {}).get('e') or 0)
    cur.execute("SELECT COALESCE(SUM(total_cost),0) AS p FROM purchase_orders WHERE user_id=%s AND order_date >= " + month_start, (uid,))
    purchases = float((cur.fetchone() or {}).get('p') or 0)
    cur.close(); conn.close()
    taxable_out = sales_rev + other_inc
    output_tax = taxable_out * rate / 100 if rate else 0
    taxable_in = expenses_total + purchases
    input_tax = taxable_in * rate / 100 if rate else 0
    return render_template('tax.html',
        rate=rate, symbol=symbol,
        sales_rev=sales_rev, other_inc=other_inc,
        expenses=expenses_total, purchases=purchases,
        taxable_out=taxable_out, output_tax=output_tax,
        taxable_in=taxable_in, input_tax=input_tax,
        net_tax=output_tax - input_tax)"""),

    ("/tax/calendar → real upcoming deadlines",
     """@app.route('/tax/calendar')
@login_required
def tax_calendar():
    return render_template('tax.html', deadlines=['VAT return: 21st', 'PAYE: 10th'])""",
     """@app.route('/tax/calendar')
@login_required
def tax_calendar():
    uid = current_user.id
    today_iso = datetime.today().strftime('%Y-%m-%d')
    conn = get_db(); cur = conn.cursor()
    events = []
    cur.execute(
        "SELECT title, doc_date, amount FROM bookkeeping_docs "
        "WHERE user_id=%s AND status IN ('draft','issued') AND doc_date >= %s "
        "ORDER BY doc_date LIMIT 20",
        (uid, today_iso))
    for r in cur.fetchall() or []:
        events.append({'date': r['doc_date'] or '—', 'kind': 'Document',
                       'title': r['title'], 'extra': _format_money(r['amount'] or 0)})
    cur.execute(
        "SELECT title, due_date FROM tasks WHERE user_id=%s AND done=0 "
        "AND due_date != '' AND due_date >= %s ORDER BY due_date LIMIT 20",
        (uid, today_iso))
    for r in cur.fetchall() or []:
        events.append({'date': r['due_date'], 'kind': 'Task',
                       'title': r['title'], 'extra': 'due'})
    cur.close(); conn.close()
    events.sort(key=lambda e: e['date'] or '9999')
    return render_template('calendar.html', events=events, today=today_iso)"""),

    ("/goals/velocity → redirect to /goals",
     """@app.route('/goals/velocity')
@login_required
def goals_velocity():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(total_amount),0) as m FROM sales WHERE user_id=%s AND sale_date >= DATE_TRUNC('month', CURRENT_DATE)", (current_user.id,))
    month = float((cur.fetchone() or {}).get('m') or 0)
    cur.close(); conn.close()
    day = max(datetime.today().day, 1)
    return render_template('goals.html', month_so_far=month, projected=round(month/day*30,2))""",
     """@app.route('/goals/velocity')
@login_required
def goals_velocity():
    return redirect(url_for('goals'))"""),

    ("/stock/aging → real aging page",
     """@app.route('/stock/aging')
@login_required
def stock_aging():
    conn = get_db(); cur = conn.cursor()
    cur.execute(\"\"\"
        SELECT st.product_name, st.quantity FROM stock st
        WHERE st.user_id=%s AND NOT EXISTS (
            SELECT 1 FROM sales s WHERE s.stock_id=st.id AND s.sale_date >= CURRENT_DATE - INTERVAL '60 days'
        ) LIMIT 12
    \"\"\", (current_user.id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template('stock.html', items=rows, aging=True)""",
     """@app.route('/stock/aging')
@login_required
def stock_aging():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute(\"\"\"
        SELECT st.id, st.product_name, st.quantity, st.cost_price, st.selling_price,
               (SELECT MAX(s.sale_date) FROM sales s WHERE s.stock_id=st.id AND s.user_id=%s) AS last_sold
        FROM stock st WHERE st.user_id=%s ORDER BY st.product_name
    \"\"\", (uid, uid))
    rows = cur.fetchall() or []
    cur.close(); conn.close()
    today = datetime.today().date()
    aged = []
    for r in rows:
        last = (r.get('last_sold') or '')[:10]
        try:
            days = (today - datetime.strptime(last, '%Y-%m-%d').date()).days if last else 999
        except ValueError:
            days = 999
        aged.append({
            'id': r['id'], 'product_name': r['product_name'],
            'quantity': r['quantity'], 'cost_price': r['cost_price'],
            'selling_price': r['selling_price'],
            'last_sold': last or 'never', 'days_aging': days,
            'tied_up': float(r['quantity'] or 0) * float(r['cost_price'] or 0),
        })
    aged.sort(key=lambda x: -x['days_aging'])
    return render_template('stock_aging.html', items=aged)"""),

    ("/stock/reorder-optimizer → real suggestions page",
     """@app.route('/stock/reorder-optimizer')
@login_required
def stock_reorder_optimizer():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COALESCE(low_stock_threshold,10) as th FROM settings WHERE user_id=%s", (current_user.id,))
    th = float((cur.fetchone() or {}).get('th') or 10)
    cur.execute(\"\"\"
        SELECT st.product_name, st.quantity, COALESCE(SUM(s.quantity_sold),0)/14.0 as vel
        FROM stock st LEFT JOIN sales s ON s.stock_id=st.id AND s.sale_date >= CURRENT_DATE - INTERVAL '14 days'
        WHERE st.user_id=%s AND st.quantity <= %s
        GROUP BY st.id, st.product_name, st.quantity ORDER BY vel DESC LIMIT 12
    \"\"\", (current_user.id, th))
    rows = cur.fetchall()
    suggestions = [{'name': r['product_name'], 'current': r['quantity'], 'reorder': max(0, int((r['vel'] or 0)*21 - r['quantity']))} for r in rows]
    cur.close(); conn.close()
    return render_template('stock.html', items=[], suggestions=suggestions)""",
     """@app.route('/stock/reorder-optimizer')
@login_required
def stock_reorder_optimizer():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT low_stock_threshold FROM settings WHERE user_id=%s", (uid,))
    srow = cur.fetchone() or {}
    threshold = float(srow.get('low_stock_threshold') or 10)
    cur.execute(\"\"\"
        SELECT st.id, st.product_name, st.quantity, st.cost_price,
               COALESCE(SUM(s.quantity_sold),0) AS units_14d
        FROM stock st
        LEFT JOIN sales s ON s.stock_id=st.id AND s.user_id=%s
            AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '14 days','YYYY-MM-DD')
        WHERE st.user_id=%s
        GROUP BY st.id, st.product_name, st.quantity, st.cost_price
        ORDER BY st.product_name
    \"\"\", (uid, uid))
    rows = cur.fetchall() or []
    cur.close(); conn.close()
    suggestions = []
    for r in rows:
        vel = float(r.get('units_14d') or 0) / 14.0
        qty = float(r.get('quantity') or 0)
        days_of_stock = (qty / vel) if vel > 0 else 999
        suggest = max(0, int(vel * 21 - qty))
        if suggest > 0 or qty <= threshold:
            suggestions.append({
                'id': r['id'], 'product_name': r['product_name'],
                'quantity': qty, 'velocity': round(vel, 2),
                'days_left': round(days_of_stock, 1) if days_of_stock < 900 else '∞',
                'suggested': suggest,
                'cost_estimate': suggest * float(r.get('cost_price') or 0),
            })
    suggestions.sort(key=lambda x: x['days_left'] if isinstance(x['days_left'], (int, float)) else 9999)
    return render_template('stock_reorder.html', suggestions=suggestions)"""),
]

fixes_ok = 0
for label, old, new in FIXES:
    if old not in src:
        print(f"  [SKIP] {label} — pattern not found (already fixed?)")
        continue
    src = src.replace(old, new, 1)
    fixes_ok += 1
    print(f"  [OK]   {label}")
    APPLIED.append(label)

# ═══════════════════════════════════════════════════════════════════
print("\n[2/4] Delete 28 duplicate/low-value routes")
# ═══════════════════════════════════════════════════════════════════

DELETE_PATHS = [
    '/stock/dead', '/customers/segments', '/purchase-orders/status',
    '/payments/timeline', '/recurring/pause', '/recurring/next',
    '/banking/forecast', '/snapshot/export', '/turnover/abc-view', '/top/ltv',
    '/sales/peak-hours', '/customers/next-offer', '/bookkeeping/categorize',
    '/accounts/closing', '/forecast/accuracy', '/forecast/drivers',
    '/health/benchmark', '/loyalty/expiry', '/loyalty/liability',
    '/counter/speed', '/day-close/checklist', '/market/position',
    '/market/trend', '/profit/elasticity', '/notes/clusters',
    '/reports/board', '/counter/upsell', '/shop/abandon',
]

deleted_ok = 0
for path in DELETE_PATHS:
    pat = re.compile(
        r"@app\.route\('" + re.escape(path) + r"'[^)]*\)\n"
        r"(?:@[^\n]+\n)*"
        r"def \w+\([^)]*\):\n"
        r".*?"
        r"(?=\n@app\.|\n#|\ndef |\nif __name__|\Z)",
        re.DOTALL,
    )
    m = pat.search(src)
    if m:
        src = src[:m.start()] + src[m.end():]
        deleted_ok += 1
        print(f"  [DEL]  {path}")
    else:
        print(f"  [SKIP] {path} — not found")
        FAILED.append(f"delete {path}")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/4] Add 'coming soon' hook for rebuild-pending routes")
# ═══════════════════════════════════════════════════════════════════

DISABLED_PATHS = [
    '/sales/margin-alert', '/sales/velocity', '/sales/repeat-rate',
    '/customers/churn-risk', '/customers/lifetime',
    '/collections/schedule', '/collections/aging',
    '/stock/abc',
    '/suppliers/lead-time', '/suppliers/reliability',
    '/purchase-orders/autofill',
    '/bookkeeping/anomaly-scan', '/bookkeeping/duplicate-check',
    '/accounts/integrity', '/accounts/trial-balance',
    '/payments/fees',
    '/forecast/scenarios',
    '/health/priority', '/health/history',
    '/goals/milestones',
    '/reports/variance',
    '/stats/cohort', '/stats/seasonality',
    '/insights/opportunities', '/insights/risks',
    '/team/permissions', '/team/activity',
    '/tasks/priority', '/tasks/blockers',
    '/notes/actions',
    '/reminders/context', '/reminders/escalation',
    '/calendar/conflicts', '/calendar/free',
    '/settings/health', '/settings/audit',
    '/rfm/actions',
    '/whatsapp/log', '/whatsapp/templates',
    '/documents/approval', '/documents/versions',
    '/banking/reconcile',
    '/investments/risk',
    '/services/utilization', '/services/yield',
    '/day-close/variance',
]

disabled_block = (
    "\n\n# ── Disabled pending rebuild (Batch 2+) ────────────────────\n"
    "_DISABLED_PATHS = frozenset({\n"
    "    " + ",\n    ".join(repr(p) for p in DISABLED_PATHS) + ",\n"
    "})\n"
    "\n\n"
    "@app.before_request\n"
    "def _kaze_block_disabled():\n"
    "    if request.path in _DISABLED_PATHS:\n"
    "        return render_template('coming_soon.html', path=request.path), 200\n"
)

if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + disabled_block + "\n\n" + src[idx:]
else:
    src += "\n\n" + disabled_block
print(f"  [OK]   before_request hook for {len(DISABLED_PATHS)} disabled paths")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/4] Write app.py + create templates")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   wrote {APP}  ({initial_routes} -> {final_routes} @app.route decorators)")

os.makedirs('templates', exist_ok=True)

TEMPLATES = {
    'templates/coming_soon.html': '''{% extends "base.html" %}
{% block title %}Coming soon{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="hourglass"></i> Coming soon</h1>
<p>This page is being built as part of an ongoing feature update.</p></div></div>
<div class="widget">
  <p style="color:var(--text2);">The page you requested — <code>{{ path }}</code> — is on the roadmap but hasn't shipped yet. It will land in an upcoming release.</p>
  <p style="margin-top:1rem;"><a href="{{ url_for('dashboard') }}" class="btn-secondary">Back to dashboard</a></p>
</div>
{% endblock %}
''',
    'templates/stock_aging.html': '''{% extends "base.html" %}
{% block title %}Stock Aging{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="clock"></i> Stock Aging</h1>
<p>How long each product has been sitting unsold. Capital tied up grows with age.</p></div></div>
{% if items %}
<div class="stat-grid">
  <div class="stat-chip"><span>Products</span><strong>{{ items|length }}</strong></div>
  <div class="stat-chip"><span>Never sold</span><strong>{{ items|selectattr('days_aging','ge',900)|list|length }}</strong></div>
  <div class="stat-chip"><span>Over 90 days</span><strong>{{ items|selectattr('days_aging','ge',90)|list|length }}</strong></div>
  <div class="stat-chip"><span>Over 60 days</span><strong>{{ items|selectattr('days_aging','ge',60)|list|length }}</strong></div>
</div>
<div class="table-wrapper"><table>
<thead><tr><th>Product</th><th>Qty</th><th>Last Sold</th><th>Days Aging</th><th>Cost Tied Up</th><th>Selling Value</th></tr></thead>
<tbody>
{% for i in items %}
<tr {% if i.days_aging >= 90 %}style="background:var(--danger-dim);"{% elif i.days_aging >= 60 %}style="background:rgba(224,160,48,0.08);"{% endif %}>
  <td>{{ i.product_name }}</td><td>{{ i.quantity }}</td><td>{{ i.last_sold }}</td>
  <td>{{ 'never' if i.days_aging >= 900 else i.days_aging ~ ' days' }}</td>
  <td>{{ money(i.tied_up) }}</td><td>{{ money(i.quantity * i.selling_price) }}</td>
</tr>
{% endfor %}
</tbody></table></div>
{% else %}
<div class="widget"><p style="color:var(--text3);">No stock items yet. Add products on the <a href="{{ url_for('stock') }}">Stock</a> page.</p></div>
{% endif %}
{% endblock %}
''',
    'templates/stock_reorder.html': '''{% extends "base.html" %}
{% block title %}Reorder Optimizer{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="package-plus"></i> Reorder Optimizer</h1>
<p>Suggested order quantities based on 14-day sales velocity and current stock.</p></div>
<a href="{{ url_for('purchase_orders') }}" class="btn-secondary">Open purchase orders</a></div>
{% if suggestions %}
<div class="table-wrapper"><table>
<thead><tr><th>Product</th><th>Current</th><th>Vel/day</th><th>Days left</th><th>Suggested</th><th>Est. Cost</th></tr></thead>
<tbody>
{% for s in suggestions %}
<tr {% if s.days_left is number and s.days_left < 7 %}style="background:var(--danger-dim);"{% elif s.days_left is number and s.days_left < 14 %}style="background:rgba(224,160,48,0.08);"{% endif %}>
  <td>{{ s.product_name }}</td><td>{{ s.quantity }}</td><td>{{ s.velocity }}</td>
  <td>{{ s.days_left }}</td><td>{{ s.suggested }}</td><td>{{ money(s.cost_estimate) }}</td>
</tr>
{% endfor %}
</tbody></table></div>
<p style="margin-top:1rem;font-size:0.85rem;color:var(--text3);">Suggested quantities aim for 21 days of stock at current velocity. Use <a href="{{ url_for('stock') }}">Stock</a> → Reorder low stock to auto-create draft POs.</p>
{% else %}
<div class="widget"><p style="color:var(--text3);">All stock is currently healthy — no reorder suggestions.</p></div>
{% endif %}
{% endblock %}
''',
}

for name, content in TEMPLATES.items():
    with open(name, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [OK]   {name}")

# ═══════════════════════════════════════════════════════════════════
print("\n[COMPILE]")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
print(f"  Fixes applied:   {fixes_ok}/5")
print(f"  Routes deleted:  {deleted_ok}/28")
print(f"  Routes disabled: {len(DISABLED_PATHS)}")
print(f"  Templates new:   {len(TEMPLATES)}")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if fixes_ok < 5 or deleted_ok < 28:
    print("\nNot all fixes/deletes landed. Review above, then decide:")
    print(f"  - Run again (safe — SKIP protects already-applied fixes)")
    print(f"  - Or restore: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 1 complete. Test locally, then deploy:

1. LOCAL TEST:

   python app.py

   Visit and confirm:
     /tax/estimate              → month-to-date tax summary, all values fill in
     /tax/calendar              → upcoming documents + tasks, no crash
     /stock/aging               → table of aged products, sorted oldest first
     /stock/reorder-optimizer   → suggestion table (or "healthy" message)

   Visit and confirm clean "coming soon":
     /sales/velocity            → 200 coming-soon page (NOT 500)
     /health/history            → 200 coming-soon page
     /whatsapp/log              → 200 coming-soon page

   Visit and confirm 404:
     /stock/dead                → 404 (deleted)
     /market/position           → 404 (deleted)

   Everything else (dashboard, sales, stock, customers, plans, subscription flow, etc.) MUST still work.

2. COMMIT AND DEPLOY:

   git add app.py kaze_batch1_cleanup.py templates/coming_soon.html templates/stock_aging.html templates/stock_reorder.html
   git commit -m "Batch 1: fix 5 routes, delete 28 dups/weak, disable 47 pending rebuild"
   git push

3. Watch Render deploy. Re-test the same set of URLs on production.

4. Once confirmed, delete backup:
   rm app.py.bak.batch1_*
""")