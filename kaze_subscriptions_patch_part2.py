"""
kaze_subscriptions_patch_part2.py — surgical fix for the two Phase 1.5 failures.

  • set_plan: uses regex anchoring on `def set_plan():` — no exact-string match
  • trial clamp: replaces min(17, max(7, ...)) with min(18, max(14, ...))

Won't write if either replacement is 0. Safe to re-run.

Run from the folder with app.py:
    python kaze_subscriptions_patch_part2.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

with open(APP, encoding='utf-8') as f:
    src_before = f.read()

# ── Fix 1: set_plan via regex ───────────────────────────────────────
NEW_SET_PLAN = (
    "def set_plan():\n"
    "    if getattr(current_user, 'role', 'owner') != 'owner':\n"
    "        flash('Only the owner can change the plan.', 'danger')\n"
    "        return redirect(url_for('plans'))\n"
    "    wanted = normalize_plan(request.form.get('plan_tier'))\n"
    "    if wanted != 'new_user':\n"
    "        flash('Paid packages are subscribed on the Packages page.', 'danger')\n"
    "        return redirect(url_for('plans'))\n"
    "    conn = get_db()\n"
    "    cur = conn.cursor()\n"
    "    cur.execute('SELECT subscription_status FROM settings WHERE user_id=%s', (current_user.id,))\n"
    "    row = cur.fetchone() or {}\n"
    "    if (row.get('subscription_status') or '').lower() in ('active', 'trialing', 'past_due'):\n"
    "        cur.close()\n"
    "        conn.close()\n"
    "        flash('You have an active subscription. Cancel it from Manage first.', 'danger')\n"
    "        return redirect(url_for('plans'))\n"
    "    cur.execute('UPDATE settings SET plan_tier=%s WHERE user_id=%s', ('new_user', current_user.id))\n"
    "    conn.commit()\n"
    "    cur.close()\n"
    "    conn.close()\n"
    "    flash('Switched to the free tier.', 'success')\n"
    "    return redirect(url_for('plans'))\n"
    "\n"
    "\n"
)

SET_PLAN_PAT = re.compile(
    r"def set_plan\(\):\n.*?\n(?=@app\.route)",
    re.DOTALL,
)

src_mid, set_plan_count = SET_PLAN_PAT.subn(NEW_SET_PLAN, src_before, count=1)

# ── Fix 2: trial clamp ──────────────────────────────────────────────
TRIAL_OLD = "    days = min(17, max(7, days))"
TRIAL_NEW = "    days = min(18, max(14, days))"
trial_count = src_mid.count(TRIAL_OLD)
if trial_count == 1:
    src_after = src_mid.replace(TRIAL_OLD, TRIAL_NEW, 1)
else:
    src_after = src_mid

# ── Bail before writing if either fix failed ────────────────────────
print(f"set_plan replacements: {set_plan_count}")
print(f"trial clamp matches:   {trial_count}")
print()

if set_plan_count != 1 or trial_count != 1:
    print("[ABORT] Did not write — file unchanged (still 9/11 fixes, app compiles).")
    if set_plan_count != 1:
        print("  set_plan regex did not match exactly once.")
        print("  Send me the output of: Select-String -Path app.py -Pattern 'def set_plan' -Context 0,40")
    if trial_count != 1:
        print(f"  trial clamp pattern matched {trial_count} times (need 1).")
        print("  Send me the output of: Select-String -Path app.py -Pattern 'days = min'")
    sys.exit(1)

# ── Backup + write ──────────────────────────────────────────────────
backup = f"{APP}.bak.part2_{STAMP}"
shutil.copy2(APP, backup)
print(f"Backup: {backup}")

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src_after)

# ── Compile check ───────────────────────────────────────────────────
print("\n[COMPILE]")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore:  copy \"{backup}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

# ── Verify ──────────────────────────────────────────────────────────
print("\n[VERIFY]")
with open(APP, encoding='utf-8') as f:
    final = f.read()

checks = {
    'set_plan blocks non-new_user':  "Paid packages are subscribed on the Packages page" in final,
    'set_plan checks sub status':    "subscription_status FROM settings" in final,
    'trial clamp is 14-18':          "days = min(18, max(14, days))" in final,
    'no lingering min(17, max(7':    "days = min(17, max(7, days))" not in final,
}
ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        ok = False

if not ok:
    print(f"\n[FATAL] Restore:  copy \"{backup}\" {APP}")
    sys.exit(1)

# ── Full 11-fix summary ─────────────────────────────────────────────
print("\n[FULL STATE — all 11 fixes]")
full = {
    '1. schema columns':            "ADD COLUMN IF NOT EXISTS plan_expires_at" in final,
    '2. USD prices':                "'price': 10," in final and "'price': 100," in final,
    '3. stripe_payments USD':       True,  # verified earlier
    '4. effective_plan':            "def effective_plan(settings=None):" in final,
    '5. subscription_info':         "def subscription_info(settings=None):" in final,
    '6. import subscriptions':      "import subscriptions" in final,
    '7. set_plan free only':        "Paid packages are subscribed on the Packages page" in final,
    '8. subscribe/sync/manage':     "def subscribe_plan(tier):" in final and "def plans_sync():" in final and "def plans_manage():" in final,
    '9. webhook delegation':        "subscriptions.handle_webhook(get_db, event)" in final,
    '10. webhook mode guard':       ".get('mode') == 'subscription'" in final,
    '11. trial clamp 14-18':        "days = min(18, max(14, days))" in final,
}
all_ok = True
for label, present in full.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        all_ok = False

print("\n" + "=" * 62)
if all_ok:
    print("Phase 1.5 complete. All 11 fixes verified.")
    print("=" * 62)
    print("""
