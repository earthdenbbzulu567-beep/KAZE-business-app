"""
kaze_batch2f_workflow.py — Batch 2f.

Consolidates 9 disabled routes into 2 tabbed pages:
  /team/health        (permissions, activity, config audit)
  /workflow/signals   (task priority, note actions, reminder context,
                       reminder escalation, calendar conflicts, calendar free)

Includes built-in safety verification — aborts if generated code
does not compile before writing app.py.

Run from the folder with app.py:
    python kaze_batch2f_workflow.py
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
backup_path = f"{APP}.bak.batch2f_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}\n")

APPLIED = []
FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("[1/7] Remove 9 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = [
    '/team/permissions', '/team/activity',
    '/tasks/priority', '/notes/actions',
    '/reminders/context', '/reminders/escalation',
    '/calendar/conflicts', '/calendar/free',
    '/settings/health',
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
print("\n[2/7] Add /team/health + /workflow/signals + 9 redirects")
# ═══════════════════════════════════════════════════════════════════

NEW_ROUTES = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 2f — Team & Workflow (consolidated from 9 disabled routes)
# ═══════════════════════════════════════════════════════════════════════

_bind_module('workspace',
    'workflow_signals',
    'redirect_tasks_priority', 'redirect_notes_actions',
    'redirect_reminders_context', 'redirect_reminders_escalation',
    'redirect_calendar_conflicts', 'redirect_calendar_free')


@app.route('/team/health')
@login_required
def team_health():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()

    # ── Permissions ─────────────────────────────────────
    cur.execute("""
        SELECT id, username, email, role
        FROM users
        WHERE id=%s OR owner_id=%s
        ORDER BY CASE WHEN role='owner' THEN 0 ELSE 1 END, username
    """, (uid, uid))
    team_rows = []
    for r in (cur.fetchall() or []):
        role = (r.get('role') or 'staff').lower()
        is_owner = (role == 'owner')
        team_rows.append({
            'id': r.get('id'),
            'username': r.get('username') or '—',
            'email': r.get('email') or '—',
            'role': role,
            'is_owner': is_owner,
        })

    # ── Activity (recent 30 across account) ─────────────
    cur.execute("""
        SELECT username, action, details, created_at
        FROM activities
        WHERE user_id=%s
        ORDER BY created_at DESC
        LIMIT 30
    """, (uid,))
    activity_rows = []
    for r in (cur.fetchall() or []):
        activity_rows.append({
            'username': r.get('username') or '—',
            'action': r.get('action') or '—',
            'details': r.get('details') or '',
            'when': r.get('created_at') or '',
        })

    # ── Config audit ────────────────────────────────────
    cur.execute("""
        SELECT business_name, currency_code, currency_symbol, tax_rate,
               monthly_revenue_goal, low_stock_threshold,
               stripe_secret_key, stripe_webhook_secret
        FROM settings WHERE user_id=%s
    """, (uid,))
    s = cur.fetchone() or {}
    config_checks = [
        {'item': 'Business name',
         'status': 'ok' if (s.get('business_name') or '').strip() else 'warn',
         'detail': (s.get('business_name') or 'Not set — appears on PDF headers')},
        {'item': 'Currency code',
         'status': 'ok' if s.get('currency_code') else 'warn',
         'detail': str(s.get('currency_code') or 'Not set')},
        {'item': 'Currency symbol',
         'status': 'ok' if s.get('currency_symbol') else 'warn',
         'detail': str(s.get('currency_symbol') or 'Not set')},
        {'item': 'Low stock threshold',
         'status': 'ok' if float(s.get('low_stock_threshold') or 0) > 0 else 'warn',
         'detail': str(s.get('low_stock_threshold') or 0) + ' units'},
        {'item': 'Monthly revenue goal',
         'status': 'ok' if float(s.get('monthly_revenue_goal') or 0) > 0 else 'info',
         'detail': ('Goal = ' + str(s.get('monthly_revenue_goal'))) if float(s.get('monthly_revenue_goal') or 0) > 0 else 'Optional — enables goal tracking'},
        {'item': 'Tax rate',
         'status': 'info',
         'detail': str(s.get('tax_rate') or 0) + '% (0 means no tax applied)'},
        {'item': 'Stripe secret key',
         'status': 'ok' if s.get('stripe_secret_key') else 'warn',
         'detail': 'Configured' if s.get('stripe_secret_key') else 'Missing — subscriptions cannot start'},
        {'item': 'Stripe webhook secret',
         'status': 'ok' if s.get('stripe_webhook_secret') else 'warn',
         'detail': 'Configured' if s.get('stripe_webhook_secret') else 'Missing — payments will not activate'},
    ]

    cur.close(); conn.close()
    return render_template('team_health.html',
        team_rows=team_rows,
        activity_rows=activity_rows,
        config_checks=config_checks,
    )


@app.route('/workflow/signals')
@login_required
def workflow_signals():
    uid = current_user.id
    today_dt = datetime.today()
    today = today_dt.strftime('%Y-%m-%d')
    horizon_14 = (today_dt + timedelta(days=14)).strftime('%Y-%m-%d')
    horizon_30 = (today_dt + timedelta(days=30)).strftime('%Y-%m-%d')
    three_days = (today_dt + timedelta(days=3)).strftime('%Y-%m-%d')
    seven_days = (today_dt + timedelta(days=7)).strftime('%Y-%m-%d')

    conn = get_db(); cur = conn.cursor()

    # ── TAB 1: Task priority (scored) ───────────────────
    cur.execute("""
        SELECT id, title, priority, due_date, done
        FROM tasks WHERE user_id=%s AND done=0
    """, (uid,))
    priority_weight = {'high': 3, 'medium': 2, 'low': 1}
    task_rows = []
    for r in (cur.fetchall() or []):
        pw = priority_weight.get((r.get('priority') or 'medium').lower(), 2)
        due = (r.get('due_date') or '')[:10]
        if due and due < today:
            urgency, label = 3.0, 'Overdue'
        elif due == today:
            urgency, label = 3.0, 'Due today'
        elif due and due <= three_days:
            urgency, label = 2.0, 'Due in 3 days'
        elif due and due <= seven_days:
            urgency, label = 1.5, 'Due this week'
        else:
            urgency, label = 1.0, 'No rush'
        task_rows.append({
            'id': r.get('id'),
            'title': r.get('title') or '—',
            'priority': r.get('priority') or 'medium',
            'due_date': due or 'no due date',
            'urgency': label,
            'score': round(pw * urgency, 1),
        })
    task_rows.sort(key=lambda x: -x['score'])

    # ── TAB 2: Note actions (extract TODO / - [ ] lines) ─
    cur.execute("SELECT id, title, body, updated_date FROM notes WHERE user_id=%s", (uid,))
    note_actions = []
    for r in (cur.fetchall() or []):
        body = r.get('body') or ''
        for line in body.split('\\n'):
            stripped = line.strip()
            if not stripped:
                continue
            action_text = None
            if stripped.startswith('- [ ]') or stripped.startswith('* [ ]'):
                action_text = stripped[5:].strip()
            elif stripped.startswith('[ ]'):
                action_text = stripped[3:].strip()
            else:
                low = stripped.lower()
                if low.startswith('todo:'):
                    action_text = stripped[5:].strip()
                elif low.startswith('action:'):
                    action_text = stripped[7:].strip()
            if action_text and len(action_text) > 2:
                note_actions.append({
                    'note_id': r.get('id'),
                    'note_title': r.get('title') or 'Note',
                    'action': action_text,
                    'updated': r.get('updated_date') or '',
                })
    note_actions = note_actions[:40]

    # ── TAB 3: Reminder context (unified upcoming 14d) ──
    context_items = []
    cur.execute("""
        SELECT title, due_date, priority FROM tasks
        WHERE user_id=%s AND done=0 AND due_date != ''
          AND due_date >= %s AND due_date <= %s
    """, (uid, today, horizon_14))
    for r in (cur.fetchall() or []):
        context_items.append({
            'date': r.get('due_date'),
            'kind': 'Task',
            'label': r.get('title') or '—',
            'detail': r.get('priority') or 'medium',
        })
    cur.execute("""
        SELECT name, next_run_date, item_type, amount FROM recurring_items
        WHERE user_id=%s AND active=1
          AND next_run_date >= %s AND next_run_date <= %s
    """, (uid, today, horizon_14))
    for r in (cur.fetchall() or []):
        context_items.append({
            'date': r.get('next_run_date'),
            'kind': 'Recurring',
            'label': r.get('name') or '—',
            'detail': (r.get('item_type') or 'item') + ' · ' + _format_money(r.get('amount') or 0),
        })
    cur.execute("""
        SELECT item_description, expected_date, status FROM purchase_orders
        WHERE user_id=%s AND status != 'received'
          AND expected_date != '' AND expected_date >= %s AND expected_date <= %s
    """, (uid, today, horizon_14))
    for r in (cur.fetchall() or []):
        context_items.append({
            'date': r.get('expected_date'),
            'kind': 'Purchase order',
            'label': r.get('item_description') or '—',
            'detail': r.get('status') or 'pending',
        })
    context_items.sort(key=lambda x: x['date'] or '9999')

    # ── TAB 4: Reminder escalation (overdue) ────────────
    escalation_items = []
    cur.execute("""
        SELECT id, title, due_date, priority FROM tasks
        WHERE user_id=%s AND done=0 AND due_date != '' AND due_date < %s
    """, (uid, today))
    for r in (cur.fetchall() or []):
        due = (r.get('due_date') or '')[:10]
        try:
            days_over = (today_dt.date() - datetime.strptime(due, '%Y-%m-%d').date()).days
        except (ValueError, TypeError):
            days_over = 0
        escalation_items.append({
            'kind': 'Task', 'label': r.get('title') or '—',
            'due': due, 'days_overdue': days_over,
            'priority': r.get('priority') or 'medium',
            'severity': 'danger' if days_over >= 14 else 'warn' if days_over >= 3 else 'info',
        })
    cur.execute("""
        SELECT id, item_description, expected_date FROM purchase_orders
        WHERE user_id=%s AND status != 'received'
          AND expected_date != '' AND expected_date < %s
    """, (uid, today))
    for r in (cur.fetchall() or []):
        due = (r.get('expected_date') or '')[:10]
        try:
            days_over = (today_dt.date() - datetime.strptime(due, '%Y-%m-%d').date()).days
        except (ValueError, TypeError):
            days_over = 0
        escalation_items.append({
            'kind': 'PO', 'label': r.get('item_description') or '—',
            'due': due, 'days_overdue': days_over,
            'priority': 'medium',
            'severity': 'danger' if days_over >= 14 else 'warn' if days_over >= 3 else 'info',
        })
    escalation_items.sort(key=lambda x: -x['days_overdue'])

    # ── TAB 5+6: Calendar conflicts + free/busy (30d) ──
    cur.execute("""
        WITH dated_items AS (
            SELECT due_date AS item_date, 'Task' AS kind, title AS label
            FROM tasks WHERE user_id=%s AND done=0 AND due_date != ''
            UNION ALL
            SELECT expected_date, 'PO', item_description
            FROM purchase_orders WHERE user_id=%s AND status != 'received' AND expected_date != ''
            UNION ALL
            SELECT session_date, 'Service', customer_name
            FROM service_sessions WHERE user_id=%s AND status != 'cancelled'
        )
        SELECT item_date, kind, label FROM dated_items
        WHERE item_date >= %s AND item_date <= %s
        ORDER BY item_date, kind
    """, (uid, uid, uid, today, horizon_30))

    by_date = {}
    for r in (cur.fetchall() or []):
        d = r.get('item_date')
        if not d:
            continue
        by_date.setdefault(d, []).append({
            'kind': r.get('kind') or '?',
            'label': r.get('label') or '—',
        })

    conflict_rows = []
    for d in sorted(by_date.keys()):
        items = by_date[d]
        if len(items) >= 2:
            conflict_rows.append({
                'date': d, 'items': items, 'count': len(items),
            })

    calendar_days = []
    for i in range(30):
        d = (today_dt + timedelta(days=i)).strftime('%Y-%m-%d')
        n = len(by_date.get(d, []))
        calendar_days.append({'date': d, 'busy': n > 0, 'count': n})
    free_count = sum(1 for d in calendar_days if not d['busy'])
    busy_count = len(calendar_days) - free_count

    cur.close(); conn.close()

    return render_template('workflow_signals.html',
        task_rows=task_rows,
        note_actions=note_actions,
        context_items=context_items,
        escalation_items=escalation_items,
        conflict_rows=conflict_rows,
        calendar_days=calendar_days,
        free_count=free_count,
        busy_count=busy_count,
    )


@app.route('/team/permissions')
@login_required
def redirect_team_permissions():
    return redirect(url_for('team_health') + '#permissions', code=301)


@app.route('/team/activity')
@login_required
def redirect_team_activity():
    return redirect(url_for('team_health') + '#activity', code=301)


@app.route('/settings/health')
@login_required
def redirect_settings_health():
    return redirect(url_for('team_health') + '#config', code=301)


@app.route('/tasks/priority')
@login_required
def redirect_tasks_priority():
    return redirect(url_for('workflow_signals') + '#taskpriority', code=301)


@app.route('/notes/actions')
@login_required
def redirect_notes_actions():
    return redirect(url_for('workflow_signals') + '#noteactions', code=301)


@app.route('/reminders/context')
@login_required
def redirect_reminders_context():
    return redirect(url_for('workflow_signals') + '#context', code=301)


@app.route('/reminders/escalation')
@login_required
def redirect_reminders_escalation():
    return redirect(url_for('workflow_signals') + '#escalation', code=301)


@app.route('/calendar/conflicts')
@login_required
def redirect_calendar_conflicts():
    return redirect(url_for('workflow_signals') + '#conflicts', code=301)


@app.route('/calendar/free')
@login_required
def redirect_calendar_free():
    return redirect(url_for('workflow_signals') + '#calendar', code=301)

'''

# ── VERIFY: extract and compile NEW_ROUTES BEFORE writing ─────────
print("\n[VERIFY] Compiling NEW_ROUTES block before writing to app.py...")
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
    tmp.write(NEW_ROUTES)
    tmp_path = tmp.name
rc = subprocess.run([sys.executable, '-m', 'py_compile', tmp_path], capture_output=True, text=True)
os.unlink(tmp_path)
if rc.returncode != 0:
    print("  [FAIL] NEW_ROUTES does not compile:")
    print(rc.stderr)
    print(f"\n[ABORT] app.py untouched. Restore: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print(f"  [OK]   NEW_ROUTES compiles ({len(NEW_ROUTES):,} chars)")
print("  [OK]   No syntax errors in the code that will be inserted")

# Insert into src
if 'if __name__ == ' in src:
    idx = src.rfind('if __name__ == ')
    src = src[:idx] + NEW_ROUTES + '\n' + src[idx:]
else:
    src += '\n' + NEW_ROUTES
print("  [OK]   inserted both routes + 9 redirects")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/7] Add Team health + Workflow signals to NAV")
# ═══════════════════════════════════════════════════════════════════

NAV_ANCHOR = "        ('Patterns', 'analytics_patterns', 'activity', 'reports', ('analytics_patterns',)),"
NAV_NEW = """        ('Patterns', 'analytics_patterns', 'activity', 'reports', ('analytics_patterns',)),
        ('Team health', 'team_health', 'users-round', 'workspace', ('team_health',)),
        ('Workflow signals', 'workflow_signals', 'check-square', 'workspace', ('workflow_signals',)),"""

if NAV_ANCHOR in src:
    src = src.replace(NAV_ANCHOR, NAV_NEW, 1)
    print("  [OK]   Team health + Workflow signals added to Analytics nav")
else:
    print("  [FAIL] nav anchor not found (Patterns entry)")
    FAILED.append("nav")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/7] Write app.py")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   {initial_routes} -> {final_routes} @app.route (+{final_routes - initial_routes})")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/7] Write templates")
# ═══════════════════════════════════════════════════════════════════

os.makedirs('templates', exist_ok=True)

TEAM_TPL = '''{% extends "base.html" %}
{% block title %}Team Health{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="users-round"></i> Team Health</h1>
    <p>Team permissions, recent activity, and configuration audit.</p>
  </div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="permissions" class="is-on">Permissions</button>
  <button type="button" data-tab="activity">Activity</button>
  <button type="button" data-tab="config">Config audit</button>
</nav>

<section class="analytics-panel is-on" id="panel-permissions">
  <h2>Team members</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Owners can invite staff, clear data, and change settings. Staff can use every business feature but cannot manage the team or destroy data.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Username</th><th>Email</th><th>Role</th><th>Invite</th><th>Settings</th><th>Clear data</th></tr></thead>
      <tbody>
      {% for r in team_rows %}
      <tr>
        <td><strong>{{ r.username }}</strong></td>
        <td>{{ r.email }}</td>
        <td><span class="status-pill {% if r.is_owner %}status-ok{% else %}status-warn{% endif %}">{{ r.role | title }}</span></td>
        <td>{% if r.is_owner %}Yes{% else %}No{% endif %}</td>
        <td>{% if r.is_owner %}Yes{% else %}No{% endif %}</td>
        <td>{% if r.is_owner %}Yes{% else %}No{% endif %}</td>
      </tr>
      {% else %}
      <tr><td colspan="6">No team members.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<section class="analytics-panel" id="panel-activity">
  <h2>Recent activity</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Last 30 actions across the account. Every save, edit, and delete is logged here.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>User</th><th>Action</th><th>Details</th><th>When</th></tr></thead>
      <tbody>
      {% for r in activity_rows %}
      <tr>
        <td>{{ r.username }}</td>
        <td>{{ r.action }}</td>
        <td style="font-size:0.85rem;color:var(--text2);">{{ r.details }}</td>
        <td style="font-size:0.85rem;color:var(--text3);">{{ r.when }}</td>
      </tr>
      {% else %}
      <tr><td colspan="4">No activity yet.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<section class="analytics-panel" id="panel-config">
  <h2>Configuration audit</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Checks for the settings that affect invoicing, subscriptions, and goal tracking. <strong>Warn</strong> means something will fail silently if not fixed. <strong>Info</strong> is optional.
  </p>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Item</th><th>Status</th><th>Detail</th></tr></thead>
      <tbody>
      {% for r in config_checks %}
      <tr {% if r.status == 'warn' %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td>{{ r.item }}</td>
        <td>
          {% if r.status == 'ok' %}<span class="status-pill status-ok">OK</span>
          {% elif r.status == 'warn' %}<span class="status-pill" style="background:rgba(224,160,48,0.15);color:#e0a030;">Warn</span>
          {% else %}<span class="status-pill" style="background:var(--surface2);color:var(--text2);">Info</span>{% endif %}
        </td>
        <td style="font-size:0.88rem;color:var(--text2);">{{ r.detail }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
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
  if (['permissions','activity','config'].includes(hash)) {
    activate(hash);
  }
})();
</script>
{% endblock %}
'''

WORKFLOW_TPL = '''{% extends "base.html" %}
{% block title %}Workflow Signals{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="check-square"></i> Workflow Signals</h1>
    <p>Task priority, note actions, upcoming context, overdue escalations, and calendar load.</p>
  </div>
</div>

<nav class="analytics-tabs" role="tablist">
  <button type="button" data-tab="taskpriority" class="is-on">Task priority</button>
  <button type="button" data-tab="noteactions">Note actions</button>
  <button type="button" data-tab="context">Reminder context</button>
  <button type="button" data-tab="escalation">Escalation</button>
  <button type="button" data-tab="conflicts">Conflicts</button>
  <button type="button" data-tab="calandar">Free/busy</button>
</nav>

<section class="analytics-panel is-on" id="panel-taskpriority">
  <h2>Task priority (scored)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Open tasks ranked by priority × urgency. High-priority overdue tasks score highest. Work top to bottom for maximum effect.
  </p>
  {% if task_rows %}
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Task</th><th>Priority</th><th>Due</th><th>Urgency</th><th>Score</th></tr></thead>
      <tbody>
      {% for r in task_rows %}
      <tr {% if r.score >= 7 %}style="background:var(--danger-dim);"{% elif r.score >= 4 %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td><strong>{{ r.title }}</strong></td>
        <td>{{ r.priority }}</td>
        <td>{{ r.due_date }}</td>
        <td>{{ r.urgency }}</td>
        <td style="font-family:var(--mono);font-weight:700;">{{ r.score }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No open tasks. Nice.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-noteactions">
  <h2>Note actions</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Extracted from notes: lines starting with <code>- [ ]</code>, <code>[ ]</code>, <code>todo:</code>, or <code>action:</code>. Use these markers in your notes to make action items visible here.
  </p>
  {% if note_actions %}
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Note</th><th>Action</th><th>Updated</th></tr></thead>
      <tbody>
      {% for r in note_actions %}
      <tr>
        <td style="font-size:0.85rem;color:var(--text2);">{{ r.note_title }}</td>
        <td>{{ r.action }}</td>
        <td style="font-size:0.85rem;color:var(--text3);">{{ r.updated }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No action items found in notes. Start a line with <code>- [ ]</code> or <code>TODO:</code> to mark a task.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-context">
  <h2>Upcoming items (next 14 days)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Everything with a date in the next two weeks: tasks, recurring items, purchase orders. One list, sorted by date.
  </p>
  {% if context_items %}
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Date</th><th>Kind</th><th>Label</th><th>Detail</th></tr></thead>
      <tbody>
      {% for r in context_items %}
      <tr>
        <td>{{ r.date }}</td>
        <td><span class="status-pill">{{ r.kind }}</span></td>
        <td><strong>{{ r.label }}</strong></td>
        <td style="font-size:0.85rem;color:var(--text2);">{{ r.detail }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--text3);">Nothing scheduled in the next 14 days.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-escalation">
  <h2>Overdue escalations</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Tasks and purchase orders past their expected date. Red = 14+ days overdue, amber = 3-13 days.
  </p>
  {% if escalation_items %}
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Kind</th><th>Item</th><th>Due</th><th>Days overdue</th><th>Severity</th></tr></thead>
      <tbody>
      {% for r in escalation_items %}
      <tr {% if r.severity == 'danger' %}style="background:var(--danger-dim);"{% elif r.severity == 'warn' %}style="background:rgba(224,160,48,0.08);"{% endif %}>
        <td>{{ r.kind }}</td>
        <td><strong>{{ r.label }}</strong></td>
        <td>{{ r.due }}</td>
        <td style="font-family:var(--mono);font-weight:700;">{{ r.days_overdue }}d</td>
        <td>
          {% if r.severity == 'danger' %}<span class="status-pill" style="background:var(--danger-dim);color:#e74c3c;">Critical</span>
          {% elif r.severity == 'warn' %}<span class="status-pill" style="background:rgba(224,160,48,0.15);color:#e0a030;">Overdue</span>
          {% else %}<span class="status-pill">Recent</span>{% endif %}
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="widget"><p style="color:var(--green);">Nothing overdue. All tasks and POs are on schedule.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-conflicts">
  <h2>Calendar conflicts (next 30 days)</h2>
  <p style="color:var(--text3);font-size:0.85rem;margin:-0.4rem 0 0.8rem;">
    Days where you have 2+ commitments scheduled: tasks, purchase orders, or service sessions.
  </p>
  {% if conflict_rows %}
  {% for c in conflict_rows %}
  <div class="widget" style="border-left:4px solid #e0a030;padding:0.9rem 1.1rem;">
    <strong>{{ c.date }}</strong> — {{ c.count }} commitments:
    <ul style="margin:0.5rem 0 0;padding-left:1.5rem;color:var(--text2);font-size:0.88rem;">
      {% for i in c.items %}
      <li><span class="status-pill">{{ i.kind }}</span> {{ i.label }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endfor %}
  {% else %}
  <div class="widget"><p style="color:var(--text3);">No conflicts. Every day has at most one commitment.</p></div>
  {% endif %}
</section>

<section class="analytics-panel" id="panel-calandar">
  <h2>Free/busy (next 30 days)</h2>
  <div class="stat-grid" style="margin:0.5rem 0 1rem;">
    <div class="stat-chip"><span>Busy days</span><strong>{{ busy_count }}</strong></div>
    <div class="stat-chip"><span>Free days</span><strong>{{ free_count }}</strong></div>
    <div class="stat-chip"><span>Total</span><strong>30</strong></div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:0.4rem;">
    {% for d in calendar_days %}
    <div style="padding:0.5rem 0.6rem;border-radius:8px;text-align:center;font-size:0.82rem;font-family:var(--mono);{% if d.busy %}background:var(--danger-dim);border:1px solid rgba(231,76,60,0.3);{% else %}background:var(--surface2);border:1px solid var(--border);{% endif %}">
      {{ d.date[5:] }}
      {% if d.busy %}<div style="font-weight:700;color:#e74c3c;">{{ d.count }}</div>{% else %}<div style="color:var(--text3);">—</div>{% endif %}
    </div>
    {% endfor %}
  </div>
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
  if (['taskpriority','noteactions','context','escalation','conflicts','calandar'].includes(hash)) {
    activate(hash);
  }
})();
</script>
{% endblock %}
'''

for name, content in [
    ('templates/team_health.html', TEAM_TPL),
    ('templates/workflow_signals.html', WORKFLOW_TPL),
]:
    with open(name, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [OK]   {name}")

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
print(f"  Removed from disabled:  {removed}/9")
print(f"  New routes added:        11 (2 pages + 9 redirects)")
print(f"  New templates:           2")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 9 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 2f complete.

NEXT STEPS — in this exact order:

1. LOCAL TEST — run:  python app.py
   (Verify $env:DATABASE_URL is set in this PowerShell session first)

   Visit /team/health:
     3 tabs: Permissions, Activity, Config audit
     Permissions should list your account
     Activity should show recent events
     Config audit should show pass/warn/info per item

   Visit /workflow/signals:
     6 tabs: Task priority, Note actions, Reminder context,
             Escalation, Conflicts, Free/busy
     Some tabs will show "no data yet" (e.g. Note actions if you
     have no TODO lines in notes; Escalation if nothing overdue).

   Redirects:
     /team/permissions         -> /team/health#permissions
     /team/activity            -> /team/health#activity
     /settings/health          -> /team/health#config
     /tasks/priority           -> /workflow/signals#taskpriority
     /notes/actions            -> /workflow/signals#noteactions
     /reminders/context        -> /workflow/signals#context
     /reminders/escalation     -> /workflow/signals#escalation
     /calendar/conflicts       -> /workflow/signals#conflicts
     /calendar/free            -> /workflow/signals#calandar

   Sidebar: Analytics section should have 8 entries now
            (Sales, Customer, Inventory, Books health, Decisions,
             Patterns, Team health, Workflow signals).

   Regression:
     /dashboard, /plans (Active), all other analytics pages

2. REPORT BACK with:
   - /team/health 3 tabs render?
   - /workflow/signals 6 tabs render?
   - All 9 redirects work (URL changes)?
   - Sidebar 8 entries?
   - Regression pass?

3. Only after I confirm, commit + push + deploy.

4. Test on production.

5. Only after prod pass — delete backup: rm app.py.bak.batch2f_*

Remaining disabled after 2f: ~16 routes
  - ~9 non-schema for Batch 2g
  - ~10 schema-required for Batch 3
""")