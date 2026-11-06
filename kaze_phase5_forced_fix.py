"""
kaze_phase5_forced_fix.py — Aggressive CSS override and dropdown replacement.
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Files to clean
LEGACY_FILES = [
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

# 1. Backups
for path in LEGACY_FILES + ['templates/base.html', 'app.py']:
    if os.path.isfile(path):
        shutil.copy2(path, f"{path}.bak.forced_{STAMP}")

# ═══════════════════════════════════════════════════════════════════
print("\n[1/3] Stripping old <style> blocks from legacy pages")
# ═══════════════════════════════════════════════════════════════════

for path in LEGACY_FILES:
    if not os.path.exists(path): continue
    with open(path, encoding='utf-8') as f:
        html = f.read()
    
    # Remove ANY <style> block that doesn't have our specific phase markers
    # This forces the page to rely only on base.html
    old_style_regex = re.compile(r'<style(?![^>]*kaze-)[^>]*>.*?</style>', re.DOTALL)
    new_html, count = old_style_regex.subn('', html)
    
    if count > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print(f"  [OK]   Stripped {count} old style block(s) from {os.path.basename(path)}")
    else:
        print(f"  [SKIP] No old styles found in {os.path.basename(path)}")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/3] Forcing Dropdown & Global CSS in base.html")
# ═══════════════════════════════════════════════════════════════════

with open('templates/base.html', encoding='utf-8') as f:
    base_html = f.read()

# Aggressive Dropdown Regex
dropdown_regex = re.compile(r'<div class="dropdown-content">.*?</div>', re.DOTALL)
NEW_DROPDOWN = """<div class="dropdown-content">
                <a href="{{ url_for('team') }}">👥 Team</a>
                <a href="{{ url_for('activity') }}">🕓 Login Activity</a>
                <a href="{{ url_for('backup_export') }}">⬇️ Backup</a>
                <hr style="margin: 4px 0; border: none; border-top: 1px solid var(--border);">
                <a href="#" onclick="openModal('tutorialModal'); return false;">❓ Tutorial</a>
                <a href="{{ url_for('settings') }}">⚙️ Settings</a>
                <a href="{{ url_for('legal_licence') }}">📜 Licence</a>
                <a href="{{ url_for('legal_terms') }}">📜 Terms</a>
                <hr style="margin: 4px 0; border: none; border-top: 1px solid var(--border);">
                <a href="{{ url_for('logout') }}" style="color: #e74c3c; font-weight: 600;">🚪 Logout</a>
            </div>"""
base_html, count = dropdown_regex.subn(NEW_DROPDOWN, base_html, count=1)
print(f"  [OK]   Replaced dropdown content ({count} matches)")

# Master Override CSS for Supreme and Legacy Tables
MASTER_CSS = """
<style id="kaze-master-override">
/* FORCE Supreme tiles to look good */
.supreme-grid { display: grid !important; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)) !important; gap: 0.9rem !important; margin: 1rem 0 2rem !important; }
.supreme-tile { background: var(--kz-surface, var(--surface)) !important; border: 1px solid var(--kz-border, var(--border)) !important; border-radius: var(--kz-radius, 12px) !important; padding: 1.25rem 1.1rem !important; text-decoration: none !important; color: inherit !important; box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05)) !important; display: flex !important; flex-direction: column !important; gap: 0.35rem !important; }
.supreme-tile:hover { transform: translateY(-2px) !important; border-color: var(--kz-brand) !important; }
.tile-label { font-size: 0.72rem !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; color: var(--kz-text-muted, var(--text3)) !important; font-weight: 700 !important; }
.tile-value { font-size: 1.9rem !important; font-family: var(--mono) !important; font-weight: 800 !important; line-height: 1.1 !important; margin: 0.2rem 0 !important; }
.tile-sub { font-size: 0.82rem !important; color: var(--kz-text-muted, var(--text2)) !important; }

/* FORCE all tables to scroll and align */
.page-content .table-wrapper { overflow-x: auto !important; border: 1px solid var(--kz-border, var(--border)) !important; border-radius: var(--kz-radius, 12px) !important; background: var(--kz-surface, var(--surface)) !important; }
.page-content table { width: 100% !important; min-width: 600px !important; border-collapse: collapse !important; }
.page-content th { background: var(--kz-bg, var(--bg3)) !important; text-transform: uppercase !important; font-size: 0.72rem !important; letter-spacing: 0.05em !important; color: var(--kz-text-muted, var(--text3)) !important; font-weight: 600 !important; padding: 12px 16px !important; }
.page-content td { padding: 12px 16px !important; white-space: nowrap !important; font-variant-numeric: tabular-nums !important; }

/* FORCE legacy widgets to look like kz-cards */
.page-content .widget { background: var(--kz-surface, var(--surface)) !important; border: 1px solid var(--kz-border, var(--border)) !important; border-radius: var(--kz-radius, 12px) !important; padding: 1.25rem 1.4rem !important; box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05)) !important; margin-bottom: 1.5rem !important; }
</style>
"""

if 'kaze-master-override' not in base_html:
    # Inject right before </head>
    base_html = base_html.replace('</head>', MASTER_CSS + '\n</head>', 1)
    print("  [OK]   Injected Master CSS Override into base.html")

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(base_html)

# ═══════════════════════════════════════════════════════════════════
print("\n[3/3] Verifying app.py")
# ═══════════════════════════════════════════════════════════════════

r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")