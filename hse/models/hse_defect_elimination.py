# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date

class HSEDefectElimination(models.Model):
    _name = 'hse.defect.elimination'
    _description = 'Defect Elimination & Bad Actor Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Project Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Defect Elimination Title', required=True, tracking=True)
    asset_id = fields.Many2one('assets.form', string='Bad Actor Asset / Tag', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Area / Unit', required=True)

    defect_category = fields.Selection([
        ('chronic_leak', 'Chronic Flange / Valve Packing Leakage'),
        ('repeat_trip', 'Repeated Spurious Trip / Instrumentation Fault'),
        ('vibration_resonance', 'High Vibration / Piping Fatigue Resonance'),
        ('seal_failure', 'Premature Mechanical Seal / Bearing Failure'),
        ('fouling_plugging', 'Frequent Exchanger Fouling / Line Plugging'),
        ('electrical_arcing', 'Electrical Drive / Motor Burnout Cycle'),
    ], string='Defect Type', default='chronic_leak', required=True, tracking=True)

    # Bad Actor Statistics
    failures_last_12_months = fields.Integer(string='Failure Frequency (Last 12 Months)', default=4, required=True)
    annual_maintenance_spend = fields.Float(string='Annual Maintenance Cost ($)', default=0.0)
    annual_production_loss = fields.Float(string='Annual Production Downtime Loss ($)', default=0.0)

    defect_description = fields.Text(string='Detailed Chronic Defect Description', required=True)
    underlying_cause = fields.Text(string='Underlying Systemic / Operational Causes', required=True)
    elimination_strategy = fields.Text(string='Engineered Elimination Strategy', required=True)

    # Cross-Functional Team
    operator_lead_id = fields.Many2one('res.users', string='Operations Representative', required=True, default=lambda self: self.env.user)
    maintenance_lead_id = fields.Many2one('res.users', string='Maintenance / Tech Representative')
    reliability_engineer_id = fields.Many2one('res.users', string='Lead Reliability Engineer')

    # Post-Elimination Defect-Free Tracking
    target_implementation_date = fields.Date(string='Elimination Target Date')
    elimination_completed_date = fields.Date(string='Elimination Fix Applied Date')

    track_30_days = fields.Boolean(string='30-Day Defect-Free Operational Run Verified', default=False, tracking=True)
    track_60_days = fields.Boolean(string='60-Day Defect-Free Operational Run Verified', default=False, tracking=True)
    track_90_days = fields.Boolean(string='90-Day Defect-Free Sustained Success Confirmed', default=False, tracking=True)

    state = fields.Selection([
        ('identified', 'Bad Actor Identified'),
        ('team_review', 'Cross-Functional Team Investigation'),
        ('action_execution', 'Elimination Actions in Execution'),
        ('tracking_period', 'Defect-Free Run Verification (90 Days)'),
        ('eliminated', 'Defect Permanently Eliminated'),
        ('closed', 'Project Closed'),
    ], string='Status', default='identified', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.defect.elimination') or _('DEF-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def action_start_team_review(self):
        self.write({'state': 'team_review'})

    def action_execute(self):
        self.write({'state': 'action_execution'})

    def action_start_tracking(self):
        self.write({
            'state': 'tracking_period',
            'elimination_completed_date': date.today()
        })

    def action_mark_eliminated(self):
        self.write({
            'state': 'eliminated',
            'track_30_days': True,
            'track_60_days': True,
            'track_90_days': True,
        })

    def action_close(self):
        self.write({'state': 'closed'})
