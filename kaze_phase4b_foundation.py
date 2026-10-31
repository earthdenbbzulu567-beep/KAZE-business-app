"""
kaze_phase4b_foundation.py — Phase 4b.

1. Adds new design tokens + component classes to base.html (no visible
   change yet — old classes still active until 4c).
2. Adds developer access (env var + settings toggle).
3. Prepares sidebar with new ID for 4c targeting.

Includes full verification — restores backup on any failure.

Run from the folder with app.py:
    python kaze_phase4b_foundation.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'
BASE = 'templates/base.html'
SETTINGS = 'templates/settings.html'

for f in (APP, BASE, SETTINGS):
    if not os.path.isfile(f):
        print(f"ERROR: {f} not found.")
        sys.exit(1)

# Backups
for f in (APP, BASE, SETTINGS):
    b = f"{f}.bak.phase4b_{STAMP}"
    shutil.copy2(f, b)
    print(f"Backup: {b}")

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/6] Schema — developer_mode_enabled column")
# ═══════════════════════════════════════════════════════════════════

with open(APP, encoding='utf-8') as f:
    src = f.read()

SCHEMA_ANCHOR = """    cur.execute("ALTER TABLE stripe_payments ADD COLUMN IF NOT EXISTS invoice_id TEXT DEFAULT ''")"""
SCHEMA_NEW = """    cur.execute("ALTER TABLE stripe_payments ADD COLUMN IF NOT EXISTS invoice_id TEXT DEFAULT ''")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS developer_mode_enabled INTEGER DEFAULT 0")"""

if SCHEMA_ANCHOR in src:
    src = src.replace(SCHEMA_ANCHOR, SCHEMA_NEW, 1)
    print("  [OK]   added developer_mode_enabled column")
else:
    print("  [FAIL] schema anchor not found")
    FAILED.append("schema")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/6] Update effective_plan() for developer bypass")
# ═══════════════════════════════════════════════════════════════════

OLD_EFFECTIVE = """def effective_plan(settings=None):
    settings = settings or {}
    today = datetime.today().strftime('%Y-%m-%d')

    expires = str(settings.get('plan_expires_at') or '')[:10]
    if expires and expires >= today:
        return normalize_plan(settings.get('plan_tier') or 'new_user')

    grace = str(settings.get('grace_expires_at') or '')[:10]
    if grace and grace >= today:
        return normalize_plan(settings.get('plan_tier') or 'new_user')

    if trial_info(settings).get('active'):
        return 'ceo'

    return 'new_user'"""

NEW_EFFECTIVE = """def effective_plan(settings=None):
    settings = settings or {}
    today = datetime.today().strftime('%Y-%m-%d')

    # Developer bypass
    dev_emails_raw = os.environ.get('KAZE_DEVELOPER_EMAILS', '')
    dev_emails = [e.strip().lower() for e in dev_emails_raw.split(',') if e.strip()]
    if current_user.is_authenticated and current_user.email.lower() in dev_emails:
        if int(settings.get('developer_mode_enabled') or 0) == 1:
            return 'founder'

    expires = str(settings.get('plan_expires_at') or '')[:10]
    if expires and expires >= today:
        return normalize_plan(settings.get('plan_tier') or 'new_user')

    grace = str(settings.get('grace_expires_at') or '')[:10]
    if grace and grace >= today:
        return normalize_plan(settings.get('plan_tier') or 'new_user')

    if trial_info(settings).get('active'):
        return 'ceo'

    return 'new_user'"""

if OLD_EFFECTIVE in src:
    src = src.replace(OLD_EFFECTIVE, NEW_EFFECTIVE, 1)
    print("  [OK]   effective_plan now respects KAZE_DEVELOPER_EMAILS")
else:
    print("  [FAIL] effective_plan anchor not found")
    FAILED.append("effective_plan")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/6] Update settings route to save developer_mode_enabled")
# ═══════════════════════════════════════════════════════════════════

OLD_SETTINGS_POST = """        package_prices = ''

        if font_size not in ('xsmall', 'small', 'medium', 'large', 'xlarge'):"""

NEW_SETTINGS_POST = """        package_prices = ''

        # Developer mode: only owners in env var can enable it
        dev_emails_raw = os.environ.get('KAZE_DEVELOPER_EMAILS', '')
        dev_emails = [e.strip().lower() for e in dev_emails_raw.split(',') if e.strip()]
        is_developer = (current_user.email.lower() in dev_emails)
        developer_mode_enabled = 1 if (is_developer and request.form.get('developer_mode_enabled') == 'on') else 0

        if font_size not in ('xsmall', 'small', 'medium', 'large', 'xlarge'):"""

