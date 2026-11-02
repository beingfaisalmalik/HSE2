# -*- coding: utf-8 -*-
"""Dynamic period selectors + one report per every workflow.

Covers the second delivery round: data-driven year/month options on the
dashboard payload and the wizard, the KPI / Leading-Indicator report types,
the seven workflow reports with department &amp; status filters, and the
"never drop undated entries" rule.
"""
from datetime import date

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

PDF_ROUTES = {
    'monthly_pdf': 'hse_safety_dashboard.report_hse_monthly',
    'yearly_pdf': 'hse_safety_dashboard.report_hse_yearly',
    'kpi_pdf': 'hse_safety_dashboard.report_hse_kpi',
    'leading_pdf': 'hse_safety_dashboard.report_hse_leading',
    'injury_pdf': 'hse_safety_dashboard.report_hse_workflow',
    'near_miss_pdf': 'hse_safety_dashboard.report_hse_workflow',
    'uac_pdf': 'hse_safety_dashboard.report_hse_workflow',
    'incident_pdf': 'hse_safety_dashboard.report_hse_workflow',
    'ca_pdf': 'hse_safety_dashboard.report_hse_workflow',
    'ptw_pdf': 'hse_safety_dashboard.report_hse_workflow',
    'figures_pdf': 'hse_safety_dashboard.report_hse_workflow',
}


