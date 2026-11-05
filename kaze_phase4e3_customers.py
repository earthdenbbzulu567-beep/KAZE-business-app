"""
kaze_phase4e3_customers.py — Phase 4e-3. Customers page visual overhaul.

1. Remove decorative "Customers Overview" card
2. Add .kz-customers-form class to Add Customer form
3. Inject page-scoped CSS for cards, forms, stat chips, tables, pagination

Not touched: Orders/Total Spent columns (spend_by_customer lookups),
chart script, Export/Import modal, pagination logic.

Run from the folder with app.py:
    python kaze_phase4e3_customers.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
TPL = 'templates/customers.html'

if not os.path.isfile(TPL):
    print(f"ERROR: {TPL} not found.")
    sys.exit(1)

with open(TPL, encoding='utf-8') as f:
    html = f.read()

orig_len = len(html)
b = f"{TPL}.bak.phase4e3_{STAMP}"
shutil.copy2(TPL, b)
print(f"Backup: {b}\n")

FAILED = []

# ── [1/5] Remove decorative Customers Overview card ─────────────
print("[1/5] Removing decorative 'Customers Overview' card...")

OVERVIEW_RE = re.compile(
    r'<div class="card detail-overlay"[^>]*>.*?(?=<div class="page-header">)',
    re.DOTALL,
)
new_html, count = OVERVIEW_RE.subn('', html, count=1)
if count == 1:
    html = new_html
    print("  [OK]   decorative card removed")
elif 'Customers Overview' not in html:
    print("  [SKIP] already gone")
else:
    print("  [FAIL] overview pattern not matched")
    FAILED.append("overview removal")

# ── [2/5] Add .kz-customers-form class to Add Customer form ─────
print("\n[2/5] Adding .kz-customers-form class...")

OLD_FORM = '<form method="POST" action="{{ url_for(\'add_customer\') }}">'
NEW_FORM = '<form method="POST" action="{{ url_for(\'add_customer\') }}" class="kz-customers-form">'

if 'class="kz-customers-form"' in html:
    print("  [SKIP] class already present")
elif OLD_FORM in html:
    html = html.replace(OLD_FORM, NEW_FORM, 1)
    print("  [OK]   class added")
else:
    print("  [FAIL] Add Customer form pattern not found")
    FAILED.append("form class")

# ── [3/5] Inject page-scoped CSS ─────────────────────────────────
print("\n[3/5] Injecting page-scoped CSS...")

NEW_CSS = """{% block content %}
<style id="kaze-customers-4e3">
/* Phase 4e-3 — Customers page visual (scoped to /customers only) */

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

/* Chart container */
.page-content .chart-container {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.5rem !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
    margin-bottom: 1.5rem !important;
}

/* Add Customer form → card, grid layout */
form.kz-customers-form {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    margin: 1.5rem 0 !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)) !important;
    gap: 0.65rem !important;
    align-items: end;
}
form.kz-customers-form .form-group {
    margin: 0 !important;
    display: block !important;
    width: 100% !important;
}
form.kz-customers-form input,
form.kz-customers-form select,
form.kz-customers-form textarea {
    width: 100% !important;
    padding: 0.6rem 0.85rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: var(--kz-radius-sm, 8px) !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.9rem !important;
}
form.kz-customers-form input:focus,
form.kz-customers-form select:focus,
form.kz-customers-form textarea:focus {
    border-color: var(--kz-brand, var(--red-bright)) !important;
    box-shadow: 0 0 0 3px var(--kz-brand-glow, var(--red-glow)) !important;
    outline: none !important;
}
form.kz-customers-form .form-group[style*="display:block"] {
    grid-column: 1 / -1;
}
form.kz-customers-form button {
    grid-column: 1 / -1;
    justify-self: start;
}

/* Submit buttons — page-scoped pill style */
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

