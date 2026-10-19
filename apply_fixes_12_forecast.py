"""
apply_fixes_12_forecast.py — replace /forecast stub with a real projection.

Before: projections = avg_daily * day, starting from 0
After:  starts from current bank/cash balance, subtracts recurring +
        pending POs, draws worst/base/best cash lines.
"""

import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'
TPL = os.path.join('templates', 'forecast.html')

if not os.path.isfile(APP):
    print("ERROR: app.py not found."); sys.exit(1)

shutil.copy2(APP, f"{APP}.bak.{STAMP}"); print(f"Backup: {APP}.bak.{STAMP}")
if os.path.isfile(TPL):
    shutil.copy2(TPL, f"{TPL}.bak.{STAMP}"); print(f"Backup: {TPL}.bak.{STAMP}")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

NEW_ROUTE = r'''@app.route('/forecast')
@login_required
def forecast():
    uid = current_user.id
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COALESCE(AVG(daily_rev),0) AS avg_rev FROM ("
        "SELECT SUM(total_amount) AS daily_rev FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
        "GROUP BY sale_date) t",
        (uid,))
    avg_daily_revenue = float((cur.fetchone() or {}).get('avg_rev') or 0)

    cur.execute(
        "SELECT COALESCE(AVG(daily_exp),0) AS avg_exp FROM ("
        "SELECT SUM(amount) AS daily_exp FROM expenses "
        "WHERE user_id=%s AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
        "GROUP BY date) t",
        (uid,))
    avg_daily_expense = float((cur.fetchone() or {}).get('avg_exp') or 0)

    cur.execute(
        "SELECT COALESCE(SUM(opening_balance),0) AS opening FROM bank_accounts WHERE user_id=%s",
        (uid,))
    opening = float((cur.fetchone() or {}).get('opening') or 0)
    cur.execute(
        "SELECT COALESCE(SUM(CASE WHEN kind='in' THEN amount ELSE -amount END),0) AS mv "
        "FROM bank_transactions WHERE user_id=%s", (uid,))
    bank_mv = float((cur.fetchone() or {}).get('mv') or 0)
    cur.execute("SELECT COUNT(*) AS n FROM bank_accounts WHERE user_id=%s", (uid,))
    bank_count = int((cur.fetchone() or {}).get('n') or 0)

    if bank_count > 0:
        current_cash = opening + bank_mv
        cash_source = 'bank accounts'
    else:
        cur.execute(
            "SELECT COALESCE(SUM(CASE WHEN entry_type='in' THEN amount ELSE -amount END),0) AS net "
            "FROM cash_books WHERE user_id=%s", (uid,))
        current_cash = float((cur.fetchone() or {}).get('net') or 0)
        cash_source = 'cash book'

    cur.execute(
        "SELECT COALESCE(SUM(amount),0) AS total FROM recurring_items "
        "WHERE user_id=%s AND active=1 AND item_type='expense' "
        "AND next_run_date <= to_char(CURRENT_DATE + INTERVAL '30 days','YYYY-MM-DD')",
        (uid,))
    upcoming_recurring = float((cur.fetchone() or {}).get('total') or 0)

    cur.execute(
        "SELECT COALESCE(SUM(total_cost),0) AS total FROM purchase_orders "
        "WHERE user_id=%s AND status='pending'", (uid,))
    upcoming_pos = float((cur.fetchone() or {}).get('total') or 0)

    cur.close()
    conn.close()

    net_daily = avg_daily_revenue - avg_daily_expense
    daily_obligations = (upcoming_recurring + upcoming_pos) / 30.0

    base, worst, best = [], [], []
    for d in range(1, 31):
        net = net_daily - daily_obligations
        base_val = current_cash + net * d
        worst_val = current_cash + (net_daily * 0.5 - daily_obligations) * d
        best_val = current_cash + (net_daily * 1.5 - daily_obligations) * d
        base.append(round(base_val, 2))
        worst.append(round(worst_val, 2))
        best.append(round(best_val, 2))

    lowest = min(base) if base else 0
    if lowest < 0:
        cash_risk = 'High — projected to go negative by day {}'.format(base.index(min(base)) + 1)
    elif lowest < current_cash * 0.2:
        cash_risk = 'Moderate — buffer below 20% of current cash'
    else:
        cash_risk = 'Low'

    return render_template(
        'forecast.html',
        current_cash=current_cash,
        cash_source=cash_source,
        avg_daily_revenue=avg_daily_revenue,
        avg_daily_expense=avg_daily_expense,
        net_daily=net_daily,
        upcoming_recurring=upcoming_recurring,
        upcoming_pos=upcoming_pos,
        daily_obligations=daily_obligations,
        base=base, worst=worst, best=best,
        lowest=lowest,
        cash_risk=cash_risk,
        avg_daily=avg_daily_revenue,
    )


'''

