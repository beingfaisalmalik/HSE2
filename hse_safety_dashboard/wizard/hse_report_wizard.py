# -*- coding: utf-8 -*-
import base64
import io
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:  # pragma: no cover
    xlsxwriter = None

MONTHS = [(str(i), n) for i, n in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July',
     'August', 'September', 'October', 'November', 'December'], start=1)]


class HseReportWizard(models.TransientModel):
    """Pick a month (or full year) and generate the safety reports."""
    _name = 'hse.report.wizard'
    _description = 'HSE Safety Report Wizard'

    year = fields.Integer(
        string='Year', required=True,
        default=lambda self: self.env['hse.safety.settings'].get_settings().reporting_year)
    month = fields.Selection(MONTHS, string='Month',
                             help="Leave empty for the full-year report.")
    report_type = fields.Selection(
        [('monthly_pdf', 'Monthly Dashboard (PDF)'),
         ('yearly_pdf', 'Yearly Report (PDF)'),
         ('xlsx', 'Excel Workbook (XLSX — KPI + registers + health checks)')],
        string='Report', required=True, default='monthly_pdf')

    def action_generate(self):
        self.ensure_one()
        if self.report_type == 'xlsx':
            return self._generate_xlsx()
        # PDF via QWeb report action
        report_ref = ('hse_safety_dashboard.action_report_hse_monthly'
                      if self.report_type == 'monthly_pdf'
                      else 'hse_safety_dashboard.action_report_hse_yearly')
        return self.env.ref(report_ref).report_action(self)

    # ------------------------------------------------------------------
    def _engine(self):
        return self.env['hse.kpi.engine']

    def _payload(self):
        engine = self._engine()
        month_no = int(self.month) if self.month else 12
        data = engine.get_dashboard(self.year, month_no)
        if not self.month:
            data['ytd_only'] = True
            data['month_name'] = str(self.year)
        return data

    def get_payload(self):
        """Entry point used by the QWeb report templates."""
        self.ensure_one()
        return self._payload()

    # ------------------------------------------------------------------
    def _generate_xlsx(self):
        if xlsxwriter is None:
            raise UserError(_('The XlsxWriter Python library is required for Excel export.'))
        engine = self._engine()
        year = self.year
        month_no = int(self.month) if self.month else 12
        data = engine.get_dashboard(year, month_no)
        settings = self.env['hse.safety.settings'].get_settings()

        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})

        title = wb.add_format({'bold': True, 'font_size': 14})
        header = wb.add_format({'bold': True, 'bg_color': '#DDEBF7', 'border': 1})
        cell = wb.add_format({'border': 1})
        num = wb.add_format({'border': 1, 'num_format': '#,##0'})
        rate = wb.add_format({'border': 1, 'num_format': '0.00'})
        pct = wb.add_format({'border': 1, 'num_format': '0%'})
        warn = wb.add_format({'border': 1, 'font_color': '#C00000', 'bold': True})

        # ---------------- KPI sheet ----------------
        ws = wb.add_worksheet('KPI Calculations')
        ws.set_column('A:A', 30)
        ws.set_column('B:AZ', 12)
        ws.write(0, 0, 'HSE Safety KPIs — %s (rate base %s)' % (
            data['month_name'], int(settings.rate_base)), title)
        cols = [
            ('Month', 'label'), ('Man-hours', 'man_hours'), ('LTI', 'lti'),
            ('MTC', 'mtc'), ('First Aid', 'first_aid'),
            ('Recordable', 'recordable'), ('All injuries', 'all_injuries'),
            ('Lost workdays', 'lost_workdays'), ('Near misses', 'near_misses'),
            ('Unsafe acts', 'unsafe_acts'), ('Unsafe cond.', 'unsafe_conditions'),
            ('Observations', 'observations'), ('Incidents', 'incidents'),
            ('CAs linked', 'ca_linked'), ('CAs closed', 'ca_closed'),
            ('CAs open', 'ca_open'), ('CAs overdue', 'ca_overdue'),
            ('CA closure %', 'ca_closure_rate'),
            ('PTW issued', 'ptw_issued'), ('PTW register', 'ptw_register_rows'),
            ('Talks', 'toolbox_talks'), ('Training h', 'training_hours'),
            ('Insp. planned', 'insp_planned'), ('Insp. done', 'insp_completed'),
            ('Insp. %', 'insp_compliance'), ('Audit', 'audit_score'),
            ('LTIFR', 'ltifr'), ('TRIR', 'trir'), ('Severity', 'severity'),
        ]
        for i, (label, _key) in enumerate(cols):
            ws.write(2, i, label, header)
        for r, m in enumerate(data['months'], start=3):
            for i, (_label, key) in enumerate(cols):
                v = m.get(key)
                if v is None:
                    ws.write(r, i, 'n/a', cell)
                elif key in ('ltifr', 'trir', 'severity'):
                    ws.write_number(r, i, v, rate)
                elif key in ('ca_closure_rate', 'insp_compliance'):
                    ws.write_number(r, i, v, pct)
                elif isinstance(v, (int, float)):
                    ws.write_number(r, i, v, num)
                else:
                    ws.write(r, i, v, cell)
        # YTD rows
        for row_i, (label, block) in enumerate(
                [('YTD (full year)', data['ytd_full']),
                 ('YTD to %s' % data['month_label'], data['ytd_to_month'])],
                start=16):
            ws.write(row_i, 0, label, header)
            for i, (_lbl, key) in enumerate(cols[1:], start=1):
                v = block.get(key)
                if v is None:
                    ws.write(row_i, i, 'n/a', cell)
                elif key in ('ltifr', 'trir', 'severity'):
                    ws.write_number(row_i, i, v, rate)
                elif key in ('ca_closure_rate', 'insp_compliance'):
                    ws.write_number(row_i, i, v, pct)
                elif isinstance(v, (int, float)):
                    ws.write_number(row_i, i, v, num)
                else:
                    ws.write(row_i, i, v, cell)

        # ---------------- Registers ----------------
        def sheet(name, headers, rows, widths):
            s = wb.add_worksheet(name)
            for i, h in enumerate(headers):
                s.write(0, i, h, header)
                s.set_column(i, i, widths[i])
            for r, row in enumerate(rows, start=1):
                for c, val in enumerate(row):
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        s.write_number(r, c, val, num)
                    else:
                        s.write(r, c, val or '', cell)
            return s

        reg = data['registers']
        sheet('Injury Log',
              ['Injury ID', 'Date', 'Type', 'Department', 'Person',
               'Lost Workdays', 'Status', 'Description'],
              [[r['name'], r['date'], r['type'], r['department'], r['person'],
                r['lost_workdays'], r['status'], r['desc']]
               for r in reg['injuries']],
              [12, 14, 22, 18, 20, 14, 10, 60])
        sheet('Near Miss Log',
              ['Near-Miss ID', 'Date', 'Department', 'Severity', 'Reported By',
               'Status', 'Description'],
              [[r['name'], r['date'], r['department'], r['severity'],
                r['reported_by'], r['status'], r['desc']]
               for r in reg['near_misses']],
              [14, 14, 18, 12, 22, 10, 60])
        sheet('UnsafeAct Condition Log',
              ['Observation ID', 'Date', 'Type', 'Department', 'Reported By',
               'Status', 'Description'],
              [[r['name'], r['date'], r['type'], r['department'],
                r['reported_by'], r['status'], r['desc']]
               for r in reg['uacs']],
              [16, 14, 20, 22, 20, 10, 60])
        sheet('Incident Log',
              ['Incident ID', 'Date', 'Type', 'Department', 'Area/Asset',
               'Estimated Impact', 'Status', 'Description'],
              [[r['name'], r['date'], r['type'], r['department'], r['area'],
                r['impact'], r['status'], r['desc']]
               for r in reg['incidents']],
              [14, 14, 18, 18, 22, 18, 10, 60])

        ca_env = self.env['hse.corrective.action']
        ca_rows = []
        for ca in ca_env.search([]):
            ca_rows.append([ca.name, ca.related_display,
                            (ca.action_description or '')[:200],
                            ca.responsible_person or '',
                            ca.target_date.isoformat() if ca.target_date else '',
                            dict(ca._fields['state'].selection).get(ca.state, ''),
                            ca.closure_date.isoformat() if ca.closure_date else '',
                            (ca.verification or '')[:200],
                            'Yes' if ca.overdue else 'No'])
        sheet('Corrective Actions',
              ['CA ID', 'Related Log Entry ID', 'Action Description',
               'Responsible', 'Target Date', 'Status', 'Closure Date',
               'Verification', 'Overdue?'],
              ca_rows,
              [10, 18, 60, 20, 14, 12, 14, 40, 10])

        ptw_rows = []
        for p in self.env['hse.ptw.register'].search([]):
            ptw_rows.append([p.name,
                             p.date_issue.isoformat() if p.date_issue else '',
                             p.department or '', p.contractor or '',
                             p.nature_of_work or '', p.type_text or '',
                             p.location or '',
                             dict(p._fields['status'].selection).get(p.status, '')])
        sheet('PTW Register',
              ['PTW No.', 'Date', 'Department', 'Company / Contractor',
               'Nature of Work', 'Permit Type', 'Location', 'Status'],
              ptw_rows,
              [12, 14, 18, 24, 28, 34, 24, 10])

        fig_rows = []
        for f in self.env['hse.monthly.figure'].search(
                [('year', '=', year)], order='month'):
            fig_rows.append([f.label, f.man_hours, f.planned_inspections,
                             f.completed_inspections, f.toolbox_talks,
                             f.ptw_issued, f.training_hours, f.audit_score])
        sheet('Leading Indicators',
              ['Month', 'Man-hours', 'Insp. Planned', 'Insp. Completed',
               'Talks', 'PTW Issued', 'Training Hours', 'Audit Score'],
              fig_rows,
              [16, 14, 14, 16, 10, 12, 16, 14])

        # ---------------- Data health ----------------
        hs = wb.add_worksheet('Data Health')
        hs.set_column('A:A', 5)
        hs.set_column('B:B', 90)
        hs.set_column('C:C', 10)
        hs.set_column('D:D', 70)
        hs.write(0, 0, 'DATA HEALTH — items that can make the numbers look '
                       'better or worse than reality', title)
        hs.write(1, 0, '#', header)
        hs.write(1, 1, 'Check', header)
        hs.write(1, 2, 'Count', header)
        hs.write(1, 3, 'Detail', header)
        for i, chk in enumerate(data['health'], start=2):
            fmt = warn if not chk['ok'] else cell
            hs.write_number(i, 0, chk['no'], cell)
            hs.write(i, 1, chk['label'], cell)
            hs.write_number(i, 2, chk['count'], fmt)
            hs.write(i, 3, chk['detail'], cell)
        wb.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'HSE_Safety_KPIs_%s%s.xlsx' % (
                year, '_%02d' % month_no if self.month else ''),
            'type': 'binary',
            'datas': base64.b64encode(buf.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
