# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HseBarrierElement(models.Model):
    _name = 'hse.barrier.element'
    _description = 'Safety Barrier Integrity Element (Hardware / Human / Organizational)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'location_id asc, name asc'

    name = fields.Char(string='Barrier Tag / Name', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Area / Asset', required=True)
    barrier_type = fields.Selection([
        ('hardware', 'Hardware / Engineered Barrier (SECE / SIS / PSV)'),
        ('human', 'Human / Operational Barrier (Operator Response, AGT Gas Test)'),
        ('organizational', 'Organizational Barrier (SOP, MOC, Competency Certification)'),
    ], string='Barrier Architecture', default='hardware', required=True)

    barrier_role = fields.Selection([
        ('prevention', 'Threat Prevention (Left side of Bow-Tie)'),
        ('mitigation', 'Consequence Mitigation (Right side of Bow-Tie)'),
    ], string='Bow-Tie Defense Line', default='prevention', required=True)

    sece_id = fields.Many2one('hse.sece', string='Safety Critical Element (if Hardware)')
    sif_id = fields.Many2one('hse.sif', string='Safety Instrumented Function (if SIS)')
    procedure_id = fields.Many2one('hse.operating.procedure', string='Operating Procedure (if Human/Org)')

    health_status = fields.Selection([
        ('effective', 'Effective & Healthy (100% Assurance)'),
        ('degraded', 'Degraded (Inspection / Overdue Test)'),
        ('bypassed', 'Active Bypass / Inhibit'),
        ('failed', 'FAILED BARRIER (Zero Containment)'),
    ], string='Real-Time Barrier Health', default='effective', tracking=True, required=True)

    impairment_reason = fields.Text(string='Degradation / Failure Cause')
    compensatory_measures = fields.Text(string='Active Compensatory Controls')

    is_impaired = fields.Boolean(string='Barrier Impaired', compute='_compute_impaired', store=True)

    @api.depends('health_status')
    def _compute_impaired(self):
        for rec in self:
            rec.is_impaired = rec.health_status in ['degraded', 'bypassed', 'failed']

    def action_set_healthy(self):
        self.write({'health_status': 'effective', 'impairment_reason': False})

    def action_set_degraded(self):
        self.write({'health_status': 'degraded'})

    def action_set_bypassed(self):
        self.write({'health_status': 'bypassed'})

    def action_set_failed(self):
        self.write({'health_status': 'failed'})
