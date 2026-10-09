# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEBbsObservation(models.Model):
    _name = 'hse.bbs.observation'
    _description = 'Behavior-Based Safety (BBS) Observation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'obs_date desc, id desc'

    name = fields.Char(string='BBS Observation Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    location_id = fields.Many2one('hse.location.profile', string='Facility / Work Area', required=True)
    obs_date = fields.Date(string='Observation Date', default=fields.Date.today, required=True)
    observer_id = fields.Many2one('res.users', string='Observer', default=lambda self: self.env.user, required=True)
    work_activity = fields.Char(string='Work Activity Observed (e.g. Flange torquing, Scaffold dismantling)', required=True)

    people_observed_count = fields.Integer(string='Workers Observed', default=3, required=True)
    safe_behaviors_count = fields.Integer(string='Safe Behaviors Counted', default=8, required=True)
    at_risk_behaviors_count = fields.Integer(string='At-Risk Behaviors Counted', default=1, required=True)
    safe_behavior_index = fields.Float(string='Safe Behavior Index (%)', compute='_compute_index', store=True)

    # Behavioral Categories Observed
    cat_body_position = fields.Boolean(string='Body Position & Line of Fire / Pinch Points')
    cat_ppe = fields.Boolean(string='PPE Selection & Proper Usage')
    cat_tools_equipment = fields.Boolean(string='Correct Tools & Machinery Guarding')
    cat_procedures = fields.Boolean(string='Following Written Operating Procedures / Permits')
    cat_housekeeping = fields.Boolean(string='Work Area Housekeeping & Walking/Working Surfaces')
    cat_eyes_on_task = fields.Boolean(string='Eyes on Task & Situational Awareness')

    at_risk_description = fields.Text(string='Description of At-Risk Act / Condition Observed')
    immediate_coaching_feedback = fields.Text(string='Positive Coaching Dialogue & Agreement with Worker', required=True)
    root_reason_for_at_risk = fields.Selection([
        ('short_cut', 'Saving Time / Taking a Shortcut'),
        ('awkward_workstation', 'Awkward Workstation Design / Heavy Effort'),
        ('lack_of_awareness', 'Lack of Hazard Awareness / Complacency'),
        ('wrong_tool', 'Correct Tool / Equipment Not Readily Available'),
        ('ppe_uncomfortable', 'PPE Uncomfortable or Ill-Fitting'),
        ('rushed_pressure', 'Production / Time Pressure'),
    ], string='Perceived Driver for At-Risk Behavior')

    state = fields.Selection([
        ('submitted', 'Observation Recorded'),
        ('coached', 'Safety Dialogue Completed'),
        ('analyzed', 'Reviewed by HSE Committee'),
    ], string='Status', default='coached', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.bbs.observation') or _('BBS-%05d') % self.env['hse.bbs.observation'].search_count([])
        return super().create(vals_list)

    @api.depends('safe_behaviors_count', 'at_risk_behaviors_count')
    def _compute_index(self):
        for rec in self:
            total = (rec.safe_behaviors_count or 0) + (rec.at_risk_behaviors_count or 0)
            if total > 0:
                rec.safe_behavior_index = round(((rec.safe_behaviors_count or 0) / total) * 100.0, 1)
            else:
                rec.safe_behavior_index = 100.0
