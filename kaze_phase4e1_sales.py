"""
kaze_phase4e1_sales.py — Phase 4e-1.

1. Remove decorative "Sales Overview" card from sales.html
2. Add .kz-sales-form class to the full Add Sale form
3. Add page-scoped CSS: stat chips as KPI cards, form as card, auto-sale
   as card, table styling, pagination pills, cleaner h2 headings

CSS is scoped inside the sales content block, so it only affects /sales.
Stock, Customers, Analytics, etc. are untouched.

Run from the folder with app.py:
    python kaze_phase4e1_sales.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
TPL = 'templates/sales.html'

if not os.path.isfile(TPL):
    print(f"ERROR: {TPL} not found.")
    sys.exit(1)

with open(TPL, encoding='utf-8') as f:
    html = f.read()

orig_len = len(html)
b = f"{TPL}.bak.phase4e1_{STAMP}"
shutil.copy2(TPL, b)
print(f"Backup: {b}\n")

FAILED = []

# ── [1/5] Remove decorative Sales Overview card ──────────────────
print("[1/5] Removing decorative 'Sales Overview' card...")

OVERVIEW_RE = re.compile(
    r'<div class="card detail-overlay"[^>]*>.*?(?=<div class="page-header">)',
    re.DOTALL,
)
new_html, count = OVERVIEW_RE.subn('', html, count=1)
if count == 1:
    html = new_html
    print("  [OK]   decorative card removed")
elif 'Sales Overview' not in html:
    print("  [SKIP] already gone")
else:
    print("  [FAIL] overview pattern not matched")
    FAILED.append("overview removal")

# ── [2/5] Add .kz-sales-form class to full Add Sale form ─────────
print("\n[2/5] Adding .kz-sales-form class to Add Sale form...")

OLD_FORM = '<form method="POST" action="{{ url_for(\'add_sale\') }}">'
NEW_FORM = '<form method="POST" action="{{ url_for(\'add_sale\') }}" class="kz-sales-form">'

if 'class="kz-sales-form"' in html:
    print("  [SKIP] class already present")
elif OLD_FORM in html:
    html = html.replace(OLD_FORM, NEW_FORM, 1)
    print("  [OK]   class added")
else:
    print("  [FAIL] Add Sale form pattern not found")
    FAILED.append("form class")

# ── [3/5] Inject page-scoped CSS ─────────────────────────────────
print("\n[3/5] Injecting page-scoped CSS...")

NEW_CSS = """{% block content %}
<style id="kaze-sales-4e1">
/* Phase 4e-1 — Sales page visual (scoped to /sales only) */

/* Hide any remaining decorative card */
.page-content .detail-overlay { display: none !important; }

/* Cleaner headings */
.page-content h2 {
    font-size: 0.98rem !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
    font-weight: 600 !important;
    color: var(--kz-text, var(--text)) !important;
    margin: 1.75rem 0 0.85rem !important;
}
.page-content h2::before { display: none !important; }

/* Page header */
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

/* Stat chips → KPI cards (page-scoped) */
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

/* Auto-sale widget → card */
#autoSaleBox {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    margin: 1.5rem 0 !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
}
#autoSaleBox h2 {
    margin: 0 0 0.4rem 0 !important;
    font-size: 0.98rem !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
    color: var(--kz-text, var(--text)) !important;
    font-weight: 600 !important;
}
#autoSaleBox h2::before { display: none !important; }
#autoSaleBox > p {
    color: var(--kz-text-muted, var(--text2)) !important;
    font-size: 0.88rem !important;
    margin: 0 0 1rem !important;
}
#autoSaleBox form {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.6rem;
    align-items: end;
}
#autoSaleBox .form-group { margin: 0 !important; display: block !important; width: 100% !important; }
#autoSaleBox label { font-size: 0.78rem !important; color: var(--kz-text-muted, var(--text3)) !important; }
#autoSaleBox input, #autoSaleBox select {
    width: 100% !important;
    padding: 0.55rem 0.8rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: var(--kz-radius-sm, 8px) !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.88rem !important;
}

