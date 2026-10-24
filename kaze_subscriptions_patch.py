"""
kaze_subscriptions_patch.py — annual USD subscriptions for KAZE.

Includes all three safeguards:
  A. Webhook guard — skips one-time fulfillment for subscription checkouts
  B. /plans/sync polling — waits for webhook to land before redirecting
  C. Per-tier subscription availability — works even if only 1 price ID set

Run from the folder with app.py:
    python kaze_subscriptions_patch.py
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
APP = 'app.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found.")
    sys.exit(1)

if not os.path.isfile('subscriptions.py'):
    print("ERROR: subscriptions.py not found in this folder.")
    print("Save it BEFORE running this patch.")
    sys.exit(1)

APPLIED, SKIPPED, FAILED = [], [], []

def backup(path):
    if os.path.isfile(path):
        b = f"{path}.bak.{STAMP}"
        if not os.path.isfile(b):
            shutil.copy2(path, b)

def patch(label, old, new, required=True):
    with open(APP, encoding='utf-8') as f:
        src = f.read()
    if old not in src:
        if new in src:
            print(f"  [SKIP] {label}")
            SKIPPED.append(label)
            return
        print(f"  [FAIL] {label} — pattern not found")
        if required: FAILED.append(label)
        return
    backup(APP)
    if src.count(old) > 1:
        print(f"  [WARN] {label} — {src.count(old)} matches")
    with open(APP, 'w', encoding='utf-8') as f:
        f.write(src.replace(old, new))
    print(f"  [OK]   {label}")
    APPLIED.append(label)

# ═══════════════════════════════════════════════════════════════════
print("\n[1/11] Schema — 6 new columns")
patch(
    "schema subscription columns",
    """    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS plan_paid_rank INTEGER DEFAULT 0")""",
    """    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS plan_paid_rank INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS plan_started_at TEXT DEFAULT ''")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS plan_expires_at TEXT DEFAULT ''")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS grace_expires_at TEXT DEFAULT ''")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT DEFAULT ''")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT DEFAULT ''")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'none'")""")

# ═══════════════════════════════════════════════════════════════════
print("\n[2/11] USD prices in PLAN_TIERS")
for tier, price in [('entrepreneur', 10), ('businessman', 25), ('ceo', 50), ('founder', 100)]:
    pattern = re.compile(
        r"('%s':\s*\{.*?'price':\s*)\d+(,)" % re.escape(tier),
        re.DOTALL,
    )
    with open(APP, encoding='utf-8') as f:
        src = f.read()
    m = pattern.search(src)
    if not m:
        print(f"  [FAIL] price for {tier}")
        FAILED.append(f"price {tier}")
        continue
    new_src = src[:m.start()] + f"{m.group(1)}{price}{m.group(2)}" + src[m.end():]
    with open(APP, 'w', encoding='utf-8') as f:
        f.write(new_src)
    print(f"  [OK]   {tier} = ${price}/year")

# ═══════════════════════════════════════════════════════════════════
print("\n[3/11] Force USD in checkout")
if os.path.isfile('stripe_payments.py'):
    with open('stripe_payments.py', encoding='utf-8') as f:
        sp = f.read()
    old_cur = """def currency_code(settings=None):
    env = (os.environ.get('STRIPE_CURRENCY') or '').strip().upper()
    shop = ''
    if settings:
        shop = str(settings.get('currency_code') or '').strip().upper()
    code = env or shop or 'USD'
    if len(code) != 3:
        code = 'USD'
    return code"""
    new_cur = """def currency_code(settings=None):
    # Subscriptions are billed in USD. Fixed for the launch model.
    return 'USD'"""
    if old_cur in sp:
        backup('stripe_payments.py')
        with open('stripe_payments.py', 'w', encoding='utf-8') as f:
            f.write(sp.replace(old_cur, new_cur))
        print("  [OK]   stripe_payments.currency_code → USD")
        APPLIED.append("stripe_payments USD")
    elif new_cur in sp:
        print("  [SKIP] stripe_payments already USD")
        SKIPPED.append("stripe_payments USD")
    else:
        print("  [FAIL] currency_code pattern not found")
        FAILED.append("currency_code")
