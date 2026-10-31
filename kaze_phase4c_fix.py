"""
kaze_phase4c_fix.py — fix Jinja scoping bug in sidebar template.

Root cause: {% set %} inside {% for %} doesn't persist in Jinja 2/3.
Fix: use rejectattr filter + namespace object.

Only replaces the sidebar <nav> block. Nothing else touched.

Run from the folder with app.py:
    python kaze_phase4c_fix.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
BASE = 'templates/base.html'

if not os.path.isfile(BASE):
    print(f"ERROR: {BASE} not found.")
    sys.exit(1)

with open(BASE, encoding='utf-8') as f:
    html = f.read()

b = f"{BASE}.bak.phase4cfix_{STAMP}"
shutil.copy2(BASE, b)
print(f"Backup: {b}\n")

NEW_NAV = """<nav class="sidebar-nav kz-sidebar" id="kz-sidebar-nav">
    {% set pinned = ['dashboard', 'counter', 'sales', 'stock', 'customers', 'services'] %}
    <div class="kz-nav-pinned">
        {% for group in nav_groups or [] %}
            {% for item in group.links %}
                {% if item.endpoint in pinned %}
                <a href="{{ url_for(item.endpoint) }}" class="kz-nav-item {% if request.endpoint in item.active %}active{% endif %}">
                    <i data-lucide="{{ item.icon }}"></i><span>{{ item.label }}</span>
                </a>
                {% endif %}
            {% endfor %}
        {% endfor %}
    </div>
    <div class="kz-nav-divider"></div>
    {% for group in nav_groups or [] %}
        {% set unpinned = group.links | rejectattr('endpoint', 'in', pinned) | list %}
        {% if unpinned %}
        {% set ns = namespace(active=false) %}
        {% for item in unpinned %}
            {% if request.endpoint in item.active %}{% set ns.active = true %}{% endif %}
        {% endfor %}
        <details class="kz-nav-group" {% if ns.active %}open{% endif %} data-group-key="{{ group.title }}">
            <summary class="kz-nav-group-header">
                <span>{{ group.title }}</span>
                <i data-lucide="chevron-down" class="kz-chevron"></i>
            </summary>
            <div class="kz-nav-group-body">
                {% for item in unpinned %}
                <a href="{{ url_for(item.endpoint) }}" class="kz-nav-item {% if request.endpoint in item.active %}active{% endif %}">
                    <i data-lucide="{{ item.icon }}"></i><span>{{ item.label }}</span>
                </a>
                {% endfor %}
            </div>
        </details>
        {% endif %}
    {% endfor %}
</nav>"""

nav_re = re.compile(r'<nav class="sidebar-nav[^"]*"[^>]*>.*?</nav>', re.DOTALL)
html, count = nav_re.subn(NEW_NAV, html, count=1)

if count != 1:
    print("[FAIL] sidebar regex did not match")
    print("       Restore: copy \"{}\" {}".format(b, BASE))
    sys.exit(1)

print("[OK]   sidebar replaced with fixed template")

# Verify — critical check: rejectattr filter and namespace present
checks = {
    'rejectattr used':   'rejectattr' in html,
    'namespace used':    'namespace(active=false)' in html,
    'details group':     '<details class="kz-nav-group"' in html,
    'no scoped set bug': 'unpinned = unpinned +' not in html,
}
all_ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        all_ok = False

# Jinja parse
try:
    Environment().parse(html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    print(f"\nRestore: copy \"{b}\" {BASE}")
    sys.exit(1)

with open(BASE, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n[OK]   Written ({len(html):,} chars)")

if not all_ok:
    print(f"\nRestore: copy \"{b}\" {BASE}")
    sys.exit(1)

print("\n" + "=" * 62)
print("Fix applied.")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart app:  python app.py

2. Reload /dashboard in browser. Hard refresh (Ctrl+F5).

3. You should now see in the sidebar:
   - 6 pinned items (Dashboard, Counter, Sales, Stock, Customers, Services)
   - Divider
   - Collapsible group headers: Money, Trade, Growth, Workspace, Account
     (Analytics section is also a group)

   Note: "Core" group becomes fully empty since all its items are pinned —
   that group header will NOT appear (correct behavior).

4. Click a group header -> expands showing items inside.

5. Navigate to /payments -> "Money" group auto-opens, Pay sub-item active.

Report:
   Groups now visible in sidebar:  ✅ / ❌
   Can expand/collapse:            ✅ / ❌
   Active group auto-opens:        ✅ / ❌
   Pinned items still work:        ✅ / ❌
""")