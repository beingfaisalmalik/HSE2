# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta

class HSERegulation(models.Model):
    _name = 'hse.regulation'
    _description = 'HSE Regulation & Compliance Standard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code asc, id desc'

    name = fields.Char(string='Regulation Title', required=True, tracking=True)
    code = fields.Char(string='Regulation / Standard Code (e.g. OSHA 1910, ISO 45001)', required=True, tracking=True)
    regulatory_body = fields.Char(string='Issuing Authority / Agency (OSHA, EPA, ISO, BSEE, API)', required=True)
    jurisdiction = fields.Char(string='Jurisdiction / Region (Federal, State, International)')

    category = fields.Selection([
        ('occupational_safety', 'Occupational Safety & Health'),
        ('process_safety', 'Process Safety Management (PSM)'),
        ('environmental', 'Environmental Protection & Emissions'),
        ('energy_isolation', 'Energy Isolation (LOTO)'),
        ('marine_offshore', 'Marine & Offshore Maritime Safety'),
        ('quality', 'Quality & Asset Integrity Standards'),
    ], string='Regulatory Domain', default='occupational_safety', required=True)

    revision_number = fields.Char(string='Current Revision', default='Rev 1.0', tracking=True)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today)
    technical_authority_id = fields.Many2one('res.users', string='Technical Authority Lead', required=True, default=lambda self: self.env.user)

    summary = fields.Text(string='Executive Summary & Purpose')
    full_text_url = fields.Char(string='Official Regulation URL / Portal Link')

    # Specific Obligations
    obligation_ids = fields.One2many('hse.compliance.obligation', 'regulation_id', string='Compliance Obligations')
    audit_ids = fields.One2many('hse.compliance.audit', 'regulation_id', string='Compliance Audits & Assessments')
    task_ids = fields.One2many('hse.compliance.task', 'regulation_id', string='Compliance Obligations Calendar')
    task_count = fields.Integer(string='Task Count', compute='_compute_task_count')

    state = fields.Selection([
        ('active', 'Active & Enforced'),
        ('under_review', 'Revision Under Review'),
        ('superseded', 'Superseded / Retired'),
    ], string='Status', default='active', tracking=True)

    def _compute_task_count(self):
        for rec in self:
            rec.task_count = len(rec.task_ids)


class HSEComplianceObligation(models.Model):
    _name = 'hse.compliance.obligation'
    _description = 'Regulatory Compliance Obligation Clause'
    _order = 'clause_code asc, id asc'

    regulation_id = fields.Many2one('hse.regulation', string='Regulation', ondelete='cascade', required=True)
    clause_code = fields.Char(string='Clause / Section Ref (e.g. 1910.119(e))', required=True)
    name = fields.Char(string='Requirement Summary', required=True)
    mandatory_rule = fields.Text(string='Full Legal Mandate Description')
    monitoring_frequency = fields.Selection([
        ('continuous', 'Continuous Operations Monitoring'),
        ('monthly', 'Monthly Review'),
        ('quarterly', 'Quarterly Compliance Check'),
        ('annual', 'Annual Formal Audit'),
    ], string='Verification Frequency', default='annual')

    compliance_status = fields.Selection([
        ('compliant', 'Fully Compliant'),
        ('partial', 'Partially Compliant (Action Required)'),
        ('non_compliant', 'Non-Compliant (High Legal Risk)'),
        ('not_applicable', 'Not Applicable to this Site'),
    ], string='Site Compliance Status', default='compliant')
    responsible_id = fields.Many2one('res.users', string='Responsible Compliance Specialist')


