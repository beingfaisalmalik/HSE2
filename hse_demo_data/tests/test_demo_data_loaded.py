# -*- coding: utf-8 -*-
"""Prove the demo loader seeded every major HSE form.

Runs post_install: if any of these counts is zero, the loader failed and
the install is reported as broken instead of silently shipping empty forms.
"""
import logging

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)

EXPECTED = {
    # master data
    'hse.location.profile': 3,
    'assets.form': 4,
    'hse.contractor': 2,
    'hse.regulation': 3,
    'hse.competency': 4,
    'hse.operating.policy': 2,
    'hse.operating.procedure': 3,
    'hse.solution': 2,
    'hse.pse.metric': 1,
    # safety operations
    'incident.reporting': 5,
    'hse.incident.injury': 2,
    'observation.observation': 5,
    'hse.permit': 3,
    'hse.permit.gas.test': 1,
    'hse.loto.plan': 2,
    'hse.loto.point': 2,
    'hse.bypass': 2,
    'hse.stop.work': 1,
    'hse.bbs.observation': 2,
    'ra_jsa.model': 2,
    'hse.moc': 2,
    'hse.ncr': 2,
    'incident.investigation': 1,
    # actions & compliance
    'hse.action': 6,
    'hse.audit': 2,
    'hse.audit.checklist': 3,
    'hse.compliance.obligation': 5,
    'hse.compliance.task': 2,
    # assets & people
    'hse.equipment.certification': 4,
    'hse.personnel.certification': 3,
    'hse.employee.competency': 3,
    'hse.training.matrix': 1,
    'hse.training.matrix.line': 5,
    'hse.meeting': 2,
    'hse.operator.log': 1,
    'hse.failure.report': 1,
    'hse.defect.elimination': 1,
    'hse.improvement': 1,
}


@tagged('post_install', '-at_install')
class TestHSEDemoDataLoaded(TransactionCase):

    def test_01_every_seeded_model_has_records(self):
        missing = []
        for model, minimum in EXPECTED.items():
            if model not in self.env:
                missing.append('%s (model missing)' % model)
                continue
            count = self.env[model].search_count([])
            if count < minimum:
                missing.append('%s (%d < %d)' % (model, count, minimum))
        self.assertFalse(
            missing,
            'demo data loader did not seed: %s' % ', '.join(missing))
        _logger.info('demo data: all %d seeded models verified', len(EXPECTED))

    def test_02_dynamic_indicators_are_meaningful(self):
        """Status math built on the seeded data actually produces results."""
        # days-without-LTI: last LTI is 24 days old, so counter > 0
        lti = self.env['incident.reporting'].search(
            [('injury_ids.injury_severity', 'in', ['fatality', 'lost_time']),
             ('incident_date', '!=', False)], order='incident_date desc', limit=1)
        self.assertTrue(lti, 'no LTI incident seeded')
        today = fields.Date.context_today(self.env['res.users'])
        self.assertGreater((today - lti.incident_date).days, 0)

        # overdue CAPA: at least one action seeded with a past target date
        overdue = self.env['hse.action'].search_count(
            [('target_date', '<', fields.Date.context_today(self.env['res.users'])), ('state', 'not in', ['verified', 'cancelled'])])
        self.assertGreaterEqual(overdue, 2)

        # equipment certs: one expired, one expiring soon
        self.assertGreaterEqual(self.env['hse.equipment.certification'].search_count(
            [('is_expired', '=', True)]), 1)
        self.assertGreaterEqual(self.env['hse.equipment.certification'].search_count(
            [('is_expiring_soon', '=', True)]), 1)

        # training gaps present for the gap matrix
        self.assertGreaterEqual(self.env['hse.training.matrix.line'].search_count(
            [('status', 'in', ['missing', 'expired'])]), 2)

        # exposure hours seeded -> TRIR source is real metrics, not baseline
        metric = self.env['hse.pse.metric'].search([], limit=1)
        self.assertTrue(metric and metric.total_site_exposure_hours > 0)

        # portal content
        self.assertGreaterEqual(self.env['hse.operating.policy'].search_count(
            [('state', '=', 'approved')]), 2)
        self.assertGreaterEqual(self.env['hse.operating.procedure'].search_count(
            [('state', '=', 'published')]), 2)

    def test_03_every_seeded_record_opens_its_form(self):
        """Each seeded record resolves its model's form view (get_view)."""
        checked = 0
        for model in EXPECTED:
            if model not in self.env:
                continue
            rec = self.env[model].search([], limit=1)
            if not rec:
                continue
            arch = self.env[model].get_view(False, 'form')
            self.assertTrue(arch.get('arch'), 'form arch empty for %s' % model)
            rec.display_name  # force read of core fields
            checked += 1
        self.assertGreaterEqual(checked, 30)
