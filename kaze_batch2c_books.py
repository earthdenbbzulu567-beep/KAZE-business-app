"""
kaze_batch2c_books.py — Batch 2c.

Consolidates 4 disabled routes into 1 tabbed page (/accounts/health):
  - Trial balance (DR/CR per account, from typed journal entries)
  - Integrity (each journal book balances to zero)
  - Anomaly scan (30d cash entries > 3x median)
  - Duplicate check (identical bookkeeping_docs)

Redirects: 4 original URLs -> new tab anchors.

/payments/fees is NOT in this batch — deferred to a future batch
that adds stripe_fee tracking. Currently disabled-pending.

Run from the folder with app.py:
    python kaze_batch2c_books.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

with open(APP, encoding='utf-8') as f:
    src = f.read()

initial_routes = src.count('@app.route')
backup_path = f"{APP}.bak.batch2c_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}\n")

APPLIED = []
FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("[1/6] Remove 4 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = ['/accounts/integrity', '/accounts/trial-balance',
             '/bookkeeping/anomaly-scan', '/bookkeeping/duplicate-check']

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
print("\n[2/6] Add /accounts/health route + 4 redirects")
# ═══════════════════════════════════════════════════════════════════

NEW_ROUTES = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 2c — Books Health (consolidated from 4 disabled routes)
# ═══════════════════════════════════════════════════════════════════════

_bind_module('accounts',
    'accounts_health',
    'redirect_trial_balance', 'redirect_accounts_integrity',
    'redirect_bookkeeping_anomaly', 'redirect_bookkeeping_duplicates')


@app.route('/accounts/health')
@login_required
def accounts_health():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    # ── Trial balance ────────────────────────────────────
    cur.execute("""
        SELECT account,
               COALESCE(SUM(debit),0) AS dr,
               COALESCE(SUM(credit),0) AS cr
        FROM journal_entries
        WHERE user_id=%s
        GROUP BY account
        ORDER BY account
    """, (uid,))
    tb_rows = []
    for r in (cur.fetchall() or []):
        tb_rows.append({
            'account': r.get('account') or '—',
            'dr': float(r.get('dr') or 0),
            'cr': float(r.get('cr') or 0),
            'net': float(r.get('dr') or 0) - float(r.get('cr') or 0),
        })
    tb_total_dr = sum(x['dr'] for x in tb_rows)
    tb_total_cr = sum(x['cr'] for x in tb_rows)
    tb_balanced = abs(tb_total_dr - tb_total_cr) < 0.01

    # ── Integrity per book ───────────────────────────────
    cur.execute("""
        SELECT book,
               COALESCE(SUM(debit),0) AS dr,
               COALESCE(SUM(credit),0) AS cr,
               COALESCE(SUM(debit),0) - COALESCE(SUM(credit),0) AS delta,
               COUNT(*) AS n
        FROM journal_entries
        WHERE user_id=%s
        GROUP BY book
        ORDER BY book
    """, (uid,))
    integrity_rows = []
    for r in (cur.fetchall() or []):
        delta = float(r.get('delta') or 0)
        integrity_rows.append({
            'book': (r.get('book') or '—').replace('_', ' ').title(),
            'dr': float(r.get('dr') or 0),
            'cr': float(r.get('cr') or 0),
            'delta': delta,
            'entries': int(r.get('n') or 0),
            'balanced': abs(delta) < 0.01,
        })
    integrity_failures = sum(1 for x in integrity_rows if not x['balanced'])

    # ── Anomaly scan (cash book, 30d, > 3x median) ───────
    cur.execute("""
        WITH stats AS (
            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS med,
                   COUNT(*) AS n
            FROM cash_books
            WHERE user_id=%s
              AND date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')
        )
        SELECT cb.entry_type, cb.category, cb.description,
               cb.amount, cb.date
        FROM cash_books cb, stats
        WHERE cb.user_id=%s
          AND cb.date >= to_char(CURRENT_DATE - INTERVAL '30 days','YYYY-MM-DD')
          AND stats.n >= 5
          AND cb.amount > 3 * stats.med
        ORDER BY cb.amount DESC
        LIMIT 25
    """, (uid, uid))
    anomaly_rows = []
    for r in (cur.fetchall() or []):
        anomaly_rows.append({
            'type': (r.get('entry_type') or '').upper(),
            'category': r.get('category') or '—',
            'description': r.get('description') or '—',
            'amount': float(r.get('amount') or 0),
            'date': r.get('date') or '—',
        })

    # ── Duplicate bookkeeping docs ───────────────────────
    cur.execute("""
        SELECT kind, party, doc_date, amount,
               COUNT(*) AS n,
               STRING_AGG(id::text, ',' ORDER BY id) AS ids
        FROM bookkeeping_docs
        WHERE user_id=%s
        GROUP BY kind, party, doc_date, amount
        HAVING COUNT(*) > 1
        ORDER BY n DESC, doc_date DESC
        LIMIT 20
    """, (uid,))
    duplicate_rows = []
    for r in (cur.fetchall() or []):
        duplicate_rows.append({
            'kind': (r.get('kind') or '').replace('_', ' ').title(),
            'party': r.get('party') or '—',
            'date': r.get('doc_date') or '—',
            'amount': float(r.get('amount') or 0),
            'count': int(r.get('n') or 0),
            'ids': r.get('ids') or '',
        })

    # Top-of-page stats
    cur.execute("SELECT COUNT(*) AS n FROM journal_entries WHERE user_id=%s", (uid,))
    total_entries = int((cur.fetchone() or {}).get('n') or 0)
    cur.execute("SELECT COUNT(*) AS n FROM bookkeeping_docs WHERE user_id=%s", (uid,))
    total_docs = int((cur.fetchone() or {}).get('n') or 0)

    cur.close(); conn.close()

    return render_template('accounts_health.html',
        tb_rows=tb_rows,
        tb_total_dr=tb_total_dr,
        tb_total_cr=tb_total_cr,
        tb_balanced=tb_balanced,
        integrity_rows=integrity_rows,
        integrity_failures=integrity_failures,
        anomaly_rows=anomaly_rows,
        duplicate_rows=duplicate_rows,
        total_entries=total_entries,
        total_docs=total_docs,
    )


@app.route('/accounts/trial-balance')
@login_required
def redirect_trial_balance():
    return redirect(url_for('accounts_health') + '#trialbalance', code=301)


@app.route('/accounts/integrity')
@login_required
def redirect_accounts_integrity():
    return redirect(url_for('accounts_health') + '#integrity', code=301)


@app.route('/bookkeeping/anomaly-scan')
@login_required
def redirect_bookkeeping_anomaly():
    return redirect(url_for('accounts_health') + '#anomaly', code=301)


@app.route('/bookkeeping/duplicate-check')
@login_required
def redirect_bookkeeping_duplicates():
    return redirect(url_for('accounts_health') + '#duplicate', code=301)

'''

if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + NEW_ROUTES + '\n' + src[idx:]
else:
    src += '\n' + NEW_ROUTES
print("  [OK]   inserted /accounts/health + 4 redirects")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/6] Add Books health to NAV")
# ═══════════════════════════════════════════════════════════════════

NAV_ANCHOR = "        ('Inventory analytics', 'stock_analytics', 'package-search', 'stock', ('stock_analytics',)),"
NAV_NEW = """        ('Inventory analytics', 'stock_analytics', 'package-search', 'stock', ('stock_analytics',)),
        ('Books health', 'accounts_health', 'book-open-check', 'accounts', ('accounts_health',)),"""

if NAV_ANCHOR in src:
    src = src.replace(NAV_ANCHOR, NAV_NEW, 1)
    print("  [OK]   Books health added to Analytics nav")
    APPLIED.append("nav")
else:
    print("  [FAIL] nav anchor not found (Inventory analytics entry)")
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
{% block title %}Books Health{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="book-open-check"></i> Books Health</h1>
    <p>Trial balance, journal integrity, anomaly scan, and duplicate document check — all in one place.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Journal entries</span><strong>{{ total_entries }}</strong></div>
  <div class="stat-chip"><span>Bookkeeping docs</span><strong>{{ total_docs }}</strong></div>
  <div class="stat-chip"><span>Trial balance</span>
    <strong style="color:{% if tb_balanced %}var(--green){% else %}#e74c3c{% endif %};">
      {{ 'Balanced' if tb_balanced else 'Off by ' + money(tb_total_dr - tb_total_cr) }}
    </strong>
  </div>
  <div class="stat-chip"><span>Integrity issues</span>
    <strong style="color:{% if integrity_failures %} #e74c3c {% else %}var(--green){% endif %};">
      {{ integrity_failures }}
    </strong>
  </div>
  <div class="stat-chip"><span>Anomalies</span><strong>{{ anomaly_rows|length }}</strong></div>
  <div class="stat-chip"><span>Duplicates</span><strong>{{ duplicate_rows|length }}</strong></div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="trialbalance" class="is-on">Trial balance</button>
  <button type="button" data-tab="integrity">Integrity</button>
  <button type="button" data-tab="anomaly">Anomaly scan</button>
  <button type="button" data-tab="duplicate">Duplicates</button>
</nav>

<section class="analytics-panel is-on" id="panel-trialbalance">
  {% if tb_rows %}
  <h2>Trial balance (typed journal entries)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Account totals from manually typed journal entries. Auto-posted entries (sales journal, purchases journal) are not shown here — those are computed on the Account tracking page.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Account</th><th style="text-align:right;">Debit</th><th style="text-align:right;">Credit</th><th style="text-align:right;">Net (DR−CR)</th></tr></thead>
      <tbody>
      {% for r in tb_rows %}
      <tr>
        <td>{{ r.account }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.dr) }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.cr) }}</td>
        <td style="text-align:right;font-family:var(--mono);{% if r.net > 0 %}color:var(--green);{% elif r.net < 0 %}color:#e74c3c;{% endif %}">{{ money(r.net) }}</td>
      </tr>
      {% endfor %}
      </tbody>
      <tfoot style="background:var(--surface2);font-weight:700;">
        <tr>
          <td>Total</td>
          <td style="text-align:right;font-family:var(--mono);">{{ money(tb_total_dr) }}</td>
          <td style="text-align:right;font-family:var(--mono);">{{ money(tb_total_cr) }}</td>
          <td style="text-align:right;font-family:var(--mono);{% if not tb_balanced %}color:#e74c3c;{% endif %}">{{ money(tb_total_dr - tb_total_cr) }}</td>
        </tr>
      </tfoot>
    </table>
  </div>
  {% if not tb_balanced %}
  <div class="widget" style="border-color:#e74c3c;background:rgba(231,76,60,0.06);">
    <strong style="color:#e74c3c;">Trial balance does not balance.</strong>
    <p style="margin:0.35rem 0 0;color:var(--text2);">
      Total debits ({{ money(tb_total_dr) }}) minus total credits ({{ money(tb_total_cr) }}) = {{ money(tb_total_dr - tb_total_cr) }}.
      A real double-entry book must balance to zero. Check for mis-typed entries or missing counterparties.
    </p>
  </div>
  {% endif %}
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No journal entries yet. Open <a href="{{ url_for('accounts') }}">Account tracking</a> to add double-entry lines.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-integrity">
  {% if integrity_rows %}
  <h2>Journal integrity (per book)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Each journal should net to zero (DR = CR). A non-zero delta means an entry was saved without its counterparty — that's a data error to fix.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Book</th><th>Entries</th><th style="text-align:right;">DR</th><th style="text-align:right;">CR</th><th style="text-align:right;">Delta</th><th>Status</th></tr></thead>
      <tbody>
      {% for r in integrity_rows %}
      <tr {% if not r.balanced %}style="background:var(--danger-dim);"{% endif %}>
        <td>{{ r.book }}</td>
        <td>{{ r.entries }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.dr) }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.cr) }}</td>
        <td style="text-align:right;font-family:var(--mono);{% if not r.balanced %}color:#e74c3c;font-weight:700;{% endif %}">{{ money(r.delta) }}</td>
        <td>{% if r.balanced %}<span class="status-pill status-ok">Balanced</span>{% else %}<span class="status-pill status-warn" style="background:var(--danger-dim);color:#e74c3c;">Off</span>{% endif %}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No journal entries to check yet.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-anomaly">
  {% if anomaly_rows %}
  <h2>Anomaly scan (cash book, last 30 days)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Cash entries larger than 3× the median cash entry from the last 30 days. Usually indicates a typo or an unusual expense worth reviewing.
    (Requires at least 5 cash entries in the last 30 days to be meaningful.)
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Date</th><th>Type</th><th>Category</th><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
      <tbody>
      {% for r in anomaly_rows %}
      <tr {% if r.type == 'OUT' %}style="background:rgba(231,76,60,0.06);"{% endif %}>
        <td>{{ r.date }}</td>
        <td>{{ r.type }}</td>
        <td>{{ r.category }}</td>
        <td>{{ r.description }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.amount) }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No anomalies detected — or fewer than 5 cash entries in the last 30 days to compare against. Nothing suspicious right now.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-duplicate">
  {% if duplicate_rows %}
  <h2>Suspected duplicate documents</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Bookkeeping documents where kind, party, date, and amount are identical across 2 or more rows. Usually means a save was clicked twice, or a paper was entered twice.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Kind</th><th>Party</th><th>Date</th><th style="text-align:right;">Amount</th><th>Copies</th><th>IDs</th></tr></thead>
      <tbody>
      {% for r in duplicate_rows %}
      <tr style="background:rgba(224,160,48,0.08);">
        <td>{{ r.kind }}</td>
        <td>{{ r.party }}</td>
        <td>{{ r.date }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.amount) }}</td>
        <td><strong>{{ r.count }}</strong></td>
        <td style="font-size:0.8rem;color:var(--text3);">#{{ r.ids }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  <p style="font-size:0.85rem;color:var(--text3);margin-top:0.75rem;">Open <a href="{{ url_for('bookkeeping') }}">Book keeping</a> to review or delete duplicates.</p>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No duplicate bookkeeping documents detected. Your entries look unique.</p></div>
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
  if (['trialbalance','integrity','anomaly','duplicate'].includes(hash)) {
    activate(hash);
  }
})();
</script>
{% endblock %}
'''

with open('templates/accounts_health.html', 'w', encoding='utf-8') as f:
    f.write(TPL)
print("  [OK]   templates/accounts_health.html")

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
print(f"  Removed from disabled:  {removed}/4")
print(f"  New routes added:        5 (1 page + 4 redirects)")
print(f"  New templates:           1")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 4 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 2c complete.

NEXT STEPS:

1. LOCAL TEST — run:  python app.py
   Visit:

     /accounts/health        -> 4 tabs (Trial balance / Integrity / Anomaly / Duplicates)
                                Click each. Some may show "no data yet" if you
                                haven't used that feature.
     /accounts/trial-balance -> 301 redirect to /accounts/health#trialbalance
     /accounts/integrity     -> 301 redirect to /accounts/health#integrity
     /bookkeeping/anomaly-scan -> 301 redirect to /accounts/health#anomaly
     /bookkeeping/duplicate-check -> 301 redirect to /accounts/health#duplicate

   Sidebar: Analytics section should now have 4 entries
            (Sales, Customer, Inventory, Books health).

   Regular usage: /dashboard, /plans (still shows Active — renews 2027-10-26),
                  /sales/analytics, /customers/analytics, /stock/analytics
                  all still work. No 500s.

2. COMMIT AND DEPLOY:

   git add app.py kaze_batch2c_books.py templates/accounts_health.html
   git commit -m "Batch 2c: books health (trial balance, integrity, anomaly, duplicates)"
   git push

3. Watch Render deploy. Re-test the same URLs on production.

4. Clean up:  rm app.py.bak.batch2c_*

NOTE — /payments/fees is NOT in this batch. It's deferred to a future
batch that adds stripe_fee tracking properly. It remains showing
"coming soon" for now.

Report back:
  Local: /accounts/health OK?  All 4 tabs render?  4 redirects work?
         Sidebar has 4 analytics entries?  Regular usage works?
  Deployed: hash, prod test results.
""")