# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HseLdarComponent(models.Model):
    _name = 'hse.ldar.component'
    _description = 'LDAR Fugitive Component Tag (EPA Method 21)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'tag_number asc'

    tag_number = fields.Char(string='Component Tag #', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Process Unit', required=True)
    component_type = fields.Selection([
        ('valve', 'Process Control / Block Valve'),
        ('flange', 'Flange / Mechanical Joint'),
        ('pump_seal', 'Pump Mechanical Seal'),
        ('compressor_seal', 'Compressor Shaft Seal'),
        ('prv', 'Pressure Relief Device (Atmospheric)'),
        ('sampling_connection', 'Open-Ended Sampling Point'),
    ], string='Component Type', default='valve', required=True)

    service_stream = fields.Selection([
        ('gas_vapor', 'Gas / Vapor Service'),
        ('light_liquid', 'Light Liquid (Vapor Pressure > 0.3 kPa)'),
        ('heavy_liquid', 'Heavy Liquid'),
    ], string='Process Stream Service', default='gas_vapor', required=True)

    leak_threshold_ppm = fields.Float(string='Regulatory Leak Threshold (ppm)', default=500.0, required=True)
    monitoring_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ], string='Mandatory Monitoring Cycle', default='quarterly', required=True)

    is_leaking = fields.Boolean(string='Currently Leaking', default=False, tracking=True)
    reading_ids = fields.One2many('hse.ldar.reading', 'component_id', string='Monitoring Readings')
    reading_count = fields.Integer(string='Readings Count', compute='_compute_readings')

    @api.depends('reading_ids')
    def _compute_readings(self):
        for rec in self:
            rec.reading_count = len(rec.reading_ids)


class HseLdarReading(models.Model):
    _name = 'hse.ldar.reading'
    _description = 'LDAR Method 21 Inspection Reading'
    _order = 'inspection_date desc'

    component_id = fields.Many2one('hse.ldar.component', string='Component', required=True, ondelete='cascade')
    inspection_date = fields.Date(string='Inspection Date', default=fields.Date.today, required=True)
    inspector_name = fields.Char(string='Certified LDAR Technician', default='Certified EPA Method 21 Inspector')
    snid_analyzer_serial = fields.Char(string='FID / PID Analyzer S/N')

    background_ppm = fields.Float(string='Atmospheric Background (ppm)', default=5.0)
    screening_value_ppm = fields.Float(string='Screening Reading (ppm)', required=True)
    net_leak_ppm = fields.Float(string='Net Emission (ppm)', compute='_compute_net', store=True)

    is_leak = fields.Boolean(string='Regulatory Leak (> Threshold)', compute='_compute_net', store=True)
    first_attempt_date = fields.Date(string='First Attempt at Repair (Within 5 Days)')
    final_repair_date = fields.Date(string='Final Repair & Re-monitoring Date (Within 15 Days)')
    delay_of_repair_dor = fields.Boolean(string='Placed on Delay of Repair (DOR - Shutdown Required)', default=False)
    dor_justification = fields.Text(string='DOR Technical Justification')

    state = fields.Selection([
        ('compliant', 'Compliant (No Leak)'),
        ('leaking', 'Leak Detected (5-Day Clock Active)'),
        ('repaired', 'Repaired & Re-monitored Pass'),
        ('dor', 'Approved Delay of Repair (Turnaround)'),
    ], string='Reading Status', compute='_compute_status', store=True)

    @api.depends('screening_value_ppm', 'background_ppm', 'component_id.leak_threshold_ppm')
    def _compute_net(self):
        for rec in self:
            net = max((rec.screening_value_ppm or 0.0) - (rec.background_ppm or 0.0), 0.0)
            rec.net_leak_ppm = net
            thresh = rec.component_id.leak_threshold_ppm or 500.0
            rec.is_leak = net >= thresh
            rec.component_id.is_leaking = rec.is_leak

    @api.depends('is_leak', 'final_repair_date', 'delay_of_repair_dor')
    def _compute_status(self):
        for rec in self:
            if not rec.is_leak:
                rec.state = 'compliant'
            elif rec.delay_of_repair_dor:
                rec.state = 'dor'
            elif rec.final_repair_date:
                rec.state = 'repaired'
            else:
                rec.state = 'leaking'
