# -*- coding: utf-8 -*-
import io
import re
from datetime import date, datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None

MONTH_NAMES = {m.lower(): i for i, m in enumerate(
    ['january', 'february', 'march', 'april', 'may', 'june', 'july',
     'august', 'september', 'october', 'november', 'december'], start=1)}
MONTH_NAMES.update({m[:3].lower(): i for m, i in list(MONTH_NAMES.items())})


def parse_excel_date(value):
    """Replicate the CalcRows date parser:
    ISNUMBER passthrough → d/m/y text (2-digit year gets +2000) → DATEVALUE
    fallback (month names, ISO). Returns a date or None."""
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        # Excel serial date
        try:
            return datetime(1899, 12, 30).date() + __import__('datetime').timedelta(days=int(value))
        except Exception:
            return None
    text = str(value).strip()
    if not text:
        return None
    # d/m/y with -, . or / separators (CalcRows SUBSTITUTE to "/")
    norm = re.sub(r'[-.]', '/', text)
    parts = [p for p in norm.split('/') if p != '']
    if len(parts) == 3:
        try:
            a, b, c = parts
            # Excel formula: DATE(year, second, first) → day=first, month=second
            day, month, year = int(a), int(b), int(c)
            if year < 100:
                year += 2000
            return date(year, month, day)
        except ValueError:
            pass
        # month-name fallback: 05-Sep-2026, Sep-2026, ...
        m = re.match(r'^(\d{1,2})[-/ ]([A-Za-z]{3,9})[-/ ,]+(\d{2,4})$', text)
        if m:
            d, mon, y = m.groups()
            mon_i = MONTH_NAMES.get(mon.lower())
            if mon_i:
                year = int(y)
                if year < 100:
                    year += 2000
                try:
                    return date(year, mon_i, int(d))
                except ValueError:
                    return None
    # ISO yyyy-mm-dd
    try:
        return datetime.strptime(text, '%Y-%m-%d').date()
    except ValueError:
        pass
    m = re.match(r'^([A-Za-z]{3,9})[-/ ](\d{2,4})$', text)
    if m:
        mon_i = MONTH_NAMES.get(m.group(1).lower())
        if mon_i:
            year = int(m.group(2))
            if year < 100:
                year += 2000
            return date(year, mon_i, 1)
    return None


