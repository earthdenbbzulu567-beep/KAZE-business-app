"""
apply_fixes_11_profit_matrix.py — replace the /profit_matrix stub with a
2×2 scatter chart.

Before: flat table of product → profit
After:  scatter plot (x = revenue, y = margin %) with quadrant labels:
        Stars (high rev, high margin), Cash Cows (high rev, low margin),
        Rockets (low rev, high margin), Dogs (low rev, low margin)
        + leaderboard table underneath.
"""

import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'
TPL = os.path.join('templates', 'profit_matrix.html')

if not os.path.isfile(APP):
    print("ERROR: app.py not found."); sys.exit(1)

shutil.copy2(APP, f"{APP}.bak.{STAMP}"); print(f"Backup: {APP}.bak.{STAMP}")
if os.path.isfile(TPL):
    shutil.copy2(TPL, f"{TPL}.bak.{STAMP}"); print(f"Backup: {TPL}.bak.{STAMP}")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

NEW_ROUTE = r'''@app.route('/profit_matrix')
@login_required
def profit_matrix():
    uid = current_user.id
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT st.product_name AS name, "
        "COALESCE(SUM(s.total_amount),0) AS revenue, "
        "COALESCE(SUM(s.profit),0) AS profit, "
        "COALESCE(SUM(s.quantity_sold),0) AS units, "
        "COUNT(*) AS tickets "
        "FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
        "WHERE s.user_id=%s "
        "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '90 days','YYYY-MM-DD') "
        "GROUP BY st.product_name "
        "ORDER BY revenue DESC",
        (uid,))
    rows = []
    for r in (cur.fetchall() or []):
        rev = float(r.get('revenue') or 0)
        pft = float(r.get('profit') or 0)
        margin_pct = round((pft / rev * 100) if rev > 0 else 0, 1)
        rows.append({
            'name': r.get('name') or 'Item',
            'revenue': rev,
            'profit': pft,
            'units': float(r.get('units') or 0),
            'tickets': int(r.get('tickets') or 0),
            'margin_pct': margin_pct,
        })
    cur.close()
    conn.close()

    avg_rev = round(sum(r['revenue'] for r in rows) / len(rows), 2) if rows else 0
    avg_margin = round(sum(r['margin_pct'] for r in rows) / len(rows), 1) if rows else 0

    buckets = {'star': [], 'cash_cow': [], 'rocket': [], 'dog': []}
    for r in rows:
        high_rev = r['revenue'] >= avg_rev
        high_margin = r['margin_pct'] >= avg_margin
        if high_rev and high_margin:
            key = 'star'
        elif high_rev and not high_margin:
            key = 'cash_cow'
        elif not high_rev and high_margin:
            key = 'rocket'
        else:
            key = 'dog'
        r['quadrant'] = key
        buckets[key].append(r)

    return render_template(
        'profit_matrix.html',
        rows=rows,
        stars=buckets['star'],
        cash_cows=buckets['cash_cow'],
        rockets=buckets['rocket'],
        dogs=buckets['dog'],
        avg_revenue=avg_rev,
        avg_margin=avg_margin,
    )


'''

PAT = re.compile(
    r"@app\.route\('/profit_matrix'\)\n@login_required\ndef profit_matrix\(\):\n.*?"
    r"(?=\n@app\.|\n#|\ndef |\nif __name__|\Z)",
    re.DOTALL)
m = PAT.search(src)
if not m:
    if "def profit_matrix():" in src and "quadrant" in src:
        print("[SKIP] already patched")
    else:
        print("[FAIL] profit_matrix not found"); sys.exit(1)
else:
    src = src[:m.start()] + NEW_ROUTE + src[m.end():]
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print("[OK] profit_matrix route replaced")

