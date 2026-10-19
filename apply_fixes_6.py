"""
apply_fixes_6.py — verifies the critical fixes are in place.
Run from the project root (where app.py lives).

    python apply_fixes_6.py

Does NOT modify anything. Just reports what still needs attention.
"""

import os

CHECKS = [
    # (file, description, must contain, must NOT contain)
    ('app.py', '1.1 /swot route re-enabled',
     "@app.route('/swot')\n@login_required\ndef swot():",
     "# DELETED FEATURE: @app.route('/swot')"),

    ('app.py', '1.2 /snapshot SQL fixed',
     "sale_date >= to_char(date_trunc('month', CURRENT_DATE),'YYYY-MM-DD')",
     "FROM sales WHERE user_id=%s AND date >= DATE_TRUNC"),

    ('app.py', '1.3 /alerts SQL fixed',
     "FROM stock st \"\n        \"WHERE st.user_id=%s AND st.quantity <= COALESCE",
     "COALESCE(low_stock_threshold,5)"),

    ('app.py', '1.4 /daily/compare SQL fixed',
     "sale_date = to_char(CURRENT_DATE,'YYYY-MM-DD')",
     "sale_date=CURRENT_DATE\""),

    ('templates/base.html', '2.1 --accent token added',
     "--accent: var(--red-bright);",
     None),

    ('templates/base.html', '2.2 .page-header gradient removed',
     None,
     "background: linear-gradient(135deg, var(--accent, #10b981)"),

    ('templates/base.html', '2.3 .stat-label rule added',
     ".stat-label {\n  display: block;",
     None),

    ('templates/counter.html', '3.1 tile highlight fixed',
     "basket.some(l => l.id === t.dataset.id)",
     "t.dataset.id === id);"),

    ('templates/business_plan.html', '4.1 SWOT link fixed',
     'url_for(\'swot\')',
     'url_for(\'business_plan\')">SWOT Analysis'),
]

print("KAZE fix verification\n" + "=" * 55)

ok = fail = 0
for path, label, must_contain, must_not_contain in CHECKS:
    if not os.path.isfile(path):
        print(f"[MISSING] {label} — {path} not found")
        fail += 1
        continue
    with open(path, 'r', encoding='utf-8') as fh:
        src = fh.read()

    problems = []
    if must_contain and must_contain not in src:
        problems.append("expected marker not found")
    if must_not_contain and must_not_contain in src:
        problems.append("old code still present")

    if problems:
        print(f"[FAIL] {label} — {', '.join(problems)}")
        fail += 1
    else:
        print(f"[OK]   {label}")
        ok += 1

print("=" * 55)
print(f"{ok} passed · {fail} failed")
if fail:
    print("\nFix the failed items above (see instructions in the guide).")
else:
    print("\nAll critical fixes applied. Restart Flask and test:")
    print("  /tutorial   /snapshot   /alerts   /daily/compare")
    print("  /counter (tap 3 tiles → all stay green)")