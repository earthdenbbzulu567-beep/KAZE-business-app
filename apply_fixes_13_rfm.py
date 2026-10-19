"""
apply_fixes_13_rfm.py — replace /rfm stub with real RFM scoring + segments.

Before: table of last purchase / frequency / monetary
After:  R/F/M scores 1-5 for each customer, grouped into
        Champions / Loyal / At Risk / Lost / New / Promising segments,
        with per-segment counts, per-segment tables, and a summary.
"""

import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'
TPL = os.path.join('templates', 'rfm.html')

if not os.path.isfile(APP):
    print("ERROR: app.py not found."); sys.exit(1)

shutil.copy2(APP, f"{APP}.bak.{STAMP}"); print(f"Backup: {APP}.bak.{STAMP}")
if os.path.isfile(TPL):
    shutil.copy2(TPL, f"{TPL}.bak.{STAMP}"); print(f"Backup: {TPL}.bak.{STAMP}")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

NEW_ROUTE = r'''@app.route('/rfm')
@login_required
def rfm():
    uid = current_user.id
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT c.id, c.name, "
        "MAX(s.sale_date) AS last_purchase, "
        "COUNT(s.id) AS frequency, "
        "COALESCE(SUM(s.total_amount),0) AS monetary "
        "FROM customers c "
        "LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id "
        "WHERE c.user_id=%s GROUP BY c.id, c.name",
        (uid,))
    raw = cur.fetchall() or []
    cur.close()
    conn.close()

    today = datetime.today().date()
    customers = []
    for c in raw:
        lp = (c.get('last_purchase') or '')[:10]
        if lp:
            try:
                days = (today - datetime.strptime(lp, '%Y-%m-%d').date()).days
            except ValueError:
                days = 9999
        else:
            days = 9999
        freq = int(c.get('frequency') or 0)
        monetary = float(c.get('monetary') or 0)
        r = 5 if days < 7 else 4 if days < 30 else 3 if days < 60 else 2 if days < 90 else 1
        f = 1 if freq <= 1 else 2 if freq == 2 else 3 if freq <= 4 else 4 if freq <= 9 else 5
        customers.append({
            'name': c.get('name') or 'Customer',
            'days': days,
            'frequency': freq,
            'monetary': monetary,
            'R': r, 'F': f,
        })

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

    return render_template(
        'rfm.html',
        customers=customers,
        groups=groups,
        summary=summary,
        segment_order=segment_order,
        total_customers=len(customers),
        avg_monetary=avg_m,
    )


'''

PAT = re.compile(
    r"@app\.route\('/rfm'\)\n@login_required\ndef rfm\(\):\n.*?"
    r"(?=\n@app\.|\n#|\ndef |\nif __name__|\Z)",
    re.DOTALL)
m = PAT.search(src)
if not m:
    if "def rfm():" in src and "segment_order" in src:
        print("[SKIP] already patched")
    else:
        print("[FAIL] rfm not found"); sys.exit(1)
else:
    src = src[:m.start()] + NEW_ROUTE + src[m.end():]
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print("[OK] rfm route replaced")

NEW_TEMPLATE = '''{% extends "base.html" %}
{% block title %}RFM Analysis{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="users"></i> RFM Analysis</h1>
    <p>Recency, Frequency, Monetary value — scored 1–5 per customer and grouped into segments.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Customers</span><strong>{{ total_customers }}</strong></div>
  <div class="stat-chip"><span>Avg lifetime spend</span><strong>{{ money(avg_monetary) }}</strong></div>
</div>

<h2>Segments</h2>
<div class="rfm-grid">
{% for s in summary %}
  <div class="rfm-card rfm-{{ s.name|lower|replace(' ','-') }}">
    <strong>{{ s.name }}</strong>
    <div class="rfm-count">{{ s.count }}</div>
    <small>customer{{ '' if s.count == 1 else 's' }}</small>
  </div>
{% endfor %}
</div>

<h2>All customers</h2>
<div class="table-wrapper">
<table>
<thead><tr><th>Customer</th><th>Segment</th><th>R</th><th>F</th><th>M</th><th>RFM</th><th>Days since last</th><th>Orders</th><th>Lifetime spend</th></tr></thead>
<tbody>
{% for c in customers %}
<tr>
  <td>{{ c.name }}</td>
  <td><span class="status-pill rfm-pill-{{ c.segment|lower|replace(' ','-') }}">{{ c.segment }}</span></td>
  <td>{{ c.R }}</td><td>{{ c.F }}</td><td>{{ c.M }}</td>
  <td><code>{{ c.rfm }}</code></td>
  <td>{% if c.days > 9000 %}never{% else %}{{ c.days }}d{% endif %}</td>
  <td>{{ c.frequency }}</td>
  <td>{{ money(c.monetary) }}</td>
</tr>
{% else %}
<tr><td colspan="9">No customers yet.</td></tr>
{% endfor %}
</tbody>
</table>
</div>

<style>
.rfm-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin: 0 0 1.5rem; }
.rfm-card { padding: 1rem; border-radius: 12px; border: 1px solid var(--border); background: var(--surface); border-left: 4px solid var(--text3); }
.rfm-card strong { font-size: 0.9rem; }
.rfm-count { font-size: 2rem; font-weight: 800; font-family: var(--mono); margin: 0.3rem 0; }
.rfm-card small { color: var(--text3); font-size: 0.78rem; }
.rfm-champion { border-left-color: var(--green); }
.rfm-loyal { border-left-color: #3498db; }
.rfm-new { border-left-color: #9b59b6; }
.rfm-at-risk { border-left-color: #e0a030; }
.rfm-needs-attention { border-left-color: #e67e22; }
.rfm-lost { border-left-color: #e74c3c; }
.rfm-pill-champion { background: var(--green-dim); color: var(--green); }
.rfm-pill-loyal { background: rgba(52,152,219,0.15); color: #3498db; }
.rfm-pill-new { background: rgba(155,89,182,0.15); color: #9b59b6; }
.rfm-pill-at-risk { background: rgba(224,160,48,0.15); color: #e0a030; }
.rfm-pill-needs-attention { background: rgba(230,126,34,0.15); color: #e67e22; }
.rfm-pill-lost { background: rgba(231,76,60,0.15); color: #e74c3c; }
</style>
{% endblock %}
'''

with open(TPL, 'w', encoding='utf-8') as fh:
    fh.write(NEW_TEMPLATE)
print(f"[OK] wrote {TPL} ({len(NEW_TEMPLATE):,} bytes)")

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
print("[OK] app.py compiles" if r.returncode == 0 else f"[FAIL]\n{r.stderr}")
print("\nTest: restart Flask, visit /rfm — segment cards + scored table.")