class HseExcelImport(models.TransientModel):
    """Import the client's Safety Dashboard workbook into the Odoo registers."""
    _name = 'hse.excel.import'
    _description = 'Import Safety Dashboard Excel Workbook'

    file = fields.Binary(string='Workbook (.xlsx)', required=True)
    filename = fields.Char()
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             default='draft')
    log = fields.Text(string='Import Log', readonly=True)

    # ------------------------------------------------------------------
    @api.model
    def _rows(self, ws, start_row, cols):
        """Yield (row_no, {key: value}) for rows that have an ID in column A/B."""
        for r in range(start_row, ws.max_row + 1):
            row = {}
            for key, col in cols.items():
                row[key] = ws.cell(r, col).value
            if not any(v not in (None, '') for v in row.values()):
                continue
            yield r, row

    def _clean_text(self, v):
        return str(v).strip() if v not in (None, '') else ''

    @api.model
    def _valid_id(self, value, prefix):
        """Accept only real register IDs like INJ-001 / NM-12 / CA-073 —
        footnote text rows in the workbook are ignored."""
        if not value:
            return False
        return bool(re.match(r'^%s-\d+$' % re.escape(prefix),
                             str(value).strip(), re.IGNORECASE))

    def action_import(self):
        self.ensure_one()
        if openpyxl is None:
            raise UserError(_('The openpyxl Python library is required for Excel import.'))
        if not self.filename or not self.filename.lower().endswith(('.xlsx', '.xlsm')):
            raise UserError(_('Please upload an .xlsx workbook.'))
        try:
            wb = openpyxl.load_workbook(io.BytesIO(
                base64_decode(self.file)), data_only=True)
        except Exception as e:
            raise UserError(_('Could not read the workbook: %s') % e)

        lines = []
        stats = {}
        # --- Corrective Actions FIRST: the logs link to them by CA ID -----
        if 'Corrective Actions' in wb.sheetnames:
            stats['cas'] = self._import_cas(wb['Corrective Actions'], lines)
        # --- Injury Log --------------------------------------------------
        if 'Injury Log' in wb.sheetnames:
            ws = wb['Injury Log']
            n = self._import_injuries(ws, lines)
            stats['injuries'] = n
        # --- Near Miss Log ----------------------------------------------
        if 'Near Miss Log' in wb.sheetnames:
            ws = wb['Near Miss Log']
            stats['near_misses'] = self._import_near_misses(ws, lines)
        # --- UnsafeAct Condition Log -------------------------------------
        uac_sheet = next((s for s in wb.sheetnames if s.startswith('UnsafeAct')),
                         None)
        if uac_sheet:
            stats['uacs'] = self._import_uacs(wb[uac_sheet], lines)
        # --- Incident Log -------------------------------------------------
        if 'Incident Log' in wb.sheetnames:
            stats['incidents'] = self._import_incidents(wb['Incident Log'], lines)
        # --- PTW register (any sheet whose row 2 screams PERMIT TO WORK) ---
        ptw_sheet = None
        for s in wb.sheetnames:
            ws = wb[s]
            head = ' '.join(str(ws.cell(r, c).value or '')
                            for r in (1, 2) for c in range(1, 8))
            if 'PERMIT TO WORK' in head.upper():
                ptw_sheet = ws
                break
        if ptw_sheet is not None:
            stats['ptw'] = self._import_ptw(ptw_sheet, lines)
        # --- KPI Calculations (man-hours col B) ----------------------------
        if 'KPI Calculations' in wb.sheetnames:
            stats['man_hours'] = self._import_man_hours(wb['KPI Calculations'], lines)
        # --- Leading Indicators --------------------------------------------
        if 'Leading Indicators' in wb.sheetnames:
            stats['leading'] = self._import_leading(wb['Leading Indicators'], lines)

        header = _('Import complete: %(inj)s injuries · %(nm)s near misses · '
                   '%(uac)s observations · %(inc)s incidents · %(ca)s CAs · '
                   '%(ptw)s PTW · %(mh)s man-hour rows · %(ld)s leading rows') % {
            'inj': stats.get('injuries', 0), 'nm': stats.get('near_misses', 0),
            'uac': stats.get('uacs', 0), 'inc': stats.get('incidents', 0),
            'ca': stats.get('cas', 0), 'ptw': stats.get('ptw', 0),
            'mh': stats.get('man_hours', 0), 'ld': stats.get('leading', 0)}
        self.write({'state': 'done',
                    'log': header + '\n\n' + '\n'.join(lines)})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ------------------------------------------------------------------
    def _import_injuries(self, ws, lines):
        Injury = self.env['hse.injury.log']
        type_map = {'lost time injury': 'lti',
                    'medical treatment case': 'mtc',
                    'first aid case': 'first_aid'}
        n = 0
        for r, row in self._rows(ws, 3, {
                'id': 1, 'date': 2, 'type': 3, 'dept': 4, 'desc': 5,
                'person': 6, 'days': 7, 'cause': 8, 'ca': 9, 'status': 10}):
            name = self._clean_text(row['id'])
            if not self._valid_id(name, 'INJ'):
                continue
            if Injury.search([('name', '=', name)], limit=1):
                lines.append('· %s skipped (already exists)' % name)
                continue
            d = parse_excel_date(row['date'])
            if row['date'] and not d:
                lines.append('· %s: unreadable date %r left empty' % (name, row['date']))
            vals = {
                'name': name,
                'date': d,
                'injury_type': type_map.get(self._clean_text(row['type']).lower(), 'mtc'),
                'department': self._clean_text(row['dept']),
                'description': self._clean_text(row['desc']),
                'person_involved': self._clean_text(row['person']),
                'lost_workdays': int(row['days'] or 0),
                'root_cause': self._clean_text(row['cause']),
                'status': 'closed' if self._clean_text(row['status']).lower() == 'closed' else 'open',
            }
            ca = self._find_ca(self._clean_text(row['ca']))
            if ca:
                vals['corrective_action_id'] = ca.id
            rec = Injury.create(vals)
            n += 1
            if not d:
                lines.append('· %s imported WITHOUT a date (data gap kept — '
                             'will appear in health check 1)' % name)
        return n

    def _import_near_misses(self, ws, lines):
        Model = self.env['hse.near.miss.log']
        sev_map = {'low': 'low', 'medium': 'medium', 'med': 'medium', 'high': 'high'}
        n = 0
        for r, row in self._rows(ws, 3, {
                'id': 1, 'date': 2, 'dept': 3, 'desc': 4, 'sev': 5,
                'by': 6, 'ca': 7, 'status': 8}):
            name = self._clean_text(row['id'])
            if not self._valid_id(name, 'NM') or Model.search([('name', '=', name)], limit=1):
                continue
            vals = {
                'name': name,
                'date': parse_excel_date(row['date']),
                'department': self._clean_text(row['dept']),
                'description': self._clean_text(row['desc']),
                'potential_severity': sev_map.get(
                    self._clean_text(row['sev']).lower(), 'medium'),
                'reported_by': self._clean_text(row['by']),
                'status': 'closed' if self._clean_text(row['status']).lower() == 'closed' else 'open',
            }
            ca = self._find_ca(self._clean_text(row['ca']))
            if ca:
                vals['corrective_action_id'] = ca.id
            Model.create(vals)
            n += 1
        return n

    def _import_uacs(self, ws, lines):
        Model = self.env['hse.uac.log']
        type_map = {'unsafe act': 'unsafe_act', 'unsafe condition': 'unsafe_condition'}
        n = 0
        for r, row in self._rows(ws, 3, {
                'id': 1, 'date': 2, 'type': 3, 'dept': 4, 'desc': 5,
                'by': 6, 'action': 7, 'ca': 8, 'status': 9}):
            name = self._clean_text(row['id'])
            if not self._valid_id(name, 'UAC') or Model.search([('name', '=', name)], limit=1):
                continue
            t = self._clean_text(row['type']).lower()
            if t not in type_map:
                lines.append('· %s: invalid type %r → kept as Unsafe Act '
                             '(was data-health check 8 in Excel)' % (name, row['type']))
            vals = {
                'name': name,
                'date': parse_excel_date(row['date']),
                'uac_type': type_map.get(t, 'unsafe_act'),
                'department': self._clean_text(row['dept']),
                'description': self._clean_text(row['desc']),
                'reported_by': self._clean_text(row['by']),
                'immediate_action': self._clean_text(row['action']),
                'status': 'closed' if self._clean_text(row['status']).lower() == 'closed' else 'open',
            }
            ca = self._find_ca(self._clean_text(row['ca']))
            if ca:
                vals['corrective_action_id'] = ca.id
            Model.create(vals)
            n += 1
        return n

    def _import_incidents(self, ws, lines):
        Model = self.env['hse.incident.log']
        type_map = {'property damage': 'property_damage',
                    'environmental': 'environmental',
                    'fire/explosion': 'fire_explosion',
                    'fire / explosion': 'fire_explosion',
                    'process safety': 'process_safety',
                    'security': 'security'}
        n = 0
        for r, row in self._rows(ws, 3, {
                'id': 1, 'date': 2, 'type': 3, 'dept': 4, 'desc': 5,
                'area': 6, 'impact': 7, 'cause': 8, 'ca': 9, 'status': 10}):
            name = self._clean_text(row['id'])
            if not self._valid_id(name, 'INC') or Model.search([('name', '=', name)], limit=1):
                continue
            vals = {
                'name': name,
                'date': parse_excel_date(row['date']),
                'incident_type': type_map.get(
                    self._clean_text(row['type']).lower(), 'other'),
                'department': self._clean_text(row['dept']),
                'description': self._clean_text(row['desc']),
                'area_asset': self._clean_text(row['area']),
                'estimated_impact': self._clean_text(row['impact']),
                'root_cause': self._clean_text(row['cause']),
                'status': 'closed' if self._clean_text(row['status']).lower() == 'closed' else 'open',
            }
            ca = self._find_ca(self._clean_text(row['ca']))
            if ca:
                vals['corrective_action_id'] = ca.id
            Model.create(vals)
            n += 1
        return n

    def _import_cas(self, ws, lines):
        Model = self.env['hse.corrective.action']
        state_map = {'open': 'open', 'in progress': 'in_progress', 'closed': 'closed'}
        n = 0
        for r, row in self._rows(ws, 3, {
                'id': 1, 'related': 2, 'action': 3, 'resp': 4, 'target': 5,
                'status': 6, 'closure': 7, 'verify': 8}):
            name = self._clean_text(row['id'])
            if not self._valid_id(name, 'CA') or Model.search([('name', '=', name)], limit=1):
                continue
            # Excel keeps 'M/DD/YYYY' placeholder text in Closure Date — treat
            # it as empty rather than inventing a date.
            closure = parse_excel_date(row['closure'])
            if closure is None and self._clean_text(row['closure']):
                lines.append('· %s: closure date %r is a placeholder — kept empty'
                             % (name, row['closure']))
            action_text = self._clean_text(row['action'])
            vals = {
                'name': name,
                'related_ref': self._clean_text(row['related']),
                'action_description': action_text or name,
                'responsible_person': self._clean_text(row['resp']),
                'target_date': parse_excel_date(row['target']),
                'state': state_map.get(self._clean_text(row['status']).lower(), 'open'),
                'closure_date': closure,
                'verification': self._clean_text(row['verify']),
            }
            Model.create(vals)
            n += 1
        return n

    def _import_ptw(self, ws, lines):
        """Support BOTH column layouts of the register sheet:
        Layout A (early rows): nature G, detail H, marks I–P, location S, status T
        Layout B (later rows): nature G, type H, location Q, status R
        Type text = J if present else H (CalcRows BC)."""
        Model = self.env['hse.ptw.register']
        n = 0
        for r in range(9, ws.max_row + 1):
            permit = self._clean_text(ws.cell(r, 3).value)   # C
            d_raw = ws.cell(r, 4).value                       # D
            if not permit and not d_raw:
                continue
            name = permit or 'ROW-%d' % r
            nature = self._clean_text(ws.cell(r, 7).value)    # G
            detail_h = self._clean_text(ws.cell(r, 8).value)  # H
            type_j = self._clean_text(ws.cell(r, 10).value)   # J
            type_text = type_j or detail_h
            # Location/status column shift between the two layouts
            loc_q = self._clean_text(ws.cell(r, 17).value)    # Q
            st_r = self._clean_text(ws.cell(r, 18).value)    # R
            loc_s = self._clean_text(ws.cell(r, 19).value)    # S
            st_t = self._clean_text(ws.cell(r, 20).value)    # T
            if loc_s or st_t:  # Layout A
                location, status = loc_s, st_t
            else:
                location, status = loc_q, st_r
            status_map = {'open': 'open', 'closed': 'closed', 'expired': 'expired'}
            # Permit numbers restart every month section — a record is a
            # duplicate only if name AND type AND location already exist.
            if Model.search([('name', '=', name),
                             ('type_text', '=', type_text),
                             ('location', '=', location)], limit=1):
                continue
            vals = {
                'name': name,
                'date_issue': parse_excel_date(d_raw),
                'department': self._clean_text(ws.cell(r, 5).value),  # E
                'contractor': self._clean_text(ws.cell(r, 6).value),  # F
                'nature_of_work': nature,
                'type_text': type_text,
                'location': location,
                'status': status_map.get(status.lower(), 'open'),
            }
            Model.create(vals)
            n += 1
        if n:
            lines.append('· PTW register: %d rows imported (both column '
                         'layouts understood)' % n)
        return n

    def _import_man_hours(self, ws, lines):
        """KPI Calculations sheet: month labels col A, man-hours col B, rows 3-14."""
        Figure = self.env['hse.monthly.figure']
        settings = self.env['hse.safety.settings'].get_settings()
        n = 0
        for r in range(3, 15):
            label = self._clean_text(ws.cell(r, 1).value)
            hours = ws.cell(r, 2).value
            if not label:
                continue
            month_no = month_from_label(label)
            if not month_no:
                continue
            fig = Figure._find(settings.reporting_year, month_no)
            if not fig:
                fig = Figure.create({'year': settings.reporting_year,
                                     'month': str(month_no)})
            if hours not in (None, '', 0, 0.0):
                fig.write({'man_hours': float(hours)})
                n += 1
            else:
                lines.append('· %s: man-hours not given (rates stay n/a)' % label)
        return n

    def _import_leading(self, ws, lines):
        """Leading Indicators sheet: B planned, C completed, E talks,
        F PTW issued, G training hours, H audit score — rows 3-14."""
        Figure = self.env['hse.monthly.figure']
        settings = self.env['hse.safety.settings'].get_settings()
        n = 0
        for r in range(3, 15):
            label = self._clean_text(ws.cell(r, 1).value)
            if not label:
                continue
            month_no = month_from_label(label)
            if not month_no:
                continue
            vals = {}
            def _num(col):
                v = ws.cell(r, col).value
                return float(v) if isinstance(v, (int, float)) else None
            planned, done = _num(2), _num(3)
            talks, ptw = _num(5), _num(6)
            training, audit = _num(7), _num(8)
            if planned is not None:
                vals['planned_inspections'] = int(planned)
            if done is not None:
                vals['completed_inspections'] = int(done)
            if talks is not None:
                vals['toolbox_talks'] = int(talks)
            if ptw is not None:
                vals['ptw_issued'] = int(ptw)
            if training is not None:
                vals['training_hours'] = training
            if audit is not None:
                vals['audit_score'] = audit
            if not vals:
                continue
            fig = Figure._find(settings.reporting_year, month_no)
            if not fig:
                vals.update({'year': settings.reporting_year, 'month': str(month_no)})
                Figure.create(vals)
            else:
                fig.write(vals)
            n += 1
        return n

    def _find_ca(self, ref):
        if not ref:
            return self.env['hse.corrective.action']
        return self.env['hse.corrective.action'].search(
            [('name', '=', ref)], limit=1)


def month_from_label(label):
    """'Jan-26', 'January 2026', 'Mar' → month number."""
    text = (label or '').strip()
    m = re.match(r'^([A-Za-z]{3,9})', text)
    if m:
        return MONTH_NAMES.get(m.group(1).lower())
    return None


def base64_decode(binary_field):
    import base64
    if isinstance(binary_field, str):
        return base64.b64decode(binary_field)
    return base64.b64decode(bytes(binary_field))
