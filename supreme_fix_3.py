"""
supreme_fix_3.py — final integration: /supreme hub + nav + cross-links + verifier.

Adds:
  - /supreme hub page pulling headline stats from all 6 features
  - One nav entry "Supreme Desk" in Growth section (defensive — skips if already there)
  - /verify_app.py final route checker

Same safe pattern: write to disk, re-read to verify, exit non-zero on failure.
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
print(f"Original: {original_size:,} bytes\n")

# ═════════════════════════════════════════════════════════════════════
# 1. Add /supreme route
# ═════════════════════════════════════════════════════════════════════
print("[1/3] /supreme hub route")

NEW_SUPREME = r'''@app.route('/supreme')
@login_required
def supreme():
    """Supreme desk — one page showing every business intelligence signal."""
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    # Health snapshot
    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS rev, COALESCE(SUM(profit),0) AS pft "
                "FROM sales WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    r = cur.fetchone() or {}
    sales_30 = float(r.get('rev') or 0)
    profit_30 = float(r.get('pft') or 0)
    cur.execute("SELECT COALESCE(SUM(total_amount),0) AS rev FROM sales WHERE user_id=%s "
                "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
                "AND sale_date < to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    sales_prev = float((cur.fetchone() or {}).get('rev') or 0)
    cur.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN quantity <= COALESCE("
                "(SELECT low_stock_threshold FROM settings WHERE user_id=%s),10) THEN 1 ELSE 0 END) AS low "
                "FROM stock WHERE user_id=%s", (uid, uid))
    st = cur.fetchone() or {}
    total_sku = int(st.get('total') or 0); low_sku = int(st.get('low') or 0)
    cur.execute("SELECT COALESCE(SUM(amount),0) AS m FROM expenses WHERE user_id=%s "
                "AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')", (uid,))
    exp_30 = float((cur.fetchone() or {}).get('m') or 0)
    cur.execute("SELECT COALESCE(SUM(opening_balance),0) AS op FROM bank_accounts WHERE user_id=%s", (uid,))
    op = float((cur.fetchone() or {}).get('op') or 0)
    cur.execute("SELECT COALESCE(SUM(CASE WHEN kind='in' THEN amount ELSE -amount END),0) AS mv FROM bank_transactions WHERE user_id=%s", (uid,))
    mv = float((cur.fetchone() or {}).get('mv') or 0)
    cur.execute("SELECT COUNT(*) AS n FROM bank_accounts WHERE user_id=%s", (uid,))
    if int((cur.fetchone() or {}).get('n') or 0) > 0:
        current_cash = op + mv
    else:
        cur.execute("SELECT COALESCE(SUM(CASE WHEN entry_type='in' THEN amount ELSE -amount END),0) AS net FROM cash_books WHERE user_id=%s", (uid,))
        current_cash = float((cur.fetchone() or {}).get('net') or 0)
    cur.execute("SELECT COUNT(DISTINCT customer_id) AS buyers, SUM(CASE WHEN c > 1 THEN 1 ELSE 0 END) AS repeaters "
                "FROM (SELECT customer_id, COUNT(*) AS c FROM sales WHERE user_id=%s "
                "AND customer_id IS NOT NULL GROUP BY customer_id) t", (uid,))
    rb = cur.fetchone() or {}
    buyers = int(rb.get('buyers') or 0); repeaters = int(rb.get('repeaters') or 0)

    trend_pct = ((sales_30 - sales_prev) / sales_prev * 100) if sales_prev > 0 else (100 if sales_30 > 0 else 0)
    trend_score = max(0, min(100, int(50 + trend_pct * 0.5)))
    margin_pct = round((profit_30 / sales_30 * 100) if sales_30 > 0 else 0, 1)
    margin_score = max(0, min(100, int(margin_pct * 2.5)))
    stock_score = int(100 - (low_sku / total_sku) * 100) if total_sku > 0 else 100
    monthly_exp = exp_30 if exp_30 > 0 else 1
    months_covered = round(current_cash / monthly_exp, 1) if current_cash > 0 else 0
    cash_score = max(0, min(100, int(months_covered * 50)))
    retention_score = int((repeaters / buyers * 100) if buyers > 0 else 0)
    health_score = int(trend_score * 0.30 + margin_score * 0.25 + stock_score * 0.15 + cash_score * 0.15 + retention_score * 0.15)
    health_status = 'Excellent' if health_score >= 80 else 'Good' if health_score >= 60 else 'Fair' if health_score >= 40 else 'Needs Attention'

    # Profit matrix counts
    cur.execute("SELECT st.product_name AS name, COALESCE(SUM(s.total_amount),0) AS rev, "
                "COALESCE(SUM(s.profit),0) AS pft FROM sales s LEFT JOIN stock st ON st.id = s.stock_id "
                "WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '90 days','YYYY-MM-DD') "
                "GROUP BY st.product_name", (uid,))
    pm_rows = []
    for row in (cur.fetchall() or []):
        rev = float(row.get('rev') or 0); pft = float(row.get('pft') or 0)
        pm_rows.append({'rev': rev, 'margin': (pft / rev * 100) if rev > 0 else 0})
    avg_rev_pm = sum(x['rev'] for x in pm_rows) / len(pm_rows) if pm_rows else 0
    avg_margin_pm = sum(x['margin'] for x in pm_rows) / len(pm_rows) if pm_rows else 0
    pm_counts = {'star': 0, 'cash_cow': 0, 'rocket': 0, 'dog': 0}
    for x in pm_rows:
        hr = x['rev'] >= avg_rev_pm; hm = x['margin'] >= avg_margin_pm
        key = 'star' if hr and hm else ('cash_cow' if hr else ('rocket' if hm else 'dog'))
        pm_counts[key] += 1

    # RFM counts
    cur.execute("SELECT MAX(s.sale_date) AS lp, COUNT(s.id) AS f, COALESCE(SUM(s.total_amount),0) AS m "
                "FROM customers c LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id "
                "WHERE c.user_id=%s GROUP BY c.id", (uid,))
    today = datetime.today().date()
    rfm_rows = []
    for row in (cur.fetchall() or []):
        lp = (row.get('lp') or '')[:10]
        try:
            days = (today - datetime.strptime(lp, '%Y-%m-%d').date()).days if lp else 9999
        except ValueError:
            days = 9999
        rfm_rows.append({'days': days, 'f': int(row.get('f') or 0), 'm': float(row.get('m') or 0)})
    avg_m = sum(x['m'] for x in rfm_rows) / len(rfm_rows) if rfm_rows else 0
    champions = at_risk_rfm = 0
    for x in rfm_rows:
        R = 5 if x['days'] < 7 else 4 if x['days'] < 30 else 3 if x['days'] < 60 else 2 if x['days'] < 90 else 1
        F = 1 if x['f'] <= 1 else 2 if x['f'] == 2 else 3 if x['f'] <= 4 else 4 if x['f'] <= 9 else 5
        M = 1 if x['m'] < avg_m * 0.5 else 2 if x['m'] < avg_m else 3 if x['m'] < avg_m * 2 else 4 if x['m'] < avg_m * 4 else 5
        if R >= 4 and F >= 4 and M >= 4:
            champions += 1
        elif R <= 2 and F >= 3:
            at_risk_rfm += 1

    # Credit high-risk count
    cur.execute("SELECT COUNT(*) AS c FROM ("
                "SELECT c.id FROM customers c LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id "
                "WHERE c.user_id=%s GROUP BY c.id HAVING COUNT(s.id) > 0) t", (uid,))
    total_scored = int((cur.fetchone() or {}).get('c') or 0)

    # Forecast risk
    cur.execute("SELECT COALESCE(AVG(daily_rev),0) AS a FROM ("
                "SELECT SUM(total_amount) AS daily_rev FROM sales WHERE user_id=%s "
                "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') GROUP BY sale_date) t", (uid,))
    avg_rev_daily = float((cur.fetchone() or {}).get('a') or 0)
    cur.execute("SELECT COALESCE(AVG(daily_exp),0) AS a FROM ("
                "SELECT SUM(amount) AS daily_exp FROM expenses WHERE user_id=%s "
                "AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD') GROUP BY date) t", (uid,))
    avg_exp_daily = float((cur.fetchone() or {}).get('a') or 0)
    net_daily = avg_rev_daily - avg_exp_daily
    projected_30 = round(current_cash + net_daily * 30, 2)
    if projected_30 < 0:
        forecast_risk = 'High'
    elif projected_30 < current_cash * 0.2:
        forecast_risk = 'Moderate'
    else:
        forecast_risk = 'Low'

    # Collections outstanding
    cur.execute("SELECT COALESCE(SUM(s.total_amount),0) AS out FROM sales s "
                "WHERE s.user_id=%s AND COALESCE(s.payment_method,'cash') NOT IN ('cash')", (uid,))
    total_outstanding = float((cur.fetchone() or {}).get('out') or 0)

    # Dead stock capital
    cur.execute("SELECT COALESCE(SUM(quantity * cost_price),0) AS v FROM stock st "
                "WHERE st.user_id=%s AND NOT EXISTS ("
                "SELECT 1 FROM sales s WHERE s.stock_id = st.id "
                "AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD'))", (uid,))
    dead_capital = float((cur.fetchone() or {}).get('v') or 0)

    cur.close(); conn.close()

    tiles = [
        {'title': 'Health Score', 'value': str(health_score), 'suffix': '/100',
         'label': health_status, 'url': url_for('health'),
         'color': 'var(--green)' if health_score >= 80 else 'var(--red-bright)' if health_score >= 60 else '#e0a030' if health_score >= 40 else '#e74c3c'},
        {'title': 'Avg Margin', 'value': f'{margin_pct}', 'suffix': '%',
         'label': 'last 30 days', 'url': url_for('profit_matrix'),
         'color': 'var(--green)' if margin_pct >= 20 else 'var(--red-bright)' if margin_pct >= 10 else '#e0a030'},
        {'title': 'Cash Forecast', 'value': forecast_risk, 'suffix': '',
         'label': f'projected 30d: {_format_money(projected_30)}', 'url': url_for('forecast'),
         'color': '#e74c3c' if forecast_risk == 'High' else '#e0a030' if forecast_risk == 'Moderate' else 'var(--green)'},
        {'title': 'RFM Champions', 'value': str(champions), 'suffix': '',
         'label': f'{at_risk_rfm} at risk', 'url': url_for('rfm'),
         'color': 'var(--green)' if champions > 0 else 'var(--text3)'},
        {'title': 'Outstanding', 'value': _format_money(total_outstanding), 'suffix': '',
         'label': 'from non-cash sales', 'url': url_for('collections'),
         'color': '#e74c3c' if total_outstanding > 0 else 'var(--green)'},
        {'title': 'Dead Capital', 'value': _format_money(dead_capital), 'suffix': '',
         'label': 'tied up in dead stock', 'url': url_for('insights'),
         'color': '#e0a030' if dead_capital > 0 else 'var(--green)'},
        {'title': 'Low Stock', 'value': str(low_sku), 'suffix': '',
         'label': f'of {total_sku} SKU(s)', 'url': url_for('stock'),
         'color': '#e74c3c' if low_sku >= 5 else '#e0a030' if low_sku > 0 else 'var(--green)'},
        {'title': 'Scored Customers', 'value': str(total_scored), 'suffix': '',
         'label': 'with credit history', 'url': url_for('credit_scores'),
         'color': 'var(--green)' if total_scored > 0 else 'var(--text3)'},
    ]

    features = [
        {'title': 'AI Insights', 'icon': 'lightbulb', 'url': url_for('insights'),
         'desc': 'Live growth trends, dead stock, payment mix, and recommendations.'},
        {'title': 'Cash Forecast', 'icon': 'trending-up', 'url': url_for('forecast'),
         'desc': '30-day cash projection from real balance with worst/base/best cases.'},
        {'title': 'Health Score', 'icon': 'activity', 'url': url_for('health'),
         'desc': 'Weighted 5-factor score: trend, margin, stock, cash, retention.'},
        {'title': 'Profit Matrix', 'icon': 'pie-chart', 'url': url_for('profit_matrix'),
         'desc': 'Stars, cash cows, rockets, dogs — quadrant classification + Pareto.'},
        {'title': 'RFM Analysis', 'icon': 'users', 'url': url_for('rfm'),
         'desc': 'Recency, frequency, monetary scoring into 6 customer segments.'},
        {'title': 'Credit Scores', 'icon': 'shield-check', 'url': url_for('credit_scores'),
         'desc': 'Payment-history score per customer, ranked from safest to riskiest.'},
        {'title': 'Barcode Scanner', 'icon': 'scan', 'url': url_for('scanner'),
         'desc': 'Point your camera at any barcode to look up the product in stock.'},
        {'title': 'Voice Entry', 'icon': 'mic', 'url': url_for('voice'),
         'desc': 'Speak a sale ("sold 3 rice for 250") and it gets recorded.'},
    ]

    return render_template('supreme.html', tiles=tiles, features=features,
                           health_score=health_score, health_status=health_status,
                           pm_counts=pm_counts, champions=champions, at_risk=at_risk_rfm,
                           current_cash=current_cash, total_outstanding=total_outstanding)


'''

# Insert before the if __name__ guard (or append at end)
if 'if __name__ == ' in src:
    idx = src.rfind("if __name__ == ")
    src = src[:idx] + NEW_SUPREME + '\n\n' + src[idx:]
else:
    src += '\n\n' + NEW_SUPREME

# Bind /supreme to dashboard module (always on)
BIND_OLD = "_bind_module(\n    'dashboard',\n    'add_income', 'add_expense', 'delete_income', 'delete_expense',"
BIND_NEW = "_bind_module(\n    'dashboard',\n    'supreme',\n    'add_income', 'add_expense', 'delete_income', 'delete_expense',"
if BIND_OLD in src:
    src = src.replace(BIND_OLD, BIND_NEW, 1)
    print("  [OK] route added + bound to dashboard module")
else:
    print("  [OK] route added (module binding skipped — not required)")

# ═════════════════════════════════════════════════════════════════════
# 2. Add nav entry (defensive)
# ═════════════════════════════════════════════════════════════════════
print("\n[2/3] Nav integration")

# Check if already present
nav_start = src.find("NAV_GROUPS = (")
if nav_start == -1:
    print("  [SKIP] NAV_GROUPS not found — add manually:")
    print("    ('Supreme Desk', 'supreme', 'crown', None, ('supreme',)),")
else:
    nav_end = src.find("\n)\n", nav_start)
    nav_block = src[nav_start:nav_end] if nav_end != -1 else src[nav_start:nav_start + 10000]
    if "'supreme'" in nav_block:
        print("  [SKIP] already in nav")
    else:
        growth_marker = "('Growth', ("
        growth_pos = src.find(growth_marker, nav_start)
        if growth_pos != -1:
            insert_pos = growth_pos + len(growth_marker)
            new_line = "\n        ('Supreme Desk', 'supreme', 'crown', None, ('supreme',)),"
            src = src[:insert_pos] + new_line + src[insert_pos:]
            print("  [OK] added to Growth section")
        else:
            print("  [SKIP] Growth section not found — add manually:")
            print("    ('Supreme Desk', 'supreme', 'crown', None, ('supreme',)),")

# ═════════════════════════════════════════════════════════════════════
# WRITE + VERIFY
# ═════════════════════════════════════════════════════════════════════
print("\n[WRITE] Writing app.py to disk...")
with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
print(f"  Wrote {len(src):,} bytes (was {original_size:,})")

print("\n[VERIFY] Re-reading from disk...")
with open(APP, 'r', encoding='utf-8') as f:
    on_disk = f.read()

checks = {
    'supreme route': "def supreme():" in on_disk,
    'supreme endpoint in nav': "'supreme'" in on_disk[on_disk.find("NAV_GROUPS"):on_disk.find("NAV_GROUPS") + 8000] if "NAV_GROUPS" in on_disk else False,
    'route uses tiles': 'return render_template(\'supreme.html\', tiles=tiles' in on_disk,
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
    sys.exit(1)
print("  [OK] app.py compiles cleanly")

# ═════════════════════════════════════════════════════════════════════
# 3. Write supreme.html template
# ═════════════════════════════════════════════════════════════════════
print("\n[3/3] Writing templates/supreme.html")

SUPREME_TPL = '''{% extends "base.html" %}
{% block title %}Supreme Desk{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="crown"></i> Supreme Desk</h1>
    <p>Every business intelligence signal in one place. Click any tile for the full analysis.</p>
  </div>
</div>

<h2>At a glance</h2>
<div class="supreme-grid">
{% for t in tiles %}
<a href="{{ t.url }}" class="supreme-tile">
  <span class="tile-label">{{ t.title }}</span>
  <span class="tile-value" style="color:{{ t.color }};">{{ t.value }}<span style="font-size:1rem;color:var(--text3);">{{ t.suffix }}</span></span>
  <span class="tile-sub">{{ t.label }}</span>
</a>
{% endfor %}
</div>

<h2>Supreme features</h2>
<div class="feature-grid">
{% for f in features %}
<a href="{{ f.url }}" class="feature-card supreme-feature">
  <div class="feature-icon"><i data-lucide="{{ f.icon }}"></i></div>
  <h3>{{ f.title }}</h3>
  <p>{{ f.desc }}</p>
</a>
{% endfor %}
</div>

<style>
.supreme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.9rem;
  margin: 0.5rem 0 2rem;
}
.supreme-tile {
  padding: 1.2rem 1.1rem;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface);
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  transition: transform 0.16s var(--ease-out), border-color 0.16s ease, box-shadow 0.16s ease;
}
.supreme-tile:hover {
  transform: translateY(-3px);
  border-color: var(--red-bright);
  box-shadow: 0 12px 24px rgba(0,0,0,0.2);
}
.tile-label {
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text3);
  font-weight: 700;
}
.tile-value {
  font-size: 1.9rem;
  font-family: var(--mono);
  font-weight: 800;
  line-height: 1.1;
  margin: 0.2rem 0;
}
.tile-sub {
  font-size: 0.82rem;
  color: var(--text2);
}
.supreme-feature {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
}
</style>
{% endblock %}
'''

if os.path.isfile('templates/supreme.html'):
    shutil.copy2('templates/supreme.html', f'templates/supreme.html.bak.{STAMP}')
with open('templates/supreme.html', 'w', encoding='utf-8') as f:
    f.write(SUPREME_TPL)
print(f"  [OK] templates/supreme.html written ({len(SUPREME_TPL):,} bytes)")

# ═════════════════════════════════════════════════════════════════════
# 4. Write /verify_app.py
# ═════════════════════════════════════════════════════════════════════
VERIFY = '''"""
verify_app.py — confirm every Supreme route is registered.

