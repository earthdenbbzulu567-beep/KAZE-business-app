"""
kaze_phase4d2_dashboard.py — Phase 4d-2.

1. Two-column grid: chart (2/3) + activity feed (1/3)
2. Activity feed redesigned with colored icons + relative timestamps
3. Secondary widgets collapsed under <details>
4. Income/expenses tab: old summaries under <details>

Run from the folder with app.py:
    python kaze_phase4d2_dashboard.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
TPL = 'templates/dashboard.html'

if not os.path.isfile(TPL):
    print(f"ERROR: {TPL} not found.")
    sys.exit(1)

with open(TPL, encoding='utf-8') as f:
    html = f.read()

orig_len = len(html)
b = f"{TPL}.bak.phase4d2_{STAMP}"
shutil.copy2(TPL, b)
print(f"Backup: {b}\n")

FAILED = []

print("[1/6] Extracting activity widget...")
ACTIVITY_RE = re.compile(
    r'<div class="widget">\s*<h2>Recent activity</h2>.*?</ul>\s*</div>',
    re.DOTALL,
)
activity_match = ACTIVITY_RE.search(html)
if not activity_match:
    print("  [FAIL] recent activity widget not found")
    FAILED.append("activity widget")
else:
    activity_block = activity_match.group(0)
    html = html.replace(activity_block, '<!-- ACTIVITY_PLACEHOLDER -->', 1)
    print("  [OK]   activity widget extracted")
    
    NEW_FEED = """<div class="kz-card kz-activity-widget">
    <div class="kz-activity-header">
        <h3>Recent Activity</h3>
        <a href="{{ url_for('activity') }}" class="kz-activity-link">View all →</a>
    </div>
    <ul class="kz-activity-feed">
        {% for act in activities[:8] %}
        {% set act_lower = (act.action or '')|lower %}
        <li class="kz-activity-item">
            <div class="kz-activity-icon {% if 'sale' in act_lower %}sale{% elif 'expense' in act_lower or 'delete' in act_lower %}expense{% elif 'stock' in act_lower or 'product' in act_lower %}stock{% elif 'customer' in act_lower %}customer{% else %}default{% endif %}">
                <i data-lucide="{% if 'sale' in act_lower %}shopping-cart{% elif 'expense' in act_lower %}receipt{% elif 'stock' in act_lower %}package{% elif 'customer' in act_lower %}user-plus{% else %}activity{% endif %}"></i>
            </div>
            <div class="kz-activity-body">
                <div class="kz-activity-action">{{ act.action }}</div>
                {% if act.details %}
                <div class="kz-activity-detail">{{ act.details }}</div>
                {% endif %}
                <div class="kz-activity-time">{{ act.created_at|timesince }}</div>
            </div>
        </li>
        {% else %}
        <li class="kz-activity-empty">No activity yet.</li>
        {% endfor %}
    </ul>
</div>"""

print("[2/6] Building two-column grid wrapper...")
CHART_RE = re.compile(
    r'<div class="widget">\s*<h2>Sales trend \(7 days\)</h2>\s*<div class="chart-container">.*?</canvas>\s*</div>\s*</div>',
    re.DOTALL,
)
chart_match = CHART_RE.search(html)
if not chart_match:
    CHART_RE2 = re.compile(
        r'<div class="widget">\s*<h2>.*?</h2>\s*<div class="chart-container">\s*<canvas id="salesTrendChart".*?</div>\s*</div>',
        re.DOTALL,
    )
    chart_match = CHART_RE2.search(html)

if not chart_match:
    print("  [FAIL] chart widget not found")
    FAILED.append("chart widget")
else:
    chart_block = chart_match.group(0)
    NEW_GRID = f"""<div class="kz-dash-grid">
    <div class="kz-dash-main">
        {chart_block}
    </div>
    <div class="kz-dash-side">
        {NEW_FEED}
    </div>