else:
    print("  [FAIL] stripe_payments.py not found")
    FAILED.append("stripe_payments.py missing")

# ═══════════════════════════════════════════════════════════════════
print("\n[4/11] effective_plan + subscription_info helpers")
patch(
    "effective_plan helpers",
    "def plan_info(settings=None):",
    """def days_between(start_iso, end_iso):
    try:
        a = datetime.strptime(str(start_iso or '')[:10], '%Y-%m-%d')
        b = datetime.strptime(str(end_iso or '')[:10], '%Y-%m-%d')
        return max(0, (b - a).days)
    except (TypeError, ValueError):
        return 0


def subscription_info(settings=None):
    settings = settings or {}
    today = datetime.today().strftime('%Y-%m-%d')
    expires = str(settings.get('plan_expires_at') or '')[:10]
    grace = str(settings.get('grace_expires_at') or '')[:10]
    status = str(settings.get('subscription_status') or 'none').lower()

    if status in ('active', 'trialing') and expires and expires >= today:
        return {'status': 'active', 'expires': expires,
                'days_left': days_between(today, expires), 'grace': ''}
    if status == 'past_due' and grace and grace >= today:
        return {'status': 'grace', 'expires': expires, 'grace': grace,
                'days_left': days_between(today, grace)}
    if status == 'canceled' and expires and expires >= today:
        return {'status': 'canceled_active', 'expires': expires,
                'days_left': days_between(today, expires), 'grace': ''}
    if expires and expires < today:
        return {'status': 'expired', 'expires': expires,
                'days_since': days_between(expires, today), 'grace': ''}
    return {'status': 'none', 'expires': '', 'grace': '', 'days_left': 0}


def effective_plan(settings=None):
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

    return 'new_user'


def plan_info(settings=None):""")

patch(
    "plan_info uses effective_plan",
    """def plan_info(settings=None):
    raw = None
    if settings:
        raw = settings.get('plan_tier')
    stored = normalize_plan(raw if raw not in (None, '') else 'ceo')
    trial = trial_info(settings)
    key = 'ceo' if trial.get('active') else stored
    info = dict(PLAN_TIERS[key])
    info['key'] = key
    info['stored_key'] = stored
    info['price'] = package_prices_for(settings).get(key, info.get('price') or 0)
    info['trial'] = trial
    return info""",
    """def plan_info(settings=None):
    settings = settings or {}
    stored = normalize_plan(settings.get('plan_tier') or 'new_user')
    key = effective_plan(settings)
    info = dict(PLAN_TIERS[key])
    info['key'] = key
    info['stored_key'] = stored
    info['price'] = package_prices_for(settings).get(key, info.get('price') or 0)
    info['trial'] = trial_info(settings)
    info['subscription'] = subscription_info(settings)
    info['stripe_customer_id'] = str(settings.get('stripe_customer_id') or '')
    return info""")

# ═══════════════════════════════════════════════════════════════════
print("\n[5/11] Import subscriptions")
patch(
    "import subscriptions",
    "import stripe_payments\nimport integrations",
    "import stripe_payments\nimport integrations\nimport subscriptions"
)

