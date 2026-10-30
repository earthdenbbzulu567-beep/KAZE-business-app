"""
kaze_batch3b_part2b.py — Batch 3b part 2b.

Builds /documents/versions using a Postgres trigger:
  - New table: bookkeeping_doc_versions
  - Postgres trigger: snapshot on INSERT/UPDATE/DELETE of bookkeeping_docs
  - /documents/versions: list of docs with version counts
  - /documents/versions/<id>: version history for one doc
  - Deletes old /documents/versions placeholder

Trigger approach (vs 6 route hooks) — trigger fires automatically on every
mutation, no route changes needed, future-proof against new mutation paths.

Run from the folder with app.py:
    python kaze_batch3b_part2b.py
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
backup_path = f"{APP}.bak.batch3b2b_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}")

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/7] Schema — bookkeeping_doc_versions table + trigger")
# ═══════════════════════════════════════════════════════════════════

SCHEMA_ANCHOR = """    cur.execute('CREATE INDEX IF NOT EXISTS idx_score_snapshots_user ON score_snapshots (user_id, snapshot_date DESC)')"""

SCHEMA_NEW = """    cur.execute('CREATE INDEX IF NOT EXISTS idx_score_snapshots_user ON score_snapshots (user_id, snapshot_date DESC)')

    # bookkeeping_doc_versions + trigger (auto-snapshot every mutation)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookkeeping_doc_versions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            doc_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            kind TEXT DEFAULT '',
            title TEXT DEFAULT '',
            party TEXT DEFAULT '',
            reference TEXT DEFAULT '',
            doc_date TEXT DEFAULT '',
            amount REAL DEFAULT 0,
            status TEXT DEFAULT '',
            approval_status TEXT DEFAULT 'none',
            approval_notes TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            line_items TEXT DEFAULT '',
            snapshot_reason TEXT DEFAULT '',
            snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_bdv_user_doc ON bookkeeping_doc_versions (user_id, doc_id, version_number DESC)')
    cur.execute('''
        CREATE OR REPLACE FUNCTION kaze_snapshot_bookkeeping_doc() RETURNS TRIGGER AS $$
        DECLARE
            v_user_id INTEGER;
            v_doc_id INTEGER;
            v_next_version INTEGER;
            v_reason TEXT;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                v_user_id := OLD.user_id;
                v_doc_id := OLD.id;
                v_reason := 'deleted';
                INSERT INTO bookkeeping_doc_versions (
                    user_id, doc_id, version_number, kind, title, party, reference,
                    doc_date, amount, status, approval_status, approval_notes,
                    notes, line_items, snapshot_reason
                ) VALUES (
                    v_user_id, v_doc_id, 0,
                    COALESCE(OLD.kind, ''), COALESCE(OLD.title, ''), COALESCE(OLD.party, ''),
                    COALESCE(OLD.reference, ''), COALESCE(OLD.doc_date, ''),
                    COALESCE(OLD.amount, 0), COALESCE(OLD.status, ''),
                    COALESCE(OLD.approval_status, 'none'), COALESCE(OLD.approval_notes, ''),
                    COALESCE(OLD.notes, ''), COALESCE(OLD.line_items, ''), v_reason
                );
                RETURN OLD;
            ELSE
                v_user_id := NEW.user_id;
                v_doc_id := NEW.id;
                v_reason := LOWER(TG_OP);
                SELECT COALESCE(MAX(version_number), 0) + 1 INTO v_next_version
                FROM bookkeeping_doc_versions
                WHERE user_id = v_user_id AND doc_id = v_doc_id
                  AND snapshot_reason != 'deleted';
                INSERT INTO bookkeeping_doc_versions (
                    user_id, doc_id, version_number, kind, title, party, reference,
                    doc_date, amount, status, approval_status, approval_notes,
                    notes, line_items, snapshot_reason
                ) VALUES (
                    v_user_id, v_doc_id, v_next_version,
                    COALESCE(NEW.kind, ''), COALESCE(NEW.title, ''), COALESCE(NEW.party, ''),
                    COALESCE(NEW.reference, ''), COALESCE(NEW.doc_date, ''),
                    COALESCE(NEW.amount, 0), COALESCE(NEW.status, ''),
                    COALESCE(NEW.approval_status, 'none'), COALESCE(NEW.approval_notes, ''),
                    COALESCE(NEW.notes, ''), COALESCE(NEW.line_items, ''), v_reason
                );
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql
    ''')
    cur.execute('DROP TRIGGER IF EXISTS trg_kaze_snapshot_bookkeeping ON bookkeeping_docs')
    cur.execute('''
        CREATE TRIGGER trg_kaze_snapshot_bookkeeping
        AFTER INSERT OR UPDATE OR DELETE ON bookkeeping_docs
        FOR EACH ROW EXECUTE FUNCTION kaze_snapshot_bookkeeping_doc()
    ''')"""

if SCHEMA_ANCHOR in src:
    src = src.replace(SCHEMA_ANCHOR, SCHEMA_NEW, 1)
    print("  [OK]   added bookkeeping_doc_versions table + trigger")
else:
    print("  [FAIL] schema anchor not found (score_snapshots index)")
    FAILED.append("schema")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/7] Delete old /documents/versions placeholder")
# ═══════════════════════════════════════════════════════════════════

# Handle both @app.route('/documents/versions') and @app.route('/documents/versions/<int:id>')
for marker in ["@app.route('/documents/versions'", "@app.route('/documents/versions/<"]:
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
        print(f"  [DEL]  {marker}... (old placeholder)")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/7] Remove from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

removed = 0
pattern = re.compile(r"\s*'/documents/versions',?\n")
if pattern.search(src):
    src = pattern.sub('\n', src, count=1)
    removed += 1
    print("  [OK]   removed /documents/versions")
else:
    print("  [SKIP] not in disabled set")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/7] Add /documents/versions routes")
# ═══════════════════════════════════════════════════════════════════

NEW_PY = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 3b part 2b — Document version history (via Postgres trigger)
# ═══════════════════════════════════════════════════════════════════════

@app.route('/documents/versions')
@login_required
def documents_versions():
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    # List docs that have at least one version
    cur.execute("""
        SELECT bv.doc_id,
               COUNT(*) AS version_count,
               MAX(bv.snapshot_at) AS last_change,
               MAX(CASE WHEN bv.snapshot_reason != 'deleted' THEN bv.title ELSE NULL END) AS current_title,
               MAX(CASE WHEN bv.snapshot_reason != 'deleted' THEN bv.kind ELSE NULL END) AS current_kind,
               MAX(bv.snapshot_reason) FILTER (WHERE bv.snapshot_at = (
                   SELECT MAX(snapshot_at) FROM bookkeeping_doc_versions bv2
                   WHERE bv2.user_id = bv.user_id AND bv2.doc_id = bv.doc_id
               )) AS latest_reason
        FROM bookkeeping_doc_versions bv
        WHERE bv.user_id=%s
        GROUP BY bv.doc_id
        ORDER BY MAX(bv.snapshot_at) DESC
        LIMIT 200
    """, (uid,))
    docs = []
    for r in (cur.fetchall() or []):
        title = r.get('current_title')
        kind = r.get('current_kind')
        if not title:
            # Deleted doc — get kind/title from the deleted snapshot
            cur.execute(
                "SELECT title, kind FROM bookkeeping_doc_versions "
                "WHERE user_id=%s AND doc_id=%s AND snapshot_reason='deleted' "
                "ORDER BY id DESC LIMIT 1",
                (uid, r.get('doc_id')))
            drow = cur.fetchone()
            if drow:
                title = drow.get('title')
                kind = drow.get('kind')
        docs.append({
            'doc_id': r.get('doc_id'),
            'title': title or '(deleted)',
            'kind': (kind or '').replace('_', ' ').title() or '—',
            'version_count': int(r.get('version_count') or 0),
            'last_change': r.get('last_change') or '?',
            'latest_reason': (r.get('latest_reason') or '').lower(),
        })
    cur.close(); conn.close()
    return render_template('documents_versions.html', docs=docs)


@app.route('/documents/versions/<int:doc_id>')
@login_required
def documents_version_detail(doc_id):
    uid = current_user.id
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT id, version_number, kind, title, party, reference, doc_date,
               amount, status, approval_status, approval_notes, notes,
               line_items, snapshot_reason, snapshot_at
        FROM bookkeeping_doc_versions
        WHERE user_id=%s AND doc_id=%s
        ORDER BY snapshot_at DESC, id DESC
    """, (uid, doc_id))
    rows = []
    for r in (cur.fetchall() or []):
        rows.append({
            'id': r.get('id'),
            'version_number': int(r.get('version_number') or 0),
            'kind': (r.get('kind') or '').replace('_', ' ').title(),
            'title': r.get('title') or '',
            'party': r.get('party') or '',
            'reference': r.get('reference') or '',
            'doc_date': r.get('doc_date') or '',
            'amount': float(r.get('amount') or 0),
            'status': r.get('status') or '',
            'approval_status': r.get('approval_status') or 'none',
            'approval_notes': r.get('approval_notes') or '',
            'notes': r.get('notes') or '',
            'line_items': r.get('line_items') or '',
            'snapshot_reason': (r.get('snapshot_reason') or '').lower(),
            'snapshot_at': r.get('snapshot_at') or '?',
        })
    cur.close(); conn.close()

    # Detect which fields changed between consecutive versions
    for i, row in enumerate(rows):
        if i + 1 < len(rows):
            older = rows[i + 1]
            changes = []
            for field in ('title', 'party', 'reference', 'amount', 'status',
                          'approval_status', 'notes', 'line_items'):
                if row.get(field) != older.get(field):
                    changes.append(field)
            row['changed_fields'] = changes
        else:
            row['changed_fields'] = []

    if not rows:
        flash('No version history found for that document.', 'info')
        return redirect(url_for('documents_versions'))

    doc_title = rows[0]['title'] or f'Document #{doc_id}'
    return render_template('documents_version_detail.html',
        rows=rows, doc_id=doc_id, doc_title=doc_title)

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
print("  [OK]   inserted /documents/versions + detail routes")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/7] Add Documents versions to NAV (Analytics section)")
# ═══════════════════════════════════════════════════════════════════

