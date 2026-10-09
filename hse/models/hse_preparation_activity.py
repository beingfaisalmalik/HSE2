# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HSEPreparationActivity(models.Model):
    _name = 'hse.preparation.activity'
    _description = 'Work Package Preparation Activities'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(string='Prep Package Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Work Package Title', required=True, tracking=True)
    activity_type = fields.Selection([
        ('turnaround', 'Plant Turnaround (TAR) Package'),
        ('overhaul', 'Major Equipment Overhaul'),
        ('commissioning', 'Startup & Pre-Commissioning'),
        ('hot_tap', 'Hot Tapping Specialized Prep'),
        ('confined_prep', 'Confined Space Cleaning & Decontamination'),
        ('scaffold_prep', 'Complex Scaffolding & Rigging Prep'),
    ], string='Preparation Classification', default='turnaround', required=True, tracking=True)

    location_id = fields.Many2one('hse.location.profile', string='Plant Area / Unit', required=True)
    asset_id = fields.Many2one('assets.form', string='Target Equipment')
    scheduled_date = fields.Date(string='Target Execution Date', required=True)
    coordinator_id = fields.Many2one('res.users', string='Preparation Coordinator', required=True, default=lambda self: self.env.user)

    # Readiness Gates
    gate1_planning = fields.Boolean(string='Gate 1: Engineering & Scoping Cleared', default=False, tracking=True)
    gate2_isolation = fields.Boolean(string='Gate 2: Isolation Scheme & Blind List Approved', default=False, tracking=True)
    gate3_site_prep = fields.Boolean(string='Gate 3: Physical Site Staging & Scaffolding Completed', default=False, tracking=True)
    gate4_ready = fields.Boolean(string='Gate 4: Safety Walkthrough Confirmed - Ready for Work', default=False, tracking=True)

    readiness_progress = fields.Float(string='Preparation Readiness (%)', compute='_compute_progress', store=True)

    # Prep Tasks Line Items
    task_ids = fields.One2many('hse.preparation.task', 'activity_id', string='Preparation Tasks')

    permit_id = fields.Many2one('hse.permit', string='Associated Permit to Work')
    loto_plan_id = fields.Many2one('hse.loto.plan', string='Associated LOTO Plan')

    state = fields.Selection([
        ('draft', 'Scoping & Planning'),
        ('in_prep', 'Preparation in Progress'),
        ('gate_review', 'Readiness Gate Evaluation'),
        ('ready', 'Ready for Execution (Authorized)'),
        ('completed', 'Execution Completed / Demobilized'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.preparation.activity') or _('PREP-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    @api.depends('task_ids.is_completed', 'gate1_planning', 'gate2_isolation', 'gate3_site_prep', 'gate4_ready')
    def _compute_progress(self):
        for rec in self:
            total_items = len(rec.task_ids) + 4
            if total_items == 4:
                completed = sum([rec.gate1_planning, rec.gate2_isolation, rec.gate3_site_prep, rec.gate4_ready])
                rec.readiness_progress = (completed / 4.0) * 100.0
            else:
                task_done = len(rec.task_ids.filtered('is_completed'))
                gates_done = sum([rec.gate1_planning, rec.gate2_isolation, rec.gate3_site_prep, rec.gate4_ready])
                rec.readiness_progress = ((task_done + gates_done) / float(total_items)) * 100.0

    def action_start_prep(self):
        self.write({'state': 'in_prep'})

    def action_evaluate_gates(self):
        self.write({'state': 'gate_review'})

    def action_authorize_ready(self):
        if not (self.gate1_planning and self.gate2_isolation and self.gate3_site_prep and self.gate4_ready):
            raise UserError(_("All 4 Readiness Gates must be formally checked and signed off before declaring Ready for Execution."))
        self.write({'state': 'ready'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class HSEPreparationTask(models.Model):
    _name = 'hse.preparation.task'
    _description = 'Preparation Activity Task'
    _order = 'sequence asc, id asc'

    activity_id = fields.Many2one('hse.preparation.activity', string='Preparation Package', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Seq #', default=10)
    task_category = fields.Selection([
        ('scaffolding', 'Scaffolding & Work Platforms (Green Tagged)'),
        ('blinding', 'Blind Flanges / Spades Staged & Tagged'),
        ('rigging', 'Cranes, Hoists & Rigging Inspected'),
        ('ventilation', 'Pneumatic Air Blowers / Ventilation Installed'),
        ('lighting', 'Explosion-Proof 24V Lighting Staged'),
        ('cleaning', 'Chemical Cleaning / Hydro-jetting'),
        ('purge', 'Nitrogen Purging & LEL Zero Verification'),
        ('waste', 'Waste Disposal Skips & Hazardous Sump Prepared'),
    ], string='Task Discipline', required=True)
    name = fields.Char(string='Specific Preparation Task', required=True)
    responsible_person = fields.Char(string='Responsible Lead')
    is_completed = fields.Boolean(string='Completed & Verified', default=False)
    completion_datetime = fields.Datetime(string='Completed Timestamp')
    notes = fields.Char(string='Task Verification Notes')
