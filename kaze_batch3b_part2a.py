"""
kaze_batch3b_part2a.py — Batch 3b part 2a.

Builds /health/history:
  - New table: score_snapshots
  - /health route: writes a snapshot once per day per user
  - New route /health/history: shows score trend + component breakdown over time
  - Deletes old /health/history placeholder

Includes pre-step to delete old placeholder route (avoid endpoint conflict).

Run from the folder with app.py:
    python kaze_batch3b_part2a.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'
TPL_DIR = 'templates'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

with open(APP, encoding='utf-8') as f:
    src = f.read()

initial_routes = src.count('@app.route')
backup_path = f"{APP}.bak.batch3b2a_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}")

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/7] Schema — score_snapshots table")
# ═══════════════════════════════════════════════════════════════════

SCHEMA_ANCHOR = """    cur.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_user ON whatsapp_messages (user_id, sent_at DESC)')"""

SCHEMA_NEW = """    cur.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_user ON whatsapp_messages (user_id, sent_at DESC)')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS score_snapshots (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            snapshot_date TEXT NOT NULL,
            overall_score INTEGER NOT NULL,
            trend_score INTEGER DEFAULT 0,
            margin_score INTEGER DEFAULT 0,
            stock_score INTEGER DEFAULT 0,
            cash_score INTEGER DEFAULT 0,
            retention_score INTEGER DEFAULT 0,
            UNIQUE(user_id, snapshot_date)
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_score_snapshots_user ON score_snapshots (user_id, snapshot_date DESC)')"""

if SCHEMA_ANCHOR in src:
    src = src.replace(SCHEMA_ANCHOR, SCHEMA_NEW, 1)
    print("  [OK]   added score_snapshots table + index")
else:
    print("  [FAIL] schema anchor not found (whatsapp_messages index)")
    FAILED.append("schema")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/7] Delete old /health/history placeholder")
# ═══════════════════════════════════════════════════════════════════

marker = "@app.route('/health/history'"
idx = src.find(marker)
if idx >= 0:
    end_idx = len(src)
    for end_marker in ['\n@app.route', '\n# ===', '\nif __name__']:
        pos = src.find(end_marker, idx + len(marker))
        if pos > 0 and pos < end_idx:
            end_idx = pos
    while end_idx > 0 and src[end_idx-1] == '\n':
        end_idx -= 1
    src = src[:idx] + src[end_idx:]
    print("  [DEL]  /health/history (old placeholder)")
else:
    print("  [SKIP] /health/history placeholder not found (already gone?)")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/7] Remove /health/history from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

removed = 0
pattern = re.compile(r"\s*'/health/history',?\n")
if pattern.search(src):
    src = pattern.sub('\n', src, count=1)
    removed += 1
    print("  [OK]   removed from disabled set")
else:
    print("  [SKIP] not in disabled set")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/7] Modify /health route to write snapshot before render")
# ═══════════════════════════════════════════════════════════════════

OLD_HEALTH_TAIL = """    components = [
        {'name': 'Sales trend', 'score': trend_score, 'weight': 30, 'detail': f'30d vs prior: {int(trend_pct):+d}%'},
        {'name': 'Margin', 'score': margin_score, 'weight': 25, 'detail': f'{margin_pct}% avg margin'},
        {'name': 'Stock health', 'score': stock_score, 'weight': 15, 'detail': f'{low_sku}/{total_sku} low-stock'},
        {'name': 'Cash buffer', 'score': cash_score, 'weight': 15, 'detail': f'{months_covered} months covered'},
        {'name': 'Retention', 'score': retention_score, 'weight': 15, 'detail': f'{repeaters}/{buyers} repeat'},
    ]
    return render_template('health.html', score=final, status=status, components=components,"""

NEW_HEALTH_TAIL = """    components = [
        {'name': 'Sales trend', 'score': trend_score, 'weight': 30, 'detail': f'30d vs prior: {int(trend_pct):+d}%'},
        {'name': 'Margin', 'score': margin_score, 'weight': 25, 'detail': f'{margin_pct}% avg margin'},
        {'name': 'Stock health', 'score': stock_score, 'weight': 15, 'detail': f'{low_sku}/{total_sku} low-stock'},
        {'name': 'Cash buffer', 'score': cash_score, 'weight': 15, 'detail': f'{months_covered} months covered'},
        {'name': 'Retention', 'score': retention_score, 'weight': 15, 'detail': f'{repeaters}/{buyers} repeat'},
    ]
    # Write snapshot for /health/history (once per day per user)
    try:
        today_iso = datetime.today().strftime('%Y-%m-%d')
        snap_cur = conn.cursor()
        snap_cur.execute(
            "INSERT INTO score_snapshots (user_id, snapshot_date, overall_score, "
            "trend_score, margin_score, stock_score, cash_score, retention_score) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (user_id, snapshot_date) DO NOTHING",
            (uid, today_iso, final, trend_score, margin_score, stock_score, cash_score, retention_score),
        )
        conn.commit()
        snap_cur.close()
    except Exception as _snap_err:
        print("health snapshot write error:", _snap_err)
    return render_template('health.html', score=final, status=status, components=components,"""

