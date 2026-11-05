"""
kaze_phase4e2_stock.py — Phase 4e-2. Stock page visual overhaul.

1. Remove decorative "Stock Overview" gradient card
2. Add .kz-stock-form class to Add Stock form
3. Inject page-scoped CSS for cards, forms, stat chips, tables, pagination
4. PRESERVE low-stock red highlighting (critical — do not override)

Not touched: bulk actions, chart script, Export/Import modal, pagination
logic, low-stock sound trigger.

Run from the folder with app.py:
    python kaze_phase4e2_stock.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
TPL = 'templates/stock.html'

if not os.path.isfile(TPL):
    print(f"ERROR: {TPL} not found.")
    sys.exit(1)

with open(TPL, encoding='utf-8') as f:
    html = f.read()

orig_len = len(html)
b = f"{TPL}.bak.phase4e2_{STAMP}"
shutil.copy2(TPL, b)
print(f"Backup: {b}\n")

FAILED = []

# ── [1/5] Remove decorative Stock Overview card ──────────────────
print("[1/5] Removing decorative 'Stock Overview' card...")

OVERVIEW_RE = re.compile(
    r'<div class="card detail-overlay"[^>]*>.*?(?=<div class="page-header">)',
    re.DOTALL,
)
new_html, count = OVERVIEW_RE.subn('', html, count=1)
if count == 1:
    html = new_html
    print("  [OK]   decorative card removed")
elif 'Stock Overview' not in html:
    print("  [SKIP] already gone")
else:
    print("  [FAIL] overview pattern not matched")
    FAILED.append("overview removal")

# ── [2/5] Add .kz-stock-form class to Add Stock form ────────────
print("\n[2/5] Adding .kz-stock-form class...")

OLD_FORM = '<form method="POST" action="{{ url_for(\'add_stock\') }}">'
NEW_FORM = '<form method="POST" action="{{ url_for(\'add_stock\') }}" class="kz-stock-form">'

if 'class="kz-stock-form"' in html:
    print("  [SKIP] class already present")
elif OLD_FORM in html:
    html = html.replace(OLD_FORM, NEW_FORM, 1)
    print("  [OK]   class added")
else:
    print("  [FAIL] Add Stock form pattern not found")
    FAILED.append("form class")

# ── [3/5] Inject page-scoped CSS ─────────────────────────────────
print("\n[3/5] Injecting page-scoped CSS...")

NEW_CSS = """{% block content %}
<style id="kaze-stock-4e2">
/* Phase 4e-2 — Stock page visual (scoped to /stock only) */

/* Hide decorative card if any residue */
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

/* Add Stock form → card, grid layout */
form.kz-stock-form {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    margin: 1.5rem 0 !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important;
    gap: 0.65rem !important;
    align-items: end;
}
form.kz-stock-form input,
form.kz-stock-form select {
    width: 100% !important;
    padding: 0.6rem 0.85rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: var(--kz-radius-sm, 8px) !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.9rem !important;
}
form.kz-stock-form input:focus,
form.kz-stock-form select:focus {
    border-color: var(--kz-brand, var(--red-bright)) !important;
    box-shadow: 0 0 0 3px var(--kz-brand-glow, var(--red-glow)) !important;
    outline: none !important;
}
form.kz-stock-form button {
    grid-column: 1 / -1;
    justify-self: start;
}

/* Submit buttons — page-scoped, pill style */
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
form[action*="stock_bulk"] > div:first-of-type select {
    padding: 0.5rem 0.8rem !important;
    border-radius: 8px !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.85rem !important;
}
form[action*="stock_bulk"] > div:first-of-type input[type="number"] {
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
/* CRITICAL: preserve low-stock highlighting — do NOT override .low-stock-row */
.page-content tbody tr:not(.low-stock-row):hover {
    background: var(--kz-surface-hover, var(--surface2)) !important;
}
/* Ensure low-stock rows keep their red background */
.page-content tbody tr.low-stock-row {
    background: var(--danger-dim) !important;
}
.page-content tbody tr.low-stock-row:hover {
    background: var(--danger-dim) !important;
    filter: brightness(1.1);
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

if 'kaze-stock-4e2' in html:
    print("  [SKIP] CSS already injected")
else:
    if '{% block content %}' in html:
        html = html.replace('{% block content %}', NEW_CSS, 1)
        print("  [OK]   CSS injected at content block start")
    else:
        print("  [FAIL] {% block content %} not found")
        FAILED.append("CSS injection")

# ── [4/5] Write ──────────────────────────────────────────────────
print("\n[4/5] Writing stock.html...")
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
    'CSS block injected':      'kaze-stock-4e2' in html,
    'form has class':          'class="kz-stock-form"' in html,
    'overview card gone':      'Stock Overview' not in html,
    'low-stock preserved':     'tr.low-stock-row' in html and 'var(--danger-dim)' in html,
    'kpi chip style':          '.page-content .stat-chip' in html,
    'pagination pills':        '.page-content .pagination a' in html,
    'bulk form intact':        'stock_bulk' in html,
    'chart script intact':     'stockValueChart' in html,
    'modal intact':            'stockActionsModal' in html,
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

print("Phase 4e-2 complete.")
print("  Decorative card: removed")
print("  Add Stock form:  card layout, grid fields, brand button")
print("  Stat chips:      KPI card style with green accent bar")
print("  Table:           card styling")
print("  Pagination:      pill buttons")
print("  Low-stock:       red highlighting PRESERVED")
print("  Bulk + modal + chart: INTACT")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart:  python app.py
2. Hard refresh /stock (Ctrl+F5)

3. Test — CRITICAL regression first:

   a) Add a test product via Add Stock form
      - Pick a unique name like "TESTPRODUCT_4E2"
      - Qty 1, cost 10, sell 20
      - Click Add Stock
      - Verify it appears in the table
      - If it fails, restore immediately:
        copy "templates/stock.html.bak.phase4e2_""" + STAMP + """" templates/stock.html

   b) Find a low-stock row (any product with low qty)
      - It should STILL have red background
      - This is the single most likely thing to break — check it

   c) Bulk actions
      - Select a checkbox → action dropdown → Apply (leave empty for now, just confirm button shows)
      - Delete the TESTPRODUCT via single Delete link → confirm removes it

4. Then visual:

   [ ] No Stock Overview card
   [ ] Add Stock form is white card with grid
   [ ] Multi-add is white card
   [ ] Stat chips are KPI cards
   [ ] Table clean headers
   [ ] Pagination pills
   [ ] Chart still renders (if any products)
   [ ] Export/Import modal opens (click button in header)
   [ ] Low-stock red rows still red
   [ ] Light theme good
   [ ] Dark theme good

5. If all pass:
   git add templates/stock.html kaze_phase4e2_stock.py
   git commit -m "Phase 4e-2: stock page visual overhaul"
   git push

AFTER 4e-2: 4e-3 (Customers page). Then 4e is complete.
""")