/* Full Add Sale form → card with grid layout */
form.kz-sales-form {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    margin: 1.5rem 0 !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)) !important;
    gap: 0.65rem !important;
    align-items: end;
}
form.kz-sales-form input,
form.kz-sales-form select {
    width: 100% !important;
    padding: 0.6rem 0.85rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: var(--kz-radius-sm, 8px) !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.9rem !important;
}
form.kz-sales-form input:focus,
form.kz-sales-form select:focus {
    border-color: var(--kz-brand, var(--red-bright)) !important;
    box-shadow: 0 0 0 3px var(--kz-brand-glow, var(--red-glow)) !important;
    outline: none !important;
}

/* Submit buttons — page-scoped */
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
form.kz-sales-form button,
#autoSaleBox form button {
    grid-column: 1 / -1;
    justify-self: start;
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
form[action*="sales_bulk"] > div:first-of-type select {
    padding: 0.5rem 0.8rem !important;
    border-radius: 8px !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.85rem !important;
}

/* Tables */
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

if 'kaze-sales-4e1' in html:
    print("  [SKIP] CSS already injected")
else:
    if '{% block content %}' in html:
        html = html.replace('{% block content %}', NEW_CSS, 1)
        print("  [OK]   CSS injected at content block start")
    else:
        print("  [FAIL] {% block content %} not found")
        FAILED.append("CSS injection")

# ── [4/5] Write ──────────────────────────────────────────────────
print("\n[4/5] Writing sales.html...")
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
    'CSS block injected':      'kaze-sales-4e1' in html,
    'form has class':          'class="kz-sales-form"' in html,
    'overview card gone':      'Sales Overview' not in html,
    'auto-sale card style':    '#autoSaleBox {' in html,
    'kpi chip style':          '.page-content .stat-chip' in html,
    'pagination pills':        '.page-content .pagination a' in html,
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

print("Phase 4e-1 complete.")
print("  Decorative card: removed")
print("  Add Sale form:   card layout, grid fields, brand button")
print("  Auto-sale:       card layout, compact grid")
print("  Stat chips:      KPI card style with green accent bar")
print("  Table:           card styling, cleaner headers")
print("  Pagination:      pill buttons")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart:  python app.py
2. Hard refresh /sales (Ctrl+F5)

3. Test:

   a) Top of page
      - No "Sales Overview" gradient card
      - Page starts with "Sales" heading + Export / Aged sales buttons
      - Divider below heading

   b) Auto sale widget
      - White card with product/qty/customer fields in a row
      - Green "Sell now" button (pill)
      - Quick "+1 Product" buttons below

   c) Chart
      - White card container, mockup styling (from 4d-1 chart theme)

   d) Add Sale form (full form)
      - White card with fields in grid layout (2-3 per row)
      - Green "Record Sale" pill button
      - All fields still function (product select, qty, customer, etc.)

   e) Multi-add
      - Collapsible white card
      - Table rows styled

   f) Stat chips (Sales on page / Units / Revenue / Profit)
      - KPI card style with green top accent

   g) Sales History table
      - Cleaner headers
      - Checkboxes still work
      - Bulk action dropdown + Apply button still work
      - Pagination at bottom is pill-styled

   h) Light theme
      - All cards white, all text readable
   i) Dark theme
      - Cards dark, text light, brand green accents

4. Regression — must all still work:
   - Create a sale via Add Sale form
   - Create a sale via Auto sale
   - Export CSV button
   - Aged sales link
   - Pagination navigation
   - Bulk select → delete (confirm still asks)
   - Receipt / Pay now / Invoice / Repeat / Delete per row

5. If all pass:
   git add templates/sales.html kaze_phase4e1_sales.py
   git commit -m "Phase 4e-1: sales page visual overhaul"
   git push

AFTER 4e-1 CONFIRMS: 4e-2 (Stock page). Same pattern.
""")