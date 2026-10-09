# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class HSEMoc(models.Model):
    _name = 'hse.moc'
    _description = 'Management of Change (MOC)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='MOC Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Change Title', required=True, tracking=True)
    change_type = fields.Selection([
        ('permanent', 'Permanent Modification'),
        ('temporary', 'Temporary Change (Time Bound)'),
        ('emergency', 'Emergency Change (Retrospective Review)'),
    ], string='Change Classification', default='permanent', required=True, tracking=True)

    category = fields.Selection([
        ('process', 'Process Chemistry / Operating Conditions (Temp/Press/Flow)'),
        ('equipment', 'Mechanical Equipment / Piping / Relief Devices'),
        ('instrumentation', 'Control Logic / DCS / SIS / Interlocks'),
        ('electrical', 'Electrical Systems / Power Distribution'),
        ('procedures', 'Operating Procedures / Safe Work Practices'),
        ('organizational', 'Key Personnel / Shift Manning / Organization'),
        ('facility', 'Civil / Structural / Fire Protection'),
    ], string='Change Discipline', default='equipment', required=True, tracking=True)

    location_id = fields.Many2one('hse.location.profile', string='Plant / Operating Area', required=True)
    asset_id = fields.Many2one('assets.form', string='Target Asset / Equipment Tag')
    description_of_change = fields.Text(string='Detailed Description of Proposed Change', required=True)
    justification = fields.Text(string='Technical & Business Justification', required=True)

    # Temporary Change Specifics
    temporary_expiry_date = fields.Date(string='Temporary Change Expiration Date')
    reversion_plan = fields.Text(string='Plan for Reversion to Baseline')

    # Financials
    estimated_cost = fields.Float(string='Estimated Capex / Implementation Cost ($)')

    # Multi-Disciplinary Reviews
    review_ids = fields.One2many('hse.moc.review', 'moc_id', string='Discipline Reviews')

    # Pre-Start Safety Review (PSSR)
    pssr_required = fields.Boolean(string='Pre-Start Safety Review (PSSR) Required', default=True)
    pssr_line_ids = fields.One2many('hse.moc.pssr.line', 'moc_id', string='PSSR Checklist')
    pssr_completed = fields.Boolean(string='PSSR Verification Completed', compute='_compute_pssr_status', store=True)

    # Risk Assessment
    initial_risk_score = fields.Integer(string='Initial Risk Score of Change', default=12)
    residual_risk_score = fields.Integer(string='Residual Risk Score Post-Mitigation', default=4)

    # Documentation & Training Impact
    updates_pid = fields.Boolean(string='P&ID / Engineering Drawings Updated')
    updates_sop = fields.Boolean(string='Operating Procedures (SOP) Updated')
    updates_training = fields.Boolean(string='Workforce Re-training Completed')

    # Linked CAPA Actions
    action_ids = fields.One2many('hse.action', 'moc_id', string='MOC Action Items')
    action_count = fields.Integer(string='Actions Count', compute='_compute_action_count')

    initiator_id = fields.Many2one('res.users', string='MOC Initiator', required=True, default=lambda self: self.env.user)
    approver_id = fields.Many2one('res.users', string='MOC Approver / Operations Manager')

    state = fields.Selection([
        ('draft', 'Draft Change Proposal'),
        ('technical_review', 'Technical Reviews Underway'),
        ('risk_review', 'Risk Assessment & Hazards Review'),
        ('approved', 'MOC Approved for Implementation'),
        ('implementation', 'Implementation / Work in Progress'),
        ('pssr', 'Pre-Start Safety Review (PSSR)'),
        ('commissioned', 'Commissioned & Active'),
        ('closed', 'Closed Out & Drawings As-Built'),
        ('cancelled', 'Cancelled / Rejected'),
    ], string='MOC Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.moc') or _('MOC-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def _compute_action_count(self):
        for rec in self:
            rec.action_count = len(rec.action_ids)

    @api.depends('pssr_line_ids.is_verified')
    def _compute_pssr_status(self):
        for rec in self:
            if rec.pssr_line_ids:
                rec.pssr_completed = all(line.is_verified for line in rec.pssr_line_ids)
            else:
                rec.pssr_completed = False

    def action_load_default_pssr(self):
        """Populate standard industrial Pre-Startup Safety Review items."""
        self.ensure_one()
        if self.pssr_line_ids:
            return
        default_items = [
            ('engineering', 'Physical construction conforms to approved design specifications and stamped P&IDs.'),
            ('engineering', 'Piping stress analysis, material test reports, and pressure tests witnessed and signed.'),
            ('safety_systems', 'Pressure relief valves (PSVs) installed, tagged, calibrated, and discharge routes verified safe.'),
            ('safety_systems', 'Emergency Shutdown (ESD) valves, pushbuttons, and SIS interlocks loop-tested.'),
            ('procedures', 'Standard Operating Procedures (SOPs) revised to reflect modification and approved.'),
            ('procedures', 'Emergency response procedures updated for new operating hazards or inventory changes.'),
            ('training', 'Operations and maintenance personnel trained on modified equipment and procedures.'),
            ('environmental', 'Secondary containment, bund drains, and emission vents verified clear and intact.'),
            ('safety_systems', 'LOTO lock removal and zero-energy de-isolation verified prior to hydrocarbon introduction.'),
        ]
        lines = []
        for cat, desc in default_items:
            lines.append((0, 0, {
                'category': cat,
                'item_description': desc,
                'is_verified': False,
            }))
        self.write({'pssr_line_ids': lines})

    def action_submit_review(self):
        self.write({'state': 'technical_review'})

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id
        })

    def action_start_implementation(self):
        self.write({'state': 'implementation'})

    def action_start_pssr(self):
        self.write({'state': 'pssr'})

    def action_commission(self):
        self.write({'state': 'commissioned'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class HSEMocReview(models.Model):
    _name = 'hse.moc.review'
    _description = 'MOC Discipline Technical Review'

    moc_id = fields.Many2one('hse.moc', string='MOC', ondelete='cascade', required=True)
    discipline = fields.Selection([
        ('process_safety', 'Process Safety Engineering (PSM)'),
        ('operations', 'Operations / Production Lead'),
        ('mechanical', 'Mechanical / Piping Integrity'),
        ('electrical_instrument', 'Electrical & Instrumentation'),
        ('environmental', 'Environmental Compliance'),
        ('maintenance', 'Reliability & Maintenance'),
    ], string='Technical Discipline', required=True)
    reviewer_id = fields.Many2one('res.users', string='Reviewer', required=True)
    recommendation = fields.Selection([
        ('approve', 'Approved - No Safety Concerns'),
        ('approve_conditions', 'Approved with Conditions / Actions'),
        ('reject', 'Rejected - Unacceptable Process Risk'),
    ], string='Discipline Finding', default='approve')
    review_comments = fields.Text(string='Reviewer Technical Comments')
    review_date = fields.Date(string='Review Date', default=fields.Date.today)


class HSEMocPssrLine(models.Model):
    _name = 'hse.moc.pssr.line'
    _description = 'Pre-Start Safety Review (PSSR) Item'

    moc_id = fields.Many2one('hse.moc', string='MOC', ondelete='cascade', required=True)
    category = fields.Selection([
        ('engineering', 'Physical Construction & Engineering Specs'),
        ('safety_systems', 'Safety Relief, Alarms, Interlocks & Firefighting'),
        ('procedures', 'Standard Operating & Emergency Procedures'),
        ('training', 'Operator Qualification & Training Completed'),
        ('environmental', 'Containment & Waste Management Handled'),
    ], string='PSSR Element', required=True)
    item_description = fields.Char(string='Checklist Verification Requirement', required=True)
    is_verified = fields.Boolean(string='Verified & Accepted', default=False)
    verified_by = fields.Many2one('res.users', string='Verified By')
    verification_date = fields.Date(string='Date Verified')
    notes = fields.Char(string='Verification Observation / Punchlist Item')
