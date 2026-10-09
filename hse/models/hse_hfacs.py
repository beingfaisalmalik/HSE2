# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HseInvestigationHfacs(models.Model):
    _name = 'hse.investigation.hfacs'
    _description = 'Human Factors Analysis & Classification System (HFACS / TapRooT)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    investigation_id = fields.Many2one('incident.investigation', string='Incident Investigation',
                                        required=True, ondelete='cascade')
    name = fields.Char(string='HFACS Reference', default='HFACS Root Cause Analysis')

    # Level 1: Unsafe Acts
    act_decision_error = fields.Boolean(string='Decision Error (Wrong Action / Misjudgment)')
    act_skill_based_error = fields.Boolean(string='Skill-Based Error (Technique Slip / Memory Lapse)')
    act_perceptual_error = fields.Boolean(string='Perceptual Error (Illusion / Misinterpreted Display)')
    act_routine_violation = fields.Boolean(string='Routine Violation (Habitual Shortcut / Informal Norm)')
    act_exceptional_violation = fields.Boolean(string='Exceptional Violation (Unpermitted High-Risk Action)')
    act_narrative = fields.Text(string='Unsafe Acts Detail')

    # Level 2: Preconditions for Unsafe Acts
    pre_mental_state = fields.Boolean(string='Adverse Mental State (Fatigue, Stress, Complacency)')
    pre_physiological_state = fields.Boolean(string='Adverse Physiological State (Illness, Impairment)')
    pre_physical_limitation = fields.Boolean(string='Physical / Mental Limitation (Inadequate Ergonomics)')
    pre_crew_resource_mgt = fields.Boolean(string='Crew Resource Mgmt (Poor Shift Handover / Cross-Talk)')
    pre_personal_readiness = fields.Boolean(string='Personal Readiness (Off-Duty Rest / Fit for Duty)')
    preconditions_narrative = fields.Text(string='Preconditions Detail')

    # Level 3: Unsafe Supervision
    sup_inadequate = fields.Boolean(string='Inadequate Supervision (Lack of Oversight / Untrained Lead)')
    sup_planned_inappropriate = fields.Boolean(string='Planned Inappropriate Ops (Unrealistic Schedule Pressure)')
    sup_failed_to_correct = fields.Boolean(string='Failed to Correct Known Deficiencies / Hazards')
    sup_violations = fields.Boolean(string='Supervisory Violation (Supervisor Authorized Bypassing Rules)')
    supervision_narrative = fields.Text(string='Supervisory Influences Detail')

    # Level 4: Organizational Influences
    org_resource_management = fields.Boolean(string='Resource Management (Staffing Shortage, Equipment Neglect)')
    org_climate = fields.Boolean(string='Organizational Climate (Production Over Safety Culture)')
    org_operational_process = fields.Boolean(string='Operational Process (Flawed SOPs, Deficient MOC Review)')
    organization_narrative = fields.Text(string='Organizational Factors Detail')

    # Human Error Probability & Factor Index
    active_factors_count = fields.Integer(string='Total Contributing Human Factors', compute='_compute_factor_index', store=True)
    human_error_index = fields.Float(string='Human Factors Severity Index (%)', compute='_compute_factor_index', store=True)

    corrective_actions_hf = fields.Text(string='Human Factors Corrective & Preventative Engineering Plan',
                                        help='Ergonomic redesign, error-tolerant interlocks, procedural clarity, crew training')

    @api.depends('act_decision_error', 'act_skill_based_error', 'act_perceptual_error', 'act_routine_violation',
                 'act_exceptional_violation', 'pre_mental_state', 'pre_physiological_state', 'pre_physical_limitation',
                 'pre_crew_resource_mgt', 'pre_personal_readiness', 'sup_inadequate', 'sup_planned_inappropriate',
                 'sup_failed_to_correct', 'sup_violations', 'org_resource_management', 'org_climate',
                 'org_operational_process')
    def _compute_factor_index(self):
        factors = [
            'act_decision_error', 'act_skill_based_error', 'act_perceptual_error', 'act_routine_violation',
            'act_exceptional_violation', 'pre_mental_state', 'pre_physiological_state', 'pre_physical_limitation',
            'pre_crew_resource_mgt', 'pre_personal_readiness', 'sup_inadequate', 'sup_planned_inappropriate',
            'sup_failed_to_correct', 'sup_violations', 'org_resource_management', 'org_climate',
            'org_operational_process'
        ]
        total_possible = len(factors)
        for rec in self:
            count = sum(1 for f in factors if getattr(rec, f, False))
            rec.active_factors_count = count
            rec.human_error_index = round((count / float(total_possible)) * 100.0, 1)
