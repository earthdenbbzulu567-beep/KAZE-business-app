"""
apply_fixes_14_health.py — replace /health stub with a real 5-factor score.

Before: score = 50 + (sales/1000) - (low * 5)   ← made-up formula
After:  weighted average of 5 real components:
        - Sales trend (30d vs prior 30d)
        - Margin % (last 30 days)
        - Stock health (low-stock ratio)
        - Cash buffer (months of expenses covered)
        - Customer retention (repeat buyer ratio)
"""

import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'
TPL = os.path.join('templates', 'health.html')

if not os.path.isfile(APP):
    print("ERROR: app.py not found."); sys.exit(1)

shutil.copy2(APP, f"{APP}.bak.{STAMP}"); print(f"Backup: {APP}.bak.{STAMP}")
if os.path.isfile(TPL):
    shutil.copy2(TPL, f"{TPL}.bak.{STAMP}"); print(f"Backup: {TPL}.bak.{STAMP}")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

NEW_ROUTE = r'''@app.route('/health')
@login_required
def health():
    uid = current_user.id
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS rev, COALESCE(SUM(profit),0) AS pft "
        "FROM sales WHERE user_id=%s "
        "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')",
        (uid,))
    r = cur.fetchone() or {}
    sales_30 = float(r.get('rev') or 0)
    profit_30 = float(r.get('pft') or 0)

    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS rev "
        "FROM sales WHERE user_id=%s "
        "AND sale_date >= to_char(CURRENT_DATE - INTERVAL '60 days','YYYY-MM-DD') "
        "AND sale_date < to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')",
        (uid,))
    sales_prev_30 = float((cur.fetchone() or {}).get('rev') or 0)

    cur.execute(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN quantity <= COALESCE("
        "(SELECT low_stock_threshold FROM settings WHERE user_id=%s),10) THEN 1 ELSE 0 END) AS low "
        "FROM stock WHERE user_id=%s",
        (uid, uid))
    st = cur.fetchone() or {}
    total_sku = int(st.get('total') or 0)
    low_sku = int(st.get('low') or 0)

    cur.execute(
        "SELECT COALESCE(SUM(amount),0) AS m FROM expenses "
        "WHERE user_id=%s AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')",
        (uid,))
    exp_30 = float((cur.fetchone() or {}).get('m') or 0)

    cur.execute("SELECT COALESCE(SUM(opening_balance),0) AS op FROM bank_accounts WHERE user_id=%s", (uid,))
    op = float((cur.fetchone() or {}).get('op') or 0)
    cur.execute(
        "SELECT COALESCE(SUM(CASE WHEN kind='in' THEN amount ELSE -amount END),0) AS mv "
        "FROM bank_transactions WHERE user_id=%s", (uid,))
    mv = float((cur.fetchone() or {}).get('mv') or 0)
    cur.execute("SELECT COUNT(*) AS n FROM bank_accounts WHERE user_id=%s", (uid,))
    if int((cur.fetchone() or {}).get('n') or 0) > 0:
        cash = op + mv
    else:
        cur.execute(
            "SELECT COALESCE(SUM(CASE WHEN entry_type='in' THEN amount ELSE -amount END),0) AS net "
            "FROM cash_books WHERE user_id=%s", (uid,))
        cash = float((cur.fetchone() or {}).get('net') or 0)

    cur.execute(
        "SELECT COUNT(DISTINCT customer_id) AS buyers, "
        "SUM(CASE WHEN c > 1 THEN 1 ELSE 0 END) AS repeaters "
        "FROM (SELECT customer_id, COUNT(*) AS c FROM sales "
        "WHERE user_id=%s AND customer_id IS NOT NULL GROUP BY customer_id) t",
        (uid,))
    rb = cur.fetchone() or {}
    buyers = int(rb.get('buyers') or 0)
    repeaters = int(rb.get('repeaters') or 0)

    cur.close()
    conn.close()

    if sales_prev_30 > 0:
        trend_pct = (sales_30 - sales_prev_30) / sales_prev_30 * 100
    else:
        trend_pct = 100 if sales_30 > 0 else 0
    trend_score = max(0, min(100, int(50 + trend_pct * 0.5)))

    margin_pct = round((profit_30 / sales_30 * 100) if sales_30 > 0 else 0, 1)
    margin_score = max(0, min(100, int(margin_pct * 2.5)))

    if total_sku > 0:
        stock_score = int(100 - (low_sku / total_sku) * 100)
    else:
        stock_score = 100

    monthly_exp = exp_30 if exp_30 > 0 else 1
    months_covered = round(cash / monthly_exp, 1) if cash > 0 else 0
    cash_score = max(0, min(100, int(months_covered * 50)))

    retention_score = int((repeaters / buyers * 100) if buyers > 0 else 0)

    final = int(
        trend_score * 0.30 + margin_score * 0.25 + stock_score * 0.15
        + cash_score * 0.15 + retention_score * 0.15
    )
    final = max(0, min(100, final))

    if final >= 80:
        status = 'Excellent'
    elif final >= 60:
        status = 'Good'
    elif final >= 40:
        status = 'Fair'
    else:
        status = 'Needs Attention'

    components = [
        {'name': 'Sales trend', 'score': trend_score, 'weight': 30,
         'detail': '30d vs prior 30d: {:+d}%'.format(int(trend_pct))},
        {'name': 'Margin', 'score': margin_score, 'weight': 25,
         'detail': 'Avg margin {}% over 30 days'.format(margin_pct)},
        {'name': 'Stock health', 'score': stock_score, 'weight': 15,
         'detail': '{} of {} SKU(s) low-stock'.format(low_sku, total_sku)},
        {'name': 'Cash buffer', 'score': cash_score, 'weight': 15,
         'detail': '{} months of expenses covered'.format(months_covered)},
        {'name': 'Retention', 'score': retention_score, 'weight': 15,
         'detail': '{} of {} customers bought twice+'.format(repeaters, buyers)},
    ]

    return render_template(
        'health.html',
        score=final,
        status=status,
        components=components,
        sales=sales_30,
        low=low_sku,
        trend_pct=round(trend_pct, 1),
        margin_pct=margin_pct,
        months_covered=months_covered,
        buyers=buyers,
        repeaters=repeaters,
    )


'''

