# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HseLifeSavingRule(models.Model):
    _name = 'hse.lifesaving.rule'
    _description = 'IOGP Life-Saving Rules (Report 459)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc, name asc'

    name = fields.Char(string='Life-Saving Rule Name', required=True, tracking=True)
    code = fields.Char(string='Rule Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    rule_category = fields.Selection([
        ('bypass', 'Bypassing Safety Controls'),
        ('confined_space', 'Confined Space Entry'),
        ('driving', 'Driving Safety'),
        ('energy_isolation', 'Energy Isolation (LOTO)'),
        ('hot_work', 'Hot Work'),
        ('line_of_fire', 'Line of Fire'),
        ('safe_lifting', 'Safe Mechanical Lifting'),
        ('work_authorization', 'Work Authorization (PTW)'),
        ('working_at_height', 'Working at Heights'),
        ('other', 'Site-Specific Life-Saving Rule'),
    ], string='IOGP Rule Category', required=True, default='work_authorization')

    icon_fa = fields.Char(string='FontAwesome Icon', default='fa-shield')
    rule_description = fields.Text(string='Rule Intent & Scope', required=True)
    mandatory_expectations = fields.Text(string='Mandatory Worker & Supervisor Expectations', required=True)

    swa_count = fields.Integer(string='Stop Work Interventions', compute='_compute_stats')
    active = fields.Boolean(string='Active', default=True)

    swa_ids = fields.One2many('hse.stop.work', 'rule_id', string='Stop Work Events')

    @api.depends('swa_ids')
    def _compute_stats(self):
        for rec in self:
            rec.swa_count = len(rec.swa_ids)


class HseStopWork(models.Model):
    _name = 'hse.stop.work'
    _description = 'Stop Work Authority (SWA) Intervention Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'stop_datetime desc'

    name = fields.Char(string='SWA Event #', required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('hse.stop.work') or _('New'))
    stop_datetime = fields.Datetime(string='Stop Work Timestamp', default=fields.Datetime.now, required=True, tracking=True)
    intervenor_id = fields.Many2one('hr.employee', string='Intervening Worker', tracking=True)
    is_contractor = fields.Boolean(string='Contractor Personnel', default=False)
    contractor_name = fields.Char(string='Contractor Worker Name / ID')
    contractor_id = fields.Many2one('hse.contractor', string='Contractor Employer')

    location_id = fields.Many2one('hse.location.profile', string='Plant Unit / Location', required=True)
    permit_id = fields.Many2one('hse.permit', string='Active Permit to Work Stopped')
    rule_id = fields.Many2one('hse.lifesaving.rule', string='Related IOGP Life-Saving Rule', required=True)

    hazard_description = fields.Text(string='Unsafe Condition / Behavior Observed', required=True)
    perceived_risk_level = fields.Selection([
        ('low', 'Low - Minor Deviation'),
        ('medium', 'Medium - Potential Recordable Injury'),
        ('high', 'High - Potential Severe Injury / LTI'),
        ('imminent_danger', 'IMMINENT DANGER - Life-Threatening / Major Process Hazard'),
    ], string='Perceived Risk Severity', default='high', required=True, tracking=True)

    immediate_action_taken = fields.Text(string='Immediate Action Taken', required=True,
                                        default='Work ceased immediately; personnel removed to safe area; supervisor notified.')
    supervisor_id = fields.Many2one('hr.employee', string='Area Supervisor / Shift Lead', required=True)
    resolution_details = fields.Text(string='Corrective Hazard Rectification', required=True)

    resumption_authorized = fields.Boolean(string='Safe Resumption Authorized', default=False, tracking=True)
    resumption_authorizer_id = fields.Many2one('hr.employee', string='Authorized By')

    positive_recognition = fields.Boolean(string='Commended for Proactive Safety Intervention', default=True)
    recognition_notes = fields.Text(string='Leadership Commendation / Award Details',
                                   default='Intervenor recognized at morning safety briefing for exemplifying Stop Work Authority.')

    state = fields.Selection([
        ('stopped', 'Work Ceased (Active SWA)'),
        ('mitigating', 'Hazard Rectification in Progress'),
        ('resumed', 'Work Safely Resumed'),
        ('commended', 'Recognized & Closed'),
    ], string='SWA Lifecycle', default='stopped', tracking=True)

    def action_start_mitigation(self):
        self.write({'state': 'mitigating'})

    def action_authorize_resumption(self):
        self.write({
            'resumption_authorized': True,
            'resumption_authorizer_id': self.env.user.employee_id.id or self.supervisor_id.id,
            'state': 'resumed'
        })

    def action_commend_and_close(self):
        self.write({'state': 'commended'})
