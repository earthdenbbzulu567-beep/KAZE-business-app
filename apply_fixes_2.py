"""
apply_fixes_2.py — MEDIUM + LOW bug fixes for KAZE.

Run from the folder containing app.py:
    python apply_fixes_2.py

Patches app.py and several templates. Each touched file gets a
.bak.<timestamp> backup before any change is made.
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
FAILED, SKIPPED, APPLIED = [], [], []


def patch(path, label, old, new):
    if not os.path.isfile(path):
        print(f"  [SKIP] {label} — {path} not found")
        return
    with open(path, 'r', encoding='utf-8') as fh:
        src = fh.read()
    if old not in src:
        if new in src:
            print(f"  [SKIP] {label} — already fixed")
            SKIPPED.append(label)
        else:
            print(f"  [FAIL] {label} — pattern not found in {path}")
            FAILED.append(label)
        return
    backup = f"{path}.bak.{STAMP}"
    if not os.path.isfile(backup):
        shutil.copy2(path, backup)
    src = src.replace(old, new)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print(f"  [OK]   {label}")
    APPLIED.append(label)


# ─────────────────────────────────────────────────────────────────────────
# app.py — pay_plan compares stored_key not trial-inflated key
# ─────────────────────────────────────────────────────────────────────────
print("[1/9] pay_plan compares stored_key")
patch(
    'app.py', 'pay_plan stored_key',
    """    settings = _stripe_settings()
    current = plan_info(settings)
    if PLAN_RANK[wanted] <= PLAN_RANK[current['key']]:
        flash('You already have this plan or a higher one.', 'info')
        return redirect(url_for('plans'))""",
    """    settings = _stripe_settings()
    current = plan_info(settings)
    # Compare against the paid plan, not the trial-inflated one, so a shop
    # on trial CEO can still buy Entrepreneur for when the trial ends.
    if PLAN_RANK[wanted] <= PLAN_RANK[current['stored_key']]:
        flash('You already have this plan or a higher one.', 'info')
        return redirect(url_for('plans'))""",
)


# ─────────────────────────────────────────────────────────────────────────
# app.py — NAV_GROUPS active tuples missing endpoints
# ─────────────────────────────────────────────────────────────────────────
print("\n[2/9] Nav highlight sub-routes")
patch(
    'app.py', 'nav Counter endpoints',
    "        ('Counter', 'counter', 'monitor-smartphone', 'counter', ('counter', 'counter_sale')),",
    "        ('Counter', 'counter', 'monitor-smartphone', 'counter', ('counter', 'counter_sale', 'counter_checkout')),",
)
patch(
    'app.py', 'nav Sales endpoints',
    "        ('Sales', 'sales', 'receipt', 'sales', ('sales', 'aged_sales')),",
    "        ('Sales', 'sales', 'receipt', 'sales', ('sales', 'aged_sales', 'auto_sale', 'repeat_sale', 'sale_to_invoice', 'sale_receipt')),",
)
patch(
    'app.py', 'nav Stock endpoints',
    "        ('Stock', 'stock', 'package', 'stock', ('stock', 'edit_stock')),",
    "        ('Stock', 'stock', 'package', 'stock', ('stock', 'edit_stock', 'add_stock', 'update_stock', 'stock_bulk', 'check_low_stock', 'reorder_low_stock', 'price_list', 'stock_valuation_pdf')),",
)
patch(
    'app.py', 'nav Customers endpoints',
    "        ('Customers', 'customers', 'users', 'customers', ('customers', 'edit_customer')),",
    "        ('Customers', 'customers', 'users', 'customers', ('customers', 'edit_customer', 'add_customer', 'customers_bulk', 'customer_statement')),",
)


# ─────────────────────────────────────────────────────────────────────────
# app.py — oauth_callback leaves provider in session
# ─────────────────────────────────────────────────────────────────────────
print("\n[3/9] oauth_callback session cleanup")
patch(
    'app.py', 'oauth pop provider',
    """    session.pop('oauth_state', None)
    session.pop('oauth_verifier', None)
    if err or not token:""",
    """    session.pop('oauth_state', None)
    session.pop('oauth_verifier', None)
    session.pop('oauth_provider', None)
    if err or not token:""",
)


# ─────────────────────────────────────────────────────────────────────────
# app.py — send_daily_summary missing conn.close()
# ─────────────────────────────────────────────────────────────────────────
print("\n[4/9] send_daily_summary close connection")
patch(
    'app.py', 'daily summary conn close',
    """    cur.execute('SELECT notify_email, email_notifications, business_name FROM settings WHERE user_id = %s', (current_user.id,))
    settings = cur.fetchone() or {}
    cur.close()

    if not sales_today:""",
    """    cur.execute('SELECT notify_email, email_notifications, business_name FROM settings WHERE user_id = %s', (current_user.id,))
    settings = cur.fetchone() or {}
    cur.close()
    conn.close()

    if not sales_today:""",
)


# ─────────────────────────────────────────────────────────────────────────
# stripe_payments.py — remove managed_payments (breaks unsupported accounts)
# ─────────────────────────────────────────────────────────────────────────
print("\n[5/9] Stripe managed_payments removed")
patch(
    'stripe_payments.py', 'strip managed_payments',
    """            'metadata': {str(k): str(v)[:500] for k, v in (metadata or {}).items()},
            'managed_payments': {'enabled': False},
        }""",
    """            'metadata': {str(k): str(v)[:500] for k, v in (metadata or {}).items()},
        }""",
)


# ─────────────────────────────────────────────────────────────────────────
# templates/base.html — hide user menu + bell from anonymous users
# ─────────────────────────────────────────────────────────────────────────
print("\n[6/9] base.html hides user chrome for anon")

patch(
    'templates/base.html', 'bell link gated',
    """                <a href="{{ url_for('notifications') }}" class="bell-link" title="Notifications">
                    🔔{% if unread_notifications and unread_notifications > 0 %}<span class="bell-badge">{{ unread_notifications }}</span>{% endif %}
                </a>
                <div class="user-menu">""",
    """                {% if current_user.is_authenticated %}
                <a href="{{ url_for('notifications') }}" class="bell-link" title="Notifications">
                    🔔{% if unread_notifications and unread_notifications > 0 %}<span class="bell-badge">{{ unread_notifications }}</span>{% endif %}
                </a>
                {% endif %}
                {% if current_user.is_authenticated %}
                <div class="user-menu">""",
)

patch(
    'templates/base.html', 'user menu gated end',
    """                        <a href="{{ url_for('logout') }}">Logout</a>
                    </div>
                </div>
            </div>
        </header>""",
    """                        <a href="{{ url_for('logout') }}">Logout</a>
                    </div>
                </div>
                {% endif %}
            </div>
        </header>""",
)


# ─────────────────────────────────────────────────────────────────────────
# templates/tasks.html — remove dead select-all checkbox
# ─────────────────────────────────────────────────────────────────────────
print("\n[7/9] tasks.html dead header checkbox")
patch(
    'templates/tasks.html', 'tasks dead header checkbox',
    """                <thead><tr><th>Title</th><th>Priority</th><th>Due</th><th>Notes</th><th><input type="checkbox" onclick="kazeToggleAll(this)"></th></tr></thead>""",
    """                <thead><tr><th>Title</th><th>Priority</th><th>Due</th><th>Notes</th><th></th></tr></thead>""",
)


# ─────────────────────────────────────────────────────────────────────────
# templates/counter.html — clear ticket resets discount
# ─────────────────────────────────────────────────────────────────────────
print("\n[8/9] counter.html clear resets discount")
patch(
    'templates/counter.html', 'counter clear resets discount',
    """    if (clearBtn) clearBtn.addEventListener('click', () => {
        basket.splice(0, basket.length);
        tiles.forEach(t => t.classList.remove('is-picked'));
        render();
    });""",
    """    if (clearBtn) clearBtn.addEventListener('click', () => {
        basket.splice(0, basket.length);
        tiles.forEach(t => t.classList.remove('is-picked'));
        discount.value = 0;
        render();
    });""",
)


# ─────────────────────────────────────────────────────────────────────────
# templates/stock.html — remove dead Jinja guard
# ─────────────────────────────────────────────────────────────────────────
print("\n[9/9] stock.html dead guard removed")
patch(
    'templates/stock.html', 'stock dead jinja guard',
    """{% block content %}
{% if ns is not defined %}{% endif %}
<div class="page-header">""",
    """{% block content %}
<div class="page-header">""",
)


# ─────────────────────────────────────────────────────────────────────────
# Verify app.py still compiles
# ─────────────────────────────────────────────────────────────────────────
print("\nVerifying app.py compiles...")
if os.path.isfile('app.py'):
    r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print("  [OK]   app.py compiles cleanly.")
    else:
        print("  [FAIL] app.py syntax error:")
        print(r.stderr)

print("\n" + "=" * 60)
print(f"Applied: {len(APPLIED)}   Skipped: {len(SKIPPED)}   Failed: {len(FAILED)}")
if FAILED:
    print("\nFailed fixes:")
    for name in FAILED:
        print(f"  - {name}")
print("=" * 60)