@tagged('post_install', '-at_install')
class TestReportOptions(TransactionCase):

    def setUp(self):
        super().setUp()
        self.settings = self.env['hse.safety.settings'].get_settings()
        self.settings.write({'reporting_year': 2026, 'rate_base': 200000.0})
        self.engine = self.env['hse.kpi.engine']
        # Give the company a document layout so report_action() returns the
        # report action itself instead of the first-run layout configurator.
        if not self.env.company.external_report_layout_id:
            self.env.company.external_report_layout_id = self.env.ref(
                'web.external_layout_standard')
        for model in ('hse.injury.log', 'hse.near.miss.log', 'hse.uac.log',
                      'hse.incident.log', 'hse.corrective.action',
                      'hse.ptw.register', 'hse.monthly.figure'):
            self.env[model].search([]).unlink()

        # ---- injuries: two years + one undated (data gap, never invented)
        self._injury('INJ-A1', date(2025, 6, 10), 'lti', 'HSE', 'closed', 1)
        self._injury('INJ-A2', date(2026, 1, 5), 'mtc', 'Ops', 'open', 0)
        self._injury('INJ-A3', date(2026, 3, 15), 'lti', 'HSE', 'closed', 2)
        self._injury('INJ-A4', None, 'first_aid', 'HSE', 'open', 0)

        # ---- other workflows (2026 only, one undated PTW)
        self.env['hse.near.miss.log'].create({
            'name': 'NM-A1', 'date': date(2026, 4, 20),
            'department': 'Ops', 'potential_severity': 'high',
            'status': 'closed', 'description': 'Slip hazard'})
        self.env['hse.uac.log'].create({
            'name': 'UAC-A1', 'date': date(2026, 3, 2),
            'department': 'HSE', 'uac_type': 'unsafe_act',
            'status': 'open', 'description': 'No helmet'})
        self.env['hse.uac.log'].create({
            'name': 'UAC-A2', 'date': date(2026, 3, 8),
            'department': 'Ops', 'uac_type': 'unsafe_condition',
            'status': 'closed', 'description': 'Oil spill'})
        self.env['hse.incident.log'].create({
            'name': 'INC-A1', 'date': date(2026, 2, 12),
            'department': 'HSE', 'incident_type': 'property_damage',
            'status': 'open', 'description': 'Forklift scrape'})
        self.env['hse.ptw.register'].create({
            'name': 'PTW-A1', 'date_issue': date(2026, 3, 5),
            'department': 'HSE', 'status': 'open',
            'type_text': 'Hot Work'})
        self.env['hse.ptw.register'].create({
            'name': 'PTW-A2', 'date_issue': date(2026, 4, 9),
            'department': 'Ops', 'status': 'closed',
            'type_text': 'Cold Work'})
        self.env['hse.ptw.register'].create({
            'name': 'PTW-A3', 'date_issue': None,
            'department': 'HSE', 'status': 'open',
            'type_text': 'Work at Height'})

        # ---- corrective actions: one linked 2026, one 2025, one broken ref
        self.env['hse.corrective.action'].create({
            'name': 'CA-A1', 'related_ref': 'INJ-A3',
            'action_description': 'Fix guard', 'state': 'open'})
        self.env['hse.corrective.action'].create({
            'name': 'CA-A2', 'related_ref': 'INJ-A1',
            'action_description': 'Review LTI', 'state': 'closed'})
        self.env['hse.corrective.action'].create({
            'name': 'CA-A3', 'related_ref': 'GHOST-99',
            'action_description': 'Orphan ref', 'state': 'open'})

        # ---- monthly figures: 2026 Jan+Mar, 2025 Jun
        self._figure(2026, 1, man_hours=10000, toolbox_talks=5,
                     audit_score=0.9)
        self._figure(2026, 3, man_hours=22000, toolbox_talks=8,
                     planned_inspections=4, completed_inspections=3)
        self._figure(2025, 6, man_hours=18000)

    # ------------------------------------------------------------ helpers
    def _injury(self, name, d, itype, dept, status, days):
        return self.env['hse.injury.log'].create({
            'name': name, 'date': d, 'injury_type': itype,
            'department': dept, 'status': status, 'lost_workdays': days})

    def _figure(self, year, month, **kw):
        return self.env['hse.monthly.figure'].create(
            dict({'year': year, 'month': str(month)}, **kw))

    def _wizard(self, **kw):
        vals = {'report_type': 'injury_pdf', 'year': '2026'}
        vals.update(kw)
        return self.env['hse.report.wizard'].create(vals)

    # ------------------------------------------- dynamic year / month list
    def test_available_years_from_data(self):
        """Years = data years ∪ settings year ∪ current year, newest first."""
        years = self.engine.available_years()
        today_year = fields.Date.context_today(self.env.user).year
        self.assertEqual(years, sorted({2026, 2025, today_year}, reverse=True))
        self.assertIn(2025, years, 'data year included')
        self.assertIn(2026, years, 'settings year included')
        self.assertEqual(years, sorted(years, reverse=True), 'newest first')

    def test_available_months_from_data(self):
        """Only months holding data — plus the all-12 fallback for empty years."""
        self.assertEqual(self.engine.available_months(2026), [1, 2, 3, 4],
                         'Jan (inj+fig), Feb (inc), Mar (inj+uac+ptw+fig+ca),'
                         ' Apr (nm+ptw) — 2025-06 CA link must NOT leak in')
        self.assertEqual(self.engine.available_months(2025), [6])
        self.assertEqual(self.engine.available_months(2019),
                         list(range(1, 13)),
                         'empty year falls back to all calendar months')

    def test_dashboard_payload_options(self):
        """Payload carries both selector lists; default month = latest with data."""
        payload = self.engine.get_dashboard(2026)
        self.assertEqual(payload['years'],
                         sorted({2026, 2025,
                                 fields.Date.context_today(self.env.user).year},
                                reverse=True))
        self.assertEqual(payload['available_months'], [1, 2, 3, 4])
        self.assertEqual(payload['month_no'], 4,
                         'default = latest month that holds data')
        # explicit month is honoured verbatim, even without data
        explicit = self.engine.get_dashboard(2026, 9)
        self.assertEqual(explicit['month_no'], 9)
        # other year from the data
        y25 = self.engine.get_dashboard(2025)
        self.assertEqual(y25['month_no'], 6)

    def test_wizard_year_selection_is_dynamic(self):
        opts = dict(self.env['hse.report.wizard']._selection_year())
        self.assertIn('2026', opts)
        self.assertIn('2025', opts)
        wiz = self._wizard(year='2025')
        self.assertEqual(int(wiz.year), 2025)

    def test_wizard_department_selection_is_dynamic(self):
        opts = dict(self.env['hse.report.wizard']._selection_department())
        self.assertIn('all', opts)
        self.assertIn('HSE', opts)
        self.assertIn('Ops', opts)

    # ------------------------------------------------------- report routing
    def test_every_report_type_routes(self):
        for rt, report_name in PDF_ROUTES.items():
            wiz = self._wizard(report_type=rt)
            res = wiz.action_generate()
            self.assertEqual(res.get('type'), 'ir.actions.report', rt)
            self.assertEqual(res.get('report_name'), report_name, rt)
        wiz = self._wizard(report_type='xlsx')
        res = wiz.action_generate()
        self.assertEqual(res.get('type'), 'ir.actions.act_url')

    def test_report_actions_and_menus_exist(self):
        for xmlid in (
            'hse_safety_dashboard.action_report_hse_kpi',
            'hse_safety_dashboard.action_report_hse_leading',
            'hse_safety_dashboard.action_report_hse_workflow',
            'hse_safety_dashboard.menu_hse_workflow_reports',
            'hse_safety_dashboard.menu_hse_report_kpi',
            'hse_safety_dashboard.menu_hse_report_leading',
            'hse_safety_dashboard.menu_hse_report_injury',
            'hse_safety_dashboard.menu_hse_report_near_miss',
            'hse_safety_dashboard.menu_hse_report_uac',
            'hse_safety_dashboard.menu_hse_report_incident',
            'hse_safety_dashboard.menu_hse_report_ca',
            'hse_safety_dashboard.menu_hse_report_ptw',
            'hse_safety_dashboard.menu_hse_report_figures',
        ):
            self.assertTrue(self.env.ref(xmlid, raise_if_not_found=False),
                            xmlid)

    # -------------------------------------------------- workflow row filters
    def test_injury_report_period(self):
        wiz = self._wizard(report_type='injury_pdf')
        wf = wiz.workflow_rows()
        self.assertEqual(wf['title'], 'Injury Log Report')
        names = [r[0] for r in wf['rows']]
        self.assertEqual(names, ['INJ-A2', 'INJ-A3'], '2026 only, sorted by ID')
        self.assertEqual(wf['count'], 2)
        self.assertEqual([r[0] for r in wf['unmatched']], ['INJ-A4'],
                         'undated injury never dropped')
        # month filter
        wiz3 = self._wizard(report_type='injury_pdf', month='3')
        wf3 = wiz3.workflow_rows()
        self.assertEqual([r[0] for r in wf3['rows']], ['INJ-A3'])
        # department filter
        wiz_hse = self._wizard(report_type='injury_pdf', department='HSE')
        wf_hse = wiz_hse.workflow_rows()
        self.assertEqual([r[0] for r in wf_hse['rows']], ['INJ-A3'],
                         'Ops injury excluded; undated HSE kept as unmatched')
        self.assertEqual([r[0] for r in wf_hse['unmatched']], ['INJ-A4'])
        # status filter
        wiz_open = self._wizard(report_type='injury_pdf', status_filter='open')
        wf_open = wiz_open.workflow_rows()
        self.assertEqual([r[0] for r in wf_open['rows']], ['INJ-A2'])

    def test_near_miss_and_incident_reports(self):
        wf = self._wizard(report_type='near_miss_pdf').workflow_rows()
        self.assertEqual(wf['headers'][0], 'Near-Miss ID')
        self.assertEqual([r[0] for r in wf['rows']], ['NM-A1'])
        wf2 = self._wizard(report_type='incident_pdf').workflow_rows()
        self.assertEqual([r[0] for r in wf2['rows']], ['INC-A1'])

    def test_uac_report_filters(self):
        wf = self._wizard(report_type='uac_pdf').workflow_rows()
        self.assertEqual([r[0] for r in wf['rows']], ['UAC-A1', 'UAC-A2'])
        wf_hse = self._wizard(report_type='uac_pdf',
                              department='HSE').workflow_rows()
        self.assertEqual([r[0] for r in wf_hse['rows']], ['UAC-A1'])
        wf_closed = self._wizard(report_type='uac_pdf',
                                 status_filter='closed').workflow_rows()
        self.assertEqual([r[0] for r in wf_closed['rows']], ['UAC-A2'])

    def test_ca_report_period_and_unmatched(self):
        wf = self._wizard(report_type='ca_pdf').workflow_rows()
        names = [r[0] for r in wf['rows']]
        self.assertEqual(names, ['CA-A1'],
                         'only the 2026-linked CA; 2025 link excluded')
        self.assertEqual([r[0] for r in wf['unmatched']], ['CA-A3'],
                         'broken related-ref stays visible, undated')
        wf25 = self._wizard(report_type='ca_pdf', year='2025').workflow_rows()
        self.assertEqual([r[0] for r in wf25['rows']], ['CA-A2'])
        wf_open = self._wizard(report_type='ca_pdf',
                               status_filter='open').workflow_rows()
        self.assertEqual([r[0] for r in wf_open['rows']], ['CA-A1'])

    def test_ptw_report_filters(self):
        wf = self._wizard(report_type='ptw_pdf').workflow_rows()
        self.assertEqual([r[0] for r in wf['rows']], ['PTW-A1', 'PTW-A2'])
        self.assertEqual([r[0] for r in wf['unmatched']], ['PTW-A3'])
        wf_ops = self._wizard(report_type='ptw_pdf',
                              department='Ops').workflow_rows()
        self.assertEqual([r[0] for r in wf_ops['rows']], ['PTW-A2'])
        wf_open = self._wizard(report_type='ptw_pdf',
                               status_filter='open').workflow_rows()
        self.assertEqual([r[0] for r in wf_open['rows']], ['PTW-A1'])
        wf_mar = self._wizard(report_type='ptw_pdf',
                              month='3').workflow_rows()
        self.assertEqual([r[0] for r in wf_mar['rows']], ['PTW-A1'])

    def test_figures_report(self):
        wf = self._wizard(report_type='figures_pdf').workflow_rows()
        self.assertEqual(wf['count'], 2, 'Jan + Mar 2026 (2025 row excluded)')
        self.assertEqual(wf['rows'][0][0], 'Jan-26')
        self.assertEqual(wf['rows'][0][1], '10000')
        wf_mar = self._wizard(report_type='figures_pdf',
                              month='3').workflow_rows()
        self.assertEqual(wf_mar['count'], 1)
        self.assertEqual(wf_mar['rows'][0][0], 'Mar-26')
        # audit score 0 means "not entered" → n/a, never a fake 0.00
        self.assertEqual(wf['rows'][0][7], '0.90')
        self.assertEqual(wf_mar['rows'][0][7], 'n/a')

    def test_workflow_entry_point_and_labels(self):
        wiz = self._wizard(report_type='injury_pdf', month='3')
        wf = wiz.get_workflow()
        self.assertEqual(wf['period'], 'March 2026')
        self.assertIn('Period: March 2026', wf['filters'])
        wiz_full = self._wizard(report_type='injury_pdf')
        self.assertEqual(wiz_full.get_workflow()['period'],
                         '2026 (full year)')

    def test_period_month_rejects_other_months(self):
        wf = self._wizard(report_type='injury_pdf',
                          month='6').workflow_rows()
        self.assertEqual(wf['rows'], [], 'June has no 2026 injuries')
        self.assertEqual(wf['count'], 0)
        self.assertIn('June 2026', wf['empty_note'])

    # -------------------------------------------------------------- XLSX
    def test_xlsx_uses_dynamic_filters(self):
        import base64
        try:
            import openpyxl
        except ImportError:  # pragma: no cover
            self.skipTest('openpyxl not available')
        wiz = self._wizard(report_type='xlsx')
        res = wiz.action_generate()
        self.assertEqual(res['type'], 'ir.actions.act_url')
        att_id = int(res['url'].split('/web/content/')[1].split('?')[0])
        data = base64.b64decode(
            self.env['ir.attachment'].browse(att_id).datas)
        wb = openpyxl.load_workbook(__import__('io').BytesIO(data))
        # Injury sheet: 2026 rows + the undated one, nothing from 2025
        inj = wb['Injury Log']
        ids = [inj.cell(r, 1).value for r in range(2, inj.max_row + 1)]
        self.assertEqual(ids, ['INJ-A2', 'INJ-A3', 'INJ-A4'])
        # Leading indicators sheet only 2026 figures
        lead = wb['Leading Indicators']
        self.assertEqual(lead.max_row, 3, 'header + Jan + Mar 2026')
        self.assertIn('KPI Calculations', wb.sheetnames)
        self.assertIn('Data Health', wb.sheetnames)