class HSEComplianceAudit(models.Model):
    _name = 'hse.compliance.audit'
    _description = 'HSE Compliance Audit & Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, id desc'

    name = fields.Char(string='Audit Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Audit Title', required=True, tracking=True)
    regulation_id = fields.Many2one('hse.regulation', string='Governing Regulation / Standard', required=True)
    location_id = fields.Many2one('hse.location.profile', string='Audited Plant Area', required=True)
    lead_auditor_id = fields.Many2one('res.users', string='Lead Auditor', required=True, default=lambda self: self.env.user)
    audit_date = fields.Date(string='Audit Execution Date', default=fields.Date.today, required=True)

    # Scoring & Results
    score_percentage = fields.Float(string='Compliance Score (%)', default=100.0, tracking=True)
    findings_count = fields.Integer(string='Total Discrepancies / Non-Compliances Found', default=0)
    findings_summary = fields.Text(string='Audit Findings & Observations')

    # Status
    state = fields.Selection([
        ('scheduled', 'Audit Scheduled'),
        ('in_progress', 'Audit In Progress'),
        ('completed', 'Audit Completed'),
        ('action_tracking', 'Remediation Actions Open'),
        ('closed', 'All Findings Resolved & Closed'),
    ], string='Audit Status', default='scheduled', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.compliance.audit') or _('AUD-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_close(self):
        self.write({'state': 'closed'})


class HSEComplianceTask(models.Model):
    _name = 'hse.compliance.task'
    _description = 'Statutory Compliance Obligation Task & Regulatory Filing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date asc, id desc'

    name = fields.Char(string='Compliance Obligation / Statutory Filing', required=True, tracking=True)
    task_ref = fields.Char(string='Filing Reference', copy=False, readonly=True, default=lambda self: _('New'))
    regulation_id = fields.Many2one('hse.regulation', string='Governing Regulation', tracking=True)
    obligation_id = fields.Many2one('hse.compliance.obligation', string='Specific Clause / Obligation', domain="[('regulation_id', '=', regulation_id)]")
    regulatory_body = fields.Char(string='Regulatory Body / Authority (e.g. OSHA, EPA, ISO, BSEE, DOT)', required=True, default='OSHA')
    location_id = fields.Many2one('hse.location.profile', string='Regulated Plant Location')

    task_type = fields.Selection([
        ('statutory_filing', 'Statutory Agency Filing / Mandated Report'),
        ('permit_renewal', 'Operating Permit / Environmental License Renewal'),
        ('mandatory_inspection', 'Statutory Third-Party Inspection / Certification'),
        ('emission_reporting', 'Air / Water Emissions Periodic Compliance'),
        ('regulatory_drill', 'Mandatory Regulatory Drill / Exercise'),
        ('internal_audit', 'Mandatory Compliance Verification Audit'),
    ], string='Obligation Type', default='statutory_filing', required=True, tracking=True)

    frequency = fields.Selection([
        ('one_off', 'One-Time Regulatory Event'),
        ('monthly', 'Monthly Statutory Obligation'),
        ('quarterly', 'Quarterly Legal Submission'),
        ('semiannual', 'Semi-Annual Statutory Certificate'),
        ('annual', 'Annual Formal Regulatory Filing'),
    ], string='Recurrence Frequency', default='annual', required=True)

    due_date = fields.Date(string='Statutory Due Date', required=True, tracking=True, default=fields.Date.today)
    lead_time_days = fields.Integer(string='Alert Lead Time (Days)', default=30)
    alert_date = fields.Date(string='Target Warning Date', compute='_compute_alert_date', store=True)

    responsible_id = fields.Many2one('res.users', string='Assigned Compliance Specialist', required=True, default=lambda self: self.env.user, tracking=True)
    approver_id = fields.Many2one('res.users', string='Authorizing Official / Signatory')

    state = fields.Selection([
        ('draft', 'Draft / Planned'),
        ('scheduled', 'Scheduled & Monitored'),
        ('in_progress', 'Filing Preparation Underway'),
        ('submitted', 'Submitted to Authority'),
        ('completed', 'Verified Compliant & Accepted'),
    ], string='Compliance State', default='scheduled', tracking=True)

    is_overdue = fields.Boolean(string='Overdue Past Legal Deadline', compute='_compute_is_overdue', store=True)
    submission_date = fields.Date(string='Actual Submission Date', tracking=True)
    agency_ack_number = fields.Char(string='Agency Receipt / Confirmation / Case #', tracking=True)
    compliance_notes = fields.Text(string='Compliance Details & Filing Evidence')
    compliance_evidence = fields.Binary(string='Agency Stamped Return / Cert PDF', attachment=True)
    evidence_filename = fields.Char(string='Evidence Filename')

    @api.depends('due_date', 'lead_time_days')
    def _compute_alert_date(self):
        for rec in self:
            if rec.due_date and rec.lead_time_days:
                rec.alert_date = rec.due_date - timedelta(days=rec.lead_time_days)
            else:
                rec.alert_date = rec.due_date

    @api.depends('due_date', 'state', 'submission_date')
    def _compute_is_overdue(self):
        today = date.today()
        for rec in self:
            if rec.state not in ['submitted', 'completed'] and rec.due_date and rec.due_date < today:
                rec.is_overdue = True
            else:
                rec.is_overdue = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('task_ref', _('New')) == _('New'):
                vals['task_ref'] = self.env['ir.sequence'].next_by_code('hse.compliance.task') or _('COMP-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_submit(self):
        self.write({'state': 'submitted', 'submission_date': fields.Date.today()})

    def action_verify(self):
        self.write({'state': 'completed'})

    def action_set_scheduled(self):
        self.write({'state': 'scheduled'})
