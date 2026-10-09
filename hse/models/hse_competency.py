# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta

class HSECompetency(models.Model):
    _name = 'hse.competency'
    _description = 'HSE Safety Competency Definition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code asc, name asc'

    name = fields.Char(string='Competency Title', required=True, tracking=True)
    code = fields.Char(string='Competency Code (e.g. CMP-AGT-01)', required=True, tracking=True)
    category = fields.Selection([
        ('control_of_work', 'Control of Work (PTW / Isolation)'),
        ('gas_testing', 'Atmospheric Gas Testing'),
        ('emergency_response', 'Emergency Response & Rescue'),
        ('hazard_control', 'Hazard Identification & Risk Assessment'),
        ('lifting_rigging', 'Lifting Operations & Rigging'),
        ('process_operations', 'Process Plant Operations & Interlocks'),
        ('environmental', 'Spill Control & Environmental Protection'),
    ], string='Competency Domain', default='control_of_work', required=True)

    description = fields.Text(string='Competency Description & Standard', required=True)
    validity_months = fields.Integer(string='Re-assessment Frequency (Months)', default=24)
    mandatory_for_permits = fields.Boolean(string='Required for Permit to Work Authorization', default=False)

    assessment_ids = fields.One2many('hse.employee.competency', 'competency_id', string='Employee Qualifications')
    matrix_line_ids = fields.One2many('hse.training.matrix.line', 'competency_id', string='Training Matrix Lines')


class HSERoleCompetency(models.Model):
    _name = 'hse.role.competency'
    _description = 'Job Role Mandatory Competency Matrix'

    job_id = fields.Many2one('hr.job', string='Job Position / Craft', required=True)
    competency_id = fields.Many2one('hse.competency', string='Required Competency', required=True)
    minimum_level = fields.Selection([
        ('level1', 'Level 1: Awareness & Basic Knowledge'),
        ('level2', 'Level 2: Supervised Execution'),
        ('level3', 'Level 3: Fully Autonomous / Authorized'),
        ('level4', 'Level 4: Master / Qualified Assessor'),
    ], string='Minimum Required Proficiency', default='level3', required=True)
    is_mandatory = fields.Boolean(string='Strict Prerequisite for Duty', default=True)


class HSEEmployeeCompetency(models.Model):
    _name = 'hse.employee.competency'
    _description = 'Employee Competency Qualification Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc, id desc'

    employee_id = fields.Many2one('hr.employee', string='Qualified Employee', required=True)
    competency_id = fields.Many2one('hse.competency', string='Assessed Competency', required=True)
    proficiency_level = fields.Selection([
        ('level1', 'Level 1: Awareness & Basic Knowledge'),
        ('level2', 'Level 2: Supervised Execution'),
        ('level3', 'Level 3: Autonomous / Authorized'),
        ('level4', 'Level 4: Master / Assessor'),
    ], string='Assessed Proficiency', default='level3', required=True, tracking=True)

    assessment_date = fields.Date(string='Assessment Date', default=fields.Date.today, required=True)
    expiry_date = fields.Date(string='Qualification Expiration Date', required=True)
    assessor_id = fields.Many2one('res.users', string='Certified Assessor', required=True, default=lambda self: self.env.user)
    evidence_notes = fields.Text(string='Assessment Evidence / Practical Exam Notes')

    is_expired = fields.Boolean(string='Qualification Expired', compute='_compute_expired', store=True)

    state = fields.Selection([
        ('active', 'Certified & Active'),
        ('under_reassessment', 'Re-Assessment Due'),
        ('expired', 'Expired / Suspended'),
    ], string='Status', default='active', tracking=True)

    @api.depends('expiry_date')
    def _compute_expired(self):
        today = date.today()
        for rec in self:
            rec.is_expired = bool(rec.expiry_date and rec.expiry_date < today)
            if rec.is_expired:
                rec.state = 'expired'


