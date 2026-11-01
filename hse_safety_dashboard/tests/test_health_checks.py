# -*- coding: utf-8 -*-
"""The 10 data-health checks — exact Excel Calc r145-r154 semantics."""
from datetime import date, timedelta

from odoo.tests.common import TransactionCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestHseHealthChecks(TransactionCase):

    def setUp(self):
        super().setUp()
        self.settings = self.env['hse.safety.settings'].get_settings()
        self.settings.write({'reporting_year': 2026, 'rate_base': 200000.0})
        self.engine = self.env['hse.kpi.engine']
        self.env['hse.injury.log'].search([]).unlink()
        self.env['hse.near.miss.log'].search([]).unlink()
        self.env['hse.uac.log'].search([]).unlink()
        self.env['hse.incident.log'].search([]).unlink()
        self.env['hse.corrective.action'].search([]).unlink()
        self.env['hse.ptw.register'].search([]).unlink()
        self.env['hse.monthly.figure'].search([]).unlink()

    def _checks(self):
        return {c['no']: c for c in self.engine.health_checks(2026)}

    def test_all_green_on_empty(self):
        checks = self._checks()
        self.assertEqual(len(checks), 10)
        for no, chk in checks.items():
            self.assertEqual(chk['count'], 0,
                             'check %s should be 0 on empty data: %s'
                             % (no, chk['label']))

    def test_check1_missing_date(self):
        self.env['hse.injury.log'].create({
            'name': 'INJ-001', 'injury_type': 'lti'})  # no date
        c1 = self._checks()[1]
        self.assertEqual(c1['count'], 1)
        self.assertFalse(c1['ok'])
        self.assertIn('Injury 1', c1['detail'])

    def test_check1_outside_year(self):
        self.env['hse.injury.log'].create({
            'name': 'INJ-002', 'date': date(2025, 5, 1), 'injury_type': 'lti'})
        self.assertEqual(self._checks()[1]['count'], 1)

    def test_check3_future_date(self):
        future = fields.Date.context_today(self.env.user) + timedelta(days=30)
        self.env['hse.near.miss.log'].create({
            'name': 'NM-001', 'date': future})
        self.assertEqual(self._checks()[3]['count'], 1)

    def test_check4_out_of_order(self):
        """Later ID with an earlier date → flagged (day/month swap heuristic)."""
        self.env['hse.injury.log'].create([
            {'name': 'INJ-001', 'date': date(2026, 6, 20), 'injury_type': 'mtc'},
            {'name': 'INJ-002', 'date': date(2026, 6, 5), 'injury_type': 'mtc'},
        ])
        c4 = self._checks()[4]
        self.assertEqual(c4['count'], 1)
        self.assertIn('Injury 1', c4['detail'])

    def test_check5_unmatched_ca_ref(self):
        """CA whose Related ID has no dated log entry (Excel AO/AP = 0)."""
        self.env['hse.corrective.action'].create({
            'name': 'CA-001', 'related_ref': 'INJ-404',  # does not exist
            'action_description': 'x'})
        self.env['hse.corrective.action'].create({
            'name': 'CA-002', 'related_ref': 'INJ-UNDATED',  # exists, no date
            'action_description': 'x'})
        self.env['hse.injury.log'].create({
            'name': 'INJ-UNDATED', 'injury_type': 'mtc'})
        self.assertEqual(self._checks()[5]['count'], 2)

    def test_check5_resolves_dated_entry(self):
        self.env['hse.injury.log'].create({
            'name': 'INJ-001', 'date': date(2026, 4, 1), 'injury_type': 'mtc'})
        self.env['hse.corrective.action'].create({
            'name': 'CA-001', 'related_ref': 'INJ-001',
            'action_description': 'x'})
        self.assertEqual(self._checks()[5]['count'], 0)

    def test_check6_open_ca_without_target(self):
        self.env['hse.corrective.action'].create({
            'name': 'CA-010', 'action_description': 'x', 'state': 'open'})
        self.env['hse.corrective.action'].create({
            'name': 'CA-011', 'action_description': 'x', 'state': 'closed'})
        c6 = self._checks()[6]
        self.assertEqual(c6['count'], 1, 'only the OPEN one counts')

    def test_check7_events_without_hours(self):
        self.env['hse.near.miss.log'].create({
            'name': 'NM-001', 'date': date(2026, 4, 20)})
        # March has hours, April doesn't → 1 flagged month
        self.env['hse.monthly.figure'].create({
            'year': 2026, 'month': '3', 'man_hours': 22000})
        c7 = self._checks()[7]
        self.assertEqual(c7['count'], 1)

    def test_check9_ptw_mismatch(self):
        self.env['hse.monthly.figure'].create({
            'year': 2026, 'month': '8', 'ptw_issued': 172})
        self.env['hse.ptw.register'].create([
            {'name': 'PTW-001', 'date_issue': date(2026, 8, 3)},
            {'name': 'PTW-002', 'date_issue': date(2026, 8, 4)},
        ])
        # register rows 2 ≠ entered 172 → flagged; other months 0 == 0
        self.assertEqual(self._checks()[9]['count'], 1)

    def test_check8_and_10_always_zero(self):
        """Selection fields + single live source make 8 and 10 impossible."""
        self.env['hse.uac.log'].create({
            'name': 'UAC-001', 'date': date(2026, 5, 5),
            'uac_type': 'unsafe_condition'})
        checks = self._checks()
        self.assertEqual(checks[8]['count'], 0)
        self.assertEqual(checks[10]['count'], 0)

    def test_attention_count(self):
        self.env['hse.injury.log'].create({'name': 'INJ-001'})  # missing date
        payload = self.engine.get_dashboard(2026, 6)
        self.assertEqual(payload['health_attention'], 1)
        self.assertFalse(payload['health'][0]['ok'])
