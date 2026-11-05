"""
kaze_phase4h_settings_auth.py — Phase 4h.

1. settings.html: page-scoped CSS (mode cards, forms, cards)
2. login.html:    page-scoped CSS (auth card)
3. signup.html:   page-scoped CSS (auth card)
4. errors.html:   full rewrite with animations (404/500/etc)
5. base.html:     offline banner JS + CSS

CSS-only for pages 1-3. Full rewrite for errors.html (safe — it's a
standalone HTML, not extending base.html). JS addition for base.html.

Preserves every form field name, ID, action, and route behavior.

Run from the folder with app.py:
    python kaze_phase4h_settings_auth.py
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

FILES = [
    ('templates/settings.html', 'settings'),
    ('templates/login.html', 'login'),
    ('templates/signup.html', 'signup'),
    ('templates/errors.html', 'errors'),
    ('templates/base.html', 'base'),
]

for path, _ in FILES:
    if not os.path.isfile(path):
        print(f"ERROR: {path} not found.")
        sys.exit(1)

for path, _ in FILES:
    b = f"{path}.bak.phase4h_{STAMP}"
    shutil.copy2(path, b)
    print(f"Backup: {b}")

FAILED = []

# ═══════════════════════════════════════════════════════════════════
print("\n[1/5] Settings page — page-scoped CSS")
# ═══════════════════════════════════════════════════════════════════

with open('templates/settings.html', encoding='utf-8') as f:
    html = f.read()

SETTINGS_CSS = """{% block content %}
<style id="kaze-settings-4h">
/* Phase 4h — Settings page visual */

.page-content .detail-overlay { display: none !important; }

.page-content .page-header {
    border-bottom: 1px solid var(--kz-border, var(--border)) !important;
    padding-bottom: 1rem !important;
    margin-bottom: 1.5rem !important;
}
.page-content .page-header h1 {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: var(--kz-text, var(--text)) !important;
}

/* Section headings */
#settingsForm > h2,
#settingsForm section > h2,
.page-content > h2 {
    font-size: 0.95rem !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
    font-weight: 600 !important;
    color: var(--kz-text, var(--text)) !important;
    margin: 2rem 0 0.9rem !important;
    padding-bottom: 0.55rem;
    border-bottom: 1px solid var(--kz-border, var(--border));
}
#settingsForm > h2::before,
#settingsForm section > h2::before,
.page-content > h2::before { display: none !important; }

/* Mode panel / Device UI section — hero cards at top */
.mode-panel {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.5rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05)) !important;
}
.mode-panel .page-header { border: none !important; padding: 0 !important; margin: 0 0 1rem !important; }
.mode-panel .page-header h2 { font-size: 1rem !important; margin: 0 !important; padding: 0 !important; border: none !important; }

/* Mode cards */
.mode-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)) !important;
    gap: 0.75rem !important;
    margin-bottom: 1rem !important;
}
.mode-card {
    background: var(--kz-bg, var(--bg3)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: 10px !important;
    padding: 0.95rem 1rem !important;
    transition: border-color 0.15s, background 0.15s !important;
}
.mode-card:hover {
    border-color: var(--kz-brand, #1a8f3c) !important;
    background: var(--kz-surface, var(--surface)) !important;
}
.mode-card.is-on,
.mode-card:has(input:checked) {
    border-color: var(--kz-brand, #1a8f3c) !important;
    background: color-mix(in srgb, var(--kz-brand, #1a8f3c) 8%, var(--kz-bg, var(--bg3))) !important;
    box-shadow: 0 0 0 2px var(--kz-brand, #1a8f3c) !important;
}
.mode-card .mode-kicker {
    color: var(--kz-text-light, var(--text3)) !important;
    font-size: 0.66rem !important;
}
.mode-card strong {
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
}
.mode-card .mode-hint {
    color: var(--kz-text-muted, var(--text3)) !important;
    font-size: 0.8rem !important;
}

/* Module check rows */
.module-checks {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)) !important;
    gap: 0.4rem 0.9rem !important;
}
.module-row {
    background: var(--kz-bg, var(--bg3)) !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.75rem !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.86rem !important;
}

/* Widgets (Stripe, PayPal, Flutterwave, Bank cards) */
#settingsForm .widget {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05)) !important;
}
#settingsForm .widget h2 {
    font-size: 0.92rem !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
    color: var(--kz-text, var(--text)) !important;
    font-weight: 600 !important;
    margin: 0 0 0.75rem !important;
    border: none !important;
    padding: 0 !important;
}
#settingsForm .widget h2::before { display: none !important; }

/* Form groups — consistent spacing */
#settingsForm .form-group {
    margin: 0.9rem 0 !important;
}
#settingsForm label {
    font-size: 0.82rem !important;
    color: var(--kz-text-muted, var(--text2)) !important;
    font-weight: 500 !important;
    margin-bottom: 0.4rem !important;
}
#settingsForm input[type="text"],
#settingsForm input[type="number"],
#settingsForm input[type="email"],
#settingsForm input[type="password"],
#settingsForm select,
#settingsForm textarea {
    padding: 0.65rem 0.9rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: 10px !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.9rem !important;
    width: 100%;
    max-width: 520px;
}
#settingsForm input:focus,
#settingsForm select:focus,
#settingsForm textarea:focus {
    outline: none !important;
    border-color: var(--kz-brand, #1a8f3c) !important;
    box-shadow: 0 0 0 3px var(--kz-brand-glow, rgba(26,143,60,0.15)) !important;
}

