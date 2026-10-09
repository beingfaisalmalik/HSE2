# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HSESece(models.Model):
    _name = 'hse.sece'
    _description = 'Safety Critical Element & Performance Standard (SECE)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'tag asc, id desc'

    tag = fields.Char(string='SECE Tag / System ID', required=True, copy=False, tracking=True)
    name = fields.Char(string='Safety Critical Element Name', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Installation / Plant Unit', required=True)
    asset_id = fields.Many2one('assets.form', string='Physical Plant Asset')

    sece_group = fields.Selection([
        ('structural', 'Group 1: Structural Integrity & Foundations'),
        ('process_containment', 'Group 2: Hydrocarbon & Toxic Process Containment'),
        ('ignition_control', 'Group 3: Ignition Prevention & Ex-Proof Enclosures'),
        ('detection', 'Group 4: Fire & Toxic Gas Detection (F&G)'),
        ('emergency_shutdown', 'Group 5: Emergency Shutdown Systems (ESD & Blowdown)'),
        ('protection_relief', 'Group 6: Overpressure Protection & Relief (PSVs, Flares)'),
        ('firefighting', 'Group 7: Fire Protection & Deluge Systems (Active & Passive)'),
        ('evacuation', 'Group 8: Lifeboats, Muster & Escape Ways (EER)'),
        ('emergency_power', 'Group 9: Emergency Power & UPS Systems'),
        ('environmental_barrier', 'Group 10: Environmental Secondary Containment'),
    ], string='SECE Barrier Group', required=True, tracking=True, default='process_containment')

    major_accident_hazard = fields.Text(string='Associated Major Accident Hazards (MAH)', required=True)

    # FARSI Performance Standards
    functionality_std = fields.Text(string='Functionality Criterion (What it must perform under demand)', required=True)
    availability_std = fields.Float(string='Target Availability (%)', default=99.5, required=True)
    reliability_std = fields.Char(string='Target Reliability (MTBF or SIL Target)', default='SIL 2 / PFD < 0.01', required=True)
    survivability_std = fields.Text(string='Survivability Specification (Fire proofing, Blast resistance, Earthquake)', required=True)
    interaction_std = fields.Text(string='System Interaction & Dependencies (Utilities, Air, Hydraulics, UPS)')

    # Operational Health
    barrier_health = fields.Selection([
        ('healthy', 'Fully Operational / Performance Standards Met'),
        ('degraded', 'Degraded / Requires Corrective Maintenance'),
        ('failed', 'Impaired / Failed Performance Standard'),
        ('isolated', 'Isolated / Bypassed under Formal Authorization'),
    ], string='Current Barrier Status', default='healthy', tracking=True)

    independent_verification_body = fields.Char(string='Independent Verification Body (IVB - e.g. DNV / Lloyd\'s Register)')
    last_ivb_audit_date = fields.Date(string='Last IVB Audit Date')
    next_ivb_audit_date = fields.Date(string='Next Scheduled IVB Audit')

    assurance_task_ids = fields.One2many('hse.sece.assurance', 'sece_id', string='Assurance Tasks & Proof Tests')
    assurance_count = fields.Integer(string='Assurance Tasks Count', compute='_compute_task_count', store=True)

    state = fields.Selection([
        ('active', 'Commissioned & Active In-Service'),
        ('impaired', 'Impaired / Deficient'),
        ('decommissioned', 'Decommissioned / Retired'),
    ], string='Status', default='active', tracking=True)

    @api.depends('assurance_task_ids')
    def _compute_task_count(self):
        for rec in self:
            rec.assurance_count = len(rec.assurance_task_ids)

    def action_set_healthy(self):
        self.write({'barrier_health': 'healthy', 'state': 'active'})

    def action_set_degraded(self):
        self.write({'barrier_health': 'degraded'})

    def action_set_impaired(self):
        self.write({'barrier_health': 'failed', 'state': 'impaired'})


class HSESeceAssurance(models.Model):
    _name = 'hse.sece.assurance'
    _description = 'SECE Assurance Task / Proof Test Record'
    _order = 'test_date desc, id desc'

    sece_id = fields.Many2one('hse.sece', string='Safety Critical Element', ondelete='cascade', required=True)
    test_date = fields.Date(string='Test / Inspection Date', default=fields.Date.today, required=True)
    inspector_id = fields.Many2one('res.users', string='Certified Competent Inspector', required=True, default=lambda self: self.env.user)
    
    test_type = fields.Selection([
        ('proof_test', 'Full Loop Function / Proof Test'),
        ('calibration', 'Transmitter Calibration & Drift Verification'),
        ('pop_test', 'PSV Pop Test & Seat Tightness Bench Test'),
        ('deluge_flow', 'Deluge Foam/Water Flow & Nozzle Integrity Test'),
        ('ups_load', 'Emergency Generator / UPS 4-Hour Battery Load Test'),
        ('thickness', 'Ultrasonic Wall Thickness & Corrosion Survey'),
    ], string='Assurance Test Category', required=True, default='proof_test')

    test_procedure_ref = fields.Char(string='Operating Standard Procedure / PM Reference', required=True)
    measured_parameters = fields.Text(string='Measured Test Parameters & Response Time', required=True)

    result = fields.Selection([
        ('pass', 'Passed - Fully Meets Performance Standard'),
        ('conditional_pass', 'Pass with Advisory Deficiencies'),
        ('fail', 'Failed - Immediate Impairment Notice Generated'),
    ], string='Assurance Outcome', required=True, default='pass')

    defects_noted = fields.Text(string='Deficiencies & Non-conformances Identified')
    capa_action_id = fields.Many2one('hse.action', string='Corrective Action Reference')
