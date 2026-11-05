"""
kaze_phase4f2_checkout.py — Phase 4f-2. Checkout page re-skin.

CSS-only injection. No JS, no HTML structure, no form action changes.

Critical invariants preserved:
  - [hidden] toggle (summary <-> embed) works because we don't add
    display rules to containers that use hidden attr
  - All 10 working IDs kept
  - min-height 420px on stripe/paypal slots preserved

Run from the folder with app.py:
    python kaze_phase4f2_checkout.py
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

orig_len = len(html)
b = f"{TPL}.bak.phase4f2_{STAMP}"
shutil.copy2(TPL, b)
print(f"Backup: {b}\n")

if 'kaze-checkout-4f2' in html:
    print("[SKIP] Already injected")
    sys.exit(0)

NEW_CSS = """<style id="kaze-checkout-4f2">
/* Phase 4f-2 — Checkout page visual. CSS-only. No layout toggles. */

/* Page wrapper */
.kaze-checkout {
    max-width: 620px !important;
    margin: 2rem auto !important;
    padding: 0 1rem;
}

/* Brand header */
.kaze-brand {
    display: flex !important;
    gap: 0.9rem !important;
    align-items: center !important;
    margin-bottom: 1.5rem !important;
    justify-content: space-between !important;
    flex-wrap: wrap;
}
.kaze-brand .kicker {
    color: var(--kz-brand, #1a8f3c) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    font-weight: 800 !important;
    margin: 0 0 0.3rem !important;
}
.kaze-brand h1 {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    margin: 0 0 0.3rem !important;
    color: var(--kz-text, var(--text)) !important;
    font-family: var(--kz-font) !important;
}
.kaze-brand p:not(.kicker) {
    color: var(--kz-text-muted, var(--text2)) !important;
    font-size: 0.88rem !important;
    margin: 0 !important;
    line-height: 1.5;
}
.kaze-brand .kaze-mark {
    width: 48px !important;
    height: 48px !important;
    border-radius: 12px !important;
    display: grid !important;
    place-items: center;
    background: linear-gradient(135deg, var(--kz-brand, #1a8f3c), #157432) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 1.3rem !important;
    flex-shrink: 0;
    box-shadow: 0 4px 12px var(--kz-brand-glow, rgba(26,143,60,0.2));
    font-family: var(--kz-font);
}

/* Cards — NO display property (critical: preserves [hidden] toggle) */
.checkout-card {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.5rem 1.6rem !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05)) !important;
    margin-bottom: 1.25rem !important;
}

/* Amount — the hero */
.checkout-amount {
    font-family: var(--kz-font) !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: var(--kz-brand, #1a8f3c) !important;
    margin: 0.5rem 0 1.25rem !important;
    line-height: 1.1;
}
.checkout-amount span {
    font-size: 0.9rem !important;
    color: var(--kz-text-light, var(--text3)) !important;
    font-weight: 500;
    font-family: var(--kz-font);
    letter-spacing: 0;
    margin-left: 0.3rem;
}

/* Sub-heading inside summary */
.checkout-card .kicker {
    color: var(--kz-text-muted, var(--text3)) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.12em !important;
}
.checkout-card h2 {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    text-transform: none !important;
    margin: 0.3rem 0 0 !important;
    color: var(--kz-text, var(--text)) !important;
}
.checkout-card h2::before { display: none !important; }

/* Form */
#kaze-pay-form .form-group {
    margin: 1rem 0 1.1rem !important;
    display: block !important;
    width: 100% !important;
}
#kaze-pay-form label {
    font-size: 0.8rem !important;
    color: var(--kz-text-muted, var(--text2)) !important;
    font-weight: 500;
    margin-bottom: 0.4rem !important;
}
#pay-method {
    width: 100% !important;
    padding: 0.7rem 0.9rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: 10px !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.92rem !important;
    font-family: inherit;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.9rem center;
    padding-right: 2.5rem !important;
    cursor: pointer;
}
#pay-method:focus {
    outline: none !important;
    border-color: var(--kz-brand, #1a8f3c) !important;
    box-shadow: 0 0 0 3px var(--kz-brand-glow, rgba(26,143,60,0.15)) !important;
}