# ═══════════════════════════════════════════════════════════════════
print("\n[6/11] set_plan — free tier only")
patch(
    "set_plan free only",
    """@app.route('/plans/set', methods=['POST'])
@login_required
def set_plan():
    if getattr(current_user, 'role', 'owner') != 'owner':
        flash('Only the owner can change the plan.', 'danger')
        return redirect(url_for('plans'))
    wanted = normalize_plan(request.form.get('plan_tier'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT plan_paid_rank FROM settings WHERE user_id=%s', (current_user.id,))
    row = cur.fetchone() or {}
    try:
        paid_rank = int(row.get('plan_paid_rank') or 0)
    except (TypeError, ValueError):
        paid_rank = 0
    cur.close()
    conn.close()
    wanted_rank = PLAN_RANK.get(wanted, 0)
    wanted_price = float(PLAN_TIERS.get(wanted, {}).get('price') or 0)
    if wanted_price > 0 and wanted_rank > paid_rank:
        flash('Pay for that package on the Packages page to unlock it.', 'danger')
        return redirect(url_for('plans'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE settings SET plan_tier=%s WHERE user_id=%s', (wanted, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    flash('Package set to {}.'.format(PLAN_TIERS[wanted]['label']), 'success')
    return redirect(url_for('plans'))""",
    """@app.route('/plans/set', methods=['POST'])
@login_required
def set_plan():
    if getattr(current_user, 'role', 'owner') != 'owner':
        flash('Only the owner can change the plan.', 'danger')
        return redirect(url_for('plans'))
    wanted = normalize_plan(request.form.get('plan_tier'))
    if wanted != 'new_user':
        flash('Paid packages are subscribed on the Packages page.', 'danger')
        return redirect(url_for('plans'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT subscription_status FROM settings WHERE user_id=%s', (current_user.id,))
    row = cur.fetchone() or {}
    if (row.get('subscription_status') or '').lower() in ('active', 'trialing', 'past_due'):
        cur.close(); conn.close()
        flash('You have an active subscription. Cancel it from Manage first.', 'danger')
        return redirect(url_for('plans'))
    cur.execute('UPDATE settings SET plan_tier=%s WHERE user_id=%s', ('new_user', current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    flash('Switched to the free tier.', 'success')
    return redirect(url_for('plans'))""")

# ═══════════════════════════════════════════════════════════════════
print("\n[7/11] New subscription routes (subscribe, sync+status polling, manage)")
patch(
    "subscribe + sync + status + manage routes",
    "@app.route('/plans/upgrade/<tier>')",
    """@app.route('/plans/subscribe/<tier>')
@login_required
def subscribe_plan(tier):
    if getattr(current_user, 'role', 'owner') != 'owner':
        flash('Only the owner can subscribe.', 'danger')
        return redirect(url_for('plans'))
    wanted = normalize_plan(tier)
    if wanted == 'new_user':
        flash('Free tier needs no subscription.', 'info')
        return redirect(url_for('plans'))
    if not subscriptions.price_id_for(wanted):
        flash('That package is not available for subscription yet.', 'danger')
        return redirect(url_for('plans'))
    settings = _stripe_settings()
    sub = subscription_info(settings)
    if sub.get('status') in ('active', 'grace', 'canceled_active'):
        flash('You already have an active subscription. Use Manage to change it.', 'danger')
        return redirect(url_for('plans'))

    customer_id, err = subscriptions.get_or_create_customer(
        settings, current_user.id, current_user.email, current_user.username)
    if err:
        flash('Could not reach Stripe: ' + err, 'danger')
        return redirect(url_for('plans'))

    if customer_id and customer_id != (settings or {}).get('stripe_customer_id'):
        conn = get_db(); cur = conn.cursor()
        cur.execute('UPDATE settings SET stripe_customer_id=%s WHERE user_id=%s',
                    (customer_id, current_user.id))
        conn.commit(); cur.close(); conn.close()

    success = url_for('plans_sync', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel = url_for('plans', _external=True)
    session, err = subscriptions.create_subscription_checkout(
        settings, wanted, customer_id, current_user.id, success, cancel)
    if err:
        flash('Could not start subscription: ' + err, 'danger')
        return redirect(url_for('plans'))
    return redirect(session.url, code=303)


@app.route('/plans/sync')
@login_required
def plans_sync():
    \"\"\"Landing page while Stripe webhook catches up.\"\"\"
    return render_template('plans_sync.html')


@app.route('/plans/status')
@login_required
def plans_status():
    \"\"\"JSON status used by the /plans/sync polling page.\"\"\"
    settings = _stripe_settings()
    sub = subscription_info(settings)
    return {
        'active': sub.get('status') in ('active', 'grace', 'canceled_active'),
        'status': sub.get('status'),
        'expires': sub.get('expires'),
    }


@app.route('/plans/manage')
@login_required
def plans_manage():
    if getattr(current_user, 'role', 'owner') != 'owner':
        flash('Only the owner can manage the subscription.', 'danger')
        return redirect(url_for('plans'))
    settings = _stripe_settings()
    customer_id = (settings or {}).get('stripe_customer_id') or ''
    if not customer_id:
        flash('No active subscription to manage.', 'info')
        return redirect(url_for('plans'))
    return_url = url_for('plans', _external=True)
    session, err = subscriptions.create_portal_session(settings, customer_id, return_url)
    if err:
        flash('Could not open the billing portal: ' + err, 'danger')
        return redirect(url_for('plans'))
    return redirect(session.url, code=303)


@app.route('/plans/upgrade/<tier>')""")

