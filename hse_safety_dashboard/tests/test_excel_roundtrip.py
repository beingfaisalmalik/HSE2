# -*- coding: utf-8 -*-
"""Excel round-trip: build a miniature workbook in memory, import it,
verify every register — including both PTW layouts and d/m/y text dates."""
import base64
import io
from datetime import date

from odoo.tests.common import TransactionCase, tagged

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None


def _build_workbook():
    wb = openpyxl.Workbook()

    # ---- Injury Log (header row 2, data from 3) ----
    ws = wb.active
    ws.title = 'Injury Log'
    ws.append(['Injury Log'])
    ws.append(['Injury ID', 'Date', 'Type', 'Department', 'Description',
               'Person Involved', 'Lost Workdays', 'Root Cause',
               'Corrective Action ID', 'Status'])
    ws.append(['INJ-001', '15/03/2026', 'Lost Time Injury', 'Mechanical',
               'Cut finger on lathe', 'Ali Khan', 2, 'No glove', 'CA-001', 'Closed'])
    ws.append(['INJ-002', date(2026, 4, 10), 'First Aid Case', 'Solid Engineering',
               'Splinter', 'Sara', 0, 'Rough surface', '', 'Open'])
    # footnote row that must be ignored
    ws.append(['Type must be Lost Time Injury, Medical Treatment Case, or First Aid Case.'])

    # ---- Near Miss Log ----
    ws = wb.create_sheet('Near Miss Log')
    ws.append(['Near-Miss Log'])
    ws.append(['Near-Miss ID', 'Date', 'Department', 'Description',
               'Potential Severity', 'Reported By', 'Corrective Action ID', 'Status'])
    ws.append(['NM-001', '20/04/2026', 'MPB Kitchen', 'Gas leak', 'High',
               'Admin Head', 'CA-073', 'Closed'])

    # ---- UnsafeAct Condition Log ----
    ws = wb.create_sheet('UnsafeAct Condition Log')
    ws.append(['UnsafeAct Condition Log'])
    ws.append(['Observation ID', 'Date', 'Type', 'Department',
               'Description / Observation', 'Reported By',
               'Immediate Action Taken', 'Corrective Action ID', 'Status'])
    ws.append(['UAC-001', '05-Sep-2026', 'Unsafe Condition', 'All over site',
               'Blades lying around', 'HSE', 'Warned team', 'CA-012', 'Open'])
    ws.append(['UAC-002', date(2026, 9, 6), 'Unsafe Act', 'Winder',
               'No hairnets', 'HSE', 'Warned', 'CA-013', 'Closed'])

    # ---- Incident Log ----
    ws = wb.create_sheet('Incident Log')
    ws.append(['Incident Log'])
    ws.append(['Incident ID', 'Date', 'Type', 'Department', 'Description',
               'Area / Asset Involved', 'Estimated Impact', 'Root Cause',
               'Corrective Action ID', 'Status'])
    ws.append(['INC-001', '12/8/2026', 'Property Damage', 'Guest House',
               'Window shattered by welding residue', 'Guest House Window',
               'PKR 60,000 est.', 'No risk assessment', 'CA-074', 'Closed'])

    # ---- Corrective Actions ----
    ws = wb.create_sheet('Corrective Actions')
    ws.append(['Corrective Actions Tracker'])
    ws.append(['CA ID', 'Related Log Entry ID', 'Action Description',
               'Responsible Person', 'Target Date', 'Status', 'Closure Date',
               'Verification / Comments', 'Overdue?'])
    ws.append(['CA-001', 'INJ-001', 'Bandage + briefing', 'HSE', '',
               'Closed', 'M/DD/YYYY', 'Visual inspection', 'No'])
    ws.append(['CA-012', 'UAC-001', 'Blade collection drive', 'Area owners',
               date(2026, 9, 15), 'Open', '', 'Visual inspection', 'Yes'])
    ws.append(['CA-013', 'UAC-002', 'Hairnet briefing', 'Supervisor', '',
               'Closed', '', 'Visual inspection', 'No'])

    # ---- PTW register: BOTH layouts (mirrors the real sheet's columns:
    #      A empty, B Sr, C Permit No., D Date issue, G nature, H detail,
    #      I-P marks, Q/R location/status in layout B, S/T in layout A)
    ws = wb.create_sheet('Aug-Sep 26')
    ws.append([None])
    ws.append([None, 'UNIT 03 - PERMIT TO WORK DATASHEET MONTH AUGUST'])
    for _ in range(5):
        ws.append([None])
    ws.append([None, 'Sr. No.', 'Permit No.', 'Date issue', 'Department',
               'Company / Contractor', 'Nature of Work', 'Combined Detail',
               'Hot Work', 'Cold Work', 'Work at Height', 'Electrical',
               'Excavation', 'Confined Space', 'Radioactivity', 'Crane',
               'Location', 'Status', 'Location A', 'Status A', 'Remarks'])
    # Layout A (location S=col19, status T=col20; type text J col10)
    ws.append([None, 1, 1, None, None, None, 'HSE',
               'DB Connection and Termination', 'PH(08)',
               'Electrical Work', None, None, None, 'E', None, None,
               None, None, 'LV Panel Room', 'Closed', None])
    # Layout B (location Q=col17, status R=col18; type text = H when J empty)
    ws.append([None, 2, 2, '5/8/2026', 'Mechanical', 'XYZ',
               'Cutting, Welding, Grinding', 'Hot Work', None, None, None,
               None, None, None, None, None, 'Outside Oil Heater Room',
               'Closed'])

    # ---- KPI Calculations (title r1, header r2, data r3-14) ----
    ws = wb.create_sheet('KPI Calculations')
    ws.append(['KPI Calculations (Monthly)'])
    ws.append(['Month', 'Man-hours'])
    for lbl, hrs in [('Jan-26', 0), ('Feb-26', 0), ('Mar-26', 22000),
                     ('Apr-26', 0), ('May-26', 0), ('Jun-26', 0),
                     ('Jul-26', 0), ('Aug-26', 60192), ('Sep-26', 0),
                     ('Oct-26', 0), ('Nov-26', 0), ('Dec-26', 0)]:
        ws.append([lbl, hrs])

    # ---- Leading Indicators (title r1, header r2, data r3+) ----
    ws = wb.create_sheet('Leading Indicators')
    ws.append(['Leading Indicators (Monthly)'])
    ws.append(['Month', 'Planned Inspections', 'Completed Inspections',
               '', 'Toolbox Talks', 'PTW Issued', 'Training Hours',
               'Internal Audit Score'])
    for lbl, vals in [
        ('Jan-26', (0, 0, 0, 0, 0, 0.92)),
        ('Aug-26', (1, 1, 172, 172, 15, None)),
        ('Sep-26', (0, 0, 87, 87, 8, None)),
    ]:
        planned, done, talks, ptw, train, audit = vals
        ws.append([lbl, planned, done, None, talks, ptw, train, audit])

    return wb


