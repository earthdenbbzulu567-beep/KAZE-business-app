"""
kaze_batch2g_fold.py — Batch 2g.

Folds 5 disabled routes into 3 existing pages + 1 new page:

  /rfm/actions          -> adds "Segment actions" to /rfm template
  /investments/risk     -> adds "Portfolio risk" to /investments template
  /day-close/variance   -> redirect to /tools/day-close (variance already shown)
  /services/utilization -> /services/analytics#utilization (new page)
  /services/yield       -> /services/analytics#yield

Uses Jinja template_globals for the /rfm and /investments additions so
existing route functions are not modified.

Verifies: NEW_ROUTES compiles as Python; all template edits parse as Jinja.

Run from the folder with app.py:
    python kaze_batch2g_fold.py
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
TPL_DIR = 'templates'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

with open(APP, encoding='utf-8') as f:
    src = f.read()

initial_routes = src.count('@app.route')
backup_path = f"{APP}.bak.batch2g_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}")

# Backup the templates we'll modify
for tpl in ('rfm.html', 'investments.html'):
    p = os.path.join(TPL_DIR, tpl)
    if os.path.isfile(p):
        shutil.copy2(p, p + f'.bak.batch2g_{STAMP}')
        print(f"Backup: {p}.bak.batch2g_{STAMP}")

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/8] Remove 5 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = [
    '/rfm/actions',
    '/day-close/variance',
    '/investments/risk',
    '/services/utilization',
    '/services/yield',
]

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
print("\n[2/8] Add template_globals + /services/analytics + 5 redirects")
# ═══════════════════════════════════════════════════════════════════

NEW_PY = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 2g — Folds & Services Analytics
# ═══════════════════════════════════════════════════════════════════════

@app.template_global()
def rfm_segment_actions(groups, segment_order):
    """Computed actions per RFM segment based on group sizes.
    Called from rfm.html. No route changes needed."""
    try:
        if not groups or not segment_order:
            return []
        counts = {s: len(groups.get(s, []) or []) for s in segment_order}
        actions = []
        if counts.get('Champion', 0) > 0:
            actions.append({
                'segment': 'Champion', 'count': counts['Champion'],
                'title': 'Thank and ask',
                'detail': 'Personally thank these customers. Ask for referrals or testimonials — happy champions convert at the highest rate.',
            })
        if counts.get('Loyal', 0) > 0:
            actions.append({
                'segment': 'Loyal', 'count': counts['Loyal'],
                'title': 'Nudge to Champion',
                'detail': 'Offer a bundle, upgrade, or premium tier. They buy regularly — a small upsell is likely to land.',
            })
        if counts.get('New', 0) > 0:
            actions.append({
                'segment': 'New', 'count': counts['New'],
                'title': 'Welcome and follow up',
                'detail': 'First purchase in the last few days. Check in. A good second experience locks them in.',
            })
        if counts.get('At Risk', 0) > 0:
            actions.append({
                'segment': 'At Risk', 'count': counts['At Risk'],
                'title': 'Re-engagement offer',
                'detail': 'Were repeat buyers, now slowed. Send a discount or personal reminder. Recovery is cheaper than acquisition.',
            })
        if counts.get('Needs Attention', 0) > 0:
            actions.append({
                'segment': 'Needs Attention', 'count': counts['Needs Attention'],
                'title': 'Check in',
                'detail': 'Buying occasionally but fading. A small offer or message may reactivate them.',
            })
        if counts.get('Lost', 0) > 0:
            actions.append({
                'segment': 'Lost', 'count': counts['Lost'],
                'title': 'Decide: win back or let go',
                'detail': 'No purchase in 90+ days. A win-back campaign may work for a few. Otherwise focus on the rest.',
            })
        return actions
    except Exception:
        return []


@app.template_global()
def portfolio_risk_metrics(holdings):
    """Portfolio concentration + diversification from holdings list.
    Called from investments.html. No route changes needed."""
    try:
        if not holdings:
            return {'has_data': False, 'message': 'Add at least one holding to see portfolio risk.'}
        total_value = sum(float(h.get('value') or 0) for h in holdings)
        if total_value <= 0:
            return {'has_data': False, 'message': 'Holdings have zero current value.'}
        weights = [float(h.get('value') or 0) / total_value for h in holdings]
        top_weight = max(weights)
        top_holding = holdings[weights.index(top_weight)]
        hhi = sum(w * w for w in weights)
        n = len(holdings)
        if n == 1:
            div_score = 0.0
        else:
            div_score = round(max(0, min(100, (1 - hhi) / (1 - 1/n) * 100)), 1)
        if top_weight >= 0.6:
            risk, risk_label = 'high', 'High concentration'
        elif top_weight >= 0.4:
            risk, risk_label = 'medium', 'Moderate concentration'
        else:
            risk, risk_label = 'low', 'Well diversified'
        return {
            'has_data': True,
            'total_value': total_value,
            'top_pct': round(top_weight * 100, 1),
            'top_name': top_holding.get('name') or 'Holding',
            'hhi': round(hhi, 3),
            'diversification_score': div_score,
            'risk': risk,
            'risk_label': risk_label,
            'count': n,
        }
    except Exception:
        return {'has_data': False, 'message': 'Could not compute portfolio risk.'}


@app.route('/services/analytics')
@login_required
def services_analytics():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT sv.id, sv.name, sv.price, sv.duration_minutes,
               COUNT(ss.id) AS sessions_booked,
               COALESCE(SUM(CASE WHEN ss.status='done' THEN 1 ELSE 0 END), 0) AS sessions_done,
               COALESCE(SUM(CASE WHEN ss.status='cancelled' THEN 1 ELSE 0 END), 0) AS sessions_cancelled,
               COALESCE(SUM(CASE WHEN ss.status='done' THEN ss.price ELSE 0 END), 0) AS revenue
        FROM services sv
        LEFT JOIN service_sessions ss ON ss.service_id = sv.id AND ss.user_id = sv.user_id
        WHERE sv.user_id = %s
        GROUP BY sv.id, sv.name, sv.price, sv.duration_minutes
        ORDER BY revenue DESC, sessions_booked DESC
    """, (uid,))
    util_rows = []
    for r in (cur.fetchall() or []):
        booked = int(r.get('sessions_booked') or 0)
        done = int(r.get('sessions_done') or 0)
        cancelled = int(r.get('sessions_cancelled') or 0)
        hours = float(r.get('duration_minutes') or 60) / 60.0
        revenue = float(r.get('revenue') or 0)
        util_pct = round(done / booked * 100, 1) if booked > 0 else 0.0
        rev_per_hour = round(revenue / (done * hours), 2) if (done > 0 and hours > 0) else 0.0
        util_rows.append({
            'name': r.get('name') or '—',
            'price': float(r.get('price') or 0),
            'duration': int(r.get('duration_minutes') or 60),
            'booked': booked,
            'done': done,
            'cancelled': cancelled,
            'revenue': revenue,
            'util_pct': util_pct,
            'rev_per_hour': rev_per_hour,
        })
    total_booked = sum(x['booked'] for x in util_rows)
    total_done = sum(x['done'] for x in util_rows)
    total_revenue = sum(x['revenue'] for x in util_rows)
    overall_util = round(total_done / total_booked * 100, 1) if total_booked > 0 else 0.0
    cur.close(); conn.close()
    return render_template('services_analytics.html',
        util_rows=util_rows,
        total_booked=total_booked,
        total_done=total_done,
        total_revenue=total_revenue,
        overall_util=overall_util,
    )