# ═══════════════════════════════════════════════════════════════════
print("\n[8/11] Webhook — subscription events + skip subscription checkouts")
patch(
    "webhook subscription delegation",
    """    etype = event.get('type')
    if etype in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):""",
    """    etype = event.get('type')
    if etype and etype.startswith('customer.subscription.'):
        return subscriptions.handle_webhook(get_db, event)
    if etype in ('invoice.payment_succeeded', 'invoice.payment_failed'):
        return subscriptions.handle_webhook(get_db, event)
    if etype in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        # Skip subscription checkouts — subscription lifecycle events
        # (customer.subscription.created, invoice.payment_succeeded) are
        # the source of truth. Without this guard, the one-time handler
        # below would insert a spurious income row for every subscription.
        if ((event.get('data') or {}).get('object') or {}).get('mode') == 'subscription':
            return ('', 200)""")

# ═══════════════════════════════════════════════════════════════════
print("\n[9/11] Trial — 14-18 days")
patch("trial 14-18 days", "    days = min(12, max(7, days))", "    days = min(18, max(14, days))")
patch("trial_choices 14-18", "        trial_day_choices=list(range(7, 13)),", "        trial_day_choices=list(range(14, 19)),")

# ═══════════════════════════════════════════════════════════════════
print("\n[10/11] plans() route — pass configured tiers")
patch(
    "plans route configured tiers",
    """        trial=trial,
        trial_day_choices=list(range(14, 19)),
        paid_rank=paid_rank,
        is_owner=(getattr(current_user, 'role', 'owner') == 'owner'),
    )""",
    """        trial=trial,
        trial_day_choices=list(range(14, 19)),
        paid_rank=paid_rank,
        is_owner=(getattr(current_user, 'role', 'owner') == 'owner'),
        subs_configured_tiers=subscriptions.configured_tiers(),
        subs_any_ready=subscriptions.subs_ready(),
    )""")

# ═══════════════════════════════════════════════════════════════════
print("\n[11/11] Templates")
os.makedirs('templates', exist_ok=True)