NAV_ANCHOR = "        ('Settings audit', 'settings_audit', 'history', None, ('settings_audit',)),"
NAV_NEW = """        ('Settings audit', 'settings_audit', 'history', None, ('settings_audit',)),
        ('Document versions', 'documents_versions', 'file-text', None, ('documents_versions',)),"""

if NAV_ANCHOR in src:
    src = src.replace(NAV_ANCHOR, NAV_NEW, 1)
    print("  [OK]   Document versions added to Analytics nav")
else:
    print("  [FAIL] nav anchor not found (Settings audit)")
    FAILED.append("nav")

# ═══════════════════════════════════════════════════════════════════
print("\n[6/7] Write app.py + templates")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
final_routes = src.count('@app.route')
print(f"  [OK]   app.py written ({initial_routes} -> {final_routes} @app.route)")

os.makedirs(TPL_DIR, exist_ok=True)

LIST_TPL = '''{% extends "base.html" %}
{% block title %}Document Versions{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="file-text"></i> Document Versions</h1>
    <p>Every edit, approval, and deletion of a bookkeeping document is automatically snapshotted. Click any document to see its full history.</p>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-chip"><span>Documents tracked</span><strong>{{ docs|length }}</strong></div>
</div>

{% if docs %}
<div class="table-wrapper">
<table>
<thead><tr><th>Document</th><th>Kind</th><th>Versions</th><th>Last change</th><th>Latest action</th><th></th></tr></thead>
<tbody>
{% for d in docs %}
<tr {% if d.latest_reason == 'deleted' %}style="opacity:0.7;"{% endif %}>
  <td><strong>{{ d.title }}</strong>{% if d.latest_reason == 'deleted' %} <span class="status-pill" style="background:var(--danger-dim);color:#e74c3c;">deleted</span>{% endif %}</td>
  <td>{{ d.kind }}</td>
  <td style="font-family:var(--mono);">{{ d.version_count }}</td>
  <td style="font-size:0.85rem;color:var(--text3);">{{ d.last_change }}</td>
  <td>
    {% if d.latest_reason == 'insert' %}<span class="status-pill">Created</span>
    {% elif d.latest_reason == 'update' %}<span class="status-pill status-warn">Edited</span>
    {% elif d.latest_reason == 'deleted' %}<span class="status-pill" style="background:var(--danger-dim);color:#e74c3c;">Deleted</span>
    {% else %}<span class="status-pill">{{ d.latest_reason|title }}</span>{% endif %}
  </td>
  <td><a href="{{ url_for('documents_version_detail', doc_id=d.doc_id) }}">History</a></td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<div class="widget">
  <p style="color:var(--text3);">
    No version history yet. Any new, edited, approved, or deleted bookkeeping document from now on
    will automatically appear here. Existing documents created before this feature was enabled are not
    retroactively tracked — try editing one on <a href="{{ url_for('bookkeeping') }}">Book keeping</a>
    to see it appear.
  </p>
</div>
{% endif %}
{% endblock %}
'''

