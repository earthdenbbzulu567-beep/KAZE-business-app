"""
kaze_batch2b_inventory.py — Batch 2b.

Consolidates 4 disabled routes into 1 tabbed page (/stock/analytics):
  - ABC analysis (Pareto classification of products by revenue)
  - Supplier lead times (avg days order -> received)
  - Supplier reliability (% received on or before expected_date)

Schema change:
  ALTER TABLE purchase_orders ADD COLUMN received_date TEXT
  receive_purchase_order() now writes today's date when receiving.

Redirects:
  /stock/abc                  -> /stock/analytics#abc
  /suppliers/lead-time        -> /stock/analytics#leadtime
  /suppliers/reliability      -> /stock/analytics#reliability
  /purchase-orders/autofill   -> /stock/reorder-optimizer  (Batch 1 route)

Run from the folder with app.py:
    python kaze_batch2b_inventory.py
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
backup_path = f"{APP}.bak.batch2b_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}\n")

APPLIED = []
FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("[1/7] Add received_date column to purchase_orders")
# ═══════════════════════════════════════════════════════════════════

SCHEMA_ANCHOR = """    cur.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS stripe_checkout_id TEXT DEFAULT ''")"""

SCHEMA_NEW = """    cur.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS stripe_checkout_id TEXT DEFAULT ''")
    cur.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS received_date TEXT DEFAULT ''")"""

if SCHEMA_ANCHOR in src:
    src = src.replace(SCHEMA_ANCHOR, SCHEMA_NEW, 1)
    print("  [OK]   added ALTER TABLE purchase_orders received_date")
    APPLIED.append("schema")
else:
    print("  [FAIL] schema anchor not found")
    FAILED.append("schema")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/7] Update receive_purchase_order to record received_date")
# ═══════════════════════════════════════════════════════════════════

RECV_OLD = """    cur.execute("UPDATE purchase_orders SET status = 'received' WHERE id = %s", (id,))"""

RECV_NEW = """    cur.execute(
        "UPDATE purchase_orders SET status = 'received', received_date = %s WHERE id = %s",
        (datetime.today().strftime('%Y-%m-%d'), id),
    )"""

if RECV_OLD in src:
    src = src.replace(RECV_OLD, RECV_NEW, 1)
    print("  [OK]   receive_purchase_order now writes received_date")
    APPLIED.append("receive handler")
else:
    print("  [FAIL] receive_purchase_order UPDATE pattern not found")
    FAILED.append("receive handler")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/7] Remove 4 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = ['/stock/abc', '/suppliers/lead-time', '/suppliers/reliability',
             '/purchase-orders/autofill']

removed = 0
for path in TO_REMOVE:
    pattern = re.compile(r"\s*'" + re.escape(path) + r"',?\n")
    if pattern.search(src):
        src = pattern.sub('\n', src, count=1)
        removed += 1
        print(f"  [OK]   removed {path}")
    else:
        print(f"  [SKIP] {path} — not found in disabled set")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/7] Add /stock/analytics route + 4 redirects")
# ═══════════════════════════════════════════════════════════════════

NEW_ROUTES = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 2b — Inventory Analytics (consolidated from 3 disabled routes)
# ═══════════════════════════════════════════════════════════════════════

_bind_module('stock',
    'stock_analytics',
    'redirect_stock_abc',
    'redirect_supplier_leadtime', 'redirect_supplier_reliability',
    'redirect_po_autofill')