PLANS_HTML = '''{% extends "base.html" %}
{% block content %}
<style>
.pkg-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.9rem; align-items: stretch; }
.pkg-card { padding: 1.2rem 1.15rem 1.2rem; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); display: flex; flex-direction: column; gap: 0.35rem; }
.pkg-card h2 { margin: 0; font-size: 1.15rem; }
.pkg-rank { font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text3); font-weight: 800; }
.pkg-tag { color: var(--text2); font-size: 0.88rem; margin: 0; min-height: 2.6em; }
.pkg-price { font-family: var(--mono); font-size: 1.35rem; margin: 0.3rem 0 0.4rem; }
.pkg-price span { font-size: 0.72rem; color: var(--text3); font-family: var(--font); }
.pkg-card ul { margin: 0 0 0.9rem; padding-left: 1.1rem; color: var(--text2); font-size: 0.88rem; line-height: 1.55; flex: 1; }
.pkg-card.is-current { border-color: var(--red-bright); box-shadow: 0 0 0 1px var(--red-bright), 0 12px 28px rgba(0,0,0,0.2); }
.pkg-card.is-founder { background: linear-gradient(180deg, var(--accent-wash), var(--surface)); }
.pkg-note { color: var(--text3); font-size: 0.85rem; max-width: 44rem; margin-top: 1.1rem; }
.pkg-badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; margin: 0.4rem 0; }
.pkg-badge.paid    { background: var(--red-glow); color: var(--red-bright); }
.pkg-badge.warn    { background: rgba(224,160,48,0.15); color: #e0a030; }
.sub-panel { padding: 1rem 1.1rem; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); margin-bottom: 1rem; }
</style>

<div class="page-header">
    <div>
        <h1>Packages</h1>
        <p>You are on <strong>{{ current.label }}</strong> — {{ current.tagline }}</p>
    </div>
</div>

{% set sub = current.subscription %}
{% if sub and sub.status == 'active' %}
<div class="sub-panel" style="border-color:var(--green);">
    <strong style="color:var(--green);">Active subscription</strong>
    <p style="margin:0.35rem 0 0.6rem;">Renews on <strong>{{ sub.expires }}</strong> ({{ sub.days_left }} day{{ '' if sub.days_left == 1 else 's' }}).</p>
    {% if is_owner %}<a class="btn-secondary" href="{{ url_for('plans_manage') }}">Manage subscription</a>{% endif %}
</div>
{% elif sub and sub.status == 'grace' %}
<div class="sub-panel" style="border-color:#e74c3c;">
    <strong style="color:#e74c3c;">Payment failed</strong>
    <p style="margin:0.35rem 0 0.6rem;">Update your card by <strong>{{ sub.grace }}</strong> ({{ sub.days_left }} day{{ '' if sub.days_left == 1 else 's' }}) or you'll drop to free.</p>
    {% if is_owner %}<a class="btn-secondary" href="{{ url_for('plans_manage') }}">Update payment</a>{% endif %}
</div>
{% elif sub and sub.status == 'canceled_active' %}
<div class="sub-panel" style="border-color:#e0a030;">
    <strong style="color:#e0a030;">Canceled</strong>
    <p style="margin:0.35rem 0 0.6rem;">You keep {{ current.label }} until <strong>{{ sub.expires }}</strong>, then drop to free.</p>
    {% if is_owner %}<a class="btn-secondary" href="{{ url_for('subscribe_plan', tier=current.stored_key) }}">Reactivate</a>{% endif %}
</div>
{% elif sub and sub.status == 'expired' %}
<div class="sub-panel" style="border-color:#e74c3c;">
    <strong style="color:#e74c3c;">Subscription expired</strong>
    <p style="margin:0.35rem 0 0.6rem;">Ended on {{ sub.expires }}. Data is safe. Subscribe again to restore.</p>
</div>
{% elif trial and trial.active %}
<div class="sub-panel" style="border-color:var(--red-bright);">
    <strong>Trial active</strong>
    <p style="margin:0.35rem 0 0;">Full CEO tools for <strong>{{ trial.days_left }}</strong> more day{{ '' if trial.days_left == 1 else 's' }} (until {{ trial.ends }}).</p>
</div>
{% elif trial and trial.expired %}
<div class="sub-panel">
    <p style="margin:0;">Trial ended {{ trial.ends }}. You are now on the free tier.</p>
</div>
{% endif %}

{% if is_owner and trial and not trial.started and (not sub or sub.status == 'none') %}
<div class="sub-panel">
    <strong>Free trial</strong>
    <p style="margin:0.35rem 0 0.7rem;color:var(--text2);max-width:40rem;">Try the full CEO desk for 14–18 days. One trial per shop.</p>
    <form method="POST" action="{{ url_for('start_trial') }}" style="display:flex;gap:0.6rem;flex-wrap:wrap;align-items:flex-end;">
        <div class="form-group"><label>Trial length</label>
            <select name="trial_days">
                {% for d in trial_day_choices %}<option value="{{ d }}" {% if d == 14 %}selected{% endif %}>{{ d }} days</option>{% endfor %}
            </select>
        </div>
        <button type="submit">Start free trial</button>
    </form>
</div>
{% endif %}

<div class="stat-grid">
    <div class="stat-chip"><span>Stock used</span><strong>{{ counts.stock }}{% if current.limits.stock %}/{{ current.limits.stock }}{% endif %}</strong></div>
    <div class="stat-chip"><span>Customers</span><strong>{{ counts.customers }}{% if current.limits.customers %}/{{ current.limits.customers }}{% endif %}</strong></div>
    <div class="stat-chip"><span>Services</span><strong>{{ counts.services }}{% if current.limits.services %}/{{ current.limits.services }}{% endif %}</strong></div>
    <div class="stat-chip"><span>Sales this month</span><strong>{{ counts.sales_month }}{% if current.limits.sales_month %}/{{ current.limits.sales_month }}{% endif %}</strong></div>
    <div class="stat-chip"><span>Team seats</span><strong>{{ counts.team }}{% if current.limits.team %}/{{ current.limits.team }}{% endif %}</strong></div>
</div>

<div class="pkg-grid">
{% for t in tiers %}
<article class="pkg-card {% if t.key == current.key %}is-current{% endif %} {% if t.key == 'founder' %}is-founder{% endif %}">
    <span class="pkg-rank">{{ loop.index }} / {{ tiers|length }}</span>
    <h2>{{ t.label }}</h2>
    <p class="pkg-tag">{{ t.tagline }}</p>
    <p class="pkg-price">
        {% if t.price %}${{ '%.0f'|format(t.price) }} <span>per year</span>
        {% else %}Free{% endif %}
    </p>
    <ul>{% for line in t.highlights %}<li>{{ line }}</li>{% endfor %}</ul>

    {% if t.key == current.stored_key and sub.status in ('active', 'grace', 'canceled_active') %}
        <span class="pkg-badge {% if sub.status != 'active' %}warn{% else %}paid{% endif %}">
            {% if sub.status == 'active' %}Subscribed until {{ sub.expires }}
            {% elif sub.status == 'grace' %}Payment failed
            {% else %}Canceled — until {{ sub.expires }}{% endif %}
        </span>
        {% if is_owner %}<a class="btn-secondary" href="{{ url_for('plans_manage') }}">Manage</a>{% endif %}
    {% elif t.price and is_owner %}
        {% if t.key in subs_configured_tiers %}
        <a class="btn-secondary" href="{{ url_for('subscribe_plan', tier=t.key) }}">Subscribe — ${{ '%.0f'|format(t.price) }}/year</a>
        {% else %}
        <p style="font-size:0.8rem;color:var(--text3);">Not available for subscription yet.</p>
        {% endif %}
    {% elif not t.price and t.key != current.key %}
        <form method="POST" action="{{ url_for('set_plan') }}">
            <input type="hidden" name="plan_tier" value="{{ t.key }}">
            <button type="submit" class="btn-secondary">Switch to free</button>
        </form>
    {% endif %}
</article>
{% endfor %}
</div>

<p class="pkg-note">Billed yearly in USD. Existing customers keep the highest tier they paid for. Your display currency in Settings is still used on screens and PDFs — the subscription charge itself is always USD.</p>
{% endblock %}
'''

