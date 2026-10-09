# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta

class HSEIncidentEvent(models.Model):
    _name = 'hse.incident.event'
    _description = 'Incident Sequence Event'
    _order = 'sequence asc, event_time asc'

    incident_id = fields.Many2one('incident.reporting', string='Parent Incident', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Sequence #', default=10)
    event_time = fields.Datetime(string='Event Timestamp', default=fields.Datetime.now, required=True)
    title = fields.Char(string='Event Title / Milestone', required=True)
    description = fields.Text(string='Detailed Event Description')
    event_type = fields.Selection([
        ('initiating', 'Initiating Event / Hazard Release'),
        ('escalation', 'Escalation / Secondary Consequence'),
        ('injury', 'Personnel Injury / Exposure'),
        ('containment', 'Emergency Containment Response'),
        ('isolation', 'Emergency Plant Isolation / Trip'),
    ], string='Event Classification', default='initiating', required=True)


class HSEIncidentInjury(models.Model):
    _name = 'hse.incident.injury'
    _description = 'Incident Personnel Injury / Illness Record'

    incident_id = fields.Many2one('incident.reporting', string='Incident', ondelete='cascade', required=True)
    person_type = fields.Selection([
        ('employee', 'Direct Employee'),
        ('contractor', 'Contractor Personnel'),
        ('third_party', 'Visitor / Third Party'),
    ], string='Person Category', default='employee', required=True)

    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    person_name = fields.Char(string='Person Full Name')
    job_title = fields.Char(string='Job Title / Trade')

    injury_severity = fields.Selection([
        ('fatality', 'Fatality'),
        ('lost_time', 'Lost Time Injury (LTI)'),
        ('restricted_work', 'Restricted Work Case (RWC)'),
        ('medical_treatment', 'Medical Treatment Case (MTC)'),
        ('first_aid', 'First Aid Only (FAC)'),
    ], string='OSHA Injury Severity', default='first_aid', required=True)

    body_part_affected = fields.Char(string='Body Part (e.g. Right Hand, Left Eye)')
    nature_of_injury = fields.Char(string='Nature of Injury (e.g. 2nd Degree Burn, Laceration, Fracture)')
    days_away_from_work = fields.Integer(string='Lost Workdays (Days Away)', default=0)
    days_restricted_duty = fields.Integer(string='Restricted Work / Transfer Days', default=0)

    medical_facility = fields.Char(string='Treating Clinic / Hospital')
    treating_physician = fields.Char(string='Treating Doctor')


class HSEIncidentEnvironmental(models.Model):
    _name = 'hse.incident.environmental'
    _description = 'Incident Environmental Release & Spill'

    incident_id = fields.Many2one('incident.reporting', string='Incident', ondelete='cascade', required=True)
    substance_name = fields.Char(string='Substance / Chemical Name (e.g. Crude Oil, H2SO4)', required=True)
    cas_number = fields.Char(string='CAS Chemical Number')

    spill_volume = fields.Float(string='Estimated Spill Volume', required=True)
    volume_unit = fields.Selection([
        ('liters', 'Liters'),
        ('barrels', 'Barrels (Bbl)'),
        ('gallons', 'Gallons'),
        ('kg', 'Kilograms / Metric Tons'),
        ('m3', 'Cubic Meters (m³)'),
    ], string='Unit', default='liters', required=True)

    media_affected = fields.Selection([
        ('contained_bund', 'Contained inside Concrete Bund / Sump (Zero Soil Ingress)'),
        ('uncontained_soil', 'Uncontained Land / Topsoil'),
        ('surface_water', 'Surface Water / River / Drain'),
        ('marine_water', 'Marine / Coastal Seawater'),
        ('air_atmosphere', 'Atmospheric Vapor Release / Flaring'),
    ], string='Release Media', default='contained_bund', required=True)

    recovered_volume = fields.Float(string='Volume Successfully Recovered', default=0.0)
    containment_status = fields.Selection([
        ('ongoing', 'Active Release / Containment Ongoing'),
        ('contained', 'Source Isolated & Leak Contained'),
        ('remediated', 'Cleaned up & Soil Disposed'),
    ], string='Remediation Status', default='contained')
    regulator_notified = fields.Boolean(string='Statutory Environmental Agency Notified (EPA / Coast Guard)')


class InheritIncidentReportingAdvanced(models.Model):
    _inherit = 'incident.reporting'

    # Advanced Fields for Maximo HSE Parity
    location_profile_id = fields.Many2one('hse.location.profile', string='Operating Location Profile')
    asset_equipment_id = fields.Many2one('assets.form', string='Affected Asset')

    # OSHA 300 Classification
    is_osha_recordable = fields.Boolean(string='OSHA 300 Recordable Incident', compute='_compute_osha_recordable', store=True)
    osha_case_number = fields.Char(string='OSHA Log Case #')
    statutory_report_due = fields.Datetime(string='Statutory Agency Reporting Deadline', compute='_compute_reporting_deadline', store=True)
    statutory_agency = fields.Char(string='Regulatory Agency to Notify (e.g. OSHA / EPA / BSEE)', default='OSHA')
    statutory_notified = fields.Boolean(string='Formally Notified to Statutory Authority', default=False)
    statutory_notification_date = fields.Datetime(string='Notification Sent Timestamp')

    total_lost_workdays = fields.Integer(string='Total Lost Workdays (Days Away)', compute='_compute_lost_days', store=True)
    total_restricted_days = fields.Integer(string='Total Restricted Duty Days', compute='_compute_lost_days', store=True)

    process_safety_tier = fields.Selection([
        ('tier1', 'API 754 Tier 1 (Loss of Primary Containment)'),
        ('tier2', 'API 754 Tier 2 Process Safety Event'),
        ('tier3', 'Tier 3 Near Miss / Barrier Challenge'),
        ('non_psm', 'Non-Process Safety Incident'),
    ], string='Process Safety Tier (API 754)', default='non_psm')

    # Sub-records
    event_ids = fields.One2many('hse.incident.event', 'incident_id', string='Sequence of Events')
    injury_ids = fields.One2many('hse.incident.injury', 'incident_id', string='Injuries & Illnesses')
    environmental_ids = fields.One2many('hse.incident.environmental', 'incident_id', string='Environmental Releases')

    # Financial Estimates
    financial_property_loss = fields.Float(string='Estimated Property & Asset Damage ($)', default=0.0)
    financial_production_loss = fields.Float(string='Estimated Production Downtime Loss ($)', default=0.0)
    financial_cleanup_loss = fields.Float(string='Estimated Cleanup & Medical Costs ($)', default=0.0)

    # Linked RCA Investigation
    investigation_ids = fields.One2many('incident.investigation', 'incident_id', string='Investigations')
    investigation_count = fields.Integer(string='Investigations Count', compute='_compute_inv_count')

    # Linked CAPA Actions
    action_ids = fields.One2many('hse.action', 'incident_id', string='CAPA Actions')
    action_count = fields.Integer(string='Actions Count', compute='_compute_act_count')

    def _compute_inv_count(self):
        for rec in self:
            rec.investigation_count = len(rec.investigation_ids)

    def _compute_act_count(self):
        for rec in self:
            rec.action_count = len(rec.action_ids)

    @api.depends('injury_ids.injury_severity')
    def _compute_osha_recordable(self):
        for rec in self:
            rec.is_osha_recordable = any(
                inj.injury_severity in ('fatality', 'lost_time', 'restricted_work', 'medical_treatment')
                for inj in rec.injury_ids
            )

    @api.depends('injury_ids.injury_severity', 'incident_date')
    def _compute_reporting_deadline(self):
        for rec in self:
            base_time = rec.incident_date or fields.Datetime.now()
            # Fatality requires 8 hour notification
            if any(inj.injury_severity == 'fatality' for inj in rec.injury_ids):
                rec.statutory_report_due = base_time + timedelta(hours=8)
            # In-patient hospitalization, amputation, or eye loss requires 24 hour notification
            elif any(inj.injury_severity in ('lost_time', 'restricted_work') for inj in rec.injury_ids):
                rec.statutory_report_due = base_time + timedelta(hours=24)
            else:
                rec.statutory_report_due = False

    @api.depends('injury_ids.days_away_from_work', 'injury_ids.days_restricted_duty')
    def _compute_lost_days(self):
        for rec in self:
            rec.total_lost_workdays = sum(inj.days_away_from_work for inj in rec.injury_ids)
            rec.total_restricted_days = sum(inj.days_restricted_duty for inj in rec.injury_ids)

    def action_create_investigation(self):
        self.ensure_one()
        return {
            'name': _('Initiate RCA Investigation'),
            'type': 'ir.actions.act_window',
            'res_model': 'incident.investigation',
            'view_mode': 'form',
            'context': {
                'default_incident_id': self.id,
                'default_immediate_cause': self.treatment_provided or '',
            },
            'target': 'current',
        }

    def action_create_action(self):
        self.ensure_one()
        return {
            'name': _('Create CAPA Action'),
            'type': 'ir.actions.act_window',
            'res_model': 'hse.action',
            'view_mode': 'form',
            'context': {
                'default_incident_id': self.id,
                'default_title': _('CAPA for %s') % (self.name or ''),
                'default_source_type': 'incident',
                'default_source_reference': self.name,
            },
            'target': 'current',
        }
