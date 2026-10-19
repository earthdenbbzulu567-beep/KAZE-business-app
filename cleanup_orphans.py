"""
cleanup_orphans.py — remove the ~80 orphan routes.

These are all the "@app.route('/sales/margin-alert')" style routes at
the bottom of app.py under '# ==== Multi Unique Functions Per Feature ===='.

Nothing in the sidebar, Ctrl+K palette, or any template links to them.
Most of them would 500 if visited anyway (they pass variables that
their templates never read). They bloat app.py by ~2,000 lines and
pollute every future search.

This script:
  1. Deletes the block from 'Multi Unique Functions' up to '/business-man'
  2. Re-adds /tax/estimate and /tax/calendar as tiny redirects to /tax
     (defensive — old bookmarks still work, but no duplicate SQL)
  3. Compile-checks the result

Run from the folder with app.py:
    python cleanup_orphans.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found. Run from the project root.")
    print(f"Current folder: {os.getcwd()}")
    sys.exit(1)

backup = f"{APP}.bak.{STAMP}"
shutil.copy2(APP, backup)
print(f"Backup saved: {backup}\n")

with open(APP, 'r', encoding='utf-8') as fh:
    original = fh.read()

before_size = len(original)
print(f"app.py before: {before_size:,} bytes")

# ─────────────────────────────────────────────────────────────────────
# Locate block boundaries
# ─────────────────────────────────────────────────────────────────────
START = "# ======================== Multi Unique Functions Per Feature ========================"
END = "@app.route('/business-man')"

start_idx = original.find(START)
if start_idx == -1:
    print("\n[SKIP] 'Multi Unique Functions Per Feature' block not found")
    print("       Already cleaned up? Nothing to do.")
    sys.exit(0)

end_idx = original.find(END, start_idx + len(START))
if end_idx == -1:
    print("\n[FAIL] Could not find '@app.route('/business-man')' after the block start")
    print("       Aborting — restore from backup if needed.")
    sys.exit(1)

removed_chunk = original[start_idx:end_idx]
route_count = removed_chunk.count("@app.route(")
line_count = removed_chunk.count('\n')

print(f"\nRemoving block:")
print(f"  • {route_count} orphan routes")
print(f"  • {line_count:,} lines")
print(f"  • {len(removed_chunk):,} bytes ({len(removed_chunk)/before_size*100:.0f}% of file)")

# Show the first and last 5 routes being deleted (sanity check)
route_names = re.findall(r"@app\.route\('([^']+)'\)", removed_chunk)
print(f"\n  First 5 routes:")
for r in route_names[:5]:
    print(f"    - {r}")
print(f"  … and {len(route_names) - 10} in between …")
print(f"  Last 5 routes:")
for r in route_names[-5:]:
    print(f"    - {r}")

# ─────────────────────────────────────────────────────────────────────
# Delete the block
# ─────────────────────────────────────────────────────────────────────
src = original[:start_idx] + original[end_idx:]

# Re-add /tax/estimate and /tax/calendar as redirects (bookmark compat)
RE_ADD = '''@app.route('/tax/estimate')
@login_required
def tax_estimate():
    """Alias for /tax — kept for old bookmarks."""
    return redirect(url_for('tax_summary'))


@app.route('/tax/calendar')
@login_required
def tax_calendar():
    """Alias for /tax — kept for old bookmarks."""
    return redirect(url_for('tax_summary'))


'''

src = src.replace(END, RE_ADD + END, 1)

# Collapse any triple-newlines
src = re.sub(r'\n{3,}', '\n\n\n', src)

after_size = len(src)
print(f"\napp.py after:  {after_size:,} bytes  (saved {before_size - after_size:,})")

with open(APP, 'w', encoding='utf-8') as fh:
    fh.write(src)
print(f"Wrote {after_size:,} bytes to {APP}")

# ─────────────────────────────────────────────────────────────────────
# Compile check
# ─────────────────────────────────────────────────────────────────────
print("\nVerifying app.py compiles…")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)
    print(f"\nRestore with:  copy \"{backup}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly.")

# ─────────────────────────────────────────────────────────────────────
# Confirm the essential routes still exist
# ─────────────────────────────────────────────────────────────────────
print("\nConfirming essential routes still exist…")
must_have = [
    "'/business-man'", "'/business-man/ask'", "'/tax'", "'/tax/estimate'",
    "'/tax/calendar'", "'/dashboard'", "'/sales'", "'/stock'",
    "'/customers'", "'/counter'", "'/reports'", "'/stats'",
]
for name in must_have:
    if name in src:
        print(f"  [OK]   {name}")
    else:
        print(f"  [WARN] {name} missing — investigate")

# ─────────────────────────────────────────────────────────────────────
# Check no template url_for's a deleted endpoint
# ─────────────────────────────────────────────────────────────────────
print("\nScanning templates for references to deleted routes…")
deleted = set()
for name in route_names:
    if '/tax/estimate' in name or '/tax/calendar' in name:
        continue  # re-added as redirects
    deleted.add(name)

dangling = 0
if os.path.isdir('templates'):
    for root, _, files in os.walk('templates'):
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                html = fh.read()
            for route in deleted:
                # Best-effort: match url_for('name') where name is the last path segment
                endpoint = route.rsplit('/', 1)[-1].replace('-', '_') if '/' in route else route
                if f"url_for('{endpoint}')" in html or f'url_for("{endpoint}")' in html:
                    print(f"  [WARN] {p} references {route} (as {endpoint})")
                    dangling += 1
if dangling == 0:
    print("  [OK]   no template references a deleted route")

# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"Deleted:  {len(route_names) - 2} routes  (kept 2 as redirects)")
print(f"Saved:    {before_size - after_size:,} bytes")
print(f"app.py:   {after_size:,} bytes")
print("=" * 60)
print("\nRestart Flask, then spot-check:")
print("  /dashboard   /sales   /stock   /tax   /business-man   → still work")
print("  /sales/velocity   /stock/abc   /goals/velocity        → 404 (correct)")
print("  /tax/estimate   /tax/calendar                          → 302 → /tax")