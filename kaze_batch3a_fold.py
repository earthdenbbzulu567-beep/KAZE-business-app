"""
kaze_batch3a_fold.py — Batch 3a.

Folds 3 disabled routes into existing pages with schema changes:
  /banking/reconcile    -> /banking (reconciled column + filter)
  /tasks/blockers       -> /tasks   (blocker note column + inline edit)
  /documents/approval   -> /bookkeeping/<kind> (approve/reject actions)

Schema:
  + bank_transactions.reconciled INTEGER DEFAULT 0
  + bank_transactions.reconciled_date TEXT DEFAULT ''
  + tasks.blocker_note TEXT DEFAULT ''
  + bookkeeping_docs.approval_status TEXT DEFAULT 'none'
  + bookkeeping_docs.approval_notes TEXT DEFAULT ''
  + bookkeeping_docs.approved_by TEXT DEFAULT ''
  + bookkeeping_docs.approved_at TEXT DEFAULT ''

/settings/audit is DEFERRED to Batch 3b (needs settings-save route changes).

Verifies Python compile + Jinja parse for every template edit before writing.

Run from the folder with app.py:
    python kaze_batch3a_fold.py
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
backup_path = f"{APP}.bak.batch3a_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}")

for tpl in ('banking.html', 'tasks.html', 'bookkeeping_type.html', 'bookkeeping.html'):
    p = os.path.join(TPL_DIR, tpl)
    if os.path.isfile(p):
        shutil.copy2(p, p + f'.bak.batch3a_{STAMP}')
        print(f"Backup: {p}.bak.batch3a_{STAMP}")

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/8] Schema — 7 new columns")
# ═══════════════════════════════════════════════════════════════════

SCHEMA_OLD = """    cur.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS received_date TEXT DEFAULT ''")"""
SCHEMA_NEW = """    cur.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS received_date TEXT DEFAULT ''")
    cur.execute("ALTER TABLE bank_transactions ADD COLUMN IF NOT EXISTS reconciled INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE bank_transactions ADD COLUMN IF NOT EXISTS reconciled_date TEXT DEFAULT ''")
    cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blocker_note TEXT DEFAULT ''")
    cur.execute("ALTER TABLE bookkeeping_docs ADD COLUMN IF NOT EXISTS approval_status TEXT DEFAULT 'none'")
    cur.execute("ALTER TABLE bookkeeping_docs ADD COLUMN IF NOT EXISTS approval_notes TEXT DEFAULT ''")
    cur.execute("ALTER TABLE bookkeeping_docs ADD COLUMN IF NOT EXISTS approved_by TEXT DEFAULT ''")
    cur.execute("ALTER TABLE bookkeeping_docs ADD COLUMN IF NOT EXISTS approved_at TEXT DEFAULT ''")"""

if SCHEMA_OLD in src:
    src = src.replace(SCHEMA_OLD, SCHEMA_NEW, 1)
    print("  [OK]   added 7 ALTER TABLE columns")
else:
    print("  [FAIL] schema anchor not found")
    FAILED.append("schema")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/8] Remove 3 paths from _DISABLED_PATHS")
# ═══════════════════════════════════════════════════════════════════

TO_REMOVE = ['/banking/reconcile', '/tasks/blockers', '/documents/approval']
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
print("\n[3/8] Add POST action endpoints + 3 redirects")
# ═══════════════════════════════════════════════════════════════════

