# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEOperatingPolicy(models.Model):
    _name = 'hse.operating.policy'
    _description = 'HSE Operating Policy & Governance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'policy_code asc, id desc'

    name = fields.Char(string='Policy Title', required=True, tracking=True)
    policy_code = fields.Char(string='Policy Code (e.g. POL-HSE-001)', required=True, tracking=True)
    policy_type = fields.Selection([
        ('safety', 'Occupational Health & Safety Policy'),
        ('life_saving', 'Golden Life-Saving Rules'),
        ('stop_work', 'Stop Work Authority (SWA) Policy'),
        ('environmental', 'Environmental Stewardship & Sustainability Policy'),
        ('asset_integrity', 'Process Safety & Asset Integrity Policy'),
        ('drug_alcohol', 'Fitness for Duty / Substance Abuse Policy'),
    ], string='Policy Classification', default='safety', required=True, tracking=True)

    iso_alignment = fields.Char(string='Aligned International Standards', default='ISO 45001:2018 / ISO 14001:2015')
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today, required=True)
    review_frequency_years = fields.Integer(string='Review Frequency (Years)', default=2)

    policy_statement = fields.Html(string='Executive Policy Statement', required=True)
    core_principles = fields.Text(string='Core Principles & Commitments', required=True)
    mandatory_rules = fields.Text(string='Mandatory Rules for All Personnel', required=True)

    policy_owner_id = fields.Many2one('res.users', string='Executive Policy Owner', required=True, default=lambda self: self.env.user)
    approved_by_id = fields.Many2one('res.users', string='Managing Director / CEO Approver')

    # Workforce Acknowledgment Tracking
    acknowledgment_ids = fields.One2many('hse.policy.acknowledgment', 'policy_id', string='Employee Acknowledgments')
    total_acknowledgments = fields.Integer(string='Total Signed Acknowledgments', compute='_compute_ack_count')

    state = fields.Selection([
        ('draft', 'Drafting'),
        ('approved', 'Executive Approved & Effective'),
        ('retired', 'Retired / Superseded'),
    ], string='Governance State', default='draft', tracking=True)

    def _compute_ack_count(self):
        for rec in self:
            rec.total_acknowledgments = len(rec.acknowledgment_ids)

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id
        })

    def action_retire(self):
        self.write({'state': 'retired'})


class HSEPolicyAcknowledgment(models.Model):
    _name = 'hse.policy.acknowledgment'
    _description = 'Workforce Policy Acknowledgment Record'
    _order = 'ack_date desc, id desc'

    policy_id = fields.Many2one('hse.operating.policy', string='Governing Policy', ondelete='cascade', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee / Worker', required=True)
    ack_date = fields.Datetime(string='Signed Timestamp', default=fields.Datetime.now, required=True)
    digital_signature = fields.Char(string='Digital Acknowledgment Signature Token')
    confirmed = fields.Boolean(string='I have read, understood, and agreed to adhere to this policy', default=True)
