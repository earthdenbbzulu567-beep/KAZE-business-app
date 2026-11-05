"""
kaze_phase4f1_payments.py — Phase 4f-1. Payments + fees visual overhaul.

Files touched:
  templates/payments.html
  templates/payments_fees.html

Preserves:
  - All form actions (pay_custom, payments_fees_sync, payments_fees_reconcile_one)
  - Per-row Reconcile buttons (btn-secondary, stay as-is)
  - Payment methods list logic (pay_methods iteration)
  - Fee column data logic (stripe_fee_fetched_at checks)
  - No route changes, no backend changes

Run from the folder with app.py:
    python kaze_phase4f1_payments.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

FILES = [
    ('templates/payments.html', 'payments'),
    ('templates/payments_fees.html', 'fees'),
]

for path, _ in FILES:
    if not os.path.isfile(path):
        print(f"ERROR: {path} not found.")
        sys.exit(1)

FAILED = []

CSS = """{% block content %}
<style id="kaze-payments-4f1">
/* Phase 4f-1 — Payments + Fees visual (scoped to those pages only) */

.page-content .detail-overlay { display: none !important; }

.page-content h2 {
    font-size: 0.98rem !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
    font-weight: 600 !important;
    color: var(--kz-text, var(--text)) !important;
    margin: 1.75rem 0 0.85rem !important;
}
.page-content h2::before { display: none !important; }

.page-content .page-header {
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
    padding-bottom: 1rem !important;
    margin-bottom: 1.5rem !important;
}
.page-content .page-header h1 {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: var(--kz-text, var(--text)) !important;
}

/* Stat chips → KPI cards */
.page-content .stat-grid { gap: 0.85rem; margin: 1rem 0 1.5rem; }
.page-content .stat-chip {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1rem 1.2rem !important;
    position: relative;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
    animation: none !important;
}
.page-content .stat-chip::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--kz-brand, #1a8f3c), var(--kz-accent, #10b981));
    opacity: 0.6;
    border-radius: var(--kz-radius, 12px) var(--kz-radius, 12px) 0 0;
}
.page-content .stat-chip span {
    font-size: 0.72rem !important;
    letter-spacing: 0.08em !important;
    color: var(--kz-text-muted, var(--text3)) !important;
}
.page-content .stat-chip strong {
    font-size: 1.3rem !important;
    color: var(--kz-text, var(--text)) !important;
    font-family: var(--kz-font);
}

/* Widget → card */
.page-content .widget {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    margin: 1.5rem 0 !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
}
.page-content .widget h2 {
    margin-top: 0 !important;
    margin-bottom: 0.75rem !important;
    font-size: 0.95rem !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
    font-weight: 600 !important;
    color: var(--kz-text, var(--text)) !important;
}
.page-content .widget h2::before { display: none !important; }
.page-content .widget > p {
    color: var(--kz-text-muted, var(--text2)) !important;
    font-size: 0.88rem !important;
    margin-bottom: 0.85rem;
}

/* Payment methods list → grid of method cards */
ul.pay-ready {
    list-style: none;
    padding: 0;
    margin: 0.85rem 0 1rem;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 0.65rem;
}
ul.pay-ready li {
    background: var(--kz-bg, var(--bg3)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: 10px !important;
    padding: 0.75rem 0.95rem !important;
    font-size: 0.85rem !important;
    color: var(--kz-text, var(--text)) !important;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    line-height: 1.4;
    font-weight: 500;
}
ul.pay-ready li .status-pill {
    align-self: flex-start;
    margin-bottom: 0.15rem;
    font-size: 0.72rem !important;
}

/* Custom payment form → card + grid */
form[action*="pay_custom"] {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)) !important;
    gap: 0.65rem !important;
    align-items: end;
}
form[action*="pay_custom"] .form-group {
    margin: 0 !important;
    display: block !important;
    width: 100% !important;
}
form[action*="pay_custom"] input,
form[action*="pay_custom"] select {
    width: 100% !important;
    padding: 0.6rem 0.85rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: var(--kz-radius-sm, 8px) !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.9rem !important;
}
form[action*="pay_custom"] input:focus,
form[action*="pay_custom"] select:focus {
    border-color: var(--kz-brand, var(--red-bright)) !important;
    box-shadow: 0 0 0 3px var(--kz-brand-glow, var(--red-glow)) !important;
    outline: none !important;
}
form[action*="pay_custom"] button {
    grid-column: 1 / -1;
    justify-self: start;
}

/* Sync + submit buttons (page-scoped pill style) */
.page-content form button[type="submit"]:not(.btn-secondary):not(.modal-close):not(.multi-row-del):not(.popup-trigger-btn) {
    background: var(--kz-brand, var(--red-bright)) !important;
    color: #fff !important;
    border-radius: 999px !important;
    padding: 0.65rem 1.4rem !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    clip-path: none !important;
    border: none !important;
    cursor: pointer;
}
.page-content form button[type="submit"]:not(.btn-secondary):not(.modal-close):not(.multi-row-del):not(.popup-trigger-btn):hover {
    background: var(--kz-brand-hover, var(--red-bright)) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--kz-shadow, 0 1px 3px rgba(0,0,0,0.1)) !important;
}