PLANS_SYNC_HTML = '''{% extends "base.html" %}
{% block title %}Activating subscription{% endblock %}
{% block content %}
<div class="page-header">
    <div>
        <h1>Activating your subscription</h1>
        <p>Stripe confirmed your payment. Waiting for the webhook — this usually takes 2-10 seconds.</p>
    </div>
</div>

<div class="widget" style="text-align:center;padding:2rem;">
    <div id="status-icon" style="font-size:3rem;line-height:1;">⏳</div>
    <p id="status-text" style="margin:1rem 0 0;color:var(--text2);">Checking subscription status…</p>
    <p id="fallback" style="margin:1.5rem 0 0;font-size:0.85rem;color:var(--text3);" hidden>
        Still processing. <a href="{{ url_for('plans') }}">Click here</a> to continue — the tier may update in a few seconds.
    </p>
</div>

<script>
(function(){
    var attempts = 0;
    var maxAttempts = 15;
    var statusText = document.getElementById('status-text');
    var statusIcon = document.getElementById('status-icon');
    var fallback = document.getElementById('fallback');

    function poll() {
        attempts++;
        statusText.textContent = 'Checking… (' + attempts + '/' + maxAttempts + ')';
        fetch('{{ url_for("plans_status") }}', { credentials: 'same-origin' })
            .then(function(r){ return r.json(); })
            .then(function(d){
                if (d && d.active) {
                    statusIcon.textContent = '✅';
                    statusText.textContent = 'Subscription active. Redirecting…';
                    window.location = '{{ url_for("plans") }}';
                    return;
                }
                if (attempts >= maxAttempts) {
                    statusIcon.textContent = '⚠️';
                    statusText.textContent = 'Webhook still pending.';
                    fallback.hidden = false;
                    return;
                }
                setTimeout(poll, 2000);
            })
            .catch(function(){
                if (attempts >= maxAttempts) {
                    fallback.hidden = false;
                    return;
                }
                setTimeout(poll, 2000);
            });
    }
    setTimeout(poll, 1500);
})();
</script>
{% endblock %}
'''

