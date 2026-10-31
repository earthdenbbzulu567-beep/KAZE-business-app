"""
kaze_phase4a.py — consolidate base.html CSS from multiple blocks into one.

Before: base.html has 8+ <style> blocks scattered through <head>. Some
contain overriding rules for the same selectors. Editing any of them
requires knowing the whole file's cascade.

After: all static <style> blocks merged into a single block at the top
of <head>. Conditional blocks (inside {% if user_settings %}) stay
separate — they must, since they depend on Jinja variables.

Visual output is identical. This is a refactor, not a redesign.

Safety: creates backup, verifies Jinja parse + style tag counts, restores
if verification fails.

Run from the folder with app.py:
    python kaze_phase4a.py
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
    print(f"WARNING: base.html is only {orig_len:,} chars.")
    print("         The expected base.html is 90,000+ chars.")
    print("         This looks wrong. Check you're in the right folder.")
    sys.exit(1)

backup_path = f"{TPL}.bak.phase4a_{STAMP}"
shutil.copy2(TPL, backup_path)
print(f"Backup: {backup_path}\n")


def count_if_depth(text):
    """Count unmatched {% if %} tags (opens minus closes)."""
    opens = len(re.findall(r'{%\s*if\s+', text))
    closes = len(re.findall(r'{%\s*endif\s*%}', text))
    return opens - closes


def is_inside_script(text, pos):
    """True if `pos` in `text` falls inside a <script>...</script> block."""
    before = text[:pos]
    so = len(re.findall(r'<script(\s[^>]*)?>', before))
    sc = len(re.findall(r'</script>', before))
    return so > sc


def first_selector(css):
    """First meaningful line — used as a hint in merged section headers."""
    for line in css.split('\n'):
        s = line.strip()
        if s and not s.startswith('/*') and not s.startswith('*'):
            return s[:70]
    return '(empty)'


# ── Step 1: Find all <style> blocks ────────────────────────────────
print(f"[1/5] Scanning for <style> blocks...")
style_pattern = re.compile(r'<style(\s[^>]*)?>(.*?)</style>', re.DOTALL)
matches = []

for m in style_pattern.finditer(html):
    if is_inside_script(html, m.start()):
        # Skip — this <style> is text inside a JS string, not a real block
        continue
    matches.append(m)

print(f"  Found {len(matches)} real <style> blocks\n")

# ── Step 2: Classify static vs conditional ─────────────────────────
print(f"[2/5] Classifying blocks...")
static_idx = []
conditional_idx = []

for i, m in enumerate(matches):
    attrs = (m.group(1) or '').strip()
    content = m.group(2)
    lines = content.count('\n')
    first = first_selector(content)
    depth = count_if_depth(html[:m.start()])

    is_cond = depth > 0
    label = 'CONDITIONAL' if is_cond else 'static'
    print(f"  Block {i+1}: {lines:4d} lines  [{label:11s}]  starts: {first}")
    if attrs:
        print(f"                 attrs: <style {attrs}>")

    if is_cond:
        conditional_idx.append(i)
    else:
        static_idx.append(i)

print(f"\n  Static:      {len(static_idx)} blocks")
print(f"  Conditional: {len(conditional_idx)} blocks")

if len(static_idx) < 2:
    print("\n[SKIP] Fewer than 2 static blocks — nothing to consolidate.")
    sys.exit(0)

# ── Step 3: Build merged CSS ───────────────────────────────────────
print(f"\n[3/5] Merging {len(static_idx)} static blocks...")

parts = []
parts.append("/* ================================================================ */")
parts.append(f"/*  KAZE base.html — consolidated style block (Phase 4a)           */")
parts.append(f"/*  {len(static_idx)} static blocks merged into 1. Cascade preserved.          */")
parts.append(f"/*  Conditional blocks inside {{% if user_settings %}} stay separate.    */")
parts.append("/* ================================================================ */")

for section_num, block_idx in enumerate(static_idx):
    m = matches[block_idx]
    content = m.group(2)
    if not content.strip():
        continue
    parts.append("")
    parts.append("/* ---------------------------------------------------------------- */")
    parts.append(f"/*  SECTION {section_num+1}  (source: original block {block_idx+1})")
    parts.append(f"/*  Starts with: {first_selector(content)}")
    parts.append("/* ---------------------------------------------------------------- */")
    parts.append(content.strip('\n'))

merged_css = '\n'.join(parts)

# ── Step 4: Reconstruct HTML ───────────────────────────────────────
print(f"\n[4/5] Reconstructing base.html...")

# Descending order so removing later blocks doesn't invalidate earlier positions
desc_idx = sorted(static_idx, reverse=True)

new_html = html
for pos, block_idx in enumerate(desc_idx):
    m = matches[block_idx]
    start, end = m.start(), m.end()
    if pos == len(desc_idx) - 1:
        # This is the first static block in original order — replace with merged
        new_html = new_html[:start] + f'<style>\n{merged_css}\n</style>' + new_html[end:]
    else:
        # Remove this block entirely
        new_html = new_html[:start] + new_html[end:]

# Collapse excessive blank lines
new_html = re.sub(r'\n{4,}', '\n\n\n', new_html)

new_len = len(new_html)
print(f"  Reconstructed: {new_len:,} chars (was {orig_len:,})")
print(f"  Style tags: {new_html.count('<style')} open, {new_html.count('</style>')} close")

# ── Step 5: Verify ────────────────────────────────────────────────
print(f"\n[5/5] Verifying...")

# Jinja parse check
try:
    Environment().parse(new_html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    print(f"\n[ABORT] base.html NOT modified. Restore:")
    print(f"        copy \"{backup_path}\" {TPL}")
    sys.exit(1)

# Style tag count check
expected_pairs = 1 + len(conditional_idx)
actual_opens = new_html.count('<style')
actual_closes = new_html.count('</style>')
if actual_opens != expected_pairs or actual_closes != expected_pairs:
    print(f"  [FAIL] Expected {expected_pairs} <style> pairs, got {actual_opens}/{actual_closes}")
    print(f"[ABORT] base.html NOT modified.")
    sys.exit(1)
print(f"  [OK]   Style tag count: {actual_opens} open, {actual_closes} close ({expected_pairs} pairs)")

# Critical token check — if any of these disappeared, merge is broken
CRITICAL_TOKENS = [
    '--bg:',
    '--red-bright:',
    '.sidebar',
    '.page-header',
    '.btn-secondary',
    '.summary-card',
    '.stat-chip',
]
missing = [t for t in CRITICAL_TOKENS if t not in new_html]
if missing:
    print(f"  [FAIL] Missing critical CSS tokens: {missing}")
    print(f"[ABORT] base.html NOT modified.")
    sys.exit(1)
print(f"  [OK]   All {len(CRITICAL_TOKENS)} critical tokens still present")

# ── Write ──────────────────────────────────────────────────────────
print(f"\n[WRITE] Writing {TPL}...")
with open(TPL, 'w', encoding='utf-8') as f:
    f.write(new_html)
print(f"  [OK]   Written ({new_len:,} chars)")

print()
print("=" * 62)
print("Phase 4a complete.")
print(f"  Static style blocks: {len(static_idx)} -> 1")
print(f"  Conditional blocks preserved: {len(conditional_idx)}")
print(f"  File: {orig_len:,} -> {new_len:,} chars")
print("=" * 62)
print("""
NEXT STEPS:

