"""
kaze_phase5_bugfix.py — Final GUI sweep, dropdown cleanup, table fixes, and DB indexes.
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
    'app.py',
    'templates/base.html',
    'templates/supreme.html',
    'templates/purchase_orders.html',
    'templates/suppliers.html',
    'templates/budgets.html',
    'templates/docs.html',
    'templates/profit_matrix.html',
    'templates/rfm.html',
    'templates/health.html',
    'templates/forecast.html',
    'templates/market.html',
    'templates/investments.html',
    'templates/shop.html',
    'templates/reports.html',
    'templates/dashboard.html',
]

for path in FILES:
    if os.path.isfile(path):
        shutil.copy2(path, f"{path}.bak.phase5bug_{STAMP}")
        print(f"Backup: {path}.bak.phase5bug_{STAMP}")

# ═══════════════════════════════════════════════════════════════════
print("\n[1/4] Fixing Top-Right Dropdown (base.html)")
# ═══════════════════════════════════════════════════════════════════

with open('templates/base.html', encoding='utf-8') as f:
    base_html = f.read()

OLD_DROPDOWN = """            <div class="dropdown-content">
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
            </div>"""

NEW_DROPDOWN = """            <div class="dropdown-content">
                <a href="{{ url_for('team') }}">👥 Team</a>
                <a href="{{ url_for('activity') }}">🕓 Login Activity</a>
                <a href="{{ url_for('backup_export') }}">⬇️ Download Backup</a>
                <hr style="margin: 4px 0; border: none; border-top: 1px solid var(--border);">
                <a href="#" onclick="openModal('tutorialModal'); return false;">❓ Help / Tutorial</a>
                <a href="{{ url_for('settings') }}">⚙️ Settings</a>
                <a href="{{ url_for('legal_licence') }}">📜 Licence</a>
                <a href="{{ url_for('legal_terms') }}">📜 Terms</a>
                <hr style="margin: 4px 0; border: none; border-top: 1px solid var(--border);">
                <a href="{{ url_for('logout') }}" style="color: #e74c3c;">🚪 Logout</a>
            </div>"""

if '👥 Team' in base_html and 'Workshop Bench' in base_html:
    base_html = base_html.replace(OLD_DROPDOWN, NEW_DROPDOWN, 1)
    print("  [OK]   Dropdown cleaned up (removed redundant sidebar links).")
else:
    print("  [WARN] Dropdown pattern not matched. Skipping.")

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(base_html)


# ═══════════════════════════════════════════════════════════════════
print("\n[2/4] Updating App Speed (DB Indexes in app.py)")
# ═══════════════════════════════════════════════════════════════════

with open('app.py', encoding='utf-8') as f:
    app_src = f.read()

NEW_INDEXES = """
    # Phase 5 Speed Optimizations
    cur.execute('CREATE INDEX IF NOT EXISTS idx_activities_user_time ON activities (user_id, created_at DESC)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_time ON user_activity (user_id, login_time DESC)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications (user_id, is_read)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_sales_date ON sales (user_id, sale_date)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses (user_id, date)')
"""

if 'idx_activities_user_time' not in app_src:
    # Inject after the first index creation in init_db
    anchor = "cur.execute('CREATE INDEX IF NOT EXISTS idx_snippets_user ON code_snippets (user_id)')"
    if anchor in app_src:
        app_src = app_src.replace(anchor, anchor + "\n" + NEW_INDEXES, 1)
        print("  [OK]   Added missing DB indexes for speed.")
    else:
        print("  [WARN] Could not find index anchor in app.py.")
else:
    print("  [SKIP] DB indexes already exist.")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_src)


# ═══════════════════════════════════════════════════════════════════
print("\n[3/4] Sweeping Legacy Pages & Supreme Desk (CSS Injection)")
# ═══════════════════════════════════════════════════════════════════

LEGACY_CSS = """
{% block content %}
<style id="kaze-legacy-sweep">
/* Phase 5 — Force legacy pages to match the Fintech Mockup */

.page-content .page-header {
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
    padding-bottom: 1rem !important;
    margin-bottom: 1.5rem !important;
}
.page-content .page-header h1 {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: var(--kz-text, var(--text)) !important;
}
.page-content h2 {
    font-size: 0.98rem !important;
    text-transform: none !important;
    font-weight: 600 !important;
    color: var(--kz-text, var(--text)) !important;
    margin: 1.75rem 0 0.85rem !important;
}
.page-content h2::before { display: none !important; }

/* Force all tables to be scrollable and not break */
.page-content .table-wrapper {
    overflow-x: auto !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
}
.page-content table { width: 100% !important; min-width: 600px; table-layout: auto !important; }
.page-content thead th {
    background: var(--kz-bg, var(--bg3)) !important;
    color: var(--kz-text-muted, var(--text3)) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
}
.page-content tbody td {
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
    color: var(--kz-text, var(--text)) !important;
    white-space: nowrap !important;
    font-variant-numeric: tabular-nums;
}

/* Force old .widget blocks to become .kz-cards */
.page-content .widget, .page-content .kz-card {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05)) !important;
    margin-bottom: 1.5rem !important;
}

/* Fix Supreme Tiles */
.supreme-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.9rem; margin: 1rem 0 2rem; }
.supreme-tile {
    background: var(--kz-surface, var(--surface));
    border: 1px solid var(--kz-border, var(--border));
    border-radius: var(--kz-radius, 12px);
    padding: 1.25rem 1.1rem;
    text-decoration: none;
    color: inherit;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
    transition: transform 0.15s;
}
.supreme-tile:hover { transform: translateY(-2px); border-color: var(--kz-brand); }
.tile-value { font-size: 2rem; font-family: var(--mono); font-weight: 800; margin: 0.2rem 0; display: block; }
</style>
"""

SWEEP_FILES = [
    'templates/supreme.html',
    'templates/purchase_orders.html',
    'templates/suppliers.html',
    'templates/budgets.html',
    'templates/docs.html',
    'templates/profit_matrix.html',
    'templates/rfm.html',
    'templates/health.html',
    'templates/forecast.html',
    'templates/market.html',
    'templates/investments.html',
    'templates/shop.html'
]

for path in SWEEP_FILES:
    if not os.path.exists(path): continue
    with open(path, encoding='utf-8') as f:
        html = f.read()
    
    if 'kaze-legacy-sweep' in html: continue
    
    if '{% block content %}' in html:
        html = html.replace('{% block content %}', LEGACY_CSS, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  [OK]   Swept {os.path.basename(path)}")


# ═══════════════════════════════════════════════════════════════════
print("\n[4/4] Enhancing Charts (Detailed Tooltips)")
# ═══════════════════════════════════════════════════════════════════

def enhance_charts(filename):
    with open(filename, encoding='utf-8') as f:
        html = f.read()
    
    if 'tooltip: { callbacks:' in html: return

    # Add detailed tooltip callbacks to Chart.js configs
    html = html.replace(
        "plugins: { legend: { position: 'bottom' } },",
        "plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: c => c.dataset.label + ': ' + window.kazeMoney(c.raw) } } },"
    )
    html = html.replace(
        "plugins: { legend: { position: 'top' } },",
        "plugins: { legend: { position: 'top' }, tooltip: { callbacks: { label: c => c.dataset.label + ': ' + window.kazeMoney(c.raw) } } },"
    )
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  [OK]   Enhanced tooltips on {os.path.basename(filename)}")

enhance_charts('templates/dashboard.html')
enhance_charts('templates/reports.html')

# Verify Python syntax
r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

print("\n" + "=" * 62)
print("Phase 5 Bug Fix complete.")
print("=" * 62)