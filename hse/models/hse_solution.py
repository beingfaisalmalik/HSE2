# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSESolution(models.Model):
    _name = 'hse.solution'
    _description = 'HSE Solutions & Lessons Learned Knowledge Base'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'rating desc, id desc'

    name = fields.Char(string='Solution Title', required=True, tracking=True)
    solution_code = fields.Char(string='Solution Ref (e.g. SOL-REL-023)', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    category = fields.Selection([
        ('mechanical', 'Mechanical & Piping Engineering Solution'),
        ('electrical_instrument', 'Electrical & Instrumentation Modification'),
        ('process_safety', 'Process Safety Control & Safeguard Solution'),
        ('human_factors', 'Human Factors & Ergonomics Redesign'),
        ('operational_procedure', 'Operating Procedure & Checklist Enhancement'),
        ('corrosion_material', 'Materials Upgrade & Corrosion Protection'),
    ], string='Solution Category', default='mechanical', required=True, tracking=True)

    applicable_equipment = fields.Selection([
        ('pumps', 'Pumps & Rotating Machinery'),
        ('compressors', 'Compressors & Turbines'),
        ('valves', 'Valves & Actuators'),
        ('piping', 'Pressure Piping & Flanges'),
        ('instruments', 'Sensors, Transmitters & DCS Logic'),
        ('general', 'General Plant Wide Application'),
    ], string='Applicable Equipment Class', default='general', required=True)

    # Problem & Root Cause Addressed
    problem_symptoms = fields.Text(string='Problem Symptoms / Failure Modes Addressed', required=True)
    root_cause_addressed = fields.Text(string='Root Causes Addressed', required=True)

    # Solution Details
    detailed_solution = fields.Html(string='Step-by-Step Engineered Solution & Implementation Instructions', required=True)
    engineering_standards = fields.Char(string='Governing Engineering Standard (e.g. API 682, ASME B31.3)')

    # Financial & Impact Analysis
    estimated_implementation_cost = fields.Float(string='Estimated Implementation Cost ($)', default=0.0)
    estimated_annual_cost_avoidance = fields.Float(string='Projected Annual Downtime & Repair Cost Avoidance ($)', default=0.0)

    # Community & Validation
    times_applied = fields.Integer(string='Times Successfully Deployed across Enterprise', default=1)
    rating = fields.Selection([
        ('1', 'Adequate'),
        ('2', 'Good'),
        ('3', 'Proven Industry Best Practice'),
    ], string='Effectiveness Rating', default='3', tracking=True)

    author_id = fields.Many2one('res.users', string='Subject Matter Expert (Author)', required=True, default=lambda self: self.env.user)
    approved_by_id = fields.Many2one('res.users', string='Technical Authority Approver')

    state = fields.Selection([
        ('draft', 'Draft Solution'),
        ('review', 'Peer & Technical Review'),
        ('published', 'Standard Operating Solution (Published)'),
        ('archived', 'Archived / Superseded'),
    ], string='Knowledge Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('solution_code', _('New')) == _('New'):
                vals['solution_code'] = self.env['ir.sequence'].next_by_code('hse.solution') or _('SOL-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def action_publish(self):
        self.write({
            'state': 'published',
            'approved_by_id': self.env.user.id
        })

    def action_archive(self):
        self.write({'state': 'archived'})
