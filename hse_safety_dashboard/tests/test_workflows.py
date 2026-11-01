# -*- coding: utf-8 -*-
"""Workflow tests: CA state machine, log status, PTW status."""
from datetime import date, timedelta

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestHseWorkflows(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['hse.corrective.action'].search([]).unlink()
        self.env['hse.injury.log'].search([]).unlink()

    def _ca(self, **kw):
        vals = {'name': 'CA-900', 'action_description': 'Do the thing'}
        vals.update(kw)
        return self.env['hse.corrective.action'].create(vals)

    # ------------------------------------------------------------------
    def test_ca_state_machine(self):
        ca = self._ca()
        self.assertEqual(ca.state, 'open')
        ca.action_start()
        self.assertEqual(ca.state, 'in_progress')
        ca.action_close()
        self.assertEqual(ca.state, 'closed')
        self.assertEqual(ca.closure_date, fields_today())
        ca.action_reopen()
        self.assertEqual(ca.state, 'open')
        self.assertFalse(ca.closure_date)

    def test_ca_overdue_flag(self):
        yesterday = fields_today() - timedelta(days=1)
        ca = self._ca(target_date=yesterday)
        self.assertTrue(ca.overdue, 'open CA past target → overdue')
        ca.action_close()
        self.assertFalse(ca.overdue, 'closed CA never overdue')

    def test_ca_no_target_not_overdue(self):
        ca = self._ca(target_date=False)
        self.assertFalse(ca.overdue)

    def test_ca_overdue_requires_target(self):
        ca = self._ca(target_date=False, state='in_progress')
        self.assertFalse(ca.overdue)
        self.env['hse.corrective.action'].search(
            [('state', '!=', 'closed'), ('target_date', '=', False)])

    def test_ca_activity_scheduled_on_target(self):
        ca = self._ca(target_date=fields_today() + timedelta(days=7))
        self.assertTrue(any(
            a.date_deadline == ca.target_date for a in ca.activity_ids),
            'creating a CA with target date schedules an activity')

    def test_unique_ca_id(self):
        import psycopg2
        self._ca(name='CA-UNIQ')
        # the failed INSERT aborts the tx — contain it in a savepoint
        with self.assertRaises(psycopg2.IntegrityError):
            with self.env.cr.savepoint():
                self._ca(name='CA-UNIQ')

    # ------------------------------------------------------------------
    def test_log_close_reopen(self):
        inj = self.env['hse.injury.log'].create({
            'name': 'INJ-777', 'date': date(2026, 6, 1),
            'injury_type': 'mtc', 'status': 'open'})
        inj.action_mark_closed()
        self.assertEqual(inj.status, 'closed')
        inj.action_mark_open()
        self.assertEqual(inj.status, 'open')

    def test_unique_log_ids(self):
        import psycopg2
        self.env['hse.injury.log'].create({
            'name': 'INJ-DUP', 'injury_type': 'lti'})
        with self.assertRaises(psycopg2.IntegrityError):
            with self.env.cr.savepoint():
                self.env['hse.injury.log'].create({
                    'name': 'INJ-DUP', 'injury_type': 'lti'})

    def test_sequence_generation(self):
        a = self.env['hse.injury.log'].create({'injury_type': 'mtc'})
        b = self.env['hse.injury.log'].create({'injury_type': 'mtc'})
        self.assertTrue(a.name.startswith('INJ-'))
        self.assertNotEqual(a.name, b.name, 'sequence must not repeat')

    # ------------------------------------------------------------------
    def test_uac_type_is_constrained(self):
        """Health check 8 can never fire — selection enforces valid types."""
        rec = self.env['hse.uac.log'].create({
            'name': 'UAC-777', 'uac_type': 'unsafe_act'})
        with self.assertRaises(ValueError):
            rec.uac_type = 'unsafe act'  # invalid selection value


def fields_today():
    from odoo import fields
    return fields.Date.today()
