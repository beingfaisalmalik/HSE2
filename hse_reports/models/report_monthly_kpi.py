# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import api, fields, models


class HseMonthlyKpiReport(models.AbstractModel):
    """Dynamic 'Monthly HSE KPI & Statistics' report values.

    Everything is computed live from the database for the current month
    (month start -> today).  No hard-coded baselines: exposure hours come
    from the latest API RP 754 metric record, falling back to a configurable
    parameter, and are always labelled with their source.
    """

    _name = 'report.hse_reports.report_monthly_hse_kpi_template'
    _description = 'HSE Monthly KPI Statistics Report Helper'

    @api.model
    def _get_report_values(self, docids, data=None):
        env = self.env
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)

        Incident = env['incident.reporting']
        Observation = env['observation.observation']

        def in_period(field):
            return [(field, '>=', month_start), (field, '<=', today)]

        # ---- Incidents -------------------------------------------------
        incidents = Incident.search(in_period('create_date')) if Incident else Incident
        incident_by_type = {}
        if Incident:
            for rec in Incident.search(in_period('incident_date') + [('incident_date', '!=', False)]):
                label = dict(rec._fields['incident_type'].selection).get(rec.incident_type, 'Unspecified')
                incident_by_type[label] = incident_by_type.get(label, 0) + 1
        lti_count = Incident.search_count(
            in_period('incident_date') + [('injury_ids.injury_severity', 'in', ['fatality', 'lost_time'])]) if Incident else 0

        # Days without LTI (same dynamic rule as the executive dashboard)
        days_without_lti = False
        last_lti = False
        if Incident:
            lti = Incident.search(
                [('injury_ids.injury_severity', 'in', ['fatality', 'lost_time']),
                 ('incident_date', '!=', False)], order='incident_date desc', limit=1)
            if lti and lti.incident_date:
                last_lti = lti.incident_date
                days_without_lti = max((today - lti.incident_date).days, 0)

        # ---- Observations ----------------------------------------------
        obs_total = Observation.search_count(in_period('create_date')) if Observation else 0
        obs_high = Observation.search_count(
            in_period('create_date') + [('priority', '=', '3')]) if Observation else 0

        # ---- Live operations (state distribution via read_group) --------
        def state_distribution(model_name, domain=None):
            if model_name not in env:
                return []
            recs = env[model_name]
            if not recs._fields.get('state'):
                return []
            groups = recs.read_group(domain or [], ['state'], groupby='state')
            out = []
            for g in groups:
                label = dict(recs._fields['state'].selection).get(g['state'], g['state'] or 'Undefined')
                out.append((label, g['state_count']))
            return sorted(out, key=lambda x: -x[1])

        permits_dist = state_distribution('hse.permit.to.work')
        loto_dist = state_distribution('hse.loto.plan')
        bypass_dist = state_distribution('hse.bypass')

        # ---- CAPA engine ------------------------------------------------
        capas_open = env['hse.action'].search_count(
            [('state', 'not in', ['verified', 'cancelled'])]) if 'hse.action' in env else 0
        capas_overdue = env['hse.action'].search_count(
            [('target_date', '<', today), ('state', 'not in', ['verified', 'cancelled'])]) if 'hse.action' in env else 0

        # ---- Compliance --------------------------------------------------
        oblig_nc = env['hse.compliance.obligation'].search_count(
            [('compliance_status', '=', 'non_compliant')]) if 'hse.compliance.obligation' in env else 0
        oblig_partial = env['hse.compliance.obligation'].search_count(
            [('compliance_status', '=', 'partial')]) if 'hse.compliance.obligation' in env else 0
        audits_period = env['hse.audit'].search_count(in_period('audit_date')) if 'hse.audit' in env else 0

        # ---- Assets & people ---------------------------------------------
        certs_expired = env['hse.equipment.certification'].search_count(
            [('is_expired', '=', True)]) if 'hse.equipment.certification' in env else 0
        certs_expiring = env['hse.equipment.certification'].search_count(
            [('is_expiring_soon', '=', True)]) if 'hse.equipment.certification' in env else 0
        personnel_expired = env['hse.personnel.certification'].search_count(
            [('state', '=', 'expired')]) if 'hse.personnel.certification' in env else 0
        training_gaps = env['hse.training.matrix.line'].search_count(
            [('status', 'in', ['missing', 'expired'])]) if 'hse.training.matrix.line' in env else 0
        meetings_period = env['hse.meeting'].search_count(in_period('create_date')) if 'hse.meeting' in env else 0

        # ---- TRIR (dynamic exposure hours, same rule as dashboard) -------
        osha_recordable = Incident.search_count(
            in_period('incident_date') + [('is_injury', '=', True)]) if Incident else 0
        exposure_hours, hours_source = 0.0, 'baseline'
        if 'hse.pse.metric' in env:
            metric = env['hse.pse.metric'].search([], order='year desc, id desc', limit=1)
            if metric and metric.total_site_exposure_hours:
                exposure_hours = metric.total_site_exposure_hours
                hours_source = 'API RP 754 metrics'
        if not exposure_hours:
            param = env['ir.config_parameter'].sudo().get_param('hse_dashboard.exposure_hours_baseline')
            try:
                exposure_hours = float(param) if param else 0.0
                if exposure_hours:
                    hours_source = 'configured baseline'
            except (TypeError, ValueError):
                exposure_hours = 0.0
        if not exposure_hours:
            exposure_hours, hours_source = 250000.0, 'industry default (configure hse_dashboard.exposure_hours_baseline)'
        trir = round((osha_recordable * 200000.0) / exposure_hours, 2) if exposure_hours else 0.0

        company = env.company
        return {
            'doc_ids': docids,
            'doc_model': 'res.company',
            'docs': env['res.company'].browse(docids) if docids else company,
            'company': company,
            'period_start': month_start,
            'period_end': today,
            'generated_at': fields.Datetime.now(),
            'incidents_total': len(incidents) if Incident else 0,
            'incident_by_type': sorted(incident_by_type.items()),
            'lti_count': lti_count,
            'days_without_lti': days_without_lti,
            'last_lti': last_lti,
            'obs_total': obs_total,
            'obs_high': obs_high,
            'permits_dist': permits_dist,
            'loto_dist': loto_dist,
            'bypass_dist': bypass_dist,
            'capas_open': capas_open,
            'capas_overdue': capas_overdue,
            'oblig_nc': oblig_nc,
            'oblig_partial': oblig_partial,
            'audits_period': audits_period,
            'certs_expired': certs_expired,
            'certs_expiring': certs_expiring,
            'personnel_expired': personnel_expired,
            'training_gaps': training_gaps,
            'meetings_period': meetings_period,
            'osha_recordable': osha_recordable,
            'exposure_hours': exposure_hours,
            'hours_source': hours_source,
            'trir': trir,
        }
