"""
kaze_stripe_uimode_fix.py — update Stripe Checkout ui_mode value.

Stripe deprecated ui_mode='embedded' in favour of 'embedded_page'.
One-line replacement in stripe_payments.py.

Run from the folder with app.py:
    python kaze_stripe_uimode_fix.py
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

if "ui_mode = 'embedded_page'" in src or '"embedded_page"' in src:
    print("[SKIP] Already using embedded_page")
    sys.exit(0)

OLD = "payload['ui_mode'] = 'embedded'"
NEW = "payload['ui_mode'] = 'embedded_page'"

if OLD not in src:
    print(f"[FAIL] Pattern not found: {OLD!r}")
    print("       Open stripe_payments.py and search for 'ui_mode' to fix by hand.")
    sys.exit(1)

b = f"{SP}.bak.uimode_{STAMP}"
shutil.copy2(SP, b)
print(f"Backup: {b}")

src = src.replace(OLD, NEW, 1)
with open(SP, 'w', encoding='utf-8') as f:
    f.write(src)
print("[OK] ui_mode set to embedded_page")

r = subprocess.run([sys.executable, '-m', 'py_compile', SP], capture_output=True, text=True)
if r.returncode != 0:
    print("[FAIL] Syntax error after patch:")
    print(r.stderr)
    print(f"\nRestore: copy \"{b}\" {SP}")
    sys.exit(1)
print("[OK] stripe_payments.py compiles cleanly")

print("\n" + "=" * 62)
print("Fix applied. Restart:  python app.py")
print("Then retest /payments → Start checkout → should reach /checkout")
print("=" * 62)