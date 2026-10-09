# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class HSEAction(models.Model):
    _name = 'hse.action'
    _description = 'HSE Corrective & Preventive Action (CAPA)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, target_date asc, id desc'

    name = fields.Char(string='Action Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Action Title', required=True, tracking=True)
    description = fields.Text(string='Detailed Action Description', required=True)
    action_type = fields.Selection([
        ('corrective', 'Corrective Action (CAPA)'),
        ('preventive', 'Preventive Action (PAPA)'),
        ('containment', 'Immediate Containment / Interim Measure'),
        ('improvement', 'Continuous Improvement Action'),
    ], string='Action Type', default='corrective', required=True, tracking=True)

    source_type = fields.Selection([
        ('incident', 'Incident'),
        ('investigation', 'Investigation RCA'),
        ('moc', 'Management of Change'),
        ('audit', 'Regulatory / Compliance Audit'),
        ('ncr', 'Non-Conformance (NCR)'),
        ('risk_assessment', 'Risk Assessment / JSA'),
        ('defect', 'Defect Elimination'),
        ('bypass', 'Bypass Review'),
        ('observation', 'Safety Observation'),
        ('other', 'Other Source'),
    ], string='Source Module', default='incident', required=True, tracking=True)

    source_reference = fields.Char(string='Source Record Ref')
    incident_id = fields.Many2one('incident.reporting', string='Linked Incident', ondelete='set null')
    investigation_id = fields.Many2one('incident.investigation', string='Linked Investigation', ondelete='set null')
    moc_id = fields.Many2one('hse.moc', string='Linked MOC', ondelete='set null')
    risk_assessment_id = fields.Many2one('ra_jsa.model', string='Linked Risk Assessment', ondelete='set null')
    observation_id = fields.Many2one('observation.observation', string='Linked Observation', ondelete='set null')

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical / Urgent'),
    ], string='Priority', default='1', tracking=True)

    assigned_to = fields.Many2one('res.users', string='Assignee / Owner', required=True, default=lambda self: self.env.user, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department')
    target_date = fields.Date(string='Target Due Date', required=True, tracking=True)
    completion_date = fields.Date(string='Actual Completion Date', tracking=True)
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_overdue', store=True)

    progress = fields.Integer(string='Progress (%)', default=0, tracking=True)
    implementation_notes = fields.Text(string='Implementation Notes & Evidence')

    # Verification / Effectiveness
    requires_verification = fields.Boolean(string='Effectiveness Review Required', default=True)
    verifier_id = fields.Many2one('res.users', string='Effectiveness Verifier')
    verification_date = fields.Date(string='Verification Date')
    verification_status = fields.Selection([
        ('pending', 'Pending Verification'),
        ('effective', 'Effective - Cause Eliminated'),
        ('ineffective', 'Ineffective - Recurrence Possible'),
    ], string='Effectiveness Status', default='pending', tracking=True)
    verification_notes = fields.Text(string='Verification Findings')

    # Extension requests
    extension_reason = fields.Text(string='Due Date Extension Reason')
    original_target_date = fields.Date(string='Original Target Date')
    extension_approved_by = fields.Many2one('res.users', string='Extension Approved By')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('implemented', 'Implemented / Pending Verification'),
        ('verified', 'Verified Effective & Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.action') or _('ACT-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
            if 'target_date' in vals and not vals.get('original_target_date'):
                vals['original_target_date'] = vals['target_date']
        return super().create(vals_list)

    @api.depends('target_date', 'state', 'completion_date')
    def _compute_overdue(self):
        today = date.today()
        for rec in self:
            if rec.state not in ('verified', 'cancelled') and rec.target_date and rec.target_date < today:
                rec.is_overdue = True
            else:
                rec.is_overdue = False

    def action_assign(self):
        self.write({'state': 'assigned'})

    def action_start(self):
        self.write({'state': 'in_progress', 'progress': max(self.progress, 15)})

    def action_implement(self):
        self.write({
            'state': 'implemented',
            'progress': 100,
            'completion_date': date.today(),
        })

    def action_verify(self):
        self.write({
            'state': 'verified',
            'verification_date': date.today(),
            'verification_status': 'effective',
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})
