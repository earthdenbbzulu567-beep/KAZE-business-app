"""
supreme_fix_1.py — critical write-to-disk fix + enhanced goals/insights/profit_matrix + batches fix.

Run from the folder with app.py:
    python supreme_fix_1.py

What makes THIS script different from the last attempt:
  - It WRITES app.py to disk (previously in-memory only)
  - It RE-READS app.py from disk to VERIFY the writes landed
  - If verification fails, it exits non-zero and tells you
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

with open(APP, 'r', encoding='utf-8') as f:
    src = f.read()
original_size = len(src)
print(f"Original app.py: {original_size:,} bytes\n")

# ─────────────────────────────────────────────────────────────────────
# Helper: replace an entire route block
# ─────────────────────────────────────────────────────────────────────
def replace_route(code, route_path, new_body):
    pattern = re.compile(
        r"@app\.route\('" + re.escape(route_path) + r"'[^)]*\)\n"
        r"(?:@[^\n]+\n)*"
        r"def \w+\([^)]*\):\n"
        r".*?"
        r"(?=\n@app\.|\n# ===|\n# ───|\ndef |\nif __name__|\Z)",
        re.DOTALL,
    )
    m = pattern.search(code)
    if not m:
        return code, False
    return code[:m.start()] + new_body + code[m.end():], True

# ═════════════════════════════════════════════════════════════════════
# 1. / — safe fallback (no crash if template missing)
# ═════════════════════════════════════════════════════════════════════
print("[1/5] / — safe fallback")
SAFE_INDEX = '''@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception:
        from flask import redirect as _rd
        return _rd('/login')
'''
src, ok = replace_route(src, '/', SAFE_INDEX)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 2. /goals — enhanced
# ═════════════════════════════════════════════════════════════════════
print("\n[2/5] /goals — enhanced")
NEW_GOALS = r'''@app.route('/goals')
@login_required
def goals():
    """Pace-tracked monthly sales target with chart and weekday analysis."""
    uid = current_user.id
    today = datetime.today()
    month_str = today.strftime('%Y-%m')
    first_of_month = today.replace(day=1)
    first_of_next_month = (first_of_month + timedelta(days=32)).replace(day=1)
    last_day = (first_of_next_month - timedelta(days=1)).day
    day_of_month = today.day
    days_remaining = last_day - day_of_month

    conn = get_db(); cur = conn.cursor()
    settings_row = _get_settings_row(uid) or {}
    try:
        monthly_goal = float(settings_row.get('monthly_revenue_goal') or 0)
    except (TypeError, ValueError):
        monthly_goal = 0.0

    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS revenue, COALESCE(SUM(profit),0) AS profit, "
        "COUNT(*) AS tickets, COALESCE(SUM(quantity_sold),0) AS units "
        "FROM sales WHERE user_id=%s AND sale_date LIKE %s",
        (uid, month_str + '%'))
    row = cur.fetchone() or {}
    month_revenue = float(row.get('revenue') or 0)
    month_profit = float(row.get('profit') or 0)
    month_tickets = int(row.get('tickets') or 0)
    month_units = float(row.get('units') or 0)

    cur.execute(
        "SELECT substr(sale_date,1,10) AS d, COALESCE(SUM(total_amount),0) AS t "
        "FROM sales WHERE user_id=%s AND sale_date LIKE %s "
        "GROUP BY substr(sale_date,1,10) ORDER BY d",
        (uid, month_str + '%'))
    daily_map = {r['d']: float(r['t']) for r in cur.fetchall()}

    daily_actual, daily_pace = [], []
    cum_a = cum_p = 0.0
    daily_target = (monthly_goal / last_day) if last_day else 0
    for d in range(1, last_day + 1):
        key = f"{month_str}-{d:02d}"
        day_rev = daily_map.get(key, 0) if d <= day_of_month else 0
        cum_a += day_rev; cum_p += daily_target
        daily_actual.append(round(cum_a, 2))
        daily_pace.append(round(cum_p, 2))

    weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    wd_rev = {i: 0.0 for i in range(7)}
    wd_cnt = {i: 0 for i in range(7)}
    for key, rev in daily_map.items():
        try:
            dt = datetime.strptime(key, '%Y-%m-%d')
            wd_rev[dt.weekday()] += rev
            wd_cnt[dt.weekday()] += 1
        except ValueError:
            continue
    weekday_avg = [{'name': weekday_names[i],
                    'avg': round(wd_rev[i] / wd_cnt[i], 2) if wd_cnt[i] else 0}
                   for i in range(7)]
    best_weekday = max(weekday_avg, key=lambda x: x['avg']) if any(w['avg'] for w in weekday_avg) else None

    days_hit = sum(1 for rev in daily_map.values() if daily_target and rev >= daily_target)
    days_active = len(daily_map)

    cur.execute("SELECT COUNT(DISTINCT customer_id) AS n FROM sales WHERE user_id=%s "
                "AND sale_date LIKE %s AND customer_id IS NOT NULL", (uid, month_str + '%'))
    active_customers = int((cur.fetchone() or {}).get('n') or 0)
    cur.execute('SELECT COUNT(*) AS n FROM customers WHERE user_id=%s', (uid,))
    total_customers = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute("SELECT sale_date, COALESCE(SUM(total_amount),0) AS t FROM sales WHERE user_id=%s "
                "AND sale_date LIKE %s GROUP BY sale_date ORDER BY t DESC LIMIT 1",
                (uid, month_str + '%'))
    best = cur.fetchone() or {}
    best_day = best.get('sale_date')
    best_day_revenue = float(best.get('t') or 0)

    last_first = (first_of_month - timedelta(days=1)).replace(day=1)
    last_month_str = last_first.strftime('%Y-%m')
    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS revenue, COALESCE(SUM(profit),0) AS profit "
                "FROM sales WHERE user_id=%s AND sale_date LIKE %s", (uid, last_month_str + '%'))
    lm = cur.fetchone() or {}
    last_month_revenue = float(lm.get('revenue') or 0)
    last_month_profit = float(lm.get('profit') or 0)
    cur.close(); conn.close()

    raw_pct = round((month_revenue / monthly_goal * 100) if monthly_goal else 0, 1)
    goal_progress_pct = min(raw_pct, 100.0)
    pace_target = round(monthly_goal * (day_of_month / last_day), 2) if monthly_goal else 0
    pace_delta = round(month_revenue - pace_target, 2)
    daily_run_rate = round(month_revenue / day_of_month, 2) if day_of_month else 0
    projected_month_end = round(daily_run_rate * last_day, 2)
    avg_margin_pct = round((month_profit / month_revenue * 100) if month_revenue else 0, 1)

    return render_template('goals.html',
        monthly_goal=monthly_goal, month_revenue=month_revenue, month_profit=month_profit,
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
        daily_labels=[str(d) for d in range(1, last_day + 1)],
        daily_target=round(daily_target, 2),
        weekday_avg=weekday_avg, best_weekday=best_weekday,
        days_hit=days_hit, days_active=days_active)


'''
src, ok = replace_route(src, '/goals', NEW_GOALS)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 3. /insights — enhanced
# ═════════════════════════════════════════════════════════════════════
print("\n[3/5] /insights — enhanced")
NEW_INSIGHTS = r'''@app.route('/insights')
@login_required
def insights():
    """Live business insights with 30d trend, gainers/decliners, dead capital."""
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS revenue, COALESCE(SUM(profit),0) AS profit, "
                "COUNT(*) AS tickets, COUNT(DISTINCT customer_id) AS customers "
                "FROM sales WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    r30 = cur.fetchone() or {}
    revenue_30 = float(r30.get('revenue') or 0)
    profit_30 = float(r30.get('profit') or 0)
    tickets_30 = int(r30.get('tickets') or 0)
    customers_30 = int(r30.get('customers') or 0)

    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS r FROM sales WHERE user_id=%s "
                "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
                "AND sale_date < to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    revenue_prev = float((cur.fetchone() or {}).get('r') or 0)
    revenue_change_pct = round((revenue_30 - revenue_prev) / revenue_prev * 100, 1) if revenue_prev > 0 else (100 if revenue_30 > 0 else 0)

    cur.execute("SELECT substr(sale_date,1,10) AS d, COALESCE(SUM(total_amount),0) AS t FROM sales "
                "WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '29 days','YYYY-MM-DD') "
                "GROUP BY substr(sale_date,1,10) ORDER BY d", (uid,))
    daily_map = {r['d']: float(r['t']) for r in cur.fetchall()}
    trend_labels, trend_values = [], []
    for i in range(29, -1, -1):
        d = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        trend_labels.append(d[5:])
        trend_values.append(round(daily_map.get(d, 0), 2))

    cur.execute("SELECT st.product_name, COALESCE(SUM(s.total_amount),0) AS rev FROM sales s "
                "LEFT JOIN stock st ON st.id = s.stock_id WHERE s.user_id=%s "
                "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
                "GROUP BY st.product_name", (uid,))
    cur_rev = {r['product_name'] or 'Item': float(r['rev']) for r in cur.fetchall()}
    cur.execute("SELECT st.product_name, COALESCE(SUM(s.total_amount),0) AS rev FROM sales s "
                "LEFT JOIN stock st ON st.id = s.stock_id WHERE s.user_id=%s "
                "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
                "AND s.sale_date < to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
                "GROUP BY st.product_name", (uid,))
    prev_rev = {r['product_name'] or 'Item': float(r['rev']) for r in cur.fetchall()}

    changes = []
    for name in set(cur_rev) | set(prev_rev):
        a, b = cur_rev.get(name, 0), prev_rev.get(name, 0)
        changes.append({'name': name, 'current': a, 'delta': a - b,
                        'pct': round((a - b) / b * 100, 1) if b > 0 else (100 if a > 0 else 0)})
    top_gainers = sorted([c for c in changes if c['delta'] > 0], key=lambda x: x['delta'], reverse=True)[:3]
    top_decliners = sorted([c for c in changes if c['delta'] < 0], key=lambda x: x['delta'])[:3]

    cur.execute("SELECT st.product_name, COUNT(*) AS t, COALESCE(SUM(s.total_amount),0) AS r, "
                "COALESCE(SUM(s.profit),0) AS p FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
                "WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
                "GROUP BY st.product_name HAVING COUNT(*) >= 3", (uid,))
    margin_rows = [{'name': r['product_name'] or 'Item', 'revenue': float(r['r'] or 0),
                    'profit': float(r['p'] or 0), 'tickets': int(r['t'] or 0),
                    'margin_pct': round(float(r['p'] or 0) / float(r['r']) * 100, 1) if r['r'] else 0}
                   for r in (cur.fetchall() or [])]
    margin_rows.sort(key=lambda x: x['margin_pct'])
    worst_margin = margin_rows[0] if margin_rows else None

    cur.execute("SELECT COUNT(*) AS n FROM stock st WHERE st.user_id=%s AND st.quantity <= COALESCE("
                "(SELECT low_stock_threshold FROM settings WHERE user_id=%s), 10)", (uid, uid))
    low_stock = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute("SELECT COUNT(*) AS n FROM stock st WHERE st.user_id=%s AND NOT EXISTS ("
                "SELECT 1 FROM sales s WHERE s.stock_id = st.id "
                "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD'))", (uid,))
    dead_stock = int((cur.fetchone() or {}).get('n') or 0)

    cur.execute("SELECT COALESCE(SUM(quantity * cost_price),0) AS v FROM stock st WHERE st.user_id=%s "
                "AND NOT EXISTS (SELECT 1 FROM sales s WHERE s.stock_id = st.id "
                "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD'))", (uid,))
    dead_capital = float((cur.fetchone() or {}).get('v') or 0)

    cur.execute("SELECT COALESCE(payment_method,'cash') AS m, COUNT(*) AS t, "
                "COALESCE(SUM(total_amount),0) AS r FROM sales WHERE user_id=%s "
                "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') "
                "GROUP BY payment_method ORDER BY r DESC", (uid,))
    payment_mix = [{'method': (r['m'] or 'cash').title(), 'tickets': int(r['t'] or 0),
                    'revenue': float(r['r'] or 0)} for r in (cur.fetchall() or [])]

    cur.execute("SELECT COALESCE(SUM(quantity * cost_price),0) AS c, "
                "COALESCE(SUM(quantity * selling_price),0) AS s FROM stock WHERE user_id=%s", (uid,))
    sv = cur.fetchone() or {}
    cur.close(); conn.close()

    insight_cards = []
    if top_gainers:
        t = top_gainers[0]
        insight_cards.append({'severity': 'success', 'icon': 'trending-up',
            'title': f"Fastest growing: {t['name']}",
            'detail': f"+{_format_money(t['delta'])} vs prior 30 days.",
            'action_label': 'Open stock', 'action_url': url_for('stock')})
    else:
        insight_cards.append({'severity': 'info', 'icon': 'package',
            'title': 'No growth trends detected yet',
            'detail': 'Need sales in both the last 30 and prior 30 days.',
            'action_label': 'Record a sale', 'action_url': url_for('sales')})
    if worst_margin:
        sev = 'danger' if worst_margin['margin_pct'] < 0 else ('warn' if worst_margin['margin_pct'] < 15 else 'info')
        insight_cards.append({'severity': sev, 'icon': 'trending-down',
            'title': f"Lowest margin: {worst_margin['name']}",
            'detail': f"{worst_margin['margin_pct']}% over {worst_margin['tickets']} tickets.",
            'action_label': 'Edit prices', 'action_url': url_for('stock')})
    if low_stock > 0:
        insight_cards.append({'severity': 'warn', 'icon': 'alert-triangle',
            'title': f"{low_stock} product(s) below stock threshold",
            'detail': 'Restock soon.', 'action_label': 'Open stock', 'action_url': url_for('stock')})
    else:
        insight_cards.append({'severity': 'success', 'icon': 'check-circle',
            'title': 'Stock levels healthy', 'detail': 'No products below threshold.',
            'action_label': 'Review stock', 'action_url': url_for('stock')})
    if dead_stock > 0:
        insight_cards.append({'severity': 'warn', 'icon': 'package',
            'title': f"{dead_stock} dead-stock item(s) · {_format_money(dead_capital)} tied up",
            'detail': 'No sales in 60 days.', 'action_label': 'Open stock', 'action_url': url_for('stock')})
    if payment_mix and revenue_30 > 0:
        tp = payment_mix[0]
        insight_cards.append({'severity': 'info', 'icon': 'credit-card',
            'title': 'Payment mix',
            'detail': f"{round(tp['revenue']/revenue_30*100,1)}% via {tp['method']} in last 30 days.",
            'action_label': 'Open payments', 'action_url': url_for('payments')})

    return render_template('insights.html', insight_cards=insight_cards,
        revenue_30=revenue_30, profit_30=profit_30, tickets_30=tickets_30, customers_30=customers_30,
        revenue_prev=revenue_prev, revenue_change_pct=revenue_change_pct,
        trend_labels=trend_labels, trend_values=trend_values,
        top_gainers=top_gainers, top_decliners=top_decliners,
        low_stock=low_stock, dead_stock=dead_stock, dead_capital=dead_capital,
        payment_mix=payment_mix,
        stock_cost_value=float(sv.get('c') or 0), stock_sell_value=float(sv.get('s') or 0))


'''
src, ok = replace_route(src, '/insights', NEW_INSIGHTS)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 4. /profit_matrix — enhanced
# ═════════════════════════════════════════════════════════════════════
print("\n[4/5] /profit_matrix — enhanced")
NEW_PM = r'''@app.route('/profit_matrix')
@login_required
def profit_matrix():
    """2x2 quadrant scatter + Pareto concentration chart + quadrant action cards."""
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT st.product_name AS name, COALESCE(SUM(s.total_amount),0) AS revenue, "
                "COALESCE(SUM(s.profit),0) AS profit, COALESCE(SUM(s.quantity_sold),0) AS units, "
                "COUNT(*) AS tickets FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
                "WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '90 days','YYYY-MM-DD') "
                "GROUP BY st.product_name ORDER BY revenue DESC", (uid,))
    rows = []
    for r in (cur.fetchall() or []):
        rev = float(r.get('revenue') or 0); pft = float(r.get('profit') or 0)
        rows.append({'name': r.get('name') or 'Item', 'revenue': rev, 'profit': pft,
                     'units': float(r.get('units') or 0), 'tickets': int(r.get('tickets') or 0),
                     'margin_pct': round((pft / rev * 100) if rev > 0 else 0, 1)})
    cur.close(); conn.close()

    avg_rev = round(sum(r['revenue'] for r in rows) / len(rows), 2) if rows else 0
    avg_margin = round(sum(r['margin_pct'] for r in rows) / len(rows), 1) if rows else 0

    buckets = {'star': [], 'cash_cow': [], 'rocket': [], 'dog': []}
    for r in rows:
        hr, hm = r['revenue'] >= avg_rev, r['margin_pct'] >= avg_margin
        key = 'star' if hr and hm else ('cash_cow' if hr else ('rocket' if hm else 'dog'))
        r['quadrant'] = key
        buckets[key].append(r)

    actions = {
        'star': {'title': 'Stars', 'advice': 'High revenue, high margin. Protect supply, keep price stable, feature them.'},
        'cash_cow': {'title': 'Cash cows', 'advice': 'High volume, low margin. Reprice or renegotiate cost.'},
        'rocket': {'title': 'Rockets', 'advice': 'High margin, low volume. Promote and bundle — margin is already good.'},
        'dog': {'title': 'Dogs', 'advice': 'Low revenue, low margin. Consider discontinuing or bundling to clear stock.'},
    }
    for k, v in actions.items():
        v['count'] = len(buckets[k])
        v['total_revenue'] = round(sum(r['revenue'] for r in buckets[k]), 2)

    total_rev = sum(r['revenue'] for r in rows)
    pareto_labels, pareto_values, pareto_cumulative = [], [], []
    cum = 0.0
    for r in rows[:15]:
        pareto_labels.append(r['name'])
        pareto_values.append(round(r['revenue'], 2))
        cum += r['revenue']
        pareto_cumulative.append(round((cum / total_rev * 100) if total_rev else 0, 1))

    return render_template('profit_matrix.html', rows=rows,
        stars=buckets['star'], cash_cows=buckets['cash_cow'],
        rockets=buckets['rocket'], dogs=buckets['dog'],
        avg_revenue=avg_rev, avg_margin=avg_margin, actions=actions,
        pareto_labels=pareto_labels, pareto_values=pareto_values, pareto_cumulative=pareto_cumulative,
        total_revenue=round(total_rev, 2), top15_count=len(pareto_labels))


'''
src, ok = replace_route(src, '/profit_matrix', NEW_PM)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 5. /batches — fix the SQL that causes 500
# ═════════════════════════════════════════════════════════════════════
print("\n[5/5] /batches — fix SQL")
BATCHES_OLD = 'SELECT name, quantity FROM stock WHERE user_id=%s LIMIT 20'
BATCHES_NEW = "SELECT product_name AS name, quantity, COALESCE(unit,'') AS unit FROM stock WHERE user_id=%s ORDER BY product_name LIMIT 50"
if BATCHES_OLD in src:
    src = src.replace(BATCHES_OLD, BATCHES_NEW, 1)
    print("  [OK] SQL fixed (product_name AS name)")
else:
    print("  [SKIP] batches SQL already fixed or pattern not found")

# ═════════════════════════════════════════════════════════════════════
# ⚠️  CRITICAL: WRITE app.py TO DISK ⚠️
# ═════════════════════════════════════════════════════════════════════
print("\n[WRITE] Writing app.py to disk...")
with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
new_size = len(src)
print(f"  Wrote {new_size:,} bytes (was {original_size:,}, +{new_size - original_size:,})")

# ═════════════════════════════════════════════════════════════════════
# ⚠️  CRITICAL: RE-READ FROM DISK TO VERIFY ⚠️
# ═════════════════════════════════════════════════════════════════════
print("\n[VERIFY] Re-reading app.py from disk to confirm writes landed...")
with open(APP, 'r', encoding='utf-8') as f:
    on_disk = f.read()

checks = {
    'safe / fallback':    'except Exception:\n        from flask import redirect' in on_disk,
    'goals monthly_goal': 'monthly_goal=monthly_goal' in on_disk,
    'goals daily_actual': 'daily_actual=daily_actual' in on_disk,
    'goals pace_delta':   'pace_delta=pace_delta' in on_disk,
    'insights top_gainers': 'top_gainers=top_gainers' in on_disk,
    'insights insight_cards': 'insight_cards=insight_cards' in on_disk,
    'profit_matrix pareto_labels': 'pareto_labels=pareto_labels' in on_disk,
    'profit_matrix actions': 'actions=actions' in on_disk,
    'batches SQL fix':    'product_name AS name, quantity, COALESCE(unit' in on_disk,
}

all_ok = True
for label, present in checks.items():
    status = '[OK]  ' if present else '[FAIL]'
    print(f"  {status} {label}")
    if not present:
        all_ok = False

if not all_ok:
    print("\n[FATAL] Some markers didn't land on disk.")
    print(f"Restore with: Copy-Item \"{APP}.bak.{STAMP}\" {APP}")
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════
# Compile check
# ═════════════════════════════════════════════════════════════════════
print("\n[COMPILE] Verifying app.py compiles...")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] Syntax error:")
    print(r.stderr)
    print(f"\nRestore with: Copy-Item \"{APP}.bak.{STAMP}\" {APP}")
    sys.exit(1)
print("  [OK] app.py compiles cleanly")

# ═════════════════════════════════════════════════════════════════════
# Template check — are goals/insights/profit_matrix already enhanced on disk?
# ═════════════════════════════════════════════════════════════════════
print("\n[TEMPLATES] Checking if templates are already enhanced...")
template_checks = {
    'templates/goals.html':         ['daily_actual', 'pace_delta'],
    'templates/insights.html':      ['insight_cards', 'top_gainers'],
    'templates/profit_matrix.html': ['pareto_labels', 'actions'],
}
for path, markers in template_checks.items():
    if not os.path.isfile(path):
        print(f"  [WARN] {path} missing")
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    missing = [m for m in markers if m not in content]
    if missing:
        print(f"  [WARN] {path} not enhanced — missing: {missing}")
        print(f"         (templates were written by the previous enhance_app.py — check git)")
    else:
        print(f"  [OK]  {path} already enhanced")

print("\n" + "=" * 60)
print("Script 1 COMPLETE.")
print("=" * 60)
print("\nNext steps:")
print("  1. Start Flask:  python app.py")
print("  2. Test pages:   /goals  /insights  /profit_matrix  /batches")
print("  3. If all 4 load → commit & push:")
print("       git add app.py")
print("       git diff --cached app.py | Select-String 'top_gainers|pareto_labels' | Measure-Object")
print("       (^ MUST be >= 2)")
print("       git commit -m 'Enhanced goals/insights/profit_matrix + fix batches SQL'")
print("       git push")
print("  4. Render → Manual Deploy → Clear build cache & deploy")
print("  5. Come back for Script 2 (forecast/rfm/health + scanner/voice/credit_scores)")