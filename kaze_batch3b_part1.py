"""
kaze_batch3b_part1.py — Batch 3b part 1.

Builds 3 disabled routes with new tables:
  /settings/audit       -> logs every settings change (who, what, when)
  /whatsapp/templates   -> CRUD for reusable message templates
  /whatsapp/log         -> audit trail of WhatsApp link clicks

Modifications:
  - settings POST route now writes audit rows for changed fields
  - /whatsapp page now links through /whatsapp/send/<id> to log sends
  - WhatsApp templates can be used with {{name}} placeholder substitution

Part 2 (next script) will build: /health/history, /documents/versions,
/payments/fees.

Uses the [VERIFY] compile-before-write pattern that catches syntax errors
before app.py is touched. Also Jinja-parses every modified template.

Run from the folder with app.py:
    python kaze_batch3b_part1.py
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
backup_path = f"{APP}.bak.batch3b1_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}")

for tpl in ('whatsapp.html',):
    p = os.path.join(TPL_DIR, tpl)
    if os.path.isfile(p):
        shutil.copy2(p, p + f'.bak.batch3b1_{STAMP}')
        print(f"Backup: {p}.bak.batch3b1_{STAMP}")

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/9] Schema — 3 new tables")
# ═══════════════════════════════════════════════════════════════════

SCHEMA_ANCHOR = """    cur.execute("ALTER TABLE bookkeeping_docs ADD COLUMN IF NOT EXISTS approved_at TEXT DEFAULT ''")"""

SCHEMA_NEW = """    cur.execute("ALTER TABLE bookkeeping_docs ADD COLUMN IF NOT EXISTS approved_at TEXT DEFAULT ''")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS settings_audit (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            old_value TEXT DEFAULT '',
            new_value TEXT DEFAULT '',
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_settings_audit_user ON settings_audit (user_id, changed_at DESC)')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS whatsapp_templates (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            body TEXT NOT NULL,
            created_date TEXT NOT NULL,
            updated_date TEXT NOT NULL
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_user ON whatsapp_templates (user_id)')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS whatsapp_messages (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            customer_id INTEGER,
            phone TEXT NOT NULL,
            body TEXT DEFAULT '',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_user ON whatsapp_messages (user_id, sent_at DESC)')"""

if SCHEMA_ANCHOR in src:
    src = src.replace(SCHEMA_ANCHOR, SCHEMA_NEW, 1)
    print("  [OK]   added 3 new tables + indexes")
else:
    print("  [FAIL] schema anchor not found")
    FAILED.append("schema")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/9] Modify settings POST to audit changes")
# ═══════════════════════════════════════════════════════════════════

# First: fetch full prior row instead of 6 fields
OLD_FETCH = """        cur.execute(
            'SELECT stripe_secret_key, stripe_webhook_secret, plan_tier, '
            'flutterwave_secret_key, flutterwave_webhook_hash, alpha_vantage_key '
            'FROM settings WHERE user_id=%s',
            (current_user.id,),
        )
        prior_keys = cur.fetchone() or {}"""
NEW_FETCH = """        cur.execute('SELECT * FROM settings WHERE user_id=%s', (current_user.id,))
        prior_keys = cur.fetchone() or {}"""
if OLD_FETCH in src:
    src = src.replace(OLD_FETCH, NEW_FETCH, 1)
    print("  [OK]   settings prior query now fetches full row")
else:
    print("  [FAIL] settings prior query anchor not found")
    FAILED.append("settings prior query")

# Second: add audit block before commit
OLD_TAIL = """              bank_name, bank_account_name, bank_account_number, bank_branch,
              current_user.id))
        conn.commit()
        cur.close()
        conn.close()
        flash('Settings saved.', 'success')
        return redirect(url_for('settings'))"""

