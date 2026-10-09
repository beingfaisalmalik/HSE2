# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HsePermitConfinedSpace(models.Model):
    _name = 'hse.permit.confined.space'
    _description = 'Confined Space Entry Permit & Continuous Atmosphere Monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Entry Certificate #', required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('hse.permit.confined.space') or _('New'))
    permit_id = fields.Many2one('hse.permit', string='Master Work Permit', ondelete='cascade')
    location_id = fields.Many2one('hse.location.profile', string='Vessel / Compartment Location', required=True)
    space_identifier = fields.Char(string='Confined Space Tag / Vessel ID', required=True)

    space_classification = fields.Selection([
        ('class_a', 'Class A: Immediately Dangerous to Life or Health (IDLH)'),
        ('class_b', 'Class B: Dangerous But Not Immediately Life Threatening'),
        ('class_c', 'Class C: Potential Hazard / Standard Confined Space'),
    ], string='Atmospheric Hazard Class', default='class_b', required=True)

    # Mandatory Safety Verification Checks
    isolation_verified = fields.Boolean(string='Mechanical / Process Isolation Verified (Blinded & Locked)')
    loto_plan_id = fields.Many2one('hse.loto.plan', string='Associated LOTO Plan')
    electrical_lockout_verified = fields.Boolean(string='Electrical Drives Locked & De-energized')
    ventilation_method = fields.Selection([
        ('forced_mechanical', 'Continuous Forced Mechanical Ventilation'),
        ('eductor_air_horn', 'Pneumatic Eductor Air Horn'),
        ('natural_draft', 'Natural Convective Draft (Approved Low Hazard Only)'),
    ], string='Purging & Ventilation', default='forced_mechanical', required=True)
    ventilation_cfm_rate = fields.Float(string='Ventilation Air Flow Rate (CFM)', default=2500.0)

    # Standby & Emergency Preparedness
    attendant_name = fields.Char(string='Designated Standby Attendant (Hole Watch)', required=True)
    rescue_team_notified = fields.Boolean(string='Plant Emergency Rescue Team Notified & On Standby', default=True)
    tripod_winch_inspected = fields.Boolean(string='Retrieval Tripod, Winch & Harness Inspected', default=True)
    scba_available = fields.Boolean(string='Emergency Escape SCBA / EEBD Available at Manway', default=True)
    continuous_detector_serial = fields.Char(string='Continuous Multi-Gas Detector S/N', default='RAE-QRAE3-TX9012')

    # Sub-records
    entrant_ids = fields.One2many('hse.permit.cs.entrant', 'cse_id', string='Authorized Entrants Log')
    gas_log_ids = fields.One2many('hse.permit.cs.gas_log', 'cse_id', string='Continuous Gas Telemetry Log')

    active_entrants_count = fields.Integer(string='Current Personnel Inside Space', compute='_compute_entrants', store=True)
    gas_readings_count = fields.Integer(string='Gas Samples Logged', compute='_compute_gas_stats')
    latest_atmosphere_safe = fields.Boolean(string='Latest Atmosphere Safe', compute='_compute_gas_stats')

    state = fields.Selection([
        ('draft', 'Draft Entry Certificate'),
        ('pre_entry_check', 'Pre-Entry Inspection'),
        ('active_entry', 'Active Entry in Progress'),
        ('suspended', 'Entry Suspended (Unsafe / Break)'),
        ('closed', 'Closed & Manway Secured'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('entrant_ids.status')
    def _compute_entrants(self):
        for rec in self:
            rec.active_entrants_count = len(rec.entrant_ids.filtered(lambda e: e.status == 'inside'))

    @api.depends('gas_log_ids.is_safe')
    def _compute_gas_stats(self):
        for rec in self:
            logs = rec.gas_log_ids.sorted('sample_timestamp', reverse=True)
            rec.gas_readings_count = len(logs)
            rec.latest_atmosphere_safe = logs[0].is_safe if logs else True

    def action_authorize_entry(self):
        if not self.isolation_verified:
            raise ValidationError(_('Cannot authorize entry: Process isolation and blind list must be verified.'))
        if not self.rescue_team_notified:
            raise ValidationError(_('Cannot authorize entry: Plant rescue team must be notified and on standby.'))
        self.write({'state': 'active_entry'})

    def action_suspend_entry(self):
        self.write({'state': 'suspended'})

    def action_resume_entry(self):
        self.write({'state': 'active_entry'})

    def action_close_entry(self):
        if self.active_entrants_count > 0:
            raise ValidationError(_('Cannot close entry certificate: All entrants must log out of the confined space first! Current inside: %s') % self.active_entrants_count)
        self.write({'state': 'closed'})


class HsePermitCsEntrant(models.Model):
    _name = 'hse.permit.cs.entrant'
    _description = 'Confined Space Authorized Entrant'
    _order = 'entry_time desc'

    cse_id = fields.Many2one('hse.permit.confined.space', string='Confined Space Entry Permit',
                             required=True, ondelete='cascade')
    worker_name = fields.Char(string='Entrant Full Name', required=True)
    badge_number = fields.Char(string='Site Badge / ID Number', required=True)
    entry_time = fields.Datetime(string='Time In', default=fields.Datetime.now, required=True)
    exit_time = fields.Datetime(string='Time Out')
    status = fields.Selection([
        ('inside', 'Inside Confined Space'),
        ('exited', 'Safely Exited'),
    ], string='Presence Status', default='inside', required=True)
    harness_attached = fields.Boolean(string='Full Body Harness & Lifeline Verified', default=True)

    def action_log_exit(self):
        self.write({
            'exit_time': fields.Datetime.now(),
            'status': 'exited',
        })


class HsePermitCsGasLog(models.Model):
    _name = 'hse.permit.cs.gas_log'
    _description = 'Confined Space Continuous Gas Sampling Log'
    _order = 'sample_timestamp desc'

    cse_id = fields.Many2one('hse.permit.confined.space', string='Confined Space Permit',
                             required=True, ondelete='cascade')
    sample_timestamp = fields.Datetime(string='Sample Timestamp', default=fields.Datetime.now, required=True)
    oxygen_pct = fields.Float(string='O₂ Concentration (%)', default=20.9, required=True)
    combustible_lel_pct = fields.Float(string='LEL Flammable Gas (%)', default=0.0, required=True)
    h2s_ppm = fields.Float(string='H₂S Toxic Gas (ppm)', default=0.0, required=True)
    co_ppm = fields.Float(string='CO Toxic Gas (ppm)', default=0.0, required=True)

    is_safe = fields.Boolean(string='Atmosphere Within Safe Limits', compute='_compute_safety', store=True)
    alarm_triggered = fields.Boolean(string='Audible Alarm Triggered', compute='_compute_safety', store=True)

    @api.depends('oxygen_pct', 'combustible_lel_pct', 'h2s_ppm', 'co_ppm')
    def _compute_safety(self):
        for rec in self:
            o2_ok = 19.5 <= rec.oxygen_pct <= 23.5
            lel_ok = rec.combustible_lel_pct < 5.0
            h2s_ok = rec.h2s_ppm < 5.0
            co_ok = rec.co_ppm < 25.0
            safe = o2_ok and lel_ok and h2s_ok and co_ok
            rec.is_safe = safe
            rec.alarm_triggered = not safe
