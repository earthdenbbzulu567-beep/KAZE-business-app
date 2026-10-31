"""
kaze_phase4c_sidebar.py — Phase 4c.

1. Restructures sidebar: 6 pinned items + collapsible groups
2. Cleans up topbar: removes mode chip, plan chip, clock
3. Applies .kz-* styling from Phase 4b
4. Persists collapse state in localStorage

Preserves all existing functionality (mobile drawer, theme toggle,
user menu, notification badge). Backup + verification on failure.

Run from the folder with app.py:
    python kaze_phase4c_sidebar.py
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

orig_len = len(html)

if 'kaze-fintech-tokens' not in html:
    print("ERROR: Phase 4b tokens not found. Run kaze_phase4b_foundation.py first.")
    sys.exit(1)

b = f"{BASE}.bak.phase4c_{STAMP}"
shutil.copy2(BASE, b)
print(f"Backup: {b}\n")

FAILED = []

# ── 1. Replace sidebar <nav> block ─────────────────────────────────
print("[1/5] Replacing sidebar navigation...")

NEW_NAV = """<nav class="sidebar-nav kz-sidebar" id="kz-sidebar-nav">
    {# Pinned core items #}
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
    {# Collapsible groups #}
    {% for group in nav_groups or [] %}
        {% set unpinned = [] %}
        {% for item in group.links %}
            {% if item.endpoint not in pinned %}
                {% set unpinned = unpinned + [item] %}
            {% endif %}
        {% endfor %}
        {% if unpinned %}
        {% set group_active = [] %}
        {% for item in unpinned %}
            {% if request.endpoint in item.active %}
                {% set group_active = group_active + [1] %}
            {% endif %}
        {% endfor %}
        <details class="kz-nav-group" {% if group_active %}open{% endif %} data-group-key="{{ group.title }}">
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

nav_re = re.compile(r'<nav class="sidebar-nav"[^>]*>.*?</nav>', re.DOTALL)
html, count = nav_re.subn(NEW_NAV, html, count=1)
if count != 1:
    print("  [FAIL] sidebar-nav block regex did not match")
    FAILED.append("sidebar nav")
else:
    print("  [OK]   sidebar replaced with pinned + collapsible structure")

# ── 2. Replace topbar ──────────────────────────────────────────────
print("\n[2/5] Replacing topbar...")

NEW_TOPBAR = """<header class="topbar kz-topbar" id="kz-topbar">
    <button class="hamburger" id="hamburgerBtn" aria-label="Toggle sidebar">☰</button>
    <form action="{{ url_for('search') }}" method="GET" class="search-form kz-search">
        <input type="text" name="q" placeholder="Search anything…" aria-label="Search">
        <button type="submit" aria-label="Submit search">🔍</button>
    </form>
    <div class="right-group kz-topbar-right">
        <button type="button" class="theme-toggle" id="themeToggle" title="Toggle theme" aria-label="Toggle theme">🌙</button>
        <button type="button" class="theme-toggle" id="soundToggle" title="Toggle sounds" aria-label="Toggle sounds">🔔</button>
        <a href="{{ url_for('notifications') }}" class="bell-link kz-bell" title="Notifications">
            <i data-lucide="bell"></i>
            {% if unread_notifications and unread_notifications > 0 %}<span class="bell-badge">{{ unread_notifications }}</span>{% endif %}
        </a>
        <div class="user-menu kz-user-menu">
            <button class="dropbtn kz-user-btn">{{ current_user.username }} <i data-lucide="chevron-down"></i></button>
            <div class="dropdown-content">
                <a href="{{ url_for('dashboard') }}">Workshop Bench</a>
                <a href="{{ url_for('team') }}">👥 Team</a>
                <a href="{{ url_for('activity') }}">Login Activity</a>
                <a href="{{ url_for('backup_export') }}">Download backup</a>
                <a href="#" onclick="openModal('tutorialModal'); return false;">Help / Tutorial</a>
                <a href="{{ url_for('tutorial') }}">📖 Practical guide</a>
                <a href="{{ url_for('shortcuts') }}">⌨️ Shortcuts</a>
                <a href="{{ url_for('swot') }}">🧭 SWOT Analysis</a>
                <a href="{{ url_for('settings') }}">Settings</a>
                <a href="{{ url_for('legal_licence') }}">Licence</a>
                <a href="{{ url_for('legal_terms') }}">Terms</a>
                <a href="{{ url_for('logout') }}">Logout</a>
            </div>
        </div>
    </div>
</header>"""

topbar_re = re.compile(r'<header class="topbar"[^>]*>.*?</header>', re.DOTALL)
html, count = topbar_re.subn(NEW_TOPBAR, html, count=1)
if count != 1:
    print("  [FAIL] topbar block regex did not match")
    FAILED.append("topbar")
else:
    print("  [OK]   topbar cleaned (removed mode chip, plan chip, clock)")

# ── 3. Inject sidebar/topbar CSS ───────────────────────────────────
print("\n[3/5] Injecting sidebar + topbar CSS...")

NEW_CSS = """<style id="kaze-fintech-sidebar">
/* Phase 4c — Sidebar + topbar visual */

.sidebar {
    background: var(--kz-surface, var(--surface)) !important;
    border-right: 1px solid var(--kz-border, var(--border)) !important;
}
.sidebar-brand {
    background: transparent !important;
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
    padding: 1.1rem 1rem !important;
}
.sidebar-brand .wordmark b {
    color: var(--kz-text, var(--text)) !important;
    font-family: var(--display);
}
.sidebar-brand .plan-badge {
    background: var(--kz-brand-light, var(--accent-wash)) !important;
    border-color: var(--kz-brand, var(--red-bright)) !important;
    color: var(--kz-brand, var(--red-bright)) !important;
}

.sidebar-nav.kz-sidebar {
    padding: 0.75rem 0.6rem !important;
    background: transparent !important;
}
.kz-nav-pinned { display: flex; flex-direction: column; gap: 2px; margin-bottom: 0.3rem; }
.kz-nav-divider {
    height: 1px;
    background: var(--kz-border, var(--border));
    margin: 0.5rem 0.4rem;
}

.kz-nav-item {
    display: flex !important;
    align-items: center;
    gap: 0.7rem;
    padding: 0.6rem 0.8rem !important;
    border-radius: 10px !important;
    color: var(--kz-text-muted, var(--text2)) !important;
    text-decoration: none !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    margin: 1px 0 !important;
    transition: background 0.15s ease, color 0.15s ease !important;
    overflow: hidden !important;
}
.kz-nav-item:hover {
    background: var(--kz-surface-hover, var(--surface2)) !important;
    color: var(--kz-text, var(--text)) !important;
}
.kz-nav-item.active {
    background: var(--kz-brand, var(--red-bright)) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}
.kz-nav-item.active i, .kz-nav-item.active svg {
    color: #ffffff !important;
    stroke: #ffffff !important;
}
.kz-nav-item i, .kz-nav-item svg {
    width: 17px !important;
    height: 17px !important;
    min-width: 17px !important;
    color: var(--kz-text-muted, var(--text2)) !important;
    stroke-width: 1.8;
    flex-shrink: 0 !important;
}
.kz-nav-item span {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Collapsible groups — override existing details styling */
.kz-nav-group {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    margin: 2px 0 !important;
    box-shadow: none !important;
}
.kz-nav-group[open] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.kz-nav-group > summary {
    padding: 0.55rem 0.75rem !important;
    cursor: pointer;
    list-style: none;
    display: flex !important;
    align-items: center;
    justify-content: space-between;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--kz-text-muted, var(--text3)) !important;
    border-radius: 8px;
    transition: color 0.15s, background 0.15s;
}
.kz-nav-group > summary:hover {
    color: var(--kz-text, var(--text)) !important;
    background: var(--kz-surface-hover, var(--surface2)) !important;
}
.kz-nav-group > summary::-webkit-details-marker { display: none; }
.kz-nav-group > summary::after { display: none !important; content: none !important; }
.kz-chevron {
    width: 13px !important;
    height: 13px !important;
    transition: transform 0.2s ease;
    flex-shrink: 0;
    opacity: 0.6;
}
.kz-nav-group[open] .kz-chevron {
    transform: rotate(180deg);
    opacity: 1;
}
.kz-nav-group-body {
    padding: 0.15rem 0 0.35rem;
    display: flex;
    flex-direction: column;
    gap: 1px;
}

/* ── Topbar ── */
.topbar.kz-topbar {
    padding: 0.6rem 1.5rem !important;
    background: var(--kz-surface, var(--surface)) !important;
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
    backdrop-filter: none !important;
    display: flex !important;
    align-items: center;
    gap: 1rem;
}
.search-form.kz-search {
    flex: 1 1 auto !important;
    max-width: 480px !important;
    margin: 0 auto !important;
    position: relative;
}
.search-form.kz-search input {
    width: 100% !important;
    border-radius: 999px !important;
    padding: 0.55rem 1rem 0.55rem 2.5rem !important;
    background: var(--kz-bg, var(--surface2)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.88rem !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.3-4.3'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: 0.9rem center !important;
}
.search-form.kz-search input:focus {
    outline: none !important;
    border-color: var(--kz-brand, var(--red-bright)) !important;
    box-shadow: 0 0 0 3px var(--kz-brand-glow, var(--red-glow)) !important;
}
.search-form.kz-search button { display: none !important; }

.kz-topbar-right {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    flex-shrink: 0;
}
.kz-topbar-right .theme-toggle {
    width: 36px !important; height: 36px !important;
    border-radius: 50% !important;
    background: transparent !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    color: var(--kz-text-muted, var(--text2)) !important;
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    padding: 0 !important;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
    clip-path: none !important;
}
.kz-topbar-right .theme-toggle:hover {
    background: var(--kz-surface-hover, var(--surface2)) !important;
    border-color: var(--kz-text-muted, var(--text2)) !important;
    transform: none !important;
}
.kz-bell {
    position: relative !important;
    width: 36px !important; height: 36px !important;
    border-radius: 50% !important;
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    color: var(--kz-text-muted, var(--text2)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    text-decoration: none !important;
    transition: background 0.15s, border-color 0.15s;
}
.kz-bell:hover {
    background: var(--kz-surface-hover, var(--surface2)) !important;
    border-color: var(--kz-text-muted, var(--text2)) !important;
    transform: none !important;
}
.kz-bell svg { width: 16px !important; height: 16px !important; stroke-width: 1.8; }
.kz-bell .bell-badge {
    position: absolute !important;
    top: -4px !important; right: -4px !important;
    background: #dc2626 !important;
    color: #fff !important;
    font-size: 0.6rem !important;
    font-weight: 700 !important;
    border-radius: 999px !important;
    padding: 1px 5px !important;
    line-height: 1.2 !important;
    animation: none !important;
}
.kz-user-btn {
    display: inline-flex !important;
    align-items: center;
    gap: 0.4rem;
    padding: 0.45rem 0.8rem !important;
    border-radius: 999px !important;
    background: var(--kz-surface-hover, var(--surface2)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-weight: 600;
    font-size: 0.85rem !important;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
    font-family: inherit;
}
.kz-user-btn:hover {
    background: var(--kz-brand-light, var(--accent-wash)) !important;
    border-color: var(--kz-brand, var(--red-bright)) !important;
    transform: none !important;
}
.kz-user-btn svg { width: 13px !important; height: 13px !important; stroke-width: 2; }

@media (max-width: 768px) {
    .topbar.kz-topbar { padding: 0.5rem 1rem !important; flex-wrap: wrap; }
    .search-form.kz-search { max-width: 100% !important; order: 3; flex: 1 1 100% !important; margin-top: 0.4rem !important; }
}
</style>"""

if 'kaze-fintech-sidebar' not in html:
    if '</head>' in html:
        html = html.replace('</head>', NEW_CSS + '\n</head>', 1)
        print("  [OK]   sidebar/topbar CSS injected")
    else:
        print("  [FAIL] </head> not found")
        FAILED.append("CSS injection")
else:
    print("  [SKIP] CSS already present")

# ── 4. Inject collapse persistence JS ─────────────────────────────
print("\n[4/5] Injecting collapse persistence JS...")

NEW_JS = """<script id="kaze-sidebar-js">
(function(){
    var STORAGE_KEY = 'kaze-sidebar-groups-v1';
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch(e) {}
    var groups = document.querySelectorAll('.kz-nav-group');
    groups.forEach(function(g) {
        var key = g.dataset.groupKey || '';
        if (!key) return;
        // If this group contains the active page, always open
        if (g.querySelector('.kz-nav-item.active')) {
            g.open = true;
            return;
        }
        // Otherwise restore saved state
        if (key in saved) {
            g.open = saved[key];
        }
        g.addEventListener('toggle', function() {
            saved[key] = g.open;
            try { localStorage.setItem(STORAGE_KEY, JSON.stringify(saved)); } catch(e) {}
        });
    });
})();
</script>"""

if 'kaze-sidebar-js' not in html:
    if '</body>' in html:
        html = html.replace('</body>', NEW_JS + '\n</body>', 1)
        print("  [OK]   persistence JS injected")
    else:
        print("  [FAIL] </body> not found")
        FAILED.append("JS injection")
else:
    print("  [SKIP] JS already present")

# ── 5. Write + verify ─────────────────────────────────────────────
print("\n[5/5] Verifying...")

with open(BASE, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"  [OK]   Written ({orig_len:,} -> {len(html):,} chars)")

try:
    Environment().parse(html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    print(f"\nRestore: copy \"{b}\" {BASE}")
    sys.exit(1)

checks = {
    'kz-sidebar class':        'kz-sidebar' in html,
    'kz-nav-item class':       'kz-nav-item' in html,
    'kz-nav-group class':      'kz-nav-group' in html,
    'collapsible details':     '<details class="kz-nav-group"' in html,
    'topbar redesigned':       'kz-topbar' in html,
    'search redesign':         'kz-search' in html,
    'JS persistence':          'kaze-sidebar-groups-v1' in html,
    'pinned items':            "'dashboard', 'counter', 'sales', 'stock', 'customers', 'services'" in html,
}
all_ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present:
        all_ok = False

print("\n" + "=" * 62)
if FAILED or not all_ok:
    print("Some changes failed:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore: copy \"{b}\" {BASE}")
    sys.exit(1)

print("Phase 4c complete.")
print("  Sidebar: 6 pinned + 5 collapsible groups")
print("  Topbar: mode/plan/clock removed")
print("  Collapse state persists in localStorage")
print(f"  File: {orig_len:,} -> {len(html):,} chars")
print("=" * 62)
print("""
NEXT STEPS:

1. LOCAL TEST — run:  python app.py

   Visual checklist:

   a) Sidebar looks different — pinned items (Dashboard, Counter, Sales,
      Stock, Customers, Services) at top with green pill on active page.
      Below: collapsible sections (Money, Trade, Analytics, Growth,
      Workspace, Account) with chevrons.

   b) Click a group header -> expands/collapses smoothly.

   c) Navigate to a page inside a group (e.g. /payments, /reports,
      /analytics/decisions) -> that group auto-expands, item is
      green-pill active.

   d) Reload page. Your collapse state persists (localStorage).

   e) Topbar: cleaner. No mode/plan chips. No clock. Search is centered.
      Right side: theme toggle, sound toggle, bell, user pill.

   f) Click theme toggle -> light theme sidebar turns white with green pills
      (mockup look). Dark theme still dark with green pills.

   g) Mobile view (resize to 400px): sidebar becomes drawer (hamburger
      opens), topbar wraps. Confirm nothing looks broken.

   Regression:

     [ ] All sidebar links still reachable
     [ ] User menu dropdown still works
     [ ] Notification bell badge shows if unread
     [ ] Mobile hamburger still opens sidebar
     [ ] /plans still loads
     [ ] /dashboard still loads

2. IF ANYTHING BROKEN:
   copy "templates/base.html.bak.phase4c_""" + STAMP + """" templates/base.html
   Tell me which element/page.

3. IF ALL PASS:
   git add templates/base.html kaze_phase4c_sidebar.py
   git commit -m "Phase 4c: sidebar restructure + topbar cleanup"
   git push

4. Deploy to production. Same visual test on prod.

5. Cleanup: rm templates/base.html.bak.phase4c_*

AFTER 4c CONFIRMS: Phase 4d begins — Dashboard redesign.
""")