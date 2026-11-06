"""
kaze_phase5_charts_fix.py — Fixes JS timing issue and applies chart themes correctly.
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
    'templates/base.html',
    'templates/dashboard.html',
    'templates/reports.html',
    'templates/cashbook.html',
    'templates/stock.html',
]

for path in FILES:
    if os.path.isfile(path):
        shutil.copy2(path, f"{path}.bak.phase5fix_{STAMP}")
        print(f"Backup: {path}.bak.phase5fix_{STAMP}")

# ═══════════════════════════════════════════════════════════════════
print("\n[1/4] Fixing base.html - Move Chart Defaults to Head")
# ═══════════════════════════════════════════════════════════════════

with open('templates/base.html', encoding='utf-8') as f:
    base_html = f.read()

# Remove the old script from the bottom of the body
OLD_SCRIPT_REGEX = re.compile(r'<script id="kaze-chart-globals">.*?</script>\n</body>', re.DOTALL)
base_html = OLD_SCRIPT_REGEX.sub('</body>', base_html)

# New script to inject in the head
GLOBAL_CHART_JS = """
<script id="kaze-chart-globals">
(function(){
    if (!window.Chart) return;
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.color = '#6b7280';
    Chart.defaults.borderColor = '#e5e7eb';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.boxWidth = 6;
    Chart.defaults.plugins.legend.labels.boxHeight = 6;
    Chart.defaults.plugins.legend.labels.padding = 16;
    Chart.defaults.plugins.tooltip.backgroundColor = '#1e293b';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    Chart.defaults.elements.bar.borderRadius = 4;
    Chart.defaults.elements.line.tension = 0.35;
    Chart.defaults.elements.point.radius = 3;
    Chart.defaults.scales.linear.grid.display = false;
    Chart.defaults.scales.category.grid.display = false;
})();
</script>
"""

# Inject it right after the charts_js block in the head
if '{% block charts_js %}{% endblock %}' in base_html:
    base_html = base_html.replace('{% block charts_js %}{% endblock %}', '{% block charts_js %}{% endblock %}\n' + GLOBAL_CHART_JS, 1)
    print("  [OK]   Injected chart defaults into <head>.")
else:
    print("  [FAIL] Could not find {% block charts_js %} in base.html")

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(base_html)


# ═══════════════════════════════════════════════════════════════════
print("\n[2/4] Replacing JS variables with Hex Codes")
# ═══════════════════════════════════════════════════════════════════

def replace_colors(filename):
    with open(filename, encoding='utf-8') as f:
        html = f.read()
    
    # Replace dynamic variables with static hex codes
    html = html.replace('window.KAZE_COLORS.sales', "'#1a8f3c'")
    html = html.replace('window.KAZE_COLORS.expenses', "'#1e293b'")
    html = html.replace('window.KAZE_COLORS.profit', "'#10b981'")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  [OK]   {filename} colors set to hex.")

replace_colors('templates/dashboard.html')
replace_colors('templates/reports.html')
replace_colors('templates/cashbook.html')
replace_colors('templates/stock.html')


# ═══════════════════════════════════════════════════════════════════
print("\n[3/4] Verifying Jinja Syntax")
# ═══════════════════════════════════════════════════════════════════

for filename in FILES:
    with open(filename, encoding='utf-8') as f:
        content = f.read()
    try:
        Environment().parse(content)
        print(f"  [OK]   {filename} parses cleanly")
    except Exception as exc:
        print(f"  [FAIL] {filename} Jinja error: {exc}")
        sys.exit(1)

print("\n[4/4] Done.")
print("\n" + "=" * 62)
print("Phase 5 (Charts Fix) complete.")
print("  Chart defaults moved to <head>.")
print("  Colors hardcoded to hex.")
print("=" * 62)