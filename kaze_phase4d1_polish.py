"""
kaze_phase4d1_polish.py — Phase 4d-1 polish.

1. Smooth sidebar expand/collapse animation (grid trick + chevron ease)
2. Global Chart.js theming — colors, fonts, tooltips via Chart.defaults
3. Light mode: force surface vars white, darken --text3 for contrast

Run from the folder with app.py:
    python kaze_phase4d1_polish.py
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
b = f"{BASE}.bak.phase4d1polish_{STAMP}"
shutil.copy2(BASE, b)
print(f"Backup: {b}\n")

FAILED = []

# ── [1/4] Wrap nav group body in inner div for grid animation ────
print("[1/4] Restructuring nav group body for animation...")

OLD_BODY = """            <div class="kz-nav-group-body">
                {% for item in unpinned %}
                <a href="{{ url_for(item.endpoint) }}" class="kz-nav-item {% if request.endpoint in item.active %}active{% endif %}">
                    <i data-lucide="{{ item.icon }}"></i><span>{{ item.label }}</span>
                </a>
                {% endfor %}
            </div>"""

NEW_BODY = """            <div class="kz-nav-group-body">
                <div class="kz-nav-group-inner">
                    {% for item in unpinned %}
                    <a href="{{ url_for(item.endpoint) }}" class="kz-nav-item {% if request.endpoint in item.active %}active{% endif %}">
                        <i data-lucide="{{ item.icon }}"></i><span>{{ item.label }}</span>
                    </a>
                    {% endfor %}
                </div>
            </div>"""

if 'kz-nav-group-inner' in html:
    print("  [SKIP] inner wrapper already present")
elif OLD_BODY in html:
    html = html.replace(OLD_BODY, NEW_BODY, 1)
    print("  [OK]   inner wrapper added to group body")
else:
    print("  [FAIL] group body pattern not found")
    FAILED.append("nav group inner wrapper")

# ── [2/4] Add smooth animation + chart theme + light mode fixes ──
print("\n[2/4] Injecting polish CSS + chart theme...")

POLISH_CSS = """<style id="kaze-polish-4d">
/* Sidebar smooth animation (overrides existing to enable grid trick) */
.kz-nav-group-body {
    display: grid !important;
    grid-template-rows: 0fr;
    transition: grid-template-rows 0.28s cubic-bezier(0.4, 0, 0.2, 1),
                opacity 0.2s ease;
    opacity: 0;
    padding: 0 !important;
}
.kz-nav-group[open] .kz-nav-group-body {
    grid-template-rows: 1fr;
    opacity: 1;
    padding-top: 0.15rem !important;
    padding-bottom: 0.35rem !important;
}
.kz-nav-group-inner {
    overflow: hidden;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 1px;
}
.kz-chevron {
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.kz-nav-group[open] .kz-chevron {
    transform: rotate(180deg) !important;
}

/* Light theme hard override — white surfaces regardless of accent */
html.theme-light,
html.theme-light body {
    --surface: #ffffff !important;
    --surface2: #f5f7f8 !important;
    --bg2: #ffffff !important;
    --bg3: #eef2ef !important;
    --text: #111827 !important;
    --text2: #374151 !important;
    --text3: #4b5563 !important;
    --border: #d5ddd7 !important;
    --border2: #c4cdc6 !important;
    color-scheme: light !important;
}

/* Light theme: catch hardcoded gray text in old templates */
html.theme-light .page-content [style*="color:#888"],
html.theme-light .page-content [style*="color: #888"],
html.theme-light .page-content [style*="color:#666"],
html.theme-light .page-content [style*="color: #666"],
html.theme-light .page-content [style*="color:#999"],
html.theme-light .page-content [style*="color: #999"],
html.theme-light .page-content [style*="color:#aaa"],
html.theme-light .page-content [style*="color: #aaa"] {
    color: var(--text2) !important;
}
</style>"""

POLISH_JS = """<script id="kaze-chart-theme">
(function(){
    function applyChartTheme() {
        if (!window.Chart) return;
        var isDark = document.documentElement.classList.contains('theme-dark') ||
                     (document.documentElement.classList.contains('theme-auto') &&
                      window.matchMedia('(prefers-color-scheme: dark)').matches);
        var textColor = isDark ? '#94a3b8' : '#6b7280';
        var gridColor = isDark ? 'rgba(51, 65, 85, 0.4)' : 'rgba(229, 231, 235, 0.8)';
        var tooltipBg = isDark ? 'rgba(30, 41, 59, 0.98)' : 'rgba(17, 24, 39, 0.95)';

        Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = textColor;
        Chart.defaults.borderColor = gridColor;

        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.boxWidth = 8;
        Chart.defaults.plugins.legend.labels.boxHeight = 8;
        Chart.defaults.plugins.legend.labels.padding = 16;

        Chart.defaults.plugins.tooltip.backgroundColor = tooltipBg;
        Chart.defaults.plugins.tooltip.padding = 12;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.plugins.tooltip.displayColors = true;
        Chart.defaults.plugins.tooltip.boxPadding = 4;
        Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 13 };
        Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };

        Chart.defaults.scales = Chart.defaults.scales || {};
        if (Chart.defaults.scales.linear) {
            Chart.defaults.scales.linear.grid = { color: gridColor, drawBorder: false };
            Chart.defaults.scales.linear.ticks = { color: textColor, padding: 6 };
        }
        if (Chart.defaults.scales.category) {
            Chart.defaults.scales.category.grid = { display: false };
            Chart.defaults.scales.category.ticks = { color: textColor, padding: 6 };
        }
    }

    // Apply immediately if Chart is loaded
    applyChartTheme();

    // Re-apply on theme change
    new MutationObserver(function() {
        applyChartTheme();
        // Refresh existing chart instances so they pick up new colors
        try {
            if (Chart.instances) {
                Object.values(Chart.instances).forEach(function(c) {
                    try { c.update('none'); } catch(e) {}
                });
            }
        } catch(e) {}
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
})();
</script>"""

# Inject CSS before </head>
if 'kaze-polish-4d' not in html:
    if '</head>' in html:
        html = html.replace('</head>', POLISH_CSS + '\n</head>', 1)
        print("  [OK]   polish CSS injected")
    else:
        print("  [FAIL] </head> not found")
        FAILED.append("CSS injection")
else:
    print("  [SKIP] polish CSS already present")

# Inject JS before </body>
if 'kaze-chart-theme' not in html:
    if '</body>' in html:
        html = html.replace('</body>', POLISH_JS + '\n</body>', 1)
        print("  [OK]   chart theme JS injected")
    else:
        print("  [FAIL] </body> not found")
        FAILED.append("JS injection")
else:
    print("  [SKIP] chart theme JS already present")

# ── [3/4] Write ──────────────────────────────────────────────────
print("\n[3/4] Writing...")
with open(BASE, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"  [OK]   Written ({orig_len:,} -> {len(html):,} chars)")

# ── [4/4] Verify ─────────────────────────────────────────────────
print("\n[4/4] Verifying...")

try:
    Environment().parse(html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    print(f"\nRestore: copy \"{b}\" {BASE}")
    sys.exit(1)

checks = {
    'inner wrapper present': 'kz-nav-group-inner' in html,
    'grid animation CSS':    'grid-template-rows: 0fr' in html,
    'light override':        'html.theme-light body' in html,
    'chart theme JS':        'Chart.defaults.font.family' in html,
    'chevron transition':    'rotate(180deg) !important' in html,
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
    print(f"\nRestore: copy \"{b}\" {BASE}")
    sys.exit(1)

print("Polish complete.")
print("  Sidebar:       smooth 0.28s expand/collapse animation")
print("  Chevron:       eased rotation")
print("  Chart theming: global defaults (fonts, colors, tooltips)")
print("  Light mode:    surface vars forced white, --text3 darkened")
print("=" * 62)
print("""
NEXT STEPS:

1. Restart:  python app.py
2. Hard refresh /dashboard (Ctrl+F5)

3. Test:

   a) Sidebar
      - Click Money group header
      - Should expand smoothly over 0.28s (not instant)
      - Chevron rotates smoothly
      - Click again -> collapses smoothly

   b) Charts
      - Reload /dashboard
      - Chart labels use Inter font
      - Tooltips have rounded corners, dark background
      - Legend dots are small circles (not squares)
      - Grid lines are subtle

   c) Light mode
      - Toggle theme to light
      - KPI card numbers should be dark on white (readable)
      - Widget/table text should be dark
      - No invisible text anywhere

   If some text is STILL invisible on light mode, tell me:
   - The page (/dashboard, /sales, etc.)
   - The specific text that's missing
   - Screenshot if possible

4. If all good:
   git add templates/base.html kaze_phase4d1_polish.py
   git commit -m "Phase 4d-1 polish: sidebar animation + chart theme + light fixes"
   git push
""")