DETAIL_TPL = '''{% extends "base.html" %}
{% block title %}Version history — {{ doc_title }}{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h1><i data-lucide="clock"></i> {{ doc_title }}</h1>
    <p>Every version of this document, newest first. Document ID #{{ doc_id }}.</p>
  </div>
  <a href="{{ url_for('documents_versions') }}" class="btn-secondary">← All documents</a>
</div>

{% if rows %}
<div class="widget" style="padding:1rem 1.1rem;">
  <p style="margin:0;font-size:0.9rem;color:var(--text2);">
    <strong>{{ rows|length }}</strong> version{{ '' if rows|length == 1 else 's' }} recorded.
    Each row shows what the document looked like at that point.
  </p>
</div>

{% for r in rows %}
<div class="widget" style="border-left:4px solid {% if r.snapshot_reason == 'deleted' %}#e74c3c{% elif r.snapshot_reason == 'insert' %}var(--green){% else %}#e0a030{% endif %};">
  <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:0.5rem;">
    <div>
      <span class="status-pill" style="background:var(--surface2);color:var(--text2);">
        v{{ r.version_number if r.version_number > 0 else '—' }}
      </span>
      <span class="status-pill" style="margin-left:0.4rem;
        {% if r.snapshot_reason == 'deleted' %}background:var(--danger-dim);color:#e74c3c;
        {% elif r.snapshot_reason == 'insert' %}background:var(--green-dim);color:var(--green);
        {% else %}background:rgba(224,160,48,0.15);color:#e0a030;{% endif %}">
        {{ r.snapshot_reason|title }}
      </span>
      <span style="margin-left:0.4rem;font-size:0.82rem;color:var(--text3);">{{ r.snapshot_at }}</span>
    </div>
    {% if r.changed_fields %}
    <span style="font-size:0.8rem;color:var(--text3);">
      changed: {{ r.changed_fields|join(', ') }}
    </span>
    {% endif %}
  </div>
  <table style="width:100%;margin-top:0.8rem;font-size:0.88rem;border-collapse:collapse;">
    <tbody>
      <tr><td style="padding:4px 8px 4px 0;color:var(--text3);width:120px;">Kind</td><td>{{ r.kind or '—' }}</td></tr>
      <tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Title</td><td>{{ r.title or '—' }}</td></tr>
      <tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Party</td><td>{{ r.party or '—' }}</td></tr>
      <tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Reference</td><td>{{ r.reference or '—' }}</td></tr>
      <tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Date</td><td>{{ r.doc_date or '—' }}</td></tr>
      <tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Amount</td><td>{{ money(r.amount) }}</td></tr>
      <tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Status</td><td>{{ r.status or '—' }}</td></tr>
      <tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Approval</td><td>{{ r.approval_status or 'none' }}{% if r.approval_notes %} — {{ r.approval_notes }}{% endif %}</td></tr>
      {% if r.notes %}<tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Notes</td><td>{{ r.notes }}</td></tr>{% endif %}
      {% if r.line_items %}<tr><td style="padding:4px 8px 4px 0;color:var(--text3);">Lines</td><td><pre style="white-space:pre-wrap;font-size:0.82rem;margin:0;">{{ r.line_items }}</pre></td></tr>{% endif %}
    </tbody>
  </table>
</div>
{% endfor %}
{% else %}
<div class="widget"><p style="color:var(--text3);">No versions found.</p></div>
{% endif %}
{% endblock %}
'''