/* Multi-add details → card */
details.multi-wrap {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 0.85rem 1.2rem !important;
    margin: 1.5rem 0 !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
}
details.multi-wrap summary {
    color: var(--kz-text, var(--text)) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* Bulk action bar */
form[action*="customers_bulk"] > div:first-of-type select {
    padding: 0.5rem 0.8rem !important;
    border-radius: 8px !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.85rem !important;
}

/* Tables — card styling */
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

/* Pagination pills */
.page-content .pagination a {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: 999px !important;
    color: var(--kz-text-muted, var(--text2)) !important;
    padding: 0.4rem 0.9rem !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    min-width: 34px;
    text-align: center;
    transition: all 0.15s ease;
}
.page-content .pagination a:hover {
    border-color: var(--kz-brand, var(--red-bright)) !important;
    color: var(--kz-brand, var(--red-bright)) !important;
}
.page-content .pagination a[style*="background:var(--red-bright)"] {
    background: var(--kz-brand, var(--red-bright)) !important;
    color: #fff !important;
    border-color: var(--kz-brand, var(--red-bright)) !important;
}
</style>
"""

if 'kaze-customers-4e3' in html:
    print("  [SKIP] CSS already injected")
else:
    if '{% block content %}' in html:
        html = html.replace('{% block content %}', NEW_CSS, 1)
        print("  [OK]   CSS injected at content block start")
    else:
        print("  [FAIL] {% block content %} not found")
        FAILED.append("CSS injection")

# ── [4/5] Write ──────────────────────────────────────────────────
print("\n[4/5] Writing customers.html...")
with open(TPL, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"  [OK]   Written ({orig_len:,} -> {len(html):,} chars)")

# ── [5/5] Verify ─────────────────────────────────────────────────
print("\n[5/5] Verifying...")

try:
    Environment().parse(html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    print(f"\nRestore: copy \"{b}\" {TPL}")
    sys.exit(1)

checks = {
    'CSS block injected':       'kaze-customers-4e3' in html,
    'form has class':           'class="kz-customers-form"' in html,
    'overview card gone':       'Customers Overview' not in html,
    'spend lookups intact':     'spend_by_customer' in html,
    'kpi chip style':           '.page-content .stat-chip' in html,
    'pagination pills':         '.page-content .pagination a' in html,
    'bulk form intact':         'customers_bulk' in html,
    'chart script intact':      'customerSpendChart' in html,
    'modal intact':             'customerActionsModal' in html,
    'orders column intact':     'order_count' in html,
    'total spent intact':       'total_spent' in html,
}
all_ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        all_ok = False

print("\n" + "=" * 62)
if FAILED or not all_ok:
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore: copy \"{b}\" {TPL}")
    sys.exit(1)

print("Phase 4e-3 complete.")
print("  Decorative card: removed")
print("  Add Customer form: card layout, grid fields, brand button")
print("  Stat chips: KPI card style with green accent bar")
print("  Table: card styling")
print("  Pagination: pill buttons")
print("  Spend chart: INTACT")
print("  Bulk + modal: INTACT")
print("  Orders / Total Spent columns: INTACT")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart:  python app.py
2. Hard refresh /customers (Ctrl+F5)

3. Test — CRITICAL regression first:

   a) Add a test customer via Add Customer form
      - Name: CUSTTEST_4E3
      - Email: test4e3@example.com (or leave blank)
      - Click Save Customer
      - Verify it appears in the table
      - If it fails, restore immediately:
        copy "templates/customers.html.bak.phase4e3_""" + STAMP + """" templates/customers.html

   b) Orders and Total Spent columns still work
      - Find any customer with existing sales
      - Their row should still show Orders > 0 and Total Spent > 0
      - If these show 0/blank when they should show data → restore

4. Then visual:

   [ ] No Customers Overview card
   [ ] Add Customer form is white card with grid
   [ ] Multi-add is white card
   [ ] Stat chips are KPI cards
   [ ] Table clean headers
   [ ] Pagination pills
   [ ] Chart still renders (if any customers with spend)
   [ ] Export/Import modal opens (click button in header)
   [ ] Light theme good
   [ ] Dark theme good

5. If all pass:
   git add templates/customers.html kaze_phase4e3_customers.py
   git commit -m "Phase 4e-3: customers page visual overhaul"
   git push

AFTER 4e-3: Phase 4e complete. Then 4f — Payments + Checkout rewrite.
""")