/* Button row */
.checkout-actions {
    display: flex !important;
    gap: 0.6rem !important;
    flex-wrap: wrap !important;
    align-items: center;
    margin: 0.6rem 0 0.8rem !important;
}

/* Pay now — pill green */
.pay-now,
#pay-now-btn {
    background: var(--kz-brand, #1a8f3c) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 0.75rem 1.8rem !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    cursor: pointer;
    clip-path: none !important;
    letter-spacing: 0.01em;
    transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
}
.pay-now:hover,
#pay-now-btn:hover:not(:disabled) {
    background: #157432 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px var(--kz-brand-glow, rgba(26,143,60,0.3)) !important;
}
.pay-now:disabled,
#pay-now-btn:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed;
}

/* Back button — outlined pill */
.back-btn,
a.back-btn,
button.back-btn {
    background: transparent !important;
    color: var(--kz-text, var(--text)) !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: 999px !important;
    padding: 0.7rem 1.3rem !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    display: inline-flex;
    align-items: center;
    transition: background 0.15s, border-color 0.15s;
    clip-path: none !important;
}
.back-btn:hover,
a.back-btn:hover {
    background: var(--kz-surface-hover, var(--surface2)) !important;
    border-color: var(--kz-text-muted, var(--text2)) !important;
}

/* Error card — NO display property (preserves [hidden]) */
.pay-error {
    background: #fee2e2 !important;
    color: #991b1b !important;
    border: 1px solid #fecaca !important;
    border-radius: 8px !important;
    padding: 0.8rem 1rem !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    margin-top: 0.75rem !important;
    line-height: 1.4;
}
html.theme-dark .pay-error {
    background: rgba(239, 68, 68, 0.15) !important;
    color: #fca5a5 !important;
    border-color: rgba(239, 68, 68, 0.3) !important;
}

/* Payment slots — preserve min-height for Stripe iframe */
#stripe-slot, #paypal-slot {
    min-height: 420px;
    padding: 0.5rem 0;
}
#stripe-slot iframe, #paypal-slot iframe {
    border-radius: 10px;
}
#bank-slot h3 {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: var(--kz-text, var(--text)) !important;
    margin: 0 0 0.5rem !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
}
#bank-slot h3::before { display: none !important; }

/* Muted / helper text */
.muted {
    color: var(--kz-text-light, var(--text3)) !important;
    font-size: 0.82rem !important;
}

/* Payment terms link */
.checkout-card > p > a,
.checkout-card p a {
    color: var(--kz-brand, #1a8f3c) !important;
    font-size: 0.82rem !important;
    text-decoration: underline !important;
    text-decoration-thickness: 1px;
    text-underline-offset: 2px;
}

/* Embed section header actions */
#checkout-embed .checkout-actions {
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
    padding-bottom: 0.9rem !important;
    margin-bottom: 1.25rem !important;
}

