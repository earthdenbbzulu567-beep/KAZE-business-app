"""
kaze_phase4a_diagnose.py — save the reconstructed html to a temp file
so we can see the EXACT line where Jinja breaks.

Does NOT modify templates/base.html. Writes to a temp file for inspection.
"""

import os
import re
from jinja2 import Environment, TemplateSyntaxError

TPL = 'templates/base.html'
OUT = 'templates/base.html.reconstructed_debug'

if not os.path.isfile(TPL):
    print(f"ERROR: {TPL} not found.")
    raise SystemExit(1)

with open(TPL, encoding='utf-8') as f:
    html = f.read()


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

static_idx = []
conditional_idx = []
for i, m in enumerate(matches):
    if count_if_depth(html[:m.start()]) > 0:
        conditional_idx.append(i)
    else:
        static_idx.append(i)

print(f"Static: {len(static_idx)}, Conditional: {len(conditional_idx)}")

parts = [
    "/* ============================================================ */",
    f"/*  KAZE base.html — consolidated (Phase 4a)                    */",
    f"/*  {len(static_idx)} static blocks merged into 1.                         */",
    "/* ============================================================ */",
]
for n, bi in enumerate(static_idx):
    c = matches[bi].group(2)
    if not c.strip():
        continue
    parts.append("")
    parts.append("/* ------------------------------------------------------------ */")
    parts.append(f"/*  SECTION {n+1}  (source: original block {bi+1})")
    parts.append(f"/*  Starts with: {first_selector(c)}")
    parts.append("/* ------------------------------------------------------------ */")
    parts.append(c.strip('\n'))
merged_css = '\n'.join(parts)

desc_idx = sorted(static_idx, reverse=True)
new_html = html
for pos, bi in enumerate(desc_idx):
    m = matches[bi]
    start, end = m.start(), m.end()
    if pos == len(desc_idx) - 1:
        new_html = new_html[:start] + f'<style>\n{merged_css}\n</style>' + new_html[end:]
    else:
        new_html = new_html[:start] + new_html[end:]

new_html = re.sub(r'\n{4,}', '\n\n\n', new_html)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(new_html)
print(f"\nReconstructed saved: {OUT}")
print(f"Length: {len(new_html):,} chars (original was {len(html):,})\n")

try:
    Environment().parse(new_html)
    print("[OK] Jinja parses cleanly (unexpected — script failed earlier)")
except TemplateSyntaxError as exc:
    print(f"[FAIL] Jinja error: line {exc.lineno}: {exc.message}")
    lines = new_html.split('\n')
    lo = max(0, exc.lineno - 8)
    hi = min(len(lines), exc.lineno + 8)
    print(f"\nContext (lines {lo+1}-{hi}):")
    print("-" * 70)
    for i in range(lo, hi):
        marker = '>>>' if i + 1 == exc.lineno else '   '
        print(f"{marker} {i+1:5d}| {lines[i][:120]}")
    print("-" * 70)