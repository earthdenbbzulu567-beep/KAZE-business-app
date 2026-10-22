"""
enhance_app.py — D (try/except on /) + enhanced /goals, /insights, /profit_matrix.
Batch 1 of the Supreme page rebuild.

Run from the folder with app.py:
    python enhance_app.py
"""
import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'

if not os.path.isfile(APP):
    print("ERROR: app.py not found.")
    sys.exit(1)

shutil.copy2(APP, f"{APP}.bak.{STAMP}")
print(f"Backup: {APP}.bak.{STAMP}\n")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

APPLIED, FAILED = [], []

def replace_route(label, route_path, new_body):
    """Replace an entire @app.route(...) block up to the next @app or top-level."""
    global src
    pattern = re.compile(
        r"@app\.route\('" + re.escape(route_path) + r"'[^)]*\)\n"
        r"(?:@[^\n]+\n)*"
        r"def \w+\([^)]*\):\n"
        r".*?"
        r"(?=\n@app\.|\n# ===|\n# ───|\ndef |\nif __name__|\Z)",
        re.DOTALL,
    )
    match = pattern.search(src)
    if not match:
        if new_body in src:
            print(f"  [SKIP] {label} — already enhanced")
            return
        print(f"  [FAIL] {label} — pattern not found")
        FAILED.append(label)
        return
    src = src[:match.start()] + new_body + src[match.end():]
    print(f"  [OK] {label}")
    APPLIED.append(label)

def write_template(path, content):
    if os.path.isfile(path):
        shutil.copy2(path, f"{path}.bak.{STAMP}")
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f"  [OK] {path}")
    APPLIED.append(path)

# ═══════════════════════════════════════════════════════════════════════
# D — Safe index (fallback if templates missing)
# ═══════════════════════════════════════════════════════════════════════
print("[1/4] / — safe fallback")

SAFE_INDEX = '''@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception:
        from flask import redirect as _rd
        return _rd('/login')
'''
replace_route('/ safe index', '/', SAFE_INDEX)

# ═══════════════════════════════════════════════════════════════════════
# ENHANCED /goals
# ═══════════════════════════════════════════════════════════════════════
print("\n[2/4] /goals — enhanced")

NEW_GOALS = r'''@app.route('/goals')
@login_required
def goals():
    """Live progress against the monthly sales target, with pace chart and weekday breakdown."""
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

    # Daily sales for chart + cumulative
    cur.execute(
        "SELECT substr(sale_date,1,10) AS d, COALESCE(SUM(total_amount),0) AS t, "
        "COUNT(*) AS n FROM sales WHERE user_id=%s AND sale_date LIKE %s "
        "GROUP BY substr(sale_date,1,10) ORDER BY d",
        (uid, month_str + '%'))
    daily_map = {r['d']: (float(r['t']), int(r['n'])) for r in cur.fetchall()}

    daily_actual = []
    daily_pace = []
    cumulative_actual = 0.0
    cumulative_pace = 0.0
    daily_target = (monthly_goal / last_day) if last_day else 0
    for d in range(1, last_day + 1):
        key = f"{month_str}-{d:02d}"
        if d <= day_of_month:
            day_rev = daily_map.get(key, (0, 0))[0]
        else:
            day_rev = 0
        cumulative_actual += day_rev
        daily_actual.append(round(cumulative_actual, 2))
        cumulative_pace += daily_target
        daily_pace.append(round(cumulative_pace, 2))

    # Weekday breakdown
    weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    weekday_rev = {i: 0.0 for i in range(7)}
    weekday_count = {i: 0 for i in range(7)}
    for key, (rev, tickets) in daily_map.items():
        try:
            dt = datetime.strptime(key, '%Y-%m-%d')
            weekday_rev[dt.weekday()] += rev
            weekday_count[dt.weekday()] += 1
        except ValueError:
            continue

    weekday_avg = []
    for i in range(7):
        avg = weekday_rev[i] / weekday_count[i] if weekday_count[i] else 0
        weekday_avg.append({'name': weekday_names[i], 'avg': round(avg, 2),
                             'total': round(weekday_rev[i], 2), 'count': weekday_count[i]})
    best_weekday = max(weekday_avg, key=lambda x: x['avg']) if any(w['avg'] for w in weekday_avg) else None

    # Days hit target
    days_hit = sum(1 for d, (rev, _) in daily_map.items() if daily_target and rev >= daily_target)
    days_active = len(daily_map)

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
    days_labels = [f"{d}" for d in range(1, last_day + 1)]

    return render_template(
        'goals.html',
        monthly_goal=monthly_goal,
        month_revenue=month_revenue, month_profit=month_profit,
        month_tickets=month_tickets, month_units=month_units,
        goal_progress_pct=goal_progress_pct, raw_goal_pct=raw_pct,
        pace_target=pace_target, pace_delta=pace_delta,
        daily_run_rate=daily_run_rate, projected_month_end=projected_month_end,
        avg_margin_pct=avg_margin_pct,
        active_customers=active_customers, total_customers=total_customers,
        last_month_revenue=last_month_revenue, last_month_profit=last_month_profit,
        best_day=best_day, best_day_revenue=best_day_revenue,
        day_of_month=day_of_month, days_in_month=last_day, days_remaining=days_remaining,
        month_label=today.strftime('%B %Y'), last_month_label=last_first.strftime('%B %Y'),
        daily_actual=daily_actual, daily_pace=daily_pace,
        daily_labels=days_labels, daily_target=round(daily_target, 2),
        weekday_avg=weekday_avg, best_weekday=best_weekday,
        days_hit=days_hit, days_active=days_active,
    )


'''
replace_route('/goals enhanced', '/goals', NEW_GOALS)