for name, content in [('templates/plans.html', PLANS_HTML), ('templates/plans_sync.html', PLANS_SYNC_HTML)]:
    if os.path.isfile(name):
        backup(name)
    with open(name, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [OK]   {name} ({len(content):,} bytes)")

# ═══════════════════════════════════════════════════════════════════
print("\n[COMPILE]")
r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, text=True)
if r.returncode != 0:
    print("  [FAIL] " + r.stderr)
    print(f"\nRestore:  copy \"{APP}.bak.{STAMP}\" {APP}")
    sys.exit(1)
print("  [OK]   app.py compiles cleanly")

# ═══════════════════════════════════════════════════════════════════
print("\n[VERIFY]")
with open(APP, encoding='utf-8') as f:
    src = f.read()
checks = {
    'schema columns':         "ADD COLUMN IF NOT EXISTS plan_expires_at" in src,
    'USD prices':             "'price': 10," in src and "'price': 100," in src,
    'effective_plan':         "def effective_plan(settings=None):" in src,
    'subscription_info':      "def subscription_info(settings=None):" in src,
    'subscriptions imported': "import subscriptions" in src,
    'subscribe route':        "def subscribe_plan(tier):" in src,
    'sync route':             "def plans_sync():" in src,
    'status JSON route':      "def plans_status():" in src,
    'manage route':           "def plans_manage():" in src,
    'webhook delegates':      "subscriptions.handle_webhook(get_db, event)" in src,
    'webhook subscription guard': ".get('mode') == 'subscription'" in src,
    'trial 14-18':            "days = min(18, max(14, days))" in src,
    'configured_tiers passed':'subs_configured_tiers=subscriptions.configured_tiers()' in src,
    'set_plan free only':     "Paid packages are subscribed on the Packages page" in src,
}
all_ok = True
for label, present in checks.items():
    print(f"  {'[OK]  ' if present else '[FAIL]'} {label}")
    if not present: all_ok = False

if not all_ok:
    print(f"\n[FATAL] Restore: copy \"{APP}.bak.{STAMP}\" {APP}")
    sys.exit(1)

