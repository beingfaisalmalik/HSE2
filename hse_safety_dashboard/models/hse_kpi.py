# -*- coding: utf-8 -*-
from datetime import date
from calendar import monthrange

from odoo import models, fields, api, _

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class HseKpiEngine(models.AbstractModel):
    """KPI engine — Python replacement for the Excel hidden Calc / CalcRows sheets.

    Every method is a pure live query over the registers: no stored snapshot,
    no #REF!, no stale cache.  The numbers always match the current records.
    """
    _name = 'hse.kpi.engine'
    _description = 'HSE KPI Engine'

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @api.model
    def _cfg(self):
        s = self.env['hse.safety.settings'].get_settings()
        return s.reporting_year, s.rate_base

    @api.model
    def month_label(self, year, month_no):
        return "%s-%02d" % (MONTH_LABELS[month_no - 1], year % 100)

    @api.model
    def _year_domain(self, year, field='date'):
        return ['|', (field, '=', False),
                '&', (field, '>=', date(year, 1, 1)),
                     (field, '<=', date(year, 12, 31))]

    @api.model
    def _load(self, year):
        """Load every register once — used by the whole-year computations."""
        log_domain = self._year_domain(year)
        return {
            'injuries': self.env['hse.injury.log'].search(log_domain),
            'near_misses': self.env['hse.near.miss.log'].search(log_domain),
            'uacs': self.env['hse.uac.log'].search(log_domain),
            'incidents': self.env['hse.incident.log'].search(log_domain),
            'ptws': self.env['hse.ptw.register'].search(
                self._year_domain(year, 'date_issue')),
            'cas': self.env['hse.corrective.action'].search([]),
            'figures': self.env['hse.monthly.figure'].search([('year', '=', year)]),
        }

    @api.model
    def _month_of(self, d, year):
        """Excel CalcRows D: month number if the clean date is inside the
        reporting year, else 0."""
        if d and d.year == year:
            return d.month
        return 0

    # ------------------------------------------------------------------
    # Dynamic period selectors — years / months driven by the data itself
    # ------------------------------------------------------------------
    @api.model
    def _dated_models(self):
        """(model, date-field) pairs that carry a stored period date.
        (Corrective actions are handled separately: their related_date is a
        non-stored compute, so it must be read record-by-record — domains on
        non-stored fields are not reliable.)"""
        return [
            ('hse.injury.log', 'date'),
            ('hse.near.miss.log', 'date'),
            ('hse.uac.log', 'date'),
            ('hse.incident.log', 'date'),
            ('hse.ptw.register', 'date_issue'),
        ]

    @api.model
    def _ca_dates(self):
        """Linked-entry dates of all corrective actions (non-stored compute)."""
        return [ca.related_date
                for ca in self.env['hse.corrective.action'].search([])
                if ca.related_date]

    @api.model
    def available_years(self):
        """Every year present in any register or monthly figure, merged with
        the configured reporting year and the current year so the selector is
        never empty.  Newest first — pure data, nothing hardcoded."""
        years = set()
        for model, fname in self._dated_models():
            for d in self.env[model].search(
                    [(fname, '!=', False)]).mapped(fname):
                if d:
                    years.add(d.year)
        for d in self._ca_dates():
            years.add(d.year)
        for y in self.env['hse.monthly.figure'].search([]).mapped('year'):
            if y:
                years.add(int(y))
        settings = self.env['hse.safety.settings'].get_settings()
        years.add(settings.reporting_year)
        years.add(fields.Date.context_today(self).year)
        return sorted(years, reverse=True)

    @api.model
    def available_months(self, year):
        """Months of `year` that actually hold data (events, permits,
        dated corrective actions or a monthly figure).  When the year has no
        data at all, fall back to all twelve calendar months so the selector
        still offers a choice."""
        year = int(year)
        months = set()
        for model, fname in self._dated_models():
            recs = self.env[model].search([
                (fname, '>=', date(year, 1, 1)),
                (fname, '<=', date(year, 12, 31))])
            for d in recs.mapped(fname):
                if d:
                    months.add(d.month)
        for d in self._ca_dates():
            if d.year == year:
                months.add(d.month)
        for f in self.env['hse.monthly.figure'].search([('year', '=', year)]):
            try:
                months.add(int(f.month))
            except (TypeError, ValueError):
                continue
        return sorted(months) or list(range(1, 13))

    # ------------------------------------------------------------------
    # One month — mirror of Calc row 17
    # ------------------------------------------------------------------
    @api.model
    def month_stats(self, year, month_no, rate_base=None, data=None):
        if rate_base is None:
            year_cfg, rate_base = self._cfg()
        if data is None:
            data = self._load(year)
        start = date(year, month_no, 1)
        end = date(year, month_no, monthrange(year, month_no)[1])

        def _in(d):
            return bool(d and start <= d <= end)

        lti = mtc = fa = lost_days = 0
        for rec in data['injuries']:
            if _in(rec.date):
                if rec.injury_type == 'lti':
                    lti += 1
                elif rec.injury_type == 'mtc':
                    mtc += 1
                elif rec.injury_type == 'first_aid':
                    fa += 1
                lost_days += rec.lost_workdays or 0

        nm_count = sum(1 for r in data['near_misses'] if _in(r.date))
        ua_count = sum(1 for r in data['uacs'] if _in(r.date) and r.uac_type == 'unsafe_act')
        uc_count = sum(1 for r in data['uacs'] if _in(r.date) and r.uac_type == 'unsafe_condition')
        obs_total = sum(1 for r in data['uacs'] if _in(r.date))
        obs_closed = sum(1 for r in data['uacs'] if _in(r.date) and r.status == 'closed')
        inc_count = sum(1 for r in data['incidents'] if _in(r.date))

        # CAs are attributed to the month of the linked event's date
        # (Excel CalcRows AO/AP — INDEX order Injury → UAC → NearMiss → Incident).
        ca_linked = ca_closed = ca_open = ca_open_only = ca_progress = 0
        ca_overdue = ca_no_target = 0
        for ca in data['cas']:
            if not _in(ca.related_date):
                continue
            ca_linked += 1
            if ca.state == 'closed':
                ca_closed += 1
            else:
                ca_open += 1
                if ca.state == 'open':
                    ca_open_only += 1
                elif ca.state == 'in_progress':
                    ca_progress += 1
                if ca.overdue:
                    ca_overdue += 1
                if not ca.target_date:
                    ca_no_target += 1

        figure = next((f for f in data['figures']
                       if f.year == year and f.month == str(month_no)), None)
        man_hours = figure.man_hours if figure else 0.0
        ptw_issued = figure.ptw_issued if figure else 0
        talks = figure.toolbox_talks if figure else 0
        training = figure.training_hours if figure else 0.0
        insp_plan = figure.planned_inspections if figure else 0
        insp_done = figure.completed_inspections if figure else 0
        # 0 is treated as 'no audit entered' (Excel blank cells)
        audit = (figure.audit_score if figure and figure.audit_score else None)

        ptw_rows = sum(1 for r in data['ptws'] if _in(r.date_issue))
        # Keyword counts on the permit type text — Excel Calc AM..AT (Hot Work etc.)
        hot_work = cold_work = height = electrical = 0
        excavation = confined = radioactivity = crane = 0
        for r in data['ptws']:
            if not _in(r.date_issue):
                continue
            tl = (r.type_text or '').lower()
            if 'hot work' in tl:
                hot_work += 1
            if 'cold work' in tl:
                cold_work += 1
            if 'work at height' in tl:
                height += 1
            if 'electrical' in tl:
                electrical += 1
            if 'excavation' in tl:
                excavation += 1
            if 'confined' in tl:
                confined += 1
            if 'radioactiv' in tl:
                radioactivity += 1
            if 'crane' in tl:
                crane += 1

        def _rate(count):
            # n/a (None) when no man-hours — mirrors IF(E>0, …, "")
            return count * rate_base / man_hours if man_hours > 0 else None

        return {
            'month_no': month_no,
            'label': self.month_label(year, month_no),
            'man_hours': man_hours,
            'lti': lti, 'mtc': mtc, 'first_aid': fa,
            'recordable': lti + mtc,
            'all_injuries': lti + mtc + fa,
            'lost_workdays': lost_days,
            'near_misses': nm_count,
            'unsafe_acts': ua_count, 'unsafe_conditions': uc_count,
            'observations': obs_total, 'observations_closed': obs_closed,
            'incidents': inc_count,
            'ca_linked': ca_linked, 'ca_closed': ca_closed,
            'ca_open': ca_open, 'ca_open_status': ca_open_only,
            'ca_in_progress': ca_progress,
            'ca_overdue': ca_overdue, 'ca_no_target': ca_no_target,
            'ca_closure_rate': (ca_closed / ca_linked) if ca_linked else None,
            'ptw_issued': ptw_issued, 'ptw_register_rows': ptw_rows,
            'ptw_hot_work': hot_work, 'ptw_cold_work': cold_work,
            'ptw_height': height, 'ptw_electrical': electrical,
            'ptw_excavation': excavation, 'ptw_confined': confined,
            'ptw_radioactivity': radioactivity, 'ptw_crane': crane,
            'toolbox_talks': talks, 'training_hours': training,
            'insp_planned': insp_plan, 'insp_completed': insp_done,
            'insp_compliance': (insp_done / insp_plan) if insp_plan else None,
            'audit_score': audit,
            'ltifr': _rate(lti),
            'trir': _rate(lti + mtc),
            'severity': _rate(lost_days),
            'has_hours': 1 if man_hours > 0 else 0,
            # Excel CalcRows AL — any activity this month
            'has_data': 1 if any((man_hours, lti + mtc + fa, nm_count, obs_total,
                                  inc_count, ptw_issued, ptw_rows, talks,
                                  training, insp_plan)) else 0,
        }

    # ------------------------------------------------------------------
    # Year — mirrors Calc rows 17-33 (12 months + YTD + selected + prior)
    # ------------------------------------------------------------------
    @api.model
    def year_stats(self, year, month_no, rate_base=None, data=None):
        if rate_base is None:
            _, rate_base = self._cfg()
        if data is None:
            data = self._load(year)
        months = [self.month_stats(year, m, rate_base, data) for m in range(1, 13)]
        sel = months[month_no - 1]
        prior = months[month_no - 2] if month_no > 1 else None

        def _sum(key, upto=None):
            return sum(m[key] for m in months
                       if upto is None or m['month_no'] <= upto)

        def _ytd_rate(count_key, upto=None):
            # SUMIFS(count, has_hours=1) * base / SUM(hours) — YTD rates only
            # count events in months that have man-hours (Calc AH29/AH30).
            hours = _sum('man_hours', upto)
            if hours <= 0:
                return None
            cnt = sum(m[count_key] for m in months
                      if m['has_hours'] and (upto is None or m['month_no'] <= upto))
            return cnt * rate_base / hours

        def _rate_sum(count_key, upto=None):
            hours = _sum('man_hours', upto)
            if hours <= 0:
                return None
            return _sum(count_key, upto) * rate_base / hours

        def _ytd_block(upto=None):
            linked = _sum('ca_linked', upto)
            closed = _sum('ca_closed', upto)
            planned = _sum('insp_planned', upto)
            done = _sum('insp_completed', upto)
            audits = [m['audit_score'] for m in months
                      if m['audit_score'] not in (None, False)
                      and (upto is None or m['month_no'] <= upto)]
            return {
                'man_hours': _sum('man_hours', upto),
                'lti': _sum('lti', upto), 'mtc': _sum('mtc', upto),
                'first_aid': _sum('first_aid', upto),
                'recordable': _sum('recordable', upto),
                'all_injuries': _sum('all_injuries', upto),
                'lost_workdays': _sum('lost_workdays', upto),
                'near_misses': _sum('near_misses', upto),
                'unsafe_acts': _sum('unsafe_acts', upto),
                'unsafe_conditions': _sum('unsafe_conditions', upto),
                'observations': _sum('observations', upto),
                'observations_closed': _sum('observations_closed', upto),
                'incidents': _sum('incidents', upto),
                'ca_linked': linked, 'ca_closed': closed,
                'ca_open': _sum('ca_open', upto),
                'ca_overdue': _sum('ca_overdue', upto),
                'ca_no_target': _sum('ca_no_target', upto),
                'ca_closure_rate': (closed / linked) if linked else None,
                'ptw_issued': _sum('ptw_issued', upto),
                'ptw_register_rows': _sum('ptw_register_rows', upto),
                'ptw_hot_work': _sum('ptw_hot_work', upto),
                'ptw_cold_work': _sum('ptw_cold_work', upto),
                'ptw_height': _sum('ptw_height', upto),
                'ptw_electrical': _sum('ptw_electrical', upto),
                'ptw_excavation': _sum('ptw_excavation', upto),
                'ptw_confined': _sum('ptw_confined', upto),
                'ptw_radioactivity': _sum('ptw_radioactivity', upto),
                'ptw_crane': _sum('ptw_crane', upto),
                'toolbox_talks': _sum('toolbox_talks', upto),
                'training_hours': _sum('training_hours', upto),
                'insp_planned': planned, 'insp_completed': done,
                'insp_compliance': (done / planned) if planned else None,
                'audit_score': (sum(audits) / len(audits)) if audits else None,
                'ltifr': _ytd_rate('lti', upto),
                'trir': _ytd_rate('recordable', upto),
                'severity': _rate_sum('lost_workdays', upto),
            }

        return {
            'months': months,
            'selected': sel,
            'prior': prior,
            'ytd_to_month': _ytd_block(month_no),
            'ytd_full': _ytd_block(None),
        }

    # ------------------------------------------------------------------
    # Days since last LTI — Excel Dashboard I3/I5
    # ------------------------------------------------------------------
    @api.model
    def days_since_last_lti(self, year, month_no=None, as_of=None):
        if as_of is None:
            if month_no:
                end = date(year, month_no, monthrange(year, month_no)[1])
                as_of = min(end, fields.Date.context_today(self))
            else:
                as_of = fields.Date.context_today(self)
        lti_dates = [r.date for r in self.env['hse.injury.log'].search(
            [('injury_type', '=', 'lti'), ('date', '!=', False), ('date', '<=', as_of)])]
        if lti_dates:
            last = max(lti_dates)
            return {'as_of': as_of, 'last_date': last,
                    'days': (as_of - last).days, 'has_lti': True}
        # No LTI recorded → days since Jan 1 of the reporting year
        return {'as_of': as_of, 'last_date': False,
                'days': (as_of - date(year, 1, 1)).days, 'has_lti': False}

    # ------------------------------------------------------------------
    # Data-health checks — exact Calc r145-r154 semantics
    # ------------------------------------------------------------------
    @api.model
    def health_checks(self, year, month_no=None, data=None):
        Injury = self.env['hse.injury.log']
        NearMiss = self.env['hse.near.miss.log']
        Uac = self.env['hse.uac.log']
        Incident = self.env['hse.incident.log']
        Ptw = self.env['hse.ptw.register']
        Ca = self.env['hse.corrective.action']
        year_start, year_end = date(year, 1, 1), date(year, 12, 31)
        today = fields.Date.context_today(self)

        def _bad_date(d):
            return not d or d < year_start or d > year_end

        # Health check 1 counts ALL rows (including dated outside this year)
        inj_all = Injury.search([])
        nm_all = NearMiss.search([])
        uac_all = Uac.search([])
        inc_all = Incident.search([])
        ptw_all = Ptw.search([])
        ca_all = Ca.search([])
        ptw_dates = {r.id: r.date_issue for r in ptw_all}

        # 1 — missing / unreadable / outside-year dates (per register)
        inj_bad = sum(1 for r in inj_all if _bad_date(r.date))
        nm_bad = sum(1 for r in nm_all if _bad_date(r.date))
        uac_bad = sum(1 for r in uac_all if _bad_date(r.date))
        inc_bad = sum(1 for r in inc_all if _bad_date(r.date))
        ptw_bad = sum(1 for r in ptw_all if _bad_date(r.date_issue))
        c1 = inj_bad + nm_bad + uac_bad + inc_bad + ptw_bad

        # 2 — dates typed as text: impossible in Odoo (true date fields)
        c2 = 0
        # 3 — future-dated entries
        c3 = (sum(1 for coll in (inj_all, nm_all, uac_all, inc_all)
                  for r in coll if r.date and r.date > today)
              + sum(1 for r in ptw_all if r.date_issue and r.date_issue > today))
        # 4 — out of chronological order (possible day/month swap), by log ID order
        def _ooo(coll):
            max_seen, n = None, 0
            for r in sorted(coll, key=lambda x: x.name or ''):
                if r.date:
                    if max_seen is not None and r.date < max_seen:
                        n += 1
                    if max_seen is None or r.date > max_seen:
                        max_seen = r.date
            return n
        ooo_inj, ooo_nm = _ooo(inj_all), _ooo(nm_all)
        ooo_uac, ooo_inc = _ooo(uac_all), _ooo(inc_all)
        c4 = ooo_inj + ooo_nm + ooo_uac + ooo_inc

        # 5 — CAs whose Related Log Entry ID has no dated match (Excel AO/AP)
        c5 = sum(1 for ca in ca_all if ca.related_ref and not ca.related_date)

        # 6 — open CAs with no target date
        c6 = Ca.search_count([('state', '!=', 'closed'), ('target_date', '=', False)])

        # 7 — months with events logged but no man-hours entered
        if data is None:
            data = self._load(year)
            stats = [self.month_stats(year, m, data=data) for m in range(1, 13)]
        else:
            stats = [self.month_stats(year, m, data=data) for m in range(1, 13)]
        c7 = sum(1 for m in stats
                 if (m['all_injuries'] + m['near_misses'] + m['observations']
                     + m['incidents']) > 0
                 and m['man_hours'] == 0)

        # 8 — UAC type not in the drop-down: selection field makes this impossible
        c8 = 0

        # 9 — months where PTW register rows ≠ PTW issued entered
        c9 = sum(1 for m in stats if m['ptw_register_rows'] != m['ptw_issued'])

        # 10 — KPI totals differing from dashboard: single live source — impossible
        c10 = 0

        def _row(no, count, label, detail):
            return {'no': no, 'count': count, 'label': label,
                    'detail': detail, 'ok': count == 0}

        return [
            _row(1, c1, _(
                'Log entries with a missing / unreadable date, or dated outside the reporting year'),
                _("Injury %(i)s · Near-miss %(n)s · Unsafe act/cond. %(u)s · Incident %(inc)s · PTW %(p)s") % {
                    'i': inj_bad, 'n': nm_bad, 'u': uac_bad, 'inc': inc_bad, 'p': ptw_bad}),
            _row(2, c2, _(
                'Dates typed as text (dashboard converts d/m/y text automatically, but please re-enter as real dates)'),
                _("Text dates cannot occur — Odoo stores true date fields")),
            _row(3, c3, _("Entries dated in the future"),
                _("Usually a day/month swap or typo")),
            _row(4, c4, _("Entries out of chronological order (possible day/month swap)"),
                _("Injury %(i)s · Near-miss %(n)s · Unsafe act/cond. %(u)s · Incident %(inc)s") % {
                    'i': ooo_inj, 'n': ooo_nm, 'u': ooo_uac, 'inc': ooo_inc}),
            _row(5, c5, _("Corrective actions whose 'Related Log Entry ID' matches no log entry"),
                _("Fix the ID or the log entry date")),
            _row(6, c6, _("Open corrective actions with no target date"),
                _("Overdue cannot be judged by date")),
            _row(7, c7, _(
                'Months with injuries / observations / incidents logged but no man-hours entered'),
                _("Enter hours in Monthly Figures — rates show n/a until then")),
            _row(8, c8, _(
                "Unsafe-act log entries whose Type is neither 'Unsafe Act' nor 'Unsafe Condition'"),
                _("Type is a controlled drop-down in Odoo")),
            _row(9, c9, _(
                "Months where PTW register rows do not match 'Permits to Work Issued' typed in Monthly Figures"),
                _("Dashboard uses the Leading Indicators figure; register count shown beside it")),
            _row(10, c10, _(
                'KPI Calculations sheet totals that differ from the dashboard (LTI, Recordable, Near-miss, Violations)'),
                _("Single live source of truth — dashboard and reports always agree")),
        ]

    # ------------------------------------------------------------------
    # Dashboard payload for the OWL action
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard(self, year=None, month_no=None):
        settings = self.env['hse.safety.settings'].get_settings()
        years = self.available_years()
        year = int(year) if year else settings.reporting_year
        if year not in years:          # explicit year outside the data wins
            years = sorted(set(years) | {year}, reverse=True)
        avail_months = self.available_months(year)
        if not month_no:
            # Default: current month when the data covers it, otherwise the
            # latest month that actually holds data.  An explicit month_no is
            # always honoured verbatim (the wizard offers every calendar month).
            today = fields.Date.context_today(self)
            month_no = (today.month if today.year == year
                        and today.month in avail_months
                        else max(avail_months))
        data = self._load(year)
        y = self.year_stats(year, month_no, settings.rate_base, data)
        checks = self.health_checks(year, month_no, data)
        attention = sum(1 for c in checks if not c['ok'])
        dsl = self.days_since_last_lti(year, month_no)
        dsl_year = self.days_since_last_lti(year, None)
        company = self.env.company

        # registers for the selected month (like Dashboard rows 87-130)
        start = date(year, month_no, 1)
        end = date(year, month_no, monthrange(year, month_no)[1])

        def _recs(coll, limit=6):
            rows = [r for r in coll if r.date and start <= r.date <= end]
            rows.sort(key=lambda r: r.date, reverse=True)
            return rows[:limit]

        injuries = _recs(self.env['hse.injury.log'].search([]))
        near_misses = _recs(self.env['hse.near.miss.log'].search([]), 4)
        uacs = _recs(self.env['hse.uac.log'].search([]), 6)
        incidents = _recs(self.env['hse.incident.log'].search([]), 4)
        open_cas_all = self.env['hse.corrective.action'].search(
            [('state', '!=', 'closed')])
        open_cas = sorted(
            [ca for ca in open_cas_all
             if ca.related_date and start <= ca.related_date <= end],
            key=lambda c: c.name)[:12]

        def _count(coll):
            return sum(1 for r in coll if r.date and start <= r.date <= end)

        return {
            'year': year,
            'years': years,                      # dynamic year options
            'available_months': avail_months,    # dynamic month options
            'month_no': month_no,
            'month_label': self.month_label(year, month_no),
            'month_name': date(year, month_no, 1).strftime('%B %Y'),
            'prev_label': y['prior']['label'] if y['prior'] else False,
            'rate_base': settings.rate_base,
            'company': company.name,
            'report_date': fields.Date.context_today(self),
            'stats': y['selected'],
            'prior': y['prior'],
            'ytd_to_month': y['ytd_to_month'],
            'ytd_full': y['ytd_full'],
            'months': y['months'],
            'health': checks,
            'health_attention': attention,
            'days_since_lti': dsl,
            'days_since_lti_year': dsl_year,
            'registers': {
                'injuries': [self._injury_row(r) for r in injuries],
                'injuries_total': _count(self.env['hse.injury.log'].search([])),
                'near_misses': [self._nm_row(r) for r in near_misses],
                'near_misses_total': _count(self.env['hse.near.miss.log'].search([])),
                'uacs': [self._uac_row(r) for r in uacs],
                'uacs_total': _count(self.env['hse.uac.log'].search([])),
                'incidents': [self._inc_row(r) for r in incidents],
                'incidents_total': _count(self.env['hse.incident.log'].search([])),
                'open_cas': [self._ca_row(r) for r in open_cas],
                'open_cas_total': len(open_cas),
            },
        }

    # ------------------------------------------------------------------
    # JSON-safe row serializers for the dashboard registers
    # ------------------------------------------------------------------
    @api.model
    def _fmt_date(self, d):
        return d.strftime('%d-%b-%Y') if d else ''

    @api.model
    def _injury_row(self, r):
        return {'name': r.name, 'date': self._fmt_date(r.date),
                'type': r._type_label(), 'department': r.department or '',
                'person': r.person_involved or '',
                'lost_workdays': r.lost_workdays or 0,
                'status': r.status, 'desc': (r.description or '')[:120]}

    @api.model
    def _nm_row(self, r):
        return {'name': r.name, 'date': self._fmt_date(r.date),
                'department': r.department or '',
                'severity': r.potential_severity or '',
                'reported_by': r.reported_by or '',
                'status': r.status, 'desc': (r.description or '')[:120]}

    @api.model
    def _uac_row(self, r):
        return {'name': r.name, 'date': self._fmt_date(r.date),
                'type': r._type_label(), 'department': r.department or '',
                'reported_by': r.reported_by or '',
                'status': r.status, 'desc': (r.description or '')[:120]}

    @api.model
    def _inc_row(self, r):
        return {'name': r.name, 'date': self._fmt_date(r.date),
                'type': r._type_label(), 'department': r.department or '',
                'area': r.area_asset or '',
                'impact': r.estimated_impact or '',
                'status': r.status, 'desc': (r.description or '')[:120]}

    @api.model
    def _ca_row(self, r):
        return {'name': r.name, 'related': r.related_display or '',
                'action': (r.action_description or '')[:120],
                'responsible': r.responsible_person or '',
                'target_date': self._fmt_date(r.target_date),
                'state': r.state, 'overdue': r.overdue}
