"""
kaze_fix_period_end.py — prevent plan_expires_at from being set to today's date.

Bug: _first_period_end() returned None when the Stripe event lacked
current_period_end (thin events, API version mismatch, or partial payload).
_unix_to_iso(None) then fell back to datetime.today(), which caused the
subscription to look expired on the very next day.

Fix: always compute a sane +365-day fallback. Also log to stderr so future
failures are visible in Render logs.
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
SUB = 'subscriptions.py'

if not os.path.isfile(SUB):
    print(f"ERROR: {SUB} not found.")
    sys.exit(1)

with open(SUB, encoding='utf-8') as f:
    src = f.read()

# Check we're in the expected state
if 'def _first_period_end' not in src:
    print("[FAIL] _first_period_end not found. Already patched?")
    sys.exit(1)

# Replace the whole function
OLD_FN = """def _first_period_end(sub_obj):
    if not sub_obj:
        return None
    items = sub_obj.get('items') or {}
    data = items.get('data') or []
    if data:
        end = data[0].get('current_period_end')
        if end:
            return end
    return sub_obj.get('current_period_end')"""

NEW_FN = """def _first_period_end(sub_obj):
    \"\"\"Return unix timestamp of the current period end, or a sane fallback.

    Stripe moved current_period_end between API versions:
      - Older: at sub.current_period_end
      - 2025-03-31+: at sub.items.data[0].current_period_end
    Some events (or future API versions) may not include it at all.
    In that case, fall back to +365 days (all KAZE plans are yearly).
    \"\"\"
    if sub_obj:
        items = sub_obj.get('items') or {}
        data = items.get('data') or []
        if data:
            end = data[0].get('current_period_end')
            if end:
                return int(end)
        end = sub_obj.get('current_period_end')
        if end:
            return int(end)
    # Sane fallback: +365 days from now (all KAZE plans are yearly).
    import sys as _sys
    import time as _time
    _sys.stderr.write(
        'KAZE WARN: _first_period_end could not find current_period_end; '
        'falling back to now+365 days\\n'
    )
    return int(_time.time()) + 365 * 86400"""

if OLD_FN not in src:
    print("[FAIL] _first_period_end body did not match expected pattern.")
    print("       Send me the current function from subscriptions.py.")
    sys.exit(1)

backup = f"{SUB}.bak.{STAMP}"
shutil.copy2(SUB, backup)
print(f"Backup: {backup}")

with open(SUB, 'w', encoding='utf-8') as f:
    f.write(src.replace(OLD_FN, NEW_FN, 1))
print("[OK]   _first_period_end has +365-day fallback")

# Also guard handle_invoice_succeeded's fallback (should already be correct,
# but belt-and-braces)
with open(SUB, encoding='utf-8') as f:
    src2 = f.read()

OLD_INV = """    period_end = inv.get('period_end')
    if not period_end:
        try:
            period_end = inv['lines']['data'][0]['period']['end']
        except (KeyError, IndexError, TypeError):
            period_end = int(datetime.today().timestamp()) + 365 * 86400"""

NEW_INV = """    period_end = inv.get('period_end')
    if not period_end:
        try:
            period_end = inv['lines']['data'][0]['period']['end']
        except (KeyError, IndexError, TypeError):
            import time as _time
            period_end = int(_time.time()) + 365 * 86400"""

if OLD_INV in src2:
    with open(SUB, 'w', encoding='utf-8') as f:
        f.write(src2.replace(OLD_INV, NEW_INV, 1))
    print("[OK]   invoice fallback also +365 days")
else:
    print("[SKIP] invoice fallback already correct or already patched")

# Compile check
print("\n[COMPILE]")
r = subprocess.run([sys.executable, '-m', 'py_compile', SUB], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"Restore: copy \"{backup}\" {SUB}")
    sys.exit(1)
print("  [OK]   compiles cleanly")

# Verify
print("\n[VERIFY]")
with open(SUB, encoding='utf-8') as f:
    final = f.read()
checks = {
    'fallback +365 in _first_period_end': 'int(_time.time()) + 365 * 86400' in final,
    'no datetime.today() fallback left':  'period_end = int(datetime.today().timestamp()) + 365 * 86400' not in final,
    'warns to stderr':                    'KAZE WARN: _first_period_end' in final,
}
ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present: ok = False

if not ok:
    print(f"\n[FATAL] Restore: copy \"{backup}\" {SUB}")
    sys.exit(1)

print("\n" + "=" * 62)
print("Code fix ready. Commit and push now.")
print("=" * 62)
print("""
  git add subscriptions.py kaze_fix_period_end.py
  git commit -m "fix: _first_period_end +365d fallback"
  git push

Wait for Render "Your service is live", THEN move to Step 2.
""")