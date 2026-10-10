"""Opt-in cookie-independent transport for the isolated client preview.

Tokens are encrypted, expire, travel only in same-origin request headers, and
restore Odoo's normal session. This never grants admin access or skips native
password, session, ACL or CSRF checks. No token is put in a URL.
"""
import base64
import hashlib
import json
from html import escape
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken
from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request


PARAMETER = 'hse_demo_data.preview_header_sessions'
HEADER = 'X-HSE-Demo-Session'
CHALLENGE_HEADER = 'X-HSE-Demo-Challenge'
TTL = 2 * 60 * 60
CHALLENGE_TTL = 5 * 60


def enabled(env):
    # The setting is intentionally independent of cookie/framing compatibility.
    return ('demo' in env.cr.dbname.lower() and
            env['ir.config_parameter'].sudo().get_param(PARAMETER, 'False').lower() in ('1', 'true'))


def cipher(env):
    secret = env['ir.config_parameter'].sudo().get_param('database.secret')
    if not secret:
        raise Forbidden('Demo session transport is not configured.')
    key = hashlib.sha256(('hse-demo-browser-session-v1:' + secret).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def allowed_ids(env):
    return {env.ref('hse_demo_data.dd_user_presenter').id,
            env.ref('hse_demo_data.dd_user_contractor').id}


def issue(env, session, kind='session'):
    if kind == 'session' and session.uid not in allowed_ids(env):
        raise Forbidden('This transport is restricted to the two fictional demo accounts.')
    return cipher(env).encrypt(json.dumps({
        'kind': kind, 'db': env.cr.dbname, 'sid': session.sid,
        'uid': session.uid if kind == 'session' else None,
    }, separators=(',', ':')).encode()).decode()


def decode(env, token, kind='session'):
    try:
        data = json.loads(cipher(env).decrypt(token.encode(), ttl=TTL if kind == 'session' else CHALLENGE_TTL))
        if (data.get('kind') != kind or data.get('db') != env.cr.dbname or
                not http.root.session_store.is_valid_key(data.get('sid', ''))):
            raise ValueError('Invalid session scope')
        if kind == 'session' and data.get('uid') not in allowed_ids(env):
            raise ValueError('Invalid demo identity')
        return data
    except (InvalidToken, ValueError, TypeError, KeyError, AttributeError):
        raise Forbidden('Your demo session expired. Please sign in again.') from None


def restore(env, token, kind='session'):
    data = decode(env, token, kind)
    session = http.root.session_store.get(data['sid'])
    if (session.db != env.cr.dbname or
            (kind == 'session' and session.uid != data['uid']) or
            (kind == 'challenge' and session.uid is not None)):
        raise Forbidden('Your demo session expired. Please sign in again.')
    # Native ir.http._authenticate will validate the session token/password.
    request.session = session
    request.update_env(user=session.uid, context=session.context, su=False)
    request.hse_browser_session = kind == 'session'
    request.hse_browser_challenge = kind == 'challenge'


def recovery_page():
    # Contains no business data or authentication token. The tab supplies its
    # own capability to a fetch request before any protected document is shown.
    return request.make_response('''<!doctype html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Opening HSE demo</title>
<script src="/hse_demo_data/static/src/js/browser_access.js?v=1" data-hse-recover="1" defer></script>
</head><body style="font:16px system-ui;padding:40px;color:#193f30">
<p>Opening your HSE demo session…</p><noscript>Please enable JavaScript to sign in.</noscript>
</body></html>''', headers=[('Content-Type', 'text/html; charset=utf-8'), ('Cache-Control', 'no-store')])


def inject(response, challenge=None):
    if not response.headers.get('Content-Type', '').startswith('text/html'):
        return
    content = response.get_data(as_text=True)
    if not content or '<head' not in content.lower():
        return
    attribute = ' data-hse-challenge="%s"' % escape(challenge, quote=True) if challenge else ''
    script = ('<script src="/hse_demo_data/static/src/js/browser_access.js?v=1"' + attribute + '></script>')
    # Insert before Odoo bundles so fetch/XHR are authenticated from the start.
    end = content.lower().find('>', content.lower().find('<head')) + 1
    response.set_data(content[:end] + script + content[end:])
    response.headers['Cache-Control'] = 'no-store'


def same_origin_target(target):
    url = urlsplit(target)
    return not url.scheme and not url.netloc and target.startswith('/') and not target.startswith('//')