NEW_GOALS_TPL = '''{% extends "base.html" %}
{% block title %}Business Goals{% endblock %}
{% block charts_js %}<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="target"></i> Business Goals</h1>
    <p>Live progress against your monthly sales target, with pace tracking and weekday patterns.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Month</span><strong>{{ month_label }}</strong></div>
  <div class="stat-chip"><span>Revenue</span><strong>{{ money(month_revenue) }}</strong></div>
  <div class="stat-chip"><span>Profit</span><strong>{{ money(month_profit) }}</strong></div>
  <div class="stat-chip"><span>Margin</span><strong>{{ avg_margin_pct }}%</strong></div>
  <div class="stat-chip"><span>Tickets</span><strong>{{ month_tickets }}</strong></div>
  <div class="stat-chip"><span>Customers</span><strong>{{ active_customers }}/{{ total_customers }}</strong></div>
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
    <div><span>Pace target</span><strong>{{ money(pace_target) }}</strong></div>
    <div><span>{% if pace_delta >= 0 %}Ahead of pace{% else %}Behind pace{% endif %}</span>
      <strong class="{% if pace_delta >= 0 %}profit-positive{% else %}profit-negative{% endif %}">{{ money(pace_delta) }}</strong></div>
    <div><span>Daily run rate</span><strong>{{ money(daily_run_rate) }}</strong></div>
    <div><span>Projected month-end</span>
      <strong class="{% if projected_month_end >= monthly_goal %}profit-positive{% else %}profit-negative{% endif %}">{{ money(projected_month_end) }}</strong></div>
    <div><span>Days remaining</span><strong>{{ days_remaining }}</strong></div>
    <div><span>Days hitting target</span><strong>{{ days_hit }}/{{ days_active }}</strong></div>
  </div>
</div>

<h2>Cumulative sales vs pace</h2>
<div class="chart-container">
  <canvas id="goalsChart" height="140"></canvas>
</div>
{% else %}
<div class="widget">
  <h2 style="margin-top:0;">Set your monthly target</h2>
  <p style="color:var(--text2);max-width:40rem;">No monthly sales target yet. Add one in Settings to unlock pace tracking, projections, and target-hit counting.</p>
  <p><a href="{{ url_for('settings') }}" class="btn-secondary" style="text-decoration:none;padding:10px 16px;">Open Settings</a></p>
</div>
{% endif %}

{% if best_weekday %}
<h2>Best days of the week</h2>
<div class="widget">
  <p style="margin:0 0 0.8rem;color:var(--text2);font-size:0.9rem;">
    Your strongest day is <strong>{{ best_weekday.name }}</strong> averaging {{ money(best_weekday.avg) }} per occurrence.
  </p>
  <div class="weekday-bars">
    {% for w in weekday_avg %}
    {% set pct = (w.avg / best_weekday.avg * 100) if best_weekday.avg else 0 %}
    <div class="weekday-row">
      <span class="wd-label">{{ w.name }}</span>
      <div class="wd-bar-wrap"><div class="wd-bar" style="width:{{ pct }}%;"></div></div>
      <span class="wd-value">{{ money(w.avg) }}</span>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}

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
      <span>Best day</span>
      <strong>{{ best_day or '—' }}</strong>
      {% if best_day_revenue %}<small style="color:var(--text3);font-size:0.75rem;">{{ money(best_day_revenue) }}</small>{% endif %}
    </div>
  </div>
</div>

<script>
{% if monthly_goal > 0 %}
(function(){
  new Chart(document.getElementById('goalsChart'), {
    type: 'line',
    data: {
      labels: {{ daily_labels|tojson }},
      datasets: [
        { label: 'Actual cumulative', data: {{ daily_actual|tojson }}, borderColor: '#2ecc71', backgroundColor: 'rgba(46,204,113,0.12)', fill: true, tension: 0.25, borderWidth: 3 },
        { label: 'Pace to target', data: {{ daily_pace|tojson }}, borderColor: '#3498db', borderDash: [6,4], fill: false, tension: 0, borderWidth: 2 }
      ]
    },
    options: {
      responsive: true,
      plugins: { title: { display: true, text: 'Running total vs target pace' },
                 tooltip: { callbacks: { label: c => c.dataset.label + ': ' + window.kazeMoney(c.raw) } } },
      scales: { y: { ticks: { callback: v => window.kazeMoney(v) } } }
    }
  });
})();
{% endif %}
</script>

<style>
.goal-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.7rem; margin-top: 1rem; }
.goal-metrics > div { padding: 0.7rem 0.85rem; background: var(--surface2); border-radius: 10px; }
.goal-metrics span { display: block; font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text3); margin-bottom: 0.25rem; }
.goal-metrics strong { font-family: var(--mono); font-size: 1.05rem; }
.profit-positive { color: var(--green); }
.profit-negative { color: #e74c3c; }
.weekday-bars { display: flex; flex-direction: column; gap: 0.4rem; }
.weekday-row { display: grid; grid-template-columns: 44px 1fr 90px; align-items: center; gap: 0.6rem; font-size: 0.88rem; }
.wd-label { font-weight: 700; color: var(--text2); }
.wd-bar-wrap { height: 10px; background: var(--surface2); border-radius: 4px; overflow: hidden; }
.wd-bar { height: 100%; background: linear-gradient(90deg, var(--red-bright), var(--green)); border-radius: 4px; }
.wd-value { font-family: var(--mono); font-size: 0.82rem; text-align: right; }
</style>
{% endblock %}
'''
write_template('templates/goals.html', NEW_GOALS_TPL)

