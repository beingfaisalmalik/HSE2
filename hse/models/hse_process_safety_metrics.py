# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HsePseMetric(models.Model):
    _name = 'hse.pse.metric'
    _description = 'API RP 754 Process Safety Leading & Lagging Performance Accounting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, period desc'

    name = fields.Char(string='Metrics Reference', required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('hse.pse.metric') or _('New'))
    year = fields.Integer(string='Reporting Year', default=lambda self: fields.Date.context_today(self).year, required=True)
    period = fields.Selection([
        ('annual', 'Annual Full Year'),
        ('q1', 'Q1 (Jan - Mar)'),
        ('q2', 'Q2 (Apr - Jun)'),
        ('q3', 'Q3 (Jul - Sep)'),
        ('q4', 'Q4 (Oct - Dec)'),
    ], string='Reporting Period', default='annual', required=True)

    location_id = fields.Many2one('hse.location.profile', string='Facility / Operating Complex', required=True)

    # Work Hours Exposure
    total_employee_hours = fields.Float(string='Company Employee Work Hours', default=650000.0, required=True)
    total_contractor_hours = fields.Float(string='Contractor Site Work Hours', default=350000.0, required=True)
    total_site_exposure_hours = fields.Float(string='Total Combined Exposure Hours', compute='_compute_hours', store=True)

    # Tier 1 & Tier 2 Lagging Indicators (API RP 754)
    tier1_events_count = fields.Integer(string='Tier 1 Process Safety Events (PSE-1)', default=0, required=True)
    tier2_events_count = fields.Integer(string='Tier 2 Process Safety Events (PSE-2)', default=1, required=True)

    pse_tier1_rate = fields.Float(string='Tier 1 Event Rate (per 200,000 hrs)', compute='_compute_rates', store=True)
    pse_tier2_rate = fields.Float(string='Tier 2 Event Rate (per 200,000 hrs)', compute='_compute_rates', store=True)
    total_pse_rate = fields.Float(string='Total PSE Rate (Tier 1 + 2)', compute='_compute_rates', store=True)

    # Process Safety Severity Score
    tier1_severity_score = fields.Float(string='Total Tier 1 Severity Points', default=0.0)
    tier2_severity_score = fields.Float(string='Total Tier 2 Severity Points', default=6.0)

    # Tier 3 & Tier 4 Leading Indicators
    challenges_safety_systems_count = fields.Integer(string='Challenges to Safety Systems (Demands on PRV/SIS)', default=4)
    safe_operating_limit_excursions = fields.Integer(string='Operating Envelope / SOL Excursions', default=2)
    primary_containment_inspection_deficiencies = fields.Integer(string='Wall Thinning / Inspection Findings', default=8)

    psm_training_completion_pct = fields.Float(string='PSM Mandatory Training Completion (%)', default=98.5)
    moc_action_closure_pct = fields.Float(string='MOC Pre-Startup Action Item Closure (%)', default=100.0)
    pha_action_closure_pct = fields.Float(string='HAZOP / PHA Recommendation Closure (%)', default=94.0)
    safety_critical_maintenance_compliance_pct = fields.Float(string='SECE PM Compliance (%)', default=99.2)

    process_safety_index = fields.Float(string='Composite Process Safety Health Index (0-100)',
                                       compute='_compute_health_index', store=True)

    state = fields.Selection([
        ('draft', 'Draft Accounting'),
        ('validated', 'Validated by PSM Manager'),
        ('published', 'Published to Executive Board / API'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('total_employee_hours', 'total_contractor_hours')
    def _compute_hours(self):
        for rec in self:
            rec.total_site_exposure_hours = (rec.total_employee_hours or 0.0) + (rec.total_contractor_hours or 0.0)

    @api.depends('tier1_events_count', 'tier2_events_count', 'total_site_exposure_hours')
    def _compute_rates(self):
        for rec in self:
            hrs = rec.total_site_exposure_hours or 1.0
            rec.pse_tier1_rate = round(((rec.tier1_events_count or 0) * 200000.0) / hrs, 3)
            rec.pse_tier2_rate = round(((rec.tier2_events_count or 0) * 200000.0) / hrs, 3)
            rec.total_pse_rate = round((((rec.tier1_events_count or 0) + (rec.tier2_events_count or 0)) * 200000.0) / hrs, 3)

    @api.depends('pse_tier1_rate', 'pse_tier2_rate', 'psm_training_completion_pct',
                 'moc_action_closure_pct', 'pha_action_closure_pct', 'safety_critical_maintenance_compliance_pct')
    def _compute_health_index(self):
        for rec in self:
            # Score formula based on leading compliance penalized by lagging events
            leading_avg = ((rec.psm_training_completion_pct or 0.0) +
                           (rec.moc_action_closure_pct or 0.0) +
                           (rec.pha_action_closure_pct or 0.0) +
                           (rec.safety_critical_maintenance_compliance_pct or 0.0)) / 4.0
            penalty = ((rec.tier1_events_count or 0) * 25.0) + ((rec.tier2_events_count or 0) * 10.0)
            rec.process_safety_index = max(round(leading_avg - penalty, 1), 0.0)

    def action_validate(self):
        self.write({'state': 'validated'})

    def action_publish(self):
        self.write({'state': 'published'})
