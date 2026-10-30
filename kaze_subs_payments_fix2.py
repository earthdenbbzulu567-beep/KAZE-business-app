"""
kaze_subs_payments_fix2.py — replace handle_invoice_succeeded by regex.

Prior fix failed because the current function body differs from what the
original script's exact-match pattern expected (has `import time as _time`
instead of `datetime.today().timestamp()`, from an earlier batch).

This script uses a regex anchor on the function name and replaces everything
up to the next top-level def — ignores inner content entirely.

Does NOT touch app.py — the invoice_id column is already applied there.

Run from the folder with app.py:
    python kaze_subs_payments_fix2.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
SUBS = 'subscriptions.py'
APP = 'app.py'

if not os.path.isfile(SUBS):
    print(f"ERROR: {SUBS} not found.")
    sys.exit(1)

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

# ── Backup ──────────────────────────────────────────────────────────
b = f"{SUBS}.bak.subspay2_{STAMP}"
shutil.copy2(SUBS, b)
print(f"Backup: {b}")

# ── Confirm schema already applied in app.py (don't re-run schema) ──
with open(APP, encoding='utf-8') as f:
    app_src = f.read()
if "invoice_id TEXT DEFAULT ''" not in app_src:
    print("[FAIL] app.py doesn't have invoice_id column yet.")
    print("       Re-run the original kaze_subs_payments_fix.py first.")
    sys.exit(1)
print("[OK] app.py schema (invoice_id column) already present — skipping")

# ── Replace handler in subscriptions.py by regex ────────────────────
with open(SUBS, encoding='utf-8') as f:
    subs_src = f.read()

NEW_HANDLER = '''def handle_invoice_succeeded(get_db, event):
    inv = event['data']['object']
    sub_id = inv.get('subscription')
    customer_id = inv.get('customer')
    # Skip non-subscription invoices (those are handled by
    # checkout.session.completed / _fulfill_stripe_payment)
    if not sub_id:
        return
    user_id = _find_user(get_db, 'subscription', sub_id)
    if not user_id:
        user_id = _find_user(get_db, 'customer', customer_id)
    if not user_id:
        return
    period_end = inv.get('period_end')
    if not period_end:
        try:
            period_end = inv['lines']['data'][0]['period']['end']
        except (KeyError, IndexError, TypeError):
            import time as _time
            period_end = int(_time.time()) + 365 * 86400
    expires_iso = _unix_to_iso(period_end)
    today_iso = datetime.today().strftime('%Y-%m-%d')

    # Extract invoice details for /payments log
    inv_id = inv.get('id') or ''
    pi_id = inv.get('payment_intent') or ''
    try:
        amount_raw = float(inv.get('amount_paid') or inv.get('total') or 0)
    except (TypeError, ValueError):
        amount_raw = 0.0
    currency = (inv.get('currency') or 'usd').upper()
    import stripe_payments as _sp
    amount_display = _sp.from_stripe_amount(int(amount_raw), currency)
    title = ''
    try:
        lines = inv['lines']['data']
        if lines:
            title = (lines[0].get('description') or '')[:160]
    except (KeyError, IndexError, TypeError):
        title = ''
    if not title:
        title = 'KAZE subscription'

    conn = get_db()
    cur = conn.cursor()

    # 1. Extend plan_expires_at (existing behavior)
    cur.execute("""
        UPDATE settings SET
            plan_expires_at=%s,
            subscription_status='active',
            grace_expires_at=''
        WHERE user_id=%s
    """, (expires_iso, user_id))

    # 2. Record the payment in stripe_payments (idempotent by invoice_id)
    if inv_id:
        cur.execute(
            "SELECT id FROM stripe_payments WHERE user_id=%s AND invoice_id=%s LIMIT 1",
            (user_id, inv_id))
        existing = cur.fetchone()
        if not existing:
            cur.execute(
                "INSERT INTO stripe_payments "
                "(user_id, kind, record_id, amount, currency, status, "
                " checkout_id, payment_intent, invoice_id, title, "
                " provider, created_date, paid_date) "
                "VALUES (%s, 'subscription', 0, %s, %s, 'paid', "
                " %s, %s, %s, %s, 'stripe', %s, %s)",
                (user_id, amount_display, currency,
                 inv_id, pi_id, inv_id, title,
                 today_iso, today_iso))

    conn.commit()
    cur.close()
    conn.close()


'''

pattern = re.compile(
    r"def handle_invoice_succeeded\(get_db, event\):\n"
    r".*?"
    r"(?=\ndef |\nclass |\Z)",
    re.DOTALL,
)

new_src, count = pattern.subn(NEW_HANDLER, subs_src, count=1)
if count != 1:
    print(f"[FAIL] Expected 1 match, got {count}. No changes made.")
    print("       Send output of:")
    print("       Select-String -Path subscriptions.py -Pattern 'def handle_invoice'")
    sys.exit(1)

with open(SUBS, 'w', encoding='utf-8') as f:
    f.write(new_src)
print("[OK] handle_invoice_succeeded replaced (regex anchor)")

# ── Compile check ──────────────────────────────────────────────────
r = subprocess.run([sys.executable, '-m', 'py_compile', SUBS], capture_output=True, text=True)
if r.returncode != 0:
    print("[FAIL] subscriptions.py syntax error after patch:")
    print(r.stderr)
    print(f"\nRestore: copy \"{b}\" {SUBS}")
    sys.exit(1)
print("[OK] subscriptions.py compiles cleanly")

# ── Verify ─────────────────────────────────────────────────────────
with open(SUBS, encoding='utf-8') as f:
    final = f.read()

checks = {
    'invoice_id mentioned':        'invoice_id' in final,
    'stripe_payments INSERT':      "INSERT INTO stripe_payments" in final,
    'idempotency SELECT':          "SELECT id FROM stripe_payments WHERE user_id=%s AND invoice_id" in final,
    'skips non-sub invoices':      "if not sub_id:" in final,
}
all_ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        all_ok = False

if not all_ok:
    print(f"\n[FATAL] Verify failed. Restore: copy \"{b}\" {SUBS}")
    sys.exit(1)

print()
print("=" * 62)
print("Fix applied.")
print("=" * 62)
print("""
NEXT STEPS:

1. LOCAL TEST — the fix only works when a NEW invoice fires.
   Existing subs won't retroactively appear. To test:

   a. python app.py
   b. Go to /plans -> Manage -> Cancel immediately in Stripe Portal
   c. Back to /plans -> Subscribe — $100/year on Founder's Premium
   d. Checkout with 4242 4242 4242 4242, any future date, any CVC
   e. Wait 5-10 seconds for webhook
   f. /payments -> NEW row should appear:
        What:      "KAZE subscription (subscription)"
        Amount:    $100.00 USD (or your display currency)
        Status:    Paid
   g. /payments/fees -> same row appears there too

2. Verify nothing broke:
   - /plans still shows Active
   - /payments shows both historical one-time rows AND new sub row
   - /dashboard, /bookkeeping still load

3. Commit + push + deploy:
   git add subscriptions.py kaze_subs_payments_fix2.py
   git commit -m "fix: subscription invoices recorded in /payments"
   git push

4. Prod test — same cancel+resubscribe flow.

5. Cleanup after prod:
   rm subscriptions.py.bak.subspay_*
   rm subscriptions.py.bak.subspay2_*
   (app.py backup from earlier fix is already harmless)

AFTER THIS: Phase 4a begins.
""")