PAT = re.compile(
    r"@app\.route\('/forecast'\)\n@login_required\ndef forecast\(\):\n.*?"
    r"(?=\n@app\.|\n#|\ndef |\nif __name__|\Z)",
    re.DOTALL)
m = PAT.search(src)
if not m:
    if "def forecast():" in src and "cash_risk" in src:
        print("[SKIP] already patched")
    else:
        print("[FAIL] forecast not found"); sys.exit(1)
else:
    src = src[:m.start()] + NEW_ROUTE + src[m.end():]
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print("[OK] forecast route replaced")

NEW_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Cash Flow Forecast{% endblock %}
{% block charts_js %}<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="trending-up"></i> Cash Flow Forecast</h1>
    <p>30-day projection from your current {{ cash_source }} balance, average daily flows, and upcoming obligations.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Current cash</span><strong>{{ money(current_cash) }}</strong></div>
  <div class="stat-chip"><span>Avg daily revenue</span><strong>{{ money(avg_daily_revenue) }}</strong></div>
  <div class="stat-chip"><span>Avg daily expense</span><strong>{{ money(avg_daily_expense) }}</strong></div>
  <div class="stat-chip"><span>Net daily</span><strong>{{ money(net_daily) }}</strong></div>
  <div class="stat-chip"><span>Upcoming recurring</span><strong>{{ money(upcoming_recurring) }}</strong></div>
  <div class="stat-chip"><span>Pending POs</span><strong>{{ money(upcoming_pos) }}</strong></div>
</div>

<div class="widget">
  <h3 style="margin-top:0;">Risk assessment</h3>
  <p style="margin:0;"><strong>Lowest projected cash:</strong> {{ money(lowest) }} · <strong>Risk:</strong> {{ cash_risk }}</p>
</div>

<div class="chart-container">
  <canvas id="forecastChart"></canvas>
</div>
<script>
(function(){
  const labels = Array.from({length:30}, (_,i) => 'Day ' + (i+1));
  new Chart(document.getElementById('forecastChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        {label: 'Best case', data: {{ best|tojson }}, borderColor: '#2ecc71', backgroundColor: 'rgba(46,204,113,0.08)', tension: 0.3, fill: false},
        {label: 'Base case', data: {{ base|tojson }}, borderColor: '#3498db', backgroundColor: 'rgba(52,152,219,0.08)', tension: 0.3, fill: false, borderWidth: 3},
        {label: 'Worst case', data: {{ worst|tojson }}, borderColor: '#e74c3c', backgroundColor: 'rgba(231,76,60,0.08)', tension: 0.3, fill: false}
      ]
    },
    options: {
      responsive: true,
      plugins: {
        title: {display: true, text: 'Projected cash position · next 30 days'},
        tooltip: {callbacks: {label: c => c.dataset.label + ': ' + window.kazeMoney(c.raw)}}
      },
      scales: {y: {ticks: {callback: v => window.kazeMoney(v)}}}
    }
  });
})();
</script>

<h2>Daily detail</h2>
<div class="table-wrapper">
<table>
<thead><tr><th>Day</th><th>Worst</th><th>Base</th><th>Best</th></tr></thead>
<tbody>
{% for i in range(30) %}
<tr>
  <td>Day {{ i+1 }}</td>
  <td>{{ money(worst[i]) }}</td>
  <td>{{ money(base[i]) }}</td>
  <td>{{ money(best[i]) }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>

<p class="note" style="color:var(--text3);font-size:0.85rem;">Simple projection from 30-day averages. Actual cash is affected by anything not recorded yet. Add recurring expenses and pending purchase orders to make the forecast sharper.</p>
{% endblock %}
'''

with open(TPL, 'w', encoding='utf-8') as fh:
    fh.write(NEW_TEMPLATE)
print(f"[OK] wrote {TPL} ({len(NEW_TEMPLATE):,} bytes)")

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
print("[OK] app.py compiles" if r.returncode == 0 else f"[FAIL]\n{r.stderr}")
print("\nTest: restart Flask, visit /forecast — see 3-line chart from real current cash.")