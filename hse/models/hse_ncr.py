# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date

class HSENonConformance(models.Model):
    _name = 'hse.ncr'
    _description = 'Non-Conformance Management (NCR)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='NCR Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Non-Conformance Title', required=True, tracking=True)
    ncr_source = fields.Selection([
        ('inspection', 'Receiving / Incoming Material Inspection'),
        ('process', 'In-Process Fabrication / Construction'),
        ('maintenance', 'Equipment Maintenance / Overhaul Discrepancy'),
        ('audit', 'Quality / HSE Management System Audit'),
        ('supplier', 'Supplier / Vendor Deliverable Non-compliance'),
        ('operations', 'Operational Process Deviation'),
    ], string='Discovery Source', default='process', required=True, tracking=True)

    severity = fields.Selection([
        ('minor', 'Minor (Cosmetic / Low Risk Deviation)'),
        ('major', 'Major (Specification Violation / Integrity Impact)'),
        ('critical', 'Critical (Process Safety / Life Threatening / Major Failure Risk)'),
    ], string='NCR Severity', default='major', required=True, tracking=True)

    location_id = fields.Many2one('hse.location.profile', string='Area / Location')
    asset_id = fields.Many2one('assets.form', string='Asset / Equipment Affected')
    supplier_id = fields.Many2one('res.partner', string='Supplier / Contractor')

    # Non-conformance Details
    problem_description = fields.Text(string='Detailed Discrepancy Description', required=True)
    specification_requirement = fields.Text(string='Applicable Engineering Specification / Requirement', required=True)

    # Immediate Containment / Quarantine
    is_quarantined = fields.Boolean(string='Material / Equipment Placed in Quarantine', default=False, tracking=True)
    quarantine_tag_no = fields.Char(string='Quarantine Danger Tag #')
    quarantine_location = fields.Char(string='Quarantine Physical Staging Area')
    immediate_containment_action = fields.Text(string='Immediate Containment Actions Taken')

    # Disposition
    disposition = fields.Selection([
        ('rework', 'Rework to Original Specification'),
        ('repair', 'Repair with Engineering Concession'),
        ('scrap', 'Scrap & Condemn'),
        ('rtv', 'Return to Vendor / Supplier (RTV)'),
        ('concession', 'Accept As-Is / Technical Concession'),
    ], string='Approved Disposition', tracking=True)
    disposition_justification = fields.Text(string='Technical Disposition Justification')
    disposition_authorized_by = fields.Many2one('res.users', string='Disposition Technical Authority')

    # Cost of Non-Conformance (CONC)
    conc_material_cost = fields.Float(string='Scrapped Material Value ($)')
    conc_labor_cost = fields.Float(string='Rework / Re-inspection Labor ($)')
    conc_delay_penalty = fields.Float(string='Delay / Demurrage Penalties ($)')
    conc_total = fields.Float(string='Total Cost of Non-Conformance ($)', compute='_compute_conc_total', store=True)

    # CAPA Link
    action_id = fields.Many2one('hse.action', string='Corrective Action Record (CAPA)')

    originator_id = fields.Many2one('res.users', string='Identified By', required=True, default=lambda self: self.env.user)
    closure_date = fields.Date(string='Formal Closure Date')

    state = fields.Selection([
        ('draft', 'Draft NCR'),
        ('quarantined', 'Identified & Quarantined'),
        ('disposition_review', 'Disposition Under Technical Review'),
        ('disposition_approved', 'Disposition Approved / Execution'),
        ('action_in_progress', 'CAPA Remediation In Progress'),
        ('closed', 'Remediation Verified & Closed'),
        ('cancelled', 'Cancelled'),
    ], string='NCR Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.ncr') or _('NCR-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    @api.depends('conc_material_cost', 'conc_labor_cost', 'conc_delay_penalty')
    def _compute_conc_total(self):
        for rec in self:
            rec.conc_total = rec.conc_material_cost + rec.conc_labor_cost + rec.conc_delay_penalty

    def action_quarantine(self):
        self.write({
            'state': 'quarantined',
            'is_quarantined': True
        })

    def action_request_disposition(self):
        self.write({'state': 'disposition_review'})

    def action_approve_disposition(self):
        self.write({
            'state': 'disposition_approved',
            'disposition_authorized_by': self.env.user.id
        })

    def action_close(self):
        self.write({
            'state': 'closed',
            'closure_date': date.today()
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})