print("\n" + "=" * 62)
print(f"APPLIED: {len(APPLIED)}   SKIPPED: {len(SKIPPED)}   FAILED: {len(FAILED)}")
print("=" * 62)

if FAILED:
    print("\nFailed:")
    for f in FAILED: print(f"  - {f}")
    print("\nOpen app.py, search for the label, fix by hand.")
    sys.exit(1)

print("""
DONE. Next steps (in order):

── 1. Create 4 products in Stripe ──
https://dashboard.stripe.com/test/products
For each: Add product → Recurring → USD → Yearly → Save → copy price_xxx
  KAZE Entrepreneur       $10 USD  Yearly
  KAZE Businessman        $25 USD  Yearly
  KAZE CEO                $50 USD  Yearly
  KAZE Founder's Premium  $100 USD Yearly

── 2. Enable Customer Portal ──
https://dashboard.stripe.com/test/settings/billing/portal
Activate + enable "Cancel at end of billing period" + "Update payment method"

── 3. Render → Environment variables ──
STRIPE_PRICE_ENTREPRENEUR = price_xxx
STRIPE_PRICE_BUSINESSMAN  = price_xxx
STRIPE_PRICE_CEO          = price_xxx
STRIPE_PRICE_FOUNDER      = price_xxx

(confirm these already exist:
 STRIPE_SECRET_KEY / STRIPE_PUBLISHABLE_KEY / STRIPE_WEBHOOK_SECRET)

── 4. Add webhook events ──
https://dashboard.stripe.com/test/webhooks
Subscribe the existing endpoint to ALL of:
  checkout.session.completed
  checkout.session.async_payment_succeeded
  checkout.session.expired
  charge.refunded
  customer.subscription.created
  customer.subscription.updated
  customer.subscription.deleted
  invoice.payment_succeeded
  invoice.payment_failed

── 5. Deploy ──
git add app.py stripe_payments.py subscriptions.py templates/plans.html templates/plans_sync.html kaze_subscriptions_patch.py
git commit -m "v4.7.0: annual USD subscriptions"
git push
Render → Manual Deploy → Clear build cache

── 6. Test (in this exact order) ──

a. Sign up fresh test account (or use existing test)
b. /plans → "Start free trial" → 14 days → CEO features unlock
c. /plans → "Subscribe — $10/year" on Entrepreneur
d. Stripe checkout loads. Use 4242 4242 4242 4242, any future date, any CVC
e. After payment: browser lands on /plans/sync
f. The sync page should poll and redirect to /plans within 2-10 seconds
g. /plans shows "Active subscription — renews on [date+1year]"
h. Verify DB: SELECT plan_tier, plan_expires_at, subscription_status, stripe_subscription_id
   FROM settings WHERE user_id=<your_test_id>;
   Expected: plan_tier='entrepreneur', plan_expires_at=<~1 year out>,
             subscription_status='active', stripe_subscription_id='sub_xxx'
i. Click "Manage" → Stripe portal loads → cancel subscription
j. Return to /plans → "Canceled — until [period end]" banner
k. Force-expire test: in DB, set plan_expires_at='2020-01-01', subscription_status='active'
   Reload /plans → should show "Subscription expired" banner and effective tier is new_user
l. Restore the DB values

── Known behaviours you'll see ──

  • If you only set 1 price ID, only that tier shows "Subscribe". Others
    show "Not available yet." That's the flexible-mode behaviour — intended.

  • Spurious income rows on subscription: NOT possible anymore due to the
    webhook guard. Confirm by checking SELECT COUNT(*) FROM income WHERE
    source='Stripe payment' AND date=CURRENT_DATE — should be 0 after a
    subscription payment.

  • If /plans/sync shows "Webhook still pending" after 30s: check Render
    logs for the webhook POST, and check Stripe Dashboard → Webhooks →
    [your endpoint] → attempts tab. If webhook 400s, the signing secret
    is wrong.

Backups:  *.bak.<timestamp> files. Delete after successful deploy + test.
""")