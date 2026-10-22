"""
supreme_fix_2.py — enhance forecast/rfm/health + make scanner/voice/credit_scores real.

Includes:
  - /forecast enhanced (30-day 3-line cash chart)
  - /rfm enhanced (scored segments)
  - /health enhanced (5-factor weighted)
  - /scanner REAL jsQR barcode detection + /api/lookup-sku endpoint
  - /voice REAL speech recognition + /voice/sale endpoint
  - /credit_scores REAL scores
  - Removes 8 broken stub routes (scanner/batch, voice/intents, etc.)

Run from the folder with app.py:
    python supreme_fix_2.py
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

def save_template(path, content):
    if os.path.isfile(path):
        shutil.copy2(path, f"{path}.bak.{STAMP}")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# ═════════════════════════════════════════════════════════════════════
# 1. /forecast — enhanced
# ═════════════════════════════════════════════════════════════════════
print("[1/9] /forecast — enhanced")
NEW_FORECAST = r'''@app.route('/forecast')
@login_required
def forecast():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COALESCE(AVG(daily_rev),0) AS a FROM ("
                "SELECT SUM(total_amount) AS daily_rev FROM sales WHERE user_id=%s "
                "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') GROUP BY sale_date) t", (uid,))
    avg_daily_revenue = float((cur.fetchone() or {}).get('a') or 0)
    cur.execute("SELECT COALESCE(AVG(daily_exp),0) AS a FROM ("
                "SELECT SUM(amount) AS daily_exp FROM expenses WHERE user_id=%s "
                "AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') GROUP BY date) t", (uid,))
    avg_daily_expense = float((cur.fetchone() or {}).get('a') or 0)
    cur.execute("SELECT COALESCE(SUM(opening_balance),0) AS op FROM bank_accounts WHERE user_id=%s", (uid,))
    op = float((cur.fetchone() or {}).get('op') or 0)
    cur.execute("SELECT COALESCE(SUM(CASE WHEN kind='in' THEN amount ELSE -amount END),0) AS mv FROM bank_transactions WHERE user_id=%s", (uid,))
    mv = float((cur.fetchone() or {}).get('mv') or 0)
    cur.execute("SELECT COUNT(*) AS n FROM bank_accounts WHERE user_id=%s", (uid,))
    bank_count = int((cur.fetchone() or {}).get('n') or 0)
    if bank_count > 0:
        current_cash = op + mv
        cash_source = 'bank accounts'
    else:
        cur.execute("SELECT COALESCE(SUM(CASE WHEN entry_type='in' THEN amount ELSE -amount END),0) AS net FROM cash_books WHERE user_id=%s", (uid,))
        current_cash = float((cur.fetchone() or {}).get('net') or 0)
        cash_source = 'cash book'
    cur.execute("SELECT COALESCE(SUM(amount),0) AS t FROM recurring_items WHERE user_id=%s "
                "AND active=1 AND item_type='expense' "
                "AND next_run_date <= to_char(CURRENT_DATE + INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    upcoming_recurring = float((cur.fetchone() or {}).get('t') or 0)
    cur.execute("SELECT COALESCE(SUM(total_cost),0) AS t FROM purchase_orders WHERE user_id=%s AND status='pending'", (uid,))
    upcoming_pos = float((cur.fetchone() or {}).get('t') or 0)
    cur.close(); conn.close()

    net_daily = avg_daily_revenue - avg_daily_expense
    daily_obligations = (upcoming_recurring + upcoming_pos) / 30.0
    base, worst, best, labels = [], [], [], []
    for d in range(1, 31):
        labels.append(f"Day {d}")
        net_base = net_daily - daily_obligations
        base.append(round(current_cash + net_base * d, 2))
        worst.append(round(current_cash + (net_daily * 0.5 - daily_obligations) * d, 2))
        best.append(round(current_cash + (net_daily * 1.5 - daily_obligations) * d, 2))
    lowest = min(base) if base else 0
    if lowest < 0:
        cash_risk = f'High — projected negative by day {base.index(min(base)) + 1}'
    elif lowest < current_cash * 0.2:
        cash_risk = 'Moderate — buffer below 20% of current cash'
    else:
        cash_risk = 'Low'

    return render_template('forecast.html',
        current_cash=current_cash, cash_source=cash_source,
        avg_daily_revenue=avg_daily_revenue, avg_daily_expense=avg_daily_expense,
        net_daily=net_daily, upcoming_recurring=upcoming_recurring,
        upcoming_pos=upcoming_pos, daily_obligations=daily_obligations,
        base=base, worst=worst, best=best, labels=labels,
        lowest=lowest, cash_risk=cash_risk, avg_daily=avg_daily_revenue)


'''
src, ok = replace_route(src, '/forecast', NEW_FORECAST)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 2. /rfm — enhanced
# ═════════════════════════════════════════════════════════════════════
print("\n[2/9] /rfm — enhanced")
NEW_RFM = r'''@app.route('/rfm')
@login_required
def rfm():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT c.id, c.name, MAX(s.sale_date) AS last_purchase, COUNT(s.id) AS frequency, "
                "COALESCE(SUM(s.total_amount),0) AS monetary FROM customers c "
                "LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id "
                "WHERE c.user_id=%s GROUP BY c.id, c.name", (uid,))
    raw = cur.fetchall() or []
    cur.close(); conn.close()

    today = datetime.today().date()
    customers = []
    for c in raw:
        lp = (c.get('last_purchase') or '')[:10]
        try:
            days = (today - datetime.strptime(lp, '%Y-%m-%d').date()).days if lp else 9999
        except ValueError:
            days = 9999
        freq = int(c.get('frequency') or 0)
        mon = float(c.get('monetary') or 0)
        r = 5 if days < 7 else 4 if days < 30 else 3 if days < 60 else 2 if days < 90 else 1
        f = 1 if freq <= 1 else 2 if freq == 2 else 3 if freq <= 4 else 4 if freq <= 9 else 5
        customers.append({'name': c.get('name') or 'Customer', 'days': days,
                          'frequency': freq, 'monetary': mon, 'R': r, 'F': f})

    avg_m = sum(c['monetary'] for c in customers) / len(customers) if customers else 0
    for c in customers:
        m = c['monetary']
        c['M'] = 1 if m < avg_m * 0.5 else 2 if m < avg_m else 3 if m < avg_m * 2 else 4 if m < avg_m * 4 else 5
        c['rfm'] = f"{c['R']}{c['F']}{c['M']}"
        if c['R'] >= 4 and c['F'] >= 4 and c['M'] >= 4:
            c['segment'] = 'Champion'
        elif c['R'] <= 2 and c['F'] >= 3:
            c['segment'] = 'At Risk'
        elif c['R'] == 1 and c['F'] <= 2:
            c['segment'] = 'Lost'
        elif c['R'] >= 4 and c['F'] <= 2:
            c['segment'] = 'New'
        elif c['R'] >= 3 and c['F'] >= 2:
            c['segment'] = 'Loyal'
        else:
            c['segment'] = 'Needs Attention'
    groups = {}
    for c in customers:
        groups.setdefault(c['segment'], []).append(c)
    segment_order = ['Champion', 'Loyal', 'New', 'At Risk', 'Needs Attention', 'Lost']
    summary = [{'name': s, 'count': len(groups.get(s, []))} for s in segment_order]
    customers.sort(key=lambda x: (x['segment'], -x['monetary']))
    return render_template('rfm.html', customers=customers, groups=groups,
        summary=summary, segment_order=segment_order,
        total_customers=len(customers), avg_monetary=avg_m)


'''
src, ok = replace_route(src, '/rfm', NEW_RFM)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 3. /health — enhanced
# ═════════════════════════════════════════════════════════════════════
print("\n[3/9] /health — enhanced")
NEW_HEALTH = r'''@app.route('/health')
@login_required
def health():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS rev, COALESCE(SUM(profit),0) AS pft "
                "FROM sales WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    r = cur.fetchone() or {}
    sales_30 = float(r.get('rev') or 0); profit_30 = float(r.get('pft') or 0)
    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS rev FROM sales WHERE user_id=%s "
                "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
                "AND sale_date < to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    sales_prev = float((cur.fetchone() or {}).get('rev') or 0)
    cur.execute("SELECT COUNT(*) AS total, "
                "SUM(CASE WHEN quantity <= COALESCE((SELECT low_stock_threshold FROM settings WHERE user_id=%s),10) "
                "THEN 1 ELSE 0 END) AS low FROM stock WHERE user_id=%s", (uid, uid))
    st = cur.fetchone() or {}
    total_sku = int(st.get('total') or 0); low_sku = int(st.get('low') or 0)
    cur.execute("SELECT COALESCE(SUM(amount),0) AS m FROM expenses "
                "WHERE user_id=%s AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    exp_30 = float((cur.fetchone() or {}).get('m') or 0)
    cur.execute("SELECT COALESCE(SUM(opening_balance),0) AS op FROM bank_accounts WHERE user_id=%s", (uid,))
    op = float((cur.fetchone() or {}).get('op') or 0)
    cur.execute("SELECT COALESCE(SUM(CASE WHEN kind='in' THEN amount ELSE -amount END),0) AS mv FROM bank_transactions WHERE user_id=%s", (uid,))
    mv = float((cur.fetchone() or {}).get('mv') or 0)
    cur.execute("SELECT COUNT(*) AS n FROM bank_accounts WHERE user_id=%s", (uid,))
    if int((cur.fetchone() or {}).get('n') or 0) > 0:
        cash = op + mv
    else:
        cur.execute("SELECT COALESCE(SUM(CASE WHEN entry_type='in' THEN amount ELSE -amount END),0) AS net FROM cash_books WHERE user_id=%s", (uid,))
        cash = float((cur.fetchone() or {}).get('net') or 0)
    cur.execute("SELECT COUNT(DISTINCT customer_id) AS buyers, SUM(CASE WHEN c > 1 THEN 1 ELSE 0 END) AS repeaters "
                "FROM (SELECT customer_id, COUNT(*) AS c FROM sales WHERE user_id=%s "
                "AND customer_id IS NOT NULL GROUP BY customer_id) t", (uid,))
    rb = cur.fetchone() or {}
    buyers = int(rb.get('buyers') or 0); repeaters = int(rb.get('repeaters') or 0)
    cur.close(); conn.close()

    trend_pct = ((sales_30 - sales_prev) / sales_prev * 100) if sales_prev > 0 else (100 if sales_30 > 0 else 0)
    trend_score = max(0, min(100, int(50 + trend_pct * 0.5)))
    margin_pct = round((profit_30 / sales_30 * 100) if sales_30 > 0 else 0, 1)
    margin_score = max(0, min(100, int(margin_pct * 2.5)))
    stock_score = int(100 - (low_sku / total_sku) * 100) if total_sku > 0 else 100
    monthly_exp = exp_30 if exp_30 > 0 else 1
    months_covered = round(cash / monthly_exp, 1) if cash > 0 else 0
    cash_score = max(0, min(100, int(months_covered * 50)))
    retention_score = int((repeaters / buyers * 100) if buyers > 0 else 0)
    final = int(trend_score * 0.30 + margin_score * 0.25 + stock_score * 0.15 + cash_score * 0.15 + retention_score * 0.15)
    final = max(0, min(100, final))
    status = 'Excellent' if final >= 80 else 'Good' if final >= 60 else 'Fair' if final >= 40 else 'Needs Attention'
    components = [
        {'name': 'Sales trend', 'score': trend_score, 'weight': 30, 'detail': f'30d vs prior: {int(trend_pct):+d}%'},
        {'name': 'Margin', 'score': margin_score, 'weight': 25, 'detail': f'{margin_pct}% avg margin'},
        {'name': 'Stock health', 'score': stock_score, 'weight': 15, 'detail': f'{low_sku}/{total_sku} low-stock'},
        {'name': 'Cash buffer', 'score': cash_score, 'weight': 15, 'detail': f'{months_covered} months covered'},
        {'name': 'Retention', 'score': retention_score, 'weight': 15, 'detail': f'{repeaters}/{buyers} repeat'},
    ]
    return render_template('health.html', score=final, status=status, components=components,
        sales=sales_30, low=low_sku, trend_pct=round(trend_pct, 1),
        margin_pct=margin_pct, months_covered=months_covered,
        buyers=buyers, repeaters=repeaters)


'''
src, ok = replace_route(src, '/health', NEW_HEALTH)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 4. /scanner — real
# ═════════════════════════════════════════════════════════════════════
print("\n[4/9] /scanner — real jsQR")
NEW_SCANNER = r'''@app.route('/scanner')
@login_required
def scanner():
    return render_template('scanner.html')


'''
src, ok = replace_route(src, '/scanner', NEW_SCANNER)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 5. /voice — real
# ═════════════════════════════════════════════════════════════════════
print("\n[5/9] /voice — real speech recognition")
NEW_VOICE = r'''@app.route('/voice')
@login_required
def voice():
    return render_template('voice.html')


'''
src, ok = replace_route(src, '/voice', NEW_VOICE)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 6. /credit_scores — real
# ═════════════════════════════════════════════════════════════════════
print("\n[6/9] /credit_scores — real scores")
NEW_CS = r'''@app.route('/credit_scores')
@login_required
def credit_scores():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT c.id, c.name, COUNT(s.id) AS orders, COALESCE(SUM(s.total_amount),0) AS total, "
                "MAX(s.sale_date) AS last_sale, "
                "SUM(CASE WHEN COALESCE(s.payment_method,'cash') != 'cash' THEN 1 ELSE 0 END) AS credit_orders, "
                "SUM(CASE WHEN COALESCE(s.payment_method,'cash') = 'cash' THEN 1 ELSE 0 END) AS cash_orders "
                "FROM customers c LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id "
                "WHERE c.user_id=%s GROUP BY c.id, c.name HAVING COUNT(s.id) > 0", (uid,))
    rows = cur.fetchall() or []
    cur.close(); conn.close()
    today = datetime.today().date()
    scores = []
    for r in rows:
        last = (r.get('last_sale') or '')[:10]
        try:
            days = (today - datetime.strptime(last, '%Y-%m-%d').date()).days if last else 999
        except ValueError:
            days = 999
        orders = int(r.get('orders') or 0)
        total = float(r.get('total') or 0)
        cash_orders = int(r.get('cash_orders') or 0)
        credit_orders = int(r.get('credit_orders') or 0)
        recency = 40 if days < 7 else 30 if days < 30 else 20 if days < 60 else 10 if days < 90 else 5
        frequency = min(30, orders * 3)
        credit_ratio = (cash_orders / orders) if orders else 0
        payment = int(credit_ratio * 30)
        score = recency + frequency + payment
        risk = 'Low' if score >= 70 else 'Medium' if score >= 40 else 'High'
        scores.append({'id': r.get('id'), 'name': r.get('name'), 'orders': orders,
                       'total': total, 'days_since': days,
                       'score': score, 'risk': risk})
    scores.sort(key=lambda x: -x['score'])
    return render_template('credit_scores.html', scores=scores)


'''
src, ok = replace_route(src, '/credit_scores', NEW_CS)
print(f"  {'[OK]' if ok else '[SKIP]'}")

# ═════════════════════════════════════════════════════════════════════
# 7. Append /api/lookup-sku + /voice/sale (new routes)
# ═════════════════════════════════════════════════════════════════════
print("\n[7/9] Append /api/lookup-sku + /voice/sale")

NEW_ROUTES = '''# ═════════════════════════════════════════════════════════════════════
# API routes added by supreme_fix_2.py
# ═════════════════════════════════════════════════════════════════════

@app.route('/api/lookup-sku')
@login_required
def api_lookup_sku():
    """JSON lookup used by /scanner. Searches stock by SKU or product_name."""
    q = (request.args.get('q') or '').strip()
    if not q:
        return {'found': False, 'reason': 'empty'}
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "SELECT id, product_name, quantity, selling_price FROM stock "
        "WHERE user_id=%s AND (sku=%s OR product_name ILIKE %s) LIMIT 1",
        (current_user.id, q, '%' + q + '%'))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return {'found': True, 'id': row['id'], 'product_name': row['product_name'],
                'quantity': float(row['quantity']), 'selling_price': float(row['selling_price'])}
    return {'found': False, 'reason': 'not_in_stock'}


@app.route('/voice/sale', methods=['GET', 'POST'])
@login_required
def voice_sale():
    """Record a sale from a parsed voice command."""
    product = (request.values.get('product') or '').strip()
    try:
        qty = float(request.values.get('qty') or 1)
    except (TypeError, ValueError):
        qty = 1
    if qty <= 0:
        flash('Quantity must be more than zero.', 'danger')
        return redirect(url_for('voice'))
    if not product:
        flash('Could not find a product in your speech. Try again.', 'danger')
        return redirect(url_for('voice'))
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "SELECT * FROM stock WHERE user_id=%s AND product_name ILIKE %s ORDER BY id LIMIT 1",
        (current_user.id, '%' + product.split()[0] + '%'))
    item = cur.fetchone()
    if not item:
        flash(f'No product matching "{product}" found. Add it in Stock first.', 'danger')
        cur.close(); conn.close()
        return redirect(url_for('voice'))
    if item['quantity'] < qty:
        flash(f'Not enough stock. Only {item["quantity"]} of {item["product_name"]} left.', 'danger')
        cur.close(); conn.close()
        return redirect(url_for('voice'))
    selling_price = float(item['selling_price'])
    cost_price = float(item['cost_price'])
    total = selling_price * qty
    profit = total - cost_price * qty
    today = datetime.today().strftime('%Y-%m-%d')
    cur.execute(
        "INSERT INTO sales (user_id, stock_id, quantity_sold, selling_price_at_time, "
        "total_amount, profit, sale_date, customer_name, customer_email, customer_id, "
        "discount, sale_notes, payment_method) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (current_user.id, item['id'], qty, selling_price, total, profit, today,
         'Voice entry', '', None, 0, 'via voice', 'cash'))
    cur.execute('UPDATE stock SET quantity = quantity - %s WHERE id = %s', (qty, item['id']))
    conn.commit()
    cur.close(); conn.close()
    log_activity(current_user.id, current_user.username, 'Voice sale',
                 f'{item["product_name"]} x{qty} {_format_money(total)}')
    flash(f'Voice sale recorded: {item["product_name"]} x{qty} — {_format_money(total)}', 'success')
    return redirect(url_for('sales'))


'''

if 'if __name__ == ' in src:
    idx = src.rfind("if __name__ == ")
    src = src[:idx] + NEW_ROUTES + '\n' + src[idx:]
else:
    src += '\n' + NEW_ROUTES
print("  [OK] appended /api/lookup-sku, /voice/sale")

# ═════════════════════════════════════════════════════════════════════
# 8. Remove broken stub sub-routes
# ═════════════════════════════════════════════════════════════════════
print("\n[8/9] Remove broken stub sub-routes")

STUB_ROUTES = ['/scanner/batch', '/scanner/history',
               '/voice/intents', '/voice/history',
               '/credit/limits', '/credit/trend',
               '/batches/fefo', '/batches/risk']
removed = 0
for route in STUB_ROUTES:
    pat = re.compile(
        r"@app\.route\('" + re.escape(route) + r"'[^)]*\)\n"
        r"(?:@[^\n]+\n)*"
        r"def \w+\([^)]*\):\n"
        r".*?"
        r"(?=\n@app\.|\n# ===|\n# ───|\n\n\n@app\.|\Z)",
        re.DOTALL)
    m = pat.search(src)
    if m:
        src = src[:m.start()] + src[m.end():]
        removed += 1
        print(f"  [DEL] {route}")
if removed == 0:
    print("  [SKIP] no stubs found")

src = re.sub(r'\n{4,}', '\n\n\n', src)

# ═════════════════════════════════════════════════════════════════════
# CRITICAL: Write to disk + verify
# ═════════════════════════════════════════════════════════════════════
print("\n[WRITE] Writing app.py to disk...")
with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
print(f"  Wrote {len(src):,} bytes (was {original_size:,})")

print("\n[VERIFY] Re-reading from disk...")
with open(APP, 'r', encoding='utf-8') as f:
    on_disk = f.read()

checks = {
    'forecast cash_risk': 'cash_risk=cash_risk' in on_disk,
    'forecast base/worst/best': 'base=base, worst=worst, best=best' in on_disk,
    'rfm segment_order': 'segment_order=segment_order' in on_disk,
    'health components': 'components=components' in on_disk,
    'scanner real route': "return render_template('scanner.html')" in on_disk,
    'voice real route': "return render_template('voice.html')" in on_disk,
    'credit_scores real': 'scores=scores' in on_disk,
    'api lookup endpoint': "def api_lookup_sku():" in on_disk,
    'voice sale endpoint': "def voice_sale():" in on_disk,
}
all_ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present: all_ok = False
if not all_ok:
    print(f"\n[FATAL] Restore: Copy-Item \"{APP}.bak.{STAMP}\" {APP}")
    sys.exit(1)

print("\n[COMPILE] Verifying compile...")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"Restore: Copy-Item \"{APP}.bak.{STAMP}\" {APP}")
    sys.exit(1)
print("  [OK] app.py compiles cleanly")

# ═════════════════════════════════════════════════════════════════════
# 9. Write templates
# ═════════════════════════════════════════════════════════════════════
print("\n[9/9] Writing templates...")

save_template('templates/forecast.html', '''{% extends "base.html" %}
{% block title %}Cash Flow Forecast{% endblock %}
{% block charts_js %}<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="trending-up"></i> Cash Flow Forecast</h1>
<p>30-day projection from your current {{ cash_source }} balance, average daily flows, and upcoming obligations.</p></div></div>
<div class="stat-grid">
  <div class="stat-chip"><span>Current cash</span><strong>{{ money(current_cash) }}</strong></div>
  <div class="stat-chip"><span>Avg daily revenue</span><strong>{{ money(avg_daily_revenue) }}</strong></div>
  <div class="stat-chip"><span>Avg daily expense</span><strong>{{ money(avg_daily_expense) }}</strong></div>
  <div class="stat-chip"><span>Net daily</span><strong>{{ money(net_daily) }}</strong></div>
  <div class="stat-chip"><span>Upcoming recurring</span><strong>{{ money(upcoming_recurring) }}</strong></div>
  <div class="stat-chip"><span>Pending POs</span><strong>{{ money(upcoming_pos) }}</strong></div>
</div>
<div class="widget"><h3 style="margin-top:0;">Risk assessment</h3>
<p style="margin:0;"><strong>Lowest projected cash:</strong> {{ money(lowest) }} · <strong>Risk:</strong> {{ cash_risk }}</p></div>
<div class="chart-container"><canvas id="forecastChart" height="150"></canvas></div>
<script>
new Chart(document.getElementById('forecastChart'), {
  type: 'line',
  data: { labels: {{ labels|tojson }}, datasets: [
    {label: 'Best case', data: {{ best|tojson }}, borderColor: '#2ecc71', tension: 0.25, fill: false},
    {label: 'Base case', data: {{ base|tojson }}, borderColor: '#3498db', tension: 0.25, fill: false, borderWidth: 3},
    {label: 'Worst case', data: {{ worst|tojson }}, borderColor: '#e74c3c', tension: 0.25, fill: false}
  ]},
  options: {responsive: true, plugins: {title: {display: true, text: 'Projected cash · next 30 days'},
    tooltip: {callbacks: {label: c => c.dataset.label + ': ' + window.kazeMoney(c.raw)}}},
    scales: {y: {ticks: {callback: v => window.kazeMoney(v)}}}}
});
</script>
<h2>Daily detail</h2>
<div class="table-wrapper"><table><thead><tr><th>Day</th><th>Worst</th><th>Base</th><th>Best</th></tr></thead>
<tbody>{% for i in range(30) %}<tr><td>{{ labels[i] }}</td><td>{{ money(worst[i]) }}</td><td>{{ money(base[i]) }}</td><td>{{ money(best[i]) }}</td></tr>{% endfor %}</tbody>
</table></div>
{% endblock %}
''')

save_template('templates/rfm.html', '''{% extends "base.html" %}
{% block title %}RFM Analysis{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="users"></i> RFM Analysis</h1>
<p>Recency, Frequency, Monetary value — scored 1–5 per customer.</p></div></div>
<div class="stat-grid">
  <div class="stat-chip"><span>Customers</span><strong>{{ total_customers }}</strong></div>
  <div class="stat-chip"><span>Avg lifetime spend</span><strong>{{ money(avg_monetary) }}</strong></div>
</div>
<h2>Segments</h2>
<div class="rfm-grid">
{% for s in summary %}
<div class="rfm-card rfm-{{ s.name|lower|replace(' ','-') }}">
<strong>{{ s.name }}</strong><div class="rfm-count">{{ s.count }}</div>
<small>customer{{ '' if s.count == 1 else 's' }}</small></div>
{% endfor %}
</div>
<h2>All customers</h2>
<div class="table-wrapper"><table>
<thead><tr><th>Customer</th><th>Segment</th><th>R</th><th>F</th><th>M</th><th>RFM</th><th>Days since</th><th>Orders</th><th>Spend</th></tr></thead>
<tbody>{% for c in customers %}
<tr><td>{{ c.name }}</td>
<td><span class="status-pill rfm-pill-{{ c.segment|lower|replace(' ','-') }}">{{ c.segment }}</span></td>
<td>{{ c.R }}</td><td>{{ c.F }}</td><td>{{ c.M }}</td>
<td><code>{{ c.rfm }}</code></td>
<td>{% if c.days > 9000 %}never{% else %}{{ c.days }}d{% endif %}</td>
<td>{{ c.frequency }}</td><td>{{ money(c.monetary) }}</td></tr>
{% else %}<tr><td colspan="9">No customers yet.</td></tr>{% endfor %}
</tbody></table></div>
<style>
.rfm-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin: 0 0 1.5rem;}
.rfm-card {padding: 1rem; border-radius: 12px; border: 1px solid var(--border); background: var(--surface); border-left: 4px solid var(--text3);}
.rfm-card strong {font-size: 0.9rem;}
.rfm-count {font-size: 2rem; font-weight: 800; font-family: var(--mono); margin: 0.3rem 0;}
.rfm-card small {color: var(--text3); font-size: 0.78rem;}
.rfm-champion {border-left-color: var(--green);}
.rfm-loyal {border-left-color: #3498db;}
.rfm-new {border-left-color: #9b59b6;}
.rfm-at-risk {border-left-color: #e0a030;}
.rfm-needs-attention {border-left-color: #e67e22;}
.rfm-lost {border-left-color: #e74c3c;}
.rfm-pill-champion {background: var(--green-dim); color: var(--green);}
.rfm-pill-loyal {background: rgba(52,152,219,0.15); color: #3498db;}
.rfm-pill-new {background: rgba(155,89,182,0.15); color: #9b59b6;}
.rfm-pill-at-risk {background: rgba(224,160,48,0.15); color: #e0a030;}
.rfm-pill-needs-attention {background: rgba(230,126,34,0.15); color: #e67e22;}
.rfm-pill-lost {background: rgba(231,76,60,0.15); color: #e74c3c;}
</style>
{% endblock %}
''')

save_template('templates/health.html', '''{% extends "base.html" %}
{% block title %}Business Health{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="activity"></i> Business Health Score</h1>
<p>Weighted score from five independent factors.</p></div></div>
<div class="widget" style="text-align:center;padding:2rem;">
<div style="font-size:5rem;font-weight:800;font-family:var(--mono);color:{% if score >= 80 %}var(--green){% elif score >= 60 %}var(--red-bright){% elif score >= 40 %}#e0a030{% else %}#e74c3c{% endif %};line-height:1;">{{ score }}</div>
<h2 style="margin:0.4rem 0 0;border:none;">{{ status }}</h2>
<p style="margin:0.5rem 0 0;color:var(--text3);">out of 100</p></div>
<div class="stat-grid">
<div class="stat-chip"><span>30-day sales</span><strong>{{ money(sales) }}</strong></div>
<div class="stat-chip"><span>Sales trend</span><strong>{{ '%+d'|format(trend_pct|int) }}%</strong></div>
<div class="stat-chip"><span>Avg margin</span><strong>{{ margin_pct }}%</strong></div>
<div class="stat-chip"><span>Low stock</span><strong>{{ low }}</strong></div>
<div class="stat-chip"><span>Cash buffer</span><strong>{{ months_covered }} mo</strong></div>
<div class="stat-chip"><span>Repeat buyers</span><strong>{{ repeaters }}/{{ buyers }}</strong></div>
</div>
<h2>Score breakdown</h2>
<div class="health-grid">
{% for c in components %}
<div class="health-card">
<div class="health-head"><strong>{{ c.name }}</strong><span>{{ c.score }}/100</span></div>
<div class="health-bar"><div style="width:{{ c.score }}%;background:{% if c.score >= 80 %}var(--green){% elif c.score >= 60 %}var(--red-bright){% elif c.score >= 40 %}#e0a030{% else %}#e74c3c{% endif %};"></div></div>
<p>{{ c.detail }}</p>
<small style="color:var(--text3);">Weight: {{ c.weight }}%</small></div>
{% endfor %}
</div>
<style>
.health-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.85rem;}
.health-card {padding: 1rem 1.1rem; border-radius: 12px; border: 1px solid var(--border); background: var(--surface);}
.health-head {display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem;}
.health-head span {font-family: var(--mono); font-weight: 700;}
.health-bar {height: 8px; background: var(--surface2); border-radius: 4px; overflow: hidden;}
.health-bar div {height: 100%;}
.health-card p {margin: 0.55rem 0 0.2rem; font-size: 0.86rem; color: var(--text2);}
</style>
{% endblock %}
''')

save_template('templates/scanner.html', '''{% extends "base.html" %}
{% block title %}Barcode Scanner{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="scan"></i> Barcode Scanner</h1>
<p>Point your camera at a barcode to look up the product in your stock.</p></div></div>
<div class="widget">
<div style="position:relative;background:#000;border-radius:12px;overflow:hidden;max-width:640px;margin:0 auto;">
<video id="preview" style="width:100%;display:block;" playsinline></video>
<canvas id="scanCanvas" style="display:none;"></canvas>
</div>
<div style="text-align:center;margin-top:1rem;display:flex;gap:0.6rem;justify-content:center;flex-wrap:wrap;">
<button type="button" class="btn-primary" id="startScan">Start camera</button>
<button type="button" class="btn-secondary" id="stopScan" style="display:none;">Stop</button>
</div>
<div id="result" style="margin-top:1rem;padding:1rem;background:var(--surface2);border-radius:10px;display:none;">
<strong>Detected:</strong> <code id="barcodeValue"></code>
<div id="productMatch" style="margin-top:0.5rem;"></div>
</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
<script>
(function(){
  const video = document.getElementById('preview');
  const canvas = document.getElementById('scanCanvas');
  const ctx = canvas.getContext('2d', {willReadFrequently: true});
  const startBtn = document.getElementById('startScan');
  const stopBtn = document.getElementById('stopScan');
  const result = document.getElementById('result');
  const barcodeEl = document.getElementById('barcodeValue');
  const matchEl = document.getElementById('productMatch');
  let stream = null, rafId = null, scanning = false;
  async function start(){
    try {
      stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'environment'}});
      video.srcObject = stream;
      await video.play();
      startBtn.style.display = 'none';
      stopBtn.style.display = '';
      scanning = true; scan();
    } catch(e) { alert('Camera failed: ' + e.message); }
  }
  function stop(){
    scanning = false;
    if(rafId) cancelAnimationFrame(rafId);
    if(stream) stream.getTracks().forEach(t => t.stop());
    video.srcObject = null;
    startBtn.style.display = ''; stopBtn.style.display = 'none';
  }
  function scan(){
    if(!scanning || video.readyState !== video.HAVE_ENOUGH_DATA){ rafId = requestAnimationFrame(scan); return; }
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(img.data, img.width, img.height, {inversionAttempts: 'dontInvert'});
    if(code && code.data){ onDetected(code.data); return; }
    rafId = requestAnimationFrame(scan);
  }
  function onDetected(data){
    stop(); result.style.display = 'block'; barcodeEl.textContent = data;
    matchEl.innerHTML = '<em style="color:var(--text3);">Looking up...</em>';
    fetch('/api/lookup-sku?q=' + encodeURIComponent(data))
      .then(r => r.json())
      .then(d => {
        if(d.found) {
          matchEl.innerHTML = '<strong style="color:var(--green);">' + d.product_name + '</strong> — ' +
            d.quantity + ' in stock at ' + window.kazeMoney(d.selling_price) +
            ' <a href="/stock/edit/' + d.id + '" style="margin-left:0.5rem;">Edit</a>';
        } else {
          matchEl.innerHTML = '<em style="color:var(--text3);">No product with this SKU. <a href="/stock">Add one</a>.</em>';
        }
      }).catch(() => { matchEl.innerHTML = '<em style="color:#e74c3c;">Lookup failed.</em>'; });
  }
  startBtn.addEventListener('click', start);
  stopBtn.addEventListener('click', stop);
  window.addEventListener('beforeunload', stop);
})();
</script>
{% endblock %}
''')

save_template('templates/voice.html', '''{% extends "base.html" %}
{% block title %}Voice Entry{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="mic"></i> Voice Entry</h1>
<p>Say: "Sold 3 rice for 250" or "5 sugar at 30 each".</p></div></div>
<div class="widget">
<div style="display:flex;gap:1rem;align-items:center;flex-wrap:wrap;">
<button type="button" class="btn-primary" id="listenBtn"><i data-lucide="mic"></i> Start listening</button>
<button type="button" class="btn-secondary" id="stopBtn" style="display:none;">Stop</button>
<span id="status" style="color:var(--text3);font-size:0.88rem;">Ready</span>
</div>
<div id="transcript" style="margin-top:1rem;padding:1rem;background:var(--surface2);border-radius:10px;min-height:60px;font-family:var(--mono);">
<em style="color:var(--text3);">Waiting for speech...</em></div>
<div id="parsed" style="margin-top:1rem;display:none;">
<h3 style="margin-top:0;">Parsed sale</h3>
<div id="parsedDetails"></div>
<button type="button" class="btn-primary" id="confirmSale" style="margin-top:0.75rem;">Confirm and record sale</button>
</div>
</div>
<script>
(function(){
  const listenBtn = document.getElementById('listenBtn');
  const stopBtn = document.getElementById('stopBtn');
  const status = document.getElementById('status');
  const transcript = document.getElementById('transcript');
  const parsed = document.getElementById('parsed');
  const parsedDetails = document.getElementById('parsedDetails');
  const confirmSale = document.getElementById('confirmSale');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null, lastParsed = null;
  if(!SpeechRecognition){
    transcript.innerHTML = '<em style="color:#e74c3c;">Speech not supported. Try Chrome, Edge, or Safari.</em>';
    listenBtn.disabled = true; return;
  }
  function parseSpeech(text){
    const lower = text.toLowerCase();
    const qtyMatch = lower.match(/(\\d+(?:\\.\\d+)?)\\s*(?:units?|pcs?|pieces?|bags?|kg|items?)?/);
    const priceMatch = lower.match(/(?:for|at)\\s+(\\d+(?:\\.\\d+)?)/);
    const eachMatch = lower.match(/(\\d+(?:\\.\\d+)?)\\s*(?:each|per unit)/);
    const qty = qtyMatch ? parseFloat(qtyMatch[1]) : 1;
    let total = null, unitPrice = null;
    if(priceMatch) total = parseFloat(priceMatch[1]);
    if(eachMatch) unitPrice = parseFloat(eachMatch[1]);
    const filler = /(\\d+(?:\\.\\d+)?|sold|record|sale|of|for|at|each|units?|pcs?|pieces?|bags?|kg|items?|the|a|an|and|please|i|want|to)/g;
    const product = lower.replace(filler, ' ').replace(/\\s+/g, ' ').trim();
    return {qty, total, unitPrice, product, raw: text};
  }
  function startListening(){
    rec = new SpeechRecognition();
    rec.continuous = false; rec.interimResults = false; rec.lang = 'en-US';
    rec.onstart = () => { status.textContent = 'Listening...'; listenBtn.style.display = 'none'; stopBtn.style.display = ''; };
    rec.onresult = (e) => {
      const text = e.results[0][0].transcript;
      transcript.innerHTML = '<strong>Heard:</strong> "' + text + '"';
      lastParsed = parseSpeech(text);
      parsed.style.display = 'block';
      parsedDetails.innerHTML = '<p><strong>Product:</strong> ' + (lastParsed.product || '(empty)') + '</p>' +
        '<p><strong>Qty:</strong> ' + lastParsed.qty + '</p>' +
        (lastParsed.total !== null ? '<p><strong>Total:</strong> ' + window.kazeMoney(lastParsed.total) + '</p>' : '') +
        (lastParsed.unitPrice !== null ? '<p><strong>Unit:</strong> ' + window.kazeMoney(lastParsed.unitPrice) + '</p>' : '');
    };
    rec.onerror = (e) => { status.textContent = 'Error: ' + e.error; };
    rec.onend = () => { listenBtn.style.display = ''; stopBtn.style.display = 'none'; status.textContent = 'Stopped'; };
    rec.start();
  }
  function stopListening(){ if(rec) rec.stop(); }
  confirmSale.addEventListener('click', () => {
    if(!lastParsed) return;
    const params = new URLSearchParams({product: lastParsed.product, qty: lastParsed.qty});
    window.location = '/voice/sale?' + params.toString();
  });
  listenBtn.addEventListener('click', startListening);
  stopBtn.addEventListener('click', stopListening);
})();
</script>
{% endblock %}
''')

save_template('templates/credit_scores.html', '''{% extends "base.html" %}
{% block title %}Credit Scores{% endblock %}
{% block content %}
<div class="page-header"><div><h1><i data-lucide="shield-check"></i> Customer Credit Scores</h1>
<p>Recency + frequency + payment consistency. Higher is better.</p></div></div>
<div class="card">
<table class="data-table">
<thead><tr><th>Customer</th><th>Score</th><th>Risk</th><th>Days since</th><th>Orders</th><th>Total</th></tr></thead>
<tbody>{% for s in scores %}
<tr><td>{{ s.name }}</td>
<td><strong>{{ s.score }}/100</strong></td>
<td><span class="status-pill" style="background:{% if s.risk == 'Low' %}var(--green-dim){% elif s.risk == 'Medium' %}rgba(224,160,48,0.15){% else %}rgba(231,76,60,0.15){% endif %};color:{% if s.risk == 'Low' %}var(--green){% elif s.risk == 'Medium' %}#e0a030{% else %}#e74c3c{% endif %};">{{ s.risk }}</span></td>
<td>{{ s.days_since }}d</td><td>{{ s.orders }}</td><td>{{ money(s.total) }}</td></tr>
{% else %}<tr><td colspan="6">No scored customers yet — need at least one sale per customer.</td></tr>{% endfor %}
</tbody></table></div>
{% endblock %}
''')

print("  [OK] all 6 templates written")

# ═════════════════════════════════════════════════════════════════════
# Final summary
# ═════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Script 2 COMPLETE.")
print("=" * 60)
print("\nWhat changed:")
print("  • /forecast  — enhanced (30-day 3-line cash projection)")
print("  • /rfm       — enhanced (R/F/M scoring + 6 segments)")
print("  • /health    — enhanced (5-factor weighted score)")
print("  • /scanner   — REAL jsQR barcode scanning + /api/lookup-sku")
print("  • /voice     — REAL speech recognition + /voice/sale")
print("  • /credit_scores — REAL recency/frequency scores")
print("  • Removed 8 broken stub sub-routes")
print("\nNext steps:")
print("  1. python app.py        (test locally)")
print("  2. Test /forecast /rfm /health /scanner /voice /credit_scores")
print("  3. git add app.py templates/")
print("  4. git diff --cached | Select-String 'api_lookup_sku|voice_sale' | Measure-Object  (must be >= 2)")
print("  5. git commit -m 'Enhanced forecast/rfm/health + real scanner/voice/credit_scores'")
print("  6. git push")
print("  7. Render → Manual Deploy → Clear build cache & deploy")