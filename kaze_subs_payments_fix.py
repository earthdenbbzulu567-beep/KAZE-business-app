"""
kaze_subs_payments_fix.py — record subscription invoices in /payments log.

Problem: /payments only shows one-time payments. Subscriptions set
plan_expires_at on settings but never create a stripe_payments row.
So revenue from subscriptions is invisible in the payment log.

Fix:
  1. Add invoice_id column to stripe_payments (idempotency key)
  2. Extend subscriptions.handle_invoice_succeeded to insert a
     stripe_payments row per subscription invoice (idempotent by invoice_id)

After deploy: subscription renewals and new subscriptions appear in
/payments and /payments/fees. Historical invoices before this deploy
do NOT retroactively appear (no backfill).

Run from the folder with app.py:
    python kaze_subs_payments_fix.py
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
SUBS = 'subscriptions.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)
if not os.path.isfile(SUBS):
    print(f"ERROR: {SUBS} not found.")
    sys.exit(1)

for path in (APP, SUBS):
    b = f"{path}.bak.subspay_{STAMP}"
    shutil.copy2(path, b)
    print(f"Backup: {b}")

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/4] Schema — invoice_id column on stripe_payments")
# ═══════════════════════════════════════════════════════════════════

with open(APP, encoding='utf-8') as f:
    src = f.read()

SCHEMA_ANCHOR = """    cur.execute("ALTER TABLE stripe_payments ADD COLUMN IF NOT EXISTS stripe_fee_fetched_at TEXT DEFAULT ''")"""
SCHEMA_NEW = """    cur.execute("ALTER TABLE stripe_payments ADD COLUMN IF NOT EXISTS stripe_fee_fetched_at TEXT DEFAULT ''")
    cur.execute("ALTER TABLE stripe_payments ADD COLUMN IF NOT EXISTS invoice_id TEXT DEFAULT ''")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stripe_invoice ON stripe_payments (user_id, invoice_id)")"""

if SCHEMA_ANCHOR in src:
    src = src.replace(SCHEMA_ANCHOR, SCHEMA_NEW, 1)
    print("  [OK]   added invoice_id column + index")
else:
    print("  [FAIL] schema anchor not found")
    FAILED.append("schema")

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)

# ═══════════════════════════════════════════════════════════════════
print("\n[2/4] Extend handle_invoice_succeeded to write stripe_payments row")
# ═══════════════════════════════════════════════════════════════════

with open(SUBS, encoding='utf-8') as f:
    subs_src = f.read()

OLD_HANDLER = """def handle_invoice_succeeded(get_db, event):
    inv = event['data']['object']
    sub_id = inv.get('subscription')
    customer_id = inv.get('customer')
    user_id = _find_user(get_db, 'subscription', sub_id) if sub_id else None
    if not user_id:
        user_id = _find_user(get_db, 'customer', customer_id)
    if not user_id:
        return
    period_end = inv.get('period_end')
    if not period_end:
        try:
            period_end = inv['lines']['data'][0]['period']['end']
        except (KeyError, IndexError, TypeError):
            period_end = int(datetime.today().timestamp()) + 365 * 86400
    expires_iso = _unix_to_iso(period_end)
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE settings SET
            plan_expires_at=%s,
            subscription_status='active',
            grace_expires_at=''
        WHERE user_id=%s
    ''', (expires_iso, user_id))
    conn.commit()
    cur.close()
    conn.close()"""

NEW_HANDLER = """def handle_invoice_succeeded(get_db, event):
    inv = event['data']['object']
    sub_id = inv.get('subscription')
    customer_id = inv.get('customer')
    # Skip non-subscription invoices (those are handled by checkout.session.completed)
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
            period_end = int(datetime.today().timestamp()) + 365 * 86400
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
    # Convert from Stripe minor units to displayed amount using existing helper
    import stripe_payments as _sp
    amount_display = _sp.from_stripe_amount(int(amount_raw), currency)
    # Title from the invoice or line item description
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
    cur.execute('''
        UPDATE settings SET
            plan_expires_at=%s,
            subscription_status='active',
            grace_expires_at=''
        WHERE user_id=%s
    ''', (expires_iso, user_id))

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
    conn.close()"""

if OLD_HANDLER in subs_src:
    subs_src = subs_src.replace(OLD_HANDLER, NEW_HANDLER, 1)
    with open(SUBS, 'w', encoding='utf-8') as f:
        f.write(subs_src)
    print("  [OK]   handle_invoice_succeeded extended to write stripe_payments row")
else:
    print("  [FAIL] handle_invoice_succeeded pattern not found")
    FAILED.append("handle_invoice_succeeded")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/4] Compile check")
# ═══════════════════════════════════════════════════════════════════

for path in (APP, SUBS):
    r = subprocess.run([sys.executable, '-m', 'py_compile', path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [FAIL] {path} syntax error:")
        print(r.stderr)
        FAILED.append(f"{path} compile")
    else:
        print(f"  [OK]   {path} compiles cleanly")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/4] Summary")
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 62)
if FAILED:
    print("Failed steps:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore app.py:  copy \"{APP}.bak.subspay_{STAMP}\" {APP}")
    print(f"Restore subs.py: copy \"{SUBS}.bak.subspay_{STAMP}\" {SUBS}")
    sys.exit(1)
print("Fix applied. Both files compile.")
print("=" * 62)
print("""
NEXT STEPS:

1. LOCAL TEST — the fix only works when a NEW invoice fires.
   Your existing subs won't retroactively appear. To test:

   a. python app.py
   b. Go to /plans
   c. Click "Manage" next to your current Founder's Premium sub
   d. In Stripe Portal: Cancel subscription -> Immediately
   e. Back to /plans -> click "Subscribe — $100/year" on Founder
   f. Complete test checkout with 4242 4242 4242 4242
   g. Wait for webhook to fire (2-10 seconds)
   h. Go to /payments -> look for a NEW row:
        "KAZE subscription (subscription)" with $100.00 amount
   i. Go to /payments/fees -> the new row should appear
      (Fee=— until you Sync, or auto-populated if charge.succeeded
       webhook is enabled)

   If the row appears -> fix works. Historical subs still won't
   appear (expected — no backfill).

2. Also verify:
   - /plans still shows Active — renews on [correct date]
   - /payments shows both historical one-time rows AND new sub row
   - /payments/fees shows the new sub row

3. COMMIT AND DEPLOY:
   git add app.py subscriptions.py kaze_subs_payments_fix.py
   git commit -m "fix: subscription invoices now recorded in /payments"
   git push

4. Prod test (same cancel+resubscribe flow).

5. After prod confirms, cleanup:
   rm app.py.bak.subspay_*
   rm subscriptions.py.bak.subspay_*

AFTER THIS DEPLOYS AND CONFIRMS: Phase 4a (base.html consolidation)
begins. Incremental as agreed. First sub-batch, no visible change —
just internal cleanup so subsequent batches have a solid foundation.
""")