# ═══════════════════════════════════════════════════════════════════════
# ENHANCED /insights
# ═══════════════════════════════════════════════════════════════════════
print("\n[3/4] /insights — enhanced")

NEW_INSIGHTS = r'''@app.route('/insights')
@login_required
def insights():
    """Live business insights with 30-day trend chart and gainers/decliners."""
    uid = current_user.id
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS revenue, COALESCE(SUM(profit),0) AS profit, "
        "COUNT(*) AS tickets, COUNT(DISTINCT customer_id) AS customers "
        "FROM sales WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')",
        (uid,))
    r30 = cur.fetchone() or {}
    revenue_30 = float(r30.get('revenue') or 0)
    profit_30 = float(r30.get('profit') or 0)
    tickets_30 = int(r30.get('tickets') or 0)
    customers_30 = int(r30.get('customers') or 0)

    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS revenue FROM sales WHERE user_id=%s "
        "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
        "AND sale_date < to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    revenue_prev = float((cur.fetchone() or {}).get('revenue') or 0)
    if revenue_prev > 0:
        revenue_change_pct = round((revenue_30 - revenue_prev) / revenue_prev * 100, 1)
    else:
        revenue_change_pct = 100 if revenue_30 > 0 else 0

    cur.execute(
        "SELECT substr(sale_date,1,10) AS d, COALESCE(SUM(total_amount),0) AS t "
        "FROM sales WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '29 days','YYYY-MM-DD') "
        "GROUP BY substr(sale_date,1,10) ORDER BY d", (uid,))
    daily_map = {r['d']: float(r['t']) for r in cur.fetchall()}
    trend_labels, trend_values = [], []
    for i in range(29, -1, -1):
        d = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        trend_labels.append(d[5:])
        trend_values.append(round(daily_map.get(d, 0), 2))

    cur.execute(
        "SELECT st.product_name, COALESCE(SUM(s.total_amount),0) AS rev_30 "
        "FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
        "WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
        "GROUP BY st.product_name", (uid,))
    cur_rev = {r['product_name'] or 'Item': float(r['rev_30']) for r in cur.fetchall()}
    cur.execute(
        "SELECT st.product_name, COALESCE(SUM(s.total_amount),0) AS rev_prev "
        "FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
        "WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
        "AND s.sale_date < to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
        "GROUP BY st.product_name", (uid,))
    prev_rev = {r['product_name'] or 'Item': float(r['rev_prev']) for r in cur.fetchall()}

    changes = []
    for name in set(cur_rev) | set(prev_rev):
        a, b = cur_rev.get(name, 0), prev_rev.get(name, 0)
        delta = a - b
        pct = (delta / b * 100) if b > 0 else (100 if a > 0 else 0)
        changes.append({'name': name, 'current': a, 'previous': b, 'delta': delta, 'pct': round(pct, 1)})
    top_gainers = sorted([c for c in changes if c['delta'] > 0], key=lambda x: x['delta'], reverse=True)[:3]
    top_decliners = sorted([c for c in changes if c['delta'] < 0], key=lambda x: x['delta'])[:3]

    cur.execute(
        "SELECT st.product_name, COUNT(*) AS tickets, COALESCE(SUM(s.total_amount),0) AS rev, "
        "COALESCE(SUM(s.profit),0) AS profit "
        "FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
        "WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
        "GROUP BY st.product_name HAVING COUNT(*) >= 3", (uid,))
    margin_rows = []
    for r in (cur.fetchall() or []):
        rev = float(r.get('rev') or 0)
        pft = float(r.get('profit') or 0)
        if rev > 0:
            margin_rows.append({'name': r.get('product_name') or 'Item', 'revenue': rev, 'profit': pft,
                                'tickets': int(r.get('tickets') or 0), 'margin_pct': round(pft / rev * 100, 1)})
    margin_rows.sort(key=lambda x: x['margin_pct'])
    worst_margin = margin_rows[0] if margin_rows else None

    cur.execute(
        "SELECT COUNT(*) AS n FROM stock st WHERE st.user_id=%s AND st.quantity <= COALESCE("
        "(SELECT low_stock_threshold FROM settings WHERE user_id=%s), 10)", (uid, uid))
    low_stock = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute(
        "SELECT COUNT(*) AS n FROM stock st WHERE st.user_id=%s AND NOT EXISTS ("
        "SELECT 1 FROM sales s WHERE s.stock_id = st.id "
        "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD'))", (uid,))
    dead_stock = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute(
        "SELECT COALESCE(SUM(quantity * cost_price),0) AS v FROM stock st "
        "WHERE st.user_id=%s AND NOT EXISTS ("
        "SELECT 1 FROM sales s WHERE s.stock_id = st.id "
        "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD'))", (uid,))
    dead_capital = float((cur.fetchone() or {}).get('v') or 0)

    cur.execute(
        "SELECT COALESCE(payment_method,'cash') AS method, COUNT(*) AS tickets, "
        "COALESCE(SUM(total_amount),0) AS revenue FROM sales WHERE user_id=%s "
        "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
        "GROUP BY payment_method ORDER BY revenue DESC", (uid,))
    payment_mix = [{'method': (r.get('method') or 'cash').title(), 'tickets': int(r.get('tickets') or 0),
                    'revenue': float(r.get('revenue') or 0)} for r in (cur.fetchall() or [])]

    cur.execute(
        "SELECT COALESCE(SUM(quantity * cost_price),0) AS cost_value, "
        "COALESCE(SUM(quantity * selling_price),0) AS sell_value FROM stock WHERE user_id=%s", (uid,))
    sv = cur.fetchone() or {}
    stock_cost_value = float(sv.get('cost_value') or 0)
    stock_sell_value = float(sv.get('sell_value') or 0)
    cur.close()
    conn.close()

    insight_cards = []
    if top_gainers:
        top = top_gainers[0]
        insight_cards.append({'severity': 'success', 'icon': 'trending-up',
            'title': f"Fastest growing: {top['name']}",
            'detail': f"+{window_money_str(top['delta'])} vs prior 30 days ({top['pct']:+}%). Current: {window_money_str(top['current'])}.",
            'action_label': 'Open stock', 'action_url': url_for('stock')})
    else:
        insight_cards.append({'severity': 'info', 'icon': 'package',
            'title': 'No growth trends detected yet',
            'detail': 'Need sales in both the last 30 days and the prior 30 days to spot movement.',
            'action_label': 'Record a sale', 'action_url': url_for('sales')})

    if worst_margin:
        sev = 'danger' if worst_margin['margin_pct'] < 0 else ('warn' if worst_margin['margin_pct'] < 15 else 'info')
        insight_cards.append({'severity': sev, 'icon': 'trending-down',
            'title': f"Lowest margin: {worst_margin['name']}",
            'detail': f"{worst_margin['margin_pct']}% over {worst_margin['tickets']} tickets. Revenue {window_money_str(worst_margin['revenue'])} · profit {window_money_str(worst_margin['profit'])}.",
            'action_label': 'Edit prices', 'action_url': url_for('stock')})

    if low_stock > 0:
        insight_cards.append({'severity': 'danger' if low_stock >= 5 else 'warn', 'icon': 'alert-triangle',
            'title': f"{low_stock} product(s) below stock threshold",
            'detail': 'Restock soon. Change the threshold in Settings.', 'action_label': 'Open stock', 'action_url': url_for('stock')})
    else:
        insight_cards.append({'severity': 'success', 'icon': 'check-circle',
            'title': 'Stock levels healthy', 'detail': 'No products below the low-stock threshold.',
            'action_label': 'Review stock', 'action_url': url_for('stock')})

    if dead_stock > 0:
        insight_cards.append({'severity': 'warn', 'icon': 'package',
            'title': f"{dead_stock} dead-stock item(s) holding {window_money_str(dead_capital)}",
            'detail': 'No sales in 60 days. Bundle or discount to free up cash.',
            'action_label': 'Open stock', 'action_url': url_for('stock')})

    if payment_mix and revenue_30 > 0:
        top_pay = payment_mix[0]
        share = round(top_pay['revenue'] / revenue_30 * 100, 1)
        insight_cards.append({'severity': 'info', 'icon': 'credit-card',
            'title': 'Payment mix',
            'detail': f"{share}% of revenue ({window_money_str(top_pay['revenue'])}) via {top_pay['method']} in the last 30 days.",
            'action_label': 'Open payments', 'action_url': url_for('payments')})

    return render_template('insights.html', insight_cards=insight_cards,
        revenue_30=revenue_30, profit_30=profit_30, tickets_30=tickets_30, customers_30=customers_30,
        revenue_prev=revenue_prev, revenue_change_pct=revenue_change_pct,
        trend_labels=trend_labels, trend_values=trend_values,
        top_gainers=top_gainers, top_decliners=top_decliners,
        low_stock=low_stock, dead_stock=dead_stock, dead_capital=dead_capital,
        payment_mix=payment_mix,
        stock_cost_value=stock_cost_value, stock_sell_value=stock_sell_value)


def window_money_str(v):
    return _format_money(v)


'''
replace_route('/insights enhanced', '/insights', NEW_INSIGHTS)

