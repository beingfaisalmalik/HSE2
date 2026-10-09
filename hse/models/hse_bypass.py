# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class HSEBypass(models.Model):
    _name = 'hse.bypass'
    _description = 'Safety Bypass, Inhibit & Override Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'applied_datetime desc, id desc'

    name = fields.Char(string='Bypass Certificate Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Bypass Description / Tag', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Area / Unit', required=True)
    asset_id = fields.Many2one('assets.form', string='Target Equipment / Loop')
    tag_number = fields.Char(string='Instrument / Interlock Tag # (e.g. PSHH-104B)', required=True, tracking=True)

    bypass_type = fields.Selection([
        ('sis', 'Safety Instrumented System (SIS) Inhibit'),
        ('esd', 'Emergency Shutdown (ESD) Override'),
        ('fire_gas', 'Fire & Gas (F&G) Detector Disable / Bypass'),
        ('alarm', 'Critical DCS Process Alarm Shelve / Inhibit'),
        ('mechanical', 'Mechanical Relief Valve / Interlock Key Override'),
    ], string='Bypass Category', default='sis', required=True, tracking=True)

    safety_criticality = fields.Selection([
        ('sil1', 'SIL 1 Safety Function'),
        ('sil2', 'SIL 2 High Criticality Function'),
        ('sil3', 'SIL 3 Major Hazard Safety Barrier'),
        ('non_sil', 'Operational Interlock (Non-SIL)'),
    ], string='Safety Integrity Level (SIL)', default='sil2', required=True, tracking=True)

    reason = fields.Selection([
        ('calibration', 'Routine Transmitter Calibration & Proof Testing'),
        ('maintenance', 'Online Instrument Sensor Replacement'),
        ('startup', 'Plant Warm-up / Transient Startup Condition'),
        ('fault', 'Transmitter Hardware Failure / Spurious Trip Prevention'),
    ], string='Technical Justification', default='calibration', required=True)

    details = fields.Text(string='Detailed Engineering Reason for Bypass', required=True)

    # Mandatory Compensating Risk Controls
    compensating_controls = fields.Text(string='Mandatory Compensating Safeguards (e.g. Dedicated Field Watch, Local Gauge Monitoring)', required=True)
    has_dedicated_watcher = fields.Boolean(string='Dedicated Field Operator Stationed on Site', default=True)
    operating_rate_reduced = fields.Boolean(string='Plant Operating Throughput Derated for Safety')

    # Time & Duration Tracking
    expected_duration_hours = fields.Float(string='Authorized Duration (Hours)', default=8.0, required=True)
    applied_datetime = fields.Datetime(string='Bypass Inhibit Applied Timestamp', default=fields.Datetime.now, tracking=True)
    expected_reinstatement = fields.Datetime(string='Scheduled Normalization Time', compute='_compute_reinstatement', store=True)
    actual_reinstated_datetime = fields.Datetime(string='Actual Normalization Timestamp', tracking=True)
    is_overdue = fields.Boolean(string='Bypass Exceeded Authorized Duration', compute='_compute_overdue', store=True)

    # Required Authorization Level Based on Duration
    authorization_level = fields.Selection([
        ('shift_supervisor', 'Level 1: Shift Supervisor (< 8 Hours)'),
        ('operations_manager', 'Level 2: Operations Manager (8 - 24 Hours)'),
        ('plant_director', 'Level 3: Plant Director (> 24 Hours)'),
    ], string='Required Approval Level', compute='_compute_auth_level', store=True)

    # Sign-offs
    requester_id = fields.Many2one('res.users', string='Requested By (Control Room)', default=lambda self: self.env.user, required=True)
    approver_id = fields.Many2one('res.users', string='Authorized Approver', tracking=True)
    approval_datetime = fields.Datetime(string='Authorization Timestamp')

    # Normalization Sign-off
    normalized_by_id = fields.Many2one('res.users', string='Reinstated / Normalized By')
    reinstatement_tested = fields.Boolean(string='Instrument Signal Restored & Tested Healthy', default=False)
    normalization_notes = fields.Text(string='Reinstatement Verification Notes')

    state = fields.Selection([
        ('draft', 'Draft Request'),
        ('requested', 'Authorization Requested'),
        ('approved', 'Approved'),
        ('active', 'Bypass Active (SAFETY OVERRIDDEN)'),
        ('reinstated', 'Normalized & Reinstated'),
        ('cancelled', 'Cancelled'),
    ], string='Bypass Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.bypass') or _('BYP-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    @api.depends('expected_duration_hours')
    def _compute_auth_level(self):
        for rec in self:
            if rec.expected_duration_hours <= 8.0:
                rec.authorization_level = 'shift_supervisor'
            elif rec.expected_duration_hours <= 24.0:
                rec.authorization_level = 'operations_manager'
            else:
                rec.authorization_level = 'plant_director'

    @api.depends('applied_datetime', 'expected_duration_hours')
    def _compute_reinstatement(self):
        for rec in self:
            if rec.applied_datetime and rec.expected_duration_hours:
                rec.expected_reinstatement = rec.applied_datetime + timedelta(hours=rec.expected_duration_hours)
            else:
                rec.expected_reinstatement = False

    @api.depends('state', 'expected_reinstatement')
    def _compute_overdue(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.state == 'active' and rec.expected_reinstatement and rec.expected_reinstatement < now:
                rec.is_overdue = True
            else:
                rec.is_overdue = False

    def action_request(self):
        self.write({'state': 'requested'})

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id,
            'approval_datetime': fields.Datetime.now(),
        })

    def action_apply_bypass(self):
        self.write({
            'state': 'active',
            'applied_datetime': fields.Datetime.now(),
        })

    def action_reinstate(self):
        if not self.reinstatement_tested:
            raise UserError(_("You must confirm that the instrument loop has been tested and verified healthy before normalizing."))
        self.write({
            'state': 'reinstated',
            'actual_reinstated_datetime': fields.Datetime.now(),
            'normalized_by_id': self.env.user.id,
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})
