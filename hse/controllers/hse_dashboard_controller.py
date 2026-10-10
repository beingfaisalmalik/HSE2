# -*- coding: utf-8 -*-
import json
from datetime import date, datetime, timedelta

from odoo import http
from odoo.http import request


def _to_date(value):
    """Normalize a Date/Datetime value to a datetime.date (dynamic-safe)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return False


class HSEDashboardController(http.Controller):

    # ------------------------------------------------------------------
    # Public JSON API endpoint.
    # Served as plain HTTP (GET or POST) and always answers with a JSON
    # body, so opening it in a browser or calling it with fetch() works.
    # (Previously this was type='json' which answered plain HTTP GET
    # requests with "Bad Request: Request inferred type is compatible
    # with ['http'] but '/hse/dashboard/data' is type='json'".)
    # ------------------------------------------------------------------
    @http.route('/hse/dashboard/data', type='http', auth='user',
                methods=['GET', 'POST'], csrf=False, website=False)
    def get_dashboard_data(self, **kwargs):
        data = self._collect_dashboard_data()
        return request.make_json_response(
            data, headers=[('Cache-Control', 'no-store')], status=200)

    # ------------------------------------------------------------------
    # KPI computation (pure dict -> easy to unit test)
    # ------------------------------------------------------------------
    def _collect_dashboard_data(self):
        env = request.env
        today = date.today()

        # 1. Core counts
        total_incidents = env['incident.reporting'].search_count([]) if 'incident.reporting' in env else 0
        osha_recordable = env['incident.reporting'].search_count([('is_osha_recordable', '=', True)]) if 'incident.reporting' in env else 0
        open_investigations = env['incident.investigation'].search_count([('state', 'in', ['draft', 'in_process'])]) if 'incident.investigation' in env else 0

        active_permits = env['hse.permit'].search_count([('state', '=', 'active')]) if 'hse.permit' in env else 0
        active_bypasses = env['hse.bypass'].search_count([('state', '=', 'active')]) if 'hse.bypass' in env else 0
        active_loto = env['hse.loto.plan'].search_count([('state', '=', 'isolated')]) if 'hse.loto.plan' in env else 0

        overdue_actions = env['hse.action'].search_count([('is_overdue', '=', True)]) if 'hse.action' in env else 0
        total_open_actions = env['hse.action'].search_count([('state', 'in', ['draft', 'assigned', 'in_progress', 'implemented'])]) if 'hse.action' in env else 0

        expiring_certs = env['hse.personnel.certification'].search_count([('state', '=', 'expiring')]) if 'hse.personnel.certification' in env else 0
        expired_certs = env['hse.personnel.certification'].search_count([('state', '=', 'expired')]) if 'hse.personnel.certification' in env else 0

        open_shifts = env['hse.operator.log'].search_count([('state', '=', 'open')]) if 'hse.operator.log' in env else 0
        total_mocs = env['hse.moc'].search_count([('state', 'in', ['draft', 'technical_review', 'implementation', 'pssr'])]) if 'hse.moc' in env else 0

        # Compliance & Training Matrix KPIs
        compliance_tasks_overdue = env['hse.compliance.task'].search_count([('is_overdue', '=', True), ('state', 'not in', ['submitted', 'completed'])]) if 'hse.compliance.task' in env else 0
        compliance_tasks_active = env['hse.compliance.task'].search_count([('state', 'in', ['scheduled', 'in_progress'])]) if 'hse.compliance.task' in env else 0
        training_gap_count = env['hse.training.matrix.line'].search_count([('status', 'in', ['missing', 'expired'])]) if 'hse.training.matrix.line' in env else 0
        safety_meetings_count = env['hse.meeting'].search_count([]) if 'hse.meeting' in env else 0

        # ------------------------------------------------------------------
        # DYNAMIC: TRIR from real exposure hours (API RP 754 metrics module
        # or a configurable baseline) instead of a hard-coded 250,000 h.
        # ------------------------------------------------------------------
        estimated_hours = 0.0
        trir_source = 'baseline'
        if 'hse.pse.metric' in env:
            metric = env['hse.pse.metric'].search([], order='year desc, id desc', limit=1)
            if metric and metric.total_site_exposure_hours:
                estimated_hours = metric.total_site_exposure_hours
                trir_source = 'api_rp_754_metrics'
        if not estimated_hours:
            param = env['ir.config_parameter'].sudo().get_param('hse_dashboard.exposure_hours_baseline')
            try:
                estimated_hours = float(param) if param else 0.0
                if estimated_hours:
                    trir_source = 'config_parameter'
            except (TypeError, ValueError):
                estimated_hours = 0.0
        if not estimated_hours:
            estimated_hours = 250000.0
            trir_source = 'default_baseline'
        trir = round((osha_recordable * 200000.0) / estimated_hours, 2) if estimated_hours else 0.0

        # ------------------------------------------------------------------
        # DYNAMIC: Days Without LTI — computed from the last LTI/fatality
        # with a known incident date; falls back to "no baseline" (False)
        # so the UI can render an explicit N/A instead of a fake counter.
        # ------------------------------------------------------------------
        days_without_lti = False
        lti_label = 'No LTI on record'
        if 'incident.reporting' in env:
            lti_incidents = env['incident.reporting'].search([
                ('injury_ids.injury_severity', 'in', ['fatality', 'lost_time']),
                ('incident_date', '!=', False),
            ], order='incident_date desc', limit=1)
            if lti_incidents and lti_incidents.incident_date:
                last_date = _to_date(lti_incidents.incident_date)
                if last_date:
                    days_without_lti = max((today - last_date).days, 0)
                    lti_label = 'Since %s' % last_date.strftime('%d %b %Y')
            elif 'incident.reporting' in env:
                any_dated = env['incident.reporting'].search(
                    [('incident_date', '!=', False)], order='incident_date asc', limit=1)
                if any_dated and any_dated.incident_date:
                    first_date = _to_date(any_dated.incident_date)
                    if first_date:
                        days_without_lti = max((today - first_date).days, 0)
                        lti_label = 'No LTI since records began (%s)' % first_date.strftime('%d %b %Y')

        # SIMOPS Conflicts
        simops_conflicts_count = 0
        simops_list = []
        if 'hse.permit' in env:
            simops_permits = env['hse.permit'].search([
                ('state', 'in', ['approved', 'active']),
                ('has_simops_conflict', '=', True)
            ])
            simops_conflicts_count = len(simops_permits)
            for sp in simops_permits[:5]:
                simops_list.append({
                    'id': sp.id,
                    'ref': sp.name,
                    'title': sp.title,
                    'location': sp.location_id.name if sp.location_id else '',
                    'risk_level': sp.simops_risk_level,
                    'type': sp.permit_type,
                })

        # Process Safety Barrier Health (Bow-Tie)
        total_barriers = env['hse.bowtie.barrier'].search_count([]) if 'hse.bowtie.barrier' in env else 0
        effective_barriers = env['hse.bowtie.barrier'].search_count([('barrier_status', '=', 'effective')]) if 'hse.bowtie.barrier' in env else 0
        failed_barriers = env['hse.bowtie.barrier'].search_count([('barrier_status', '=', 'failed')]) if 'hse.bowtie.barrier' in env else 0
        degraded_barriers = env['hse.bowtie.barrier'].search_count([('barrier_status', '=', 'degraded')]) if 'hse.bowtie.barrier' in env else 0
        barrier_health_pct = round((effective_barriers / total_barriers * 100), 1) if total_barriers > 0 else 100.0

        # Standing / Defeated Alarms
        standing_alarms_count = env['hse.operator.log.alarm'].search_count([
            ('status', 'in', ['standing', 'defeated'])
        ]) if 'hse.operator.log.alarm' in env else 0

        # Recent Safety Observations
        recent_observations = []
        if 'observation.observation' in env:
            obs_records = env['observation.observation'].search([], order='id desc', limit=5)
            for o in obs_records:
                recent_observations.append({
                    'id': o.id,
                    'name': o.name or f"OBS-{o.id}",
                    'observer': o.employee_observer_name or 'Anonymous',
                    'hazard': getattr(o, 'hazard_type', 'General'),
                    'priority': getattr(o, 'priority', '2'),
                    'state': o.state,
                    'date': fields_datetime_str(o.observation_date),
                    'text': (o.observation or '')[:90] + ('...' if len(o.observation or '') > 90 else ''),
                })

        # 2. Critical Active Bypasses List
        bypasses_data = []
        if 'hse.bypass' in env:
            bypasses = env['hse.bypass'].search([('state', '=', 'active')], limit=5, order='applied_datetime desc')
            for b in bypasses:
                bypasses_data.append({
                    'id': b.id,
                    'tag': b.tag_number,
                    'title': b.title,
                    'location': b.location_id.name if b.location_id else '',
                    'applied_at': b.applied_datetime.strftime('%Y-%m-%d %H:%M') if b.applied_datetime else '',
                    'is_overdue': b.is_overdue,
                    'sil': b.safety_criticality,
                })

        # 3. Active Permits List
        permits_data = []
        if 'hse.permit' in env:
            permits = env['hse.permit'].search([('state', '=', 'active')], limit=5, order='start_datetime desc')
            for p in permits:
                permits_data.append({
                    'id': p.id,
                    'ref': p.name,
                    'title': p.title,
                    'type': dict(p._fields['permit_type'].selection).get(p.permit_type, p.permit_type),
                    'location': p.location_id.name if p.location_id else '',
                    'valid_until': p.end_datetime.strftime('%Y-%m-%d %H:%M') if p.end_datetime else '',
                })

        # 4. Overdue Actions List
        overdue_data = []
        if 'hse.action' in env:
            actions = env['hse.action'].search([('is_overdue', '=', True)], limit=5, order='target_date asc')
            for a in actions:
                overdue_data.append({
                    'id': a.id,
                    'ref': a.name,
                    'title': a.title,
                    'assigned_to': a.assigned_to.name if a.assigned_to else '',
                    'target_date': a.target_date.strftime('%Y-%m-%d') if a.target_date else '',
                    'priority': a.priority,
                    'progress': a.progress,
                })

        # 5. Risk Matrix Grid (5x5 matrix counts) — DYNAMIC hazard counts
        matrix_grid = []
        hazards = env['ra_jsa.hazard'].search([]) if 'ra_jsa.hazard' in env else []

        for likelihood in range(5, 0, -1):
            row = []
            for consequence in range(1, 6):
                score = consequence * likelihood
                if score >= 16:
                    color_class = 'cell-critical'
                    level_name = 'Critical'
                elif score >= 10:
                    color_class = 'cell-high'
                    level_name = 'High'
                elif score >= 4:
                    color_class = 'cell-medium'
                    level_name = 'Medium'
                else:
                    color_class = 'cell-low'
                    level_name = 'Low'

                count = len([h for h in hazards if getattr(h, 'severity_level', False) and getattr(h, 'likelihood', False) and int(h.severity_level) == consequence and int(h.likelihood) == likelihood])

                row.append({
                    'consequence': consequence,
                    'likelihood': likelihood,
                    'score': score,
                    'level': level_name,
                    'color_class': color_class,
                    'count': count,
                })
            matrix_grid.append(row)

        # DYNAMIC: meta block (generated timestamp, server date, current user)
        generated_at = fields_datetime_now_str()

        return {
            'generated_at': generated_at,
            'server_date': today.strftime('%Y-%m-%d'),
            'total_incidents': total_incidents,
            'osha_recordable': osha_recordable,
            'trir': trir,
            'trir_exposure_hours': estimated_hours,
            'trir_source': trir_source,
            'days_without_lti': days_without_lti,
            'days_without_lti_label': lti_label,
            'simops_conflicts_count': simops_conflicts_count,
            'simops_conflicts_list': simops_list,
            'barrier_health_pct': barrier_health_pct,
            'total_barriers': total_barriers,
            'failed_barriers': failed_barriers,
            'degraded_barriers': degraded_barriers,
            'standing_alarms_count': standing_alarms_count,
            'recent_observations': recent_observations,
            'open_investigations': open_investigations,
            'active_permits': active_permits,
            'active_bypasses': active_bypasses,
            'active_loto': active_loto,
            'overdue_actions': overdue_actions,
            'total_open_actions': total_open_actions,
            'expiring_certs': expiring_certs,
            'expired_certs': expired_certs,
            'open_shifts': open_shifts,
            'total_mocs': total_mocs,
            'compliance_tasks_overdue': compliance_tasks_overdue,
            'compliance_tasks_active': compliance_tasks_active,
            'training_gap_count': training_gap_count,
            'safety_meetings_count': safety_meetings_count,
            'active_bypasses_list': bypasses_data,
            'active_permits_list': permits_data,
            'overdue_actions_list': overdue_data,
            'matrix_grid': matrix_grid,
        }


def fields_datetime_str(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return ''


def fields_datetime_now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
