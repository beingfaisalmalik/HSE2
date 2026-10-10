"""The native date-filtered reports must include the entire selected end day."""
from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.hse.tools.report_dates import date_range_domain


@tagged('post_install', '-at_install')
class TestHSEClientSummaryReports(TransactionCase):
    def test_all_six_parameterized_reports_render_real_rows(self):
        presenter = self.env.ref('hse_demo_data.dd_user_presenter')
        env = self.env(user=presenter, context=dict(self.env.context, tz='UTC'))
        day = fields.Date.today()
        cases = [
            ('hse.wizard.report', 'dd_jsa_1'),
            ('observation.wizard', 'dd_obs_1'),
            ('incident.reporting.wizard', 'dd_inc_lti1'),
            ('incident.investigation.wizard', 'dd_inv_lti1'),
            ('capa.wizard', 'dd_legacy_capa'),
        ]
        for model, sample in cases:
            wizard = env[model].create({'start_date': day, 'end_date': day})
            action = wizard.printhsereport()
            record = env.ref('hse_demo_data.' + sample)
            self.assertIn(record.id, action['data']['data'], model)
            content, fmt = env['ir.actions.report']._render_qweb_html(
                action['report_name'], wizard.ids, data=action['data'])
            self.assertEqual(fmt, 'html')
            self.assertGreater(len(content), 500)
            self.assertNotIn(b'No data found', content)
        meeting = env.ref('hse_demo_data.dd_meet_1')
        meeting_day = meeting.meeting_datetime.date()
        wizard = env['transit.wizard'].create({
            'from_date': meeting_day, 'to_date': meeting_day,
            'department_ids': [Command.set(meeting.department_id.ids)],
        })
        action = wizard.print_report()
        self.assertEqual(action['data']['from_date'], str(meeting_day))
        content, fmt = env['ir.actions.report']._render_qweb_html(
            action['report_name'], wizard.ids, data=action['data'])
        self.assertEqual(fmt, 'html')
        self.assertIn(meeting.name.encode(), content)

    def test_date_ranges_are_inclusive_and_timezone_aware(self):
        day = fields.Date.today()
        utc = date_range_domain(self.env(context={'tz': 'UTC'}), 'create_date', day, day)
        self.assertEqual(utc[0], ('create_date', '>=', str(day) + ' 00:00:00'))
        self.assertEqual(utc[1], ('create_date', '<', str(day + timedelta(days=1)) + ' 00:00:00'))
        local = date_range_domain(self.env(context={'tz': 'Asia/Karachi'}), 'create_date', day, day)
        self.assertEqual(local[0][2], str(day - timedelta(days=1)) + ' 19:00:00')
        self.assertEqual(local[1][2], str(day) + ' 19:00:00')

    def test_invalid_or_incomplete_report_ranges_are_rejected(self):
        day = fields.Date.today()
        for start, end in ((False, day), (day, False), (day, day - timedelta(days=1))):
            with self.assertRaises(UserError):
                date_range_domain(self.env, 'create_date', start, end)
        for model in ('hse.wizard.report', 'observation.wizard', 'incident.reporting.wizard',
                      'incident.investigation.wizard', 'capa.wizard'):
            wizard = self.env[model].create({'start_date': day, 'end_date': day - timedelta(days=1)})
            with self.assertRaises(UserError):
                wizard.printhsereport()