NEW_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Product Profitability{% endblock %}
{% block charts_js %}<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="pie-chart"></i> Profitability Matrix</h1>
    <p>Revenue vs margin over the last 90 days. Average revenue: {{ money(avg_revenue) }} · average margin: {{ avg_margin }}%.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Products</span><strong>{{ rows|length }}</strong></div>
  <div class="stat-chip"><span>Stars</span><strong>{{ stars|length }}</strong></div>
  <div class="stat-chip"><span>Cash cows</span><strong>{{ cash_cows|length }}</strong></div>
  <div class="stat-chip"><span>Rockets</span><strong>{{ rockets|length }}</strong></div>
  <div class="stat-chip"><span>Dogs</span><strong>{{ dogs|length }}</strong></div>
</div>

{% if rows %}
<div class="chart-container">
  <canvas id="pmChart"></canvas>
</div>
<script>
(function(){
  const data = {{ rows | tojson }};
  const colors = {star:'#2ecc71', cash_cow:'#3498db', rocket:'#e0a030', dog:'#e74c3c'};
  const groups = {star:[], cash_cow:[], rocket:[], dog:[]};
  data.forEach(r => groups[r.quadrant].push({x: r.revenue, y: r.margin_pct, name: r.name}));
  const ctx = document.getElementById('pmChart').getContext('2d');
  new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [
        {label: 'Stars', data: groups.star, backgroundColor: colors.star, pointRadius: 8},
        {label: 'Cash cows', data: groups.cash_cow, backgroundColor: colors.cash_cow, pointRadius: 8},
        {label: 'Rockets', data: groups.rocket, backgroundColor: colors.rocket, pointRadius: 8},
        {label: 'Dogs', data: groups.dog, backgroundColor: colors.dog, pointRadius: 8},
      ]
    },
    options: {
      responsive: true,
      plugins: {
        title: {display: true, text: 'Revenue vs margin · last 90 days'},
        tooltip: {
          callbacks: {
            label: c => `${c.raw.name} · ${window.kazeMoney(c.raw.x)} · ${c.raw.y}%`
          }
        }
      },
      scales: {
        x: {title: {display: true, text: 'Revenue'}, ticks: {callback: v => window.kazeMoney(v)}},
        y: {title: {display: true, text: 'Margin %'}, beginAtZero: true}
      }
    }
  });
})();
</script>
{% else %}
<div class="widget"><p style="color:var(--text3);">No sales in the last 90 days. Record a sale to populate the matrix.</p></div>
{% endif %}

<h2>Leaderboard</h2>
<div class="table-wrapper">
<table>
<thead><tr><th>Product</th><th>Quadrant</th><th>Revenue</th><th>Profit</th><th>Margin</th><th>Units</th><th>Tickets</th></tr></thead>
<tbody>
{% for r in rows %}
<tr>
  <td>{{ r.name }}</td>
  <td><span class="status-pill" style="background:{% if r.quadrant=='star' %}var(--green-dim){% elif r.quadrant=='cash_cow' %}rgba(52,152,219,0.15){% elif r.quadrant=='rocket' %}rgba(224,160,48,0.15){% else %}rgba(231,76,60,0.15){% endif %};color:{% if r.quadrant=='star' %}var(--green){% elif r.quadrant=='cash_cow' %}#3498db{% elif r.quadrant=='rocket' %}#e0a030{% else %}#e74c3c{% endif %};">{{ r.quadrant|replace('_',' ')|title }}</span></td>
  <td>{{ money(r.revenue) }}</td>
  <td>{{ money(r.profit) }}</td>
  <td>{{ r.margin_pct }}%</td>
  <td>{{ r.units|round(1) }}</td>
  <td>{{ r.tickets }}</td>
</tr>
{% else %}
<tr><td colspan="7">No data.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
{% endblock %}
'''

with open(TPL, 'w', encoding='utf-8') as fh:
    fh.write(NEW_TEMPLATE)
print(f"[OK] wrote {TPL} ({len(NEW_TEMPLATE):,} bytes)")

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
print("[OK] app.py compiles" if r.returncode == 0 else f"[FAIL]\n{r.stderr}")
print("\nTest: restart Flask, visit /profit_matrix, expect scatter + table.")