"""
kaze_batch2d_decisions.py — Batch 2d.

Consolidates 5 disabled routes into 1 tabbed page (/analytics/decisions):
  - Scenarios     (worst/base/best cash with adjustable multipliers)
  - Priority      (health issues ranked by weighted impact)
  - Milestones    (goal checkpoints at day 7/14/21/28/end)
  - Opportunities (data-driven growth suggestions)
  - Risks         (warning signals)

Redirects: 5 original URLs -> new tab anchors.
Deferred: /health/history, /reports/variance, /stats/cohort, /stats/seasonality
          (Batch 2e — trends/patterns theme, may need schema).

Run from the folder with app.py:
    python kaze_batch2d_decisions.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

with open(APP, encoding='utf-8') as f:
    src = f.read()

initial_routes = src.count('@app.route')
backup_path = f"{APP}.bak.batch2d_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}\n")

APPLIED = []
FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("[1/6] Remove 5 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = ['/forecast/scenarios', '/health/priority', '/goals/milestones',
             '/insights/opportunities', '/insights/risks']

removed = 0
for path in TO_REMOVE:
    pattern = re.compile(r"\s*'" + re.escape(path) + r"',?\n")
    if pattern.search(src):
        src = pattern.sub('\n', src, count=1)
        removed += 1
        print(f"  [OK]   removed {path}")
    else:
        print(f"  [SKIP] {path} — not found")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/6] Add /analytics/decisions route + 5 redirects")
# ═══════════════════════════════════════════════════════════════════

NEW_ROUTES = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 2d — Decisions & Signals (consolidated from 5 disabled routes)
# ═══════════════════════════════════════════════════════════════════════

_bind_module('dashboard',
    'analytics_decisions',
    'redirect_forecast_scenarios', 'redirect_health_priority',
    'redirect_goals_milestones', 'redirect_insights_opportunities',
    'redirect_insights_risks')


@app.route('/analytics/decisions')
@login_required
def analytics_decisions():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    # ══════════════════════════════════════════════════════
    # TAB 1 — Scenarios (cash projection at 3 multipliers)
    # ══════════════════════════════════════════════════════
    cur.execute("""
        SELECT COALESCE(SUM(opening_balance),0) AS op FROM bank_accounts WHERE user_id=%s
    """, (uid,))
    opening = float((cur.fetchone() or {}).get('op') or 0)

    cur.execute("""
        SELECT COALESCE(SUM(CASE WHEN kind='in' THEN amount ELSE -amount END),0) AS mv
        FROM bank_transactions WHERE user_id=%s
    """, (uid,))
    bank_mv = float((cur.fetchone() or {}).get('mv') or 0)

    cur.execute("SELECT COUNT(*) AS n FROM bank_accounts WHERE user_id=%s", (uid,))
    if int((cur.fetchone() or {}).get('n') or 0) > 0:
        current_cash = opening + bank_mv
        cash_source = 'bank accounts'
    else:
        cur.execute("""
            SELECT COALESCE(SUM(CASE WHEN entry_type='in' THEN amount ELSE -amount END),0) AS net
            FROM cash_books WHERE user_id=%s
        """, (uid,))
        current_cash = float((cur.fetchone() or {}).get('net') or 0)
        cash_source = 'cash book'

    cur.execute("""
        SELECT COALESCE(AVG(daily_rev),0) AS a FROM (
            SELECT SUM(total_amount) AS daily_rev FROM sales
            WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')
            GROUP BY sale_date
        ) t
    """, (uid,))
    avg_daily_revenue = float((cur.fetchone() or {}).get('a') or 0)

    cur.execute("""
        SELECT COALESCE(AVG(daily_exp),0) AS a FROM (
            SELECT SUM(amount) AS daily_exp FROM expenses
            WHERE user_id=%s AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')
            GROUP BY date
        ) t
    """, (uid,))
    avg_daily_expense = float((cur.fetchone() or {}).get('a') or 0)

    cur.execute("""
        SELECT COALESCE(SUM(amount),0) AS t FROM recurring_items
        WHERE user_id=%s AND active=1 AND item_type='expense'
          AND next_run_date <= to_char(CURRENT_DATE + INTERVAL '30 days','YYYY-MM-DD')
    """, (uid,))
    upcoming_recurring = float((cur.fetchone() or {}).get('t') or 0)

    cur.execute("""
        SELECT COALESCE(SUM(total_cost),0) AS t FROM purchase_orders
        WHERE user_id=%s AND status='pending'
    """, (uid,))
    upcoming_pos = float((cur.fetchone() or {}).get('t') or 0)

    net_daily_base = avg_daily_revenue - avg_daily_expense
    daily_obligations = (upcoming_recurring + upcoming_pos) / 30.0

    scenarios = []
    for label, rev_mul, exp_mul in [
        ('Worst case', 0.7, 1.2),
        ('Conservative', 0.9, 1.1),
        ('Base (current pace)', 1.0, 1.0),
        ('Optimistic', 1.2, 0.95),
        ('Best case', 1.4, 0.9),
    ]:
        daily_net = (avg_daily_revenue * rev_mul) - (avg_daily_expense * exp_mul) - daily_obligations
        projected_30 = current_cash + daily_net * 30
        projected_90 = current_cash + daily_net * 90
        scenarios.append({
            'label': label,
            'daily_net': round(daily_net, 2),
            'projected_30': round(projected_30, 2),
            'projected_90': round(projected_90, 2),
            'risk': ('danger' if projected_30 < 0 else
                     'warn' if projected_30 < current_cash * 0.2 else 'ok'),
        })

    # ══════════════════════════════════════════════════════
    # TAB 2 — Priority (health issues ranked by impact)
    # ══════════════════════════════════════════════════════
    cur.execute("""
        SELECT COALESCE(SUM(total_amount),0) AS rev, COALESCE(SUM(profit),0) AS pft
        FROM sales WHERE user_id=%s
          AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')
    """, (uid,))
    r30 = cur.fetchone() or {}
    sales_30 = float(r30.get('rev') or 0)
    profit_30 = float(r30.get('pft') or 0)

    cur.execute("""
        SELECT COALESCE(SUM(total_amount),0) AS rev
        FROM sales WHERE user_id=%s
          AND sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD')
          AND sale_date < to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')
    """, (uid,))
    sales_prev = float((cur.fetchone() or {}).get('rev') or 0)

    cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN quantity <= COALESCE(
                   (SELECT low_stock_threshold FROM settings WHERE user_id=%s), 10)
                   THEN 1 ELSE 0 END) AS low
        FROM stock WHERE user_id=%s
    """, (uid, uid))
    st = cur.fetchone() or {}
    total_sku = int(st.get('total') or 0)
    low_sku = int(st.get('low') or 0)

    cur.execute("""
        SELECT COALESCE(SUM(amount),0) AS m FROM expenses
        WHERE user_id=%s AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')
    """, (uid,))
    exp_30 = float((cur.fetchone() or {}).get('m') or 0)

    cur.execute("""
        SELECT COUNT(DISTINCT customer_id) AS buyers,
               SUM(CASE WHEN c > 1 THEN 1 ELSE 0 END) AS repeaters
        FROM (SELECT customer_id, COUNT(*) AS c FROM sales
              WHERE user_id=%s AND customer_id IS NOT NULL
              GROUP BY customer_id) t
    """, (uid,))
    rb = cur.fetchone() or {}
    buyers = int(rb.get('buyers') or 0)
    repeaters = int(rb.get('repeaters') or 0)

    trend_pct = ((sales_30 - sales_prev) / sales_prev * 100) if sales_prev > 0 else (100 if sales_30 > 0 else 0)
    trend_score = max(0, min(100, int(50 + trend_pct * 0.5)))
    margin_pct = round((profit_30 / sales_30 * 100) if sales_30 > 0 else 0, 1)
    margin_score = max(0, min(100, int(margin_pct * 2.5)))
    stock_score = int(100 - (low_sku / total_sku) * 100) if total_sku > 0 else 100
    monthly_exp = exp_30 if exp_30 > 0 else 1
    months_covered = round(current_cash / monthly_exp, 1) if current_cash > 0 else 0
    cash_score = max(0, min(100, int(months_covered * 50)))
    retention_score = int((repeaters / buyers * 100) if buyers > 0 else 0)

    priority_rows = []
    for name, score, weight, advice in [
        ('Sales trend', trend_score, 30,
         f'30d vs prior 30d: {int(trend_pct):+d}%. Every 10% of trend improvement is worth ~5 health points.'),
        ('Margin', margin_score, 25,
         f'{margin_pct}% avg margin. Raise prices or reduce costs to lift this — each 4% margin is worth ~10 health points.'),
        ('Stock health', stock_score, 15,
         f'{low_sku} of {total_sku} SKUs low. Restock to close the gap.'),
        ('Cash buffer', cash_score, 15,
         f'{months_covered} months covered. Every 0.4 extra months of buffer is worth ~10 health points.'),
        ('Customer retention', retention_score, 15,
         f'{repeaters} of {buyers} customers repeat. Every 10% retention gain is worth ~1.5 health points.'),
    ]:
        gap = 100 - score
        impact = round(gap * weight / 100, 1)
        priority_rows.append({
            'name': name,
            'score': score,
            'gap': gap,
            'weight': weight,
            'impact': impact,
            'advice': advice,
        })
    priority_rows.sort(key=lambda x: -x['impact'])

    # ══════════════════════════════════════════════════════
    # TAB 3 — Milestones (goal pace checkpoints)
    # ══════════════════════════════════════════════════════
    cur.execute("SELECT monthly_revenue_goal FROM settings WHERE user_id=%s", (uid,))
    goal = float((cur.fetchone() or {}).get('monthly_revenue_goal') or 0)

    today = datetime.today()
    month_start = today.replace(day=1)
    days_in_month = ((month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)).day
    day_of_month = today.day
    month_str = today.strftime('%Y-%m')

    cur.execute("""
        SELECT substr(sale_date,1,10) AS d, COALESCE(SUM(total_amount),0) AS t
        FROM sales WHERE user_id=%s AND sale_date LIKE %s
        GROUP BY substr(sale_date,1,10) ORDER BY d
    """, (uid, month_str + '%'))
    daily_map = {r['d']: float(r['t']) for r in cur.fetchall()}

    milestones = []
    checkpoints = [7, 14, 21, 28, days_in_month]
    cumulative = 0.0
    for d in range(1, days_in_month + 1):
        key = f"{month_str}-{d:02d}"
        cumulative += daily_map.get(key, 0) if d <= day_of_month else 0
        if d in checkpoints:
            expected = goal * (d / days_in_month) if goal else 0
            actual = cumulative
            diff = actual - expected
            if d < day_of_month:
                status = 'hit' if diff >= 0 else 'missed'
            elif d == day_of_month or d < day_of_month + 7:
                status = 'ontrack' if diff >= -goal * 0.05 else 'behind'
            else:
                status = 'pending'
            milestones.append({
                'day': d,
                'expected': round(expected, 2),
                'actual': round(actual, 2),
                'diff': round(diff, 2),
                'status': status,
            })

    # ══════════════════════════════════════════════════════
    # TAB 4 — Opportunities (data-driven suggestions)
    # ══════════════════════════════════════════════════════
    opportunities = []

    # High-margin low-velocity products
    cur.execute("""
        SELECT COALESCE(st.product_name, 'Item') AS name,
               COALESCE(SUM(s.quantity_sold),0) AS units,
               COALESCE(SUM(s.total_amount),0) AS revenue,
               COALESCE(SUM(s.profit),0) AS profit
        FROM sales s LEFT JOIN stock st ON st.id = s.stock_id
        WHERE s.user_id=%s
          AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD')
        GROUP BY st.product_name
        HAVING COUNT(*) >= 2
    """, (uid,))
    for r in (cur.fetchall() or []):
        rev = float(r.get('revenue') or 0)
        pft = float(r.get('profit') or 0)
        units = float(r.get('units') or 0)
        if rev > 0:
            margin = pft / rev * 100
            if margin >= 30 and units < 5:
                opportunities.append({
                    'icon': 'trending-up', 'severity': 'info',
                    'title': f'High-margin, low-volume: {r.get("name") or "Item"}',
                    'detail': f'{round(margin, 1)}% margin but only {int(units)} units sold in 60 days. '
                              f'Bundle it with a faster seller or feature it prominently — margin is already good.',
                })

    # Lapsed repeaters (bought before, not in last 60 days)
    cur.execute("""
        SELECT c.name, MAX(s.sale_date) AS last_sale, COUNT(s.id) AS orders
        FROM customers c JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id
        WHERE c.user_id=%s
        GROUP BY c.id, c.name
        HAVING COUNT(s.id) >= 2
           AND MAX(s.sale_date) < to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD')
        ORDER BY MAX(s.sale_date) ASC
        LIMIT 5
    """, (uid,))
    lapsed = list(cur.fetchall() or [])
    if lapsed:
        names = ', '.join(r['name'] for r in lapsed[:3])
        opportunities.append({
            'icon': 'users', 'severity': 'info',
            'title': f'{len(lapsed)} regular customer(s) have not bought in 60+ days',
            'detail': f'Top lapsed: {names}. A small discount or reminder often reactivates them — '
                      f'they have already shown they buy from you.',
        })

    # Best day of week
    cur.execute("""
        SELECT EXTRACT(DOW FROM sale_date::date) AS dow,
               COALESCE(SUM(total_amount),0) AS rev
        FROM sales WHERE user_id=%s
          AND sale_date >= to_char(CURRENT_DATE - INTERVAL '90 days','YYYY-MM-DD')
        GROUP BY EXTRACT(DOW FROM sale_date::date)
        ORDER BY rev DESC LIMIT 1
    """, (uid,))
    dow_row = cur.fetchone()
    if dow_row and float(dow_row.get('rev') or 0) > 0:
        dow_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        try:
            dow_idx = int(dow_row.get('dow') or 0)
            day_name = dow_names[dow_idx] if 0 <= dow_idx < 7 else 'a weekday'
        except (ValueError, TypeError):
            day_name = 'a weekday'
        opportunities.append({
            'icon': 'calendar', 'severity': 'success',
            'title': f'{day_name} is your strongest sales day',
            'detail': f'Based on last 90 days. Consider extra staff, longer hours, or targeted promos on {day_name}s.',
        })

    # ══════════════════════════════════════════════════════
    # TAB 5 — Risks (warning signals)
    # ══════════════════════════════════════════════════════
    risks = []

    # Low stock
    if low_sku > 0:
        risks.append({
            'icon': 'alert-triangle', 'severity': 'danger' if low_sku >= 5 else 'warn',
            'title': f'{low_sku} product(s) below stock threshold',
            'detail': f'Of {total_sku} tracked SKUs. Restock soon to avoid stockouts.',
        })

    # Sales trend decline
    if trend_pct < -15:
        risks.append({
            'icon': 'trending-down', 'severity': 'warn',
            'title': f'Sales down {abs(int(trend_pct))}% vs prior 30 days',
            'detail': f'Last 30 days: {round(sales_30, 2)} vs prior 30: {round(sales_prev, 2)}. Investigate cause before it becomes a pattern.',
        })

    # Negative-margin products
    cur.execute("""
        SELECT COALESCE(st.product_name, 'Item') AS name,
               COALESCE(SUM(s.total_amount),0) AS revenue,
               COALESCE(SUM(s.profit),0) AS profit
        FROM sales s LEFT JOIN stock st ON st.id = s.stock_id
        WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '90 days','YYYY-MM-DD')
        GROUP BY st.product_name HAVING COUNT(*) >= 2 AND SUM(s.profit) < 0
        ORDER BY SUM(s.profit) ASC LIMIT 5
    """, (uid,))
    losing = list(cur.fetchall() or [])
    if losing:
        names = ', '.join(r['name'] for r in losing[:3])
        risks.append({
            'icon': 'alert-circle', 'severity': 'danger',
            'title': f'{len(losing)} product(s) with negative margin',
            'detail': f'Losing money on: {names}. Either raise the price or stop selling.',
        })

    # Top customer gone quiet
    cur.execute("""
        SELECT c.name, MAX(s.sale_date) AS last_sale,
               COALESCE(SUM(s.total_amount),0) AS spent
        FROM customers c JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id
        WHERE c.user_id=%s
        GROUP BY c.id, c.name
        ORDER BY spent DESC LIMIT 1
    """, (uid,))
    top_cust = cur.fetchone()
    if top_cust:
        last = (top_cust.get('last_sale') or '')[:10]
        try:
            days = (today.date() - datetime.strptime(last, '%Y-%m-%d').date()).days if last else 9999
        except ValueError:
            days = 9999
        if days >= 60:
            risks.append({
                'icon': 'users', 'severity': 'warn',
                'title': f'Top customer has gone quiet ({days}d)',
                'detail': f'{top_cust.get("name")} was your highest-spending customer. Reach out before they are lost.',
            })

    # Cash concern
    if current_cash < monthly_exp * 1.5 and current_cash > 0:
        risks.append({
            'icon': 'wallet', 'severity': 'warn' if months_covered >= 1 else 'danger',
            'title': f'Cash buffer is {months_covered} months',
            'detail': f'Current cash {round(current_cash, 2)} vs monthly expenses ~{round(monthly_exp, 2)}. '
                      f'Below 3 months of buffer is tight — watch collections and defer non-critical spend.',
        })

    cur.close(); conn.close()

    return render_template('analytics_decisions.html',
        scenarios=scenarios,
        current_cash=current_cash,
        cash_source=cash_source,
        avg_daily_revenue=avg_daily_revenue,
        avg_daily_expense=avg_daily_expense,
        daily_obligations=round(daily_obligations, 2),
        priority_rows=priority_rows,
        goal=goal,
        milestones=milestones,
        day_of_month=day_of_month,
        days_in_month=days_in_month,
        opportunities=opportunities,
        risks=risks,
    )


