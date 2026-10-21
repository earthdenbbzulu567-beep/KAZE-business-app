"""OAuth sign-in for KAZE: Google, Yahoo, X (Twitter), Microsoft.

Client ids and secrets come from environment variables. Card and mailbox
contents are not pulled — only the provider user id, email, and display name
needed to open or link a KAZE login.
"""

import base64
import hashlib
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request

PROVIDERS = {
    'google': {
        'label': 'Google',
        'auth': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token': 'https://oauth2.googleapis.com/token',
        'userinfo': 'https://openidconnect.googleapis.com/v1/userinfo',
        'scope': 'openid email profile',
        'id_env': 'GOOGLE_CLIENT_ID',
        'secret_env': 'GOOGLE_CLIENT_SECRET',
        'extra_auth': {'access_type': 'online', 'prompt': 'select_account'},
    },
    'yahoo': {
        'label': 'Yahoo',
        'auth': 'https://api.login.yahoo.com/oauth2/request_auth',
        'token': 'https://api.login.yahoo.com/oauth2/get_token',
        'userinfo': 'https://api.login.yahoo.com/openid/v1/userinfo',
        'scope': 'openid email profile',
        'id_env': 'YAHOO_CLIENT_ID',
        'secret_env': 'YAHOO_CLIENT_SECRET',
        'basic': True,
    },
    'x': {
        'label': 'X',
        'auth': 'https://twitter.com/i/oauth2/authorize',
        'token': 'https://api.twitter.com/2/oauth2/token',
        'userinfo': 'https://api.twitter.com/2/users/me',
        'scope': 'tweet.read users.read offline.access',
        'id_env': 'X_CLIENT_ID',
        'secret_env': 'X_CLIENT_SECRET',
        'pkce': True,
        'basic': True,
        'userinfo_fields': 'user.fields=id,name,username',
    },
    'microsoft': {
        'label': 'Microsoft',
        'auth': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        'token': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        'userinfo': 'https://graph.microsoft.com/oidc/userinfo',
        'scope': 'openid email profile',
        'id_env': 'MICROSOFT_CLIENT_ID',
        'secret_env': 'MICROSOFT_CLIENT_SECRET',
    },
}


def _env(name):
    return (os.environ.get(name) or '').strip()


def keys(provider):
    spec = PROVIDERS.get(provider) or {}
    return _env(spec.get('id_env') or ''), _env(spec.get('secret_env') or '')


def ready(provider):
    client_id, secret = keys(provider)
    return bool(client_id and secret)


def ready_list():
    return [key for key in PROVIDERS if ready(key)]


def _b64url(raw):
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def make_pkce():
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode('ascii')).digest())
    return verifier, challenge


def authorize_url(provider, redirect_uri, state, code_challenge=None):
    spec = PROVIDERS[provider]
    client_id, _ = keys(provider)
    if not client_id:
        return None
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': spec['scope'],
        'state': state,
    }
    if spec.get('pkce') and code_challenge:
        params['code_challenge'] = code_challenge
        params['code_challenge_method'] = 'S256'
    params.update(spec.get('extra_auth') or {})
    return spec['auth'] + '?' + urllib.parse.urlencode(params)


def _post_form(url, data, headers=None):
    body = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_header('Accept', 'application/json')
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode('utf-8') or '{}'), None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')[:300]
        return None, 'Token request failed ({}): {}'.format(exc.code, detail)
    except Exception as exc:
        return None, str(exc)


def _get_json(url, headers=None):
    req = urllib.request.Request(url, method='GET')
    req.add_header('Accept', 'application/json')
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode('utf-8') or '{}'), None
    except Exception as exc:
        return None, str(exc)


def exchange_code(provider, code, redirect_uri, code_verifier=None):
    spec = PROVIDERS[provider]
    client_id, secret = keys(provider)
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
    }
    headers = {}
    if spec.get('pkce') and code_verifier:
        data['code_verifier'] = code_verifier
    if spec.get('basic'):
        token = base64.b64encode('{}:{}'.format(client_id, secret).encode('utf-8')).decode('ascii')
        headers['Authorization'] = 'Basic {}'.format(token)
    else:
        data['client_secret'] = secret
    return _post_form(spec['token'], data, headers)


def fetch_profile(provider, access_token):
    spec = PROVIDERS[provider]
    url = spec['userinfo']
    if spec.get('userinfo_fields'):
        url = url + '?' + spec['userinfo_fields']
    payload, err = _get_json(url, {'Authorization': 'Bearer ' + access_token})
    if err:
        return None, err
    payload = payload or {}
    if provider == 'x':
        data = payload.get('data') or payload
        xid = str(data.get('id') or '')
        name = (data.get('name') or data.get('username') or 'x-user').strip()
        username = (data.get('username') or name or ('x' + xid))[:40]
        email = 'x_{}@oauth.kaze.invalid'.format(xid or secrets.token_hex(4))
        return {'id': xid, 'email': email, 'name': name, 'username': username}, None
    pid = str(payload.get('sub') or payload.get('id') or payload.get('oid') or '')
    email = (payload.get('email') or payload.get('preferred_username') or '').strip().lower()
    name = (payload.get('name') or payload.get('given_name') or email.split('@')[0] or provider).strip()
    username = (name.replace(' ', '') or provider)[:40]
    if not pid:
        return None, 'The provider did not return a user id.'
    if not email:
        email = '{}_{}@oauth.kaze.invalid'.format(provider, pid)
    return {'id': pid, 'email': email, 'name': name, 'username': username}, None
