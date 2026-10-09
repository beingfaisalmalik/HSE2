# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEInvestigationWhy(models.Model):
    _name = 'hse.investigation.why'
    _description = '5 Whys Root Cause Analysis Step'
    _order = 'why_number asc'

    investigation_id = fields.Many2one('incident.investigation', string='Investigation', ondelete='cascade', required=True)
    why_number = fields.Integer(string='Why # (1-5)', required=True, default=1)
    question = fields.Char(string='Why did this occur?', required=True)
    answer = fields.Text(string='Answer / Evidence', required=True)
    is_root_cause = fields.Boolean(string='Identified as Root Cause', default=False)


class HSEInvestigationFishbone(models.Model):
    _name = 'hse.investigation.fishbone'
    _description = 'Ishikawa / Fishbone Diagram Contributing Cause'

    investigation_id = fields.Many2one('incident.investigation', string='Investigation', ondelete='cascade', required=True)
    category = fields.Selection([
        ('man', 'Man / People (Training, Competency, Fatigue, Ergonomics)'),
        ('machine', 'Machine / Equipment (Design, Wear, Maintenance, Interlocks)'),
        ('method', 'Method / Procedure (SOP clarity, JSA quality, Permitting)'),
        ('material', 'Material / Chemistry (Corrosion, Specifications, Quality)'),
        ('measurement', 'Measurement / Instruments (Calibration, Sensors, Alarms)'),
        ('environment', 'Environment / Milieu (Weather, Lighting, Noise, Heat)'),
    ], string='Ishikawa Branch (6M)', required=True)
    cause_description = fields.Char(string='Contributing Cause', required=True)
    significance = fields.Selection([
        ('direct', 'Direct Triggering Cause'),
        ('contributing', 'Contributing Cause'),
        ('root', 'Root Systemic Defect'),
    ], string='Significance', default='contributing', required=True)


class HSEInvestigationTimeline(models.Model):
    _name = 'hse.investigation.timeline'
    _description = 'Investigation Chronological Event Timeline'
    _order = 'event_time asc'

    investigation_id = fields.Many2one('incident.investigation', string='Investigation', ondelete='cascade', required=True)
    event_time = fields.Datetime(string='Timestamp', required=True)
    description = fields.Text(string='Event Description & Observed State', required=True)
    source_evidence = fields.Char(string='Evidence Source (e.g. DCS Historian, CCTV, Witness)')


class HSEBowtieBarrier(models.Model):
    _name = 'hse.bowtie.barrier'
    _description = 'Bow-Tie Safety Barrier Analysis'
    _order = 'side asc, sequence asc, id asc'

    investigation_id = fields.Many2one('incident.investigation', string='Investigation', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    side = fields.Selection([
        ('preventive', 'Preventive Barrier (Threat → Top Event)'),
        ('mitigative', 'Mitigative Barrier (Top Event → Consequence)'),
    ], string='Barrier Position', default='preventive', required=True)

    barrier_category = fields.Selection([
        ('engineered_passive', 'Engineered Passive (Blast Wall, Bund, Fireproofing)'),
        ('engineered_active', 'Engineered Active (ESD Valve, Deluge, Relief Valve, SIS)'),
        ('procedural', 'Procedural / Administrative (SOP, PTW, LOTO, Pre-Job Brief)'),
        ('human', 'Human / Operational Intervention (Control Room Response, Field Watch)'),
    ], string='Barrier Type', default='engineered_active', required=True)

    threat_or_consequence = fields.Char(string='Threat / Initiator or Potential Consequence', required=True)
    barrier_name = fields.Char(string='Safety Barrier Description', required=True)

    barrier_status = fields.Selection([
        ('effective', 'Effective (Barrier Functioned as Designed)'),
        ('degraded', 'Degraded (Operated Partially or with Delay)'),
        ('failed', 'Failed / Missing (Barrier Defeated or Breached)'),
    ], string='Barrier Performance', default='failed', required=True)

    failure_mechanism = fields.Text(string='Failure Mechanism / Underlying Cause')
    action_id = fields.Many2one('hse.action', string='Remedial CAPA Action')


class InheritIncidentInvestigationAdvanced(models.Model):
    _inherit = 'incident.investigation'

    # Advanced RCA Methodologies
    rca_method = fields.Selection([
        ('five_whys', '5 Whys Structured Methodology'),
        ('fishbone', 'Ishikawa / Fishbone Cause & Effect Diagram'),
        ('taproot', 'TapRooT / Barrier Analysis'),
        ('fmeca', 'FMECA & Failure Mode Analysis'),
        ('comprehensive', 'Comprehensive Multi-Methodology RCA'),
    ], string='RCA Analysis Framework', default='comprehensive', required=True)

    why_ids = fields.One2many('hse.investigation.why', 'investigation_id', string='5 Whys Analysis')
    fishbone_ids = fields.One2many('hse.investigation.fishbone', 'investigation_id', string='Ishikawa Fishbone Factors')
    timeline_ids = fields.One2many('hse.investigation.timeline', 'investigation_id', string='Sequence of Events Timeline')
    bowtie_barrier_ids = fields.One2many('hse.bowtie.barrier', 'investigation_id', string='Bow-Tie Safety Barriers')

    # Human Factors Analysis
    human_error_type = fields.Selection([
        ('slip', 'Slip / Inattention (Action not as planned)'),
        ('lapse', 'Memory Lapse / Step Omitted'),
        ('mistake', 'Mistake / Rule-Based or Knowledge-Based Error'),
        ('violation', 'Situational / Exceptional Rule Violation'),
        ('none', 'No Human Error (Purely Mechanical / Latent Systemic)'),
    ], string='Human Error Classification', default='slip')

    organizational_factors = fields.Text(string='Organizational & Culture Factors (Workload, Time Pressure, Shift Handover)')

    # Formal Sign-offs
    peer_reviewer_id = fields.Many2one('res.users', string='Independent Peer Reviewer')
    peer_review_date = fields.Date(string='Peer Review Date')
    management_approver_id = fields.Many2one('res.users', string='Plant Manager / Safety Director')
    approval_date = fields.Date(string='Management Approval Date')

    # Direct CAPA Actions
    action_ids = fields.One2many('hse.action', 'investigation_id', string='CAPA Actions')
    action_count = fields.Integer(string='Action Count', compute='_compute_action_count')

    def _compute_action_count(self):
        for rec in self:
            rec.action_count = len(rec.action_ids)

    def action_create_capa(self):
        self.ensure_one()
        return {
            'name': _('Create Investigation Action'),
            'type': 'ir.actions.act_window',
            'res_model': 'hse.action',
            'view_mode': 'form',
            'context': {
                'default_investigation_id': self.id,
                'default_incident_id': self.incident_id.id if self.incident_id else False,
                'default_title': _('RCA Action for %s') % (self.ref_name or ''),
                'default_source_type': 'investigation',
                'default_source_reference': self.ref_name,
            },
            'target': 'current',
        }