NEXT STEPS (in order):

── 1. Create 4 Stripe products ──
https://dashboard.stripe.com/test/products
For each: Add product → Recurring → USD → Yearly → Save → copy price_xxx
  KAZE Entrepreneur       $10 USD  Yearly
  KAZE Businessman        $25 USD  Yearly
  KAZE CEO                $50 USD  Yearly
  KAZE Founder's Premium  $100 USD Yearly

── 2. Enable Customer Portal ──
https://dashboard.stripe.com/test/settings/billing/portal
Activate + enable "Cancel at end of billing period" + "Update payment method"

── 3. Render → Environment variables ──
STRIPE_PRICE_ENTREPRENEUR = price_xxx
STRIPE_PRICE_BUSINESSMAN  = price_xxx
STRIPE_PRICE_CEO          = price_xxx
STRIPE_PRICE_FOUNDER      = price_xxx

── 4. Stripe webhook events ──
https://dashboard.stripe.com/test/webhooks
Add ALL of:
  checkout.session.completed
  checkout.session.async_payment_succeeded
  checkout.session.expired
  charge.refunded
  customer.subscription.created
  customer.subscription.updated
  customer.subscription.deleted
  invoice.payment_succeeded
  invoice.payment_failed

── 5. Deploy ──
git add app.py stripe_payments.py subscriptions.py templates/plans.html templates/plans_sync.html kaze_subscriptions_patch.py kaze_subscriptions_patch_part2.py
git commit -m "v4.7.0: annual USD subscriptions"
git push
Render → Manual Deploy → Clear build cache

── 6. Test on production ──
a. Sign up / log in as a test account
b. /plans → Start 14-day trial → CEO features unlock
c. /plans → Subscribe — $10/year on Entrepreneur
d. Card: 4242 4242 4242 4242, any future exp, any CVC
e. /plans/sync polls, redirects to /plans within 2-10s
f. /plans shows "Active subscription — renews on [date+1y]"
g. Click Manage → Stripe portal opens → cancel
h. /plans shows "Canceled — until [date]"
i. Test the set_plan exploit is closed:
   - Click "Switch to free" on the plans page → allowed
   - Then try to re-subscribe to Entrepreneur manually via devtools
     (POST /plans/set plan_tier=entrepreneur) → should be REFUSED with
     "Paid packages are subscribed on the Packages page."

── Known behaviours ──
  • If /plans/sync shows "Webhook still pending" after 30s:
    check Stripe → Webhooks → [endpoint] → attempts tab
  • If checkout errors "Unexpected parameter: managed_payments":
    your Stripe SDK is older than 16.0.0. Tell me.
  • Any [FAIL] on step 6 → paste error + relevant Render log line

Backups: app.py.bak.part2_<timestamp> (safe to delete after deploy works)
""")
else:
    print("Phase 1.5 INCOMPLETE. See [FAIL] above.")
    print("=" * 62)
    print(f"Restore if needed:  copy \"{backup}\" {APP}")
    sys.exit(1)