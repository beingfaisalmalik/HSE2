# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HseSafetyCultureAssessment(models.Model):
    _name = 'hse.safety.culture.assessment'
    _description = 'Safety Culture Maturity Assessment (DuPont Bradley Curve / Hearts & Minds)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'assessment_date desc'

    name = fields.Char(string='Assessment Title', required=True, tracking=True)
    assessment_date = fields.Date(string='Assessment Date', default=fields.Date.today, required=True)
    location_id = fields.Many2one('hse.location.profile', string='Facility / Unit Assessed', required=True)
    lead_assessor_id = fields.Many2one('hr.employee', string='Lead Culture Assessor', required=True)
    participants_count = fields.Integer(string='Survey / Interview Sample Size', default=120)

    # 5 Bradley Curve / Hudson Maturity Dimensions (Scored 1.0 to 5.0)
    score_leadership_commitment = fields.Float(string='1. Visible Leadership Commitment (1-5)', default=4.2, required=True)
    score_workforce_engagement = fields.Float(string='2. Workforce Engagement & SWA (1-5)', default=4.0, required=True)
    score_hazard_reporting_just_culture = fields.Float(string='3. Just Culture & Open Reporting (1-5)', default=3.8, required=True)
    score_risk_awareness_discipline = fields.Float(string='4. Operational Risk Discipline (1-5)', default=4.1, required=True)
    score_continuous_learning = fields.Float(string='5. Continuous Learning from Weak Signals (1-5)', default=3.9, required=True)

    overall_maturity_score = fields.Float(string='Overall Safety Culture Score (1.0 - 5.0)',
                                         compute='_compute_maturity', store=True)

    bradley_curve_stage = fields.Selection([
        ('reactive', 'Stage 1: Reactive (Natural Instincts, Compliance by Coercion)'),
        ('dependent', 'Stage 2: Dependent (Management Direction, Rules & Supervisors)'),
        ('independent', 'Stage 3: Independent (Individual Care, Knowledge & Self-Discipline)'),
        ('interdependent', 'Stage 4: Interdependent (Team Ownership, Collective Care, Zero Harm)'),
        ('generative', 'Stage 5: Generative (Safety is How Business is Done)'),
    ], string='Bradley Curve Maturity Level', compute='_compute_maturity', store=True)

    strengths = fields.Text(string='Identified Cultural Strengths')
    vulnerabilities = fields.Text(string='Cultural Blind Spots & Vulnerabilities')
    roadmap_actions = fields.Text(string='Roadmap Actions to Next Maturity Stage')

    state = fields.Selection([
        ('draft', 'In Assessment'),
        ('evaluated', 'Maturity Evaluated'),
        ('action_plan', 'Culture Action Plan Active'),
        ('completed', 'Archived / Baseline Established'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('score_leadership_commitment', 'score_workforce_engagement',
                 'score_hazard_reporting_just_culture', 'score_risk_awareness_discipline',
                 'score_continuous_learning')
    def _compute_maturity(self):
        for rec in self:
            avg = ((rec.score_leadership_commitment or 0.0) +
                   (rec.score_workforce_engagement or 0.0) +
                   (rec.score_hazard_reporting_just_culture or 0.0) +
                   (rec.score_risk_awareness_discipline or 0.0) +
                   (rec.score_continuous_learning or 0.0)) / 5.0
            rec.overall_maturity_score = round(avg, 2)

            if avg < 1.8:
                rec.bradley_curve_stage = 'reactive'
            elif avg < 2.8:
                rec.bradley_curve_stage = 'dependent'
            elif avg < 3.8:
                rec.bradley_curve_stage = 'independent'
            elif avg < 4.8:
                rec.bradley_curve_stage = 'interdependent'
            else:
                rec.bradley_curve_stage = 'generative'

    def action_evaluate(self):
        self._compute_maturity()
        self.write({'state': 'evaluated'})

    def action_approve_roadmap(self):
        self.write({'state': 'action_plan'})

    def action_complete(self):
        self.write({'state': 'completed'})
