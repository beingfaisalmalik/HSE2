# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEAudit(models.Model):
    _name = 'hse.audit'
    _description = 'HSE Management System & Process Safety Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, id desc'

    name = fields.Char(string='Audit Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Audit Title & Scope', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Audited Facility / Operating Plant', required=True)
    lead_auditor_id = fields.Many2one('res.users', string='Lead Auditor', required=True, default=lambda self: self.env.user)
    audit_team = fields.Text(string='Audit Team Members & Subject Matter Experts', required=True)
    audit_date = fields.Date(string='Audit Start Date', default=fields.Date.today, required=True)
    target_end_date = fields.Date(string='Audit Close Date', required=True)

    protocol = fields.Selection([
        ('iso45001', 'ISO 45001:2018 Occupational Health & Safety Management System'),
        ('iso14001', 'ISO 14001:2015 Environmental Management System'),
        ('osha_psm', 'OSHA 1910.119 Process Safety Management (14 Elements)'),
        ('api_rp_75', 'API RP 75 Safety and Environmental Management Systems (SEMS)'),
        ('responsible_care', 'Responsible Care Management System (RCMS)'),
        ('internal_compliance', 'Corporate Annual Internal HSE Compliance Audit'),
    ], string='Audit Standard / Protocol', default='osha_psm', required=True, tracking=True)

    audit_summary = fields.Text(string='Executive Audit Summary & Overall Assessment')
    checklist_ids = fields.One2many('hse.audit.checklist', 'audit_id', string='Checklist Findings & Inquiries')

    total_checks = fields.Integer(string='Total Criteria Audited', compute='_compute_findings', store=True)
    compliant_count = fields.Integer(string='Compliant Items', compute='_compute_findings', store=True)
    critical_deficiency_count = fields.Integer(string='Critical Deficiencies', compute='_compute_findings', store=True)
    major_nc_count = fields.Integer(string='Major Non-Conformances', compute='_compute_findings', store=True)
    minor_nc_count = fields.Integer(string='Minor Non-Conformances', compute='_compute_findings', store=True)
    compliance_score_percent = fields.Float(string='Audit Compliance Score (%)', compute='_compute_findings', store=True)

    state = fields.Selection([
        ('planned', 'Audit Scheduled'),
        ('fieldwork', 'On-Site Fieldwork & Interviews'),
        ('reporting', 'Draft Report & Findings Review'),
        ('approved', 'Audit Formally Endorsed'),
        ('capa_tracking', 'CAPA Action Closure in Progress'),
        ('closed', 'All Non-Conformances Rectified & Closed'),
    ], string='Status', default='planned', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.audit') or _('AUD-%04d') % self.env['hse.audit'].search_count([])
        return super().create(vals_list)

    @api.depends('checklist_ids', 'checklist_ids.finding_type')
    def _compute_findings(self):
        for rec in self:
            total = len(rec.checklist_ids)
            rec.total_checks = total
            rec.compliant_count = len(rec.checklist_ids.filtered(lambda c: c.finding_type == 'compliant'))
            rec.critical_deficiency_count = len(rec.checklist_ids.filtered(lambda c: c.finding_type == 'critical'))
            rec.major_nc_count = len(rec.checklist_ids.filtered(lambda c: c.finding_type == 'major_nc'))
            rec.minor_nc_count = len(rec.checklist_ids.filtered(lambda c: c.finding_type == 'minor_nc'))
            if total > 0:
                rec.compliance_score_percent = round((rec.compliant_count / total) * 100.0, 1)
            else:
                rec.compliance_score_percent = 100.0

    def action_start_fieldwork(self):
        self.write({'state': 'fieldwork'})

    def action_submit_reporting(self):
        self.write({'state': 'reporting'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_close(self):
        self.write({'state': 'closed'})


class HSEAuditChecklist(models.Model):
    _name = 'hse.audit.checklist'
    _description = 'Audit Protocol Checklist Line & Finding'
    _order = 'sequence asc, id asc'

    audit_id = fields.Many2one('hse.audit', string='Audit', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Seq', default=10)
    requirement_clause = fields.Char(string='Standard Clause / Requirement (e.g. 1910.119(e) Process Hazard Analysis)', required=True)
    verification_criteria = fields.Text(string='Audit Verification Question & Objective Evidence Criteria', required=True)

    finding_type = fields.Selection([
        ('compliant', 'Compliant (Effective Implementation Verified)'),
        ('opportunity', 'Opportunity for Improvement (OFI)'),
        ('minor_nc', 'Minor Non-Conformance'),
        ('major_nc', 'Major Non-Conformance'),
        ('critical', 'Critical Process Safety Deficiency'),
    ], string='Audit Finding', required=True, default='compliant')

    evidence_notes = fields.Text(string='Objective Evidence Inspected (Records, Interviews, Field Observation)')
    capa_action_id = fields.Many2one('hse.action', string='Generated CAPA Action')