</div>"""
    html = html.replace(chart_block, NEW_GRID, 1)
    html = html.replace('<!-- ACTIVITY_PLACEHOLDER -->', '', 1)
    print("  [OK]   grid layout created")

print("[3/6] Collapsing secondary widgets...")
SECONDARY_RE = re.compile(
    r"({% if mode_on\('stock'\).*?</div>\s*\{% endif %})\s*"
    r"({% if mode_on\('services'\) and upcoming_sessions %}.*?</div>\s*\{% endif %})\s*"
    r"({% if mode_on\('workspace'\) and open_tasks %}.*?</div>\s*\{% endif %})\s*"
    r"({% if mode_on\('operations'\) and upcoming_recurring %}.*?</div>\s*\{% endif %})",
    re.DOTALL,
)
sec_match = SECONDARY_RE.search(html)
if sec_match:
    full_block = sec_match.group(0)
    NEW_COLLAPSED = f"""<details class="kz-dash-secondary">
    <summary>
        <span>More widgets</span>
        <span class="kz-secondary-hint">Low stock · Upcoming services · Open tasks · Coming up</span>
    </summary>
    <div class="kz-dash-secondary-body">
        {full_block}
    </div>
</details>"""
    html = html.replace(full_block, NEW_COLLAPSED, 1)
    print("  [OK]   secondary widgets collapsed")
else:
    print("  [SKIP] secondary widget pattern not matched")

print("[4/6] Collapsing old summary in income/expenses tab...")
OLD_SUMMARY_RE = re.compile(
    r'(<section class="dash-panel" id="panel-books">\s*)'
    r'(<div class="summary-container">.*?</div>\s*</div>)\s*',
    re.DOTALL,
)
sec_match = OLD_SUMMARY_RE.search(html)
if sec_match:
    prefix = sec_match.group(1)
    old_summary = sec_match.group(2)
    NEW_COLLAPSED_SUMMARY = f"""{prefix}
    <details class="kz-dash-secondary">
        <summary>
            <span>Income &amp; Expenses summary</span>
            <span class="kz-secondary-hint">Other income · Expenses · Net · Cash drawer</span>
        </summary>
        <div class="kz-dash-secondary-body">
            {old_summary}
        </div>
    </details>
    """
    html = html.replace(sec_match.group(0), NEW_COLLAPSED_SUMMARY, 1)
    print("  [OK]   old summary in income/expenses collapsed")
else:
    print("  [SKIP] income/expenses summary not matched")

print("[5/6] Injecting CSS...")
NEW_CSS = """<style id="kaze-dashboard-4d2">
.kz-dash-grid {
    display: grid;
    grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
    gap: 1.25rem;
    margin-bottom: 1.5rem;
    align-items: start;
}
@media (max-width: 960px) {
    .kz-dash-grid { grid-template-columns: 1fr; }
}
.kz-dash-main > .widget:last-child,
.kz-dash-side > .widget:last-child,
.kz-dash-side > .kz-card:last-child { margin-bottom: 0; }