NEW_TAIL = """              bank_name, bank_account_name, bank_account_number, bank_branch,
              current_user.id))
        # Audit: log what changed (savepoint so an audit failure never blocks save)
        try:
            cur.execute('SAVEPOINT kaze_audit_sp')
            cur.execute('SELECT * FROM settings WHERE user_id=%s', (current_user.id,))
            new_row = cur.fetchone() or {}
            AUDIT_NORMAL = [
                'plan_tier', 'business_name', 'currency_code', 'currency_symbol',
                'tax_rate', 'monthly_revenue_goal', 'app_mode', 'ui_device',
                'theme', 'low_stock_threshold', 'items_per_page', 'date_format',
                'fiscal_year_start', 'number_decimals', 'invoice_prefix',
                'business_phone', 'business_address', 'font_family', 'font_size',
                'density', 'accent_color',
            ]
            AUDIT_SENSITIVE = [
                'stripe_secret_key', 'stripe_publishable_key', 'stripe_webhook_secret',
                'paypal_client_id', 'paypal_secret', 'flutterwave_public_key',
                'flutterwave_secret_key', 'flutterwave_webhook_hash',
                'alpha_vantage_key',
            ]
            for field in AUDIT_NORMAL:
                o = str((prior_keys or {}).get(field) or '')
                n = str(new_row.get(field) or '')
                if o != n:
                    cur.execute(
                        "INSERT INTO settings_audit (user_id, field_name, old_value, new_value) VALUES (%s, %s, %s, %s)",
                        (current_user.id, field, o[:200], n[:200]))
            for field in AUDIT_SENSITIVE:
                o = str((prior_keys or {}).get(field) or '')
                n = str(new_row.get(field) or '')
                if o != n:
                    cur.execute(
                        "INSERT INTO settings_audit (user_id, field_name, old_value, new_value) VALUES (%s, %s, %s, %s)",
                        (current_user.id, field,
                         '(changed)' if o else '(set)',
                         '(changed)' if n else '(cleared)'))
            cur.execute('RELEASE SAVEPOINT kaze_audit_sp')
        except Exception as exc:
            print('settings audit error:', exc)
            try:
                cur.execute('ROLLBACK TO SAVEPOINT kaze_audit_sp')
            except Exception:
                pass
        conn.commit()
        cur.close()
        conn.close()
        flash('Settings saved.', 'success')
        return redirect(url_for('settings'))"""

if OLD_TAIL in src:
    src = src.replace(OLD_TAIL, NEW_TAIL, 1)
    print("  [OK]   settings audit block inserted")
else:
    print("  [FAIL] settings UPDATE tail anchor not found")
    FAILED.append("settings audit block")

# ═══════════════════════════════════════════════════════════════════
print("\n[2.5/9] Remove old placeholder route definitions (avoid endpoint conflicts)")
DELETE_ROUTES = [
    ('/settings/audit', 'settings_audit'),
    ('/whatsapp/templates', 'whatsapp_templates'),
    ('/whatsapp/log', 'whatsapp_log'),
]
for _path, _funcname in DELETE_ROUTES:
    _pat = re.compile(
        r"@app\\.route\\('" + re.escape(_path) + r"'[^)]*\\)\\n"
        r"(?:@[^\\n]+\\n)*"
        r"def " + re.escape(_funcname) + r"\\([^)]*\\):\\n"
        r"(?:    .*\\n|\\n)*?"
        r"(?=\\n@app\\.|\\n#|\\ndef |\\nif __name__|\\Z)",
        re.MULTILINE | re.DOTALL,
    )
    _m = _pat.search(src)
    if _m:
        src = src[:_m.start()] + src[_m.end():]
        print(f"  [DEL]  {_path} (old placeholder)")
    else:
        print(f"  [SKIP] {_path} (not found or already deleted)")

print("\n[3/9] Remove 3 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = ['/settings/audit', '/whatsapp/templates', '/whatsapp/log']
removed = 0
for path in TO_REMOVE:
    pattern = re.compile(r"\s*'" + re.escape(path) + r"',?\n")
    if pattern.search(src):
        src = pattern.sub('\n', src, count=1)
        removed += 1
        print(f"  [OK]   removed {path}")
    else:
        print(f"  [SKIP] {path} — not found in disabled set")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/9] Add 6 new routes")
# ═══════════════════════════════════════════════════════════════════

NEW_PY = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 3b part 1 — Settings audit + WhatsApp templates + WhatsApp log
# ═══════════════════════════════════════════════════════════════════════

