"""
kaze_fix_stripe_event.py — convert Stripe Event objects to dicts.

Stripe SDK 16.0.0 changed `stripe.Webhook.construct_event()` to return a
`stripe.Event` object with no `.get()` method. Every webhook handler in the
app does `event.get('type')` — which throws AttributeError → 500.

Fix: convert the event to a plain dict inside `stripe_payments.parse_webhook()`
BEFORE it's returned to any caller. Then every `.get(...)` and `[...]` works.

Run from the folder with app.py:
    python kaze_fix_stripe_event.py
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
SP = 'stripe_payments.py'

if not os.path.isfile(SP):
    print(f"ERROR: {SP} not found.")
    sys.exit(1)

with open(SP, encoding='utf-8') as f:
    src = f.read()

# ── Check current state ─────────────────────────────────────────────
if 'construct_event' not in src:
    print("[FAIL] 'construct_event' not found in stripe_payments.py.")
    print("       Your file may have been modified. Send me the parse_webhook block.")
    sys.exit(1)

if '_kaze_event_to_dict' in src:
    print("[SKIP] Already patched — _kaze_event_to_dict is present.")
    print("       If you're still seeing webhook 500s, the fix isn't deployed yet.")
    print("       Commit and push, then let Render redeploy.")
    sys.exit(0)

OLD_PARSE = """def parse_webhook(payload, sig_header, settings=None):
    _, _, webhook = keys_from(settings)
    if not stripe_available():
        return None, 'stripe package missing'
    import stripe
    if not webhook:
        return None, 'STRIPE_WEBHOOK_SECRET is not set.'
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook)
        return event, None
    except Exception as exc:
        return None, str(exc)"""

NEW_PARSE = """def _kaze_event_to_dict(event):
    \"\"\"Stripe SDK 16.0.0+ returns StripeObject, not dict. Convert it.
    Every handler downstream expects dicts so .get() and [...] work.\"\"\"
    if event is None:
        return None
    if isinstance(event, dict):
        return event
    try:
        if hasattr(event, 'to_dict_recursive'):
            return event.to_dict_recursive()
        if hasattr(event, 'to_dict'):
            return event.to_dict()
    except Exception:
        pass
    try:
        import json as _json
        return _json.loads(str(event))
    except Exception:
        return None


def parse_webhook(payload, sig_header, settings=None):
    _, _, webhook = keys_from(settings)
    if not stripe_available():
        return None, 'stripe package missing'
    import stripe
    if not webhook:
        return None, 'STRIPE_WEBHOOK_SECRET is not set.'
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook)
        event = _kaze_event_to_dict(event)
        if event is None:
            return None, 'Event parsed but could not be converted to dict.'
        return event, None
    except Exception as exc:
        return None, str(exc)"""

if OLD_PARSE not in src:
    print("[FAIL] parse_webhook body did not match expected pattern.")
    print("       Send me the current parse_webhook function from stripe_payments.py.")
    sys.exit(1)

backup = f"{SP}.bak.{STAMP}"
shutil.copy2(SP, backup)
print(f"Backup: {backup}")

with open(SP, 'w', encoding='utf-8') as f:
    f.write(src.replace(OLD_PARSE, NEW_PARSE, 1))
print("[OK]   parse_webhook now converts Event → dict")

# ── Compile check ───────────────────────────────────────────────────
print("\n[COMPILE] stripe_payments.py")
r = subprocess.run([sys.executable, '-m', 'py_compile', SP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore: copy \"{backup}\" {SP}")
    sys.exit(1)
print("  [OK]   compiles cleanly")

print("\n[COMPILE] app.py (sanity — unchanged)")
r2 = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'], capture_output=True, text=True)
if r2.returncode != 0:
    print("  [FAIL] " + r2.stderr)
    sys.exit(1)
print("  [OK]   app.py still compiles")

# ── Verify ──────────────────────────────────────────────────────────
print("\n[VERIFY]")
with open(SP, encoding='utf-8') as f:
    final = f.read()
checks = {
    '_kaze_event_to_dict defined':   'def _kaze_event_to_dict(event):' in final,
    'to_dict_recursive used':        'to_dict_recursive' in final,
    'parse_webhook calls converter': 'event = _kaze_event_to_dict(event)' in final,
    'returns dict not Event':        'return event, None' in final,
}
ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        ok = False

if not ok:
    print(f"\n[FATAL] Restore: copy \"{backup}\" {SP}")
    sys.exit(1)

print("\n" + "=" * 62)
print("Fix applied. Ready to deploy.")
print("=" * 62)
print("""
NEXT STEPS:

1. Commit and push:

   git add stripe_payments.py kaze_fix_stripe_event.py
   git commit -m "fix: Stripe SDK 16 Event -> dict conversion in webhooks"
   git push

2. Wait for Render "Your service is live" (~60-90s).

3. Do NOT re-run the subscription checkout. Stripe already has your
   payment. The webhook will retry automatically.

4. Watch the retry:

   Stripe Dashboard -> Developers -> Webhooks -> your endpoint -> Attempts
   The most recent attempt should flip from 500 to 200 within 1-3 minutes.
   If it stays 500, click the attempt and read the new error.

5. Verify the subscription activated:

   /plans -> should now show "Active subscription — renews on [date]"
   If it still shows "Subscribe", wait 2 more minutes for the retry.

   OR check DB directly (Render -> Postgres -> query):
   SELECT plan_tier, plan_expires_at, subscription_status
   FROM settings WHERE user_id = <your_test_id>;

   Expected: entrepreneur / ~1yr from today / active

6. Then run the remaining tests:
   - Test 4 (cancel via Manage portal)
   - Test 5 (exploit closed — POST /plans/set with plan_tier=founder)

If Step 4 still shows 500 after the fix deploys, paste the NEW error from
the Stripe attempts tab — it will be a different error message, and I'll
write a targeted fix.

Backup: stripe_payments.py.bak.<timestamp>  (delete once deployed and tested)
""")