NEW_PY = '''

# ═══════════════════════════════════════════════════════════════════════
# Batch 3a — Fold-ins with schema
# ═══════════════════════════════════════════════════════════════════════

@app.route('/banking/tx/<int:id>/reconcile', methods=['POST'])
@login_required
def reconcile_bank_tx(id):
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "SELECT id, reconciled FROM bank_transactions WHERE id=%s AND user_id=%s",
        (id, current_user.id))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        flash('Transaction not found.', 'danger')
        return redirect(url_for('banking'))
    new_val = 0 if (row.get('reconciled') or 0) == 1 else 1
    date_val = datetime.today().strftime('%Y-%m-%d') if new_val == 1 else ''
    cur.execute(
        "UPDATE bank_transactions SET reconciled=%s, reconciled_date=%s "
        "WHERE id=%s AND user_id=%s",
        (new_val, date_val, id, current_user.id))
    conn.commit()
    cur.close(); conn.close()
    flash('Marked reconciled.' if new_val else 'Un-reconciled.', 'success')
    return redirect(url_for('banking'))


@app.route('/tasks/<int:id>/blocker', methods=['POST'])
@login_required
def save_task_blocker(id):
    note = (request.form.get('blocker_note') or '').strip()[:500]
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM tasks WHERE id=%s AND user_id=%s", (id, current_user.id))
    if not cur.fetchone():
        cur.close(); conn.close()
        flash('Task not found.', 'danger')
        return redirect(url_for('tasks'))
    cur.execute(
        "UPDATE tasks SET blocker_note=%s WHERE id=%s AND user_id=%s",
        (note, id, current_user.id))
    conn.commit()
    cur.close(); conn.close()
    flash('Blocker updated.' if note else 'Blocker cleared.', 'success')
    return redirect(url_for('tasks'))


@app.route('/bookkeeping/doc/<int:id>/approve', methods=['POST'])
@login_required
def approve_book_doc(id):
    decision = (request.form.get('decision') or 'approved').lower()
    if decision not in ('approved', 'rejected', 'none'):
        decision = 'approved'
    note = (request.form.get('approval_notes') or '').strip()[:500]
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "SELECT id, kind FROM bookkeeping_docs WHERE id=%s AND user_id=%s",
        (id, current_user.id))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        flash('Document not found.', 'danger')
        return redirect(url_for('bookkeeping'))
    now = datetime.today().strftime('%Y-%m-%d %H:%M') if decision != 'none' else ''
    cur.execute(
        "UPDATE bookkeeping_docs SET approval_status=%s, approval_notes=%s, "
        "approved_by=%s, approved_at=%s WHERE id=%s AND user_id=%s",
        (decision, note,
         current_user.username if decision != 'none' else '',
         now, id, current_user.id))
    conn.commit()
    kind = row.get('kind') or 'invoice'
    cur.close(); conn.close()
    flash('Approval status updated.', 'success')
    return redirect(url_for('bookkeeping_type', kind=kind))


# Redirects from original disabled routes
@app.route('/banking/reconcile')
@login_required
def redirect_banking_reconcile():
    return redirect(url_for('banking') + '#reconcile', code=301)


@app.route('/tasks/blockers')
@login_required
def redirect_tasks_blockers():
    return redirect(url_for('tasks') + '#blockers', code=301)


@app.route('/documents/approval')
@login_required
def redirect_documents_approval():
    return redirect(url_for('bookkeeping'), code=301)

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
print("  [OK]   inserted 3 action endpoints + 3 redirects")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/8] Modify banking.html — reconcile column + filter")
# ═══════════════════════════════════════════════════════════════════

bank_path = os.path.join(TPL_DIR, 'banking.html')
if not os.path.isfile(bank_path):
    print(f"  [FAIL] {bank_path} not found")
    FAILED.append("banking.html")
else:
    with open(bank_path, encoding='utf-8') as f:
        bank = f.read()
    # Replace the "Recent movements" table header + row markup to add reconcile
    OLD_MOV = """    <thead><tr><th>Date</th><th>Account</th><th>Type</th><th>Party</th><th>Ref</th><th>Amount</th><th></th></tr></thead>
    <tbody>
    {% for t in txs %}
        <tr>
            <td>{{ t.tx_date }}</td>
            <td>{{ t.account_name }}</td>
            <td>{{ t.kind }}</td>
            <td>{{ t.counterparty }}</td>
            <td>{{ t.reference }}</td>
            <td>{{ money(t.amount) }}</td>
            <td>
                <form method="POST" action="{{ url_for('delete_bank_tx', id=t.id) }}" onsubmit="return confirm('Delete this movement?');">
                    <button type="submit" class="btn-secondary">Delete</button>
                </form>
            </td>
        </tr>
    {% endfor %}
    </tbody>"""
    NEW_MOV = """    <thead><tr><th>Date</th><th>Account</th><th>Type</th><th>Party</th><th>Ref</th><th>Amount</th><th>Reconciled</th><th></th></tr></thead>
    <tbody>
    {% for t in txs %}
        <tr {% if not t.reconciled %}style="background:rgba(224,160,48,0.04);"{% endif %}>
            <td>{{ t.tx_date }}</td>
            <td>{{ t.account_name }}</td>
            <td>{{ t.kind }}</td>
            <td>{{ t.counterparty }}</td>
            <td>{{ t.reference }}</td>
            <td>{{ money(t.amount) }}</td>
            <td>
                <form method="POST" action="{{ url_for('reconcile_bank_tx', id=t.id) }}" style="display:inline;">
                    {% if t.reconciled %}
                        <span class="status-pill status-ok">✓ {{ t.reconciled_date or 'yes' }}</span>
                        <button type="submit" class="btn-secondary" style="padding:2px 8px;font-size:0.75rem;">Undo</button>
                    {% else %}
                        <button type="submit" class="btn-secondary" style="padding:2px 8px;font-size:0.75rem;">Mark</button>
                    {% endif %}
                </form>
            </td>
            <td>
                <form method="POST" action="{{ url_for('delete_bank_tx', id=t.id) }}" onsubmit="return confirm('Delete this movement?');">
                    <button type="submit" class="btn-secondary">Delete</button>
                </form>
            </td>
        </tr>
    {% endfor %}
    </tbody>"""
    if OLD_MOV not in bank:
        print("  [FAIL] banking.html recent-movements table markup did not match expected pattern")
        FAILED.append("banking.html row pattern")
    else:
        bank = bank.replace(OLD_MOV, NEW_MOV, 1)
        # Add reconcile summary under the stat grid
        RECONCILE_ANCHOR = '<h2>Accounts</h2>'
        RECONCILE_BLOCK = '''<div class="widget" id="reconcile">
    <h2 style="margin-top:0;">Reconciliation</h2>
    <p style="color:var(--text2);font-size:0.9rem;">Rows without a ✓ are not yet matched against your bank statement. Use the "Mark" button in the recent movements table below.</p>