class HSETrainingMatrix(models.Model):
    _name = 'hse.training.matrix'
    _description = 'HSE Training Matrix & Competency Gap Analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'evaluation_date desc, id desc'

    name = fields.Char(string='Matrix Assessment Title', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Target Department (Optional)')
    job_ids = fields.Many2many('hr.job', string='Target Job Roles / Crafts')
    evaluation_date = fields.Date(string='Assessment Date', default=fields.Date.today, required=True)
    evaluated_by = fields.Many2one('res.users', string='Evaluated By', default=lambda self: self.env.user, required=True)

    line_ids = fields.One2many('hse.training.matrix.line', 'matrix_id', string='Competency Gap Lines')

    total_evaluated = fields.Integer(string='Total Competencies Evaluated', compute='_compute_matrix_kpis', store=True)
    compliant_count = fields.Integer(string='Compliant Records', compute='_compute_matrix_kpis', store=True)
    expiring_count = fields.Integer(string='Expiring Soon', compute='_compute_matrix_kpis', store=True)
    gap_count = fields.Integer(string='Missing / Expired Gaps', compute='_compute_matrix_kpis', store=True)
    compliance_rate = fields.Float(string='Compliance Score (%)', compute='_compute_matrix_kpis', store=True)

    state = fields.Selection([
        ('draft', 'Draft Matrix'),
        ('calculated', 'Gaps Evaluated'),
        ('actions_generated', 'Remediation Actions Created'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('line_ids', 'line_ids.status')
    def _compute_matrix_kpis(self):
        for rec in self:
            total = len(rec.line_ids)
            compliant = len(rec.line_ids.filtered(lambda l: l.status == 'compliant'))
            expiring = len(rec.line_ids.filtered(lambda l: l.status == 'expiring_soon'))
            gaps = len(rec.line_ids.filtered(lambda l: l.status in ['expired', 'missing']))
            rec.total_evaluated = total
            rec.compliant_count = compliant
            rec.expiring_count = expiring
            rec.gap_count = gaps
            rec.compliance_rate = round((compliant / total * 100.0), 1) if total > 0 else 0.0

    def action_evaluate_matrix(self):
        """Evaluate all employees against role competency requirements."""
        self.ensure_one()
        domain = []
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.job_ids:
            domain.append(('job_id', 'in', self.job_ids.ids))
        employees = self.env['hr.employee'].search(domain)

        # Clear existing lines
        self.line_ids.unlink()

        today = fields.Date.today()
        soon = today + timedelta(days=60)
        new_lines = []

        for emp in employees:
            if not emp.job_id:
                continue
            role_competencies = self.env['hse.role.competency'].search([('job_id', '=', emp.job_id.id)])
            for rc in role_competencies:
                emp_comp = self.env['hse.employee.competency'].search([
                    ('employee_id', '=', emp.id),
                    ('competency_id', '=', rc.competency_id.id),
                ], order='expiry_date desc', limit=1)

                if not emp_comp:
                    status = 'missing'
                    exp_date = False
                    prof = 'none'
                elif emp_comp.expiry_date and emp_comp.expiry_date < today:
                    status = 'expired'
                    exp_date = emp_comp.expiry_date
                    prof = emp_comp.proficiency_level
                elif emp_comp.expiry_date and emp_comp.expiry_date <= soon:
                    status = 'expiring_soon'
                    exp_date = emp_comp.expiry_date
                    prof = emp_comp.proficiency_level
                else:
                    status = 'compliant'
                    exp_date = emp_comp.expiry_date
                    prof = emp_comp.proficiency_level

                new_lines.append((0, 0, {
                    'employee_id': emp.id,
                    'job_id': emp.job_id.id,
                    'competency_id': rc.competency_id.id,
                    'required_level': rc.minimum_level,
                    'current_level': prof,
                    'expiry_date': exp_date,
                    'status': status,
                    'is_mandatory': rc.is_mandatory,
                }))

        self.write({
            'line_ids': new_lines,
            'state': 'calculated',
        })
        return True

    def action_generate_training_actions(self):
        """Generate remediation actions for non-compliant gaps."""
        self.ensure_one()
        Action = self.env['hse.action']
        gap_lines = self.line_ids.filtered(lambda l: l.status in ['missing', 'expired'])
        for line in gap_lines:
            Action.create({
                'title': f"Training Gap: {line.employee_id.name} - {line.competency_id.name}",
                'action_type': 'corrective',
                'priority': '3' if line.is_mandatory else '2',
                'target_date': fields.Date.today() + timedelta(days=30),
                'assigned_to': self.evaluated_by.id,
                'description': f"Mandatory safety competency gap identified in Training Matrix '{self.name}'. Employee {line.employee_id.name} ({line.job_id.name if line.job_id else 'N/A'}) requires certification in {line.competency_id.name} (Required Level: {line.required_level}).",
            })
        self.write({'state': 'actions_generated'})
        return True


class HSETrainingMatrixLine(models.Model):
    _name = 'hse.training.matrix.line'
    _description = 'HSE Training Matrix Line Detail'
    _order = 'status asc, employee_id asc'

    matrix_id = fields.Many2one('hse.training.matrix', string='Matrix', ondelete='cascade', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    job_id = fields.Many2one('hr.job', string='Job Role')
    competency_id = fields.Many2one('hse.competency', string='Safety Competency', required=True)
    required_level = fields.Selection([
        ('level1', 'Level 1: Awareness & Basic Knowledge'),
        ('level2', 'Level 2: Supervised Execution'),
        ('level3', 'Level 3: Fully Autonomous / Authorized'),
        ('level4', 'Level 4: Master / Qualified Assessor'),
    ], string='Required Proficiency', default='level3')
    current_level = fields.Selection([
        ('none', 'Not Qualified / No Record'),
        ('level1', 'Level 1: Awareness & Basic Knowledge'),
        ('level2', 'Level 2: Supervised Execution'),
        ('level3', 'Level 3: Fully Autonomous / Authorized'),
        ('level4', 'Level 4: Master / Qualified Assessor'),
    ], string='Current Proficiency', default='none')
    expiry_date = fields.Date(string='Current Expiry Date')
    status = fields.Selection([
        ('compliant', 'Fully Compliant'),
        ('expiring_soon', 'Expiring Within 60 Days'),
        ('expired', 'Expired (Non-Compliant)'),
        ('missing', 'Missing Qualification (Gap)'),
    ], string='Compliance Status', default='missing', required=True)
    is_mandatory = fields.Boolean(string='Mandatory Prerequisite', default=True)
