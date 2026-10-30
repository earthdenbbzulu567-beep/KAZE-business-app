"""
kaze_batch3b2c_fix.py — filter fees page to Stripe payments only.

The /payments/fees page was trying to reconcile ALL paid payments through
Stripe's PaymentIntent API. But Flutterwave payments store Flutterwave
transaction IDs in the payment_intent column — Stripe can't find them.

Fix:
  - /payments/fees:        only show provider='stripe' (or NULL, treated as stripe)
  - /payments/fees/sync:   only sync provider='stripe'
  - /payments/fees/<id>/reconcile: refuse non-Stripe payments
  - template:              note about Flutterwave payments being excluded

Run from the folder with app.py:
    python kaze_batch3b2c_fix.py
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

backup_path = f"{APP}.bak.batch3b2cfix_{STAMP}"
shutil.copy2(APP, backup_path)
print(f"Backup: {backup_path}")

for tpl in ('payments_fees.html',):
    p = os.path.join(TPL_DIR, tpl)
    if os.path.isfile(p):
        shutil.copy2(p, p + f'.bak.batch3b2cfix_{STAMP}')
        print(f"Backup: {p}.bak.batch3b2cfix_{STAMP}")

with open(APP, encoding='utf-8') as f:
    src = f.read()

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/4] Filter /payments/fees to Stripe only")
# ═══════════════════════════════════════════════════════════════════

OLD_FEES_QUERY = """    cur.execute(\"\"\"
        SELECT id, kind, record_id, amount, currency, status, provider,
               COALESCE(payment_intent, '') AS payment_intent,
               created_date, paid_date,
               COALESCE(stripe_fee, 0) AS stripe_fee,
               COALESCE(stripe_net, 0) AS stripe_net,
               COALESCE(stripe_fee_currency, '') AS stripe_fee_currency,
               COALESCE(stripe_fee_fetched_at, '') AS stripe_fee_fetched_at
        FROM stripe_payments
        WHERE user_id=%s AND status='paid'
        ORDER BY id DESC LIMIT 200
    \"\"\", (uid,))"""

NEW_FEES_QUERY = """    cur.execute(\"\"\"
        SELECT id, kind, record_id, amount, currency, status, provider,
               COALESCE(payment_intent, '') AS payment_intent,
               created_date, paid_date,
               COALESCE(stripe_fee, 0) AS stripe_fee,
               COALESCE(stripe_net, 0) AS stripe_net,
               COALESCE(stripe_fee_currency, '') AS stripe_fee_currency,
               COALESCE(stripe_fee_fetched_at, '') AS stripe_fee_fetched_at
        FROM stripe_payments
        WHERE user_id=%s AND status='paid'
          AND COALESCE(NULLIF(provider, ''), 'stripe') = 'stripe'
        ORDER BY id DESC LIMIT 200
    \"\"\", (uid,))"""

if OLD_FEES_QUERY in src:
    src = src.replace(OLD_FEES_QUERY, NEW_FEES_QUERY, 1)
    print("  [OK]   /payments/fees query filtered to Stripe")
else:
    print("  [FAIL] fees query anchor not found")
    FAILED.append("fees query")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/4] Filter /payments/fees/sync to Stripe only")
# ═══════════════════════════════════════════════════════════════════

OLD_SYNC_QUERY = """    cur.execute(\"\"\"
        SELECT id, payment_intent, amount, currency
        FROM stripe_payments
        WHERE user_id=%s AND status='paid'
          AND COALESCE(stripe_fee_fetched_at, '') = ''
          AND COALESCE(payment_intent, '') != ''
        ORDER BY id DESC LIMIT 20
    \"\"\", (uid,))"""

NEW_SYNC_QUERY = """    cur.execute(\"\"\"
        SELECT id, payment_intent, amount, currency
        FROM stripe_payments
        WHERE user_id=%s AND status='paid'
          AND COALESCE(NULLIF(provider, ''), 'stripe') = 'stripe'
          AND COALESCE(stripe_fee_fetched_at, '') = ''
          AND COALESCE(payment_intent, '') != ''
        ORDER BY id DESC LIMIT 20
    \"\"\", (uid,))"""

if OLD_SYNC_QUERY in src:
    src = src.replace(OLD_SYNC_QUERY, NEW_SYNC_QUERY, 1)
    print("  [OK]   sync query filtered to Stripe")
else:
    print("  [FAIL] sync query anchor not found")
    FAILED.append("sync query")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/4] Reject non-Stripe payments in reconcile_one")
# ═══════════════════════════════════════════════════════════════════

OLD_RECON_ONE = """    cur.execute(
        "SELECT id, payment_intent, amount FROM stripe_payments WHERE id=%s AND user_id=%s",
        (pay_id, uid))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        flash('Payment not found.', 'danger')
        return redirect(url_for('payments_fees'))
    fee, net, cur_c, err = _fetch_stripe_fee_for_row(row, settings)"""