NEW_INSIGHTS_TPL = '''{% extends "base.html" %}
{% block title %}Business Insights{% endblock %}
{% block charts_js %}<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="lightbulb"></i> Business Insights</h1>
    <p>Live facts computed from your last 30-60 days of sales, stock, and customers.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Revenue (30d)</span><strong>{{ money(revenue_30) }}</strong>
    {% if revenue_prev > 0 %}<small style="color:{% if revenue_change_pct >= 0 %}var(--green){% else %}#e74c3c{% endif %};font-size:0.72rem;">{{ '+' if revenue_change_pct >= 0 else '' }}{{ revenue_change_pct }}% vs prior</small>{% endif %}
  </div>
  <div class="stat-chip"><span>Profit (30d)</span><strong>{{ money(profit_30) }}</strong></div>
  <div class="stat-chip"><span>Tickets (30d)</span><strong>{{ tickets_30 }}</strong></div>
  <div class="stat-chip"><span>Customers (30d)</span><strong>{{ customers_30 }}</strong></div>
  <div class="stat-chip"><span>Low stock</span><strong>{{ low_stock }}</strong></div>
  <div class="stat-chip"><span>Dead stock</span><strong>{{ dead_stock }}</strong></div>
</div>

<h2>Revenue trend</h2>
<div class="chart-container">
  <canvas id="insightsChart" height="140"></canvas>
</div>

<h2>Recommendations</h2>
<div class="insight-grid">
{% for ins in insight_cards %}
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

{% if top_gainers or top_decliners %}
<h2>Moving products</h2>
<div class="insight-cols">
  {% if top_gainers %}
  <div class="widget">
    <h3 style="margin-top:0;">Top gainers (30d vs prior 30d)</h3>
    <table class="data-table">
      <thead><tr><th>Product</th><th>Current</th><th>Change</th></tr></thead>
      <tbody>
      {% for g in top_gainers %}
        <tr><td>{{ g.name }}</td><td>{{ money(g.current) }}</td>
          <td style="color:var(--green);">+{{ money(g.delta) }} ({{ g.pct }}%)</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}
  {% if top_decliners %}
  <div class="widget">
    <h3 style="margin-top:0;">Top decliners</h3>
    <table class="data-table">
      <thead><tr><th>Product</th><th>Current</th><th>Change</th></tr></thead>
      <tbody>
      {% for d in top_decliners %}
        <tr><td>{{ d.name }}</td><td>{{ money(d.current) }}</td>
          <td style="color:#e74c3c;">{{ money(d.delta) }} ({{ d.pct }}%)</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}
</div>
{% endif %}

{% if payment_mix %}
<h2>Payment mix (30 days)</h2>
<div class="table-wrapper">
<table>
<thead><tr><th>Method</th><th>Tickets</th><th>Revenue</th><th>% of total</th></tr></thead>
<tbody>
{% for p in payment_mix %}
<tr><td>{{ p.method }}</td><td>{{ p.tickets }}</td><td>{{ money(p.revenue) }}</td>
  <td>{% if revenue_30 > 0 %}{{ ((p.revenue / revenue_30) * 100)|round(1) }}%{% else %}—{% endif %}</td></tr>
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
    <div class="stat-chip"><span>Dead capital</span><strong>{{ money(dead_capital) }}</strong></div>
  </div>
</div>

<script>
(function(){
  new Chart(document.getElementById('insightsChart'), {
    type: 'line',
    data: {
      labels: {{ trend_labels|tojson }},
      datasets: [{
        label: 'Daily revenue (30d)', data: {{ trend_values|tojson }},
        borderColor: '#2ecc71', backgroundColor: 'rgba(46,204,113,0.12)',
        fill: true, tension: 0.25, borderWidth: 2
      }]
    },
    options: { responsive: true,
      plugins: { title: { display: true, text: 'Daily revenue · last 30 days' },
                 tooltip: { callbacks: { label: c => window.kazeMoney(c.raw) } } },
      scales: { y: { ticks: { callback: v => window.kazeMoney(v) }, beginAtZero: true } } }
  });
})();
</script>

<style>
.insight-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; margin: 1rem 0 1.5rem; }
.insight-card { display: flex; gap: 0.9rem; padding: 1.1rem 1.2rem; border-radius: 14px; border: 1px solid var(--border);
  background: var(--surface); border-left-width: 4px; transition: transform .16s ease; }
.insight-card:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,0.18); }
.insight-card.insight-success { border-left-color: var(--green); }
.insight-card.insight-info { border-left-color: #3498db; }
.insight-card.insight-warn { border-left-color: #e0a030; }
.insight-card.insight-danger { border-left-color: #e74c3c; }
.insight-icon { width: 40px; height: 40px; flex-shrink: 0; display: grid; place-items: center; border-radius: 10px; background: var(--surface2); }
.insight-success .insight-icon { background: var(--green-dim); color: var(--green); }
.insight-info .insight-icon { background: rgba(52,152,219,0.12); color: #3498db; }
.insight-warn .insight-icon { background: rgba(224,160,48,0.12); color: #e0a030; }
.insight-danger .insight-icon { background: rgba(231,76,60,0.12); color: #e74c3c; }
.insight-icon svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.75; }
.insight-body { flex: 1; min-width: 0; }
.insight-body h3 { margin: 0 0 0.35rem; font-size: 1rem; font-weight: 700; }
.insight-body p { margin: 0 0 0.55rem; font-size: 0.88rem; color: var(--text2); line-height: 1.5; }
.insight-action { font-size: 0.82rem; font-weight: 700; color: var(--red-bright); text-decoration: none; }
.insight-action:hover { text-decoration: underline; }
.insight-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 0 0 1rem; }
@media (max-width: 800px) { .insight-cols { grid-template-columns: 1fr; } }
</style>
{% endblock %}
'''
write_template('templates/insights.html', NEW_INSIGHTS_TPL)

