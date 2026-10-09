# -*- coding: utf-8 -*-
import math
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HSELopaStudy(models.Model):
    _name = 'hse.lopa.study'
    _description = 'Layers of Protection Analysis (LOPA) & SIL Determination'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='LOPA Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Scenario Title', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Facility / Unit', required=True)
    hazop_deviation_id = fields.Many2one('hse.hazop.deviation', string='Originating HAZOP Deviation')
    date = fields.Date(string='Analysis Date', default=fields.Date.today, required=True)
    facilitator_id = fields.Many2one('res.users', string='LOPA Facilitator', required=True, default=lambda self: self.env.user)
    participants = fields.Text(string='Assessment Team Members', required=True)

    # Consequence & Target
    consequence_description = fields.Text(string='Consequence Description (e.g. Vessel Overpressure & Toxic Rupture)', required=True)
    severity_category = fields.Selection([
        ('cat1', 'Category 1: Minor On-site First Aid ($10k loss)'),
        ('cat2', 'Category 2: Moderate Lost Time Injury ($100k loss)'),
        ('cat3', 'Category 3: Single Fatality / Severe Offsite Impact ($1M loss)'),
        ('cat4', 'Category 4: Multiple Fatalities / Major Disaster (> $10M loss)'),
    ], string='Consequence Severity Category', default='cat3', required=True)

    target_mitigated_frequency = fields.Float(
        string='Target Mitigated Frequency (TMF / yr)',
        default=0.0001,
        help="Corporate risk tolerance criterion. E.g. 1e-4 / yr for Cat 3, 1e-5 / yr for Cat 4."
    )

    # Initiating Event
    initiating_event_desc = fields.Text(string='Initiating Event (e.g. PCV-102 fails wide open, pump seal rupture)', required=True)
    initiating_event_freq = fields.Float(
        string='Initiating Event Frequency (IEF / yr)',
        default=0.1,
        required=True,
        help="Typical frequency: e.g. 0.1/yr for control loop failure, 1.0/yr for human error."
    )

    # Enabling Conditions & Conditional Modifiers
    enabling_condition_prob = fields.Float(string='Enabling Condition Probability (Pe)', default=1.0)
    time_in_area_prob = fields.Float(string='Occupancy / Time in Area Probability (Po)', default=1.0)
    ignition_prob = fields.Float(string='Ignition / Escalation Probability (Pi)', default=1.0)

    unmitigated_frequency = fields.Float(string='Unmitigated Event Frequency (f_u / yr)', compute='_compute_lopa_math', store=True)

    # Independent Protection Layers (IPLs)
    ipl_ids = fields.One2many('hse.lopa.ipl', 'lopa_id', string='Independent Protection Layers (IPLs)')
    total_ipl_pfd = fields.Float(string='Combined IPL PFD Product', compute='_compute_lopa_math', store=True)

    # Results & SIL Assignment
    mitigated_frequency = fields.Float(string='Mitigated Event Frequency (f_m / yr)', compute='_compute_lopa_math', store=True)
    risk_reduction_factor = fields.Float(string='Required Risk Reduction Factor (RRF)', compute='_compute_lopa_math', store=True)
    target_met = fields.Boolean(string='Risk Criteria Satisfied without SIF', compute='_compute_lopa_math', store=True)
    required_sil = fields.Selection([
        ('none', 'No SIF Required (Existing IPLs Sufficient)'),
        ('sil1', 'SIL 1 (PFD 0.1 to 0.01 / RRF 10 - 100)'),
        ('sil2', 'SIL 2 (PFD 0.01 to 0.001 / RRF 100 - 1,000)'),
        ('sil3', 'SIL 3 (PFD 0.001 to 0.0001 / RRF 1,000 - 10,000)'),
        ('sil4', 'SIL 4 (Fundamental Process Redesign Mandatory)'),
    ], string='Allocated Safety Integrity Level (SIL)', compute='_compute_lopa_math', store=True)

    recommendations = fields.Text(string='SIF Safety Requirement Specification (SRS) & Action Items')

    state = fields.Selection([
        ('draft', 'Draft Study'),
        ('validated', 'Technical Peer Review'),
        ('approved', 'Endorsed by Technical Authority'),
        ('closed', 'Closed & SIF Implemented'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.lopa.study') or _('LOPA-%04d') % self.env['hse.lopa.study'].search_count([])
        return super().create(vals_list)

    @api.depends('initiating_event_freq', 'enabling_condition_prob', 'time_in_area_prob', 'ignition_prob',
                 'ipl_ids.pfd', 'target_mitigated_frequency')
    def _compute_lopa_math(self):
        for rec in self:
            pe = rec.enabling_condition_prob if rec.enabling_condition_prob > 0 else 1.0
            po = rec.time_in_area_prob if rec.time_in_area_prob > 0 else 1.0
            pi = rec.ignition_prob if rec.ignition_prob > 0 else 1.0
            fu = (rec.initiating_event_freq or 0.1) * pe * po * pi
            rec.unmitigated_frequency = fu

            combined_pfd = 1.0
            for ipl in rec.ipl_ids:
                if ipl.is_valid_ipl and ipl.pfd > 0:
                    combined_pfd *= ipl.pfd
            rec.total_ipl_pfd = combined_pfd

            fm = fu * combined_pfd
            rec.mitigated_frequency = fm

            tmf = rec.target_mitigated_frequency if rec.target_mitigated_frequency > 0 else 0.0001
            if fm <= tmf:
                rec.target_met = True
                rec.risk_reduction_factor = 1.0
                rec.required_sil = 'none'
            else:
                rec.target_met = False
                rrf = fm / tmf
                rec.risk_reduction_factor = rrf
                if rrf <= 10:
                    rec.required_sil = 'sil1'
                elif rrf <= 100:
                    rec.required_sil = 'sil1'
                elif rrf <= 1000:
                    rec.required_sil = 'sil2'
                elif rrf <= 10000:
                    rec.required_sil = 'sil3'
                else:
                    rec.required_sil = 'sil4'

    def action_validate(self):
        self.write({'state': 'validated'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_close(self):
        self.write({'state': 'closed'})


class HSELopaIpl(models.Model):
    _name = 'hse.lopa.ipl'
    _description = 'Independent Protection Layer (IPL)'
    _order = 'sequence asc, id asc'

    lopa_id = fields.Many2one('hse.lopa.study', string='LOPA Scenario', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Seq', default=10)
    name = fields.Char(string='Protection Layer Tag & Description', required=True)
    
    ipl_type = fields.Selection([
        ('bpcs', 'Basic Process Control System (BPCS Loop / Interlock)'),
        ('alarm', 'Operator Response to Critical Alarm (with ample response time)'),
        ('psv', 'Pressure Relief Device (PSV / Rupture Disk)'),
        ('flame_arrester', 'Mechanical Passive Barrier (Flame Arrester / Seal)'),
        ('dike', 'Containment Dike / Secondary Bund Wall'),
        ('blast_wall', 'Blast Wall / Thermal Fire Insulation'),
        ('sis', 'Existing Safety Instrumented Function (SIF)'),
    ], string='IPL Category', required=True, default='bpcs')

    pfd = fields.Float(
        string='Probability of Failure on Demand (PFD)',
        default=0.1,
        required=True,
        help="Probability the layer fails when demanded (e.g. 0.1 = 1 order of magnitude risk reduction)."
    )

    is_valid_ipl = fields.Boolean(
        string='Meets 4 Core IPL Criteria',
        default=True,
        help="Must be Independent, Effective, Auditable, and Dependable."
    )
    justification = fields.Text(string='Independence & Reliability Justification')
    proof_test_interval_months = fields.Integer(string='Mandatory Proof Test Interval (Months)', default=12)
