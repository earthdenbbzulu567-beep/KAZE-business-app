"""
kaze_batch2f_fix.py — fix the false-positive verification in batch 2f.

Problem: batch script used exec("NEW_ROUTES = '''...'''") which re-parses
escape sequences in the string, turning '\\n' into a real newline. This
made the verification fail even though the batch code is correct.

Fix: write the NEW_ROUTES string directly to a temp file (no re-exec).
That's exactly what the batch writes to app.py anyway.

app.py is untouched — the batch aborted at [VERIFY] before writing.
"""

import os
import shutil
import subprocess
import sys

SCRIPT = 'kaze_batch2f_workflow.py'

if not os.path.isfile(SCRIPT):
    print(f"ERROR: {SCRIPT} not found.")
    sys.exit(1)

shutil.copy2(SCRIPT, SCRIPT + '.bak')
print(f"Backup: {SCRIPT}.bak")

with open(SCRIPT, encoding='utf-8') as f:
    content = f.read()

OLD_BLOCK = '''print("\\n[VERIFY] Compiling NEW_ROUTES block before writing to app.py...")
ns = {}
try:
    exec("NEW_ROUTES = \'\'\'" + NEW_ROUTES + "\'\'\'", ns)
    evaluated = ns['NEW_ROUTES']
except Exception as exc:
    print(f"  [FAIL] Could not evaluate NEW_ROUTES: {exc}")
    print(f"\\n[ABORT] app.py untouched. Restore: copy \\"{backup_path}\\" {APP}")
    sys.exit(1)

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
    tmp.write(evaluated)
    tmp_path = tmp.name
rc = subprocess.run([sys.executable, '-m', 'py_compile', tmp_path], capture_output=True, text=True)
os.unlink(tmp_path)
if rc.returncode != 0:
    print("  [FAIL] NEW_ROUTES as evaluated does not compile:")
    print(rc.stderr)
    print(f"\\n[ABORT] app.py untouched. Restore: copy \\"{backup_path}\\" {APP}")
    sys.exit(1)
print(f"  [OK]   NEW_ROUTES compiles when evaluated ({len(evaluated):,} chars)")
print("  [OK]   No syntax errors in the code that will be inserted")'''

NEW_BLOCK = '''print("\\n[VERIFY] Compiling NEW_ROUTES block before writing to app.py...")
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
    tmp.write(NEW_ROUTES)
    tmp_path = tmp.name
rc = subprocess.run([sys.executable, '-m', 'py_compile', tmp_path], capture_output=True, text=True)
os.unlink(tmp_path)
if rc.returncode != 0:
    print("  [FAIL] NEW_ROUTES does not compile:")
    print(rc.stderr)
    print(f"\\n[ABORT] app.py untouched. Restore: copy \\"{backup_path}\\" {APP}")
    sys.exit(1)
print(f"  [OK]   NEW_ROUTES compiles ({len(NEW_ROUTES):,} chars)")
print("  [OK]   No syntax errors in the code that will be inserted")'''

if OLD_BLOCK not in content:
    print("[FAIL] Could not find the buggy verification block.")
    print("       The script may already be patched, or the source differs.")
    print("       Check with: Select-String -Path kaze_batch2f_workflow.py -Pattern 'exec.*NEW_ROUTES'")
    sys.exit(1)

content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)

with open(SCRIPT, 'w', encoding='utf-8') as f:
    f.write(content)
print("[OK] Patched verification block")

# Verify batch script itself compiles
r = subprocess.run([sys.executable, '-m', 'py_compile', SCRIPT],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("[FAIL] Batch script still has syntax errors:")
    print(r.stderr)
    print(f"Restore: copy \"{SCRIPT}.bak\" {SCRIPT}")
    sys.exit(1)
print("[OK] Batch script compiles cleanly")

# Confirm no more exec of NEW_ROUTES
with open(SCRIPT, encoding='utf-8') as f:
    verify = f.read()
if 'exec("NEW_ROUTES' in verify:
    print("[FAIL] exec line still present — patch did not take")
    sys.exit(1)
print("[OK] No more double-parse exec in verification")

print()
print("=" * 62)
print("Fix applied. Ready to re-run the batch.")
print("=" * 62)
print()
print("Next:  python kaze_batch2f_workflow.py")
print()
print("Expected: [VERIFY] passes, batch proceeds through [7/7] Summary.")
print("  Removed from disabled:  9/9")
print("  New routes added:        11 (2 pages + 9 redirects)")
print("  New templates:           2")
print("  @app.route: 314 -> 325")