# ═══════════════════════════════════════════════════════════════════════
# ENHANCED /profit_matrix
# ═══════════════════════════════════════════════════════════════════════
print("\n[4/4] /profit_matrix — enhanced")

NEW_PM = r'''@app.route('/profit_matrix')
@login_required
def profit_matrix():
    """2×2 scatter + Pareto chart + action recommendations."""
    uid = current_user.id
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT st.product_name AS name, COALESCE(SUM(s.total_amount),0) AS revenue, "
        "COALESCE(SUM(s.profit),0) AS profit, COALESCE(SUM(s.quantity_sold),0) AS units, "
        "COUNT(*) AS tickets FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
        "WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '90 days','YYYY-MM-DD') "
        "GROUP BY st.product_name ORDER BY revenue DESC", (uid,))
    rows = []
    for r in (cur.fetchall() or []):
        rev = float(r.get('revenue') or 0)
        pft = float(r.get('profit') or 0)
        margin_pct = round((pft / rev * 100) if rev > 0 else 0, 1)
        rows.append({'name': r.get('name') or 'Item', 'revenue': rev, 'profit': pft,
                     'units': float(r.get('units') or 0), 'tickets': int(r.get('tickets') or 0),
                     'margin_pct': margin_pct})
    cur.close()
    conn.close()

    avg_rev = round(sum(r['revenue'] for r in rows) / len(rows), 2) if rows else 0
    avg_margin = round(sum(r['margin_pct'] for r in rows) / len(rows), 1) if rows else 0

    buckets = {'star': [], 'cash_cow': [], 'rocket': [], 'dog': []}
    for r in rows:
        hr, hm = r['revenue'] >= avg_rev, r['margin_pct'] >= avg_margin
        if hr and hm: key = 'star'
        elif hr and not hm: key = 'cash_cow'
        elif not hr and hm: key = 'rocket'
        else: key = 'dog'
        r['quadrant'] = key
        buckets[key].append(r)

    actions = {
        'star':    {'icon': 'star', 'title': 'Stars', 'advice': 'High revenue, high margin. Protect supply, keep price stable, feature them.'},
        'cash_cow':{'icon': 'dollar-sign', 'title': 'Cash cows', 'advice': 'High volume but low margin. Reprice or renegotiate cost. Cash flow drivers.'},
        'rocket':  {'icon': 'rocket', 'title': 'Rockets', 'advice': 'High margin, low volume. Promote and bundle — margin is already good.'},
        'dog':     {'icon': 'alert-circle', 'title': 'Dogs', 'advice': 'Low revenue and low margin. Consider discontinuing or bundling to clear stock.'},
    }
    for k, v in actions.items():
        v['count'] = len(buckets[k])
        v['total_revenue'] = round(sum(r['revenue'] for r in buckets[k]), 2)

    # Pareto: sort by revenue, cumulative %
    total_rev = sum(r['revenue'] for r in rows)
    pareto_labels, pareto_values, pareto_cumulative = [], [], []
    cumulative = 0.0
    for r in rows[:15]:
        pareto_labels.append(r['name'])
        pareto_values.append(round(r['revenue'], 2))
        cumulative += r['revenue']
        pareto_cumulative.append(round((cumulative / total_rev * 100) if total_rev else 0, 1))

    return render_template('profit_matrix.html', rows=rows,
        stars=buckets['star'], cash_cows=buckets['cash_cow'],
        rockets=buckets['rocket'], dogs=buckets['dog'],
        avg_revenue=avg_rev, avg_margin=avg_margin, actions=actions,
        pareto_labels=pareto_labels, pareto_values=pareto_values, pareto_cumulative=pareto_cumulative,
        total_revenue=round(total_rev, 2), top15_count=len(pareto_labels))


'''
replace_route('/profit_matrix enhanced', '/profit_matrix', NEW_PM)

