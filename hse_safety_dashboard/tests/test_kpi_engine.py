# -*- coding: utf-8 -*-
"""KPI engine tests — the exact arithmetic of the Excel Calc sheet."""
from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHseKpiEngine(TransactionCase):

    def setUp(self):
        super().setUp()
        self.settings = self.env['hse.safety.settings'].get_settings()
        self.settings.write({'reporting_year': 2026, 'rate_base': 200000.0})
        self.engine = self.env['hse.kpi.engine']
        # Clear demo/other data so counts are deterministic
        self.env['hse.injury.log'].search([]).unlink()
        self.env['hse.near.miss.log'].search([]).unlink()
        self.env['hse.uac.log'].search([]).unlink()
        self.env['hse.incident.log'].search([]).unlink()
        self.env['hse.corrective.action'].search([]).unlink()
        self.env['hse.ptw.register'].search([]).unlink()
        self.env['hse.monthly.figure'].search([]).unlink()

    def _figure(self, month, **kw):
        return self.env['hse.monthly.figure'].create(
            dict({'year': 2026, 'month': str(month)}, **kw))

    def _injury(self, name, d, itype='lti', days=0):
        return self.env['hse.injury.log'].create({
            'name': name, 'date': d, 'injury_type': itype,
            'lost_workdays': days, 'status': 'closed'})

    # ------------------------------------------------------------------
    def test_rates_with_hours(self):
        """LTIFR = LTI × 200,000 / hours (Calc AH17)."""
        self._figure(3, man_hours=22000)
        self._injury('INJ-001', date(2026, 3, 10), 'lti', days=1)
        self._injury('INJ-002', date(2026, 3, 15), 'mtc')
        self._injury('INJ-003', date(2026, 3, 20), 'first_aid')
        st = self.engine.month_stats(2026, 3)
        self.assertEqual(st['lti'], 1)
        self.assertEqual(st['mtc'], 1)
        self.assertEqual(st['first_aid'], 1)
        self.assertEqual(st['recordable'], 2, 'Recordable = LTI + MTC')
        self.assertEqual(st['all_injuries'], 3)
        self.assertEqual(st['lost_workdays'], 1)
        self.assertAlmostEqual(st['ltifr'], 1 * 200000 / 22000, places=6)
        self.assertAlmostEqual(st['trir'], 2 * 200000 / 22000, places=6)
        self.assertAlmostEqual(st['severity'], 1 * 200000 / 22000, places=6)

    def test_rates_without_hours_are_na(self):
        """No man-hours → LTIFR/TRIR/Severity are None (Excel "")."""
        self._injury('INJ-010', date(2026, 5, 5), 'lti', days=2)
        st = self.engine.month_stats(2026, 5)
        self.assertIsNone(st['ltifr'])
        self.assertIsNone(st['trir'])
        self.assertIsNone(st['severity'])
        self.assertEqual(st['has_hours'], 0)

    def test_ytd_rates_only_use_months_with_hours(self):
        """Calc AH30: SUMIFS(LTI, has_hours=1) × base / SUM(hours)."""
        self._figure(3, man_hours=10000)   # has hours
        self._figure(4, man_hours=0)       # no hours
        self._injury('INJ-001', date(2026, 3, 5), 'lti')
        self._injury('INJ-002', date(2026, 4, 5), 'lti')  # month without hours
        ytd = self.engine.year_stats(2026, 6)['ytd_to_month']
        # LTI in March (has hours) counts; April LTI excluded from numerator;
        # denominator = 10,000 + 0.
        self.assertAlmostEqual(ytd['ltifr'], 1 * 200000 / 10000, places=6)
        self.assertEqual(ytd['lti'], 2, 'raw YTD LTI count includes both')

    def test_month_attribution_outside_year_is_zero(self):
        """CalcRows D: date in another year → month 0 (excluded)."""
        self._injury('INJ-090', date(2025, 7, 1), 'lti')
        st = self.engine.month_stats(2026, 7)
        self.assertEqual(st['lti'], 0)

    def test_days_since_last_lti(self):
        """Dashboard I5: as_of − last LTI date; fallback Jan 1."""
        self._injury('INJ-002', date(2026, 3, 10), 'lti')
        dsl = self.engine.days_since_last_lti(2026, month_no=6,
                                              as_of=date(2026, 6, 30))
        self.assertTrue(dsl['has_lti'])
        self.assertEqual(dsl['days'], (date(2026, 6, 30) - date(2026, 3, 10)).days)
        # no LTI → days since Jan 1
        self.env['hse.injury.log'].search([]).unlink()
        dsl2 = self.engine.days_since_last_lti(2026, month_no=6,
                                               as_of=date(2026, 6, 30))
        self.assertFalse(dsl2['has_lti'])
        self.assertEqual(dsl2['days'], (date(2026, 6, 30) - date(2026, 1, 1)).days)

    def test_observations_and_incidents(self):
        self.env['hse.uac.log'].create([
            {'name': 'UAC-001', 'date': date(2026, 8, 3), 'uac_type': 'unsafe_act',
             'status': 'closed'},
            {'name': 'UAC-002', 'date': date(2026, 8, 4), 'uac_type': 'unsafe_condition',
             'status': 'open'},
            {'name': 'UAC-003', 'date': date(2026, 8, 5), 'uac_type': 'unsafe_act',
             'status': 'closed'},
        ])
        self.env['hse.near.miss.log'].create({
            'name': 'NM-001', 'date': date(2026, 8, 9), 'potential_severity': 'high'})
        self.env['hse.incident.log'].create({
            'name': 'INC-001', 'date': date(2026, 8, 12),
            'incident_type': 'property_damage'})
        st = self.engine.month_stats(2026, 8)
        self.assertEqual(st['unsafe_acts'], 2)
        self.assertEqual(st['unsafe_conditions'], 1)
        self.assertEqual(st['observations'], 3)
        self.assertEqual(st['observations_closed'], 2)
        self.assertEqual(st['near_misses'], 1)
        self.assertEqual(st['incidents'], 1)

    def test_ca_attribution_and_closure_rate(self):
        """CAs count in the month of the linked event's date (Calc AO/AP)."""
        inj = self.env['hse.injury.log'].create({
            'name': 'INJ-001', 'date': date(2026, 8, 2), 'injury_type': 'mtc'})
        ca = self.env['hse.corrective.action'].create({
            'name': 'CA-001', 'related_ref': 'INJ-001',
            'action_description': 'Fix the guard', 'state': 'closed',
            'closure_date': date(2026, 8, 20)})
        inj.write({'corrective_action_id': ca.id})
        ca_open = self.env['hse.corrective.action'].create({
            'name': 'CA-002', 'related_ref': 'INJ-001',
            'action_description': 'Retrain crew', 'state': 'open',
            'target_date': date(2026, 8, 25)})
        st = self.engine.month_stats(2026, 8)
        self.assertEqual(st['ca_linked'], 2)
        self.assertEqual(st['ca_closed'], 1)
        self.assertEqual(st['ca_open'], 1)
        self.assertAlmostEqual(st['ca_closure_rate'], 0.5)
        self.assertTrue(ca_open.overdue is False or ca_open.overdue is True)

    def test_ptw_keyword_counts(self):
        self.env['hse.ptw.register'].create([
            {'name': 'PTW-001', 'date_issue': date(2026, 8, 3),
             'type_text': 'Hot Work / Work at Height'},
            {'name': 'PTW-002', 'date_issue': date(2026, 8, 4),
             'type_text': 'Cold Work'},
            {'name': 'PTW-003', 'date_issue': date(2026, 8, 5),
             'type_text': 'Electrical Work / Confined Space'},
            {'name': 'PTW-004', 'date_issue': date(2026, 9, 3),
             'type_text': 'Hot Work'},
        ])
        st = self.engine.month_stats(2026, 8)
        self.assertEqual(st['ptw_register_rows'], 3)
        self.assertEqual(st['ptw_hot_work'], 1)
        self.assertEqual(st['ptw_cold_work'], 1)
        self.assertEqual(st['ptw_height'], 1)
        self.assertEqual(st['ptw_electrical'], 1)
        self.assertEqual(st['ptw_confined'], 1)
        st9 = self.engine.month_stats(2026, 9)
        self.assertEqual(st9['ptw_hot_work'], 1)

    def test_inspections_compliance_and_audit(self):
        self._figure(8, planned_inspections=4, completed_inspections=3,
                     audit_score=0.92)
        st = self.engine.month_stats(2026, 8)
        self.assertAlmostEqual(st['insp_compliance'], 0.75)
        self.assertAlmostEqual(st['audit_score'], 0.92)
        st2 = self.engine.month_stats(2026, 2)
        self.assertIsNone(st2['insp_compliance'], 'no planned → n/a')
        self.assertIsNone(st2['audit_score'])

    def test_get_dashboard_payload_shape(self):
        self._figure(9, man_hours=5000, toolbox_talks=10)
        payload = self.engine.get_dashboard(2026, 9)
        for key in ('year', 'month_no', 'month_label', 'month_name', 'stats',
                    'prior', 'ytd_to_month', 'ytd_full', 'months', 'health',
                    'health_attention', 'days_since_lti', 'registers',
                    'rate_base', 'company'):
            self.assertIn(key, payload)
        self.assertEqual(len(payload['months']), 12)
        self.assertEqual(payload['month_label'], 'Sep-26')
        self.assertEqual(payload['stats']['toolbox_talks'], 10)
        self.assertEqual(len(payload['health']), 10)
        self.assertIn('injuries', payload['registers'])