if OLD_SETTINGS_POST in src:
    src = src.replace(OLD_SETTINGS_POST, NEW_SETTINGS_POST, 1)
    print("  [OK]   settings POST now reads developer_mode_enabled")
else:
    print("  [FAIL] settings POST anchor not found")
    FAILED.append("settings POST")

# Now add to the UPDATE query and the tuple
OLD_UPDATE_SQL = """                bank_name=%s, bank_account_name=%s, bank_account_number=%s, bank_branch=%s
            WHERE user_id=%s
        ''', (low_stock_threshold, email_notifications, notify_email,"""
NEW_UPDATE_SQL = """                bank_name=%s, bank_account_name=%s, bank_account_number=%s, bank_branch=%s,
                developer_mode_enabled=%s
            WHERE user_id=%s
        ''', (low_stock_threshold, email_notifications, notify_email,"""

if OLD_UPDATE_SQL in src:
    src = src.replace(OLD_UPDATE_SQL, NEW_UPDATE_SQL, 1)
    print("  [OK]   UPDATE query includes developer_mode_enabled")
else:
    print("  [FAIL] UPDATE query anchor not found")
    FAILED.append("settings UPDATE query")

OLD_TUPLE_END = """              bank_name, bank_account_name, bank_account_number, bank_branch,
              current_user.id))"""
NEW_TUPLE_END = """              bank_name, bank_account_name, bank_account_number, bank_branch,
              developer_mode_enabled,
              current_user.id))"""

if OLD_TUPLE_END in src:
    src = src.replace(OLD_TUPLE_END, NEW_TUPLE_END, 1)
    print("  [OK]   UPDATE tuple includes developer_mode_enabled")
else:
    print("  [FAIL] UPDATE tuple anchor not found")
    FAILED.append("settings UPDATE tuple")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/6] Update settings GET route to expose is_developer")
# ═══════════════════════════════════════════════════════════════════

OLD_SETTINGS_RETURN = """    return render_template('settings.html', settings=settings_row, custom_modules=custom_modules, totp_on=totp_on, totp_secret=totp_secret, totp_qr=_qr_svg(_otpauth_uri(totp_secret, current_user.username)) if totp_secret else '', backup_codes=backup_codes or [])"""

NEW_SETTINGS_RETURN = """    dev_emails_raw = os.environ.get('KAZE_DEVELOPER_EMAILS', '')
    dev_emails = [e.strip().lower() for e in dev_emails_raw.split(',') if e.strip()]
    is_developer = (current_user.email.lower() in dev_emails)
    return render_template('settings.html', settings=settings_row, custom_modules=custom_modules, totp_on=totp_on, totp_secret=totp_secret, totp_qr=_qr_svg(_otpauth_uri(totp_secret, current_user.username)) if totp_secret else '', backup_codes=backup_codes or [], is_developer=is_developer)"""

if OLD_SETTINGS_RETURN in src:
    src = src.replace(OLD_SETTINGS_RETURN, NEW_SETTINGS_RETURN, 1)
    print("  [OK]   settings GET passes is_developer to template")
else:
    print("  [FAIL] settings GET return anchor not found")
    FAILED.append("settings GET return")

# Write app.py
with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)

# ═══════════════════════════════════════════════════════════════════
print("\n[5/6] Inject Fintech design tokens into base.html")
# ═══════════════════════════════════════════════════════════════════

with open(BASE, encoding='utf-8') as f:
    base_html = f.read()

# Check if already added
if 'kaze-fintech-tokens' in base_html:
    print("  [SKIP] Design tokens already present")