NEW_PM_TPL = '''{% extends "base.html" %}
{% block title %}Product Profitability{% endblock %}
{% block charts_js %}<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="pie-chart"></i> Profitability Matrix</h1>
    <p>Revenue vs margin over the last 90 days. Avg revenue: {{ money(avg_revenue) }} · Avg margin: {{ avg_margin }}%.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Products</span><strong>{{ rows|length }}</strong></div>
  <div class="stat-chip"><span>Stars</span><strong>{{ stars|length }}</strong></div>
  <div class="stat-chip"><span>Cash cows</span><strong>{{ cash_cows|length }}</strong></div>
  <div class="stat-chip"><span>Rockets</span><strong>{{ rockets|length }}</strong></div>
  <div class="stat-chip"><span>Dogs</span><strong>{{ dogs|length }}</strong></div>
  <div class="stat-chip"><span>Total revenue</span><strong>{{ money(total_revenue) }}</strong></div>
</div>

{% if rows %}
<h2>Positioning</h2>
<div class="chart-container">
  <canvas id="pmChart" height="160"></canvas>
</div>

<h2>What to do, by quadrant</h2>
<div class="action-grid">
  {% for key in ['star','cash_cow','rocket','dog'] %}
  {% set a = actions[key] %}
  <div class="action-card action-{{ key }}">
    <div class="action-head">
      <strong>{{ a.title }}</strong>
      <span class="action-count">{{ a.count }}</span>
    </div>
    <p class="action-advice">{{ a.advice }}</p>
    <div class="action-rev">{{ money(a.total_revenue) }} revenue</div>
  </div>
  {% endfor %}
</div>

<h2>Pareto — which products make your money</h2>
<div class="chart-container">
  <canvas id="paretoChart" height="150"></canvas>
</div>
<p style="margin:-0.5rem 0 1rem;font-size:0.85rem;color:var(--text3);">
  The bars are revenue per product. The line shows cumulative %. If the top {{ top15_count }} products hit 80% before the end, you have concentration risk — a small number of products you cannot afford to lose.
</p>

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
{% else %}
<div class="widget"><p style="color:var(--text3);">No sales in the last 90 days. Record a sale to populate the matrix.</p></div>
{% endif %}

<script>
{% if rows %}
(function(){
  const data = {{ rows|tojson }};
  const colors = {star:'#2ecc71', cash_cow:'#3498db', rocket:'#e0a030', dog:'#e74c3c'};
  const groups = {star:[], cash_cow:[], rocket:[], dog:[]};
  data.forEach(r => groups[r.quadrant].push({x: r.revenue, y: r.margin_pct, name: r.name}));
  new Chart(document.getElementById('pmChart'), {
    type: 'scatter',
    data: { datasets: [
      {label: 'Stars', data: groups.star, backgroundColor: colors.star, pointRadius: 8},
      {label: 'Cash cows', data: groups.cash_cow, backgroundColor: colors.cash_cow, pointRadius: 8},
      {label: 'Rockets', data: groups.rocket, backgroundColor: colors.rocket, pointRadius: 8},
      {label: 'Dogs', data: groups.dog, backgroundColor: colors.dog, pointRadius: 8}
    ]},
    options: { responsive: true,
      plugins: { title: { display: true, text: 'Revenue vs margin (last 90 days)' },
                 tooltip: { callbacks: { label: c => `${c.raw.name} · ${window.kazeMoney(c.raw.x)} · ${c.raw.y}%` } } },
      scales: { x: { title: { display: true, text: 'Revenue' }, ticks: { callback: v => window.kazeMoney(v) } },
                y: { title: { display: true, text: 'Margin %' }, beginAtZero: true } } }
  });

  new Chart(document.getElementById('paretoChart'), {
    type: 'bar',
    data: {
      labels: {{ pareto_labels|tojson }},
      datasets: [
        { type: 'bar', label: 'Revenue', data: {{ pareto_values|tojson }},
          backgroundColor: 'rgba(46,204,113,0.7)', yAxisID: 'y' },
        { type: 'line', label: 'Cumulative %', data: {{ pareto_cumulative|tojson }},
          borderColor: '#3498db', backgroundColor: 'rgba(52,152,219,0.1)',
          yAxisID: 'y1', tension: 0.2, borderWidth: 2 }
      ]
    },
    options: { responsive: true,
      plugins: { title: { display: true, text: 'Revenue concentration (Pareto)' } },
      scales: {
        x: { ticks: { autoSkip: true, maxRotation: 45 } },
        y: { title: { display: true, text: 'Revenue' }, ticks: { callback: v => window.kazeMoney(v) } },
        y1: { position: 'right', title: { display: true, text: 'Cumulative %' }, min: 0, max: 100, grid: { drawOnChartArea: false } }
      } }
  });
})();
{% endif %}
</script>

<style>
.action-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.9rem; margin: 0 0 1.5rem; }
.action-card { padding: 1.1rem 1.2rem; border-radius: 14px; border: 1px solid var(--border); background: var(--surface); border-left-width: 4px; }
.action-card.action-star { border-left-color: #2ecc71; }
.action-card.action-cash_cow { border-left-color: #3498db; }
.action-card.action-rocket { border-left-color: #e0a030; }
.action-card.action-dog { border-left-color: #e74c3c; }
.action-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.4rem; }
.action-head strong { font-size: 1rem; }
.action-count { font-family: var(--mono); font-size: 1.3rem; font-weight: 800; }
.action-advice { font-size: 0.85rem; color: var(--text2); margin: 0 0 0.5rem; line-height: 1.5; }
.action-rev { font-size: 0.78rem; color: var(--text3); font-family: var(--mono); }
</style>
{% endblock %}
'''
write_template('templates/profit_matrix.html', NEW_PM_TPL)

# ═══════════════════════════════════════════════════════════════════════
# Compile check
# ═══════════════════════════════════════════════════════════════════════
print("\nVerifying app.py compiles...")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK] app.py compiles cleanly.\n")
else:
    print("  [FAIL] syntax error:")
    print(r.stderr)
    backup = f"{APP}.bak.{STAMP}"
    print(f"\nRestore with:  Copy-Item \"{backup}\" {APP}")
    sys.exit(1)

print("=" * 60)
print(f"Applied: {len(APPLIED)}   Failed: {len(FAILED)}")
if FAILED:
    print("\nFailed items:")
    for f in FAILED: print(f"  - {f}")
else:
    print("\nBatch 1 done (try/except + goals + insights + profit_matrix).")
    print("\nTest locally:")
    print("  python app.py")
    print("  Open http://localhost:5000/  /goals  /insights  /profit_matrix")
print("=" * 60)