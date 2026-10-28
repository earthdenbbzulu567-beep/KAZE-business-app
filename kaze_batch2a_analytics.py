"""
kaze_batch2a_analytics.py — Batch 2a.

Consolidates 5 disabled routes into 2 tabbed analytics pages:
  /sales/analytics       (margin, velocity, repeat)
  /customers/analytics   (churn risk, lifetime value)

Adds 301 redirects from the original 5 paths.
Removes those 5 from _DISABLED_PATHS.
Adds an Analytics nav section.

Run from the folder with app.py:
    python kaze_batch2a_analytics.py
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
backup_path = f"{APP}.bak.batch2a_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}\n")

APPLIED = []
FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("[1/6] Remove 5 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = [
    '/sales/margin-alert', '/sales/velocity', '/sales/repeat-rate',
    '/customers/churn-risk', '/customers/lifetime',
]

removed = 0
for path in TO_REMOVE:
    # Match either single-line or list-item formats
    pattern = re.compile(r"\s*'" + re.escape(path) + r"',?\n")
    if pattern.search(src):
        src = pattern.sub('\n', src, count=1)
        removed += 1
        print(f"  [OK]   removed {path} from disabled set")
    else:
        print(f"  [SKIP] {path} — not found in disabled set")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/6] Add new routes + redirects")
# ═══════════════════════════════════════════════════════════════════

NEW_CODE = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 2a — Sales & Customer Analytics (consolidated from 5 disabled routes)
# ═══════════════════════════════════════════════════════════════════════

_bind_module('sales',
    'sales_analytics',
    'redirect_sales_margin', 'redirect_sales_velocity', 'redirect_sales_repeat')
_bind_module('customers',
    'customers_analytics',
    'redirect_customers_churn', 'redirect_customers_lifetime')


@app.route('/sales/analytics')
@login_required
def sales_analytics():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    # ── Margin alert ─────────────────────────────────────
    cur.execute("""
        SELECT COALESCE(st.product_name, 'Item') AS name,
               COALESCE(SUM(s.quantity_sold),0) AS units,
               COALESCE(SUM(s.total_amount),0) AS revenue,
               COALESCE(SUM(s.profit),0) AS profit,
               COUNT(*) AS tickets
        FROM sales s LEFT JOIN stock st ON st.id = s.stock_id
        WHERE s.user_id=%s
          AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '90 days','YYYY-MM-DD')
        GROUP BY st.product_name
        HAVING COUNT(*) >= 3
        ORDER BY (COALESCE(SUM(s.profit),0) / NULLIF(COALESCE(SUM(s.total_amount),0), 0)) ASC
        LIMIT 15
    """, (uid,))
    margin_rows = []
    for r in (cur.fetchall() or []):
        rev = float(r.get('revenue') or 0)
        pft = float(r.get('profit') or 0)
        if rev > 0:
            margin_pct = round(pft / rev * 100, 1)
        else:
            margin_pct = 0.0
        margin_rows.append({
            'name': r.get('name') or 'Item',
            'units': float(r.get('units') or 0),
            'revenue': rev, 'profit': pft,
            'margin_pct': margin_pct,
            'tickets': int(r.get('tickets') or 0),
        })

    # ── Velocity ─────────────────────────────────────────
    cur.execute("""
        SELECT COALESCE(st.product_name, 'Item') AS name,
               COALESCE(st.quantity, 0) AS stock,
               COALESCE(SUM(s.quantity_sold),0) AS units_14d
        FROM stock st
        LEFT JOIN sales s ON s.stock_id = st.id AND s.user_id=%s
            AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '14 days','YYYY-MM-DD')
        WHERE st.user_id=%s
        GROUP BY st.id, st.product_name, st.quantity
        HAVING COALESCE(SUM(s.quantity_sold),0) > 0
        ORDER BY (COALESCE(SUM(s.quantity_sold),0) / 14.0) DESC
        LIMIT 20
    """, (uid, uid))
    velocity_rows = []
    for r in (cur.fetchall() or []):
        vel = float(r.get('units_14d') or 0) / 14.0
        stock = float(r.get('stock') or 0)
        days_left = (stock / vel) if vel > 0 else 999
        velocity_rows.append({
            'name': r.get('name') or 'Item',
            'units_14d': float(r.get('units_14d') or 0),
            'velocity': round(vel, 2),
            'stock': stock,
            'days_left': round(days_left, 1) if days_left < 900 else '∞',
            'flag': ('danger' if days_left < 7 else
                     'warn' if days_left < 14 else ''),
        })

    # ── Repeat rate ──────────────────────────────────────
    cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN cnt >= 2 THEN 1 ELSE 0 END) AS repeaters
        FROM (
            SELECT customer_id, COUNT(*) AS cnt
            FROM sales
            WHERE user_id=%s AND customer_id IS NOT NULL
            GROUP BY customer_id
        ) t
    """, (uid,))
    rr = cur.fetchone() or {}
    total_customers = int(rr.get('total') or 0)
    repeaters = int(rr.get('repeaters') or 0)
    one_timers = total_customers - repeaters
    repeat_pct = round(repeaters / total_customers * 100, 1) if total_customers else 0.0

    # Top 15 repeat customers for context
    cur.execute("""
        SELECT COALESCE(c.name, 'Walk-in') AS name,
               COUNT(s.id) AS orders,
               COALESCE(SUM(s.total_amount),0) AS spent
        FROM sales s JOIN customers c ON c.id = s.customer_id
        WHERE s.user_id=%s
        GROUP BY c.id, c.name
        HAVING COUNT(s.id) >= 2
        ORDER BY spent DESC
        LIMIT 15
    """, (uid,))
    repeat_list = [
        {'name': r.get('name') or 'Customer',
         'orders': int(r.get('orders') or 0),
         'spent': float(r.get('spent') or 0)}
        for r in (cur.fetchall() or [])
    ]

    # ── Top stats ────────────────────────────────────────
    cur.execute("""
        SELECT COALESCE(SUM(total_amount),0) AS revenue,
               COALESCE(SUM(profit),0) AS profit,
               COUNT(*) AS tickets
        FROM sales WHERE user_id=%s
    """, (uid,))
    totals = cur.fetchone() or {}
    total_revenue = float(totals.get('revenue') or 0)
    total_profit = float(totals.get('profit') or 0)
    total_tickets = int(totals.get('tickets') or 0)
    overall_margin = round(total_profit / total_revenue * 100, 1) if total_revenue else 0.0

    cur.close(); conn.close()

    return render_template('sales_analytics.html',
        margin_rows=margin_rows,
        velocity_rows=velocity_rows,
        repeat_list=repeat_list,
        total_customers=total_customers,
        repeaters=repeaters,
        one_timers=one_timers,
        repeat_pct=repeat_pct,
        total_revenue=total_revenue,
        total_profit=total_profit,
        total_tickets=total_tickets,
        overall_margin=overall_margin,
    )