# Redirects
@app.route('/rfm/actions')
@login_required
def redirect_rfm_actions():
    return redirect(url_for('rfm') + '#actions', code=301)


@app.route('/day-close/variance')
@login_required
def redirect_day_close_variance():
    return redirect(url_for('day_close'), code=301)


@app.route('/investments/risk')
@login_required
def redirect_investments_risk():
    return redirect(url_for('investments') + '#risk', code=301)


@app.route('/services/utilization')
@login_required
def redirect_services_utilization():
    return redirect(url_for('services_analytics') + '#utilization', code=301)


@app.route('/services/yield')
@login_required
def redirect_services_yield():
    return redirect(url_for('services_analytics') + '#yield', code=301)

'''

# ── VERIFY: compile NEW_PY before writing ────────────────────────
print("\n[VERIFY] Compiling NEW_PY block before writing to app.py...")
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

# Insert into src
if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + NEW_PY + '\n' + src[idx:]
else:
    src += '\n' + NEW_PY
print("  [OK]   inserted template_globals + /services/analytics + 5 redirects")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/8] Add Services analytics to NAV")
# ═══════════════════════════════════════════════════════════════════

NAV_ANCHOR = "        ('Workflow signals', 'workflow_signals', 'check-square', 'workspace', ('workflow_signals',)),"
NAV_NEW = """        ('Workflow signals', 'workflow_signals', 'check-square', 'workspace', ('workflow_signals',)),
        ('Services analytics', 'services_analytics', 'graduation-cap', 'services', ('services_analytics',)),"""

if NAV_ANCHOR in src:
    src = src.replace(NAV_ANCHOR, NAV_NEW, 1)
    print("  [OK]   Services analytics added to Analytics nav")
else:
    print("  [FAIL] nav anchor not found (Workflow signals entry)")
    FAILED.append("nav")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/8] Write app.py")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   {initial_routes} -> {final_routes} @app.route (+{final_routes - initial_routes})")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/8] Modify rfm.html — add Segment actions section")
# ═══════════════════════════════════════════════════════════════════

RFM_SECTION = '''
<h2 id="actions" style="margin-top:2rem;">Segment actions</h2>
<p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
  Suggested next step for each segment you currently have customers in.
