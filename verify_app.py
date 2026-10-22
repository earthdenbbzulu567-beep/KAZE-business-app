"""
verify_app.py — confirm every Supreme route is registered.

Run from the app folder:
    python verify_app.py

Imports the app and lists every registered route. No DB connection required.
"""
import sys

print("KAZE route verification")
print("=" * 60)

try:
    from app import app
except Exception as e:
    print(f"[FAIL] Could not import app.py: {e}")
    sys.exit(1)

routes = sorted([r.rule for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>'])
print(f"Total routes registered: {len(routes)}\n")

REQUIRED = [
    '/', '/login', '/signup', '/dashboard',
    '/goals', '/insights', '/profit_matrix', '/forecast', '/rfm', '/health',
    '/credit_scores', '/scanner', '/voice', '/batches',
    '/supreme',
    '/api/lookup-sku', '/voice/sale',
    '/stock', '/sales', '/customers', '/counter', '/reports', '/settings',
    '/tax', '/swot', '/business-plan', '/collections',
    '/banking', '/investments', '/shop', '/market', '/payments',
    '/purchase-orders', '/suppliers', '/recurring', '/budgets',
    '/docs', '/calendar', '/tasks', '/notes', '/reminders',
    '/team', '/activity', '/tutorial', '/shortcuts',
    '/plans', '/notifications', '/healthz',
]

print("Required routes:")
ok = fail = 0
for path in REQUIRED:
    found = path in routes
    print(f"  [{'OK' if found else 'MISSING'}] {path}")
    if found: ok += 1
    else: fail += 1

print("\n" + "=" * 60)
print(f"{ok} found · {fail} missing")

if fail:
    print("\nMissing routes may be intentional if you removed features.")
else:
    print("\nAll required routes registered.")
