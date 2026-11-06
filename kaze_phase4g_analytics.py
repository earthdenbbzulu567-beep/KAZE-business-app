"""
kaze_phase4g_analytics.py — Phase 4g.

Injects a unified page-scoped CSS block into the 10 Analytics pages to
match the new mockup design. Pure CSS injection. No logic or HTML changes.
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

FILES = [
    'templates/sales_analytics.html',
    'templates/customers_analytics.html',
    'templates/stock_analytics.html',
    'templates/accounts_health.html',
    'templates/analytics_decisions.html',
    'templates/analytics_patterns.html',
    'templates/team_health.html',
    'templates/workflow_signals.html',
    'templates/services_analytics.html',
    'templates/settings_audit.html',
]

for path in FILES:
    if not os.path.isfile(path):
        print(f"ERROR: {path} not found.")
        sys.exit(1)
    shutil.copy2(path, f"{path}.bak.phase4g_{STAMP}")
    print(f"Backup: {path}.bak.phase4g_{STAMP}")

ANALYTICS_CSS = """{% block content %}
<style id="kaze-analytics-4g">
/* Phase 4g — Analytics page visual unification */

/* Page Header */
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

/* Cleaner Headings */
.page-content h2 {
    font-size: 0.98rem !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
    font-weight: 600 !important;
    color: var(--kz-text, var(--text)) !important;
    margin: 1.75rem 0 0.85rem !important;
}
.page-content h2::before { display: none !important; }

/* Stat Chips → KPI Cards */
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

/* Widgets / Cards */
.page-content .widget {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    margin: 1.5rem 0 !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
}

/* Tabs (Analytics specific) */
.analytics-tabs {
    display: flex !important;
    gap: 0.4rem !important;
    margin: 1rem 0 1.5rem !important;
    flex-wrap: wrap !important;
    border-bottom: none !important;
}
.analytics-tabs button {
    background: transparent !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: 999px !important;
    padding: 0.5rem 1.1rem !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: var(--kz-text-muted, var(--text2)) !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    font-family: inherit !important;
}
.analytics-tabs button:hover {
    background: var(--kz-surface-hover, var(--surface2)) !important;
    color: var(--kz-text, var(--text)) !important;
}
.analytics-tabs button.is-on {
    background: var(--kz-brand, var(--red-bright)) !important;
    color: #ffffff !important;
    border-color: var(--kz-brand, var(--red-bright)) !important;
    font-weight: 700 !important;
}

/* Tables inside analytics */
.page-content .table-wrapper {
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    overflow: hidden;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
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
</style>
"""

for path in FILES:
    with open(path, encoding='utf-8') as f:
        html = f.read()

    if 'kaze-analytics-4g' in html:
        print(f"  [SKIP] {path} — already patched")
        continue

    if '{% block content %}' in html:
        html = html.replace('{% block content %}', ANALYTICS_CSS, 1)
    else:
        print(f"  [FAIL] {path} — no block content")
        continue

    try:
        Environment().parse(html)
        print(f"  [OK]   {path} parsed")
    except Exception as exc:
        print(f"  [FAIL] {path} Jinja error: {exc}")
        continue

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  [OK]   {path} written")

print("\n" + "=" * 62)
print("Phase 4g complete.")
print("  10 analytics pages now use mockup styling.")
print("=" * 62)
print("""
NEXT STEPS:
1. Restart: python app.py
2. Test these 10 pages:
   - /sales/analytics
   - /customers/analytics
   - /stock/analytics
   - /accounts/health
   - /analytics/decisions
   - /analytics/patterns
   - /team/health
   - /workflow/signals
   - /services/analytics
   - /settings/audit

   Check: Tabs are pill-shaped. KPI cards have green top borders.
          Tables have clean headers. No errors.

3. Commit:
   rm templates/*.bak.phase4g_*
   git add templates/*.html kaze_phase4g_analytics.py
   git commit -m "Phase 4g: analytics pages visual unification"
   git push

Once 4g is pushed and Render is green, Phase 4 is officially done.
""")