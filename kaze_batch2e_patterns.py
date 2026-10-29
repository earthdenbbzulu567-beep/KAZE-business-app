"""
kaze_batch2e_patterns.py — Batch 2e.

Consolidates 3 disabled routes into 1 tabbed page (/analytics/patterns):
  - Cohorts      (customer retention by first-purchase month)
  - Seasonality  (day-of-week + month-of-year revenue patterns)
  - Variance     (actual vs goal, last 6 months)

Includes built-in safety verification:
  - Extracts the NEW_ROUTES block as the batch would evaluate it
  - Compiles it as Python BEFORE writing app.py
  - Aborts if it fails; app.py stays untouched

Run from the folder with app.py:
    python kaze_batch2e_patterns.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

with open(APP, encoding='utf-8') as f:
    src = f.read()

initial_routes = src.count('@app.route')
backup_path = f"{APP}.bak.batch2e_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}\n")

APPLIED = []
FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("[1/7] Remove 3 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = ['/stats/cohort', '/stats/seasonality', '/reports/variance']

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
print("\n[2/7] Add /analytics/patterns route + 3 redirects")
# ═══════════════════════════════════════════════════════════════════

NEW_ROUTES = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 2e — Patterns (consolidated from 3 disabled routes)
# ═══════════════════════════════════════════════════════════════════════

_bind_module('reports',
    'analytics_patterns',
    'redirect_stats_cohort', 'redirect_stats_seasonality',
    'redirect_reports_variance')


@app.route('/analytics/patterns')
@login_required
def analytics_patterns():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    from collections import defaultdict
    from datetime import datetime as _dt

    # ── Cohorts ───────────────────────────────────────
    cur.execute("""
        WITH first_purchase AS (
            SELECT customer_id, MIN(sale_date) AS first_date
            FROM sales
            WHERE user_id=%s AND customer_id IS NOT NULL
            GROUP BY customer_id
        ),
        purchases AS (
            SELECT s.customer_id,
                   substr(fp.first_date, 1, 7) AS cohort_month,
                   substr(s.sale_date, 1, 7) AS purchase_month
            FROM sales s
            JOIN first_purchase fp ON fp.customer_id = s.customer_id
            WHERE s.user_id=%s
        )
        SELECT cohort_month, purchase_month,
               COUNT(DISTINCT customer_id) AS customers
        FROM purchases
        GROUP BY cohort_month, purchase_month
        ORDER BY cohort_month, purchase_month
    """, (uid, uid))

    cohort_data = defaultdict(dict)
    cohort_sizes = defaultdict(int)
    all_months = set()

    for r in (cur.fetchall() or []):
        cm = r['cohort_month']
        pm = r['purchase_month']
        cnt = int(r['customers'] or 0)
        try:
            cm_dt = _dt.strptime(cm + '-01', '%Y-%m-%d')
            pm_dt = _dt.strptime(pm + '-01', '%Y-%m-%d')
            offset = (pm_dt.year - cm_dt.year) * 12 + (pm_dt.month - cm_dt.month)
        except (ValueError, TypeError):
            offset = 0
        if offset < 0:
            continue
        cohort_data[cm][offset] = cnt
        if offset == 0:
            cohort_sizes[cm] = cnt
        all_months.add(offset)

    cohort_rows = []
    for cm in sorted(cohort_data.keys()):
        size = cohort_sizes.get(cm, 0)
        cells = []
        for off in sorted(all_months):
            n = cohort_data[cm].get(off, 0)
            pct = round(n / size * 100, 1) if size > 0 else 0
            cells.append({'offset': off, 'customers': n, 'pct': pct})
        cohort_rows.append({'cohort': cm, 'size': size, 'cells': cells})
    max_offset = (max(all_months) + 1) if all_months else 0

    # ── Seasonality ───────────────────────────────────
    cur.execute("""
        SELECT EXTRACT(DOW FROM sale_date::date) AS dow,
               AVG(daily_rev) AS avg_rev,
               COUNT(*) AS days
        FROM (
            SELECT sale_date, SUM(total_amount) AS daily_rev
            FROM sales WHERE user_id=%s
            GROUP BY sale_date
        ) daily
        GROUP BY EXTRACT(DOW FROM sale_date::date)
        ORDER BY dow
    """, (uid,))
    dow_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    dow_rows = []
    dow_max = 0
    for r in (cur.fetchall() or []):
        try:
            idx = int(r.get('dow') or 0)
        except (TypeError, ValueError):
            idx = 0
        avg = float(r.get('avg_rev') or 0)
        dow_max = max(dow_max, avg)
        dow_rows.append({
            'name': dow_names[idx] if 0 <= idx < 7 else '?',
            'avg': round(avg, 2),
            'days': int(r.get('days') or 0),
        })
    for r in dow_rows:
        r['bar_pct'] = round(r['avg'] / dow_max * 100, 1) if dow_max > 0 else 0

    cur.execute("""
        SELECT EXTRACT(MONTH FROM sale_date::date) AS mon,
               AVG(daily_rev) AS avg_rev,
               COUNT(*) AS days
        FROM (
            SELECT sale_date, SUM(total_amount) AS daily_rev
            FROM sales WHERE user_id=%s
            GROUP BY sale_date
        ) daily
        GROUP BY EXTRACT(MONTH FROM sale_date::date)
        ORDER BY mon
    """, (uid,))
    mon_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    mon_rows = []
    mon_max = 0
    for r in (cur.fetchall() or []):
        try:
            idx = int(r.get('mon') or 1)
        except (TypeError, ValueError):
            idx = 1
        avg = float(r.get('avg_rev') or 0)
        mon_max = max(mon_max, avg)
        mon_rows.append({
            'name': mon_names[idx - 1] if 1 <= idx <= 12 else '?',
            'avg': round(avg, 2),
            'days': int(r.get('days') or 0),
        })
    for r in mon_rows:
        r['bar_pct'] = round(r['avg'] / mon_max * 100, 1) if mon_max > 0 else 0

    # ── Variance vs goal ──────────────────────────────
    cur.execute("SELECT monthly_revenue_goal FROM settings WHERE user_id=%s", (uid,))
    goal = float((cur.fetchone() or {}).get('monthly_revenue_goal') or 0)

    cur.execute("""
        SELECT substr(sale_date, 1, 7) AS month,
               COALESCE(SUM(total_amount),0) AS revenue,
               COALESCE(SUM(profit),0) AS profit
        FROM sales
        WHERE user_id=%s
          AND sale_date >= to_char(CURRENT_DATE - INTERVAL '6 months','YYYY-MM-DD')
        GROUP BY substr(sale_date, 1, 7)
        ORDER BY month
    """, (uid,))
    variance_rows = []
    for r in (cur.fetchall() or []):
        rev = float(r.get('revenue') or 0)
        var = rev - goal if goal else 0
        variance_rows.append({
            'month': r.get('month') or '?',
            'revenue': rev,
            'profit': float(r.get('profit') or 0),
            'goal': goal,
            'variance': round(var, 2),
            'hit': (var >= 0) if goal else None,
        })

    cur.close(); conn.close()

    return render_template('analytics_patterns.html',
        cohort_rows=cohort_rows,
        max_offset=max_offset,
        dow_rows=dow_rows,
        mon_rows=mon_rows,
        variance_rows=variance_rows,
        goal=goal,
    )


@app.route('/stats/cohort')
@login_required
def redirect_stats_cohort():
    return redirect(url_for('analytics_patterns') + '#cohorts', code=301)


@app.route('/stats/seasonality')
@login_required
def redirect_stats_seasonality():
    return redirect(url_for('analytics_patterns') + '#seasonality', code=301)


@app.route('/reports/variance')
@login_required
def redirect_reports_variance():
    return redirect(url_for('analytics_patterns') + '#variance', code=301)

'''

# ── VERIFICATION: extract and compile BEFORE writing ─────────────
print("\n[VERIFY] Compiling NEW_ROUTES block before writing to app.py...")
code_to_check = "NEW_ROUTES = '''" + NEW_ROUTES + "'''"
ns = {}
try:
    exec(code_to_check, ns)
    evaluated = ns['NEW_ROUTES']
except Exception as exc:
    print(f"  [FAIL] Could not evaluate NEW_ROUTES: {exc}")
    print(f"\n[ABORT] app.py untouched. Restore if needed: copy \"{backup_path}\" {APP}")
    sys.exit(1)

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
    tmp.write(evaluated)
    tmp_path = tmp.name
rc = subprocess.run([sys.executable, '-m', 'py_compile', tmp_path], capture_output=True, text=True)
os.unlink(tmp_path)
if rc.returncode != 0:
    print("  [FAIL] NEW_ROUTES as evaluated does not compile:")
    print(rc.stderr)
    print(f"\n[ABORT] app.py untouched. Restore if needed: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print(f"  [OK]   NEW_ROUTES compiles when evaluated ({len(evaluated):,} chars)")
print(f"  [OK]   No syntax errors in the code that will be inserted")

# Insert into src
if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + NEW_ROUTES + '\n' + src[idx:]
else:
    src += '\n' + NEW_ROUTES
print("  [OK]   inserted /analytics/patterns + 3 redirects")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/7] Add Patterns to NAV")
# ═══════════════════════════════════════════════════════════════════

NAV_ANCHOR = "        ('Decisions & signals', 'analytics_decisions', 'lightbulb', 'reports', ('analytics_decisions',)),"
NAV_NEW = """        ('Decisions & signals', 'analytics_decisions', 'lightbulb', 'reports', ('analytics_decisions',)),
        ('Patterns', 'analytics_patterns', 'activity', 'reports', ('analytics_patterns',)),"""

if NAV_ANCHOR in src:
    src = src.replace(NAV_ANCHOR, NAV_NEW, 1)
    print("  [OK]   Patterns added to Analytics nav")
else:
    print("  [FAIL] nav anchor not found (Decisions entry)")
    FAILED.append("nav")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/7] Write app.py")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   {initial_routes} -> {final_routes} @app.route (+{final_routes - initial_routes})")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/7] Write template")
# ═══════════════════════════════════════════════════════════════════

os.makedirs('templates', exist_ok=True)

TPL = '''{% extends "base.html" %}
{% block title %}Patterns{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="activity"></i> Patterns</h1>
    <p>Cohort retention, seasonality, and variance vs goal over the last 6 months.</p>
  </div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="cohorts" class="is-on">Cohorts</button>
  <button type="button" data-tab="seasonality">Seasonality</button>
  <button type="button" data-tab="variance">Variance</button>
</nav>

<section class="analytics-panel is-on" id="panel-cohorts">
  {% if cohort_rows %}
  <h2>Customer retention cohorts</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Each row is a cohort of customers whose first purchase was in that month. Each column shows months since first purchase. Cells show customers who purchased in that month, with percentage of the original cohort.
  </p>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>Cohort</th>
          <th>Size</th>
          {% for i in range(max_offset) %}
          <th>Month {{ i }}</th>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
      {% for row in cohort_rows %}
      <tr>
        <td><strong>{{ row.cohort }}</strong></td>
        <td>{{ row.size }}</td>
        {% for cell in row.cells %}
        <td style="text-align:center;{% if cell.pct >= 60 %}background:var(--green-dim);{% elif cell.pct >= 30 %}background:rgba(224,160,48,0.08);{% elif cell.pct == 0 %}color:var(--text3);{% endif %}">
          {{ cell.customers }} <small>({{ cell.pct }}%)</small>
        </td>
        {% endfor %}
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  <p style="font-size:0.85rem;color:var(--text3);margin-top:0.75rem;">
    Customers who stay past month 1 are much more likely to stay long term. Retention falling fast in month 1 usually means the first experience needs attention.
  </p>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No cohort data yet. Need at least one customer with a recorded sale to start building cohorts.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-seasonality">
  {% if dow_rows %}
  <h2>Day-of-week pattern</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Average revenue per day of the week, across all sales. Bar length is relative.
  </p>
  <div class="seasonality-bars">
    {% for r in dow_rows %}
    <div class="season-row">
      <span class="season-label">{{ r.name }}</span>
      <div class="season-bar-wrap"><div class="season-bar" style="width:{{ r.bar_pct }}%;"></div></div>
      <span class="season-value">{{ money(r.avg) }} ({{ r.days }}d)</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if mon_rows %}
  <h2 style="margin-top:2rem;">Month-of-year pattern</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Average revenue per calendar month. Best months show where demand peaks.
  </p>
  <div class="seasonality-bars">
    {% for r in mon_rows %}
    <div class="season-row">
      <span class="season-label">{{ r.name }}</span>
      <div class="season-bar-wrap"><div class="season-bar" style="width:{{ r.bar_pct }}%;"></div></div>
      <span class="season-value">{{ money(r.avg) }} ({{ r.days }}d)</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if not dow_rows and not mon_rows %}
  <div class="widget"><p style="color:var(--text3);">No sales data yet to analyze seasonality.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-variance">
  {% if goal > 0 %}
  <h2>Actual vs goal, last 6 months</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Monthly revenue compared to your current goal of <strong>{{ money(goal) }}</strong>.
    Note: goal is not stored historically. Past months are compared to the goal today, not the goal at that time.
  </p>
  {% if variance_rows %}
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Month</th><th style="text-align:right;">Revenue</th><th style="text-align:right;">Goal</th><th style="text-align:right;">Variance</th><th>Status</th></tr></thead>
      <tbody>
      {% for r in variance_rows %}
      <tr {% if r.hit %}style="background:var(--green-dim);"{% else %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td>{{ r.month }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.revenue) }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.goal) }}</td>
        <td style="text-align:right;font-family:var(--mono);{% if r.variance < 0 %}color:#e74c3c;{% else %}color:var(--green);{% endif %}">{{ money(r.variance) }}</td>
        <td>{% if r.hit %}<span class="status-pill status-ok">Hit</span>{% else %}<span class="status-pill" style="background:rgba(224,160,48,0.15);color:#e0a030;">Missed</span>{% endif %}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No sales in the last 6 months to compare.</p></div>
  {% endif %}
  {% else %}
  <div class="widget"><p style="color:var(--text3);">
    Set a monthly revenue goal in <a href="{{ url_for('settings') }}">Settings</a> to unlock variance tracking.
  </p></div>
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
.seasonality-bars { display:flex; flex-direction:column; gap:0.4rem; margin:0.5rem 0 1rem; }
.season-row { display:grid; grid-template-columns:56px 1fr 140px; align-items:center; gap:0.7rem; font-size:0.88rem; }
.season-label { font-weight:700; color:var(--text2); }
.season-bar-wrap { height:14px; background:var(--surface2); border-radius:4px; overflow:hidden; }
.season-bar { height:100%; background:linear-gradient(90deg,var(--red-bright),var(--green)); border-radius:4px; }
.season-value { font-family:var(--mono); font-size:0.82rem; text-align:right; color:var(--text2); }
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
  if (['cohorts','seasonality','variance'].includes(hash)) {
    activate(hash);
  }
})();
</script>
{% endblock %}
'''

with open('templates/analytics_patterns.html', 'w', encoding='utf-8') as f:
    f.write(TPL)
print("  [OK]   templates/analytics_patterns.html")

# ═══════════════════════════════════════════════════════════════════
print("\n[6/7] Compile check app.py")
# ═══════════════════════════════════════════════════════════════════

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

# ═══════════════════════════════════════════════════════════════════
print("\n[7/7] Summary")
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 62)
print(f"  Removed from disabled:  {removed}/3")
print(f"  New routes added:        4 (1 page + 3 redirects)")
print(f"  New templates:           1")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 3 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 2e complete.

NEXT STEPS — in this exact order:

1. LOCAL TEST — run:  python app.py
   (Make sure $env:DATABASE_URL is set in this PowerShell session)

   Visit:

     /analytics/patterns   -> 3 tabs (Cohorts / Seasonality / Variance)
                              Click each. See expected content below.

     /stats/cohort          -> 301 redirect to /analytics/patterns#cohorts
     /stats/seasonality     -> 301 redirect to /analytics/patterns#seasonality
     /reports/variance      -> 301 redirect to /analytics/patterns#variance

   Sidebar: Analytics section should now have 6 entries
            (Sales, Customer, Inventory, Books health, Decisions, Patterns).

   Regression — verify still works:
     /dashboard
     /plans (Active — renews 2027-10-26)
     /sales/analytics, /customers/analytics, /stock/analytics,
     /accounts/health, /analytics/decisions

2. REPORT BACK with actual tab contents:
   - Cohorts tab: how many cohort rows? what do the cells show?
   - Seasonality tab: 7 day rows + 12 month rows?
   - Variance tab: 6 month rows OR "set a goal" message
   - 3 redirects work?
   - Sidebar 6 entries?
   - Regression all pass?

3. Only after I confirm your local test results, commit + push + deploy.

4. Test on production.

5. Only after prod pass — delete backup: rm app.py.bak.batch2e_*

Note: /health/history is deferred to Batch 3 (needs score_snapshots schema).

Deferred but still disabled: 16 non-schema routes + 10 schema routes.
After Batch 2e: 13 non-schema remain for Batches 2f/2g.
""")