# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEProcessSafetyEvent(models.Model):
    _name = 'hse.pse'
    _description = 'API RP 754 Process Safety Event (PSE / LOPC)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_datetime desc, id desc'

    name = fields.Char(string='PSE Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Event Title', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Process Unit / Facility', required=True)
    event_datetime = fields.Datetime(string='Incident Timestamp', default=fields.Datetime.now, required=True, tracking=True)

    tier = fields.Selection([
        ('tier1', 'API RP 754 Tier 1 Process Safety Event (Major Hazard LOPC)'),
        ('tier2', 'API RP 754 Tier 2 Process Safety Event (Moderate LOPC)'),
        ('tier3', 'API RP 754 Tier 3 Challenge to Safety Systems (Demand on SIF/PSV)'),
        ('tier4', 'API RP 754 Tier 4 Operating Discipline & Process Safety Metric'),
    ], string='Process Safety Tier', required=True, default='tier2', tracking=True)

    mode_of_operation = fields.Selection([
        ('normal', 'Normal Steady-State Operation'),
        ('startup', 'Plant Startup / Transient'),
        ('shutdown', 'Controlled Shutdown'),
        ('emergency_shutdown', 'Emergency Shutdown / Trip Response'),
        ('maintenance', 'Turnaround / Maintenance De-inventory'),
    ], string='Operating Mode', default='normal', required=True)

    # Chemical Release Details (LOPC)
    chemical_id = fields.Many2one('hse.location.chemical', string='Released Substance')
    chemical_name = fields.Char(string='Chemical / Material Released', required=True)
    phase_of_release = fields.Selection([
        ('gas', 'Gas / Vapor'),
        ('liquid', 'Liquid'),
        ('two_phase', 'Two-Phase Flashing Jet'),
        ('solid', 'Slurry / Catalyst'),
    ], string='Phase', default='liquid', required=True)

    release_duration_minutes = fields.Float(string='Duration of Release (Minutes)', default=15.0)
    mass_released_kg = fields.Float(string='Total Mass Released (kg)', required=True)
    threshold_quantity_kg = fields.Float(string='API RP 754 Threshold Quantity (kg)', default=500.0)
    threshold_exceeded = fields.Boolean(string='Threshold Quantity Exceeded', compute='_compute_threshold_exceeded', store=True)

    # Consequences
    has_fatality = fields.Boolean(string='Resulted in Fatality', default=False)
    has_lost_time_injury = fields.Boolean(string='Resulted in Days Away From Work (DAFW / LTI)', default=False)
    has_hospitalization = fields.Boolean(string='Resulted in Hospital Admission (Inpatient)', default=False)
    has_fire_explosion = fields.Boolean(string='Resulted in Fire or Explosion', default=False)
    direct_cost = fields.Float(string='Total Direct Cost of Event ($)', default=0.0)
    offsite_impact = fields.Boolean(string='Offsite Impact / Public Evacuation / Shelter-in-Place', default=False)

    barrier_failure_summary = fields.Text(string='Root Causes & Safety Barrier Failures Identified', required=True)
    investigation_id = fields.Many2one('incident.investigation', string='Comprehensive RCA Investigation')

    state = fields.Selection([
        ('reported', 'Reported'),
        ('investigating', 'Detailed Barrier Investigation'),
        ('classified', 'Formally Classified & Validated'),
        ('regulatory_reported', 'Reported to National Regulator (e.g. OSHA / EPA / CSB)'),
        ('closed', 'Actions Complete & Closed'),
    ], string='Event Status', default='reported', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.pse') or _('PSE-%04d') % self.env['hse.pse'].search_count([])
        return super().create(vals_list)

    @api.depends('mass_released_kg', 'threshold_quantity_kg')
    def _compute_threshold_exceeded(self):
        for rec in self:
            rec.threshold_exceeded = bool(rec.mass_released_kg and rec.threshold_quantity_kg and rec.mass_released_kg >= rec.threshold_quantity_kg)

    def action_investigate(self):
        self.write({'state': 'investigating'})

    def action_classify(self):
        self.write({'state': 'classified'})

    def action_regulatory_report(self):
        self.write({'state': 'regulatory_reported'})

    def action_close(self):
        self.write({'state': 'closed'})