Run from the app folder:
    python verify_app.py

Imports the app and lists every registered route. No DB connection required.
"""
import sys

print("KAZE route verification")
print("=" * 60)

try:
    from app import app
except Exception as e:
    print(f"[FAIL] Could not import app.py: {e}")
    sys.exit(1)

routes = sorted([r.rule for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>'])
print(f"Total routes registered: {len(routes)}\\n")

REQUIRED = [
    '/', '/login', '/signup', '/dashboard',
    '/goals', '/insights', '/profit_matrix', '/forecast', '/rfm', '/health',
    '/credit_scores', '/scanner', '/voice', '/batches',
    '/supreme',
    '/api/lookup-sku', '/voice/sale',
    '/stock', '/sales', '/customers', '/counter', '/reports', '/settings',
    '/tax', '/swot', '/business-plan', '/collections',
    '/banking', '/investments', '/shop', '/market', '/payments',
    '/purchase-orders', '/suppliers', '/recurring', '/budgets',
    '/docs', '/calendar', '/tasks', '/notes', '/reminders',
    '/team', '/activity', '/tutorial', '/shortcuts',
    '/plans', '/notifications', '/healthz',
]

print("Required routes:")
ok = fail = 0
for path in REQUIRED:
    found = path in routes
    print(f"  [{'OK' if found else 'MISSING'}] {path}")
    if found: ok += 1
    else: fail += 1

print("\\n" + "=" * 60)
print(f"{ok} found · {fail} missing")

if fail:
    print("\\nMissing routes may be intentional if you removed features.")
else:
    print("\\nAll required routes registered.")
'''

with open('verify_app.py', 'w', encoding='utf-8') as f:
    f.write(VERIFY)
print("  [OK] verify_app.py written")

print("\n" + "=" * 60)
print("Script 3 COMPLETE.")
print("=" * 60)
print("\nWhat changed:")
print("  • /supreme hub — 8 tiles + 8 feature cards")
print("  • Nav entry 'Supreme Desk' added to Growth section")
print("  • verify_app.py — final route checker")
print("\nNext steps:")
print("  1. python app.py")
print("  2. Visit /supreme and click through every tile")
print("  3. python verify_app.py   (should show all routes present)")
print("  4. git add app.py templates/ verify_app.py")
print("  5. git commit -m 'Supreme desk hub + nav integration + verifier'")
print("  6. git push")
print("  7. Render → Manual Deploy → Clear build cache & deploy")