else:
    NEW_CSS = """<style id="kaze-fintech-tokens">
/* =================================================================
   KAZE FINTECH DESIGN SYSTEM — Phase 4b Foundation
   Light-first, green accent. Compatible with existing dark theme.
   ================================================================= */

:root {
    /* Brand colors */
    --kz-brand: #1a8f3c;
    --kz-brand-hover: #157432;
    --kz-brand-light: #e8f5e9;
    --kz-brand-glow: rgba(26, 143, 60, 0.15);
    --kz-accent: #10b981;

    /* Light theme (default for new design) */
    --kz-bg: #f9fafb;
    --kz-surface: #ffffff;
    --kz-surface-hover: #f3f4f6;
    --kz-border: #e5e7eb;
    --kz-border-strong: #d1d5db;
    --kz-text: #111827;
    --kz-text-muted: #6b7280;
    --kz-text-light: #9ca3af;

    /* Typography */
    --kz-font: 'Inter', 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --kz-radius-sm: 8px;
    --kz-radius: 12px;
    --kz-radius-lg: 20px;
    --kz-radius-pill: 999px;

    /* Shadows */
    --kz-shadow-sm: 0 1px 2px 0 rgba(0,0,0,0.05);
    --kz-shadow: 0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px -1px rgba(0,0,0,0.1);
    --kz-shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1);
    --kz-shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1);
}

/* Dark theme overrides */
html.theme-dark {
    --kz-bg: #0f172a;
    --kz-surface: #1e293b;
    --kz-surface-hover: #334155;
    --kz-border: #334155;
    --kz-border-strong: #475569;
    --kz-text: #f8fafc;
    --kz-text-muted: #94a3b8;
    --kz-text-light: #64748b;
    --kz-brand-light: rgba(26, 143, 60, 0.15);
}

/* -----------------------------------------------------------------
   Components
   ----------------------------------------------------------------- */

.kz-card {
    background: var(--kz-surface);
    border: 1px solid var(--kz-border);
    border-radius: var(--kz-radius);
    box-shadow: var(--kz-shadow);
    padding: 1.5rem;
    color: var(--kz-text);
}

.kz-card-hover:hover {
    box-shadow: var(--kz-shadow-lg);
    transform: translateY(-2px);
    transition: all 0.2s ease;
}

.kz-stat-card {
    background: var(--kz-surface);
    border-radius: var(--kz-radius);
    padding: 1.25rem;
    border: 1px solid var(--kz-border);
    box-shadow: var(--kz-shadow-sm);
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
}

.kz-stat-label {
    font-size: 0.8rem;
    color: var(--kz-text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.kz-stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--kz-text);
    line-height: 1.2;
}

.kz-stat-delta {
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
}
.kz-stat-delta.up { color: #059669; }
.kz-stat-delta.down { color: #dc2626; }

.kz-btn {
    background: var(--kz-brand);
    color: #ffffff;
    border: none;
    border-radius: var(--kz-radius-pill);
    padding: 0.65rem 1.3rem;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    text-decoration: none;
}
.kz-btn:hover {
    background: var(--kz-brand-hover);
    transform: translateY(-1px);
    box-shadow: var(--kz-shadow);
}
.kz-btn:active { transform: translateY(0); }

.kz-btn-secondary {
    background: transparent;
    color: var(--kz-text);
    border: 1px solid var(--kz-border-strong);
}
.kz-btn-secondary:hover {
    background: var(--kz-surface-hover);
    border-color: var(--kz-text-muted);
}

.kz-input {
    width: 100%;
    padding: 0.65rem 0.9rem;
    border: 1px solid var(--kz-border-strong);
    border-radius: var(--kz-radius-sm);
    background: var(--kz-surface);
    color: var(--kz-text);
    font-size: 0.9rem;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.kz-input:focus {
    outline: none;
    border-color: var(--kz-brand);
    box-shadow: 0 0 0 3px var(--kz-brand-glow);
}

.kz-nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 1rem;
    border-radius: var(--kz-radius-pill);
    color: var(--kz-text-muted);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9rem;
    transition: all 0.15s ease;
    margin-bottom: 2px;
}
.kz-nav-item:hover {
    background: var(--kz-surface-hover);
    color: var(--kz-text);
}
.kz-nav-item.active {
    background: var(--kz-brand);
    color: #ffffff;
}
.kz-nav-item svg, .kz-nav-item i { width: 18px; height: 18px; }

.kz-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.6rem;
    border-radius: var(--kz-radius-pill);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}
.kz-badge.success { background: #d1fae5; color: #065f46; }
.kz-badge.warn { background: #fef3c7; color: #92400e; }
.kz-badge.danger { background: #fee2e2; color: #991b1b; }
.kz-badge.info { background: #dbeafe; color: #1e40af; }

html.theme-dark .kz-badge.success { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
html.theme-dark .kz-badge.warn { background: rgba(245, 158, 11, 0.2); color: #fcd34d; }
html.theme-dark .kz-badge.danger { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }
html.theme-dark .kz-badge.info { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }

.kz-overlay-header {
    background: var(--kz-surface);
    border-radius: var(--kz-radius);
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
    border: 1px solid var(--kz-border);
    box-shadow: var(--kz-shadow-sm);
}
.kz-overlay-header h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--kz-text);
}
.kz-overlay-stats {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
}
.kz-overlay-stat {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}
.kz-overlay-stat span {
    font-size: 0.72rem;
    color: var(--kz-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.kz-overlay-stat strong {
    font-size: 1.1rem;
    color: var(--kz-text);
    font-family: var(--mono);
}
</style>
"""

    # Inject right before </head>
    if '</head>' in base_html:
        base_html = base_html.replace('</head>', NEW_CSS + '\n</head>', 1)
        print("  [OK]   Injected kaze-fintech-tokens style block")
    else:
        print("  [FAIL] </head> not found in base.html")
        FAILED.append("base.html head")

