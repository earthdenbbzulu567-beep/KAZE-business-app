import shutil
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
path = 'templates/dashboard.html'
shutil.copy2(path, f"{path}.bak.undopl_{STAMP}")

with open(path, encoding='utf-8') as f:
    html = f.read()

# 1. Find the PL Board in the sidebar and extract it
pl_start = html.find('<div class="pl-board')
if pl_start == -1:
    print("[FAIL] PL Board not found. Already moved back?")
    exit(1)

# It was wrapped in a div with margin-top by the last script
wrapper_start = html.rfind('<div style="margin-top: 1.5rem;">', 0, pl_start)
pl_end = html.find('</div>', html.find('pl-total', pl_start)) + 6
wrapper_end = html.find('</div>', pl_end) + 6

pl_html = html[pl_start:pl_end]

# Remove the wrapper and the PL Board from the sidebar
html = html[:wrapper_start] + html[wrapper_end:]

# 2. Insert it back at the bottom, right before the <style> block
style_start = html.find('<style>', html.find('pl-board'))
# Actually, the style block is the one at the very bottom of the file
style_start = html.rfind('<style>')

html = html[:style_start] + pl_html + '\n\n' + html[style_start:]
print("  [OK]   PL Board moved back to the bottom.")

# 3. Fix the black gap via CSS
# We change .kz-dash-grid from align-items: start to stretch
html = html.replace(
    'align-items: start;',
    'align-items: stretch;'
)
# We also need to make sure the side column can stretch
html = html.replace(
    '.kz-dash-side > .kz-card:last-child { margin-bottom: 0; }',
    '.kz-dash-side > .kz-card:last-child { margin-bottom: 0; height: 100%; display: flex; flex-direction: column; }'
)
print("  [OK]   Activity feed will now stretch to match chart height.")

try:
    Environment().parse(html)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("  [OK]   dashboard.html saved.")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")

print("\nDone. Restart Flask and hard refresh.")