</p>
{% set segment_actions = rfm_segment_actions(groups, segment_order) %}
{% if segment_actions %}
  {% for a in segment_actions %}
  <div class="widget" style="border-left:4px solid {% if a.segment == 'Champion' %}var(--green){% elif a.segment == 'Loyal' %}#3498db{% elif a.segment == 'New' %}#9b59b6{% elif a.segment == 'At Risk' %}#e0a030{% elif a.segment == 'Needs Attention' %}#e67e22{% else %}#e74c3c{% endif %};">
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:1rem;flex-wrap:wrap;">
      <div>
        <strong style="font-size:1.05rem;">{{ a.title }}</strong>
        <span class="status-pill" style="margin-left:0.4rem;background:var(--surface2);color:var(--text2);">{{ a.segment }} · {{ a.count }} customer{{ '' if a.count == 1 else 's' }}</span>
      </div>
    </div>
    <p style="margin:0.5rem 0 0;font-size:0.9rem;color:var(--text2);">{{ a.detail }}</p>
  </div>
  {% endfor %}
{% else %}
  <div class="widget"><p style="color:var(--text3);">No customers segmented yet. Segment actions appear once you have customers with sales history.</p></div>
{% endif %}
'''

rfm_path = os.path.join(TPL_DIR, 'rfm.html')
if not os.path.isfile(rfm_path):
    print(f"  [FAIL] {rfm_path} not found")
    FAILED.append("rfm.html")
else:
    with open(rfm_path, encoding='utf-8') as f:
        rfm_content = f.read()
    # Insert before the LAST {% endblock %}
    parts = rfm_content.rsplit('{% endblock %}', 1)
    if len(parts) != 2:
        print("  [FAIL] rfm.html has no {% endblock %} — cannot insert safely")
        FAILED.append("rfm.html endblock")
    else:
        # Verify the section parses as Jinja before writing
        try:
            from jinja2 import Environment
            Environment().parse(RFM_SECTION)
        except Exception as exc:
            print(f"  [FAIL] RFM section has Jinja syntax error: {exc}")
            FAILED.append("rfm section jinja")
        else:
            new_rfm = parts[0] + RFM_SECTION + '{% endblock %}' + parts[1]
            with open(rfm_path, 'w', encoding='utf-8') as f:
                f.write(new_rfm)
            print("  [OK]   rfm.html — Segment actions section added")

# ═══════════════════════════════════════════════════════════════════
print("\n[6/8] Modify investments.html — add Portfolio risk section")
# ═══════════════════════════════════════════════════════════════════

INVEST_SECTION = '''
<h2 id="risk" style="margin-top:2rem;">Portfolio risk</h2>
{% set risk = portfolio_risk_metrics(holdings) %}
{% if risk.has_data %}
<div class="stat-grid" style="margin:0.5rem 0 1rem;">
  <div class="stat-chip">
    <span>Concentration</span>
    <strong style="color:{% if risk.risk == 'high' %}#e74c3c{% elif risk.risk == 'medium' %}#e0a030{% else %}var(--green){% endif %};">
      {{ risk.top_pct }}%
    </strong>
    <small style="display:block;color:var(--text3);font-size:0.75rem;">top holding = {{ risk.top_name }}</small>
  </div>
  <div class="stat-chip">
    <span>Diversification</span>
    <strong>{{ risk.diversification_score }}/100</strong>
    <small style="display:block;color:var(--text3);font-size:0.75rem;">{{ risk.count }} holding{{ '' if risk.count == 1 else 's' }}</small>
  </div>
  <div class="stat-chip">
    <span>Risk level</span>
    <strong style="color:{% if risk.risk == 'high' %}#e74c3c{% elif risk.risk == 'medium' %}#e0a030{% else %}var(--green){% endif %};">
      {{ risk.risk_label }}
    </strong>
  </div>
