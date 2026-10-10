"""Opt-in transport compatibility for HTTPS, cross-site Arena preview frames.

Authentication and CSRF checks are unchanged. Session transport and framing are
adjusted only for HTTPS *.e2b.app previews after an operator opts in. Framing is
limited to Arena HTTPS hosts. Ordinary deployments retain standard Odoo policy.
"""
from urllib.parse import urlsplit

import json

from werkzeug.exceptions import Forbidden

from odoo import models, http
from odoo.http import request

from .. import browser_access


PREVIEW_COOKIE_PARAMETER = 'hse_demo_data.preview_partitioned_sessions'


def preview_cookie_scope(enabled, scheme, host_url, public_url=''):
    host = (urlsplit(host_url).hostname or '').lower()
    declared = urlsplit(public_url)
    # Some preview proxies omit X-Forwarded-Host, so Odoo sees upstream HTTP.
    # Trust only the explicitly configured HTTPS origin matching this host.
    tls = scheme == 'https' or (declared.scheme == 'https' and declared.hostname == host)
    return bool(enabled) and tls and host.endswith('.e2b.app')


def partition_session_cookies(response):
    cookies = []
    for cookie in response.headers.getlist('Set-Cookie'):
        if cookie.startswith('session_id='):
            parts = [part for part in cookie.split(';')
                     if part.strip().split('=', 1)[0].lower() not in
                     ('samesite', 'secure', 'partitioned')]
            cookie = ';'.join(parts) + '; SameSite=None; Secure; Partitioned'
        cookies.append(cookie)
    response.headers.setlist('Set-Cookie', cookies)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        transport = browser_access.enabled(request.env)
        incoming = request.httprequest
        if transport:
            token = incoming.headers.get(browser_access.HEADER)
            challenge = incoming.headers.get(browser_access.CHALLENGE_HEADER)
            if token:
                browser_access.restore(request.env, token)
            elif challenge:
                # An anonymous login challenge cannot authorize another route.
                if incoming.path != '/web/login' or incoming.method != 'POST':
                    raise Forbidden('The sign-in challenge is only valid for login.')
                if incoming.form.get('login') not in ('hse.presenter', 'hse.contractor'):
                    raise Forbidden('Use a fictional demo account for preview sign-in.')
                browser_access.restore(request.env, challenge, 'challenge')
            elif (incoming.method == 'GET' and
                  (endpoint.routing.get('auth') == 'user' or incoming.path in ('/web', '/odoo')) and
                  not request.session.uid and request.dispatcher.routing_type == 'http'):
                # Full navigation/refresh cannot carry custom headers. Recover
                # from this tab's token, not from IP or a shared global login.
                from werkzeug.exceptions import abort
                abort(browser_access.recovery_page())
        super()._authenticate(endpoint)

    @classmethod
    def _post_dispatch(cls, response):
        super()._post_dispatch(response)
        incoming = request.httprequest
        if browser_access.enabled(request.env):
            if getattr(request, 'hse_browser_challenge', False) and request.session.uid:
                # Native password authentication and native CSRF have succeeded.
                if request.session.uid not in browser_access.allowed_ids(request.env):
                    request.session.logout(keep_db=True)
                    raise Forbidden('Use a fictional demo account for preview sign-in.')
                token = browser_access.issue(request.env, request.session)
                target = '/hse/demo' if request.session.uid == request.env.ref(
                    'hse_demo_data.dd_user_presenter').id else '/hse/portal'
                response.status_code = 200
                response.headers.pop('Location', None)
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                response.headers['Cache-Control'] = 'no-store'
                response.set_data(json.dumps({'token': token, 'next': target}))
            elif incoming.path == '/web/login' and not request.session.uid:
                http.root.session_store.save(request.session)
                browser_access.inject(response, browser_access.issue(request.env, request.session, 'challenge'))
            elif getattr(request, 'hse_browser_session', False):
                # Native logout revokes the stored Odoo session as usual.
                if request.session.uid:
                    response.headers[browser_access.HEADER] = browser_access.issue(request.env, request.session)
                    browser_access.inject(response)
                response.headers['Cache-Control'] = 'no-store'
        parameters = request.env['ir.config_parameter'].sudo()
        enabled = parameters.get_param(PREVIEW_COOKIE_PARAMETER, 'False').lower() in ('true', '1')
        public_url = parameters.get_param('web.base.url', '') if enabled else ''
        if preview_cookie_scope(enabled, incoming.scheme, incoming.host_url, public_url):
            partition_session_cookies(response)
            if response.headers.get('Content-Type', '').startswith('text/html'):
                # Odoo's standard login/backend forbid cross-site framing.
                # Allow only Arena's HTTPS hosts for this opted-in preview.
                response.headers.pop('X-Frame-Options', None)
                policy = response.headers.get('Content-Security-Policy', '')
                directives = [item.strip() for item in policy.split(';') if item.strip() and
                              not item.strip().startswith('frame-ancestors')]
                directives.append("frame-ancestors 'self' https://arena.ai:* https://*.arena.ai:*")
                response.headers['Content-Security-Policy'] = '; '.join(directives)
