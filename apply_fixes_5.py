"""
apply_fixes_5.py — fix column names in /turnover and /batches
"""

import os, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
FAILED, APPLIED, SKIPPED = [], [], []

def patch(path, label, old, new):
    if not os.path.isfile(path):
        print(f"  [SKIP] {label} — {path} missing"); return
    with open(path, 'r', encoding='utf-8') as fh:
        src = fh.read()
    if old not in src:
        if new in src:
            print(f"  [SKIP] {label} — already fixed"); SKIPPED.append(label)
        else:
            print(f"  [FAIL] {label} — pattern not found"); FAILED.append(label)
        return
    b = f"{path}.bak.{STAMP}"
    if not os.path.isfile(b):
        shutil.copy2(path, b)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(src.replace(old, new))
    print(f"  [OK]   {label}")
    APPLIED.append(label)


print("[1] /turnover SQL")
patch('app.py', 'turnover column fix',
'''@app.route('/turnover')
@login_required
def turnover():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, quantity, COALESCE(cost_price,0) as cost FROM stock WHERE user_id=%s ORDER BY quantity DESC LIMIT 20", (current_user.id,))
    items = cur.fetchall()
    conn.close()
    return render_template('turnover.html', items=items)''',
'''@app.route('/turnover')
@login_required
def turnover():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT product_name AS name, quantity, COALESCE(cost_price,0) AS cost "
        "FROM stock WHERE user_id=%s ORDER BY quantity DESC LIMIT 20",
        (current_user.id,))
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('turnover.html', items=items)''')


print("\n[2] /batches SQL")
patch('app.py', 'batches column fix',
'''@app.route('/batches')
@login_required
def batches():
    # Batch/expiry tracker - simple list
    conn = get_db()
    cur = conn.cursor()
    # Assume we add a table later, for now mock or from stock
    cur.execute("SELECT name, quantity FROM stock WHERE user_id=%s LIMIT 20", (current_user.id,))
    items = cur.fetchall()
    conn.close()
    return render_template('batches.html', items=items)''',
'''@app.route('/batches')
@login_required
def batches():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT product_name AS name, quantity, unit FROM stock "
        "WHERE user_id=%s ORDER BY product_name LIMIT 50",
        (current_user.id,))
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('batches.html', items=items)''')


print("\nVerifying app.py compiles…")
r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK]   app.py compiles cleanly.")
else:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)

print("\n" + "=" * 60)
print(f"Applied: {len(APPLIED)}   Skipped: {len(SKIPPED)}   Failed: {len(FAILED)}")
if FAILED:
    for f in FAILED: print(f"  - {f}")
print("=" * 60)