/* Checkbox rows — inline layout */
#settingsForm .form-group:has(input[type="checkbox"]:not([name="app_mode"]):not([name="ui_device"])) {
    display: flex !important;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}
#settingsForm input[type="checkbox"] {
    width: 18px !important;
    height: 18px !important;
    margin: 0 !important;
    accent-color: var(--kz-brand, #1a8f3c) !important;
}

/* Save button */
#settingsForm > button[type="submit"],
#settingsForm > div > button[type="submit"] {
    background: var(--kz-brand, #1a8f3c) !important;
    color: #fff !important;
    border-radius: 999px !important;
    padding: 0.75rem 1.8rem !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    clip-path: none !important;
    border: none !important;
    margin-top: 1rem !important;
    cursor: pointer;
}
#settingsForm > button[type="submit"]:hover {
    background: #157432 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px var(--kz-brand-glow, rgba(26,143,60,0.3)) !important;
}

/* Secondary buttons inside form (Save mode, Preview, etc) */
#settingsForm button:not([type="submit"]) {
    border-radius: 10px !important;
}

/* Two-factor + Password + Backup + Clear data section cards */
.page-content > h2 ~ .widget,
.page-content > h2 ~ form {
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius, 12px) !important;
    padding: 1.25rem 1.4rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: var(--kz-shadow-sm, 0 1px 2px rgba(0,0,0,0.05)) !important;
}
</style>
"""

if 'kaze-settings-4h' in html:
    print("  [SKIP] CSS already injected")
else:
    if '{% block content %}' in html:
        html = html.replace('{% block content %}', SETTINGS_CSS, 1)
        print("  [OK]   CSS injected")
    else:
        print("  [FAIL] block content not found")
        FAILED.append("settings")

# Verify form integrity — critical form fields must survive
CRITICAL_SETTINGS = [
    'name="low_stock_threshold"',
    'name="notify_email"',
    'name="currency_code"',
    'name="currency_symbol"',
    'name="tax_rate"',
    'name="monthly_revenue_goal"',
    'name="app_mode"',
    'name="stripe_publishable_key"',
    'name="stripe_secret_key"',
    'name="paypal_client_id"',
    'name="flutterwave_public_key"',
    'name="developer_mode_enabled"',
    'id="modes"',
    'id="settingsForm"',
    'action="{{ url_for(\'change_password\') }}"',
    'action="{{ url_for(\'twofa_start\') }}"',
    'action="{{ url_for(\'backup_import\') }}"',
    'action="{{ url_for(\'clear_data\') }}"',
]
for pattern in CRITICAL_SETTINGS:
    if pattern not in html:
        print(f"  [FAIL] missing critical field: {pattern}")
        FAILED.append(f"settings field {pattern}")

try:
    Environment().parse(html)
    print("  [OK]   Jinja parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    FAILED.append("settings jinja")
    html = None

if html:
    with open('templates/settings.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  [OK]   Written")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/5] Login page — page-scoped CSS")
# ═══════════════════════════════════════════════════════════════════

AUTH_CSS = """{% block content %}
<style id="kaze-auth-4h">
/* Phase 4h — Auth pages (login + signup) */

.auth-card {
    max-width: 420px !important;
    margin: 6vh auto !important;
    padding: 2.2rem 2rem 1.8rem !important;
    background: var(--kz-surface, var(--surface)) !important;
    border: 1px solid var(--kz-border, var(--border)) !important;
    border-radius: var(--kz-radius-lg, 20px) !important;
    box-shadow: var(--kz-shadow-xl, 0 20px 25px -5px rgba(0,0,0,0.1)) !important;
}