</div>

<h2>Accounts</h2>'''
        if RECONCILE_ANCHOR in bank:
            bank = bank.replace(RECONCILE_ANCHOR, RECONCILE_BLOCK, 1)
        try:
            Environment().parse(bank)
        except Exception as exc:
            print(f"  [FAIL] banking.html has Jinja syntax error: {exc}")
            FAILED.append("banking.html jinja")
        else:
            with open(bank_path, 'w', encoding='utf-8') as f:
                f.write(bank)
            print("  [OK]   banking.html — reconcile column + section")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/8] Modify tasks.html — blocker column + inline edit")
# ═══════════════════════════════════════════════════════════════════

tasks_path = os.path.join(TPL_DIR, 'tasks.html')
if not os.path.isfile(tasks_path):
    print(f"  [FAIL] {tasks_path} not found")
    FAILED.append("tasks.html")
else:
    with open(tasks_path, encoding='utf-8') as f:
        tasks = f.read()
    OLD_TASKS_HEADER = """<thead><tr><th></th><th>Status</th><th>Task</th><th>Priority</th><th>Due</th><th>Action</th></tr></thead>"""
    NEW_TASKS_HEADER = """<thead><tr><th></th><th>Status</th><th>Task</th><th>Priority</th><th>Due</th><th>Blocker</th><th>Action</th></tr></thead>"""
    OLD_TASKS_ROW = """    <td>{{ item.priority }}</td>
    <td>{{ item.due_date or '—' }}</td>
    <td>
        <a href="{{ url_for('toggle_task', id=item.id) }}">{% if item.done %}Reopen{% else %}Complete{% endif %}</a>
        <a href="{{ url_for('delete_task', id=item.id) }}" class="delete-btn" onclick="return confirm('Delete this task?')">Delete</a>
    </td>"""
    NEW_TASKS_ROW = """    <td>{{ item.priority }}</td>
    <td>{{ item.due_date or '—' }}</td>
    <td>
        <form method="POST" action="{{ url_for('save_task_blocker', id=item.id) }}" style="display:flex;gap:0.3rem;align-items:center;">
            <input type="text" name="blocker_note" value="{{ item.blocker_note or '' }}" placeholder="—" maxlength="500" style="font-size:0.82rem;padding:4px 6px;min-width:120px;">
            <button type="submit" class="btn-secondary" style="padding:2px 8px;font-size:0.75rem;">Save</button>
        </form>
    </td>
    <td>
        <a href="{{ url_for('toggle_task', id=item.id) }}">{% if item.done %}Reopen{% else %}Complete{% endif %}</a>
        <a href="{{ url_for('delete_task', id=item.id) }}" class="delete-btn" onclick="return confirm('Delete this task?')">Delete</a>
    </td>"""
    OLD_EMPTY = """<tr><td colspan="6">No tasks yet.</td></tr>"""
    NEW_EMPTY = """<tr><td colspan="7">No tasks yet.</td></tr>"""
    ok_tasks = True
    for old, new, label in [
        (OLD_TASKS_HEADER, NEW_TASKS_HEADER, 'header'),
        (OLD_TASKS_ROW, NEW_TASKS_ROW, 'row'),
        (OLD_EMPTY, NEW_EMPTY, 'empty'),
    ]:
        if old in tasks:
            tasks = tasks.replace(old, new, 1)
        else:
            print(f"  [FAIL] tasks.html — {label} pattern not found")
            ok_tasks = False
    if ok_tasks:
        try:
            Environment().parse(tasks)
        except Exception as exc:
            print(f"  [FAIL] tasks.html Jinja error: {exc}")
            FAILED.append("tasks.html jinja")
        else:
            with open(tasks_path, 'w', encoding='utf-8') as f:
                f.write(tasks)
            print("  [OK]   tasks.html — blocker column + inline edit")

# ═══════════════════════════════════════════════════════════════════
print("\n[6/8] Modify bookkeeping_type.html — approval column + actions")
# ═══════════════════════════════════════════════════════════════════

bktype_path = os.path.join(TPL_DIR, 'bookkeeping_type.html')
if not os.path.isfile(bktype_path):
    print(f"  [FAIL] {bktype_path} not found")
    FAILED.append("bookkeeping_type.html")
else:
    with open(bktype_path, encoding='utf-8') as f:
        bk = f.read()
    OLD_BK_HEAD = """<thead><tr><th>Title</th><th>Party</th><th>Ref</th><th>Date</th><th>Amount</th><th>Status</th><th>Action</th></tr></thead>"""
    NEW_BK_HEAD = """<thead><tr><th>Title</th><th>Party</th><th>Ref</th><th>Date</th><th>Amount</th><th>Status</th><th>Approval</th><th>Action</th></tr></thead>"""
    OLD_BK_ROW = """    <td><span class="status-pill">{{ item.status }}</span></td>
    <td>
        <a href="{{ url_for('bookkeeping_pdf', id=item.id) }}">PDF</a>"""
    NEW_BK_ROW = """    <td><span class="status-pill">{{ item.status }}</span></td>
    <td>
        <form method="POST" action="{{ url_for('approve_book_doc', id=item.id) }}" style="display:flex;gap:0.3rem;align-items:center;flex-wrap:wrap;">
            <select name="decision" style="font-size:0.8rem;padding:3px 5px;">
                <option value="none" {% if item.approval_status == 'none' %}selected{% endif %}>—</option>
                <option value="approved" {% if item.approval_status == 'approved' %}selected{% endif %}>✓ Approved</option>
                <option value="rejected" {% if item.approval_status == 'rejected' %}selected{% endif %}>✗ Rejected</option>
            </select>
            <button type="submit" class="btn-secondary" style="padding:2px 8px;font-size:0.75rem;">Set</button>
        </form>
    </td>
    <td>
        <a href="{{ url_for('bookkeeping_pdf', id=item.id) }}">PDF</a>"""
    OLD_BK_EMPTY = """<tr><td colspan="7">None yet. Create the first {{ label }} above.</td></tr>"""
    NEW_BK_EMPTY = """<tr><td colspan="8">None yet. Create the first {{ label }} above.</td></tr>"""
    ok_bk = True
    for old, new, label in [
        (OLD_BK_HEAD, NEW_BK_HEAD, 'header'),
        (OLD_BK_ROW, NEW_BK_ROW, 'row'),
        (OLD_BK_EMPTY, NEW_BK_EMPTY, 'empty'),
    ]:
        if old in bk:
            bk = bk.replace(old, new, 1)
        else:
            print(f"  [FAIL] bookkeeping_type.html — {label} pattern not found")
            ok_bk = False
    if ok_bk:
        try:
            Environment().parse(bk)
        except Exception as exc:
            print(f"  [FAIL] bookkeeping_type.html Jinja error: {exc}")
            FAILED.append("bookkeeping_type.html jinja")
        else:
            with open(bktype_path, 'w', encoding='utf-8') as f:
                f.write(bk)
            print("  [OK]   bookkeeping_type.html — approval column + actions")

# ═══════════════════════════════════════════════════════════════════
print("\n[7/8] Modify bookkeeping.html — pending approval count")
# ═══════════════════════════════════════════════════════════════════

bk_path = os.path.join(TPL_DIR, 'bookkeeping.html')
if not os.path.isfile(bk_path):
    print(f"  [SKIP] {bk_path} not found")
else:
    with open(bk_path, encoding='utf-8') as f:
        bko = f.read()
    ANCHOR = '<h2>Source documents</h2>'
    NEW_BLOCK = '''<div class="widget" id="approvals">
    <h2 style="margin-top:0;">Approval status</h2>
    <p style="color:var(--text2);font-size:0.9rem;margin:0;">Open any document type below and use the Approval column to mark it approved or rejected. Approved documents are ready to file; rejected ones need fixing.</p>