1. LOCAL TEST — run:  python app.py

   CRITICAL: this batch should produce ZERO visible change. Same CSS,
   same cascade, same everything. Your job is to verify that.

   Checklist — open each page, confirm it looks the same as before:

     [ ] /                       Landing page (hero, cards)
     [ ] /dashboard              Dashboard (hero, tabs, stats, P/L)
     [ ] /plans                  Plans (pricing cards)
     [ ] /payments               Payments (form, log)
     [ ] /sales                  Sales (form, table, chart)
     [ ] /stock                  Stock (form, table, chart)
     [ ] /customers              Customers (form, table)
     [ ] /settings               Settings (mode grid, forms)
     [ ] /bookkeeping            Bookkeeping (doc cards)
     [ ] /analytics/decisions    Analytics (tabs, cards)
     [ ] /health                 Health (score, components)
     [ ] /login                  Auth card

   Specifically check:
     - Sidebar unchanged (nav, brand, plan badge)
     - Topbar unchanged (theme toggle, sound, clock, bell, user menu)
     - Buttons unchanged (rounded, gradient, hover)
     - Tables unchanged (headers, row hover, borders)
     - Forms unchanged (inputs, labels, focus glow)
     - Dark theme still dark
     - Light theme still correct (click theme toggle in topbar)
     - Cards still have rounded corners and hover lift

2. If ANYTHING looks wrong:
   copy "templates/base.html.bak.phase4a_""" + STAMP + """ " templates/base.html
   Then tell me: which page, which element, what changed.

   DON'T panic — the backup is one copy command away.

3. If everything looks identical:
   git add templates/base.html kaze_phase4a.py
   git commit -m "Phase 4a: consolidate base.html CSS blocks (no visual change)"
   git push

4. Deploy to production, spot-check 3-4 pages on prod, then:
   rm templates/base.html.bak.phase4a_*

AFTER 4a CONFIRMS: Phase 4b — sidebar/nav restructure. That's the first
visible change in Phase 4.
""")