PAT = re.compile(
    r"@app\.route\('/health'\)\n@login_required\ndef health\(\):\n.*?"
    r"(?=\n@app\.|\n#|\ndef |\nif __name__|\Z)",
    re.DOTALL)
m = PAT.search(src)
if not m:
    if "def health():" in src and "components" in src and "trend_score" in src:
        print("[SKIP] already patched")
    else:
        print("[FAIL] health not found"); sys.exit(1)
else:
    src = src[:m.start()] + NEW_ROUTE + src[m.end():]
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print("[OK] health route replaced")

NEW_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Business Health Score{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="activity"></i> Business Health Score</h1>
    <p>A weighted score computed from five independent factors. No guessing — every point is traced to real data.</p>
  </div>
</div>

<div class="widget" style="text-align:center;padding:2rem;">
  <div style="font-size:5rem;font-weight:800;font-family:var(--mono);color:{% if score >= 80 %}var(--green){% elif score >= 60 %}var(--red-bright){% elif score >= 40 %}#e0a030{% else %}#e74c3c{% endif %};line-height:1;">{{ score }}</div>
  <h2 style="margin:0.4rem 0 0;border:none;">{{ status }}</h2>
  <p style="margin:0.5rem 0 0;color:var(--text3);">out of 100</p>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>30-day sales</span><strong>{{ money(sales) }}</strong></div>
  <div class="stat-chip"><span>Sales trend</span><strong>{{ '%+d'|format(trend_pct|int) }}%</strong></div>
  <div class="stat-chip"><span>Avg margin</span><strong>{{ margin_pct }}%</strong></div>
  <div class="stat-chip"><span>Low-stock SKUs</span><strong>{{ low }}</strong></div>
  <div class="stat-chip"><span>Cash buffer</span><strong>{{ months_covered }} mo</strong></div>
  <div class="stat-chip"><span>Repeat buyers</span><strong>{{ repeaters }} / {{ buyers }}</strong></div>
</div>

<h2>Score breakdown</h2>
<div class="health-grid">
{% for c in components %}
  <div class="health-card">
    <div class="health-head">
      <strong>{{ c.name }}</strong>
      <span>{{ c.score }}/100</span>
    </div>
    <div class="health-bar"><div style="width:{{ c.score }}%;background:{% if c.score >= 80 %}var(--green){% elif c.score >= 60 %}var(--red-bright){% elif c.score >= 40 %}#e0a030{% else %}#e74c3c{% endif %};"></div></div>
    <p>{{ c.detail }}</p>
    <small style="color:var(--text3);">Weight: {{ c.weight }}%</small>
  </div>
{% endfor %}
</div>

<style>
.health-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.85rem; }
.health-card { padding: 1rem 1.1rem; border-radius: 12px; border: 1px solid var(--border); background: var(--surface); }
.health-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }
.health-head span { font-family: var(--mono); font-weight: 700; }
.health-bar { height: 8px; background: var(--surface2); border-radius: 4px; overflow: hidden; }
.health-bar div { height: 100%; transition: width 0.8s var(--ease-out); }
.health-card p { margin: 0.55rem 0 0.2rem; font-size: 0.86rem; color: var(--text2); }
</style>
{% endblock %}
'''

with open(TPL, 'w', encoding='utf-8') as fh:
    fh.write(NEW_TEMPLATE)
print(f"[OK] wrote {TPL} ({len(NEW_TEMPLATE):,} bytes)")

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
print("[OK] app.py compiles" if r.returncode == 0 else f"[FAIL]\n{r.stderr}")
print("\nTest: restart Flask, visit /health — score + 5-component breakdown.")