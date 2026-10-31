"""
kaze_phase4a_v2.py — consolidate base.html CSS. Fixed f-string bug.

Same as phase4a but the merged CSS header no longer contains
{% if user_settings %} as literal Jinja (that was breaking parse).

Verifies Jinja before writing. File is untouched on failure.

Run from the folder with app.py:
    python kaze_phase4a_v2.py
"""

import os
import re
import shutil
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
TPL = 'templates/base.html'

if not os.path.isfile(TPL):
    print(f"ERROR: {TPL} not found.")
    sys.exit(1)

with open(TPL, encoding='utf-8') as f:
    html = f.read()

orig_len = len(html)
print(f"Original {TPL}: {orig_len:,} chars")

if orig_len < 20000:
    print(f"WARNING: base.html is only {orig_len:,} chars — wrong file?")
    sys.exit(1)

# If a prior aborted run left a debug file, don't let it confuse us
if os.path.exists(TPL + '.reconstructed_debug'):
    os.remove(TPL + '.reconstructed_debug')
    print("Removed stale .reconstructed_debug")

backup_path = f"{TPL}.bak.phase4a_{STAMP}"
shutil.copy2(TPL, backup_path)
print(f"Backup: {backup_path}\n")


def is_inside_script(text, pos):
    before = text[:pos]
    so = len(re.findall(r'<script(\s[^>]*)?>', before))
    sc = len(re.findall(r'</script>', before))
    return so > sc


def count_if_depth(text):
    opens = len(re.findall(r'{%\s*if\s+', text))
    closes = len(re.findall(r'{%\s*endif\s*%}', text))
    return opens - closes


def first_selector(css):
    for line in css.split('\n'):
        s = line.strip()
        if s and not s.startswith('/*') and not s.startswith('*'):
            return s[:70]
    return '(empty)'


style_pattern = re.compile(r'<style(\s[^>]*)?>(.*?)</style>', re.DOTALL)
matches = [m for m in style_pattern.finditer(html) if not is_inside_script(html, m.start())]
print(f"[1/5] Found {len(matches)} real <style> blocks")

static_idx = []
conditional_idx = []
for i, m in enumerate(matches):
    c = m.group(2)
    is_cond = count_if_depth(html[:m.start()]) > 0
    label = 'CONDITIONAL' if is_cond else 'static'
    print(f"  Block {i+1}: {c.count(chr(10)):4d} lines [{label:11s}] {first_selector(c)}")
    (conditional_idx if is_cond else static_idx).append(i)

print(f"\n[2/5] Static: {len(static_idx)}  Conditional: {len(conditional_idx)}")

if len(static_idx) < 2:
    print("\n[SKIP] Fewer than 2 static blocks — nothing to consolidate.")
    sys.exit(0)

# Build merged CSS — note: NO literal Jinja tags in the header
parts = [
    "/* ============================================================ */",
    "/*  KAZE base.html — consolidated style block (Phase 4a)        */",
    "/*  " + str(len(static_idx)) + " static blocks merged into 1.",
    "/*  Conditional blocks remain separate and follow this block.    */",
    "/* ============================================================ */",
]

for section_num, block_idx in enumerate(static_idx):
    c = matches[block_idx].group(2)
    if not c.strip():
        continue
    parts.append("")
    parts.append("/* ------------------------------------------------------------ */")
    parts.append("/*  SECTION " + str(section_num + 1) +
                 "  (source: original block " + str(block_idx + 1) + ")")
    parts.append("/*  Starts with: " + first_selector(c))
    parts.append("/* ------------------------------------------------------------ */")
    parts.append(c.strip('\n'))

merged_css = '\n'.join(parts)

print(f"\n[3/5] Merging {len(static_idx)} blocks into one...")

# Reconstruct — descending order so positions stay valid
desc_idx = sorted(static_idx, reverse=True)
new_html = html
for pos, block_idx in enumerate(desc_idx):
    m = matches[block_idx]
    start, end = m.start(), m.end()
    if pos == len(desc_idx) - 1:
        new_html = new_html[:start] + '<style>\n' + merged_css + '\n</style>' + new_html[end:]
    else:
        new_html = new_html[:start] + new_html[end:]

new_html = re.sub(r'\n{4,}', '\n\n\n', new_html)
print(f"[4/5] Reconstructed: {len(new_html):,} chars (was {orig_len:,})")

# Verify BEFORE writing
print(f"\n[5/5] Verifying...")

try:
    Environment().parse(new_html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    print(f"\n[ABORT] File NOT modified. Backup: {backup_path}")
    sys.exit(1)

expected_pairs = 1 + len(conditional_idx)
actual_opens = new_html.count('<style')
actual_closes = new_html.count('</style>')
if actual_opens != expected_pairs or actual_closes != expected_pairs:
    print(f"  [FAIL] Expected {expected_pairs} pairs, got {actual_opens}/{actual_closes}")
    print(f"[ABORT] File NOT modified.")
    sys.exit(1)
print(f"  [OK]   Style tag count: {actual_opens} pairs")

CRITICAL_TOKENS = ['--bg:', '--red-bright:', '.sidebar', '.page-header',
                   '.btn-secondary', '.summary-card', '.stat-chip']
missing = [t for t in CRITICAL_TOKENS if t not in new_html]
if missing:
    print(f"  [FAIL] Missing critical tokens: {missing}")
    print(f"[ABORT] File NOT modified.")
    sys.exit(1)
print(f"  [OK]   All {len(CRITICAL_TOKENS)} critical tokens present")

print(f"\n[WRITE] Writing {TPL}...")
with open(TPL, 'w', encoding='utf-8') as f:
    f.write(new_html)
print(f"  [OK]   Written ({len(new_html):,} chars)")

print()
print("=" * 62)
print("Phase 4a complete.")
print(f"  Static style blocks: {len(static_idx)} -> 1")
print(f"  Conditional preserved: {len(conditional_idx)}")
print(f"  File: {orig_len:,} -> {len(new_html):,} chars")
print("=" * 62)
print("""
NEXT: Local test. This batch should produce ZERO visible change.

Open each of these and confirm it looks identical to before:

  [ ] /                        Landing page
  [ ] /dashboard               Dashboard
  [ ] /plans                   Plans
  [ ] /payments                Payments
  [ ] /sales                   Sales
  [ ] /stock                   Stock
  [ ] /customers               Customers
  [ ] /settings                Settings
  [ ] /bookkeeping             Bookkeeping
  [ ] /analytics/decisions     Analytics
  [ ] /health                  Health
  [ ] /login                   Auth card
  [ ] Dark theme
  [ ] Light theme (toggle in topbar)

If ALL identical -> commit + push.

If ANYTHING looks wrong:
  copy "templates/base.html.bak.phase4a_""" + STAMP + """" templates/base.html
  Tell me which page/element/what changed.
""")