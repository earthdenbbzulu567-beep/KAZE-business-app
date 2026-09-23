"""External APIs for KAZE. Timeouts and a short cache keep pages fast."""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 4
QUOTE_TTL = 900
_CACHE = {}


def _cache_get(key):
    row = _CACHE.get(key)
    if not row:
        return None
    ts, value = row
    if time.time() - ts > QUOTE_TTL:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key, value):
    _CACHE[key] = (time.time(), value)
    return value


def http_json(url, method='GET', headers=None, body=None, timeout=TIMEOUT):
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
            raw = resp.read().decode('utf-8', errors='replace')
            return json.loads(raw or '{}'), None
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode('utf-8', errors='replace')[:240]
        except Exception:
            detail = str(exc)
        return None, 'HTTP %s: %s' % (exc.code, detail or exc.reason)
    except Exception as exc:
        return None, str(exc)[:200]


def _setting(settings, env_name, column):
    env = (os.environ.get(env_name) or '').strip()
    if env:
        return env
    if settings:
        return str(settings.get(column) or '').strip()
    return ''


# ---------- Alpha Vantage ----------

def alpha_key(settings=None):
    return _setting(settings, 'ALPHA_VANTAGE_KEY', 'alpha_vantage_key')


def alpha_ready(settings=None):
    return bool(alpha_key(settings))


def quote_price(symbol, settings=None):
    symbol = (symbol or '').strip().upper()
    if not symbol:
        return None, 'Add a ticker first.'
    cached = _cache_get('q:' + symbol)
    if cached is not None:
        return cached, None
    key = alpha_key(settings)
    if not key:
        return None, 'Add an Alpha Vantage key in Settings.'
    url = 'https://www.alphavantage.co/query?' + urllib.parse.urlencode({
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': key,
    })
    payload, err = http_json(url)
    if err:
        return None, err
    note = (payload or {}).get('Note') or (payload or {}).get('Information')
    if note:
        return None, 'Price service is busy. Try again in a minute.'
    quote = (payload or {}).get('Global Quote') or {}
    raw = quote.get('05. price') or quote.get('05.price')
    try:
        price = float(raw)
    except (TypeError, ValueError):
        return None, 'No price for %s.' % symbol
    if price <= 0:
        return None, 'No price for %s.' % symbol
    return _cache_set('q:' + symbol, price), None


def fx_rate(base, quote, settings=None):
    base = (base or 'USD').strip().upper()
    quote = (quote or 'ZMW').strip().upper()
    if base == quote:
        return 1.0, None
    cached = _cache_get('fx:%s:%s' % (base, quote))
    if cached is not None:
        return cached, None
    key = alpha_key(settings)
    if not key:
        return None, 'Add an Alpha Vantage key in Settings.'
    url = 'https://www.alphavantage.co/query?' + urllib.parse.urlencode({
        'function': 'CURRENCY_EXCHANGE_RATE',
        'from_currency': base,
        'to_currency': quote,
        'apikey': key,
    })
    payload, err = http_json(url)
    if err:
        return None, err
    note = (payload or {}).get('Note') or (payload or {}).get('Information')
    if note:
        return None, 'FX service is busy. Try again in a minute.'
    row = (payload or {}).get('Realtime Currency Exchange Rate') or {}
    raw = row.get('5. Exchange Rate')
    try:
        rate = float(raw)
    except (TypeError, ValueError):
        return None, 'No FX rate for %s/%s.' % (base, quote)
    if rate <= 0:
        return None, 'No FX rate for %s/%s.' % (base, quote)
    return _cache_set('fx:%s:%s' % (base, quote), rate), None


# ---------- Flutterwave ----------

def flutterwave_keys(settings=None):
    secret = _setting(settings, 'FLUTTERWAVE_SECRET_KEY', 'flutterwave_secret_key')
    public = _setting(settings, 'FLUTTERWAVE_PUBLIC_KEY', 'flutterwave_public_key')
    hook = _setting(settings, 'FLUTTERWAVE_WEBHOOK_HASH', 'flutterwave_webhook_hash')
    return secret, public, hook


def flutterwave_ready(settings=None):
    secret, public, _ = flutterwave_keys(settings)
    return bool(secret and public)


def create_flutterwave_payment(settings, *, tx_ref, amount, currency, redirect_url,
                               title, customer_name='', customer_email='', meta=None):
    secret, _, _ = flutterwave_keys(settings)
    if not secret:
        return None, 'Flutterwave is not set up yet. Add keys in Settings.'
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0.0
    if value <= 0:
        return None, 'Amount must be greater than zero.'
    code = (currency or 'ZMW').upper()
    if len(code) != 3:
        code = 'ZMW'
    body = {
        'tx_ref': tx_ref,
        'amount': round(value, 2),
        'currency': code,
        'redirect_url': redirect_url,
        'customer': {
            'email': customer_email or 'shop@kaze.local',
            'name': customer_name or 'KAZE customer',
        },
        'customizations': {
            'title': 'KAZE Shop',
            'description': title or 'Shop order',
        },
        'meta': meta or {},
    }
    payload, err = http_json(
        'https://api.flutterwave.com/v3/payments',
        method='POST',
        headers={'Authorization': 'Bearer ' + secret},
        body=body,
    )
    if err:
        return None, err
    data = (payload or {}).get('data') or {}
    link = data.get('link')
    if not link:
        msg = (payload or {}).get('message') or 'Flutterwave did not return a checkout link.'
        return None, msg
    return {'link': link, 'tx_ref': tx_ref}, None


def verify_flutterwave(settings, tx_ref=None, transaction_id=None):
    secret, _, _ = flutterwave_keys(settings)
    if not secret:
        return None, 'Flutterwave is not set up.'
    if transaction_id:
        url = 'https://api.flutterwave.com/v3/transactions/%s/verify' % transaction_id
    elif tx_ref:
        url = 'https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref=' + urllib.parse.quote(str(tx_ref))
    else:
        return None, 'Missing Flutterwave reference.'
    payload, err = http_json(url, headers={'Authorization': 'Bearer ' + secret})
    if err:
        return None, err
    data = (payload or {}).get('data') or {}
    status = str(data.get('status') or '').lower()
    if status not in ('successful', 'success'):
        return None, 'Payment is %s.' % (status or 'unconfirmed')
    return data, None


def flutterwave_hash_ok(settings, header_hash):
    _, _, expected = flutterwave_keys(settings)
    if not expected:
        return True
    return str(header_hash or '') == expected
