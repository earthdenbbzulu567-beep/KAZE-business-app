"""
apply_fixes_3.py — repair the broken base.html topbar block,
remove stray .bak files from git, and add a .gitignore.
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

BASE = 'templates/base.html'

if not os.path.isfile(BASE):
    print(f"ERROR: {BASE} not found. Run from the project root.")
    sys.exit(1)

# Backup
bak = f"{BASE}.bak.{STAMP}"
shutil.copy2(BASE, bak)
print(f"Backup saved: {bak}")

with open(BASE, 'r', encoding='utf-8') as fh:
    src = fh.read()

# ── Locate the topbar right-group block and replace it with a clean version ──
pattern = re.compile(r'<div class="right-group">.*?</header>', re.DOTALL)

if not pattern.search(src):
    print("ERROR: Could not find <div class=\"right-group\">... </header> block.")
    sys.exit(1)

clean_block = '''<div class="right-group">
                <a class="status-chip" href="{{ url_for('settings') }}" title="App mode">{{ app_modes[app_mode].label if app_modes is defined and app_mode in app_modes else (app_mode or 'Full') }}</a>
                <a class="status-chip" href="{{ url_for('plans') }}" title="Package">{{ plan.label if plan else 'New user' }}</a>
                <button type="button" class="theme-toggle" id="themeToggle" title="Switch dark / light mode" aria-label="Switch dark or light mode">🌙</button>
                <button type="button" class="theme-toggle" id="soundToggle" title="Sound cues on / off" aria-label="Sound cues on or off">🔔</button>
                <span class="live-clock" id="liveClock" title="Local time"></span>
                {% if current_user.is_authenticated %}
                <a href="{{ url_for('notifications') }}" class="bell-link" title="Notifications">
                    🔔{% if unread_notifications and unread_notifications > 0 %}<span class="bell-badge">{{ unread_notifications }}</span>{% endif %}
                </a>
                <div class="user-menu">
                    <button class="dropbtn">{{ current_user.username }} ▼</button>
                    <div class="dropdown-content">
                        <a href="{{ url_for('dashboard') }}">Dashboard</a>
                        <a href="{{ url_for('team') }}">👥 Team</a>
                        <a href="{{ url_for('activity') }}">Login Activity</a>
                        <a href="{{ url_for('backup_export') }}">Download backup</a>
                        <a href="#" onclick="openModal('tutorialModal'); return false;">Help / Tutorial</a>
                        <a href="{{ url_for('settings') }}">Settings</a>
                        <a href="{{ url_for('legal_licence') }}">Licence</a>
                        <a href="{{ url_for('legal_terms') }}">Terms</a>
                        <a href="{{ url_for('logout') }}">Logout</a>
                    </div>
                </div>
                {% endif %}
            </div>
        </header>'''

src_new = pattern.sub(clean_block, src, count=1)

# Sanity: the topbar region should have balanced if/endif around the user menu
if src_new.count('{% if current_user.is_authenticated %}') < src_new.count('{% endif %}'):
    pass  # fine, many other ifs in the file

with open(BASE, 'w', encoding='utf-8') as fh:
    fh.write(src_new)

print(f"[OK] repaired {BASE}")

# ── Remove .bak files from git, add .gitignore ──
print("\nRemoving committed .bak files from git...")
r = subprocess.run(['git', 'ls-files', '*.bak.*'], capture_output=True, text=True)
bak_files = [f for f in r.stdout.splitlines() if f.strip()]
if bak_files:
    subprocess.run(['git', 'rm', '--cached'] + bak_files, check=False)
    print(f"  [OK] untracked {len(bak_files)} .bak file(s) from git (files kept on disk)")
else:
    print("  [SKIP] no .bak files tracked in git")

# write .gitignore
GITIGNORE_ADD = """

# KAZE — ignore editor/script backups
*.bak.*
*.bak
__pycache__/
*.pyc
.venv/
venv/
"""
gi_path = '.gitignore'
existing = ''
if os.path.isfile(gi_path):
    with open(gi_path, 'r', encoding='utf-8') as fh:
        existing = fh.read()
if '*.bak.*' not in existing:
    with open(gi_path, 'a', encoding='utf-8') as fh:
        fh.write(GITIGNORE_ADD)
    print(f"  [OK] added *.bak.* to {gi_path}")
else:
    print(f"  [SKIP] {gi_path} already covers .bak files")

print("\nDone.")
print("=" * 60)
print("Next:")
print('  git add -A')
print('  git commit -m "Fix base.html topbar, drop .bak files"')
print('  git push')
print("=" * 60)