@app.route('/stock/analytics')
@login_required
def stock_analytics():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    # ── ABC analysis ─────────────────────────────────────
    cur.execute("""
        SELECT product_name, revenue,
               SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_rev,
               SUM(revenue) OVER () AS total_rev
        FROM (
            SELECT COALESCE(st.product_name, 'Item') AS product_name,
                   COALESCE(SUM(s.total_amount),0) AS revenue
            FROM sales s LEFT JOIN stock st ON st.id = s.stock_id
            WHERE s.user_id=%s
              AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '90 days','YYYY-MM-DD')
            GROUP BY st.product_name
            HAVING SUM(s.total_amount) > 0
        ) t
        ORDER BY revenue DESC
    """, (uid,))

    abc_rows = []
    for r in (cur.fetchall() or []):
        rev = float(r.get('revenue') or 0)
        cum = float(r.get('cum_rev') or 0)
        tot = float(r.get('total_rev') or 0)
        cum_pct = (cum / tot * 100) if tot else 0
        if cum_pct <= 80:
            cls = 'A'
        elif cum_pct <= 95:
            cls = 'B'
        else:
            cls = 'C'
        abc_rows.append({
            'name': r.get('product_name') or 'Item',
            'revenue': rev,
            'share_pct': round(rev / tot * 100, 1) if tot else 0,
            'cum_pct': round(cum_pct, 1),
            'class': cls,
        })

    abc_totals = {'A': 0, 'B': 0, 'C': 0}
    for r in abc_rows:
        abc_totals[r['class']] += r['revenue']

    # ── Lead times ───────────────────────────────────────
    cur.execute("""
        SELECT s.name,
               COUNT(po.id) AS n,
               AVG(EXTRACT(EPOCH FROM (po.received_date::timestamp - po.order_date::timestamp)) / 86400.0) AS avg_days,
               MIN(EXTRACT(EPOCH FROM (po.received_date::timestamp - po.order_date::timestamp)) / 86400.0) AS min_days,
               MAX(EXTRACT(EPOCH FROM (po.received_date::timestamp - po.order_date::timestamp)) / 86400.0) AS max_days
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        WHERE po.user_id=%s
          AND po.status = 'received'
          AND COALESCE(po.received_date, '') <> ''
          AND COALESCE(po.order_date, '') <> ''
        GROUP BY s.id, s.name
        ORDER BY avg_days ASC
    """, (uid,))

    lead_rows = []
    for r in (cur.fetchall() or []):
        lead_rows.append({
            'name': r.get('name') or 'Supplier',
            'orders': int(r.get('n') or 0),
            'avg_days': round(float(r.get('avg_days') or 0), 1),
            'min_days': round(float(r.get('min_days') or 0), 1),
            'max_days': round(float(r.get('max_days') or 0), 1),
        })

    # ── Reliability (on-time %) ──────────────────────────
    cur.execute("""
        SELECT s.name,
               COUNT(po.id) AS total,
               SUM(CASE WHEN po.expected_date <> ''
                         AND po.received_date <= po.expected_date
                        THEN 1 ELSE 0 END) AS on_time,
               SUM(CASE WHEN po.expected_date = ''
                        THEN 1 ELSE 0 END) AS no_expectation
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        WHERE po.user_id=%s
          AND po.status = 'received'
          AND COALESCE(po.received_date, '') <> ''
        GROUP BY s.id, s.name
        ORDER BY s.name
    """, (uid,))

    rel_rows = []
    for r in (cur.fetchall() or []):
        total = int(r.get('total') or 0)
        on_time = int(r.get('on_time') or 0)
        no_exp = int(r.get('no_expectation') or 0)
        judged = total - no_exp
        pct = round(on_time / judged * 100, 1) if judged else 0.0
        if judged == 0:
            flag = ''
        elif pct >= 90:
            flag = 'ok'
        elif pct >= 70:
            flag = 'warn'
        else:
            flag = 'danger'
        rel_rows.append({
            'name': r.get('name') or 'Supplier',
            'total': total,
            'judged': judged,
            'no_expectation': no_exp,
            'on_time': on_time,
            'on_time_pct': pct,
            'flag': flag,
        })

    cur.close(); conn.close()

    total_revenue_90d = sum(r['revenue'] for r in abc_rows)
    return render_template('stock_analytics.html',
        abc_rows=abc_rows,
        abc_totals=abc_totals,
        abc_count=len(abc_rows),
        total_revenue_90d=total_revenue_90d,
        lead_rows=lead_rows,
        rel_rows=rel_rows,
    )


# Redirects from original routes
@app.route('/stock/abc')
@login_required
def redirect_stock_abc():
    return redirect(url_for('stock_analytics') + '#abc', code=301)


@app.route('/suppliers/lead-time')
@login_required
def redirect_supplier_leadtime():
    return redirect(url_for('stock_analytics') + '#leadtime', code=301)


@app.route('/suppliers/reliability')
@login_required
def redirect_supplier_reliability():
    return redirect(url_for('stock_analytics') + '#reliability', code=301)


@app.route('/purchase-orders/autofill')
@login_required
def redirect_po_autofill():
    return redirect(url_for('stock_reorder_optimizer'), code=301)