for name, content in [
    (os.path.join(TPL_DIR, 'documents_versions.html'), LIST_TPL),
    (os.path.join(TPL_DIR, 'documents_version_detail.html'), DETAIL_TPL),
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
print(f"  New routes added:        2 (list + detail)")
print(f"  New tables:              1 (bookkeeping_doc_versions)")
print(f"  New trigger:             1 (auto-snapshot on bookkeeping_docs)")
print(f"  New templates:           2")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 1 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    sys.exit(1)

print("""
Batch 3b part 2b complete.

NEXT STEPS:

1. LOCAL TEST — run:  python app.py
   (Verify $env:DATABASE_URL is set)

   First visit will apply the trigger via init_db(). The trigger fires on
   EVERY bookkeeping_docs mutation from now on, automatically.

   /documents/versions  -> probably empty at first (no new mutations yet)

   To populate:
     - Go to /bookkeeping/invoice (or any kind)
     - Create a new invoice -> trigger fires -> version v1 (insert)
     - Edit that invoice (change status) -> trigger fires -> v2 (update)
     - Approve it -> trigger fires -> v3 (update)
     - Go back to /documents/versions -> invoice appears with 3 versions
     - Click "History" -> see v3, v2, v1 in descending order
       with "changed: status" annotations

   Delete a doc -> trigger fires -> v-deleted appears with reason 'deleted'

   Regression:
     /dashboard, /plans (Active), /bookkeeping, /bookkeeping/<kind> all work
     No 500s on any page

2. REPORT BACK:
   - /documents/versions loads?
   - Trigger fires after creating a doc (new version appears)?
   - Trigger fires after editing/approving (v2, v3 appear)?
   - Trigger fires after delete (deleted version appears)?
   - History detail page shows versions with change annotations?
   - Regression pass?

3. Only after I confirm, commit + push + deploy.

4. Test on production.

5. Only after prod pass:
     rm app.py.bak.batch3b2b_*

REMAINING AFTER THIS:
  Part 2c — /payments/fees (last rebuild before GUI remodel)
""")