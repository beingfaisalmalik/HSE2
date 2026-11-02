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

# One report per workflow — every register of the suite is reportable.
WORKFLOW_REPORTS = {
    'injury_pdf': 'Injury Log Report',
    'near_miss_pdf': 'Near-Miss Log Report',
    'uac_pdf': 'Unsafe Act / Condition Report',
    'incident_pdf': 'Incident Log Report',
    'ca_pdf': 'Corrective Actions Report',
    'ptw_pdf': 'PTW Register Report',
    'figures_pdf': 'Monthly Figures Report',
}


class HseReportWizard(models.TransientModel):
    """Pick a dynamic period (year / month) and generate any safety report.

    Every choice — year options, month options on the dashboard, departments
    and statuses offered here — is derived from the data itself, never
    hardcoded.  Workflow reports are filtered by period + department + status;
    entries that can never fall inside the period (no date at all) are shown
    in a clearly labelled section instead of being silently dropped.
    """
    _name = 'hse.report.wizard'
    _description = 'HSE Safety Report Wizard'

    # ------------------------------------------------------------- fields
    year = fields.Selection(
        selection='_selection_year',
        string='Year', required=True,
        default=lambda self: str(
            self.env['hse.safety.settings'].get_settings().reporting_year),
        help='Years present in the registers / monthly figures (data-driven).')
    month = fields.Selection(MONTHS, string='Month',
                             help="Leave empty for the full-year report.")
    department = fields.Selection(
        selection='_selection_department',
        string='Department', default='all',
        help='Filters the workflow/register reports. “All departments” '
             'shows everything.')
    status_filter = fields.Selection(
        [('all', 'All statuses'), ('open', 'Open / not closed'),
         ('closed', 'Closed / expired')],
        string='Status', default='all',
        help='Filters the workflow/register reports by status '
             '(applies where the register has one).')
    report_type = fields.Selection(
        [('monthly_pdf', 'Monthly Dashboard (PDF)'),
         ('yearly_pdf', 'Yearly Report (PDF)'),
         ('kpi_pdf', 'KPI Calculations (PDF)'),
         ('leading_pdf', 'Leading Indicators (PDF)'),
         ('injury_pdf', 'Injury Log Report (PDF)'),
         ('near_miss_pdf', 'Near-Miss Log Report (PDF)'),
         ('uac_pdf', 'Unsafe Act / Condition Report (PDF)'),
         ('incident_pdf', 'Incident Log Report (PDF)'),
         ('ca_pdf', 'Corrective Actions Report (PDF)'),
         ('ptw_pdf', 'PTW Register Report (PDF)'),
         ('figures_pdf', 'Monthly Figures Report (PDF)'),
         ('xlsx', 'Excel Workbook (XLSX — KPI + registers + health checks)')],
        string='Report', required=True, default='monthly_pdf')

    # ------------------------------------------------ dynamic selections
    @api.model
    def _selection_year(self):
        """Year options straight from the data (newest first)."""
        engine = self.env['hse.kpi.engine']
        return [(str(y), str(y)) for y in engine.available_years()]

    @api.model
    def _selection_department(self):
        """Department options = every distinct department on the registers."""
        deps = set()
        for model in ('hse.injury.log', 'hse.near.miss.log',
                      'hse.uac.log', 'hse.incident.log', 'hse.ptw.register'):
            for d in self.env[model].search([]).mapped('department'):
                if d:
                    deps.add(d)
        return [('all', 'All departments')] + [(d, d) for d in sorted(deps)]

    # ----------------------------------------------------------- routing
    def action_generate(self):
        self.ensure_one()
        if self.report_type == 'xlsx':
            return self._generate_xlsx()
        return self.env.ref(self._report_xmlid()).report_action(self)

    def _report_xmlid(self):
        fixed = {
            'monthly_pdf': 'hse_safety_dashboard.action_report_hse_monthly',
            'yearly_pdf': 'hse_safety_dashboard.action_report_hse_yearly',
            'kpi_pdf': 'hse_safety_dashboard.action_report_hse_kpi',
            'leading_pdf': 'hse_safety_dashboard.action_report_hse_leading',
        }
        if self.report_type in fixed:
            return fixed[self.report_type]
        return 'hse_safety_dashboard.action_report_hse_workflow'

    # ----------------------------------------------------------- payload
    def _engine(self):
        return self.env['hse.kpi.engine']

    def _payload(self):
        engine = self._engine()
        year = int(self.year)
        month_no = int(self.month) if self.month else 12
        data = engine.get_dashboard(year, month_no)
        if not self.month:
            data['ytd_only'] = True
            data['month_name'] = str(year)
        return data

    def get_payload(self):
        """Entry point used by the QWeb report templates."""
        self.ensure_one()
        return self._payload()

    # --------------------------------------------- period / filter helpers
    def _period_label(self):
        year = int(self.year)
        if self.month:
            return '%s %s' % (dict(MONTHS)[self.month], year)
        return '%s (full year)' % year

    def _in_period(self, d):
        if not d or d.year != int(self.year):
            return False
        if self.month and d.month != int(self.month):
            return False
        return True

    def _dept_ok(self, rec):
        if not self.department or self.department == 'all':
            return True
        return (rec.department or '') == self.department

    def _filters_label(self, report_type):
        parts = ['Period: %s' % self._period_label()]
        has_dept = report_type not in ('ca_pdf', 'figures_pdf')
        if has_dept and self.department and self.department != 'all':
            parts.append('Department: %s' % self.department)
        if self.status_filter != 'all' and report_type != 'figures_pdf':
            parts.append('Status: %s' % dict(
                self._fields['status_filter'].selection)[self.status_filter])
        return '  ·  '.join(parts)

    @api.model
    def _fmt_date(self, d):
        return d.strftime('%d-%b-%Y') if d else ''

    @staticmethod
    def _clip(text, n=200):
        text = text or ''
        return text if len(text) <= n else text[:n - 1] + '…'

    # --------------------------------------------------- workflow reports
    def workflow_rows(self, report_type=None, display=True):
        """Rows for one workflow report, filtered by year (+ month,
        department, status).  Returns title / period / headers / rows plus an
        `unmatched` bucket: entries with no date (or a corrective action
        whose related entry has no date) can never fall inside the period,
        so they are reported separately instead of vanishing."""
        self.ensure_one()
        rt = report_type or self.report_type
        if rt not in WORKFLOW_REPORTS:
            raise UserError(_('Not a workflow report: %s') % rt)
        year = int(self.year)
        title = WORKFLOW_REPORTS[rt]
        headers, rows, unmatched = [], [], []

        def _status_ok_log(rec):
            if self.status_filter == 'all':
                return True
            if self.status_filter == 'open':
                return rec.status == 'open'
            return rec.status == 'closed'

        if rt == 'injury_pdf':
            headers = ['Injury ID', 'Date', 'Type', 'Department', 'Person',
                       'Lost Workdays', 'Status', 'Description']
            for r in self.env['hse.injury.log'].search([], order='name'):
                if not self._dept_ok(r) or not _status_ok_log(r):
                    continue
                row = [r.name, self._fmt_date(r.date), r._type_label(),
                       r.department or '', r.person_involved or '',
                       r.lost_workdays or 0,
                       dict(r._fields['status'].selection).get(r.status, ''),
                       self._clip(r.description)]
                if not r.date:
                    unmatched.append(row)
                elif self._in_period(r.date):
                    rows.append(row)

        elif rt == 'near_miss_pdf':
            headers = ['Near-Miss ID', 'Date', 'Department', 'Severity',
                       'Reported By', 'Status', 'Description']
            for r in self.env['hse.near.miss.log'].search([], order='name'):
                if not self._dept_ok(r) or not _status_ok_log(r):
                    continue
                row = [r.name, self._fmt_date(r.date), r.department or '',
                       dict(r._fields['potential_severity'].selection).get(
                           r.potential_severity, ''),
                       r.reported_by or '',
                       dict(r._fields['status'].selection).get(r.status, ''),
                       self._clip(r.description)]
                if not r.date:
                    unmatched.append(row)
                elif self._in_period(r.date):
                    rows.append(row)

        elif rt == 'uac_pdf':
            headers = ['Observation ID', 'Date', 'Type', 'Department',
                       'Reported By', 'Status', 'Description']
            for r in self.env['hse.uac.log'].search([], order='name'):
                if not self._dept_ok(r) or not _status_ok_log(r):
                    continue
                row = [r.name, self._fmt_date(r.date), r._type_label(),
                       r.department or '', r.reported_by or '',
                       dict(r._fields['status'].selection).get(r.status, ''),
                       self._clip(r.description)]
                if not r.date:
                    unmatched.append(row)
                elif self._in_period(r.date):
                    rows.append(row)

        elif rt == 'incident_pdf':
            headers = ['Incident ID', 'Date', 'Type', 'Department',
                       'Area / Asset', 'Estimated Impact', 'Status',
                       'Description']
            for r in self.env['hse.incident.log'].search([], order='name'):
                if not self._dept_ok(r) or not _status_ok_log(r):
                    continue
                row = [r.name, self._fmt_date(r.date), r._type_label(),
                       r.department or '', r.area_asset or '',
                       r.estimated_impact or '',
                       dict(r._fields['status'].selection).get(r.status, ''),
                       self._clip(r.description)]
                if not r.date:
                    unmatched.append(row)
                elif self._in_period(r.date):
                    rows.append(row)

        elif rt == 'ca_pdf':
            headers = ['CA ID', 'Related Log Entry ID', 'Action Description',
                       'Responsible', 'Target Date', 'Status', 'Closure Date',
                       'Verification', 'Overdue?']
            for r in self.env['hse.corrective.action'].search(
                    [], order='name'):
                if self.status_filter != 'all':
                    is_closed = r.state == 'closed'
                    if self.status_filter == 'closed' and not is_closed:
                        continue
                    if self.status_filter == 'open' and is_closed:
                        continue
                row = [r.name, r.related_display or r.related_ref or '',
                       self._clip(r.action_description),
                       r.responsible_person or '',
                       self._fmt_date(r.target_date),
                       dict(r._fields['state'].selection).get(r.state, ''),
                       self._fmt_date(r.closure_date),
                       self._clip(r.verification),
                       'Yes' if r.overdue else 'No']
                if not r.related_date:
                    # no resolvable related-entry date — can never be placed
                    # inside the period; keep it visible, never invent one
                    unmatched.append(row)
                elif self._in_period(r.related_date):
                    rows.append(row)

        elif rt == 'ptw_pdf':
            headers = ['PTW No.', 'Date', 'Department',
                       'Company / Contractor', 'Nature of Work',
                       'Permit Type', 'Location', 'Status']
            for r in self.env['hse.ptw.register'].search([], order='name'):
                if not self._dept_ok(r):
                    continue
                if self.status_filter != 'all':
                    if self.status_filter == 'open' and r.status != 'open':
                        continue
                    if self.status_filter == 'closed' \
                            and r.status not in ('closed', 'expired'):
                        continue
                row = [r.name, self._fmt_date(r.date_issue),
                       r.department or '', r.contractor or '',
                       r.nature_of_work or '', r.type_text or '',
                       r.location or '',
                       dict(r._fields['status'].selection).get(r.status, '')]
                if not r.date_issue:
                    unmatched.append(row)
                elif self._in_period(r.date_issue):
                    rows.append(row)

        elif rt == 'figures_pdf':
            headers = ['Month', 'Man-hours', 'Insp. Planned',
                       'Insp. Completed', 'Talks', 'PTW Issued',
                       'Training Hours', 'Audit Score']
            figures = self.env['hse.monthly.figure'].search(
                [('year', '=', year)], order='month')
            for f in figures:
                if self.month and str(f.month) != str(int(self.month)):
                    continue

                def _num(v):
                    if display and isinstance(v, float):
                        return '%g' % v
                    return v

                def _audit(v):
                    # 0 / blank = "no audit entered" → n/a, never a fake 0.00
                    if not v:
                        return 'n/a'
                    return '%0.2f' % v if display else v
                rows.append([
                    self._engine().month_label(year, int(f.month)),
                    _num(f.man_hours), f.planned_inspections or 0,
                    f.completed_inspections or 0, f.toolbox_talks or 0,
                    f.ptw_issued or 0, _num(f.training_hours),
                    _audit(f.audit_score)])

        if display:
            # PDF safety: the PDF engine sizes table columns from content —
            # a very long cell in a narrow column can become taller than the
            # page and abort the render.  Clip text for display only; the
            # Excel export keeps full values.
            def _safe(row):
                return [self._clip(v, 120) if isinstance(v, str) else v
                        for v in row]
            rows = [_safe(r) for r in rows]
            unmatched = [_safe(r) for r in unmatched]
        return {
            'title': title,
            'period': self._period_label(),
            'filters': self._filters_label(rt),
            'report_date': fields.Date.context_today(self),
            'headers': headers,
            'rows': rows,
            'count': len(rows),
            'empty_note': _('No records match the selected filters for %s.'
                            ) % self._period_label(),
            'unmatched_headers': headers,
            'unmatched': unmatched,
            'unmatched_count': len(unmatched),
        }

    def get_workflow(self):
        """Entry point used by the workflow QWeb report template."""
        self.ensure_one()
        return self.workflow_rows()

    # ------------------------------------------------------------------
    def _generate_xlsx(self):
        if xlsxwriter is None:
            raise UserError(_('The XlsxWriter Python library is required for Excel export.'))
        engine = self._engine()
        year = int(self.year)
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

        # ---------------- Registers (same dynamic filters as the PDFs) --
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

        def wf_sheet(name, rt, widths):
            wf = self.workflow_rows(rt, display=False)
            return sheet(name, wf['headers'], wf['rows'] + wf['unmatched'],
                         widths)

        wf_sheet('Injury Log', 'injury_pdf',
                 [12, 14, 22, 18, 20, 14, 10, 60])
        wf_sheet('Near Miss Log', 'near_miss_pdf',
                 [14, 14, 18, 12, 22, 10, 60])
        wf_sheet('UnsafeAct Condition Log', 'uac_pdf',
                 [16, 14, 20, 22, 20, 10, 60])
        wf_sheet('Incident Log', 'incident_pdf',
                 [14, 14, 18, 18, 22, 18, 10, 60])
        wf_sheet('Corrective Actions', 'ca_pdf',
                 [10, 18, 60, 20, 14, 12, 14, 40, 10])
        wf_sheet('PTW Register', 'ptw_pdf',
                 [12, 14, 18, 24, 28, 34, 24, 10])
        wf_sheet('Leading Indicators', 'figures_pdf',
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