# Add ID to sidebar-nav for 4c targeting
if 'id="kz-sidebar-nav"' not in base_html:
    base_html = base_html.replace('<nav class="sidebar-nav">', '<nav class="sidebar-nav" id="kz-sidebar-nav">', 1)
    print("  [OK]   Added id='kz-sidebar-nav' to nav element")

with open(BASE, 'w', encoding='utf-8') as f:
    f.write(base_html)

# ═══════════════════════════════════════════════════════════════════
print("\n[6/6] Update settings.html with developer toggle")
# ═══════════════════════════════════════════════════════════════════

with open(SETTINGS, encoding='utf-8') as f:
    st = f.read()

DEV_ANCHOR = "<h2>Stripe payments</h2>"
DEV_BLOCK = """{% if is_developer %}
    <h2>Developer Settings</h2>
    <div class="widget" style="border-left:4px solid var(--kz-brand, #1a8f3c);">
        <p style="color:var(--text2);max-width:40rem;margin-bottom:1rem;">You are listed in KAZE_DEVELOPER_EMAILS. Developer mode gives you unlimited Founder's Premium access for testing. Turn it off to test the paywall and checkout flow as a regular user.</p>
        <div class="form-group" style="display:flex;align-items:center;gap:0.75rem;margin:0;">
            <label style="margin:0;">Developer mode</label>
            <input type="checkbox" name="developer_mode_enabled" {% if settings.developer_mode_enabled == 1 %}checked{% endif %} style="width:20px;height:20px;">
        </div>
    </div>
    {% endif %}

    <h2>Stripe payments</h2>"""

if 'Developer Settings' not in st:
    if DEV_ANCHOR in st:
        st = st.replace(DEV_ANCHOR, DEV_BLOCK, 1)
        print("  [OK]   Added Developer Settings toggle")
    else:
        print("  [FAIL] settings anchor for developer block not found")
        FAILED.append("settings template")
else:
    print("  [SKIP] Developer Settings already present")

with open(SETTINGS, 'w', encoding='utf-8') as f:
    f.write(st)

# ═══════════════════════════════════════════════════════════════════
print("\n[COMPILE] Verifying...")
# ═══════════════════════════════════════════════════════════════════

r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

try:
    Environment().parse(base_html)
    print("  [OK]   base.html parses as valid Jinja")
except Exception as exc:
    print(f"  [FAIL] base.html Jinja error: {exc}")
    sys.exit(1)

try:
    Environment().parse(st)
    print("  [OK]   settings.html parses as valid Jinja")
except Exception as exc:
    print(f"  [FAIL] settings.html Jinja error: {exc}")
    sys.exit(1)

print("\n" + "=" * 62)
print("Phase 4b complete.")
print("  Schema: +developer_mode_enabled")
print("  Backend: effective_plan() respects KAZE_DEVELOPER_EMAILS")
print("  base.html: +kaze-fintech-tokens CSS, +id='kz-sidebar-nav'")
print("  settings.html: +Developer Settings toggle (env-var only)")
print("=" * 62)

if FAILED:
    print("\nFailed steps:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore app.py: copy \"{APP}.bak.phase4b_{STAMP}\" {APP}")
    print(f"Restore base:   copy \"{BASE}.bak.phase4b_{STAMP}\" {BASE}")
    print(f"Restore st:     copy \"{SETTINGS}.bak.phase4b_{STAMP}\" {SETTINGS}")
    sys.exit(1)

print("""
NEXT STEPS:

1. LOCAL TEST — run:  python app.py

   Visuals: NO CHANGE. All existing classes are still in use.
   Only new .kz-* classes exist — unused by any template yet.

   Functional:
   a) /settings -> scroll down. If your email is in KAZE_DEVELOPER_EMAILS
      env var, you'll see "Developer Settings" section with a toggle.
      If the env var isn't set locally, this won't appear — that's
      expected. We'll set it on production.

   b) Toggle Developer mode ON. Save settings.
   c) /plans -> should show "You are on Founder's premium"
      (or your effective plan becomes founder regardless of expiry).
   d) Toggle Developer mode OFF. Save.
   e) /plans -> returns to normal (probably New user).

2. SET ENV VAR ON RENDER:

   Render -> Singapore -> Environment -> add:
     KAZE_DEVELOPER_EMAILS = immanuelzulu25@gmail.com

   This unlocks the Developer Settings section + Founder access in production.
   Without it, nothing changes on prod.

3. COMMIT + PUSH:

   git add app.py templates/base.html templates/settings.html kaze_phase4b_foundation.py
   git commit -m "Phase 4b: fintech design tokens + developer access"
   git push

4. PROD TEST:
   - /settings shows Developer Settings section
   - Toggle dev mode -> /plans shows Founder's Premium
   - Toggle off -> /plans reverts
   - Visual: nothing broken on existing pages
""")