@app.route('/settings/audit')
@login_required
def settings_audit():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT field_name, old_value, new_value, changed_at
        FROM settings_audit
        WHERE user_id=%s
        ORDER BY changed_at DESC, id DESC
        LIMIT 200
    """, (uid,))
    rows = list(cur.fetchall() or [])
    cur.close(); conn.close()
    return render_template('settings_audit.html', rows=rows)


@app.route('/whatsapp/templates')
@login_required
def whatsapp_templates():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "SELECT id, name, body, created_date, updated_date FROM whatsapp_templates "
        "WHERE user_id=%s ORDER BY updated_date DESC",
        (uid,))
    templates = list(cur.fetchall() or [])
    cur.close(); conn.close()
    return render_template('whatsapp_templates.html', templates=templates)


@app.route('/whatsapp/templates/add', methods=['POST'])
@login_required
def whatsapp_template_add():
    name = (request.form.get('name') or '').strip()[:120]
    body = (request.form.get('body') or '').strip()[:2000]
    if not name or not body:
        flash('Name and body are required.', 'danger')
        return redirect(url_for('whatsapp_templates'))
    now = datetime.today().strftime('%Y-%m-%d %H:%M')
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO whatsapp_templates (user_id, name, body, created_date, updated_date) VALUES (%s, %s, %s, %s, %s)",
        (current_user.id, name, body, now, now))
    conn.commit(); cur.close(); conn.close()
    flash('Template saved.', 'success')
    return redirect(url_for('whatsapp_templates'))


@app.route('/whatsapp/templates/<int:id>/delete', methods=['POST'])
@login_required
def whatsapp_template_delete(id):
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "DELETE FROM whatsapp_templates WHERE id=%s AND user_id=%s",
        (id, current_user.id))
    conn.commit(); cur.close(); conn.close()
    flash('Template deleted.', 'success')
    return redirect(url_for('whatsapp_templates'))


@app.route('/whatsapp/log')
@login_required
def whatsapp_log():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT wm.sent_at, wm.phone, wm.body, c.name AS customer_name
        FROM whatsapp_messages wm
        LEFT JOIN customers c ON c.id = wm.customer_id
        WHERE wm.user_id=%s
        ORDER BY wm.sent_at DESC
        LIMIT 200
    """, (uid,))
    rows = list(cur.fetchall() or [])
    cur.close(); conn.close()
    return render_template('whatsapp_log.html', rows=rows)


@app.route('/whatsapp/send/<int:customer_id>')
@login_required
def whatsapp_send(customer_id):
    """Log the send attempt then redirect to wa.me. We cannot track actual
    delivery via wa.me, so we log the user's action of clicking Send."""
    import urllib.parse
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "SELECT id, name, phone FROM customers WHERE id=%s AND user_id=%s",
        (customer_id, uid))
    cust = cur.fetchone()
    if not cust:
        cur.close(); conn.close()
        flash('Customer not found.', 'danger')
        return redirect(url_for('whatsapp'))
    phone = (cust.get('phone') or '').strip()
    if not phone:
        cur.close(); conn.close()
        flash('This customer has no phone number.', 'danger')
        return redirect(url_for('whatsapp'))
    template_id = request.args.get('template_id', type=int) or 0
    body = ''
    if template_id:
        cur.execute(
            "SELECT body FROM whatsapp_templates WHERE id=%s AND user_id=%s",
            (template_id, uid))
        trow = cur.fetchone()
        if trow:
            body = trow.get('body') or ''
    if '{{name}}' in body:
        body = body.replace('{{name}}', cust.get('name') or '')
    cur.execute(
        "INSERT INTO whatsapp_messages (user_id, customer_id, phone, body) VALUES (%s, %s, %s, %s)",
        (uid, customer_id, phone, body[:500]))
    conn.commit()
    cur.close(); conn.close()
    phone_clean = phone.replace('+', '').replace(' ', '').replace('-', '')
    url = 'https://wa.me/' + phone_clean
    if body:
        url += '?text=' + urllib.parse.quote(body)
    return redirect(url, code=302)

