"""The real authenticated demo pages and downloads must work in Odoo."""
import csv
import io

from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestHSEClientDemoHTTP(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.presenter = cls.env.ref('hse_demo_data.dd_user_presenter')
        cls.contractor = cls.env.ref('hse_demo_data.dd_user_contractor')
        cls.password = 'HSE-Test-Only-2026!'
        for user in (cls.presenter, cls.contractor):
            user.with_context(no_reset_password=True).write({'password': cls.password})

    def test_public_welcome_has_no_business_data(self):
        response = self.url_open('/hse/demo/welcome')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Your client demo starts here.', response.text)
        self.assertIn('Presenter experience', response.text)
        self.assertIn('Frontline experience', response.text)
        self.assertNotIn('class="module-card"', response.text)
        self.assertNotIn('Overdue corrective actions', response.text)
        self.assertNotIn(self.env.ref('hse_demo_data.dd_inc_lti1').name, response.text)

    def test_hosted_preview_sign_in_escapes_the_cookie_blocked_frame(self):
        parameters = self.env['ir.config_parameter'].sudo()
        parameters.set_param('hse_demo_data.preview_partitioned_sessions', True)
        parameters.set_param('web.base.url', 'https://8069-demo.e2b.app')
        response = self.url_open('/hse/demo/welcome', headers={'Host': '8069-demo.e2b.app'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Secure sign-in opens in a new tab.', response.text)
        self.assertEqual(response.text.count('target="_blank"'), 2)
        self.assertEqual(response.text.count('rel="noopener noreferrer"'), 2)
        # Merely enabling preview mode must not change ordinary localhost access.
        response = self.url_open('/hse/demo/welcome')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Secure sign-in opens in a new tab.', response.text)
        self.assertNotIn('target="_blank"', response.text)

    def test_anonymous_requests_require_login(self):
        response = self.url_open('/hse/demo')
        self.assertEqual(response.status_code, 200)
        self.assertIn('/web/login', response.url)
        self.assertNotIn('Safer operations.', response.text)

    def test_presenter_hub_dashboard_and_downloads(self):
        self.authenticate(self.presenter.login, self.password)
        response = self.url_open('/hse/demo')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Eight journeys.', response.text)
        self.assertIn('Northstar', response.text)
        self.assertEqual(response.text.count('class="module-card"'), 73)
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('no-store', response.headers['Cache-Control'])
        data_response = self.url_open('/hse/dashboard/data')
        self.assertEqual(data_response.status_code, 200)
        data = data_response.json()
        self.assertEqual(data['total_barriers'], 4)
        self.assertGreater(sum(cell['count'] for row in data['matrix_grid'] for cell in row), 0)
        guide = self.url_open('/hse/demo/guide')
        self.assertEqual(guide.status_code, 200)
        self.assertIn('text/markdown', guide.headers['Content-Type'])
        self.assertIn('attachment', guide.headers['Content-Disposition'])
        self.assertIn('PSSR', guide.text)
        coverage = self.url_open('/hse/demo/coverage.csv')
        self.assertEqual(coverage.status_code, 200)
        rows = list(csv.reader(io.StringIO(coverage.text)))
        self.assertEqual(len(rows), 74)
        self.assertTrue(all(row[-1] == 'Yes' for row in rows[1:]))

    def test_portal_cannot_read_presenter_pages_or_downloads(self):
        self.authenticate(self.contractor.login, self.password)
        for path in ('/hse/demo', '/hse/demo/guide', '/hse/demo/coverage.csv'):
            response = self.url_open(path)
            self.assertEqual(response.status_code, 403, path)
            self.assertNotIn('class="module-card"', response.text)
        response = self.url_open('/hse/portal/my-submissions')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Air hose crosses', response.text)
        self.assertIn('Loose staging strap', response.text)
