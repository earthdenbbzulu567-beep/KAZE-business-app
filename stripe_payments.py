"""Stripe Checkout helpers for KAZE. Card numbers never touch this app."""

import os

ZERO_DECIMAL = {
    'BIF', 'CLP', 'DJF', 'GNF', 'JPY', 'KMF', 'KRW', 'MGA',
    'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF',
}

THREE_DECIMAL = {'BHD', 'JOD', 'KWD', 'OMR', 'TND'}


def stripe_available():
    try:
        import stripe  # noqa: F401
        return True
    except Exception:
        return False


def keys_from(settings=None):
    settings = settings or {}
    secret = (os.environ.get('STRIPE_SECRET_KEY') or '').strip()
    publishable = (os.environ.get('STRIPE_PUBLISHABLE_KEY') or '').strip()
    webhook = (os.environ.get('STRIPE_WEBHOOK_SECRET') or '').strip()
    if not secret:
        secret = str(settings.get('stripe_secret_key') or '').strip()
    if not publishable:
        publishable = str(settings.get('stripe_publishable_key') or '').strip()
    if not webhook:
        webhook = str(settings.get('stripe_webhook_secret') or '').strip()
    return secret, publishable, webhook


def stripe_ready(settings=None):
    secret, publishable, _ = keys_from(settings)
    return bool(secret and publishable and stripe_available())


def currency_code(settings=None):
    code = ''
    if settings:
        code = str(settings.get('currency_code') or '').strip()
    code = (code or os.environ.get('STRIPE_CURRENCY') or 'USD').upper()
    if len(code) != 3:
        code = 'USD'
    return code


def to_stripe_amount(amount, currency='USD'):
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0.0
    if value <= 0:
        return 0
    cur = (currency or 'USD').upper()
    if cur in ZERO_DECIMAL:
        return int(round(value))
    if cur in THREE_DECIMAL:
        return int(round(value * 1000))
    return int(round(value * 100))


def from_stripe_amount(units, currency='USD'):
    try:
        units = int(units or 0)
    except (TypeError, ValueError):
        units = 0
    cur = (currency or 'USD').upper()
    if cur in ZERO_DECIMAL:
        return float(units)
    if cur in THREE_DECIMAL:
        return units / 1000.0
    return units / 100.0


def create_checkout(settings, *, amount, title, success_url, cancel_url, metadata):
    secret, _, _ = keys_from(settings)
    if not secret:
        return None, 'Stripe secret key is not set. Add it in Settings or as STRIPE_SECRET_KEY.'
    if not stripe_available():
        return None, 'The stripe package is not installed. Add stripe to requirements and redeploy.'
    import stripe
    stripe.api_key = secret
    currency = currency_code(settings)
    units = to_stripe_amount(amount, currency)
    if units <= 0:
        return None, 'Amount must be greater than zero.'
    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=[{
                'quantity': 1,
                'price_data': {
                    'currency': currency.lower(),
                    'unit_amount': units,
                    'product_data': {'name': (title or 'KAZE payment')[:120]},
                },
            }],
            metadata={str(k): str(v)[:500] for k, v in (metadata or {}).items()},
        )
        return session, None
    except Exception as exc:
        return None, 'Stripe could not start checkout: {}'.format(exc)


def parse_webhook(payload, sig_header, settings=None):
    _, _, webhook = keys_from(settings)
    if not stripe_available():
        return None, 'stripe package missing'
    import stripe
    if not webhook:
        return None, 'STRIPE_WEBHOOK_SECRET is not set.'
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook)
        return event, None
    except Exception as exc:
        return None, str(exc)