.kz-activity-widget {
    padding: 1.25rem 1.25rem 1rem !important;
    margin: 0 !important;
    height: fit-content;
    display: flex;
    flex-direction: column;
}
.kz-activity-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1rem;
    padding-bottom: 0.85rem;
    border-bottom: 1px solid var(--kz-border, var(--border));
}
.kz-activity-header h3 {
    margin: 0;
    font-size: 0.95rem !important;
    font-weight: 600;
    color: var(--kz-text, var(--text));
}
.kz-activity-link {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--kz-brand, var(--red-bright));
    text-decoration: none;
}
.kz-activity-link:hover { text-decoration: underline; }
.kz-activity-feed {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}
.kz-activity-item { display: flex; gap: 0.75rem; align-items: flex-start; padding: 0; }
.kz-activity-icon {
    width: 32px; height: 32px;
    border-radius: 8px;
    display: grid; place-items: center;
    flex-shrink: 0;
    background: var(--kz-surface-hover, var(--surface2));
}
.kz-activity-icon i, .kz-activity-icon svg { width: 16px; height: 16px; stroke-width: 2; }
.kz-activity-icon.sale { background: #d1fae5; color: #059669; }
.kz-activity-icon.expense { background: #fee2e2; color: #dc2626; }
.kz-activity-icon.stock { background: #dbeafe; color: #2563eb; }
.kz-activity-icon.customer { background: #ede9fe; color: #7c3aed; }
.kz-activity-icon.default { background: #f3f4f6; color: #6b7280; }
html.theme-dark .kz-activity-icon.sale { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
html.theme-dark .kz-activity-icon.expense { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }
html.theme-dark .kz-activity-icon.stock { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
html.theme-dark .kz-activity-icon.customer { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; }
html.theme-dark .kz-activity-icon.default { background: rgba(107, 114, 128, 0.2); color: #d1d5db; }
.kz-activity-body { flex: 1; min-width: 0; }
.kz-activity-action { font-size: 0.85rem; font-weight: 600; color: var(--kz-text, var(--text)); margin-bottom: 2px; }
.kz-activity-detail { font-size: 0.78rem; color: var(--kz-text-muted, var(--text2)); margin-bottom: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kz-activity-time { font-size: 0.72rem; color: var(--kz-text-light, var(--text3)); font-family: var(--mono); }
.kz-activity-empty { color: var(--kz-text-light, var(--text3)); font-size: 0.85rem; text-align: center; padding: 1rem; }

.kz-dash-secondary {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    margin: 1.25rem 0 !important;
    padding: 0 !important;
    overflow: hidden;
}
.kz-dash-secondary > summary {
    padding: 1rem 1.25rem !important;
    cursor: pointer;
    list-style: none;
    display: flex !important;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--kz-text, var(--text));
}
.kz-dash-secondary > summary::-webkit-details-marker { display: none; }
.kz-dash-secondary > summary::after {
    content: '▾';
    color: var(--kz-text-muted, var(--text3));
    transition: transform 0.2s;
}
.kz-dash-secondary[open] > summary::after { transform: rotate(180deg); }
.kz-dash-secondary[open] > summary { border-bottom: 1px solid var(--kz-border, var(--border)); }
.kz-secondary-hint { font-size: 0.78rem; font-weight: 500; color: var(--kz-text-light, var(--text3)); }
.kz-dash-secondary-body { padding: 1rem 1.25rem; }
.kz-dash-secondary-body .widget { margin: 0 0 1rem !important; padding: 1rem !important; }
.kz-dash-secondary-body .widget:last-child { margin-bottom: 0 !important; }
</style>"""

if 'kaze-dashboard-4d2' not in html:
    if '</head>' in html:
        html = html.replace('</head>', NEW_CSS + '\n</head>', 1)
        print("  [OK]   CSS injected")
    elif '{% block content %}' in html:
        html = html.replace('{% block content %}', '{% block content %}\n' + NEW_CSS, 1)
        print("  [OK]   CSS injected at content start")
    else:
        print("  [FAIL] no injection point")
        FAILED.append("CSS")
else:
    print("  [SKIP] CSS already present")

print("[6/6] Verifying...")
with open(TPL, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"  [OK]   Written ({orig_len:,} -> {len(html):,} chars)")

try:
    Environment().parse(html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    print(f"\nRestore: copy \"{b}\" {TPL}")
    sys.exit(1)

checks = {
    'two-column grid':       'kz-dash-grid' in html,
    'activity feed':         'kz-activity-feed' in html,
    'activity icons':        'kz-activity-icon' in html,
    'secondary collapsed':   'kz-dash-secondary' in html,
    'more widgets summary':  'More widgets' in html,
    'CSS present':           'kaze-dashboard-4d2' in html,
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

print("Phase 4d-2 complete.")
print("  Layout:  2/3 chart + 1/3 activity feed")
print("  Feed:    colored icons + relative timestamps")
print("  Extra:   Low stock / services / tasks / recurring collapsed")
print("  Books:   old summary cards collapsed")
print("=" * 62)