@tagged('post_install', '-at_install')
class TestHseExcelRoundtrip(TransactionCase):

    def setUp(self):
        super().setUp()
        self.settings = self.env['hse.safety.settings'].get_settings()
        self.settings.write({'reporting_year': 2026})
        self.env['hse.injury.log'].search([]).unlink()
        self.env['hse.near.miss.log'].search([]).unlink()
        self.env['hse.uac.log'].search([]).unlink()
        self.env['hse.incident.log'].search([]).unlink()
        self.env['hse.corrective.action'].search([]).unlink()
        self.env['hse.ptw.register'].search([]).unlink()
        self.env['hse.monthly.figure'].search([]).unlink()

    def _import(self):
        if openpyxl is None:
            self.skipTest('openpyxl not available')
        buf = io.BytesIO()
        wb = _build_workbook()
        wb.save(buf)
        wizard = self.env['hse.excel.import'].create({
            'file': base64.b64encode(buf.getvalue()),
            'filename': 'safety_dashboard.xlsx',
        })
        wizard.action_import()
        return wizard

    def test_full_roundtrip(self):
        wiz = self._import()

        # --- Injuries: 2 imported, footnote row ignored ---
        inj = self.env['hse.injury.log'].search([])
        self.assertEqual(len(inj), 2, 'both rows kept, footnote skipped')
        i1 = self.env['hse.injury.log'].search([('name', '=', 'INJ-001')])
        self.assertEqual(i1.date, date(2026, 3, 15), 'd/m/y text parsed')
        self.assertEqual(i1.injury_type, 'lti')
        self.assertEqual(i1.lost_workdays, 2)
        self.assertEqual(i1.status, 'closed')
        self.assertTrue(i1.corrective_action_id, 'CA-001 linked')
        i2 = self.env['hse.injury.log'].search([('name', '=', 'INJ-002')])
        self.assertEqual(i2.date, date(2026, 4, 10), 'native date cell')
        self.assertEqual(i2.injury_type, 'first_aid')
        self.assertEqual(i2.status, 'open')
        self.assertFalse(i2.corrective_action_id)

        # --- Near miss ---
        nm = self.env['hse.near.miss.log'].search([('name', '=', 'NM-001')])
        self.assertEqual(nm.date, date(2026, 4, 20))
        self.assertEqual(nm.potential_severity, 'high')
        self.assertFalse(nm.corrective_action_id,
                         'CA-073 does not exist — link stays empty, not invented')

        # --- UAC: text date "05-Sep-2026" must parse ---
        u1 = self.env['hse.uac.log'].search([('name', '=', 'UAC-001')])
        self.assertEqual(u1.date, date(2026, 9, 5))
        self.assertEqual(u1.uac_type, 'unsafe_condition')
        self.assertTrue(u1.corrective_action_id, 'CA-012 linked')

        # --- Incident: d/m/y "12/8/2026" ---
        inc = self.env['hse.incident.log'].search([('name', '=', 'INC-001')])
        self.assertEqual(inc.date, date(2026, 8, 12))
        self.assertEqual(inc.incident_type, 'property_damage')

        # --- CAs ---
        ca1 = self.env['hse.corrective.action'].search([('name', '=', 'CA-001')])
        self.assertEqual(ca1.state, 'closed')
        self.assertFalse(ca1.closure_date,
                         "'M/DD/YYYY' placeholder must NOT become a date")
        ca12 = self.env['hse.corrective.action'].search([('name', '=', 'CA-012')])
        self.assertEqual(ca12.state, 'open')
        self.assertEqual(ca12.target_date, date(2026, 9, 15))
        self.assertEqual(ca12.related_date, date(2026, 9, 5),
                         'CA month attribution via UAC-001')

        # --- PTW: 2 rows, both layouts ---
        ptws = self.env['hse.ptw.register'].search([])
        self.assertEqual(len(ptws), 2)
        ptw_a = self.env['hse.ptw.register'].search([('name', '=', '1')])
        self.assertEqual(ptw_a.location, 'LV Panel Room',
                         'layout A location from column S')
        self.assertEqual(ptw_a.status, 'closed')
        self.assertEqual(ptw_a.type_text, 'Electrical Work',
                         'type text from column J')
        ptw_b = self.env['hse.ptw.register'].search([('name', '=', '2')])
        self.assertEqual(ptw_b.date_issue, date(2026, 8, 5))
        self.assertEqual(ptw_b.location, 'Outside Oil Heater Room',
                         'layout B location from column Q')
        self.assertEqual(ptw_b.type_text, 'Hot Work',
                         'type text from column H when J empty')

        # --- Man-hours ---
        fig3 = self.env['hse.monthly.figure']._find(2026, 3)
        self.assertEqual(fig3.man_hours, 22000)
        fig8 = self.env['hse.monthly.figure']._find(2026, 8)
        self.assertEqual(fig8.man_hours, 60192)

        # --- Leading indicators ---
        self.assertEqual(fig8.toolbox_talks, 172)
        self.assertEqual(fig8.ptw_issued, 172)
        self.assertEqual(fig8.training_hours, 15)
        fig1 = self.env['hse.monthly.figure']._find(2026, 1)
        self.assertAlmostEqual(fig1.audit_score, 0.92)
        fig9 = self.env['hse.monthly.figure']._find(2026, 9)
        self.assertEqual(fig9.toolbox_talks, 87)
        self.assertEqual(fig9.ptw_issued, 87)

        # --- Import log mentions PTW layouts ---
        self.assertIn('both column layouts', wiz.log or '')

    def test_reimport_is_safe(self):
        """Existing IDs are skipped — re-import must not duplicate."""
        self._import()
        n_inj = self.env['hse.injury.log'].search_count([])
        n_ptw = self.env['hse.ptw.register'].search_count([])
        wiz2 = self._import()
        self.assertEqual(self.env['hse.injury.log'].search_count([]), n_inj)
        self.assertEqual(self.env['hse.ptw.register'].search_count([]), n_ptw)
        self.assertIn('skipped', wiz2.log or '')

    def test_dashboard_after_import(self):
        """After import the engine mirrors the Excel live numbers."""
        self._import()
        engine = self.env['hse.kpi.engine']
        aug = engine.month_stats(2026, 8)
        self.assertEqual(aug['man_hours'], 60192)
        self.assertEqual(aug['ptw_issued'], 172)
        self.assertEqual(aug['ptw_register_rows'], 1, 'one dated PTW row in Aug')
        self.assertEqual(aug['toolbox_talks'], 172)
        sep = engine.month_stats(2026, 9)
        self.assertEqual(sep['toolbox_talks'], 87)
        # health checks fire on the imported workbook's real gaps
        checks = {c['no']: c for c in engine.health_checks(2026)}
        self.assertGreater(checks[1]['count'], 0, 'one PTW row has no date')
        self.assertEqual(checks[9]['count'], 2,
                         'Aug (1 register row vs 172 entered) and '
                         'Sep (0 vs 87) mismatch — same as the Excel')