</div>

<h2>Source documents</h2>'''
    if ANCHOR in bko and 'id="approvals"' not in bko:
        bko = bko.replace(ANCHOR, NEW_BLOCK, 1)
        try:
            Environment().parse(bko)
        except Exception as exc:
            print(f"  [FAIL] bookkeeping.html Jinja error: {exc}")
            FAILED.append("bookkeeping.html jinja")
        else:
            with open(bk_path, 'w', encoding='utf-8') as f:
                f.write(bko)
            print("  [OK]   bookkeeping.html — approvals section")
    else:
        print("  [SKIP] bookkeeping.html — anchor not found or already patched")

# ═══════════════════════════════════════════════════════════════════
print("\n[8/8] Write app.py + final compile check")
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
print(f"  New routes added:        6 (3 actions + 3 redirects)")
print(f"  Schema columns added:    7")
print(f"  Templates modified:      4")
print(f"  @app.route: {initial_routes} -> {final_routes}")
print("=" * 62)

if removed != 3 or FAILED:
    print("\nSome changes did not land:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    print(f"Restore templates: *bak.batch3a_{STAMP}")
    sys.exit(1)

print("""
Batch 3a complete. Note: /settings/audit was moved to Batch 3b for
cleanliness (it modifies the settings save route, not just a column).

NEXT STEPS:

1. LOCAL TEST — run:  python app.py
   (Verify $env:DATABASE_URL is set)

   /banking      -> scroll down past the three form cards
                    -> "Reconciliation" widget appears
                    -> Recent movements table has new "Reconciled" column
                    -> Click "Mark" on any row -> turns green with date
                    -> Click "Undo" -> back to unreconciled

   /tasks        -> the tasks table now has a "Blocker" column
                    -> Type a note in the input for any task -> Save
                    -> Value persists after reload

   /bookkeeping  -> scroll down -> "Approval status" widget appears

   /bookkeeping/<any-kind>  e.g. /bookkeeping/invoice
                    -> Each row now has "Approval" column with dropdown
                    -> Change to "Approved", click Set -> persists

   Redirects:
     /banking/reconcile    -> /banking#reconcile
     /tasks/blockers       -> /tasks#blockers
     /documents/approval   -> /bookkeeping

   Regression — verify:
     /dashboard, /plans (Active), /banking (all forms still work),
     /tasks (complete/reopen still work),
     /bookkeeping (doc types still list),
     /bookkeeping/<kind> (create new doc still works)

2. REPORT BACK with:
   - /banking has reconcile column + Mark works?
   - /tasks has blocker column + Save works?
   - /bookkeeping/<kind> has approval column + Set works?
   - 3 redirects work?
   - Regression pass?

3. Only after I confirm, commit + push + deploy.

4. Test on production.

5. Only after prod pass:
     rm app.py.bak.batch3a_*
     rm templates/*.bak.batch3a_*

REMAINING DISABLED after 3a: 6 routes (all Batch 3b)
  /settings/audit
  /health/history
  /payments/fees (TBD)
  /whatsapp/log (TBD — likely delete)
  /whatsapp/templates
  /documents/versions
""")