</div>
<div class="widget">
  <p style="color:var(--text2);font-size:0.9rem;margin:0;">
    {% if risk.risk == 'high' %}
    <strong style="color:#e74c3c;">Concentration is high.</strong>
    Over {{ risk.top_pct }}% of portfolio value is in one holding. If that holding underperforms, most of your portfolio feels it. Consider spreading future investment across more assets.
    {% elif risk.risk == 'medium' %}
    <strong style="color:#e0a030;">Moderate concentration.</strong>
    {{ risk.top_pct }}% of value in {{ risk.top_name }}. Reasonable, but there's room to diversify further.
    {% else %}
    <strong style="color:var(--green);">Well diversified.</strong>
    No single holding dominates. This is a healthy allocation.
    {% endif %}
    (Herfindahl index: {{ risk.hhi }} — lower is more diversified.)
  </p>
</div>
{% else %}
<div class="widget"><p style="color:var(--text3);">{{ risk.message }}</p></div>
{% endif %}
'''

inv_path = os.path.join(TPL_DIR, 'investments.html')
if not os.path.isfile(inv_path):
    print(f"  [FAIL] {inv_path} not found")
    FAILED.append("investments.html")
else:
    with open(inv_path, encoding='utf-8') as f:
        inv_content = f.read()
    parts = inv_content.rsplit('{% endblock %}', 1)
    if len(parts) != 2:
        print("  [FAIL] investments.html has no {% endblock %}")
        FAILED.append("investments.html endblock")
    else:
        try:
            from jinja2 import Environment
            Environment().parse(INVEST_SECTION)
        except Exception as exc:
            print(f"  [FAIL] Invest section has Jinja syntax error: {exc}")
            FAILED.append("invest section jinja")
        else:
            new_inv = parts[0] + INVEST_SECTION + '{% endblock %}' + parts[1]
            with open(inv_path, 'w', encoding='utf-8') as f:
                f.write(new_inv)
            print("  [OK]   investments.html — Portfolio risk section added")

# ═══════════════════════════════════════════════════════════════════
print("\n[7/8] Write services_analytics.html (new template)")
# ═══════════════════════════════════════════════════════════════════

SERVICES_TPL = '''{% extends "base.html" %}
{% block title %}Services Analytics{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="graduation-cap"></i> Services Analytics</h1>
    <p>How your services perform: utilization (booked vs completed) and yield (revenue per hour).</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Sessions booked</span><strong>{{ total_booked }}</strong></div>
  <div class="stat-chip"><span>Sessions completed</span><strong>{{ total_done }}</strong></div>
  <div class="stat-chip"><span>Overall utilization</span><strong>{{ overall_util }}%</strong></div>
  <div class="stat-chip"><span>Total service revenue</span><strong>{{ money(total_revenue) }}</strong></div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="utilization" class="is-on">Utilization</button>
  <button type="button" data-tab="yield">Yield</button>
</nav>

<section class="analytics-panel is-on" id="panel-utilization">
  <h2>Service utilization</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Booked vs completed vs cancelled, per service. Low utilization on a popular service often means cancellations or no-shows; low booked across all services means you need more demand.
  </p>
  {% if util_rows %}
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Service</th><th style="text-align:right;">Booked</th><th style="text-align:right;">Done</th><th style="text-align:right;">Cancelled</th><th style="text-align:right;">Util %</th></tr></thead>
      <tbody>
      {% for r in util_rows %}
      <tr {% if r.util_pct >= 80 %}style="background:var(--green-dim);"{% elif r.util_pct < 40 and r.booked > 0 %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td>{{ r.name }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ r.booked }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ r.done }}</td>
        <td style="text-align:right;font-family:var(--mono);{% if r.cancelled > 0 %}color:#e74c3c;{% endif %}">{{ r.cancelled }}</td>
        <td style="text-align:right;font-family:var(--mono);font-weight:700;">{{ r.util_pct }}%</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No services yet. Add services on the <a href="{{ url_for('services') }}">Services</a> page.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-yield">
  <h2>Service yield</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Revenue per completed hour. Higher yield means better use of your time — worth prioritising these services.
  </p>
  {% if util_rows %}
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Service</th><th style="text-align:right;">Duration</th><th style="text-align:right;">Price</th><th style="text-align:right;">Revenue</th><th style="text-align:right;">Rev/hour</th></tr></thead>
      <tbody>
      {% for r in util_rows %}
      <tr>
        <td>{{ r.name }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ r.duration }}m</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.price) }}</td>
        <td style="text-align:right;font-family:var(--mono);">{{ money(r.revenue) }}</td>
        <td style="text-align:right;font-family:var(--mono);font-weight:700;">{{ money(r.rev_per_hour) }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No services yet to compare yield.</p></div>
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
  if (['utilization','yield'].includes(hash)) {
    activate(hash);
  }
})();
</script>
{% endblock %}
'''

# Verify Jinja parse before writing
try:
    from jinja2 import Environment
    Environment().parse(SERVICES_TPL)
except Exception as exc:
    print(f"  [FAIL] services_analytics.html has Jinja syntax error: {exc}")
    FAILED.append("services_analytics jinja")
else:
    with open(os.path.join(TPL_DIR, 'services_analytics.html'), 'w', encoding='utf-8') as f:
        f.write(SERVICES_TPL)
    print("  [OK]   templates/services_analytics.html")

# ═══════════════════════════════════════════════════════════════════
print("\n[8/8] Compile check app.py")
# ═══════════════════════════════════════════════════════════════════

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
print(f"  Removed from disabled:  {removed}/5")
print(f"  New routes added:        6 (1 page + 5 redirects)")
print(f"  New template:            services_analytics.html")
print(f"  Modified templates:      rfm.html, investments.html")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 5 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    print(f"Restore templates: *bak.batch2g_{STAMP}")
    sys.exit(1)

print("""
Batch 2g complete.

NEXT STEPS:

1. LOCAL TEST — run:  python app.py
   (Verify $env:DATABASE_URL is set)

   NEW page:
     /services/analytics  -> 2 tabs (Utilization / Yield)
                             Both should show data if you have services

   MODIFIED pages:
     /rfm                 -> scroll down — new "Segment actions" section
                             below the RFM customer table
     /investments         -> scroll down — new "Portfolio risk" section
                             below the holdings table

   Redirects:
     /rfm/actions          -> /rfm#actions
     /day-close/variance   -> /tools/day-close
     /investments/risk     -> /investments#risk
     /services/utilization -> /services/analytics#utilization
     /services/yield       -> /services/analytics#yield

   Sidebar: Analytics now has 9 entries
            (added Services analytics).

   Regression — verify:
     /dashboard, /plans (Active), all analytics pages,
     /rfm (with new section, existing segments still work),
     /investments (with new section, holdings still work)

2. REPORT BACK:
   - /services/analytics 2 tabs?
   - /rfm shows Segment actions section?
   - /investments shows Portfolio risk section?
   - 5 redirects work?
   - Sidebar 9 entries?
   - Regression pass?

3. Only after I confirm, commit + push + deploy.

4. Test on production.

5. Only after prod pass:
     rm app.py.bak.batch2g_*
     rm templates/rfm.html.bak.batch2g_*
     rm templates/investments.html.bak.batch2g_*

REMAINING DISABLED ROUTES (9 — all schema-required, Batch 3):
  /health/history, /payments/fees,
  /whatsapp/log, /whatsapp/templates,
  /documents/approval, /documents/versions,
  /banking/reconcile, /tasks/blockers,
  /settings/audit
""")