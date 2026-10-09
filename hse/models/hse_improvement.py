# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date

class HSEImprovement(models.Model):
    _name = 'hse.improvement'
    _description = 'HSE Continuous Improvement & Kaizen'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Improvement Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Improvement Title', required=True, tracking=True)
    initiative_type = fields.Selection([
        ('kaizen', 'Kaizen Rapid Improvement Event'),
        ('six_sigma', 'Six Sigma DMAIC Project'),
        ('suggestion', 'Frontline Workforce Safety Suggestion'),
        ('audit_opp', 'Audit Opportunity for Improvement (OFI)'),
        ('near_miss_action', 'Near Miss Preventative Initiative'),
        ('energy_efficiency', 'Energy & Carbon Reduction Initiative'),
    ], string='Methodology / Program', default='kaizen', required=True, tracking=True)

    category = fields.Selection([
        ('safety', 'Occupational Safety & Ergonomics'),
        ('process_safety', 'Process Safety & Containment'),
        ('environmental', 'Waste & Emissions Minimization'),
        ('reliability', 'Equipment Reliability & Availability'),
        ('cost_reduction', 'Operational Cost Optimization'),
    ], string='Impact Area', default='safety', required=True, tracking=True)

    location_id = fields.Many2one('hse.location.profile', string='Plant Area')
    asset_id = fields.Many2one('assets.form', string='Asset / System')

    # Problem & Proposed Solution
    current_state = fields.Text(string='Current Baseline State / Problem Statement', required=True)
    proposed_solution = fields.Text(string='Proposed Innovation / Solution', required=True)

    # Benefit & ROI Analysis
    estimated_annual_savings = fields.Float(string='Projected Annual Cost Savings ($)', default=0.0, tracking=True)
    implementation_budget = fields.Float(string='Required Implementation Budget ($)', default=0.0)
    risk_reduction_points = fields.Integer(string='Risk Reduction Matrix Points', default=5)
    manhours_saved_per_year = fields.Float(string='Estimated Productive Hours Saved / Year', default=0.0)

    # Team & Milestones
    sponsor_id = fields.Many2one('res.users', string='Management Sponsor')
    project_lead_id = fields.Many2one('res.users', string='Improvement Project Lead', required=True, default=lambda self: self.env.user)
    target_completion_date = fields.Date(string='Target Implementation Date')
    actual_completion_date = fields.Date(string='Actual Completion Date')

    # Verified Results Post-Implementation
    results_summary = fields.Text(string='Verified Before vs. After Results')
    actual_annual_savings = fields.Float(string='Actual Verified Annual Savings ($)', default=0.0)

    state = fields.Selection([
        ('submitted', 'Idea / Opportunity Submitted'),
        ('evaluated', 'Technical & Business Evaluation'),
        ('approved', 'Approved for Execution'),
        ('in_progress', 'Implementation In Progress'),
        ('verified', 'Results Verified & Standardized'),
        ('closed', 'Completed & Closed'),
        ('rejected', 'Rejected / Not Feasible'),
    ], string='Status', default='submitted', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.improvement') or _('IMP-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def action_evaluate(self):
        self.write({'state': 'evaluated'})

    def action_approve(self):
        self.write({'state': 'approved', 'sponsor_id': self.env.user.id})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_verify(self):
        self.write({
            'state': 'verified',
            'actual_completion_date': date.today()
        })

    def action_close(self):
        self.write({'state': 'closed'})

    def action_reject(self):
        self.write({'state': 'rejected'})
