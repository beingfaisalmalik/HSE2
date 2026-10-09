# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEOperatingProcedure(models.Model):
    _name = 'hse.operating.procedure'
    _description = 'Standard Operating Procedure (SOP)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'procedure_code asc, revision desc'

    name = fields.Char(string='Procedure Title', required=True, tracking=True)
    procedure_code = fields.Char(string='SOP Code (e.g. SOP-OPS-014)', required=True, tracking=True)
    procedure_type = fields.Selection([
        ('sop', 'Standard Operating Procedure (Normal Run)'),
        ('startup', 'Plant / Unit Startup Procedure'),
        ('shutdown', 'Controlled Normal Shutdown Procedure'),
        ('emergency', 'Emergency Operating Procedure (EOP)'),
        ('abnormal', 'Abnormal Operating / Upset Response'),
        ('maintenance', 'Routine Operational Maintenance Routine'),
    ], string='Procedure Classification', default='sop', required=True, tracking=True)

    location_id = fields.Many2one('hse.location.profile', string='Applicable Area / Facility')
    asset_id = fields.Many2one('assets.form', string='Applicable Equipment')
    revision = fields.Char(string='Revision Number', default='Rev 1.0', required=True, tracking=True)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today, required=True)
    review_interval_months = fields.Integer(string='Review Frequency (Months)', default=12)
    next_review_date = fields.Date(string='Next Scheduled Review Date')

    # Safety Criticality
    is_safety_critical = fields.Boolean(string='Safety Critical Task (SECE Associated)', default=False, tracking=True)
    mandatory_ppe = fields.Char(string='Mandatory PPE (e.g. Hard hat, safety glasses, chemical gloves, H2S monitor)')
    required_crew_size = fields.Integer(string='Minimum Required Crew Size', default=2)

    purpose_and_scope = fields.Text(string='Purpose & Operational Scope', required=True)
    prerequisites = fields.Text(string='Prerequisites & Permitting Requirements')

    # Steps Breakdown
    step_ids = fields.One2many('hse.operating.procedure.step', 'procedure_id', string='Step-by-Step Instructions')

    author_id = fields.Many2one('res.users', string='Author / Process Engineer', required=True, default=lambda self: self.env.user)
    approver_id = fields.Many2one('res.users', string='Operations Manager Approver')

    state = fields.Selection([
        ('draft', 'Drafting'),
        ('review', 'Under Peer / Safety Review'),
        ('approved', 'Approved & Released'),
        ('published', 'Active / Published in Field'),
        ('archived', 'Archived / Superseded'),
    ], string='Lifecycle Status', default='draft', tracking=True)

    def action_submit_review(self):
        self.write({'state': 'review'})

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id
        })

    def action_publish(self):
        self.write({'state': 'published'})

    def action_archive(self):
        self.write({'state': 'archived'})


class HSEOperatingProcedureStep(models.Model):
    _name = 'hse.operating.procedure.step'
    _description = 'Operating Procedure Execution Step'
    _order = 'step_number asc, id asc'

    procedure_id = fields.Many2one('hse.operating.procedure', string='Procedure', ondelete='cascade', required=True)
    step_number = fields.Integer(string='Step #', required=True, default=1)
    name = fields.Char(string='Step Summary / Action', required=True)
    detailed_instructions = fields.Text(string='Detailed Instructions & Expected Value', required=True)
    hazard_warning = fields.Char(string='Critical Hazard Warning / Caution')
    is_hold_point = fields.Boolean(string='Quality / Safety Hold Point (Witness Sign-off Required)', default=False)
    verification_check = fields.Char(string='Acceptance Criteria / Check')
