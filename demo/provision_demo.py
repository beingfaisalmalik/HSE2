"""Run through `odoo shell` in an ISOLATED demo database.

Required secrets are supplied via environment variables, never committed to the
addon. This script intentionally changes branding and login credentials only
when explicitly invoked by the demo bootstrap, not on normal module install.
"""
import os
import base64
from urllib.parse import urlsplit

from odoo import tools


def provision_demo(env, environ):
    required = ('DEMO_ADMIN_PASSWORD', 'DEMO_PRESENTER_PASSWORD', 'DEMO_PORTAL_PASSWORD')
    passwords = {name: environ.get(name, '') for name in required}
    if any(len(value) < 14 or '\n' in value or '\r' in value for value in passwords.values()):
        raise ValueError('Supply all three demo passwords (at least 14 characters; no line breaks).')
    if len(set(passwords.values())) != len(passwords):
        raise ValueError('Use distinct passwords for the three demo accounts.')
    if 'demo' not in env.cr.dbname.lower():
        raise ValueError('Refusing to provision a database whose name does not contain "demo".')
    installed = env['ir.module.module'].search([
        ('name', '=', 'hse_demo_data'), ('state', '=', 'installed')], limit=1)
    if not installed:
        raise ValueError('Install hse_demo_data before provisioning the isolated demo.')

    base_url = environ.get('DEMO_BASE_URL', '').rstrip('/')
    if base_url:
        url = urlsplit(base_url)
        if (url.scheme not in ('http', 'https') or not url.hostname or
                url.username or url.password or url.path or url.query or url.fragment or
                any(character.isspace() for character in base_url)):
            raise ValueError('DEMO_BASE_URL must be a plain HTTP(S) origin, without credentials or a path.')
    with tools.file_open('hse_demo_data/static/demo/northstar_logo.png', 'rb') as source:
        logo = base64.b64encode(source.read())
    with tools.file_open('hse_demo_data/static/demo/northstar_mark.png', 'rb') as source:
        favicon = base64.b64encode(source.read())

    for xmlid, variable in (
        ('base.user_admin', 'DEMO_ADMIN_PASSWORD'),
        ('hse_demo_data.dd_user_presenter', 'DEMO_PRESENTER_PASSWORD'),
        ('hse_demo_data.dd_user_contractor', 'DEMO_PORTAL_PASSWORD'),
    ):
        env.ref(xmlid).with_context(no_reset_password=True).write({'password': passwords[variable]})
    env.ref('base.main_company').write({
        'name': 'Northstar Petrochemicals (Demo)', 'logo': logo,
        'email': 'info@northstar.example', 'phone': '+1 202-555-0100',
        'street': '100 Demo Process Avenue', 'city': 'Northstar Demo City',
    })
    env['website'].search([], limit=1).write({'name': 'Northstar HSE Demo',
                                            'homepage_url': '/hse/demo/welcome',
                                            'favicon': favicon})
    parameters = env['ir.config_parameter'].sudo()
    if base_url:
        parameters.set_param('web.base.url', base_url)
        parameters.set_param('web.base.url.freeze', True)
    if 'DEMO_PREVIEW_EMBEDDED' in environ:
        parameters.set_param('hse_demo_data.preview_partitioned_sessions',
                             environ['DEMO_PREVIEW_EMBEDDED'].lower() in ('1', 'true'))
    # Only the server-side PDF worker uses this URL; browser assets are relative.
    parameters.set_param('report.url', 'http://127.0.0.1:8069')
    env.cr.commit()
    print('Demo provisioned. Logins: hse.presenter and hse.contractor. Passwords are in your private .env.')


if 'env' in globals():  # Odoo shell injects this environment.
    provision_demo(env, os.environ)