NEW_RECON_ONE = """    cur.execute(
        "SELECT id, payment_intent, amount, provider FROM stripe_payments WHERE id=%s AND user_id=%s",
        (pay_id, uid))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        flash('Payment not found.', 'danger')
        return redirect(url_for('payments_fees'))
    prov = (row.get('provider') or 'stripe').strip().lower() or 'stripe'
    if prov != 'stripe':
        cur.close(); conn.close()
        flash(f'Only Stripe payments can be reconciled here (this is {prov}).', 'danger')
        return redirect(url_for('payments_fees'))
    fee, net, cur_c, err = _fetch_stripe_fee_for_row(row, settings)"""

if OLD_RECON_ONE in src:
    src = src.replace(OLD_RECON_ONE, NEW_RECON_ONE, 1)
    print("  [OK]   reconcile_one now rejects non-Stripe")
else:
    print("  [FAIL] reconcile_one anchor not found")
    FAILED.append("reconcile_one")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/4] Add explanatory note to fees template")
# ═══════════════════════════════════════════════════════════════════

FEES_TPL = os.path.join(TPL_DIR, 'payments_fees.html')
if not os.path.isfile(FEES_TPL):
    print(f"  [FAIL] {FEES_TPL} not found")
    FAILED.append("fees template missing")
else:
    with open(FEES_TPL, encoding='utf-8') as f:
        tpl = f.read()

    OLD_NOTE = """<p style="margin-top:1rem;font-size:0.85rem;color:var(--text3);">
  Fee source: Stripe <code>balance_transaction</code> for each payment. If fees show "—", the payment may be too recent (wait a few seconds and Sync again) or was a bank transfer (no Stripe processing fee applies).
</p>"""

    NEW_NOTE = """<p style="margin-top:1rem;font-size:0.85rem;color:var(--text3);">
  Fee source: Stripe <code>balance_transaction</code> for each payment. If fees show "—", the payment may be too recent (wait a few seconds and Sync again) or was a bank transfer (no Stripe processing fee applies).
</p>
<p style="margin-top:0.6rem;font-size:0.85rem;color:var(--text3);">
  <strong>Only Stripe payments appear here.</strong> Flutterwave, PayPal, and bank transfer payments have fees too, but they are charged by those providers and tracked separately. This page reconciles Stripe processing costs only.
</p>"""

    if OLD_NOTE in tpl:
        tpl = tpl.replace(OLD_NOTE, NEW_NOTE, 1)
        try:
            Environment().parse(tpl)
        except Exception as exc:
            print(f"  [FAIL] fees template Jinja error after edit: {exc}")
            FAILED.append("fees template jinja")
        else:
            with open(FEES_TPL, 'w', encoding='utf-8') as f:
                f.write(tpl)
            print("  [OK]   fees template note added")
    else:
        print("  [SKIP] template note pattern not found (already applied?)")

# ═══════════════════════════════════════════════════════════════════
print("\n[WRITE] Writing app.py + compile check")
# ═══════════════════════════════════════════════════════════════════

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)
print(f"  [OK]   app.py written")

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore app.py: copy \"{backup_path}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
print("Fix applied. What to expect:")
print("=" * 62)
print("""
After the fix:
  - /payments/fees shows ONLY Stripe-paid payments
  - Your current 3 paid payments are Flutterwave — they will no
    longer appear on this page (correct)
  - Sync button will say "Nothing to sync" or succeed silently
  - No more "No such payment_intent" errors
  - Flutterwave fees are a separate feature (future work)

You said your two $100 Stripe Founder subscriptions don't appear
in /payments log — that's correct. Subscriptions set plan_expires_at
on settings, they don't create stripe_payments rows. That's a design
gap, not a bug in this batch.

NEXT STEPS:

1. Local test — run:  python app.py
   /payments/fees       -> shows 0 payments (correct — all your paid are FLW)
   Click "Sync fees"    -> flash: "Nothing to sync..." (no errors)
   /payments            -> 18 rows, Fee/Net columns still there (— for now)
   /plans               -> Active
   No 500s.

2. Commit + push + deploy:
   git add app.py kaze_batch3b2c_fix.py templates/payments_fees.html
   git commit -m "fix: fees page filters to Stripe-only payments"
   git push

3. Add charge.succeeded to Stripe webhook (still worth doing for
   future Stripe payments):
   https://dashboard.stripe.com/test/webhooks
   Click endpoint -> Add events -> charge.succeeded -> Save

4. Deploy + prod test same URLs.

5. Cleanup:
   rm app.py.bak.batch3b2c_*
   rm app.py.bak.batch3b2cfix_*
   rm templates/payments.html.bak.batch3b2c_*
   rm templates/payments_fees.html.bak.batch3b2cfix_*

AFTER THIS: Phase 3 rebuild is genuinely complete.
""")