@app.route('/forecast/scenarios')
@login_required
def redirect_forecast_scenarios():
    return redirect(url_for('analytics_decisions') + '#scenarios', code=301)


@app.route('/health/priority')
@login_required
def redirect_health_priority():
    return redirect(url_for('analytics_decisions') + '#priority', code=301)


@app.route('/goals/milestones')
@login_required
def redirect_goals_milestones():
    return redirect(url_for('analytics_decisions') + '#milestones', code=301)


@app.route('/insights/opportunities')
@login_required
def redirect_insights_opportunities():
    return redirect(url_for('analytics_decisions') + '#opportunities', code=301)


@app.route('/insights/risks')
@login_required
def redirect_insights_risks():
    return redirect(url_for('analytics_decisions') + '#risks', code=301)

'''

if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + NEW_ROUTES + '\n' + src[idx:]
else:
    src += '\n' + NEW_ROUTES
print("  [OK]   inserted /analytics/decisions + 5 redirects")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/6] Add Decisions to NAV")
# ═══════════════════════════════════════════════════════════════════

NAV_ANCHOR = "        ('Books health', 'accounts_health', 'book-open-check', 'accounts', ('accounts_health',)),"
NAV_NEW = """        ('Books health', 'accounts_health', 'book-open-check', 'accounts', ('accounts_health',)),
        ('Decisions & signals', 'analytics_decisions', 'lightbulb', 'reports', ('analytics_decisions',)),"""

if NAV_ANCHOR in src:
    src = src.replace(NAV_ANCHOR, NAV_NEW, 1)
    print("  [OK]   Decisions & signals added to Analytics nav")
    APPLIED.append("nav")
else:
    print("  [FAIL] nav anchor not found (Books health entry)")
    FAILED.append("nav")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/6] Write app.py")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   {initial_routes} -> {final_routes} @app.route (+{final_routes - initial_routes})")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/6] Write template")
# ═══════════════════════════════════════════════════════════════════

os.makedirs('templates', exist_ok=True)

TPL = '''{% extends "base.html" %}
{% block title %}Decisions & Signals{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="lightbulb"></i> Decisions & Signals</h1>
    <p>Scenarios, priorities, milestones, opportunities, and risks — everything that asks "what should I do next?".</p>
  </div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="scenarios" class="is-on">Scenarios</button>
  <button type="button" data-tab="priority">Priority</button>
  <button type="button" data-tab="milestones">Milestones</button>
  <button type="button" data-tab="opportunities">Opportunities</button>
  <button type="button" data-tab="risks">Risks</button>
</nav>

<section class="analytics-panel is-on" id="panel-scenarios">
  <h2>Cash projection scenarios</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Current cash: <strong>{{ money(current_cash) }}</strong> (from {{ cash_source }}).
    Avg daily revenue: {{ money(avg_daily_revenue) }} · Avg daily expense: {{ money(avg_daily_expense) }} · Daily obligations: {{ money(daily_obligations) }}.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Scenario</th><th style="text-align:right;">Daily net</th><th style="text-align:right;">Projected 30d</th><th style="text-align:right;">Projected 90d</th><th>Signal</th></tr></thead>
      <tbody>
      {% for s in scenarios %}
      <tr {% if s.risk == 'danger' %}style="background:var(--danger-dim);"{% elif s.risk == 'warn' %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td><strong>{{ s.label }}</strong></td>
        <td style="text-align:right;font-family:var(--mono);{% if s.daily_net < 0 %}color:#e74c3c;{% else %}color:var(--green);{% endif %}">{{ money(s.daily_net) }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(s.projected_30) }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(s.projected_90) }}</td>
        <td>
          {% if s.risk == 'danger' %}<span class="status-pill" style="background:var(--danger-dim);color:#e74c3c;">Cash squeeze</span>
          {% elif s.risk == 'warn' %}<span class="status-pill" style="background:rgba(224,160,48,0.15);color:#e0a030;">Tight</span>
          {% else %}<span class="status-pill status-ok">Healthy</span>{% endif %}
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<section class="analytics-panel" id="panel-priority">
  <h2>What to fix first</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Each health component below shows its current score (out of 100), how much room is left, and how much health-score impact closing that gap would give.
    <strong>Sorted by impact</strong> — work top to bottom for maximum effect.
  </p>
  {% if priority_rows %}
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Component</th><th style="text-align:right;">Score</th><th style="text-align:right;">Gap</th><th style="text-align:right;">Weight</th><th style="text-align:right;">Impact</th><th>What to do</th></tr></thead>
      <tbody>
      {% for r in priority_rows %}
      <tr {% if loop.first %}style="background:var(--green-dim);"{% endif %}>
        <td><strong>{{ r.name }}</strong></td>
        <td style="text-align:right;font-family:var(--mono);">{{ r.score }}/100</td>
        <td style="text-align:right;font-family:var(--mono);">{{ r.gap }}</td>
        <td style="text-align:right;">{{ r.weight }}%</td>
        <td style="text-align:right;font-family:var(--mono);font-weight:700;color:var(--red-bright);">+{{ r.impact }}</td>
        <td style="font-size:0.85rem;">{{ r.advice }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No health data yet.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-milestones">
  <h2>Goal milestones — {{ day_of_month }} of {{ days_in_month }} days elapsed</h2>
  {% if goal > 0 %}
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Monthly goal: <strong>{{ money(goal) }}</strong>. Each checkpoint shows expected pace vs actual cumulative revenue at that day.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Checkpoint</th><th style="text-align:right;">Expected</th><th style="text-align:right;">Actual</th><th style="text-align:right;">Difference</th><th>Status</th></tr></thead>
      <tbody>
      {% for m in milestones %}
      <tr {% if m.status == 'missed' %}style="background:var(--danger-dim);"{% elif m.status == 'behind' %}style="background:rgba(224,160,48,0.08);"{% elif m.status == 'hit' %}style="background:var(--green-dim);"{% endif %}>
        <td>Day {{ m.day }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(m.expected) }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(m.actual) }}</td>
        <td style="text-align:right;font-family:var(--mono);{% if m.diff < 0 %}color:#e74c3c;{% elif m.diff > 0 %}color:var(--green);{% endif %}">{{ money(m.diff) }}</td>
        <td>
          {% if m.status == 'hit' %}<span class="status-pill status-ok">Hit</span>
          {% elif m.status == 'missed' %}<span class="status-pill" style="background:var(--danger-dim);color:#e74c3c;">Missed</span>
          {% elif m.status == 'ontrack' %}<span class="status-pill status-ok">On track</span>
          {% elif m.status == 'behind' %}<span class="status-pill" style="background:rgba(224,160,48,0.15);color:#e0a030;">Behind</span>
          {% else %}<span class="status-pill" style="background:var(--surface2);color:var(--text3);">Pending</span>{% endif %}
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">
    Set a monthly revenue goal in <a href="{{ url_for('settings') }}">Settings</a> to unlock milestone tracking.
  </p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-opportunities">
  <h2>Growth opportunities</h2>
  {% if opportunities %}
  {% for o in opportunities %}
  <div class="widget" style="border-left:4px solid {% if o.severity == 'success' %}var(--green){% else %}#3498db{% endif %};">
    <div style="display:flex;gap:0.75rem;align-items:flex-start;">
      <div style="flex-shrink:0;width:32px;height:32px;display:grid;place-items:center;border-radius:8px;background:var(--surface2);">
        <i data-lucide="{{ o.icon }}"></i>
      </div>
      <div style="flex:1;">
        <strong>{{ o.title }}</strong>
        <p style="margin:0.35rem 0 0;font-size:0.9rem;color:var(--text2);">{{ o.detail }}</p>
      </div>
    </div>
  </div>
  {% endfor %}
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No specific growth opportunities detected right now. This is a good sign — nothing obvious to chase.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-risks">
  <h2>Risk signals</h2>
  {% if risks %}
  {% for r in risks %}
  <div class="widget" style="border-left:4px solid {% if r.severity == 'danger' %}#e74c3c{% elif r.severity == 'warn' %}#e0a030{% else %}#3498db{% endif %};">
    <div style="display:flex;gap:0.75rem;align-items:flex-start;">
      <div style="flex-shrink:0;width:32px;height:32px;display:grid;place-items:center;border-radius:8px;background:var(--surface2);">
        <i data-lucide="{{ r.icon }}"></i>
      </div>
      <div style="flex:1;">
        <strong>{{ r.title }}</strong>
        <p style="margin:0.35rem 0 0;font-size:0.9rem;color:var(--text2);">{{ r.detail }}</p>
      </div>
    </div>
  </div>
  {% endfor %}
  {% else %}
  <div class="widget"><p style="color:var(--green);">No risk signals detected. Your data looks healthy across all tracked signals.</p></div>
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
  if (['scenarios','priority','milestones','opportunities','risks'].includes(hash)) {
    activate(hash);
  }
})();
</script>
{% endblock %}
'''

with open('templates/analytics_decisions.html', 'w', encoding='utf-8') as f:
    f.write(TPL)
print("  [OK]   templates/analytics_decisions.html")

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
print(f"  New routes added:        6 (1 page + 5 redirects)")
print(f"  New templates:           1")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 5 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 2d complete.

NEXT STEPS — in this exact order:

1. LOCAL TEST — run:  python app.py
   Visit:

     /analytics/decisions   -> 5 tabs (Scenarios / Priority / Milestones /
                                Opportunities / Risks)
                                Click each. Some may show "no data yet" (fine).
                                Scenarios should show 5 rows with projections.
                                Priority should show 5 components ranked.

     /forecast/scenarios    -> 301 redirect to /analytics/decisions#scenarios
     /health/priority       -> 301 redirect to /analytics/decisions#priority
     /goals/milestones      -> 301 redirect to /analytics/decisions#milestones
     /insights/opportunities -> 301 redirect to /analytics/decisions#opportunities
     /insights/risks        -> 301 redirect to /analytics/decisions#risks

   Sidebar: 5 entries under Analytics now
            (Sales, Customer, Inventory, Books health, Decisions & signals).

   Regression — verify still works:
     /dashboard
     /plans (Active — renews 2027-10-26)
     /sales/analytics, /customers/analytics, /stock/analytics, /accounts/health

2. DO NOT delete the backup yet. Do not commit. Do not push.

   Report back the local test results with an honest ✅ / ❌ per item.

3. Only after I confirm your local test results, commit + push + deploy.

4. Test on production (same URLs).

5. Only after prod pass — delete backup: rm app.py.bak.batch2d_*

Note: /health/history, /reports/variance, /stats/cohort, /stats/seasonality
are NOT in this batch. They're deferred to Batch 2e (trends & patterns).
""")