'''

if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + NEW_ROUTES + '\n' + src[idx:]
else:
    src += '\n' + NEW_ROUTES
print("  [OK]   inserted /stock/analytics + 4 redirects")
APPLIED.append("new routes")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/7] Add Inventory analytics to NAV")
# ═══════════════════════════════════════════════════════════════════

NAV_ANCHOR = "        ('Customer analytics', 'customers_analytics', 'users', 'customers', ('customers_analytics',)),"
NAV_NEW = """        ('Customer analytics', 'customers_analytics', 'users', 'customers', ('customers_analytics',)),
        ('Inventory analytics', 'stock_analytics', 'package-search', 'stock', ('stock_analytics',)),"""

if NAV_ANCHOR in src:
    src = src.replace(NAV_ANCHOR, NAV_NEW, 1)
    print("  [OK]   Inventory analytics added to Analytics nav section")
    APPLIED.append("nav")
else:
    print("  [FAIL] nav anchor not found (Batch 2a entry)")
    FAILED.append("nav")

# ═══════════════════════════════════════════════════════════════════
print("\n[6/7] Write app.py + template")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   wrote {APP}  ({initial_routes} -> {final_routes} @app.route)")

os.makedirs('templates', exist_ok=True)

STOCK_ANALYTICS_TPL = '''{% extends "base.html" %}
{% block title %}Inventory Analytics{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="package-search"></i> Inventory Analytics</h1>
    <p>ABC analysis of product revenue, plus supplier lead time and reliability from received purchase orders.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>A-class products</span><strong>{{ abc_rows|selectattr('class','equalto','A')|list|length }}</strong></div>
  <div class="stat-chip"><span>B-class</span><strong>{{ abc_rows|selectattr('class','equalto','B')|list|length }}</strong></div>
  <div class="stat-chip"><span>C-class</span><strong>{{ abc_rows|selectattr('class','equalto','C')|list|length }}</strong></div>
  <div class="stat-chip"><span>Revenue (90d)</span><strong>{{ money(total_revenue_90d) }}</strong></div>
  <div class="stat-chip"><span>Suppliers tracked</span><strong>{{ lead_rows|length }}</strong></div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="abc" class="is-on">ABC analysis</button>
  <button type="button" data-tab="leadtime">Lead times</button>
  <button type="button" data-tab="reliability">Reliability</button>
</nav>

<section class="analytics-panel is-on" id="panel-abc">
  {% if abc_rows %}
  <h2>ABC analysis (last 90 days revenue)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Products sorted by revenue. A = top 80% of revenue, B = next 15%, C = bottom 5%.
    Focus stock control effort on A items; C items can use simpler reorder rules.
  </p>
  <div class="stat-grid" style="margin:0.5rem 0 1rem;">
    <div class="stat-chip"><span>A — 80% revenue</span><strong>{{ money(abc_totals.A) }}</strong></div>
    <div class="stat-chip"><span>B — 15% revenue</span><strong>{{ money(abc_totals.B) }}</strong></div>
    <div class="stat-chip"><span>C — 5% revenue</span><strong>{{ money(abc_totals.C) }}</strong></div>
  </div>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Class</th><th>Product</th><th>Revenue</th><th>Share</th><th>Cumulative</th></tr></thead>
      <tbody>
      {% for r in abc_rows %}
      <tr {% if r.class == 'A' %}style="background:var(--green-dim);"{% elif r.class == 'C' %}style="background:var(--danger-dim);"{% endif %}>
        <td><strong>{{ r.class }}</strong></td>
        <td>{{ r.name }}</td>
        <td>{{ money(r.revenue) }}</td>
        <td>{{ r.share_pct }}%</td>
        <td>{{ r.cum_pct }}%</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No sales in the last 90 days. Record a sale to see ABC analysis.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-leadtime">
  {% if lead_rows %}
  <h2>Supplier lead times</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Average days from purchase order to marked-received. Only counts POs you've received through the app since the tracking started.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Supplier</th><th>Orders</th><th>Avg days</th><th>Fastest</th><th>Slowest</th></tr></thead>
      <tbody>
      {% for r in lead_rows %}
      <tr>
        <td>{{ r.name }}</td>
        <td>{{ r.orders }}</td>
        <td>{{ r.avg_days }}d</td>
        <td>{{ r.min_days }}d</td>
        <td>{{ r.max_days }}d</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">
    No received purchase orders with a date yet. Create POs on the
    <a href="{{ url_for('purchase_orders') }}">Purchase Orders</a> page and mark them received
    to start tracking lead times.
  </p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-reliability">
  {% if rel_rows %}
  <h2>Supplier reliability</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    On-time delivery rate: POs received on or before expected_date, as a percentage of POs that had an expected date.
    Green = 90%+, amber = 70-90%, red = below 70%.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Supplier</th><th>Total POs</th><th>Judged</th><th>On time</th><th>On-time %</th><th>No expected date</th></tr></thead>
      <tbody>
      {% for r in rel_rows %}
      <tr {% if r.flag == 'danger' %}style="background:var(--danger-dim);"{% elif r.flag == 'warn' %}style="background:rgba(224,160,48,0.08);"{% elif r.flag == 'ok' %}style="background:var(--green-dim);"{% endif %}>
        <td>{{ r.name }}</td>
        <td>{{ r.total }}</td>
        <td>{{ r.judged }}</td>
        <td>{{ r.on_time }}</td>
        <td>{{ r.on_time_pct }}%</td>
        <td>{{ r.no_expectation }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">
    No received purchase orders with dates yet. Reliability metrics populate after you
    receive purchase orders that had an <em>expected date</em> set.
  </p></div>
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
  function activate(name) {
    tabs.forEach(t => t.classList.toggle('is-on', t.dataset.tab === name));
    panels.forEach(p => p.classList.toggle('is-on', p.id === 'panel-' + name));
  }
  tabs.forEach(t => t.addEventListener('click', () => {
    activate(t.dataset.tab);
    history.replaceState(null, '', '#' + t.dataset.tab);
  }));
  const hash = (location.hash || '').replace('#', '');
  if (['abc','leadtime','reliability'].includes(hash)) {
    activate(hash);
  }
})();
</script>
{% endblock %}
'''

with open('templates/stock_analytics.html', 'w', encoding='utf-8') as f:
    f.write(STOCK_ANALYTICS_TPL)
print(f"  [OK]   templates/stock_analytics.html")

# ═══════════════════════════════════════════════════════════════════
print("\n[7/7] Compile check")
# ═══════════════════════════════════════════════════════════════════

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
print(f"  Removed from disabled:  {removed}/4")
print(f"  New routes added:        5 (1 analytics + 4 redirects)")
print(f"  New templates:           1")
print(f"  Schema change:           +purchase_orders.received_date")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 4 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 2b complete.

NEXT STEPS:

1. LOCAL TEST — run:  python app.py
   Visit:

     /stock/analytics          -> 3 tabs (ABC / Lead times / Reliability)
                                  Click each. ABC should have data.
                                  Supplier tabs likely empty (see below)

     /stock/abc                -> 301 redirects to /stock/analytics#abc
     /suppliers/lead-time      -> 301 redirects to /stock/analytics#leadtime
     /suppliers/reliability    -> 301 redirects to /stock/analytics#reliability
     /purchase-orders/autofill -> 301 redirects to /stock/reorder-optimizer

   Sidebar: "Inventory analytics" should now appear under Analytics
   section (3 items total: Sales, Customer, Inventory).

   Regular usage still works: dashboard, /plans, /sales, /stock, etc.

2. HONEST WARNING:
   Lead time + reliability tabs will show empty until you receive
   purchase orders through the app that had order_date + expected_date.
   Old POs won't count (no received_date was recorded).
   This is expected. Not a bug. Populates over time.

   ABC tab will have data immediately if you have sales in last 90 days.

3. COMMIT AND DEPLOY:

   git add app.py kaze_batch2b_inventory.py templates/stock_analytics.html
   git commit -m "Batch 2b: inventory analytics + received_date tracking"
   git push

4. Watch Render deploy. Re-test the same URLs on production.

5. Confirm the schema change landed — in Render Postgres query:
   \\d purchase_orders
   Should show received_date column.

6. Clean up:  rm app.py.bak.batch2b_*

Report back:
  Local: /stock/analytics OK?  ABC tab has data?  4 redirects work?
         Sidebar has Inventory analytics? Regular usage still works?
  Deployed: hash, prod test results, schema confirmed.
""")