'''

# VERIFY: compile before writing
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
print("  [OK]   inserted 6 new routes")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/9] Add Settings audit to NAV (Analytics section)")
# ═══════════════════════════════════════════════════════════════════

NAV_ANCHOR = "        ('Services analytics', 'services_analytics', 'graduation-cap', 'services', ('services_analytics',)),"
NAV_NEW = """        ('Services analytics', 'services_analytics', 'graduation-cap', 'services', ('services_analytics',)),
        ('Settings audit', 'settings_audit', 'history', None, ('settings_audit',)),"""

if NAV_ANCHOR in src:
    src = src.replace(NAV_ANCHOR, NAV_NEW, 1)
    print("  [OK]   Settings audit added to Analytics nav")
else:
    print("  [FAIL] nav anchor not found")
    FAILED.append("nav")

# ═══════════════════════════════════════════════════════════════════
print("\n[6/9] Write app.py")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   app.py written ({initial_routes} -> {final_routes} @app.route)")

# ═══════════════════════════════════════════════════════════════════
print("\n[7/9] Write 3 new templates")
# ═══════════════════════════════════════════════════════════════════

os.makedirs(TPL_DIR, exist_ok=True)

TPL_AUDIT = '''{% extends "base.html" %}
{% block title %}Settings Audit{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="history"></i> Settings Audit</h1>
    <p>Every change to your settings, when it happened, and what changed. Sensitive fields (Stripe keys, PayPal secrets) show "changed" but not the values.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Total changes</span><strong>{{ rows|length }}</strong></div>
</div>

{% if rows %}
<div class="table-wrapper">
<table>
<thead><tr><th>When</th><th>Field</th><th>Old value</th><th>New value</th></tr></thead>
<tbody>
{% for r in rows %}
<tr>
  <td style="font-size:0.85rem;color:var(--text3);">{{ r.changed_at }}</td>
  <td><code>{{ r.field_name }}</code></td>
  <td style="font-size:0.85rem;color:var(--text2);">{{ r.old_value or '—' }}</td>
  <td style="font-size:0.85rem;color:var(--text2);">{{ r.new_value or '—' }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<div class="widget"><p style="color:var(--text3);">No settings changes recorded yet. When you change a setting and save, it appears here.</p></div>
{% endif %}
{% endblock %}
'''

TPL_TEMPLATES = '''{% extends "base.html" %}
{% block title %}WhatsApp Templates{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="message-circle"></i> WhatsApp Templates</h1>
    <p>Reusable message bodies. Use <code>{{ '{{name}}' }}</code> in the body and it gets replaced with the customer's name when you send.</p>
  </div>
  <a href="{{ url_for('whatsapp') }}" class="btn-secondary">← Back to WhatsApp</a>
</div>

<details open style="margin-bottom:1.5rem;">
  <summary>New template</summary>
  <div>
    <form method="POST" action="{{ url_for('whatsapp_template_add') }}">
      <div class="form-group">
        <label>Name</label>
        <input type="text" name="name" required maxlength="120" placeholder="e.g. Payment reminder, Restock notice">
      </div>
      <div class="form-group" style="display:block;width:100%;">
        <label>Body</label>
        <textarea name="body" rows="4" required maxlength="2000" style="width:100%;max-width:640px;" placeholder="Hi {{ '{{name}}' }}, just a friendly reminder that your invoice is due."></textarea>
        <p style="font-size:0.8rem;color:var(--text3);margin:4px 0 0;">Use <code>{{ '{{name}}' }}</code> for the customer's name. Keep it under 500 chars — WhatsApp URL length is limited.</p>
      </div>
      <button type="submit">Save template</button>
    </form>
  </div>
</details>

<h2>Saved templates</h2>
{% if templates %}
<div class="table-wrapper">
<table>
<thead><tr><th>Name</th><th>Body preview</th><th>Updated</th><th>Actions</th></tr></thead>
<tbody>
{% for t in templates %}
<tr>
  <td><strong>{{ t.name }}</strong></td>
  <td style="font-size:0.85rem;color:var(--text2);max-width:400px;">{{ t.body[:120] }}{% if t.body|length > 120 %}…{% endif %}</td>
  <td style="font-size:0.85rem;color:var(--text3);">{{ t.updated_date }}</td>
  <td>
    <form method="POST" action="{{ url_for('whatsapp_template_delete', id=t.id) }}" onsubmit="return confirm('Delete this template?');" style="display:inline;">
      <button type="submit" class="btn-secondary">Delete</button>
    </form>
  </td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<div class="widget"><p style="color:var(--text3);">No templates saved yet. Add one above, then use it from the WhatsApp page.</p></div>
{% endif %}
{% endblock %}
'''

TPL_LOG = '''{% extends "base.html" %}
{% block title %}WhatsApp Log{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="list"></i> WhatsApp Log</h1>
    <p>Each row is a click on the "Send WhatsApp" button from the WhatsApp page. This logs the click, not WhatsApp's actual delivery status.</p>
  </div>
  <a href="{{ url_for('whatsapp') }}" class="btn-secondary">← Back to WhatsApp</a>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Shown</span><strong>{{ rows|length }}</strong></div>
</div>

{% if rows %}
<div class="table-wrapper">
<table>
<thead><tr><th>When</th><th>Customer</th><th>Phone</th><th>Message sent</th></tr></thead>
<tbody>
{% for r in rows %}
<tr>
  <td style="font-size:0.85rem;color:var(--text3);">{{ r.sent_at }}</td>
  <td>{{ r.customer_name or '—' }}</td>
  <td style="font-family:var(--mono);font-size:0.85rem;">{{ r.phone }}</td>
  <td style="font-size:0.85rem;color:var(--text2);">{{ r.body or '(no template used)' }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<div class="widget"><p style="color:var(--text3);">No WhatsApp sends logged yet. Send a message from the <a href="{{ url_for('whatsapp') }}">WhatsApp Hub</a> to see it here.</p></div>
{% endif %}
{% endblock %}
'''

for name, content in [
    (os.path.join(TPL_DIR, 'settings_audit.html'), TPL_AUDIT),
    (os.path.join(TPL_DIR, 'whatsapp_templates.html'), TPL_TEMPLATES),
    (os.path.join(TPL_DIR, 'whatsapp_log.html'), TPL_LOG),
]:
    try:
        Environment().parse(content)
    except Exception as exc:
        print(f"  [FAIL] {name} Jinja error: {exc}")
        FAILED.append(f"{name} jinja")
        continue
    with open(name, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [OK]   {name}")

# ═══════════════════════════════════════════════════════════════════
print("\n[8/9] Rewrite whatsapp.html — template picker + log link + send routing")
# ═══════════════════════════════════════════════════════════════════

WHATSAPP_TPL = '''{% extends "base.html" %}
{% block title %}WhatsApp Hub{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="message-circle"></i> WhatsApp Hub</h1>
    <p>Send invoice links and reminders via WhatsApp. Sends are logged automatically.</p>
  </div>
  <div style="display:flex;gap:0.4rem;flex-wrap:wrap;">
    <a href="{{ url_for('whatsapp_templates') }}" class="btn-secondary">Manage templates</a>
    <a href="{{ url_for('whatsapp_log') }}" class="btn-secondary">View log</a>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Customers with phone</span><strong>{{ customers|length }}</strong></div>
  <div class="stat-chip"><span>Saved templates</span><strong>{{ templates|length }}</strong></div>
</div>

{% if templates %}
<div class="widget">
  <h2 style="margin-top:0;">Quick send with template</h2>
  <p style="color:var(--text2);font-size:0.9rem;">Pick a customer and a template. The message body opens in WhatsApp with <code>{{ '{{name}}' }}</code> replaced by the customer's name.</p>
  <form method="GET" action="" id="quickSendForm" onsubmit="return quickSendRedirect();">
    <div class="form-group">
      <label>Customer</label>
      <select name="customer_id" required>
        <option value="">— Choose —</option>
        {% for c in customers %}
        <option value="{{ c.id }}">{{ c.name }} ({{ c.phone }})</option>
        {% endfor %}
      </select>
    </div>
    <div class="form-group">
      <label>Template</label>
      <select name="template_id" required>
        {% for t in templates %}
        <option value="{{ t.id }}">{{ t.name }}</option>
        {% endfor %}
      </select>
    </div>
    <button type="submit">Send via WhatsApp</button>
  </form>
  <script>
    function quickSendRedirect() {
      var f = document.getElementById('quickSendForm');
      var cid = f.customer_id.value;
      var tid = f.template_id.value;
      if (!cid) { alert('Choose a customer.'); return false; }
      window.open('/whatsapp/send/' + cid + '?template_id=' + tid, '_blank');
      return false;
    }
  </script>
</div>
{% else %}
<div class="widget">
  <p style="color:var(--text2);margin:0;">No templates yet. <a href="{{ url_for('whatsapp_templates') }}">Create one</a> to enable quick send, or use the direct buttons below.</p>
</div>
{% endif %}

<h2>Customers</h2>
<div class="card">
  <table class="data-table">
    <thead><tr><th>Customer</th><th>Phone</th><th>Action</th></tr></thead>
    <tbody>
      {% for c in customers %}
      <tr>
        <td>{{ c.name }}</td>
        <td style="font-family:var(--mono);font-size:0.88rem;">{{ c.phone }}</td>
        <td>
          <a class="btn-sm" href="{{ url_for('whatsapp_send', customer_id=c.id) }}" target="_blank">Send WhatsApp</a>
        </td>
      </tr>
      {% else %}
      <tr><td colspan="3" style="color:var(--text3);">No customers with phone numbers yet. <a href="{{ url_for('customers') }}">Add one</a>.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<p style="margin-top:1rem;font-size:0.85rem;color:var(--text3);">
  Each click is logged in your <a href="{{ url_for('whatsapp_log') }}">WhatsApp Log</a>. KAZE cannot confirm that WhatsApp delivered the message — it only records the send action.
</p>
{% endblock %}
'''

try:
    Environment().parse(WHATSAPP_TPL)
except Exception as exc:
    print(f"  [FAIL] whatsapp.html Jinja error: {exc}")
    FAILED.append("whatsapp.html jinja")
else:
    with open(os.path.join(TPL_DIR, 'whatsapp.html'), 'w', encoding='utf-8') as f:
        f.write(WHATSAPP_TPL)
    print("  [OK]   whatsapp.html rewritten")

# ═══════════════════════════════════════════════════════════════════
print("\n[9/9] Modify /whatsapp route to pass templates list")
# ═══════════════════════════════════════════════════════════════════

OLD_WHATSAPP = """@app.route('/whatsapp')
@login_required
def whatsapp():
    # List recent invoices/customers for quick WhatsApp share
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, phone FROM customers WHERE user_id=%s AND phone != '' LIMIT 20", (current_user.id,))
    customers = cur.fetchall()
    conn.close()
    return render_template('whatsapp.html', customers=customers)"""

NEW_WHATSAPP = """@app.route('/whatsapp')
@login_required
def whatsapp():
    uid = current_user.id
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, phone FROM customers WHERE user_id=%s AND phone != '' ORDER BY name LIMIT 100", (uid,))
    customers = list(cur.fetchall() or [])
    cur.execute(
        "SELECT id, name FROM whatsapp_templates WHERE user_id=%s ORDER BY name",
        (uid,))
    templates = list(cur.fetchall() or [])
    cur.close()
    conn.close()
    return render_template('whatsapp.html', customers=customers, templates=templates)"""

if OLD_WHATSAPP in src:
    src = src.replace(OLD_WHATSAPP, NEW_WHATSAPP, 1)
    print("  [OK]   /whatsapp route now passes templates")
else:
    print("  [FAIL] /whatsapp route anchor not found")
    FAILED.append("whatsapp route")

# ═══════════════════════════════════════════════════════════════════
print("\n[FINAL] Write app.py + compile check")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   app.py written ({initial_routes} -> {final_routes} @app.route)")

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
print(f"  Removed from disabled:  {removed}/3")
print(f"  New routes added:        6")
print(f"  New tables:              3 (settings_audit, whatsapp_templates, whatsapp_messages)")
print(f"  New templates:           3")
print(f"  Modified templates:      1 (whatsapp.html)")
print(f"  Modified routes:         2 (settings POST audit, /whatsapp context)")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 3 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    print(f"Restore whatsapp.html: copy \"templates/whatsapp.html.bak.batch3b1_{STAMP}\" templates/whatsapp.html")
    sys.exit(1)

print("""
Batch 3b part 1 complete. Batch 3b part 2 (health history, documents
versions, payments fees) will be written next — after this batch deploys.

NEXT STEPS:

1. LOCAL TEST — run:  python app.py
   (Verify $env:DATABASE_URL is set)

   /settings          -> save any small change (e.g. edit about text)
                         -> then /settings/audit should show it logged

   /settings/audit    -> table of changes (empty on first visit before saving)

   /whatsapp          -> shows template picker + customer table
                         -> each customer "Send WhatsApp" opens wa.me in new tab
                         -> after clicking, /whatsapp/log shows the attempt

   /whatsapp/templates -> create a template with {{name}} placeholder
                        -> back to /whatsapp, template appears in picker

   /whatsapp/log      -> any clicks you made above appear here

   Sidebar -> Analytics section now has 10 entries
              (added Settings audit)

   Regression — verify:
     /dashboard, /plans (Active), /customers, /settings all work

2. REPORT BACK:
   - /settings/audit exists and shows rows after saving settings?
   - /whatsapp has template picker (if templates exist)?
   - /whatsapp/templates CRUD works?
   - /whatsapp/log records sends?
   - Sidebar 10 analytics entries?
   - Regression pass?

3. Only after I confirm, commit + push + deploy.

4. Test on production.

5. Only after prod pass:
     rm app.py.bak.batch3b1_*
     rm templates/whatsapp.html.bak.batch3b1_*

PART 2 (NEXT SCRIPT):
  /health/history, /documents/versions, /payments/fees
""")