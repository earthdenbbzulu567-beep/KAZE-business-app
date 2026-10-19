"""
apply_fixes_10_insights.py — replace the /insights stub with a live page.

Before:
    Route:    Two SQL queries, then tips hardcoded as:
              "Sales are moderate. Try promotional offers."
    Template: A single card with a bullet list.

After:
    6 real insight cards computed from your actual data:
      1. Best seller (30 days) — name, units, revenue, profit
      2. Worst margin product (60 days, min 3 tickets) — margin %
      3. Low stock count vs Settings threshold
      4. Dead stock count (no sales in 60 days)
      5. At-risk customers (bought last month, not this month)
      6. Payment mix (which channel your money comes through)

    Plus stock value cards and a payment breakdown table.

Run from the folder with app.py:
    python apply_fixes_10_insights.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'
TPL = os.path.join('templates', 'insights.html')

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found. Run from the project root.")
    sys.exit(1)

app_backup = f"{APP}.bak.{STAMP}"
shutil.copy2(APP, app_backup)
print(f"Backup saved: {app_backup}")

if os.path.isfile(TPL):
    tpl_backup = f"{TPL}.bak.{STAMP}"
    shutil.copy2(TPL, tpl_backup)
    print(f"Backup saved: {tpl_backup}")

# ─────────────────────────────────────────────────────────────────────
# 1 — replace the route
# ─────────────────────────────────────────────────────────────────────
print("\n[1/3] Patching /insights route in app.py…")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

# Match the whole existing insights() function body from decorator to next @app or top-level def
ROUTE_PATTERN = re.compile(
    r"@app\.route\('/insights'\)\n"
    r"@login_required\n"
    r"def insights\(\):\n"
    r".*?"
    r"(?=\n@app\.|\n#|\ndef |\nif __name__|\Z)",
    re.DOTALL,
)

NEW_ROUTE = r'''@app.route('/insights')
@login_required
def insights():
    """Live business insights computed from sales, stock, and customers."""
    uid = current_user.id
    conn = get_db()
    cur = conn.cursor()

    # 1 — last 30 days summary
    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS revenue, "
        "COALESCE(SUM(profit),0) AS profit, "
        "COUNT(*) AS tickets, "
        "COUNT(DISTINCT customer_id) AS customers "
        "FROM sales WHERE user_id=%s "
        "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')",
        (uid,))
    r30 = cur.fetchone() or {}
    revenue_30 = float(r30.get('revenue') or 0)
    profit_30 = float(r30.get('profit') or 0)
    tickets_30 = int(r30.get('tickets') or 0)
    customers_30 = int(r30.get('customers') or 0)

    # 2 — best seller last 30 days
    cur.execute(
        "SELECT st.product_name, "
        "COALESCE(SUM(s.quantity_sold),0) AS units, "
        "COALESCE(SUM(s.total_amount),0) AS revenue, "
        "COALESCE(SUM(s.profit),0) AS profit "
        "FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
        "WHERE s.user_id=%s "
        "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
        "GROUP BY st.product_name "
        "ORDER BY revenue DESC LIMIT 1",
        (uid,))
    best = cur.fetchone()

    # 3 — worst margin, min 3 tickets, last 60 days
    cur.execute(
        "SELECT st.product_name, "
        "COALESCE(SUM(s.total_amount),0) AS revenue, "
        "COALESCE(SUM(s.profit),0) AS profit, "
        "COUNT(*) AS tickets "
        "FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
        "WHERE s.user_id=%s "
        "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
        "GROUP BY st.product_name HAVING COUNT(*) >= 3",
        (uid,))
    margin_rows = []
    for r in (cur.fetchall() or []):
        rev = float(r.get('revenue') or 0)
        pft = float(r.get('profit') or 0)
        if rev > 0:
            margin_rows.append({
                'name': r.get('product_name') or 'Item',
                'revenue': rev,
                'profit': pft,
                'tickets': int(r.get('tickets') or 0),
                'margin_pct': round(pft / rev * 100, 1),
            })
    margin_rows.sort(key=lambda x: x['margin_pct'])
    worst_margin = margin_rows[0] if margin_rows else None

    # 4 — low stock
    cur.execute(
        "SELECT COUNT(*) AS n FROM stock st "
        "WHERE st.user_id=%s AND st.quantity <= COALESCE("
        "(SELECT low_stock_threshold FROM settings WHERE user_id=%s), 10)",
        (uid, uid))
    low_stock = int((cur.fetchone() or {}).get('n') or 0)

    # 5 — dead stock (no sales in 60 days)
    cur.execute(
        "SELECT COUNT(*) AS n FROM stock st "
        "WHERE st.user_id=%s AND NOT EXISTS ("
        "SELECT 1 FROM sales s WHERE s.stock_id = st.id "
        "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD'))",
        (uid,))
    dead_stock = int((cur.fetchone() or {}).get('n') or 0)

    # 6 — customers at risk (bought last month, not this month)
    cur.execute(
        "SELECT COUNT(*) AS n FROM ("
        "SELECT s.customer_id FROM sales s "
        "WHERE s.user_id=%s AND s.customer_id IS NOT NULL "
        "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
        "AND s.sale_date < to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD') "
        "GROUP BY s.customer_id) lm "
        "WHERE lm.customer_id NOT IN ("
        "SELECT DISTINCT s.customer_id FROM sales s "
        "WHERE s.user_id=%s AND s.customer_id IS NOT NULL "
        "AND s.sale_date >= to_char(DATE_TRUNC('month', CURRENT_DATE),'YYYY-MM-DD'))",
        (uid, uid))
    at_risk = int((cur.fetchone() or {}).get('n') or 0)

    # 7 — payment mix last 30 days
    cur.execute(
        "SELECT COALESCE(payment_method,'cash') AS method, "
        "COUNT(*) AS tickets, COALESCE(SUM(total_amount),0) AS revenue "
        "FROM sales WHERE user_id=%s "
        "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
        "GROUP BY payment_method ORDER BY revenue DESC",
        (uid,))
    payment_mix = []
    for r in (cur.fetchall() or []):
        payment_mix.append({
            'method': (r.get('method') or 'cash').title(),
            'tickets': int(r.get('tickets') or 0),
            'revenue': float(r.get('revenue') or 0),
        })

    # 8 — stock value at cost / at selling price
    cur.execute(
        "SELECT COALESCE(SUM(quantity * cost_price),0) AS cost_value, "
        "COALESCE(SUM(quantity * selling_price),0) AS sell_value "
        "FROM stock WHERE user_id=%s",
        (uid,))
    sv = cur.fetchone() or {}
    stock_cost_value = float(sv.get('cost_value') or 0)
    stock_sell_value = float(sv.get('sell_value') or 0)

    cur.close()
    conn.close()

    insights = []

    if best and float(best.get('revenue') or 0) > 0:
        insights.append({
            'severity': 'success',
            'icon': 'trending-up',
            'title': 'Top seller: {}'.format(best.get('product_name') or 'Item'),
            'detail': '{} revenue · {} units · {} profit in the last 30 days.'.format(
                _format_money(float(best.get('revenue') or 0)),
                int(float(best.get('units') or 0)),
                _format_money(float(best.get('profit') or 0))),
            'action_label': 'Open stock',
            'action_url': url_for('stock'),
        })
    else:
        insights.append({
            'severity': 'info',
            'icon': 'package',
            'title': 'No sales in the last 30 days',
            'detail': 'Record a sale or open Counter to start seeing top-seller insight.',
            'action_label': 'Open counter',
            'action_url': url_for('counter'),
        })

    if worst_margin:
        sev = 'danger' if worst_margin['margin_pct'] < 0 else ('warn' if worst_margin['margin_pct'] < 15 else 'info')
        insights.append({
            'severity': sev,
            'icon': 'trending-down',
            'title': 'Lowest margin: {}'.format(worst_margin['name']),
            'detail': '{}% margin over {} tickets. Revenue {} · profit {}. Consider repricing or dropping.'.format(
                worst_margin['margin_pct'], worst_margin['tickets'],
                _format_money(worst_margin['revenue']),
                _format_money(worst_margin['profit'])),
            'action_label': 'Edit prices',
            'action_url': url_for('stock'),
        })
    else:
        insights.append({
            'severity': 'info',
            'icon': 'bar-chart-3',
            'title': 'Not enough sales to score margins',
            'detail': 'Need at least 3 tickets on a product in the last 60 days to detect a low-margin item.',
            'action_label': 'Record a sale',
            'action_url': url_for('sales'),
        })

    if low_stock > 0:
        insights.append({
            'severity': 'danger' if low_stock >= 5 else 'warn',
            'icon': 'alert-triangle',
            'title': '{} product(s) below stock threshold'.format(low_stock),
            'detail': 'Restock soon. Change the threshold in Settings → Low stock threshold.',
            'action_label': 'Open stock',
            'action_url': url_for('stock'),
        })
    else:
        insights.append({
            'severity': 'success',
            'icon': 'check-circle',
            'title': 'Stock levels healthy',
            'detail': 'No products are below the low-stock threshold right now.',
            'action_label': 'Review stock',
            'action_url': url_for('stock'),
        })

    if dead_stock > 0:
        insights.append({
            'severity': 'warn',
            'icon': 'package',
            'title': '{} dead-stock item(s)'.format(dead_stock),
            'detail': 'No sales in the last 60 days. Bundle or discount to free up cash.',
            'action_label': 'Open stock',
            'action_url': url_for('stock'),
        })

    if at_risk > 0:
        insights.append({
            'severity': 'warn',
            'icon': 'users',
            'title': '{} customer(s) at risk'.format(at_risk),
            'detail': 'Bought last month, not this month. A small reminder usually wins them back.',
            'action_label': 'Open customers',
            'action_url': url_for('customers'),
        })
    elif customers_30 > 0:
        insights.append({
            'severity': 'success',
            'icon': 'users',
            'title': 'Customers are coming back',
            'detail': '{} distinct customer(s) bought in the last 30 days.'.format(customers_30),
            'action_label': 'Open customers',
            'action_url': url_for('customers'),
        })

    if payment_mix:
        top = payment_mix[0]
        if len(payment_mix) > 1 and revenue_30 > 0:
            share = round(top['revenue'] / revenue_30 * 100, 1)
            detail = '{}% of revenue ({}) came via {} in the last 30 days.'.format(
                share, _format_money(top['revenue']), top['method'])
        else:
            detail = 'Every sale last 30 days used {}.'.format(top['method'])
        insights.append({
            'severity': 'info',
            'icon': 'credit-card',
            'title': 'Payment mix',
            'detail': detail,
            'action_label': 'Open payments',
            'action_url': url_for('payments'),
        })

    return render_template(
        'insights.html',
        insights=insights,
        revenue_30=revenue_30,
        profit_30=profit_30,
        tickets_30=tickets_30,
        customers_30=customers_30,
        low_stock=low_stock,
        dead_stock=dead_stock,
        at_risk=at_risk,
        stock_cost_value=stock_cost_value,
        stock_sell_value=stock_sell_value,
        payment_mix=payment_mix,
    )


'''

match = ROUTE_PATTERN.search(src)
if not match:
    if "def insights():" in src and "worst_margin" in src:
        print("  [SKIP] /insights already patched")
    else:
        print("  [FAIL] /insights function not found in app.py")
        print("         Restore backup, then run again.")
        sys.exit(1)
else:
    src = src[:match.start()] + NEW_ROUTE + src[match.end():]
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print("  [OK]   /insights route replaced")

# ─────────────────────────────────────────────────────────────────────
# 2 — rewrite templates/insights.html
# ─────────────────────────────────────────────────────────────────────
print("\n[2/3] Rewriting templates/insights.html…")

NEW_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Business Insights{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="lightbulb"></i> Business Insights</h1>
    <p>Live, actionable facts computed from your last 30–60 days of sales, stock, and customers.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Revenue (30d)</span><strong>{{ money(revenue_30) }}</strong></div>
  <div class="stat-chip"><span>Profit (30d)</span><strong>{{ money(profit_30) }}</strong></div>
  <div class="stat-chip"><span>Tickets (30d)</span><strong>{{ tickets_30 }}</strong></div>
  <div class="stat-chip"><span>Customers (30d)</span><strong>{{ customers_30 }}</strong></div>
  <div class="stat-chip"><span>Low stock</span><strong>{{ low_stock }}</strong></div>
  <div class="stat-chip"><span>Dead stock</span><strong>{{ dead_stock }}</strong></div>
</div>

<h2>Recommendations</h2>
<div class="insight-grid">
{% for ins in insights %}
  <div class="insight-card insight-{{ ins.severity }}">
    <div class="insight-icon"><i data-lucide="{{ ins.icon }}"></i></div>
    <div class="insight-body">
      <h3>{{ ins.title }}</h3>
      <p>{{ ins.detail }}</p>
      <a href="{{ ins.action_url }}" class="insight-action">{{ ins.action_label }} →</a>
    </div>
  </div>
{% endfor %}
</div>

{% if payment_mix %}
<h2>Payment mix (30 days)</h2>
<div class="table-wrapper">
<table>
<thead><tr><th>Method</th><th>Tickets</th><th>Revenue</th><th>% of total</th></tr></thead>
<tbody>
{% for p in payment_mix %}
<tr>
  <td>{{ p.method }}</td>
  <td>{{ p.tickets }}</td>
  <td>{{ money(p.revenue) }}</td>
  <td>{% if revenue_30 > 0 %}{{ ((p.revenue / revenue_30) * 100)|round(1) }}%{% else %}—{% endif %}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% endif %}

<div class="widget">
  <h2>Stock value</h2>
  <div class="stat-grid" style="margin:0;">
    <div class="stat-chip"><span>At cost</span><strong>{{ money(stock_cost_value) }}</strong></div>
    <div class="stat-chip"><span>At selling price</span><strong>{{ money(stock_sell_value) }}</strong></div>
    <div class="stat-chip"><span>Potential margin</span><strong>{{ money(stock_sell_value - stock_cost_value) }}</strong></div>
  </div>
</div>

<style>
.insight-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
  margin: 1rem 0 1.5rem;
}
.insight-card {
  display: flex;
  gap: 0.9rem;
  padding: 1.1rem 1.2rem;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface);
  border-left-width: 4px;
  transition: transform 0.16s var(--ease-out), border-color 0.16s ease, box-shadow 0.16s ease;
}
.insight-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0,0,0,0.18);
}
.insight-card.insight-success { border-left-color: var(--green); }
.insight-card.insight-info    { border-left-color: #3498db; }
.insight-card.insight-warn    { border-left-color: #e0a030; }
.insight-card.insight-danger  { border-left-color: #e74c3c; }
.insight-icon {
  width: 40px; height: 40px; flex-shrink: 0;
  display: grid; place-items: center;
  border-radius: 10px;
  background: var(--surface2);
}
.insight-success .insight-icon { background: var(--green-dim); color: var(--green); }
.insight-info .insight-icon    { background: rgba(52,152,219,0.12); color: #3498db; }
.insight-warn .insight-icon    { background: rgba(224,160,48,0.12); color: #e0a030; }
.insight-danger .insight-icon  { background: rgba(231,76,60,0.12); color: #e74c3c; }
.insight-icon svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.75; }
.insight-body { flex: 1; min-width: 0; }
.insight-body h3 {
  margin: 0 0 0.35rem;
  font-size: 1rem;
  font-weight: 700;
}
.insight-body p {
  margin: 0 0 0.55rem;
  font-size: 0.88rem;
  color: var(--text2);
  line-height: 1.5;
}
.insight-action {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--red-bright);
  text-decoration: none;
}
.insight-action:hover { text-decoration: underline; }
</style>
{% endblock %}
'''

with open(TPL, 'w', encoding='utf-8') as fh:
    fh.write(NEW_TEMPLATE)
print(f"  [OK]   wrote {TPL} ({len(NEW_TEMPLATE):,} bytes)")

# ─────────────────────────────────────────────────────────────────────
# 3 — compile check
# ─────────────────────────────────────────────────────────────────────
print("\n[3/3] Verifying app.py compiles…")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK]   app.py compiles cleanly.")
else:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)
    print(f"\nRestore with:  copy \"{app_backup}\" {APP}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────
# Bonus audit
# ─────────────────────────────────────────────────────────────────────
print("\nVerifying template variables…")
used = set(re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)', NEW_TEMPLATE))
allowed = {
    'insights', 'revenue_30', 'profit_30', 'tickets_30', 'customers_30',
    'low_stock', 'dead_stock', 'at_risk', 'stock_cost_value',
    'stock_sell_value', 'payment_mix',
    'money', 'url_for', 'ins', 'p', 'loop',
}
missing = used - allowed
if missing:
    print(f"  [WARN] template references unknown variables: {sorted(missing)}")
else:
    print(f"  [OK]   all {len(used)} variables accounted for")

print("\n" + "=" * 60)
print("Done.")
print("=" * 60)
print("\nTest:")
print("  1. Restart Flask")
print("  2. Visit /insights")
print("  3. Expect: stat grid on top, 5-6 insight cards, payment mix table")
print("  4. Record a sale → refresh → cards update with real figures")
print("  5. Reaches /insights from sidebar → Growth → AI Insights")