@app.route('/customers/analytics')
@login_required
def customers_analytics():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    # ── Churn risk ───────────────────────────────────────
    cur.execute("""
        SELECT c.id, c.name,
               MAX(s.sale_date) AS last_sale,
               COUNT(s.id) AS orders,
               COALESCE(SUM(s.total_amount),0) AS spent
        FROM customers c
        JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id
        WHERE c.user_id = %s
        GROUP BY c.id, c.name
        HAVING COUNT(s.id) > 0
        ORDER BY MAX(s.sale_date) ASC
        LIMIT 30
    """, (uid,))
    churn_rows = []
    today = datetime.today().date()
    for r in (cur.fetchall() or []):
        last = (r.get('last_sale') or '')[:10]
        try:
            days = (today - datetime.strptime(last, '%Y-%m-%d').date()).days if last else 9999
        except ValueError:
            days = 9999
        flag = 'danger' if days >= 90 else ('warn' if days >= 60 else '')
        churn_rows.append({
            'id': r.get('id'),
            'name': r.get('name') or 'Customer',
            'last_sale': last or 'never',
            'days': days,
            'orders': int(r.get('orders') or 0),
            'spent': float(r.get('spent') or 0),
            'flag': flag,
        })

    # ── Lifetime value ───────────────────────────────────
    cur.execute("""
        SELECT c.id, c.name,
               COUNT(s.id) AS orders,
               COALESCE(SUM(s.total_amount),0) AS spent,
               MAX(s.sale_date) AS last_sale,
               COALESCE(MIN(s.sale_date), '') AS first_sale
        FROM customers c
        JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id
        WHERE c.user_id = %s
        GROUP BY c.id, c.name
        ORDER BY spent DESC
        LIMIT 20
    """, (uid,))
    ltv_rows = []
    for r in (cur.fetchall() or []):
        orders = int(r.get('orders') or 0)
        spent = float(r.get('spent') or 0)
        last = (r.get('last_sale') or '')[:10]
        try:
            days_since = (today - datetime.strptime(last, '%Y-%m-%d').date()).days if last else 9999
        except ValueError:
            days_since = 9999
        ltv_rows.append({
            'id': r.get('id'),
            'name': r.get('name') or 'Customer',
            'orders': orders,
            'spent': spent,
            'aov': round(spent / orders, 2) if orders else 0,
            'days_since': days_since,
        })

    # ── Top stats ────────────────────────────────────────
    cur.execute("SELECT COUNT(*) AS n FROM customers WHERE user_id=%s", (uid,))
    total_customers = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute("""
        SELECT COUNT(DISTINCT customer_id) AS n
        FROM sales
        WHERE user_id=%s AND customer_id IS NOT NULL
          AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')
    """, (uid,))
    active_30d = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute("""
        SELECT COALESCE(AVG(total_spent),0) AS aov
        FROM (
            SELECT customer_id, SUM(total_amount) AS total_spent
            FROM sales
            WHERE user_id=%s AND customer_id IS NOT NULL
            GROUP BY customer_id
        ) t
    """, (uid,))
    avg_ltv = float((cur.fetchone() or {}).get('aov') or 0)

    churn_count = sum(1 for r in churn_rows if r['flag'] in ('danger', 'warn'))

    cur.close(); conn.close()

    return render_template('customers_analytics.html',
        churn_rows=churn_rows,
        ltv_rows=ltv_rows,
        total_customers=total_customers,
        active_30d=active_30d,
        avg_ltv=avg_ltv,
        churn_count=churn_count,
    )