/* Tables — card style */
.page-content .table-wrapper {
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    overflow: hidden;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
}
.page-content table {
    background: var(--kz-surface, var(--surface)) !important;
}
.page-content thead th {
    background: var(--kz-bg, var(--bg3)) !important;
    color: var(--kz-text-muted, var(--text3)) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-weight: 600 !important;
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
}
.page-content tbody td {
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
    color: var(--kz-text, var(--text)) !important;
}
.page-content tbody tr:hover {
    background: var(--kz-surface-hover, var(--surface2)) !important;
}
</style>
"""

for path, label in FILES:
    print(f"\n[{'[1/4]' if label == 'payments' else '[2/4]'}] Overhauling {path}...")
    with open(path, encoding='utf-8') as f:
        html = f.read()
    orig_len = len(html)
    b = f"{path}.bak.phase4f1_{STAMP}"
    shutil.copy2(path, b)
    print(f"  Backup: {b}")

    if f'kaze-payments-4f1' in html:
        print(f"  [SKIP] CSS already injected")
        continue

    if '{% block content %}' in html:
        html = html.replace('{% block content %}', CSS, 1)
        print(f"  [OK]   CSS injected")
    else:
        print(f"  [FAIL] {{% block content %}} not found in {path}")
        FAILED.append(f"CSS in {path}")
        continue

    try:
        Environment().parse(html)
        print(f"  [OK]   Jinja parses cleanly")
    except Exception as exc:
        print(f"  [FAIL] Jinja error: {exc}")
        FAILED.append(f"Jinja {path}")
        continue

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  [OK]   Written ({orig_len:,} -> {len(html):,} chars)")

# ── Verification ──────────────────────────────────────────────────
print("\n[3/4] Verifying content integrity...")

def check(path, patterns, label):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    ok = True
    for pat, desc in patterns:
        present = pat in content
        print(f"  {'[OK]  ' if present else '[FAIL]'} {label}: {desc}")
        if not present:
            ok = False
    return ok

payments_ok = check('templates/payments.html', [
    ('pay_custom', 'custom payment form action'),
    ('pay_methods', 'payment methods loop'),
    ('pay-ready', 'methods list class'),
    ('checkout_id', 'payment log ref column'),
    ('stripe_fee_fetched_at', 'fee display logic'),
], 'payments')

fees_ok = check('templates/payments_fees.html', [
    ('payments_fees_sync', 'sync action'),
    ('payments_fees_reconcile_one', 'per-row reconcile action'),
    ('btn-secondary', 'reconcile buttons preserved'),
    ('stripe_fee_fetched_at', 'fee display logic'),
    ('total_gross', 'summary gross total'),
], 'fees')

# ── Summary ───────────────────────────────────────────────────────
print("\n[4/4] Summary")

print("\n" + "=" * 62)
if FAILED or not (payments_ok and fees_ok):
    print("FAILED — restore before proceeding:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore payments: copy \"templates/payments.html.bak.phase4f1_{STAMP}\" templates/payments.html")
    print(f"Restore fees:     copy \"templates/payments_fees.html.bak.phase4f1_{STAMP}\" templates/payments_fees.html")
    sys.exit(1)

print("Phase 4f-1 complete.")
print("  payments.html:      KPI chips, method cards, form-as-card, table-as-card")
print("  payments_fees.html: KPI chips, sync button pill, table-as-card")
print("  All form actions, per-row reconcile buttons, fee logic: INTACT")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart:  python app.py
2. Hard refresh /payments (Ctrl+F5)
3. Then hard refresh /payments/fees (Ctrl+F5)

4. Test /payments — CRITICAL:

   a) Layout
      [ ] No decorative card at top
      [ ] 2 KPI chips at top (Stripe status, Records count)
      [ ] "Accepted methods" as grid of cards (one per payment method)
      [ ] "Take a custom payment" form is a card, fields in grid
      [ ] Payment log table has card styling
      [ ] Fee + Net columns still present in payment log

   b) Custom payment flow (do NOT need to complete checkout — just verify it starts)
      - Fill: Title "TEST 4F1", Amount 1, Method = Card — Visa/Mastercard
      - Click "Start checkout"
      - Should redirect to /checkout — that page is 4f-2 (still old styling, will be fixed next)
      - Press back to return to /payments
      - If Start checkout breaks — restore immediately

   c) Regression on the table
      [ ] All 18 historical payments still shown
      [ ] Status pills show "Paid" / "pending"
      [ ] Ref column shows checkout_id
      [ ] Fee/Net columns show "—" for unsynced (or amounts for synced)

5. Test /payments/fees:

   [ ] No decorative card at top
   [ ] 5 KPI chips (Gross / Fees / Net / Fee % / Pending)
   [ ] "Sync fees from Stripe" button is pill green
   [ ] Table with Fee / Net / Fee status columns
   [ ] Per-row "Reconcile" buttons still btn-secondary styled (small, not pill green)
   [ ] Status pills show "Pending" for unsynced payments

6. Regression — must still work:
   - Click "Sync fees from Stripe" → flash message
   - If any Stripe-paid row exists → per-row Reconcile works
     (likely none exist — your payments are all Flutterwave)

7. If all pass:
   git add templates/payments.html templates/payments_fees.html kaze_phase4f1_payments.py
   git commit -m "Phase 4f-1: payments + fees visual overhaul"
   git push

AFTER 4f-1: 4f-2 (checkout page rewrite — embedded Stripe, PayPal, Flutterwave, bank).
""")