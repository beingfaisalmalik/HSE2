# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEBenefitLoss(models.Model):
    _name = 'hse.benefit.loss'
    _description = 'HSE Benefits & Losses Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc, id desc'

    name = fields.Char(string='Benefit/Loss Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Impact Title', required=True, tracking=True)
    event_type = fields.Selection([
        ('loss', 'Operational / Safety Loss Event'),
        ('benefit', 'Realized Benefit / Avoided Cost'),
    ], string='Impact Type', default='loss', required=True, tracking=True)

    event_date = fields.Date(string='Accounting / Event Date', default=fields.Date.today, required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Area / Unit', required=True)
    asset_id = fields.Many2one('assets.form', string='Asset / Equipment Tag')

    # Linked Sources
    incident_id = fields.Many2one('incident.reporting', string='Associated Incident')
    investigation_id = fields.Many2one('incident.investigation', string='Associated Investigation')
    improvement_id = fields.Many2one('hse.improvement', string='Associated Improvement Project')

    # Production Downtime Loss Breakdown
    downtime_hours = fields.Float(string='Production Downtime (Hours)', default=0.0)
    production_volume_lost = fields.Float(string='Volume Lost (Bbl / MWh / MT)', default=0.0)
    production_unit = fields.Char(string='Unit of Measure', default='Barrels')
    loss_production_cost = fields.Float(string='Deferred Production Revenue Loss ($)', default=0.0, tracking=True)

    # Equipment & Asset Damage
    loss_equipment_repair = fields.Float(string='Direct Equipment Repair / Replacement Cost ($)', default=0.0)
    loss_contractor_services = fields.Float(string='Third-Party Specialist / Emergency Labor ($)', default=0.0)

    # Environmental & Regulatory Losses
    loss_environmental_cleanup = fields.Float(string='Spill Remediation & Waste Disposal ($)', default=0.0)
    loss_regulatory_fines = fields.Float(string='Statutory Agency Fines / Penalties ($)', default=0.0)

    # Health & Safety Costs
    loss_medical_compensation = fields.Float(string='Worker Compensation & Medical Claims ($)', default=0.0)
    loss_legal_fees = fields.Float(string='Legal & Litigation Expenses ($)', default=0.0)

    # Realized Benefits (For Benefit records)
    benefit_cost_avoidance = fields.Float(string='Avoided Downtime Savings ($)', default=0.0)
    benefit_energy_savings = fields.Float(string='Energy / Chemical Consumption Savings ($)', default=0.0)
    benefit_safety_roi = fields.Float(string='Reduced Insurance Premium / Risk Savings ($)', default=0.0)

    total_loss = fields.Float(string='Total Financial Loss ($)', compute='_compute_totals', store=True)
    total_benefit = fields.Float(string='Total Realized Benefit ($)', compute='_compute_totals', store=True)
    net_impact = fields.Float(string='Net Financial Balance ($)', compute='_compute_totals', store=True)

    notes = fields.Text(string='Accounting Justification & Cost Breakdown Notes')

    state = fields.Selection([
        ('draft', 'Draft Entry'),
        ('verified', 'Finance / Operations Verified'),
        ('closed', 'Financial Period Closed'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.benefit.loss') or _('FIN-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    @api.depends('loss_production_cost', 'loss_equipment_repair', 'loss_contractor_services',
                 'loss_environmental_cleanup', 'loss_regulatory_fines', 'loss_medical_compensation',
                 'loss_legal_fees', 'benefit_cost_avoidance', 'benefit_energy_savings', 'benefit_safety_roi')
    def _compute_totals(self):
        for rec in self:
            rec.total_loss = (
                rec.loss_production_cost +
                rec.loss_equipment_repair +
                rec.loss_contractor_services +
                rec.loss_environmental_cleanup +
                rec.loss_regulatory_fines +
                rec.loss_medical_compensation +
                rec.loss_legal_fees
            )
            rec.total_benefit = (
                rec.benefit_cost_avoidance +
                rec.benefit_energy_savings +
                rec.benefit_safety_roi
            )
            rec.net_impact = rec.total_benefit - rec.total_loss

    def action_verify(self):
        self.write({'state': 'verified'})

    def action_close(self):
        self.write({'state': 'closed'})
