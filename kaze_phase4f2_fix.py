"""
kaze_phase4f2_fix.py — fix the badge in the 4f-2 checkout re-skin.

What this does:
  1. Removes my gradient .kaze-mark CSS rule (the one that changed the badge)
  2. Adds new CSS that styles img.kaze-mark to match the sidebar brand mark
     (dark bg, subtle green ring, rounded)
  3. Replaces <span class="kaze-mark">K</span> with the actual logo image
     from static/logo_icon.png

Preserves every other 4f-2 style: cards, amount, buttons, error, form select.

Run from the folder with app.py:
    python kaze_phase4f2_fix.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
TPL = 'templates/checkout.html'

if not os.path.isfile(TPL):
    print(f"ERROR: {TPL} not found.")
    sys.exit(1)

with open(TPL, encoding='utf-8') as f:
    html = f.read()

b = f"{TPL}.bak.phase4f2fix_{STAMP}"
shutil.copy2(TPL, b)
print(f"Backup: {b}\n")

if 'kaze-checkout-4f2' not in html:
    print("[FAIL] 4f-2 CSS not present. Run kaze_phase4f2_checkout.py first.")
    sys.exit(1)

# ── [1/4] Remove my bad .kaze-mark CSS rule ────────────────────────
print("[1/4] Removing bad .kaze-mark CSS rule...")

OLD_RULE_RE = re.compile(
    r'\.kaze-brand \.kaze-mark\s*\{[^}]*\}',
    re.DOTALL,
)
new_html, count = OLD_RULE_RE.subn('', html, count=1)
if count == 1:
    html = new_html
    print("  [OK]   bad .kaze-mark rule removed")
else:
    print("  [WARN] .kaze-mark rule not found (may already be removed)")

# ── [2/4] Add new img.kaze-mark CSS ────────────────────────────────
print("\n[2/4] Adding new img.kaze-mark CSS...")

NEW_RULE = """
/* Logo image — matches sidebar .brand-mark */
.kaze-brand .kaze-mark,
img.kaze-mark {
    width: 52px !important;
    height: 52px !important;
    min-width: 52px !important;
    border-radius: 14px !important;
    display: block !important;
    flex-shrink: 0 !important;
    object-fit: cover !important;
    background: #070707 !important;
    box-shadow: 0 0 0 1px rgba(46, 125, 50, 0.55),
                0 6px 14px rgba(0, 0, 0, 0.3) !important;
}
"""

# Insert right after the style tag opening (before the first CSS rule)
if 'kaze-checkout-4f2' in html:
    # Find the <style id="kaze-checkout-4f2"> opening and insert after it
    marker = '<style id="kaze-checkout-4f2">'
    if marker in html:
        html = html.replace(marker, marker + NEW_RULE, 1)
        print("  [OK]   img.kaze-mark CSS added")
    else:
        print("  [FAIL] style tag not found")
        sys.exit(1)
else:
    print("  [FAIL] state unexpected")
    sys.exit(1)

# ── [3/4] Replace span badge with img logo ────────────────────────
print("\n[3/4] Replacing span badge with logo image...")

OLD_SPAN = '<span class="kaze-mark">K</span>'
NEW_IMG = '<img src="{{ url_for(\'static\', filename=\'logo_icon.png\') }}" alt="KAZE" class="kaze-mark">'

if NEW_IMG in html:
    print("  [SKIP] img already present")
elif OLD_SPAN in html:
    html = html.replace(OLD_SPAN, NEW_IMG, 1)
    print("  [OK]   span replaced with img")
else:
    print("  [FAIL] span.kaze-mark not found")
    print("       Open templates/checkout.html and search for 'kaze-mark' to fix manually.")
    sys.exit(1)

# ── [4/4] Verify + write ───────────────────────────────────────────
print("\n[4/4] Verifying...")

try:
    Environment().parse(html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    print(f"Restore: copy \"{b}\" {TPL}")
    sys.exit(1)

checks = {
    'img.kaze-mark CSS present':   'img.kaze-mark' in html,
    'logo_icon.png referenced':    "logo_icon.png" in html,
    'no gradient on badge':        'linear-gradient(135deg, var(--kz-brand' not in html or 'kaze-mark' not in html.split('linear-gradient(135deg, var(--kz-brand')[0][-200:],
    'span K badge gone':           '<span class="kaze-mark">K</span>' not in html,
    'all 10 IDs preserved':        all(p in html for p in [
        'id="kaze-pay-form"', 'id="checkout-summary"', 'id="checkout-embed"',
        'id="pay-method"', 'id="pay-now-btn"', 'id="pay-error"',
        'id="embed-back"', 'id="stripe-slot"', 'id="paypal-slot"', 'id="bank-slot"',
    ]),
}
all_ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        all_ok = False

if not all_ok:
    print(f"\n[ABORT] File not written. Restore: copy \"{b}\" {TPL}")
    sys.exit(1)

with open(TPL, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n[OK]   Written ({len(html):,} chars)")

print()
print("=" * 62)
print("Fix applied.")
print("  Badge is now the real KAZE logo image, sized like sidebar.")
print("  All 4f-2 card / amount / button / select styles unchanged.")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart:  python app.py
2. Hard refresh /payments, trigger checkout
3. On /checkout:

   a) Logo check
      [ ] Logo is the actual KAZE "K" image (dark bg with green K)
      [ ] Size 52x52, rounded 14px
      [ ] Same visual as sidebar brand mark (scaled up)
      [ ] No gradient fill (should NOT look like a floating green pill)

   b) Everything else still correct
      [ ] Amount large, green
      [ ] Method select styled
      [ ] Pay now pill green
      [ ] Back button outlined
      [ ] Card styling clean

4. If all good:
   git add templates/checkout.html kaze_phase4f2_fix.py kaze_phase4f2_checkout.py
   git commit -m "Phase 4f-2: checkout page re-skin + logo fix"
   git push

5. Prod test — full checkout flow with 4242 4242 4242 4242

If anything looks wrong:
   copy "templates/checkout.html.bak.phase4f2fix_""" + STAMP + """" templates/checkout.html
""")