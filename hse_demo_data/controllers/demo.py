import csv
import io

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request
from odoo.addons.hse.controllers.hse_dashboard_controller import HSEDashboardController

from ..services import build_demo_context, build_walkthrough
from ..models.preview_http import PREVIEW_COOKIE_PARAMETER, preview_cookie_scope
from .. import browser_access


class HSEClientDemo(http.Controller):
    def _check_presenter(self):
        user = request.env.user
        if not (request.env.is_admin() or user.has_group('hse_demo_data.group_demo_presenter')):
            raise Forbidden('The client demo is restricted to authorized demo presenters.')

    @http.route('/hse/demo/welcome', type='http', auth='public', methods=['GET'], website=False)
    def demo_welcome(self, **kwargs):
        # Static orientation only: never expose catalog counts or business
        # records to the public user, and never log anyone in automatically.
        if request.session.uid:
            user = request.env.user
            target = '/hse/demo' if (request.env.is_admin() or
                user.has_group('hse_demo_data.group_demo_presenter')) else '/hse/portal'
            return request.redirect(target)
        parameters = request.env['ir.config_parameter'].sudo()
        enabled = parameters.get_param(PREVIEW_COOKIE_PARAMETER, 'False').lower() in ('true', '1')
        cookie_free = browser_access.enabled(request.env)
        separate_sign_in = not cookie_free and preview_cookie_scope(
            enabled, request.httprequest.scheme, request.httprequest.host_url,
            parameters.get_param('web.base.url', '') if enabled else '',
        )
        return request.render('hse_demo_data.client_demo_welcome',
                              {'separate_sign_in': separate_sign_in, 'cookie_free': cookie_free},
                              headers=[('Cache-Control', 'no-store')])

    @http.route('/hse/demo', type='http', auth='user', methods=['GET'], website=False)
    def demo_home(self, **kwargs):
        self._check_presenter()
        context = build_demo_context(request.env)
        context['kpis'] = HSEDashboardController()._collect_dashboard_data()
        return request.render('hse_demo_data.client_demo', context, headers=[('Cache-Control', 'no-store')])

    @http.route('/hse/demo/guide', type='http', auth='user', methods=['GET'], website=False)
    def demo_guide(self, **kwargs):
        self._check_presenter()
        content = build_walkthrough(build_demo_context(request.env))
        return request.make_response(content, headers=[
            ('Content-Type', 'text/markdown; charset=utf-8'),
            ('Content-Disposition', 'attachment; filename="HSE_CLIENT_WALKTHROUGH.md"'),
            ('Cache-Control', 'no-store'),
        ])

    @http.route('/hse/demo/coverage.csv', type='http', auth='user', methods=['GET'], website=False)
    def demo_coverage(self, **kwargs):
        self._check_presenter()
        context = build_demo_context(request.env)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Category', 'Module', 'Model', 'Records', 'Sample external ID', 'Ready'])
        for item in context['modules']:
            writer.writerow([item['category_title'], item['title'], item['model'], item['count'],
                             item['sample'], 'Yes' if item['ready'] else 'No'])
        return request.make_response(output.getvalue(), headers=[
            ('Content-Type', 'text/csv; charset=utf-8'),
            ('Content-Disposition', 'attachment; filename="HSE_DEMO_COVERAGE.csv"'),
            ('Cache-Control', 'no-store'),
        ])
