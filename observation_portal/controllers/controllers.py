# -*- coding: utf-8 -*-
import base64
from datetime import date

from odoo import http
from odoo.http import request

STATE_LABELS = {
    'draft': 'Submitted',
    'in_process': 'In Process',
    'locked': 'Closed / Resolved',
    'rejected': 'Rejected — Rework',
    'reopen': 'Re-Opened',
}
HAZARD_LABELS = {
    'physical': 'Physical',
    'chemical': 'Chemical',
    'biological': 'Biological',
    'other': 'Other / Ergonomic',
}
INCIDENT_TYPE_LABELS = {
    'injury': 'Injury',
    'near_miss': 'Near Miss',
    'fire': 'Fire',
    'transport': 'Transport',
}


class ObservationPortalController(http.Controller):

    # ------------------------------------------------------------------
    # Modern HSE self-service portal
    # ------------------------------------------------------------------
    def _portal_context(self):
        """Shared render values for the portal pages."""
        user = request.env.user
        Obs = request.env['observation.observation'].sudo()
        Incident = request.env['incident.reporting'].sudo()
        my_obs = Obs.search([('create_uid', '=', user.id)], order='id desc', limit=50)
        my_inc = Incident.search([('create_uid', '=', user.id)], order='id desc', limit=50)
        open_count = len([r for r in my_obs if r.state in ('draft', 'in_process')]) + \
                     len([r for r in my_inc if r.state in ('draft', 'in_process')])
        closed_count = len([r for r in my_obs if r.state == 'locked']) + \
                       len([r for r in my_inc if r.state == 'locked'])
        rules = request.env['hse.lifesaving.rule'].sudo().search([('active', '=', True)], order='sequence asc', limit=9)
        policies = request.env['hse.operating.policy'].sudo().search([('state', '=', 'approved')], order='id desc', limit=20)
        procedures = request.env['hse.operating.procedure'].sudo().search([('state', '=', 'published')], order='procedure_code asc', limit=20)
        locations = request.env['hse.location.profile'].sudo().search([], order='name asc')
        return {
            'state_labels': STATE_LABELS,
            'hazard_labels': HAZARD_LABELS,
            'inc_type_labels': INCIDENT_TYPE_LABELS,
            'observations': my_obs,
            'incidents': my_inc,
            'my_obs_count': len(my_obs),
            'my_inc_count': len(my_inc),
            'open_count': open_count,
            'closed_count': closed_count,
            'rules': rules,
            'policies': policies,
            'procedures': procedures,
            'locations': locations,
            'policy_count': len(policies),
        }

    @http.route('/hse/portal', type='http', auth='user', website=True)
    def portal_home(self, **kw):
        """Modern HSE self-service home for external users."""
        return request.render('observation_portal.hse_portal_home', self._portal_context())

    @http.route('/hse/portal/observation', type='http', auth='user', website=True)
    def portal_observation_form(self, submitted=None, **kw):
        ctx = self._portal_context()
        ctx['submitted'] = submitted
        return request.render('observation_portal.hse_portal_observation_form', ctx)

    @http.route('/hse/portal/observation/submit', type='http', auth='user', website=True, methods=['POST'])
    def portal_observation_submit(self, **post):
        self._create_observation(post)
        return request.redirect('/hse/portal/observation?submitted=1')

    @http.route('/hse/portal/incident', type='http', auth='user', website=True)
    def portal_incident_form(self, submitted=None, created_ref=None, **kw):
        ctx = self._portal_context()
        ctx['submitted'] = submitted
        ctx['created_ref'] = created_ref
        ctx['today'] = date.today().strftime('%Y-%m-%d')
        return request.render('observation_portal.hse_portal_incident_form', ctx)

    @http.route('/hse/portal/incident/submit', type='http', auth='user', website=True, methods=['POST'])
    def portal_incident_submit(self, **post):
        incident = self._create_incident(post)
        return request.redirect('/hse/portal/incident?submitted=1&created_ref=%s' % (incident.name or ''))

    @http.route('/hse/portal/my-submissions', type='http', auth='user', website=True)
    def portal_my_submissions(self, **kw):
        return request.render('observation_portal.hse_portal_my_submissions', self._portal_context())

    @http.route('/hse/portal/policies', type='http', auth='user', website=True)
    def portal_policies(self, **kw):
        return request.render('observation_portal.hse_portal_policies', self._portal_context())

    # ------------------------------------------------------------------
    # Creation helpers
    # ------------------------------------------------------------------
    def _create_observation(self, post):
        photo = request.httprequest.files.get('hazard_photo')
        photo_b64 = False
        photo_filename = False
        if photo and photo.filename:
            photo_b64 = base64.b64encode(photo.read())
            photo_filename = photo.filename

        location_id = False
        raw_loc = post.get('location_id')
        if raw_loc and str(raw_loc).isdigit():
            location_id = int(raw_loc)

        vals = {
            'employee_observer_name': post.get('name'),
            'employee_code': post.get('employee_code'),
            'hazard_type': post.get('hazard_type', 'physical'),
            'priority': post.get('priority', '2'),
            'observation': post.get('observation'),
            'immediate_action': post.get('immediate_action'),
            'location_id': location_id,
        }
        if photo_b64:
            vals['hazard_photo'] = photo_b64
            vals['hazard_photo_filename'] = photo_filename
        return request.env['observation.observation'].sudo().create(vals)

    def _create_incident(self, post):
        user = request.env.user
        is_internal = user.has_group('base.group_user')
        incident_date = post.get('incident_date') or date.today().strftime('%Y-%m-%d')
        vals = {
            'ir_description': post.get('incident_detail'),
            'incident_detail': post.get('incident_detail'),
            'incident_type': post.get('incident_type', 'near_miss'),
            'priority': post.get('priority', '2'),
            'exact_location': post.get('exact_location'),
            'incident_date': incident_date,
            'summary_of_incident': post.get('summary_of_incident'),
            'select_emp_type': 'internal' if is_internal else 'external',
            'external_company_name': post.get('external_company_name') or False,
            'external_employee_name': post.get('external_employee_name') or False,
        }
        return request.env['incident.reporting'].sudo().create(vals)

    # ------------------------------------------------------------------
    # LEGACY routes kept for backward compatibility
    # ------------------------------------------------------------------
    @http.route('/observation/form', auth='user', website=True)
    def portal_form(self, success=None, **kw):
        """Legacy entry point -> renders the modern observation form."""
        ctx = self._portal_context()
        ctx['submitted'] = success
        return request.render('observation_portal.hse_portal_observation_form', ctx)

    @http.route('/observation/form/submit', type='http', auth='user', website=True, methods=['POST'])
    def submit_form(self, **post):
        """Handle form submission and save data."""
        self._create_observation(post)
        return request.redirect('/observation/form?success=1')
