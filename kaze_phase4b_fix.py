"""
kaze_phase4b_fix.py — patch the 4 backend anchors that missed.

Why they missed:
  - effective_plan has a docstring added by kaze_subscriptions_patch.py
  - settings POST no longer has 'if font_size' directly after 'package_prices'
  - settings GET return line format slightly differs

Uses regex anchors (def effective_plan(...): ...) to be robust against
inner content changes.
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

b = f"{APP}.bak.phase4bfix_{STAMP}"
shutil.copy2(APP, b)
print(f"Backup: {b}\n")

with open(APP, encoding='utf-8') as f:
    src = f.read()

FAILED = []

# ── [1/4] effective_plan ───────────────────────────────────────────
print("[1/4] Update effective_plan()...")
if 'KAZE_DEVELOPER_EMAILS' in src and 'developer_mode_enabled' in src[src.find('def effective_plan'):src.find('def plan_info')]:
    print("  [SKIP] already patched")
else:
    pattern = re.compile(
        r"def effective_plan\(settings=None\):\n.*?\n(?=\ndef |\nclass |\Z)",
        re.DOTALL,
    )
    NEW_FN = '''def effective_plan(settings=None):
    settings = settings or {}
    today = datetime.today().strftime('%Y-%m-%d')

    # Developer bypass
    dev_emails_raw = os.environ.get('KAZE_DEVELOPER_EMAILS', '')
    dev_emails = [e.strip().lower() for e in dev_emails_raw.split(',') if e.strip()]
    if current_user.is_authenticated and current_user.email.lower() in dev_emails:
        if int(settings.get('developer_mode_enabled') or 0) == 1:
            return 'founder'

    expires = str(settings.get('plan_expires_at') or '')[:10]
    if expires and expires >= today:
        return normalize_plan(settings.get('plan_tier') or 'new_user')

    grace = str(settings.get('grace_expires_at') or '')[:10]
    if grace and grace >= today:
        return normalize_plan(settings.get('plan_tier') or 'new_user')

    if trial_info(settings).get('active'):
        return 'ceo'

    return 'new_user'


'''
    src, count = pattern.subn(NEW_FN, src, count=1)
    if count != 1:
        print("  [FAIL] effective_plan regex did not match")
        FAILED.append("effective_plan")
    else:
        print("  [OK]   effective_plan replaced")

# ── [2/4] settings POST — add developer_mode_enabled read ─────────
print("[2/4] Settings POST — read developer_mode_enabled...")
ANCHOR_POST = "        plan_tier = normalize_plan((prior_keys.get('plan_tier') if prior_keys else None) or 'ceo')"
NEW_POST = """        dev_emails_raw = os.environ.get('KAZE_DEVELOPER_EMAILS', '')
        dev_emails = [e.strip().lower() for e in dev_emails_raw.split(',') if e.strip()]
        is_developer = (current_user.email.lower() in dev_emails)
        developer_mode_enabled = 1 if (is_developer and request.form.get('developer_mode_enabled') == 'on') else 0

        plan_tier = normalize_plan((prior_keys.get('plan_tier') if prior_keys else None) or 'ceo')"""

if 'developer_mode_enabled = 1 if' in src:
    print("  [SKIP] already patched")
elif ANCHOR_POST in src:
    src = src.replace(ANCHOR_POST, NEW_POST, 1)
    print("  [OK]   developer_mode_enabled calculation added")
else:
    print("  [FAIL] POST anchor not found")
    FAILED.append("settings POST")

# ── [3/4] settings UPDATE query ────────────────────────────────────
print("[3/4] Settings UPDATE query — add column...")
OLD_SQL = "bank_branch=%s\n            WHERE user_id=%s"
NEW_SQL = "bank_branch=%s,\n                developer_mode_enabled=%s\n            WHERE user_id=%s"

if 'developer_mode_enabled=%s' in src:
    print("  [SKIP] already patched")
elif OLD_SQL in src:
    src = src.replace(OLD_SQL, NEW_SQL, 1)
    print("  [OK]   UPDATE query includes developer_mode_enabled")
else:
    print("  [FAIL] UPDATE query anchor not found")
    FAILED.append("UPDATE query")

# ── [3b/4] settings UPDATE tuple ───────────────────────────────────
print("[3b/4] Settings UPDATE tuple — add value...")
OLD_TUPLE = "bank_branch,\n              current_user.id))"
NEW_TUPLE = "bank_branch,\n              developer_mode_enabled,\n              current_user.id))"

if 'developer_mode_enabled,\n              current_user.id))' in src:
    print("  [SKIP] already patched")
elif OLD_TUPLE in src:
    src = src.replace(OLD_TUPLE, NEW_TUPLE, 1)
    print("  [OK]   UPDATE tuple includes developer_mode_enabled")
else:
    print("  [FAIL] UPDATE tuple anchor not found")
    FAILED.append("UPDATE tuple")

# ── [4/4] settings GET — pass is_developer ────────────────────────
print("[4/4] Settings GET — pass is_developer...")
OLD_RETURN = "return render_template('settings.html', settings=settings_row, custom_modules=custom_modules, totp_on=totp_on, totp_secret=totp_secret, totp_qr=_qr_svg(_otpauth_uri(totp_secret, current_user.username)) if totp_secret else '', backup_codes=backup_codes or [])"
NEW_RETURN = """dev_emails_raw = os.environ.get('KAZE_DEVELOPER_EMAILS', '')
    dev_emails = [e.strip().lower() for e in dev_emails_raw.split(',') if e.strip()]
    is_developer = (current_user.email.lower() in dev_emails)

    return render_template('settings.html', settings=settings_row, custom_modules=custom_modules, totp_on=totp_on, totp_secret=totp_secret, totp_qr=_qr_svg(_otpauth_uri(totp_secret, current_user.username)) if totp_secret else '', backup_codes=backup_codes or [], is_developer=is_developer)"""

if 'is_developer=is_developer' in src:
    print("  [SKIP] already patched")
elif OLD_RETURN in src:
    src = src.replace(OLD_RETURN, NEW_RETURN, 1)
    print("  [OK]   is_developer passed to render_template")
else:
    print("  [FAIL] GET return anchor not found")
    FAILED.append("GET return")

# ── Write + Verify ─────────────────────────────────────────────────
with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("\n  [FAIL] app.py syntax error after patch:")
    print(r.stderr)
    print(f"\nRestore: copy \"{b}\" {APP}")
    sys.exit(1)
print("\n  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
if FAILED:
    print("Some steps failed:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore: copy \"{b}\" {APP}")
    sys.exit(1)

print("Phase 4b fix applied successfully.")
print("All 4 backend anchors patched.")
print("=" * 62)