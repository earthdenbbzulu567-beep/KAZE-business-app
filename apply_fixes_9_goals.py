"""
apply_fixes_9_goals.py — replace the /goals stub with a live page.

Before:
    Route:     return render_template('goals.html')
    Template:  K 50,000 · 65% (hardcoded in HTML)
    Nothing on this page was true.

After:
    Route computes real numbers from sales + settings:
      • month_revenue, month_profit, tickets, units
      • goal_progress_pct vs settings.monthly_revenue_goal
      • pace target, ahead/behind pace delta
      • daily run rate, projected month-end
      • active customers this month vs total customers
      • last month's revenue + profit for comparison
      • best day this month

    Template renders those numbers with a real progress bar.

Run from the folder with app.py:
    python apply_fixes_9_goals.py
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'
TPL = os.path.join('templates', 'goals.html')

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found. Run from the project root.")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────
# Backups
# ─────────────────────────────────────────────────────────────────────
app_backup = f"{APP}.bak.{STAMP}"
shutil.copy2(APP, app_backup)
print(f"Backup saved: {app_backup}")

tpl_backup = None
if os.path.isfile(TPL):
    tpl_backup = f"{TPL}.bak.{STAMP}"
    shutil.copy2(TPL, tpl_backup)
    print(f"Backup saved: {tpl_backup}")

# ─────────────────────────────────────────────────────────────────────
# 1 — patch app.py
# ─────────────────────────────────────────────────────────────────────
print("\n[1/3] Patching /goals route in app.py…")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

OLD_ROUTE = """@app.route('/goals')
@login_required
def goals():
    return render_template('goals.html')"""

NEW_ROUTE = '''@app.route('/goals')
@login_required
def goals():
    """Live progress against the monthly sales target."""
    uid = current_user.id
    today = datetime.today()
    month_str = today.strftime('%Y-%m')
    first_of_month = today.replace(day=1)
    first_of_next_month = (first_of_month + timedelta(days=32)).replace(day=1)
    last_day = (first_of_next_month - timedelta(days=1)).day
    day_of_month = today.day
    days_remaining = last_day - day_of_month

    conn = get_db()
    cur = conn.cursor()

    settings_row = _get_settings_row(uid) or {}
    try:
        monthly_goal = float(settings_row.get('monthly_revenue_goal') or 0)
    except (TypeError, ValueError):
        monthly_goal = 0.0

    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS revenue, "
        "COALESCE(SUM(profit),0) AS profit, COUNT(*) AS tickets, "
        "COALESCE(SUM(quantity_sold),0) AS units "
        "FROM sales WHERE user_id=%s AND sale_date LIKE %s",
        (uid, month_str + '%'))
    row = cur.fetchone() or {}
    month_revenue = float(row.get('revenue') or 0)
    month_profit = float(row.get('profit') or 0)
    month_tickets = int(row.get('tickets') or 0)
    month_units = float(row.get('units') or 0)

    cur.execute(
        "SELECT COUNT(DISTINCT customer_id) AS n FROM sales "
        "WHERE user_id=%s AND sale_date LIKE %s AND customer_id IS NOT NULL",
        (uid, month_str + '%'))
    active_customers = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute('SELECT COUNT(*) AS n FROM customers WHERE user_id=%s', (uid,))
    total_customers = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute(
        "SELECT sale_date, COALESCE(SUM(total_amount),0) AS t "
        "FROM sales WHERE user_id=%s AND sale_date LIKE %s "
        "GROUP BY sale_date ORDER BY t DESC LIMIT 1",
        (uid, month_str + '%'))
    best = cur.fetchone() or {}
    best_day = best.get('sale_date')
    best_day_revenue = float(best.get('t') or 0)

    last_first = (first_of_month - timedelta(days=1)).replace(day=1)
    last_month_str = last_first.strftime('%Y-%m')
    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS revenue, "
        "COALESCE(SUM(profit),0) AS profit "
        "FROM sales WHERE user_id=%s AND sale_date LIKE %s",
        (uid, last_month_str + '%'))
    lm = cur.fetchone() or {}
    last_month_revenue = float(lm.get('revenue') or 0)
    last_month_profit = float(lm.get('profit') or 0)

    cur.close()
    conn.close()

    raw_pct = round((month_revenue / monthly_goal * 100) if monthly_goal else 0, 1)
    goal_progress_pct = min(raw_pct, 100.0)
    pace_target = round(monthly_goal * (day_of_month / last_day), 2) if monthly_goal else 0
    pace_delta = round(month_revenue - pace_target, 2)
    daily_run_rate = round(month_revenue / day_of_month, 2) if day_of_month else 0
    projected_month_end = round(daily_run_rate * last_day, 2)
    avg_margin_pct = round((month_profit / month_revenue * 100) if month_revenue else 0, 1)

    return render_template(
        'goals.html',
        monthly_goal=monthly_goal,
        month_revenue=month_revenue,
        month_profit=month_profit,
        month_tickets=month_tickets,
        month_units=month_units,
        goal_progress_pct=goal_progress_pct,
        raw_goal_pct=raw_pct,
        pace_target=pace_target,
        pace_delta=pace_delta,
        daily_run_rate=daily_run_rate,
        projected_month_end=projected_month_end,
        avg_margin_pct=avg_margin_pct,
        active_customers=active_customers,
        total_customers=total_customers,
        last_month_revenue=last_month_revenue,
        last_month_profit=last_month_profit,
        best_day=best_day,
        best_day_revenue=best_day_revenue,
        day_of_month=day_of_month,
        days_in_month=last_day,
        days_remaining=days_remaining,
        month_label=today.strftime('%B %Y'),
        last_month_label=last_first.strftime('%B %Y'),
    )'''

if OLD_ROUTE not in src:
    if "def goals():" in src and "pace_target" in src:
        print("  [SKIP] /goals already patched")
    else:
        print("  [FAIL] old /goals route not found in app.py")
        print("         restore from backup, then open app.py and search:")
        print("           @app.route('/goals')")
        sys.exit(1)
else:
    src = src.replace(OLD_ROUTE, NEW_ROUTE, 1)
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print("  [OK]   /goals route replaced")

# ─────────────────────────────────────────────────────────────────────
# 2 — rewrite templates/goals.html
# ─────────────────────────────────────────────────────────────────────
print("\n[2/3] Rewriting templates/goals.html…")

NEW_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Business Goals{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="target"></i> Business Goals</h1>
    <p>Live progress against your monthly sales target. Numbers update the moment you ring a sale.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Month</span><strong>{{ month_label }}</strong></div>
  <div class="stat-chip"><span>Revenue</span><strong>{{ money(month_revenue) }}</strong></div>
  <div class="stat-chip"><span>Profit</span><strong>{{ money(month_profit) }}</strong></div>
  <div class="stat-chip"><span>Tickets</span><strong>{{ month_tickets }}</strong></div>
  <div class="stat-chip"><span>Avg margin</span><strong>{{ avg_margin_pct }}%</strong></div>
</div>

{% if monthly_goal > 0 %}
<div class="widget">
  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:1rem;flex-wrap:wrap;">
    <div>
      <h2 style="margin:0;">Monthly sales target</h2>
      <p style="margin:0.35rem 0 0;color:var(--text2);font-size:0.9rem;">
        {{ money(month_revenue) }} of {{ money(monthly_goal) }} — {{ raw_goal_pct }}%
      </p>
    </div>
    <div style="text-align:right;">
      <div style="font-size:2rem;font-family:var(--mono);color:var(--red-bright);">{{ raw_goal_pct }}%</div>
      <div style="font-size:0.8rem;color:var(--text3);">Day {{ day_of_month }} of {{ days_in_month }}</div>
    </div>
  </div>
  <div style="background:var(--surface2);border-radius:10px;height:18px;overflow:hidden;margin:1rem 0 0.75rem;">
    <div style="background:{% if goal_progress_pct >= 100 %}var(--green){% elif pace_delta >= 0 %}var(--red-bright){% else %}#e0a030{% endif %};height:100%;width:{{ goal_progress_pct }}%;transition:width 0.8s var(--ease-out);"></div>
  </div>
  <div class="goal-metrics">
    <div>
      <span>Pace target</span>
      <strong>{{ money(pace_target) }}</strong>
    </div>
    <div>
      <span>{% if pace_delta >= 0 %}Ahead of pace{% else %}Behind pace{% endif %}</span>
      <strong class="{% if pace_delta >= 0 %}profit-positive{% else %}profit-negative{% endif %}">{{ money(pace_delta) }}</strong>
    </div>
    <div>
      <span>Daily run rate</span>
      <strong>{{ money(daily_run_rate) }}</strong>
    </div>
    <div>
      <span>Projected month-end</span>
      <strong class="{% if projected_month_end >= monthly_goal %}profit-positive{% else %}profit-negative{% endif %}">{{ money(projected_month_end) }}</strong>
    </div>
    <div>
      <span>Days remaining</span>
      <strong>{{ days_remaining }}</strong>
    </div>
  </div>
</div>
{% else %}
<div class="widget">
  <h2 style="margin-top:0;">Set your monthly target</h2>
  <p style="color:var(--text2);max-width:40rem;">No monthly sales target yet. Add one in Settings to unlock live progress tracking, pace alerts, and month-end projection.</p>
  <p><a href="{{ url_for('settings') }}" class="btn-secondary" style="text-decoration:none;padding:10px 16px;">Open Settings</a></p>
</div>
{% endif %}

<div class="widget">
  <h2>Customers</h2>
  <div class="stat-grid" style="margin:0;">
    <div class="stat-chip"><span>Total customers</span><strong>{{ total_customers }}</strong></div>
    <div class="stat-chip"><span>Bought this month</span><strong>{{ active_customers }}</strong></div>
    <div class="stat-chip"><span>Walk-ins this month</span><strong>{{ month_tickets - active_customers if month_tickets >= active_customers else 0 }}</strong></div>
  </div>
</div>

<div class="widget">
  <h2>{{ month_label }} vs {{ last_month_label }}</h2>
  <div class="stat-grid" style="margin:0;">
    <div class="stat-chip">
      <span>Revenue this month</span>
      <strong>{{ money(month_revenue) }}</strong>
      {% if last_month_revenue > 0 %}
      {% set rev_pct = ((month_revenue - last_month_revenue) / last_month_revenue * 100)|round(1) %}
      <small style="color:{% if rev_pct >= 0 %}var(--green){% else %}#e74c3c{% endif %};font-size:0.75rem;">{{ '+' if rev_pct >= 0 else '' }}{{ rev_pct }}% vs last month</small>
      {% endif %}
    </div>
    <div class="stat-chip">
      <span>Profit this month</span>
      <strong>{{ money(month_profit) }}</strong>
      {% if last_month_profit > 0 %}
      {% set pft_pct = ((month_profit - last_month_profit) / last_month_profit * 100)|round(1) %}
      <small style="color:{% if pft_pct >= 0 %}var(--green){% else %}#e74c3c{% endif %};font-size:0.75rem;">{{ '+' if pft_pct >= 0 else '' }}{{ pft_pct }}% vs last month</small>
      {% endif %}
    </div>
    <div class="stat-chip">
      <span>Best day this month</span>
      <strong>{{ best_day or '—' }}</strong>
      {% if best_day_revenue %}<small style="color:var(--text3);font-size:0.75rem;">{{ money(best_day_revenue) }}</small>{% endif %}
    </div>
  </div>
</div>

<style>
.goal-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.7rem;
  margin-top: 1rem;
}
.goal-metrics > div {
  padding: 0.7rem 0.85rem;
  background: var(--surface2);
  border-radius: 10px;
}
.goal-metrics span {
  display: block;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text3);
  margin-bottom: 0.25rem;
}
.goal-metrics strong {
  font-family: var(--mono);
  font-size: 1.05rem;
}
.profit-positive { color: var(--green); }
.profit-negative { color: #e74c3c; }
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
# Bonus: verify all variables the template uses are passed
# ─────────────────────────────────────────────────────────────────────
print("\nVerifying template variables…")
import re
used = set(re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)', NEW_TEMPLATE))
required = {
    'monthly_goal', 'month_revenue', 'month_profit', 'month_tickets',
    'month_units', 'goal_progress_pct', 'raw_goal_pct', 'pace_target',
    'pace_delta', 'daily_run_rate', 'projected_month_end', 'avg_margin_pct',
    'active_customers', 'total_customers', 'last_month_revenue',
    'last_month_profit', 'best_day', 'best_day_revenue', 'day_of_month',
    'days_in_month', 'days_remaining', 'month_label', 'last_month_label',
    'money', 'url_for',
}
missing = used - required
if missing:
    print(f"  [WARN] template references: {sorted(missing)}")
else:
    print(f"  [OK]   all {len(used)} variables supplied")

print("\n" + "=" * 60)
print("Done.")
print("=" * 60)
print("\nTest:")
print("  1. Restart Flask")
print("  2. Visit /goals — should show real numbers (0 if no sales this month)")
print("  3. Record a sale → refresh /goals → progress bar moves")
print("  4. Change Settings → Monthly revenue goal → refresh → target updates")