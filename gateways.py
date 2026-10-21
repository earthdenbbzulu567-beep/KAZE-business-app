"""Payment rails for KAZE. Card numbers never touch this app."""

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

METHODS = (
    ('stripe', 'Card — Visa / Mastercard / Amex', 'Stripe Checkout. Cards stay on Stripe.'),
    ('paypal', 'PayPal', 'PayPal balance or linked card.'),
    ('flutterwave', 'Card / mobile money', 'Visa, Mastercard, and mobile money on Flutterwave.'),
    ('bank', 'Current account / bank transfer', 'Pay from a current or savings account. Mark paid when the deposit lands.'),
)

_paypal_token = {'value': None, 'exp': 0}


def _setting(settings, env_name, column):
    env = (os.environ.get(env_name) or '').strip()
    if env:
        return env
    if settings:
        return str(settings.get(column) or '').strip()
    return ''


def paypal_keys(settings=None):
    client = _setting(settings, 'PAYPAL_CLIENT_ID', 'paypal_client_id')
    secret = _setting(settings, 'PAYPAL_SECRET', 'paypal_secret')
    mode = (_setting(settings, 'PAYPAL_MODE', 'paypal_mode') or 'sandbox').lower()
    if mode not in ('sandbox', 'live'):
        mode = 'sandbox'
    return client, secret, mode


def paypal_ready(settings=None):
    client, secret, _ = paypal_keys(settings)
    return bool(client and secret)


def paypal_base(settings=None):
    _, _, mode = paypal_keys(settings)
    if mode == 'live':
        return 'https://api-m.paypal.com'
    return 'https://api-m.sandbox.paypal.com'


def _http(url, method='GET', headers=None, body=None, timeout=8):
    data = None
    if body is not None:
        data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Accept', 'application/json')
    if body is not None:
        req.add_header('Content-Type', 'application/json')
    for key, val in (headers or {}).items():
        req.add_header(key, val)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8') or '{}'
            return json.loads(raw), None
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode('utf-8') or '{}')
        except Exception:
            payload = {}
        msg = payload.get('message') or payload.get('error_description') or payload.get('name') or str(exc)
        return payload, str(msg)[:220]
    except Exception as exc:
        return None, str(exc)[:220]


def paypal_token(settings=None):
    now = time.time()
    if _paypal_token['value'] and now < _paypal_token['exp']:
        return _paypal_token['value'], None
    client, secret, _ = paypal_keys(settings)
    if not client or not secret:
        return None, 'PayPal is not set up yet. Add the client id and secret in Settings.'
    raw = base64.b64encode(('%s:%s' % (client, secret)).encode('utf-8')).decode('ascii')
    req = urllib.request.Request(
        paypal_base(settings) + '/v1/oauth2/token',
        data=b'grant_type=client_credentials',
        method='POST',
        headers={
            'Authorization': 'Basic ' + raw,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode('utf-8') or '{}')
    except Exception as exc:
        return None, 'PayPal login failed: %s' % str(exc)[:160]
    token = payload.get('access_token')
    if not token:
        return None, payload.get('error_description') or 'PayPal did not return a token.'
    expires = int(payload.get('expires_in') or 300)
    _paypal_token['value'] = token
    _paypal_token['exp'] = now + max(60, expires - 60)
    return token, None


def paypal_create_order(settings, *, amount, currency, title, return_url, cancel_url, custom_id):
    token, err = paypal_token(settings)
    if err:
        return None, err
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0.0
    if value <= 0:
        return None, 'Amount must be greater than zero.'
    code = (currency or 'USD').upper()
    if len(code) != 3:
        code = 'USD'
    body = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'custom_id': str(custom_id or '')[:127],
            'description': (title or 'KAZE payment')[:127],
            'amount': {'currency_code': code, 'value': '%.2f' % value},
        }],
        'application_context': {
            'brand_name': 'KAZE',
            'user_action': 'PAY_NOW',
            'return_url': return_url,
            'cancel_url': cancel_url,
        },
    }
    payload, err = _http(
        paypal_base(settings) + '/v2/checkout/orders',
        method='POST',
        headers={'Authorization': 'Bearer ' + token},
        body=body,
    )
    if err and not (payload or {}).get('id'):
        return None, err
    order_id = (payload or {}).get('id')
    approve = ''
    for link in (payload or {}).get('links') or []:
        if link.get('rel') == 'approve':
            approve = link.get('href') or ''
            break
    if not order_id or not approve:
        return None, 'PayPal did not return an approval link.'
    return {'id': order_id, 'url': approve}, None


def paypal_capture(settings, order_id):
    token, err = paypal_token(settings)
    if err:
        return None, err
    order_id = (order_id or '').strip()
    if not order_id:
        return None, 'Missing PayPal order.'
    payload, err = _http(
        paypal_base(settings) + '/v2/checkout/orders/%s/capture' % urllib.parse.quote(order_id),
        method='POST',
        headers={'Authorization': 'Bearer ' + token},
        body={},
    )
    if err and str((payload or {}).get('status') or '').upper() not in ('COMPLETED', 'APPROVED'):
        return payload, err
    return payload, None


def bank_details(settings=None):
    settings = settings or {}
    return {
        'bank_name': _setting(settings, 'BANK_NAME', 'bank_name'),
        'account_name': _setting(settings, 'BANK_ACCOUNT_NAME', 'bank_account_name'),
        'account_number': _setting(settings, 'BANK_ACCOUNT_NUMBER', 'bank_account_number'),
        'branch': _setting(settings, 'BANK_BRANCH', 'bank_branch'),
    }


def bank_ready(settings=None):
    info = bank_details(settings)
    return bool(info['account_number'] and (info['bank_name'] or info['account_name']))


def ready_methods(settings=None):
    import stripe_payments
    import integrations
    flags = {
        'stripe': stripe_payments.stripe_ready(settings),
        'paypal': paypal_ready(settings),
        'flutterwave': integrations.flutterwave_ready(settings),
        'bank': bank_ready(settings),
    }
    rows = []
    for key, label, hint in METHODS:
        rows.append({'key': key, 'label': label, 'hint': hint, 'ready': bool(flags.get(key))})
    return rows


def default_method(settings=None):
    for row in ready_methods(settings):
        if row['ready']:
            return row['key']
    return ''
