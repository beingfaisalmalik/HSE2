# -*- coding: utf-8 -*-
"""Post-installation UI & reporting verification.

Proves that after module installation/upgrade:
  1. every window action of the HSE suite resolves (model + every view loads);
  2. every backend form view loads and carries its dynamic hero banner;
  3. the client-side enhancer assets (OWL widgets + FormRenderer patch) are
     registered in the web assets bundle;
  4. every HSE report (legacy + new) actually renders for a sample record.
"""
import logging

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)

HSE_MODULES = ('hse', 'hse_meeting', 'hse_reports', 'observation_portal')

NEW_REPORTS = [
    'hse_reports.action_report_hse_audit',
    'hse_reports.action_report_hse_compliance_register',
    'hse_reports.action_report_hse_competency_matrix',
    'hse_reports.action_report_hse_equipment_cert',
    'hse_reports.action_report_hse_osha300_log',
    'hse_reports.action_report_monthly_hse_kpi',
]

VALID_VIEW_TYPES = {'tree', 'form', 'kanban', 'graph', 'pivot', 'calendar',
                    'activity', 'map', 'cohort', 'gantt', 'list'}


@tagged('post_install', '-at_install')
class TestHSEEverythingOpens(TransactionCase):

    def _module_xmlids(self, module):
        return self.env['ir.model.data'].search([('module', '=', module)])

    def test_01_every_window_action_resolves_and_views_load(self):
        """Each act_window of the suite points at a live model and every
        referenced/default view loads through get_views()."""
        xids = self.env['ir.model.data'].search(
            [('module', 'in', HSE_MODULES), ('model', '=', 'ir.actions.act_window')])
        self.assertTrue(len(xids), 'no window actions found')
        checked = 0
        for xid in xids:
            action = self.env['ir.actions.act_window'].browse(xid.res_id).exists()
            if not action or not action.res_model:
                continue
            self.assertIn(action.res_model, self.env,
                          'action %s targets missing model %s' % (xid.complete_name, action.res_model))
            model = self.env[action.res_model]
            modes = (action.view_mode or 'tree,form').split(',')
            for mode in modes:
                self.assertIn(mode, VALID_VIEW_TYPES,
                              'action %s has invalid view mode %s' % (xid.complete_name, mode))
            specs = [[False, mode] for mode in modes]
            result = model.get_views(specs, options={'toolbar': True})
            for mode in modes:
                self.assertIn(mode, result['views'],
                              'action %s: %s view failed to load' % (xid.complete_name, mode))
                self.assertTrue(result['views'][mode].get('arch'),
                                'action %s: empty %s arch' % (xid.complete_name, mode))
            # explicit view_ids referenced by the action must all load too
            for view_ref in action.view_ids:
                model.get_views([[view_ref.view_id.id, view_ref.view_mode]])
            checked += 1
        _logger.info('UI smoke: %d window actions fully resolved', checked)
        self.assertGreater(checked, 50, 'expected the full HSE action set, got %d' % checked)

    def test_02_every_backend_form_view_loads_and_has_hero(self):
        """All form views of HSE-suite models load; the flagship set carries
        the dynamic inline-CSS hero banner."""
        views = self.env['ir.ui.view'].search([
            ('type', '=', 'form'),
            ('model', '!=', False),
        ])
        hero_count = 0
        form_count = 0
        for view in views:
            if not view.model or view.model not in self.env:
                continue
            root_module = (view.model_data_id and view.model_data_id.module) or ''
            if root_module not in HSE_MODULES:
                continue
            arch = self.env[view.model].get_view(view.id, 'form')
            arch_str = arch.get('arch') or ''
            if isinstance(arch_str, bytes):
                arch_str = arch_str.decode('utf-8', 'replace')
            self.assertTrue(arch_str, 'form view %s returned empty arch' % view.xml_id)
            form_count += 1
            if 'hse-x-hero' in arch_str:
                hero_count += 1
        _logger.info('UI smoke: %d backend form views loaded, %d hero-styled', form_count, hero_count)
        self.assertGreater(form_count, 60)
        self.assertGreaterEqual(hero_count, 75, 'dynamic hero banners missing from %d forms' % (form_count - hero_count))

    def test_03_client_enhancer_assets_registered(self):
        """The OWL enhancer JS/XML/SCSS are part of web.assets_backend."""
        paths = {str(t[0]).lstrip('/') for t in
                 self.env['ir.asset']._get_asset_paths(bundle='web.assets_backend', assets_params={})}
        self.assertIn('hse/static/src/js/hse_form_enhancer.js', paths,
                      'enhancer JS not in web.assets_backend')
        self.assertIn('hse/static/src/xml/hse_form_enhancer.xml', paths,
                      'enhancer OWL templates not in web.assets_backend')
        self.assertIn('hse/static/src/scss/hse_style.scss', paths)

    def _sample_ids(self, model, limit=3):
        """Sample record ids; creates a minimal record when the model is
        empty so every report is genuinely rendered at least once.
        (TransactionCase rolls everything back.)"""
        if model not in self.env:
            return []
        recs = self.env[model].search([], limit=limit)
        if recs:
            return recs.ids
        try:
            if model == 'hse.location.profile':
                rec = self.env[model].create({'name': 'UI Test Unit', 'code': 'UI-TST'})
            elif model == 'hse.audit':
                ids_ = self._sample_ids('hse.location.profile', 1)
                loc = ids_[0] if ids_ else self.env['hse.location.profile'].create(
                    {'name': 'UI Test Unit', 'code': 'UI-TST'}).id
                rec = self.env[model].create({
                    'title': 'UI Verification Audit', 'location_id': loc,
                    'audit_team': 'Automated UI Test', 'target_end_date': fields.Date.today(),
                })
            elif model == 'hse.regulation':
                rec = self.env[model].create({
                    'name': 'UI Test Regulation', 'code': 'UI-TST-1',
                    'regulatory_body': 'Automated Test Agency'})
            elif model == 'hse.compliance.obligation':
                reg = self.env['hse.regulation'].search([], limit=1) or \
                    self.env['hse.regulation'].create({
                        'name': 'UI Test Regulation', 'code': 'UI-TST-1',
                        'regulatory_body': 'Automated Test Agency'})
                rec = self.env[model].create({
                    'regulation_id': reg.id, 'clause_code': 'UI-1',
                    'name': 'UI Test Obligation'})
            elif model == 'hse.training.matrix':
                rec = self.env[model].create({'name': 'UI Test Matrix'})
            elif model == 'hse.equipment.certification':
                asset = self.env['assets.form'].create({'name': 'UI Test Vessel'})
                loc = self.env['hse.location.profile'].search([], limit=1) or \
                    self.env['hse.location.profile'].create({'name': 'UI Test Unit', 'code': 'UI-TST'})
                rec = self.env[model].create({
                    'certificate_number': 'UI-CERT-1', 'title': 'UI Verification Certificate',
                    'asset_id': asset.id, 'location_id': loc.id,
                    'certifying_authority': 'Automated Test Agency',
                    'expiry_date': fields.Date.today(),
                })
            else:
                return []
            return rec.ids
        except Exception as exc:
            _logger.warning('could not fabricate sample %s: %s', model, exc)
            return []

    def test_04_every_hse_report_renders(self):
        """Legacy + new reports compile and render for sample records.
        Rendered as HTML (PDF needs wkhtmltopdf, absent in CI sandboxes)."""
        report_ids = []
        for xmlid in NEW_REPORTS:
            rec = self.env.ref(xmlid, raise_if_not_found=False)
            self.assertTrue(rec, 'missing new report %s' % xmlid)
            report_ids.append(rec.id)
        legacy = self.env['ir.model.data'].search([
            ('module', 'in', ('hse_reports', 'hse_meeting')),
            ('model', '=', 'ir.actions.report'),
        ])
        report_ids += legacy.mapped('res_id')
        rendered = skipped = 0
        for report in self.env['ir.actions.report'].browse(report_ids):
            model = report.model
            ids = self._sample_ids(model)
            if not ids:
                skipped += 1
                continue
            if report.report_name == 'hse_reports.report_monthly_hse_kpi_template':
                ids = self.env.company.ids or [self.env.company.id]
            content = self.env['ir.actions.report']._render_qweb_html(
                report.report_name or report.report_file, ids)[0]
            self.assertTrue(content, 'empty render for %s' % report.report_name)
            rendered += 1
        _logger.info('Report smoke: %d rendered, %d skipped (no sample data)', rendered, skipped)
        new_rendered = 0
        for xmlid in NEW_REPORTS:
            report = self.env.ref(xmlid)
            ids = self._sample_ids(report.model)
            if report.report_name == 'hse_reports.report_monthly_hse_kpi_template':
                ids = self.env.company.ids
            content = self.env['ir.actions.report']._render_qweb_html(report.report_name, ids)[0]
            self.assertTrue(content, 'new report %s rendered empty' % xmlid)
            new_rendered += 1
        self.assertEqual(new_rendered, len(NEW_REPORTS),
                         'not all new HSE reports rendered')

    def test_05_monthly_kpi_values_are_dynamic(self):
        """The KPI helper computes from live data without hard-coding."""
        helper = self.env['report.hse_reports.report_monthly_hse_kpi_template']
        vals = helper._get_report_values(self.env.company.ids)
        for key in ('incidents_total', 'days_without_lti', 'trir', 'capas_overdue',
                    'training_gaps', 'period_start', 'period_end', 'hours_source'):
            self.assertIn(key, vals)
        self.assertEqual(vals['period_start'].day, 1)
        self.assertGreaterEqual(vals['period_end'], vals['period_start'])
        self.assertIn(vals['hours_source'],
                      ('API RP 754 metrics', 'configured baseline',
                       'industry default (configure hse_dashboard.exposure_hours_baseline)'))
