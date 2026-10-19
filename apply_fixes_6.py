"""
apply_fixes_6.py — KAZE verification (14 checks).

Covers:
  1.1–1.4b  Critical 500 fixes and cleanup verification
  2.1–2.3   base.html CSS fixes
  3.1       counter.html tile highlight
  4.1       business_plan.html SWOT link
  11–14     Supreme page rebuilds (profit_matrix, forecast, rfm, health)

Run from the project root:
    python apply_fixes_6.py
"""

import os

CHECKS = [
    {
        'label': '1.1 /swot route re-enabled',
        'file': 'app.py',
        'must_contain': "@app.route('/swot')\n@login_required\ndef swot():",
        'must_not_contain': "# DELETED FEATURE: @app.route('/swot')",
    },
    {
        'label': '1.2 /snapshot SQL fixed',
        'file': 'app.py',
        'must_contain': "sale_date >= to_char(date_trunc('month', CURRENT_DATE),'YYYY-MM-DD')",
        'must_not_contain': "FROM sales WHERE user_id=%s AND date >= DATE_TRUNC",
    },
    {
        'label': '1.3 /alerts SQL fixed',
        'file': 'app.py',
        'must_contain': "WHERE st.user_id=%s AND st.quantity <= COALESCE",
        'must_not_contain': "COALESCE(low_stock_threshold,5)",
    },
    {
        'label': '1.4 no bare sale_date=CURRENT_DATE anywhere',
        'file': 'app.py',
        'must_contain': None,
        'must_not_contain': 'sale_date=CURRENT_DATE"',
    },
    {
        'label': '1.4b /day-close/variance route removed (cleanup)',
        'file': 'app.py',
        'must_contain': None,
        'must_not_contain': "def day_close_variance():",
    },
    {
        'label': '2.1 --accent token added',
        'file': 'templates/base.html',
        'must_contain': "--accent: var(--red-bright);",
        'must_not_contain': None,
    },
    {
        'label': '2.2 .page-header gradient removed',
        'file': 'templates/base.html',
        'must_contain': None,
        'must_not_contain': "background: linear-gradient(135deg, var(--accent, #10b981)",
    },
    {
        'label': '2.3 .stat-label rule added',
        'file': 'templates/base.html',
        'must_contain': ".stat-label {",
        'must_not_contain': None,
    },
    {
        'label': '3.1 counter tile highlight fixed',
        'file': 'templates/counter.html',
        'must_contain': "basket.some(l => l.id === t.dataset.id)",
        'must_not_contain': None,
    },
    {
        'label': '4.1 SWOT link in business_plan.html',
        'file': 'templates/business_plan.html',
        'must_contain': "url_for('swot')",
        'must_not_contain': 'url_for(\'business_plan\')">SWOT Analysis',
    },
    {
        'label': '11 profit_matrix scatter chart',
        'file': 'templates/profit_matrix.html',
        'must_contain': "type: 'scatter'",
        'must_not_contain': None,
    },
    {
        'label': '12 forecast 3-line chart',
        'file': 'templates/forecast.html',
        'must_contain': "label: 'Worst case'",
        'must_not_contain': None,
    },
    {
        'label': '13 rfm segment grid',
        'file': 'templates/rfm.html',
        'must_contain': 'rfm-grid',
        'must_not_contain': None,
    },
    {
        'label': '14 health component grid',
        'file': 'templates/health.html',
        'must_contain': 'health-grid',
        'must_not_contain': None,
    },
]

print("KAZE fix verification")
print("=" * 60)

ok = fail = 0
for check in CHECKS:
    path = check['file']
    label = check['label']

    if not os.path.isfile(path):
        print(f"[MISSING] {label} — {path} not found")
        fail += 1
        continue

    with open(path, 'r', encoding='utf-8') as fh:
        src = fh.read()

    problems = []
    if check['must_contain'] and check['must_contain'] not in src:
        problems.append("expected marker missing")
    if check['must_not_contain'] and check['must_not_contain'] in src:
        problems.append("old code still present")

    if problems:
        print(f"[FAIL] {label} — {', '.join(problems)}")
        fail += 1
    else:
        print(f"[OK]   {label}")
        ok += 1

print("=" * 60)
print(f"{ok} passed · {fail} failed")

if fail:
    print("\nFix the failed items above, then re-run this script.")
else:
    print("\nAll 14 fixes verified.")
    print("\nSpot-check in the browser:")
    print("  /tutorial /snapshot /alerts         → load without 500")
    print("  /counter (tap 3 tiles)              → all stay green")
    print("  any page                            → no green banner at top")
    print("  /goals                              → real numbers, pace bar")
    print("  /insights                           → 5–6 live insight cards")
    print("  /profit_matrix                      → scatter + quadrant table")
    print("  /forecast                           → 3-line chart from real cash")
    print("  /rfm                                → 6 segment cards + scored table")
    print("  /health                             → 5-component score breakdown")