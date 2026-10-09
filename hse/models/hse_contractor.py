# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEContractor(models.Model):
    _name = 'hse.contractor'
    _description = 'Contractor HSE Prequalification & Performance Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Contractor Company Name', required=True, tracking=True)
    vendor_id = fields.Many2one('res.partner', string='Partner / Vendor Record')
    trade_category = fields.Selection([
        ('mechanical', 'Mechanical, Piping & Welding'),
        ('electrical', 'Electrical & Instrumentation'),
        ('civil', 'Civil & Structural'),
        ('scaffolding', 'Scaffolding & Rigging Services'),
        ('insulation', 'Thermal Insulation & Painting'),
        ('tank_cleaning', 'Hazardous Tank Cleaning & Industrial Hydrojetting'),
        ('ndt', 'Non-Destructive Testing & Inspection'),
        ('logistics', 'Crane & Heavy Haulage Logistics'),
    ], string='Primary Specialty Trade', required=True, default='mechanical')

    # Safety Prequalification Metrics
    emr_rate = fields.Float(string='Experience Modification Rate (EMR)', default=0.85, required=True, help="EMR <= 1.0 indicates better than average safety performance.")
    trir_3year_avg = fields.Float(string='3-Year Average TRIR', default=0.75, required=True)
    fatalities_last_5years = fields.Integer(string='Fatalities (Last 5 Years)', default=0, required=True)
    osha_citations_count = fields.Integer(string='OSHA Citations (Last 3 Years)', default=0)

    # Compliance & Insurance
    insurance_policy_number = fields.Char(string='Commercial General Liability Policy #', required=True)
    insurance_expiry_date = fields.Date(string='Insurance Certificate Expiration Date', required=True, tracking=True)
    insurance_coverage_amount = fields.Float(string='Insurance Liability Limit ($)', default=10000000.0)
    safety_manual_approved = fields.Boolean(string='Contractor HSE Safety Manual Formally Approved', default=False)

    # Grade
    safety_grade = fields.Selection([
        ('grade_a', 'Grade A: Approved for High-Risk Process Work'),
        ('grade_b', 'Grade B: Approved for General Industrial Work'),
        ('conditional', 'Conditional: Requires Continuous HSE Supervision'),
        ('disqualified', 'Disqualified: Safety Criteria Not Met'),
    ], string='Contractor Safety Qualification Grade', compute='_compute_safety_grade', store=True)

    worker_count = fields.Integer(string='Inducted Active Workers', compute='_compute_worker_count', store=True)
    induction_ids = fields.One2many('hse.contractor.induction', 'contractor_id', string='Worker Inductions')
    kpi_ids = fields.One2many('hse.contractor.kpi', 'contractor_id', string='Monthly Performance Logs')

    @api.depends('emr_rate', 'trir_3year_avg', 'fatalities_last_5years', 'safety_manual_approved')
    def _compute_safety_grade(self):
        for rec in self:
            if rec.fatalities_last_5years > 0 or rec.emr_rate > 1.2:
                rec.safety_grade = 'disqualified'
            elif rec.emr_rate <= 0.9 and rec.trir_3year_avg <= 1.0 and rec.safety_manual_approved:
                rec.safety_grade = 'grade_a'
            elif rec.emr_rate <= 1.0:
                rec.safety_grade = 'grade_b'
            else:
                rec.safety_grade = 'conditional'

    @api.depends('induction_ids', 'induction_ids.state')
    def _compute_worker_count(self):
        for rec in self:
            rec.worker_count = len(rec.induction_ids.filtered(lambda i: i.state == 'active'))


class HSEContractorInduction(models.Model):
    _name = 'hse.contractor.induction'
    _description = 'Contractor Personnel Site Safety Induction & Gate Pass'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'induction_date desc, id desc'

    name = fields.Char(string='Gate Pass / Badge #', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    contractor_id = fields.Many2one('hse.contractor', string='Employer Contractor', required=True)
    worker_name = fields.Char(string='Worker Full Name', required=True)
    national_id_passport = fields.Char(string='National ID / Passport #', required=True)
    job_title = fields.Char(string='Craft / Job Role (e.g. Certified Welder 6G, Rigger Level III)', required=True)

    induction_date = fields.Date(string='Induction Date', default=fields.Date.today, required=True)
    expiry_date = fields.Date(string='Induction Expiry Date', required=True)
    trainer_id = fields.Many2one('res.users', string='HSE Induction Instructor', default=lambda self: self.env.user)

    # Verification Checks
    drug_alcohol_test_verified = fields.Boolean(string='Negative 10-Panel Drug & Alcohol Screen Verified', default=True)
    trade_certificates_verified = fields.Boolean(string='Trade Qualifications & Licenses Verified', default=True)
    site_rules_acknowledged = fields.Boolean(string='Golden Safety Rules Acknowledged & Signed', default=True)
    ppe_issued_verified = fields.Boolean(string='Mandatory PPE Inspected (FRC, Hardhat, Safety Glasses, Boots)', default=True)

    state = fields.Selection([
        ('draft', 'Registered'),
        ('active', 'Inducted & Gate Pass Active'),
        ('expired', 'Induction Expired (Re-orientation Required)'),
        ('revoked', 'Gate Pass Revoked (Safety Violation)'),
    ], string='Badge Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.contractor.induction') or _('BADGE-%05d') % self.env['hse.contractor.induction'].search_count([])
        return super().create(vals_list)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_revoke(self):
        self.write({'state': 'revoked'})


class HSEContractorKpi(models.Model):
    _name = 'hse.contractor.kpi'
    _description = 'Contractor Monthly HSE Performance Metric Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, month desc, id desc'

    contractor_id = fields.Many2one('hse.contractor', string='Contractor', required=True)
    year = fields.Integer(string='Year', default=lambda self: fields.Date.context_today(self).year, required=True)
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True, default=lambda self: str(fields.Date.context_today(self).month))

    man_hours_worked = fields.Float(string='Total Man-Hours Worked', required=True, default=5000.0)
    toolbox_talks_conducted = fields.Integer(string='Toolbox Talks Conducted', default=25)
    safety_inspections_count = fields.Integer(string='Internal Safety Audits Conducted', default=4)

    # Lagging Events
    near_misses_count = fields.Integer(string='Near Misses Reported', default=1)
    first_aid_cases = fields.Integer(string='First Aid Cases (FAC)', default=0)
    recordable_incidents = fields.Integer(string='OSHA Recordable Incidents (LTI/MTC/RWC)', default=0)
    safety_violations_fines = fields.Float(string='Safety Violation Fines Levied ($)', default=0.0)

    # Computed TRIR
    monthly_trir = fields.Float(string='Calculated Monthly TRIR', compute='_compute_trir', store=True)

    @api.depends('recordable_incidents', 'man_hours_worked')
    def _compute_trir(self):
        for rec in self:
            if rec.man_hours_worked and rec.man_hours_worked > 0:
                rec.monthly_trir = round((rec.recordable_incidents * 200000.0) / rec.man_hours_worked, 2)
            else:
                rec.monthly_trir = 0.0
