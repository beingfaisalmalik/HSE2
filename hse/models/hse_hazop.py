# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HSEHazopStudy(models.Model):
    _name = 'hse.hazop.study'
    _description = 'Hazard and Operability (HAZOP) / Process Hazard Analysis (PHA)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='HAZOP Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Study Title', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Facility / Process Unit', required=True, tracking=True)
    study_type = fields.Selection([
        ('hazop', 'Hazard and Operability Study (HAZOP)'),
        ('what_if', 'What-If / Checklist Analysis'),
        ('fmea', 'Failure Modes and Effects Analysis (FMEA)'),
        ('hazid', 'Hazard Identification (HAZID)'),
        ('chazop', 'Control & Computer HAZOP (CHAZOP)'),
    ], string='Methodology', default='hazop', required=True, tracking=True)

    date = fields.Date(string='Study Date', default=fields.Date.today, required=True, tracking=True)
    target_completion_date = fields.Date(string='Target Completion')
    actual_completion_date = fields.Date(string='Actual Completion')

    leader_id = fields.Many2one('res.users', string='HAZOP Facilitator / Chairman', required=True, tracking=True)
    scribe_id = fields.Many2one('res.users', string='HAZOP Scribe / Secretary')
    team_members = fields.Text(string='Multi-Disciplinary Team Members (Process, Ops, Inst, Mech, HSE)', required=True)

    scope_description = fields.Text(string='Scope of Review & Battery Limits', required=True)
    pid_references = fields.Char(string='P&ID Drawing Numbers & Revisions', required=True)
    design_intent = fields.Text(string='Design Intent & Operating Modes (Normal, Startup, Turndown)')

    node_ids = fields.One2many('hse.hazop.node', 'study_id', string='Process Nodes')
    node_count = fields.Integer(string='Total Nodes', compute='_compute_counts', store=True)
    recommendation_count = fields.Integer(string='Total Recommendations', compute='_compute_counts', store=True)
    open_recommendations_count = fields.Integer(string='Open Recommendations', compute='_compute_counts', store=True)

    state = fields.Selection([
        ('draft', 'Scoping & Preparation'),
        ('in_session', 'HAZOP Sessions Active'),
        ('review', 'Draft Report Review'),
        ('approved', 'HAZOP Formally Endorsed'),
        ('action_tracking', 'Recommendations Implementation'),
        ('closed', 'Study & Actions Closed'),
    ], string='Study Lifecycle', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.hazop.study') or _('HAZOP-%04d') % self.env['hse.hazop.study'].search_count([])
        return super().create(vals_list)

    @api.depends('node_ids', 'node_ids.deviation_ids', 'node_ids.deviation_ids.recommendation_ids', 'node_ids.deviation_ids.recommendation_ids.state')
    def _compute_counts(self):
        for rec in self:
            rec.node_count = len(rec.node_ids)
            recs = rec.node_ids.mapped('deviation_ids').mapped('recommendation_ids')
            rec.recommendation_count = len(recs)
            rec.open_recommendations_count = len(recs.filtered(lambda r: r.state in ['draft', 'assigned', 'in_progress']))

    def action_start_session(self):
        self.write({'state': 'in_session'})

    def action_submit_review(self):
        self.write({'state': 'review'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_track_actions(self):
        self.write({'state': 'action_tracking'})

    def action_close(self):
        self.write({'state': 'closed', 'actual_completion_date': fields.Date.today()})


class HSEHazopNode(models.Model):
    _name = 'hse.hazop.node'
    _description = 'HAZOP Process Node'
    _order = 'node_number asc, id asc'

    study_id = fields.Many2one('hse.hazop.study', string='HAZOP Study', ondelete='cascade', required=True)
    node_number = fields.Integer(string='Node #', required=True, default=1)
    name = fields.Char(string='Node Title & Equipment Tag', required=True)
    node_boundary = fields.Text(string='Physical / Process Node Boundary', required=True)
    design_intent = fields.Text(string='Process Design Intent', required=True)
    operating_temp_range = fields.Char(string='Operating Temp Range (e.g. 180 - 220 °C)')
    operating_press_range = fields.Char(string='Operating Pressure Range (e.g. 15 - 18 barg)')
    flow_medium = fields.Char(string='Process Fluid / Medium')

    deviation_ids = fields.One2many('hse.hazop.deviation', 'node_id', string='Deviations Evaluated')
    deviation_count = fields.Integer(string='Deviations Count', compute='_compute_dev_count', store=True)

    @api.depends('deviation_ids')
    def _compute_dev_count(self):
        for rec in self:
            rec.deviation_count = len(rec.deviation_ids)


class HSEHazopDeviation(models.Model):
    _name = 'hse.hazop.deviation'
    _description = 'HAZOP Process Deviation Worksheet'
    _order = 'id asc'

    node_id = fields.Many2one('hse.hazop.node', string='Process Node', ondelete='cascade', required=True)
    study_id = fields.Many2one('hse.hazop.study', related='node_id.study_id', string='HAZOP Study', store=True)

    parameter = fields.Selection([
        ('flow', 'Flow'),
        ('pressure', 'Pressure'),
        ('temperature', 'Temperature'),
        ('level', 'Level'),
        ('composition', 'Composition / Phase'),
        ('viscosity', 'Viscosity'),
        ('reaction', 'Reaction / Catalysis'),
        ('utility', 'Utility (Steam, Power, Cooling Water, N2)'),
        ('operation', 'Operation (Startup, Shutdown, Purging)'),
        ('maintenance', 'Maintenance / Isolation'),
    ], string='Process Parameter', required=True, default='pressure')

    guide_word = fields.Selection([
        ('no', 'No / None (Zero Flow/Feed)'),
        ('more', 'More (High Flow/Pressure/Temp)'),
        ('less', 'Less (Low Flow/Pressure/Temp)'),
        ('reverse', 'Reverse (Backflow / Counter-current)'),
        ('as_well_as', 'As Well As (Contamination / Ingress)'),
        ('part_of', 'Part Of (Phase Split / Missing Component)'),
        ('other_than', 'Other Than (Wrong Fluid / Misdirected)'),
        ('early_late', 'Early / Late (Timing Sequence Error)'),
    ], string='Guide Word', required=True, default='more')

    deviation_text = fields.Char(string='Synthesized Deviation', compute='_compute_deviation_text', store=True)
    causes = fields.Text(string='Credible Root Causes (e.g. Control Valve fails open, Tube rupture)', required=True)
    consequences = fields.Text(string='Consequences without Safeguards (Safety, Environmental, Asset)', required=True)

    # Initial Unmitigated Risk
    unmitigated_severity = fields.Integer(string='Unmitigated Severity (1-5)', default=3, required=True)
    unmitigated_likelihood = fields.Integer(string='Unmitigated Likelihood (1-5)', default=3, required=True)
    unmitigated_risk_score = fields.Integer(string='Unmitigated Score', compute='_compute_risk_scores', store=True)

    # Safeguards
    existing_safeguards = fields.Text(string='Existing Engineered & Procedural Safeguards (PSVs, Interlocks, Alarms)', required=True)

    # Residual Mitigated Risk
    mitigated_severity = fields.Integer(string='Mitigated Severity (1-5)', default=3, required=True)
    mitigated_likelihood = fields.Integer(string='Mitigated Likelihood (1-5)', default=1, required=True)
    mitigated_risk_score = fields.Integer(string='Mitigated Score', compute='_compute_risk_scores', store=True)
    risk_level = fields.Selection([
        ('low', 'Low / Acceptable (ALARP)'),
        ('medium', 'Medium (Tolerable with Controls)'),
        ('high', 'High (Undesirable - Action Required)'),
        ('critical', 'Critical (Unacceptable - Stop/Immediate Redesign)'),
    ], string='Residual Risk Category', compute='_compute_risk_scores', store=True)

    # LOPA / SIL allocation trigger
    requires_lopa = fields.Boolean(string='Requires LOPA / SIL Determination', default=False)
    sil_target = fields.Selection([
        ('none', 'No Safety Instrumented Function Required'),
        ('sil1', 'SIL 1 (RRF 10 - 100)'),
        ('sil2', 'SIL 2 (RRF 100 - 1,000)'),
        ('sil3', 'SIL 3 (RRF 1,000 - 10,000)'),
    ], string='Target SIL Requirement', default='none')

    recommendation_ids = fields.One2many('hse.hazop.recommendation', 'deviation_id', string='Recommendations')

    @api.depends('guide_word', 'parameter')
    def _compute_deviation_text(self):
        gw_map = dict(self._fields['guide_word'].selection)
        param_map = dict(self._fields['parameter'].selection)
        for rec in self:
            gw = gw_map.get(rec.guide_word, rec.guide_word or '')
            pm = param_map.get(rec.parameter, rec.parameter or '')
            rec.deviation_text = f"{gw} - {pm}"

    @api.depends('unmitigated_severity', 'unmitigated_likelihood', 'mitigated_severity', 'mitigated_likelihood')
    def _compute_risk_scores(self):
        for rec in self:
            rec.unmitigated_risk_score = (rec.unmitigated_severity or 1) * (rec.unmitigated_likelihood or 1)
            score = (rec.mitigated_severity or 1) * (rec.mitigated_likelihood or 1)
            rec.mitigated_risk_score = score
            if score >= 16:
                rec.risk_level = 'critical'
            elif score >= 10:
                rec.risk_level = 'high'
            elif score >= 4:
                rec.risk_level = 'medium'
            else:
                rec.risk_level = 'low'


class HSEHazopRecommendation(models.Model):
    _name = 'hse.hazop.recommendation'
    _description = 'HAZOP Study Action Item / Recommendation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    deviation_id = fields.Many2one('hse.hazop.deviation', string='Deviation Reference', ondelete='cascade', required=True)
    study_id = fields.Many2one('hse.hazop.study', related='deviation_id.study_id', string='HAZOP Study', store=True)
    name = fields.Char(string='Action Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    recommendation = fields.Text(string='Engineering Recommendation / Action Plan', required=True, tracking=True)

    action_category = fields.Selection([
        ('design', 'Engineering / Process Redesign'),
        ('hardware', 'Instrumentation / Hardware Interlock Addition'),
        ('psv', 'Relief Valve Sizing / Capacity Re-check'),
        ('procedure', 'Operating Procedure (SOP) Modification'),
        ('maintenance', 'PM / Inspection Frequency Modification'),
        ('training', 'Operator Competency & Simulator Training'),
    ], string='Category', default='design', required=True)

    assigned_department = fields.Selection([
        ('process', 'Process Engineering'),
        ('instrumentation', 'Instrumentation & Control'),
        ('mechanical', 'Mechanical & Piping'),
        ('operations', 'Operations'),
        ('hse', 'HSE & Process Safety'),
    ], string='Actionee Discipline', default='process', required=True)

    responsible_user_id = fields.Many2one('res.users', string='Action Owner', tracking=True)
    target_date = fields.Date(string='Target Completion Date', required=True, tracking=True)
    closure_date = fields.Date(string='Actual Closure Date', tracking=True)

    closure_notes = fields.Text(string='Closure Evidence & Engineering Documentation')
    moc_id = fields.Many2one('hse.moc', string='Associated Management of Change (MOC)')
    action_id = fields.Many2one('hse.action', string='Central CAPA Action')

    state = fields.Selection([
        ('draft', 'Proposed in Session'),
        ('assigned', 'Assigned & Accepted'),
        ('in_progress', 'Engineering Review / Implementation'),
        ('completed', 'Implemented & Pending HSE Verification'),
        ('verified', 'Verified Closed by Process Safety'),
        ('rejected', 'Deemed Unnecessary / Alternative Implemented'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.hazop.recommendation') or _('REC-%05d') % self.env['hse.hazop.recommendation'].search_count([])
        return super().create(vals_list)

    def action_assign(self):
        self.write({'state': 'assigned'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_verify_close(self):
        self.write({'state': 'verified', 'closure_date': fields.Date.today()})