if OLD_HEALTH_TAIL in src:
    src = src.replace(OLD_HEALTH_TAIL, NEW_HEALTH_TAIL, 1)
    print("  [OK]   /health route writes daily snapshot before render")
else:
    print("  [FAIL] /health route tail pattern not found")
    FAILED.append("health route modification")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/7] Add new /health/history route")
# ═══════════════════════════════════════════════════════════════════

NEW_PY = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 3b part 2a — Health history
# ═══════════════════════════════════════════════════════════════════════

@app.route('/health/history')
@login_required
def health_history():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT snapshot_date, overall_score, trend_score, margin_score,
               stock_score, cash_score, retention_score
        FROM score_snapshots
        WHERE user_id=%s
        ORDER BY snapshot_date ASC
        LIMIT 180
    """, (uid,))
    rows = []
    for r in (cur.fetchall() or []):
        rows.append({
            'date': r.get('snapshot_date') or '?',
            'overall': int(r.get('overall_score') or 0),
            'trend': int(r.get('trend_score') or 0),
            'margin': int(r.get('margin_score') or 0),
            'stock': int(r.get('stock_score') or 0),
            'cash': int(r.get('cash_score') or 0),
            'retention': int(r.get('retention_score') or 0),
        })
    cur.close(); conn.close()

    has_data = len(rows) > 0
    first_score = rows[0]['overall'] if has_data else 0
    last_score = rows[-1]['overall'] if has_data else 0
    delta = last_score - first_score if has_data else 0

    labels = [r['date'] for r in rows]
    overalls = [r['overall'] for r in rows]
    trends = [r['trend'] for r in rows]
    margins = [r['margin'] for r in rows]
    stocks = [r['stock'] for r in rows]
    cashes = [r['cash'] for r in rows]
    retentions = [r['retention'] for r in rows]

    return render_template('health_history.html',
        rows=rows,
        has_data=has_data,
        first_score=first_score,
        last_score=last_score,
        delta=delta,
        labels=labels,
        overalls=overalls,
        trends=trends,
        margins=margins,
        stocks=stocks,
        cashes=cashes,
        retentions=retentions,
    )

'''

# VERIFY: compile NEW_PY
print("  [VERIFY] Compiling NEW_PY...")
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
    tmp.write(NEW_PY)
    tmp_path = tmp.name
rc = subprocess.run([sys.executable, '-m', 'py_compile', tmp_path], capture_output=True, text=True)
os.unlink(tmp_path)
if rc.returncode != 0:
    print("  [FAIL] NEW_PY does not compile:")
    print(rc.stderr)
    print(f"\n[ABORT] app.py untouched. Restore: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print(f"  [OK]   NEW_PY compiles ({len(NEW_PY):,} chars)")

if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + NEW_PY + '\n' + src[idx:]
else:
    src += '\n' + NEW_PY
print("  [OK]   inserted /health/history route")

# ═══════════════════════════════════════════════════════════════════
print("\n[6/7] Write app.py + write template")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   app.py written ({initial_routes} -> {final_routes} @app.route)")

os.makedirs(TPL_DIR, exist_ok=True)

TPL = '''{% extends "base.html" %}
{% block title %}Health History{% endblock %}
{% block charts_js %}<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="history"></i> Health History</h1>
    <p>Your business health score over time. A snapshot is recorded each day you visit the <a href="{{ url_for('health') }}">Health Score</a> page.</p>
  </div>
  <a href="{{ url_for('health') }}" class="btn-secondary">← Current score</a>
</div>

{% if has_data %}
<div class="stat-grid">
  <div class="stat-chip"><span>Snapshots</span><strong>{{ rows|length }}</strong></div>
  <div class="stat-chip"><span>First score</span><strong>{{ first_score }}/100</strong></div>
  <div class="stat-chip"><span>Latest score</span><strong>{{ last_score }}/100</strong></div>
  <div class="stat-chip">
    <span>Change</span>
    <strong style="color:{% if delta > 0 %}var(--green){% elif delta < 0 %}#e74c3c{% else %}var(--text3){% endif %};">
      {{ '%+d'|format(delta) }}
    </strong>
  </div>
</div>

<h2>Overall score trend</h2>
<div class="chart-container">
  <canvas id="overallChart" height="140"></canvas>
</div>

<h2>Component trends</h2>
<div class="chart-container">
  <canvas id="componentsChart" height="150"></canvas>
</div>

<h2>All snapshots</h2>
<div class="table-wrapper">
<table>
<thead><tr>
  <th>Date</th><th>Overall</th><th>Trend</th><th>Margin</th>
  <th>Stock</th><th>Cash</th><th>Retention</th>
</tr></thead>
<tbody>
{% for r in rows|reverse %}
<tr>
  <td>{{ r.date }}</td>
  <td style="font-family:var(--mono);font-weight:700;color:{% if r.overall >= 80 %}var(--green){% elif r.overall >= 60 %}var(--red-bright){% elif r.overall >= 40 %}#e0a030{% else %}#e74c3c{% endif %};">{{ r.overall }}</td>
  <td style="font-family:var(--mono);">{{ r.trend }}</td>
  <td style="font-family:var(--mono);">{{ r.margin }}</td>
  <td style="font-family:var(--mono);">{{ r.stock }}</td>
  <td style="font-family:var(--mono);">{{ r.cash }}</td>
  <td style="font-family:var(--mono);">{{ r.retention }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>

<script>
(function(){
  const labels = {{ labels|tojson }};
  const overalls = {{ overalls|tojson }};
  const trends = {{ trends|tojson }};
  const margins = {{ margins|tojson }};
  const stocks = {{ stocks|tojson }};
  const cashes = {{ cashes|tojson }};
  const retentions = {{ retentions|tojson }};

  new Chart(document.getElementById('overallChart'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Overall health',
        data: overalls,
        borderColor: '#2ecc71',
        backgroundColor: 'rgba(46,204,113,0.12)',
        tension: 0.25,
        fill: true,
        borderWidth: 3,
        pointRadius: 5,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: 'Overall score over time' },
        tooltip: { callbacks: { label: c => 'Overall: ' + c.raw + '/100' } }
      },
      scales: { y: { min: 0, max: 100, ticks: { stepSize: 20 } } }
    }
  });

  new Chart(document.getElementById('componentsChart'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        { label: 'Trend', data: trends, borderColor: '#e0a030', tension: 0.25, fill: false, borderWidth: 2 },
        { label: 'Margin', data: margins, borderColor: '#2ecc71', tension: 0.25, fill: false, borderWidth: 2 },
        { label: 'Stock', data: stocks, borderColor: '#3498db', tension: 0.25, fill: false, borderWidth: 2 },
        { label: 'Cash', data: cashes, borderColor: '#9b59b6', tension: 0.25, fill: false, borderWidth: 2 },
        { label: 'Retention', data: retentions, borderColor: '#e74c3c', tension: 0.25, fill: false, borderWidth: 2 },
      ]
    },
    options: {
      responsive: true,
      plugins: { title: { display: true, text: 'Component scores (each 0-100)' } },
      scales: { y: { min: 0, max: 100, ticks: { stepSize: 20 } } }
    }
  });
})();
</script>

{% else %}
<div class="widget">
  <p style="color:var(--text3);">
    No snapshots yet. Visit the <a href="{{ url_for('health') }}">Health Score</a> page —
    a snapshot is recorded once per day, so the trend builds over the next few days/weeks
    as you use the app.
  </p>
</div>
{% endif %}
{% endblock %}
'''

try:
    Environment().parse(TPL)
except Exception as exc:
    print(f"  [FAIL] health_history.html Jinja error: {exc}")
    FAILED.append("template jinja")
else:
    with open(os.path.join(TPL_DIR, 'health_history.html'), 'w', encoding='utf-8') as f:
        f.write(TPL)
    print("  [OK]   templates/health_history.html")

# ═══════════════════════════════════════════════════════════════════
print("\n[7/7] Compile check")
# ═══════════════════════════════════════════════════════════════════

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
print(f"  Removed from disabled:  {removed}/1")
print(f"  New routes added:        1 (/health/history)")
print(f"  New tables:              1 (score_snapshots)")
print(f"  Route modifications:     1 (/health writes snapshot)")
print(f"  New templates:           1")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 1 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 3b part 2a complete.

NEXT STEPS:

1. LOCAL TEST — run:  python app.py
   (Verify $env:DATABASE_URL is set)

   /health         -> visit once. Should render normally.
                      Behind the scenes a snapshot row is written for today.
   /health/history -> NEW page. First visit will show:
                      - 1 row in the table (today's snapshot)
                      - chart with 1 data point (a dot, not yet a line)
                      - "Change: 0"

   Visit /health a second time today -> history still shows 1 row
   (once-per-day deduplication works)

   Regression:
     /dashboard, /plans (Active), /health (still works normally)

2. REPORT BACK:
   - /health loads without error and snapshot writes silently?
   - /health/history loads and shows the row from today?
   - /health still renders score/status/components as before?
   - /plans still active?
   - No 500s on any page?

3. Only after I confirm, commit + push + deploy.
4. Test on production.

5. Only after prod pass:
     rm app.py.bak.batch3b2a_*

NEXT AFTER THIS:
  Part 2b — /documents/versions (bookkeeping doc version history)
  Part 2c — /payments/fees (Stripe fee tracking)
""")