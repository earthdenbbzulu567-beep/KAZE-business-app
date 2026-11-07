import shutil
import glob
from jinja2 import Environment

# 1. Find the most recent backup (from just before we moved the PL board)
backups = sorted(glob.glob('templates/dashboard.html.bak.plfix_*'))
if not backups:
    print("[FAIL] Could not find the plfix backup. Aborting.")
    exit(1)

latest_backup = backups[-1]
shutil.copy2(latest_backup, 'templates/dashboard.html')
print(f"  [OK]   Restored dashboard.html from {latest_backup}")

# 2. Read the restored file
with open('templates/dashboard.html', encoding='utf-8') as f:
    html = f.read()

# 3. Apply the CSS-only fix for the black gap
# Change grid alignment from 'start' to 'stretch'
if 'align-items: start;' in html:
    html = html.replace('align-items: start;', 'align-items: stretch;')
    print("  [OK]   Grid alignment changed to stretch.")
else:
    print("  [WARN] 'align-items: start;' not found in CSS.")

# Make the Activity feed card fill the height
old_card_rule = '.kz-dash-side > .kz-card:last-child { margin-bottom: 0; }'
new_card_rule = '.kz-dash-side > .kz-card:last-child { margin-bottom: 0; height: 100%; display: flex; flex-direction: column; }'

if old_card_rule in html:
    html = html.replace(old_card_rule, new_card_rule)
    print("  [OK]   Activity feed card set to fill height.")
else:
    print("  [WARN] Activity feed card CSS rule not found.")

# 4. Verify and save
try:
    Environment().parse(html)
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("  [OK]   dashboard.html saved successfully.")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")

print("\nDone. Restart Flask and hard refresh.")