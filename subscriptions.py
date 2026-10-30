"""
subscriptions.py — Stripe Subscriptions for KAZE.

Handles:
  - Stripe Checkout in subscription mode
  - Webhook events for subscription lifecycle
  - Customer Portal for self-service management
  - Source of truth for plan_expires_at

Card data never touches this app.
"""

import os
from datetime import datetime

# ── Price IDs ───────────────────────────────────────────────────────
# Set these as environment variables on your host:
#   STRIPE_PRICE_ENTREPRENEUR=price_xxx
#   STRIPE_PRICE_BUSINESSMAN=price_xxx
#   STRIPE_PRICE_CEO=price_xxx
#   STRIPE_PRICE_FOUNDER=price_xxx

_TIER_ENV = {
    'entrepreneur': 'STRIPE_PRICE_ENTREPRENEUR',
    'businessman':  'STRIPE_PRICE_BUSINESSMAN',
    'ceo':          'STRIPE_PRICE_CEO',
    'founder':      'STRIPE_PRICE_FOUNDER',
}


def price_id_for(tier):
    env = _TIER_ENV.get((tier or '').lower())
    if not env:
        return ''
    return (os.environ.get(env) or '').strip()


def subs_ready():
    """True if AT LEAST ONE tier price ID is configured.
    Per-tier availability is checked separately with price_id_for()."""
    return any(price_id_for(t) for t in _TIER_ENV)


def configured_tiers():
    """List of tier keys with a configured Stripe price ID."""
    return [t for t in _TIER_ENV if price_id_for(t)]


def missing_prices():
    return [t for t in _TIER_ENV if not price_id_for(t)]


# ── Stripe helpers ──────────────────────────────────────────────────

def _stripe():
    try:
        import stripe
        return stripe
    except Exception:
        return None


def _secret(settings):
    import stripe_payments
    secret, _, _ = stripe_payments.keys_from(settings)
    return secret


def _unix_to_iso(ts):
    try:
        return datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d')
    except (TypeError, ValueError):
        return datetime.today().strftime('%Y-%m-%d')


def _first_period_end(sub_obj):
    """Return unix timestamp of the current period end, or a sane fallback.

    Stripe moved current_period_end between API versions:
      - Older: at sub.current_period_end
      - 2025-03-31+: at sub.items.data[0].current_period_end
    Some events (or future API versions) may not include it at all.
    In that case, fall back to +365 days (all KAZE plans are yearly).
    """
    if sub_obj:
        items = sub_obj.get('items') or {}
        data = items.get('data') or []
        if data:
            end = data[0].get('current_period_end')
            if end:
                return int(end)
        end = sub_obj.get('current_period_end')
        if end:
            return int(end)
    # Sane fallback: +365 days from now (all KAZE plans are yearly).
    import sys as _sys
    import time as _time
    _sys.stderr.write(
        'KAZE WARN: _first_period_end could not find current_period_end; '
        'falling back to now+365 days\n'
    )
    return int(_time.time()) + 365 * 86400


# ── Customer + Checkout ─────────────────────────────────────────────

def get_or_create_customer(settings, user_id, email, username):
    stripe = _stripe()
    secret = _secret(settings)
    if not stripe or not secret:
        return None, 'Stripe is not configured.'
    stripe.api_key = secret
    existing = (settings or {}).get('stripe_customer_id') or ''
    if existing:
        return existing, None
    try:
        customer = stripe.Customer.create(
            email=email or None,
            name=username or None,
            metadata={'user_id': str(user_id)},
        )
        return customer.id, None
    except Exception as exc:
        return None, str(exc)[:220]


def create_subscription_checkout(settings, tier, customer_id, user_id,
                                 success_url, cancel_url):
    stripe = _stripe()
    secret = _secret(settings)
    if not stripe or not secret:
        return None, 'Stripe is not configured.'
    price_id = price_id_for(tier)
    if not price_id:
        return None, 'Package "%s" is not available for subscription yet.' % tier
    stripe.api_key = secret
    try:
        session = stripe.checkout.Session.create(
            mode='subscription',
            customer=customer_id,
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user_id),
                'tier': tier,
                'source': 'kaze_subscription',
            },
            subscription_data={
                'metadata': {
                    'user_id': str(user_id),
                    'tier': tier,
                },
            },
            managed_payments={'enabled': False},
            allow_promotion_codes=True,
        )
        return session, None
    except Exception as exc:
        return None, str(exc)[:300]