/* No-method fallback message */
.checkout-card p:only-of-type {
    color: var(--kz-text-muted, var(--text2)) !important;
    font-size: 0.9rem !important;
}
</style>
"""

# Inject right after {% block content %} so cascade places it in body —
# but our !important selectors ensure our styles win
if '{% block content %}' in html:
    html = html.replace('{% block content %}', '{% block content %}\n' + NEW_CSS, 1)
    print("[OK] CSS injected after block content")
else:
    print("[FAIL] {% block content %} not found")
    print(f"Restore: copy \"{b}\" {TPL}")
    sys.exit(1)

# Verify Jinja
try:
    Environment().parse(html)
    print("[OK] Jinja parses cleanly")
except Exception as exc:
    print(f"[FAIL] Jinja error: {exc}")
    print(f"Restore: copy \"{b}\" {TPL}")
    sys.exit(1)

# Verify critical IDs and behaviors still present
CRITICAL = [
    ('id="kaze-pay-form"', 'form ID'),
    ('id="checkout-summary"', 'summary ID'),
    ('id="checkout-embed"', 'embed ID'),
    ('id="pay-method"', 'method select ID'),
    ('id="pay-now-btn"', 'pay button ID'),
    ('id="pay-error"', 'error display ID'),
    ('id="embed-back"', 'back button ID'),
    ('id="stripe-slot"', 'stripe slot ID'),
    ('id="paypal-slot"', 'paypal slot ID'),
    ('id="bank-slot"', 'bank slot ID'),
    ('name="kind"', 'hidden kind input'),
    ('name="amount"', 'hidden amount input'),
    ('initEmbeddedCheckout', 'Stripe JS method'),
    ('paypal.Buttons', 'PayPal JS'),
    ('FlutterwaveCheckout', 'Flutterwave JS'),
    ('kaze_checkout_embed', 'embed endpoint reference'),
    ('kaze_paypal_capture', 'paypal capture endpoint'),
]
all_ok = True
for pattern, label in CRITICAL:
    present = pattern in html
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        all_ok = False

# Critical: verify no display rule accidentally added on hidden containers
BAD_PATTERNS = [
    ('#checkout-summary {', 'display rule on summary'),
    ('#checkout-embed {', 'display rule on embed'),
    ('#bank-slot {', 'display rule on bank slot'),
]
for pat, label in BAD_PATTERNS:
    if pat in NEW_CSS and 'display' in NEW_CSS[NEW_CSS.find(pat):NEW_CSS.find(pat)+200]:
        print(f"  [FAIL] {label} — would break hidden toggle")
        all_ok = False

if not all_ok:
    print(f"\n[ABORT] File not written. Restore: copy \"{b}\" {TPL}")
    sys.exit(1)

print("  [OK]   No display rules on hidden containers")

with open(TPL, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n[OK]   Written ({orig_len:,} -> {len(html):,} chars)")

r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'], capture_output=True, text=True)
if r.returncode != 0:
    print("  [WARN] app.py has syntax error (should not be affected by template edit)")
    print(r.stderr)

print("\n" + "=" * 62)
print("Phase 4f-2 complete.")
print("  All 10 IDs preserved")
print("  Stripe / PayPal / Flutterwave / bank JS untouched")
print("  Hidden toggle behavior intact")
print(f"  File: {orig_len:,} -> {len(html):,} chars")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart:  python app.py
2. Hard refresh /payments, then trigger checkout:
   - Fill Custom payment form, click Start checkout
   - Should land on /checkout with new styling

3. Test:

   a) Checkout page visual
      [ ] K mark is green rounded square
      [ ] Header (kicker / Checkout / hint) styled
      [ ] Amount large, brand green
      [ ] Method select styled, chevron on right
      [ ] Pay now is pill green
      [ ] Back button outlined pill
      [ ] Card has subtle shadow, white bg (light theme)
      [ ] Card has dark bg (dark theme)

   b) Click "Pay now" with Stripe selected
      - Summary card should DISAPPEAR
      - Embed card should APPEAR
      - Stripe iframe should load into #stripe-slot
      - If Summary stays visible AND Embed shows → hidden toggle broken, RESTORE

   c) Click "Go back" on embed
      - Embed should DISAPPEAR
      - Summary should REAPPEAR

   d) Error state test
      - (If you can trigger one) — error should show as red card, not just text

   e) Regression
      - /payments page still works
      - Custom payment form still submits
      - Historical payments still show
      - Light/dark both look right on both pages

4. If all pass:
   git add templates/checkout.html kaze_phase4f2_checkout.py
   git commit -m "Phase 4f-2: checkout page re-skin (CSS-only)"
   git push

5. Prod test — this is the moment to test the FULL checkout flow
   with a real Stripe test card (4242 4242 4242 4242). Confirms:
   - New styling looks right
   - ui_mode embedded_page fix works end-to-end
   - Stripe embed iframe loads and completes
   - Success redirects to /plans or /payments correctly
""")