# Redirects from the old URLs into the new tabs
@app.route('/sales/margin-alert')
@login_required
def redirect_sales_margin():
    return redirect(url_for('sales_analytics') + '#margin', code=301)


@app.route('/sales/velocity')
@login_required
def redirect_sales_velocity():
    return redirect(url_for('sales_analytics') + '#velocity', code=301)


@app.route('/sales/repeat-rate')
@login_required
def redirect_sales_repeat():
    return redirect(url_for('sales_analytics') + '#repeat', code=301)


@app.route('/customers/churn-risk')
@login_required
def redirect_customers_churn():
    return redirect(url_for('customers_analytics') + '#churn', code=301)


@app.route('/customers/lifetime')
@login_required
def redirect_customers_lifetime():
    return redirect(url_for('customers_analytics') + '#lifetime', code=301)

'''

# Insert new routes right before `if __name__` (safe module-level location)
if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + NEW_CODE + '\n' + src[idx:]
else:
    src += '\n' + NEW_CODE
print("  [OK]   inserted 7 new routes + 5 redirects")
APPLIED.append("new routes")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/6] Add Analytics section to NAV_GROUPS")
# ═══════════════════════════════════════════════════════════════════

NAV_ANALYTICS = """    ('Analytics', (
        ('Sales analytics', 'sales_analytics', 'bar-chart-3', 'sales', ('sales_analytics',)),
        ('Customer analytics', 'customers_analytics', 'users', 'customers', ('customers_analytics',)),
    )),
"""

# Insert just before ('Growth', section
growth_marker = "('Growth', ("
if growth_marker in src:
    idx = src.find(growth_marker)
    # Find the preceding "    (" that starts the group — insert before it
    insert_at = src.rfind("\n    ('", 0, idx)
    if insert_at > 0:
        src = src[:insert_at+1] + NAV_ANALYTICS + src[insert_at+1:]
        print("  [OK]   inserted Analytics section before Growth")
        APPLIED.append("nav section")
    else:
        print("  [FAIL] could not locate insert point")
        FAILED.append("nav section")
else:
    print("  [FAIL] 'Growth' nav section not found")
    FAILED.append("nav section")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/6] Write app.py")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   {initial_routes} -> {final_routes} @app.route decorators (+{final_routes-initial_routes})")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/6] Write templates")
# ═══════════════════════════════════════════════════════════════════

os.makedirs('templates', exist_ok=True)

SALES_TPL = '''{% extends "base.html" %}
{% block title %}Sales Analytics{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="bar-chart-3"></i> Sales Analytics</h1>
    <p>Margin health, sales velocity, and customer repeat rate — computed live from your sales data.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Total revenue</span><strong>{{ money(total_revenue) }}</strong></div>
  <div class="stat-chip"><span>Total profit</span><strong>{{ money(total_profit) }}</strong></div>
  <div class="stat-chip"><span>Overall margin</span><strong>{{ overall_margin }}%</strong></div>
  <div class="stat-chip"><span>Tickets</span><strong>{{ total_tickets }}</strong></div>
  <div class="stat-chip"><span>Repeat rate</span><strong>{{ repeat_pct }}%</strong></div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="margin" class="is-on">Margin alert</button>
  <button type="button" data-tab="velocity">Velocity</button>
  <button type="button" data-tab="repeat">Repeat rate</button>
</nav>

<section class="analytics-panel is-on" id="panel-margin">
  {% if margin_rows %}
  <h2>Thinnest margins (last 90 days)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">Products with 3 or more tickets, sorted by margin ascending. Flagged red under 15%.</p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Product</th><th>Units</th><th>Revenue</th><th>Profit</th><th>Margin</th><th>Tickets</th></tr></thead>
      <tbody>
      {% for r in margin_rows %}
      <tr {% if r.margin_pct < 15 %}style="background:var(--danger-dim);"{% elif r.margin_pct < 25 %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td>{{ r.name }}</td>
        <td>{{ r.units }}</td>
        <td>{{ money(r.revenue) }}</td>
        <td>{{ money(r.profit) }}</td>
        <td>{{ r.margin_pct }}%</td>
        <td>{{ r.tickets }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">Not enough data yet. You need at least 3 tickets on a product in the last 90 days for margin analysis.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-velocity">
  {% if velocity_rows %}
  <h2>Sales velocity (last 14 days)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">Products sold at least once in the last two weeks, ranked by units/day. Days of stock flagged red under 7, amber under 14.</p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Product</th><th>Units (14d)</th><th>Units/day</th><th>Stock</th><th>Days left</th></tr></thead>
      <tbody>
      {% for r in velocity_rows %}
      <tr {% if r.flag == 'danger' %}style="background:var(--danger-dim);"{% elif r.flag == 'warn' %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td>{{ r.name }}</td>
        <td>{{ r.units_14d }}</td>
        <td>{{ r.velocity }}</td>
        <td>{{ r.stock }}</td>
        <td>{{ r.days_left }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No sales in the last 14 days. Record a sale to see velocity.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-repeat">
  <h2>Customer repeat rate</h2>
  <div class="stat-grid" style="margin:1rem 0;">
    <div class="stat-chip"><span>Total customers</span><strong>{{ total_customers }}</strong></div>
    <div class="stat-chip"><span>Bought 2+ times</span><strong>{{ repeaters }}</strong></div>
    <div class="stat-chip"><span>One-time buyers</span><strong>{{ one_timers }}</strong></div>
    <div class="stat-chip"><span>Repeat rate</span><strong>{{ repeat_pct }}%</strong></div>
  </div>
  {% if repeat_list %}
  <h3 style="margin-top:1.5rem;">Top repeat customers</h3>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Customer</th><th>Orders</th><th>Total spent</th></tr></thead>
      <tbody>
      {% for c in repeat_list %}
      <tr><td>{{ c.name }}</td><td>{{ c.orders }}</td><td>{{ money(c.spent) }}</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No customers have bought more than once yet.</p></div>
  {% endif %}
</section>

<style>
.analytics-tabs { display:flex; gap:0.4rem; margin:1rem 0 1.2rem; flex-wrap:wrap; border-bottom:1px solid var(--border); }
.analytics-tabs button {
  background: transparent; border: none; border-bottom: 2px solid transparent;
  padding: 0.6rem 1rem; font-size: 0.9rem; font-weight: 700;
  color: var(--text2); cursor: pointer; font-family: inherit;
}
.analytics-tabs button.is-on { color: var(--red-bright); border-bottom-color: var(--red-bright); }
.analytics-tabs button:hover { color: var(--text); }
.analytics-panel { display: none; }
.analytics-panel.is-on { display: block; }
</style>

<script>
(function(){
  const tabs = document.querySelectorAll('.analytics-tabs button');
  const panels = document.querySelectorAll('.analytics-panel');
  function activate(name, scroll) {
    tabs.forEach(t => t.classList.toggle('is-on', t.dataset.tab === name));
    panels.forEach(p => p.classList.toggle('is-on', p.id === 'panel-' + name));
    if (scroll !== false) {
      document.getElementById('panel-' + name)?.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
  }
  tabs.forEach(t => t.addEventListener('click', () => {
    activate(t.dataset.tab, false);
    history.replaceState(null, '', '#' + t.dataset.tab);
  }));
  // Honour #hash on load
  const hash = (location.hash || '').replace('#', '');
  if (['margin','velocity','repeat'].includes(hash)) {
    activate(hash, false);
  }
})();
</script>
{% endblock %}
'''

CUSTOMERS_TPL = '''{% extends "base.html" %}
{% block title %}Customer Analytics{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="users"></i> Customer Analytics</h1>
    <p>Churn risk and lifetime value — computed live from your customers and sales.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Total customers</span><strong>{{ total_customers }}</strong></div>
  <div class="stat-chip"><span>Active last 30d</span><strong>{{ active_30d }}</strong></div>
  <div class="stat-chip"><span>Churn risk</span><strong>{{ churn_count }}</strong></div>
  <div class="stat-chip"><span>Avg lifetime value</span><strong>{{ money(avg_ltv) }}</strong></div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="churn" class="is-on">Churn risk</button>
  <button type="button" data-tab="lifetime">Lifetime value</button>
</nav>

<section class="analytics-panel is-on" id="panel-churn">
  {% if churn_rows %}
  <h2>Churn risk</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">Customers with at least one purchase, sorted by days since last purchase. Red = 90+ days, amber = 60-90 days.</p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Customer</th><th>Last purchase</th><th>Days since</th><th>Orders</th><th>Total spent</th></tr></thead>
      <tbody>
      {% for r in churn_rows %}
      <tr {% if r.flag == 'danger' %}style="background:var(--danger-dim);"{% elif r.flag == 'warn' %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td>{{ r.name }}</td>
        <td>{{ r.last_sale }}</td>
        <td>{{ 'never' if r.days >= 9000 else r.days ~ 'd' }}</td>
        <td>{{ r.orders }}</td>
        <td>{{ money(r.spent) }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No customer-linked sales yet. Attach customers to sales to see churn risk.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-lifetime">
  {% if ltv_rows %}
  <h2>Lifetime value (top 20)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">Ranked by total spend. AOV is per-ticket average.</p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Customer</th><th>Orders</th><th>Total spent</th><th>AOV</th><th>Days since last</th></tr></thead>
      <tbody>
      {% for r in ltv_rows %}
      <tr>
        <td>{{ r.name }}</td>
        <td>{{ r.orders }}</td>
        <td>{{ money(r.spent) }}</td>
        <td>{{ money(r.aov) }}</td>
        <td>{{ 'never' if r.days_since >= 9000 else r.days_since ~ 'd' }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No customer-linked sales yet.</p></div>
  {% endif %}
</section>

<style>
.analytics-tabs { display:flex; gap:0.4rem; margin:1rem 0 1.2rem; flex-wrap:wrap; border-bottom:1px solid var(--border); }
.analytics-tabs button {
  background: transparent; border: none; border-bottom: 2px solid transparent;
  padding: 0.6rem 1rem; font-size: 0.9rem; font-weight: 700;
  color: var(--text2); cursor: pointer; font-family: inherit;
}
.analytics-tabs button.is-on { color: var(--red-bright); border-bottom-color: var(--red-bright); }
.analytics-tabs button:hover { color: var(--text); }
.analytics-panel { display: none; }
.analytics-panel.is-on { display: block; }
</style>

<script>
(function(){
  const tabs = document.querySelectorAll('.analytics-tabs button');
  const panels = document.querySelectorAll('.analytics-panel');
  function activate(name, scroll) {
    tabs.forEach(t => t.classList.toggle('is-on', t.dataset.tab === name));
    panels.forEach(p => p.classList.toggle('is-on', p.id === 'panel-' + name));
    if (scroll !== false) {
      document.getElementById('panel-' + name)?.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
  }
  tabs.forEach(t => t.addEventListener('click', () => {
    activate(t.dataset.tab, false);
    history.replaceState(null, '', '#' + t.dataset.tab);
  }));
  const hash = (location.hash || '').replace('#', '');
  if (['churn','lifetime'].includes(hash)) {
    activate(hash, false);
  }
})();
</script>
{% endblock %}
'''

for name, content in [
    ('templates/sales_analytics.html', SALES_TPL),
    ('templates/customers_analytics.html', CUSTOMERS_TPL),
]:
    with open(name, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [OK]   {name}")

# ═══════════════════════════════════════════════════════════════════
print("\n[6/6] Compile check")
# ═══════════════════════════════════════════════════════════════════

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
print(f"  Removed from disabled:  {removed}/5")
print(f"  New routes added:        7 (2 analytics + 5 redirects)")
print(f"  New templates:           2")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 5 or FAILED:
    print("\nSome fixes did not land. Check [FAIL] lines above.")
    if FAILED:
        for f in FAILED:
            print(f"  - {f}")
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 2a complete.

NEXT STEPS:

1. LOCAL TEST — run:  python app.py
   Then visit:

     /sales/analytics          -> 3 tabs (Margin / Velocity / Repeat)
                                  Click each tab, verify data + no crash
     /customers/analytics      -> 2 tabs (Churn / Lifetime)
                                  Click each tab

     /sales/margin-alert       -> 301 redirects to /sales/analytics#margin
     /sales/velocity           -> 301 redirects to /sales/analytics#velocity
     /sales/repeat-rate        -> 301 redirects to /sales/analytics#repeat
     /customers/churn-risk     -> 301 redirects to /customers/analytics#churn
     /customers/lifetime       -> 301 redirects to /customers/analytics#lifetime

   Check the sidebar — a new "Analytics" section should appear between
   Trade and Growth, containing both new pages.

   Also verify: dashboard, sales, stock, customers, /plans still work.
   No 500s anywhere.

2. COMMIT AND DEPLOY:

   git add app.py kaze_batch2a_analytics.py templates/sales_analytics.html templates/customers_analytics.html
   git commit -m "Batch 2a: sales + customer analytics (5 routes -> 2 tabbed pages)"
   git push

3. Watch Render deploy. Re-test the same set of URLs on production.

4. Once confirmed, delete backup:  rm app.py.bak.batch2a_*

Report back:
  Local: /sales/analytics OK?  /customers/analytics OK?
         All 5 redirects work? Sidebar shows Analytics section?
         Regular usage still works?
  Deployed: hash, prod test results.
""")