.auth-card img {
    width: 64px !important;
    height: 64px !important;
    border-radius: 16px !important;
    margin: 0 auto 0.9rem !important;
    display: block !important;
    background: #070707 !important;
    box-shadow: 0 6px 18px rgba(0,0,0,0.25) !important;
}

.auth-card .home-kicker {
    color: var(--kz-brand, #1a8f3c) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.16em !important;
    font-weight: 800 !important;
    margin: 0 0 0.7rem !important;
    text-align: center;
}

.auth-card h1 {
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    margin: 0 0 0.4rem !important;
    text-align: center;
    color: var(--kz-text, var(--text)) !important;
}

.auth-card .form-group {
    display: block !important;
    width: 100% !important;
    margin: 0 0 1rem 0 !important;
}

.auth-card label {
    font-size: 0.82rem !important;
    color: var(--kz-text-muted, var(--text2)) !important;
    font-weight: 500 !important;
    margin-bottom: 0.4rem !important;
    display: block;
}

.auth-card input[type="text"],
.auth-card input[type="email"],
.auth-card input[type="password"] {
    width: 100% !important;
    padding: 0.7rem 0.9rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: 10px !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    font-size: 0.92rem !important;
    font-family: inherit !important;
}
.auth-card input:focus {
    outline: none !important;
    border-color: var(--kz-brand, #1a8f3c) !important;
    box-shadow: 0 0 0 3px var(--kz-brand-glow, rgba(26,143,60,0.15)) !important;
}

.auth-card button[type="submit"] {
    width: 100% !important;
    background: var(--kz-brand, #1a8f3c) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 0.8rem 1.5rem !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    margin-top: 0.6rem !important;
    clip-path: none !important;
    cursor: pointer;
    transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
}
.auth-card button[type="submit"]:hover {
    background: #157432 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px var(--kz-brand-glow, rgba(26,143,60,0.3)) !important;
}

.auth-card p a,
.auth-card label a {
    color: var(--kz-brand, #1a8f3c) !important;
    text-decoration: underline !important;
    text-underline-offset: 2px;
}

/* OAuth buttons */
.auth-card .oauth-btn {
    display: block !important;
    padding: 0.65rem 1rem !important;
    border: 1px solid var(--kz-border-strong, var(--border2)) !important;
    border-radius: 10px !important;
    background: var(--kz-surface, var(--surface)) !important;
    color: var(--kz-text, var(--text)) !important;
    text-decoration: none !important;
    text-align: center !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    transition: background 0.15s, border-color 0.15s;
}
.auth-card .oauth-btn:hover {
    background: var(--kz-surface-hover, var(--surface2)) !important;
    border-color: var(--kz-brand, #1a8f3c) !important;
    color: var(--kz-text, var(--text)) !important;
}
.auth-card .oauth-split {
    color: var(--kz-text-light, var(--text3)) !important;
    font-size: 0.8rem !important;
    margin: 0 0 0.7rem !important;
}
.auth-card .oauth-note {
    color: var(--kz-text-light, var(--text3)) !important;
    font-size: 0.74rem !important;
    line-height: 1.45 !important;
}
</style>
"""

for path, label in [('templates/login.html', 'login'), ('templates/signup.html', 'signup')]:
    print(f"\n  [{label}]")
    with open(path, encoding='utf-8') as f:
        h = f.read()
    if 'kaze-auth-4h' in h:
        print(f"  [SKIP] CSS already injected")
        continue
    if '{% block content %}' in h:
        h = h.replace('{% block content %}', AUTH_CSS, 1)
        print(f"  [OK]   CSS injected")
    else:
        print(f"  [FAIL] block content not found")
        FAILED.append(label)
        continue

    # Verify critical form elements
    needed = ['name="password"', 'method="POST"']
    if label == 'login':
        needed.append('name="login_input"')
    if label == 'signup':
        needed.append('name="username"')
        needed.append('name="accept_terms"')
    for n in needed:
        if n not in h:
            print(f"  [FAIL] missing: {n}")
            FAILED.append(f"{label} field {n}")

    try:
        Environment().parse(h)
        print(f"  [OK]   Jinja parses cleanly")
    except Exception as exc:
        print(f"  [FAIL] Jinja error: {exc}")
        FAILED.append(f"{label} jinja")
        continue

    with open(path, 'w', encoding='utf-8') as f:
        f.write(h)
    print(f"  [OK]   Written")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/5] Errors page — full rewrite with animations")
# ═══════════════════════════════════════════════════════════════════

ERRORS_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ code }} · KAZE</title>
    <style>
        :root {
            --bg: #f9fafb;
            --surface: #ffffff;
            --border: #e5e7eb;
            --text: #111827;
            --text-muted: #6b7280;
            --text-light: #9ca3af;
            --brand: #1a8f3c;
            --brand-hover: #157432;
            --danger: #dc2626;
            --warn: #d97706;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg: #0f172a;
                --surface: #1e293b;
                --border: #334155;
                --text: #f8fafc;
                --text-muted: #94a3b8;
                --text-light: #64748b;
                --brand: #22c55e;
                --brand-hover: #16a34a;
            }
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 1.5rem;
        }
        .wrap {
            max-width: 26rem;
            width: 100%;
            text-align: center;
            animation: fadeInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) both;
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .brand-mark {
            width: 72px;
            height: 72px;
            border-radius: 18px;
            margin: 0 auto 1.5rem;
            background: linear-gradient(135deg, var(--brand), var(--brand-hover));
            display: grid;
            place-items: center;
            font-size: 2rem;
            font-weight: 800;
            color: #ffffff;
            box-shadow: 0 12px 28px rgba(26, 143, 60, 0.3);
            animation: popIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s both;
        }
        @keyframes popIn {
            from { transform: scale(0); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .code {
            font-size: 5rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            line-height: 1;
            margin: 0 0 0.5rem;
            color: {% if code and code >= 500 %}var(--danger){% elif code and code >= 400 %}var(--warn){% else %}var(--brand){% endif %};
            animation: pulseSoft 2.4s ease-in-out infinite;
        }
        @keyframes pulseSoft {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.75; }
        }
        h1 {
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 0 0 0.6rem;
            animation: fadeInUp 0.5s ease 0.2s both;
        }
        .message {
            color: var(--text-muted);
            font-size: 0.95rem;
            line-height: 1.6;
            margin: 0 0 2rem;
            animation: fadeInUp 0.5s ease 0.3s both;
        }
        .actions {
            display: flex;
            gap: 0.6rem;
            justify-content: center;
            flex-wrap: wrap;
            animation: fadeInUp 0.5s ease 0.4s both;
        }
        .actions a {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.7rem 1.3rem;
            border-radius: 999px;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.15s ease;
        }
        .actions a.primary {
            background: var(--brand);
            color: #ffffff;
        }
        .actions a.primary:hover {
            background: var(--brand-hover);
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(26, 143, 60, 0.3);
        }
        .actions a.secondary {
            background: transparent;
            color: var(--text);
            border: 1px solid var(--border);
        }
        .actions a.secondary:hover {
            border-color: var(--brand);
            color: var(--brand);
        }
        .footnote {
            color: var(--text-light);
            font-size: 0.75rem;
            margin-top: 2.5rem;
            animation: fadeInUp 0.5s ease 0.5s both;
        }
    </style>
</head>
<body>
    <div class="wrap">
        <div class="brand-mark">K</div>
        <div class="code">{{ code }}</div>
        <h1>{{ title }}</h1>
        <p class="message">{{ message }}</p>
        <div class="actions">
            <a href="/" class="primary">← Home</a>
            <a href="/dashboard" class="secondary">Dashboard</a>
        </div>
        <p class="footnote">KAZE Traders Business Manager</p>
    </div>
</body>
</html>'''

with open('templates/errors.html', 'w', encoding='utf-8') as f:
    f.write(ERRORS_HTML)
print("  [OK]   errors.html rewritten with animations")
print("  [OK]   Supports dark/light via prefers-color-scheme")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/5] base.html — offline banner")
# ═══════════════════════════════════════════════════════════════════

with open('templates/base.html', encoding='utf-8') as f:
    base_html = f.read()

OFFLINE_CSS = """<style id="kaze-offline-banner-css">
#kaze-offline-banner {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
    padding: 0.7rem 1.2rem;
    background: #dc2626;
    color: #ffffff;
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    transform: translateY(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: 'Inter', -apple-system, sans-serif;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
#kaze-offline-banner.visible {
    transform: translateY(0);
}
#kaze-offline-banner button {
    background: rgba(255, 255, 255, 0.2);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 700;
    cursor: pointer;
    clip-path: none;
    transition: background 0.15s;
}
#kaze-offline-banner button:hover {
    background: rgba(255, 255, 255, 0.35);
}
body.kaze-offline .main-content { padding-top: 36px; }
</style>"""

OFFLINE_HTML_JS = """<div id="kaze-offline-banner" role="alert" aria-live="polite">
    <span>⚠ You're offline. Some features may not work.</span>
    <button type="button" id="kaze-offline-retry">Reconnect</button>
</div>
<script id="kaze-offline-js">
(function(){
    var banner = document.getElementById('kaze-offline-banner');
    var retryBtn = document.getElementById('kaze-offline-retry');
    if (!banner) return;
    function update() {
        if (navigator.onLine === false) {
            banner.classList.add('visible');
            document.body.classList.add('kaze-offline');
        } else {
            banner.classList.remove('visible');
            document.body.classList.remove('kaze-offline');
        }
    }
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    if (retryBtn) {
        retryBtn.addEventListener('click', function() {
            if (navigator.onLine) {
                update();
                window.location.reload();
            } else {
                retryBtn.textContent = 'Still offline…';
                setTimeout(function() { retryBtn.textContent = 'Reconnect'; }, 2000);
            }
        });
    }
    update();
})();
</script>"""

if 'kaze-offline-banner-css' in base_html:
    print("  [SKIP] Offline banner already present")
else:
    if '</head>' in base_html:
        base_html = base_html.replace('</head>', OFFLINE_CSS + '\n</head>', 1)
        print("  [OK]   offline banner CSS injected")
    else:
        print("  [FAIL] </head> not found")
        FAILED.append("base offline CSS")

    # Insert banner HTML+JS right after <body ...>
    body_open_idx = base_html.find('<body')
    if body_open_idx >= 0:
        # Find end of opening body tag
        body_tag_end = base_html.find('>', body_open_idx)
        if body_tag_end >= 0:
            base_html = base_html[:body_tag_end+1] + '\n' + OFFLINE_HTML_JS + base_html[body_tag_end+1:]
            print("  [OK]   offline banner HTML+JS injected")
        else:
            print("  [FAIL] body tag has no closing >")
            FAILED.append("base offline HTML")
    else:
        print("  [FAIL] <body not found")
        FAILED.append("base offline HTML")

try:
    Environment().parse(base_html)
    print("  [OK]   base.html parses cleanly")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")
    FAILED.append("base jinja")
else_ok = True

# Verify critical base elements
for pattern in ['id="kz-sidebar-nav"', 'kaze-fintech-tokens', 'kaze-offline-banner']:
    if pattern not in base_html:
        print(f"  [FAIL] missing critical: {pattern}")
        FAILED.append(f"base {pattern}")

if not FAILED or 'base jinja' not in FAILED:
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)
    print(f"  [OK]   Written")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/5] Summary")
print("\n" + "=" * 62)

r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'], capture_output=True, text=True)
if r.returncode != 0:
    print("[WARN] app.py has syntax error (should not be affected):")
    print(r.stderr)

if FAILED:
    print(f"\n{len(FAILED)} issues:")
    for f in FAILED:
        print(f"  - {f}")
    print(f"\nRestore from backups: templates/*.bak.phase4h_{STAMP}")
    sys.exit(1)

print("Phase 4h complete.")
print("  settings.html: mode cards, forms, widgets → mockup cards")
print("  login.html:    auth card restyled")
print("  signup.html:   auth card restyled")
print("  errors.html:   rewritten with animations + dark/light")
print("  base.html:     offline banner (auto-detects navigator.onLine)")
print("=" * 62)
print(f"""
NEXT STEPS:

1. Restart:  python app.py

2. Test /settings
   [ ] Mode cards styled as mockup cards
   [ ] Currency, tax, goal inputs styled
   [ ] Stripe/PayPal/Flutterwave widget panels clean
   [ ] Save all settings works
   [ ] Developer Settings section still visible (if you're in env var)

3. Test /login
   [ ] Card centered, shadow, rounded
   [ ] Logo at top
   [ ] Inputs styled
   [ ] Login button pill green
   [ ] OAuth buttons below
   [ ] Log in with your test credentials → works

4. Test /signup
   [ ] Card styled
   [ ] Create a test account → works
   [ ] Delete the test account afterward

5. Test error pages
   - Visit /thisdoesnotexist → 404 page with animation
   - (500 hard to trigger — if you see one, note the styling)

6. Test offline banner
   - Open any page
   - Turn off WiFi (or use DevTools Network tab → Offline)
   - Banner should slide down from top: "⚠ You're offline"
   - Turn WiFi back on → banner slides up
   - Click "Reconnect" while offline → shows "Still offline…" for 2 sec

7. Regression
   - /dashboard, /sales, /plans still work
   - Sidebar groups, theme toggle, all still work

8. If all pass:
   git add templates/settings.html templates/login.html templates/signup.html templates/errors.html templates/base.html kaze_phase4h_settings_auth.py
   git commit -m "Phase 4h: settings + auth + error pages + offline banner"
   git push

AFTER 4h: 4g (analytics) + 4i (overlays + SMTP + payment activation).
""")