def create_portal_session(settings, customer_id, return_url):
    stripe = _stripe()
    secret = _secret(settings)
    if not stripe or not secret:
        return None, 'Stripe is not configured.'
    if not customer_id:
        return None, 'No active Stripe customer for this account.'
    stripe.api_key = secret
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session, None
    except Exception as exc:
        return None, str(exc)[:220]


# ── Webhook handlers ────────────────────────────────────────────────

def _find_user(get_db, by='customer', value=''):
    if not value:
        return None
    conn = get_db()
    cur = conn.cursor()
    col = 'stripe_customer_id' if by == 'customer' else 'stripe_subscription_id'
    cur.execute('SELECT user_id FROM settings WHERE %s=%%s LIMIT 1' % col, (value,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return int(row['user_id']) if row else None


def _find_user_from_meta(get_db, meta):
    try:
        uid = int((meta or {}).get('user_id') or 0)
    except (TypeError, ValueError):
        uid = 0
    return uid if uid else None


def handle_subscription_created(get_db, event):
    sub = event['data']['object']
    sub_id = sub.get('id')
    customer_id = sub.get('customer')
    meta = sub.get('metadata') or {}
    tier = (meta.get('tier') or '').lower()
    if tier not in _TIER_ENV:
        return
    user_id = _find_user(get_db, 'customer', customer_id) or _find_user_from_meta(get_db, meta)
    if not user_id:
        return
    period_end = _first_period_end(sub)
    expires_iso = _unix_to_iso(period_end)
    started_iso = datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE settings SET
            plan_tier=%s,
            plan_started_at=%s,
            plan_expires_at=%s,
            stripe_subscription_id=%s,
            stripe_customer_id=%s,
            subscription_status='active',
            grace_expires_at=''
        WHERE user_id=%s
    ''', (tier, started_iso, expires_iso, sub_id, customer_id, user_id))
    cur.execute("SELECT plan_paid_rank FROM settings WHERE user_id=%s", (user_id,))
    row = cur.fetchone() or {}
    try:
        prior_rank = int(row.get('plan_paid_rank') or 0)
    except (TypeError, ValueError):
        prior_rank = 0
    from app import PLAN_RANK
    new_rank = max(prior_rank, PLAN_RANK.get(tier, 0))
    cur.execute('UPDATE settings SET plan_paid_rank=%s WHERE user_id=%s', (new_rank, user_id))
    conn.commit()
    cur.close()
    conn.close()


def handle_subscription_updated(get_db, event):
    sub = event['data']['object']
    sub_id = sub.get('id')
    status = (sub.get('status') or '').lower()
    user_id = _find_user(get_db, 'subscription', sub_id)
    if not user_id:
        return
    period_end = _first_period_end(sub)
    expires_iso = _unix_to_iso(period_end)
    mapped = {
        'active': 'active',
        'trialing': 'active',
        'past_due': 'past_due',
        'unpaid': 'past_due',
        'canceled': 'canceled',
        'incomplete': 'past_due',
        'incomplete_expired': 'canceled',
    }.get(status, status or 'none')
    conn = get_db()
    cur = conn.cursor()
    if mapped == 'active':
        cur.execute('''
            UPDATE settings SET
                plan_expires_at=%s,
                subscription_status=%s,
                grace_expires_at=''
            WHERE user_id=%s
        ''', (expires_iso, mapped, user_id))
    else:
        cur.execute('UPDATE settings SET subscription_status=%s WHERE user_id=%s',
                    (mapped, user_id))
    conn.commit()
    cur.close()
    conn.close()


def handle_subscription_deleted(get_db, event):
    sub = event['data']['object']
    sub_id = sub.get('id')
    user_id = _find_user(get_db, 'subscription', sub_id)
    if not user_id:
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE settings SET subscription_status='canceled' WHERE user_id=%s",
                (user_id,))
    conn.commit()
    cur.close()
    conn.close()


def handle_invoice_succeeded(get_db, event):
    inv = event['data']['object']
    sub_id = inv.get('subscription')
    customer_id = inv.get('customer')
    # Skip non-subscription invoices (those are handled by
    # checkout.session.completed / _fulfill_stripe_payment)
    if not sub_id:
        return
    user_id = _find_user(get_db, 'subscription', sub_id)
    if not user_id:
        user_id = _find_user(get_db, 'customer', customer_id)
    if not user_id:
        return
    period_end = inv.get('period_end')
    if not period_end:
        try:
            period_end = inv['lines']['data'][0]['period']['end']
        except (KeyError, IndexError, TypeError):
            import time as _time
            period_end = int(_time.time()) + 365 * 86400
    expires_iso = _unix_to_iso(period_end)
    today_iso = datetime.today().strftime('%Y-%m-%d')

    # Extract invoice details for /payments log
    inv_id = inv.get('id') or ''
    pi_id = inv.get('payment_intent') or ''
    try:
        amount_raw = float(inv.get('amount_paid') or inv.get('total') or 0)
    except (TypeError, ValueError):
        amount_raw = 0.0
    currency = (inv.get('currency') or 'usd').upper()
    import stripe_payments as _sp
    amount_display = _sp.from_stripe_amount(int(amount_raw), currency)
    title = ''
    try:
        lines = inv['lines']['data']
        if lines:
            title = (lines[0].get('description') or '')[:160]
    except (KeyError, IndexError, TypeError):
        title = ''
    if not title:
        title = 'KAZE subscription'

    conn = get_db()
    cur = conn.cursor()

    # 1. Extend plan_expires_at (existing behavior)
    cur.execute("""
        UPDATE settings SET
            plan_expires_at=%s,
            subscription_status='active',
            grace_expires_at=''
        WHERE user_id=%s
    """, (expires_iso, user_id))

    # 2. Record the payment in stripe_payments (idempotent by invoice_id)
    if inv_id:
        cur.execute(
            "SELECT id FROM stripe_payments WHERE user_id=%s AND invoice_id=%s LIMIT 1",
            (user_id, inv_id))
        existing = cur.fetchone()
        if not existing:
            cur.execute(
                "INSERT INTO stripe_payments "
                "(user_id, kind, record_id, amount, currency, status, "
                " checkout_id, payment_intent, invoice_id, title, "
                " provider, created_date, paid_date) "
                "VALUES (%s, 'subscription', 0, %s, %s, 'paid', "
                " %s, %s, %s, %s, 'stripe', %s, %s)",
                (user_id, amount_display, currency,
                 inv_id, pi_id, inv_id, title,
                 today_iso, today_iso))

    conn.commit()
    cur.close()
    conn.close()



def handle_invoice_failed(get_db, event):
    inv = event['data']['object']
    sub_id = inv.get('subscription')
    customer_id = inv.get('customer')
    user_id = _find_user(get_db, 'subscription', sub_id) if sub_id else None
    if not user_id:
        user_id = _find_user(get_db, 'customer', customer_id)
    if not user_id:
        return
    from datetime import timedelta
    grace_iso = (datetime.today() + timedelta(days=3)).strftime('%Y-%m-%d')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE settings SET
            subscription_status='past_due',
            grace_expires_at=%s
        WHERE user_id=%s
    ''', (grace_iso, user_id))
    conn.commit()
    cur.close()
    conn.close()


def handle_webhook(get_db, event):
    etype = event.get('type') or ''
    if etype == 'customer.subscription.created':
        handle_subscription_created(get_db, event)
    elif etype == 'customer.subscription.updated':
        handle_subscription_updated(get_db, event)
    elif etype == 'customer.subscription.deleted':
        handle_subscription_deleted(get_db, event)
    elif etype == 'invoice.payment_succeeded':
        handle_invoice_succeeded(get_db, event)
    elif etype == 'invoice.payment_failed':
        handle_invoice_failed(get_db, event)
    return ('', 200)