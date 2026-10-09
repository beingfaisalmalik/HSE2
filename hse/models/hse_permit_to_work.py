# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class HSEPermit(models.Model):
    _name = 'hse.permit'
    _description = 'Permit to Work (PTW / Control of Work)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc, id desc'

    name = fields.Char(string='Permit Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Work Task / Title', required=True, tracking=True)
    permit_type = fields.Selection([
        ('hot_work', 'Hot Work (Naked Flame / Welding / Spark Potential)'),
        ('cold_work', 'Cold Work (General Mechanical / Piping)'),
        ('confined_space', 'Confined Space Entry (Vessel / Tank / Pit)'),
        ('working_at_height', 'Working at Height (> 1.8m / Scaffolding)'),
        ('electrical', 'Electrical Work / High Voltage Isolation'),
        ('excavation', 'Excavation & Trenching (> 0.5m)'),
        ('radiography', 'Non-Destructive Testing / Industrial Radiography'),
        ('chemical', 'Hazardous Chemical / Toxic Line Breaking'),
    ], string='Permit Category', required=True, tracking=True)

    location_id = fields.Many2one('hse.location.profile', string='Operating Location / Unit', required=True, tracking=True)
    asset_id = fields.Many2one('assets.form', string='Asset / Equipment Tag')
    work_order_ref = fields.Char(string='Work Order / Job Ref')

    # Performing Party
    performing_company = fields.Selection([
        ('internal', 'Company Personnel'),
        ('contractor', 'External Contractor'),
    ], string='Workforce Type', default='internal', required=True)
    contractor_name = fields.Char(string='Contractor Company Name')
    requester_id = fields.Many2one('res.users', string='Performing Authority (Requester)', required=True, default=lambda self: self.env.user)
    receiver_name = fields.Char(string='Permit Receiver / Lead Technician')
    receiver_phone = fields.Char(string='Receiver Emergency Phone')
    workers_count = fields.Integer(string='Number of Workers in Party', default=2)

    # Timeframe
    start_datetime = fields.Datetime(string='Scheduled Start Time', required=True, default=fields.Datetime.now)
    end_datetime = fields.Datetime(string='Valid Until Time', required=True,
                                  default=lambda self: fields.Datetime.now() + timedelta(hours=12))
    duration_hours = fields.Float(string='Permit Validity Duration (Hours)', compute='_compute_duration', store=True)

    # Linked Safety Documents
    risk_assessment_id = fields.Many2one('ra_jsa.model', string='Approved JSA / Risk Assessment')
    loto_plan_id = fields.Many2one('hse.loto.plan', string='Approved LOTO Isolation Plan')

    # Hazards Checklist
    hazard_flammable = fields.Boolean(string='Flammable Hydrocarbons / Gases Present')
    hazard_toxic = fields.Boolean(string='Toxic Gas (H₂S, SO₂, CO, Chlorine)')
    hazard_oxygen_deficiency = fields.Boolean(string='Oxygen Deficiency / Asphyxiation Risk')
    hazard_high_pressure = fields.Boolean(string='High Pressure Fluids / Steam')
    hazard_falling_objects = fields.Boolean(string='Overhead / Falling Object Hazard')
    hazard_electrical = fields.Boolean(string='Live Electrical Conductors / HV')
    hazard_environmental = fields.Boolean(string='Environmental Spill / Drain Ingress Risk')

    # Mandatory Safety Precautions
    req_gas_test = fields.Boolean(string='Continuous / Periodic Gas Testing Required', default=True)
    req_fire_watch = fields.Boolean(string='Dedicated Fire Watcher Stationed', default=False)
    req_hole_watch = fields.Boolean(string='Dedicated Confined Space Entry Attendant', default=False)
    req_breathing_apparatus = fields.Boolean(string='SCBA / Supplied Air Respirator Mandatory')
    req_fall_arrest = fields.Boolean(string='Full Body Harness & Double Lanyards')
    req_lockout = fields.Boolean(string='Lockout / Tagout Energy Isolation Applied')
    req_barricade = fields.Boolean(string='Area Barricaded & Warning Signs Posted')

    # Gas Testing Logs
    gas_test_ids = fields.One2many('hse.permit.gas.test', 'permit_id', string='Gas Test Records')

    # SIMOPS (Simultaneous Operations) Collision Detection
    has_simops_conflict = fields.Boolean(string='SIMOPS Collision Flagged', compute='_compute_simops', store=True)
    conflicting_permit_ids = fields.Many2many('hse.permit', 'hse_permit_simops_rel', 'permit_id', 'conflict_id',
                                             string='Conflicting Concurrent Permits', compute='_compute_simops', store=True)
    simops_risk_level = fields.Selection([
        ('none', 'No Simultaneous Conflict'),
        ('medium', 'SIMOPS Managed (Non-Conflicting Crafts)'),
        ('high', 'CRITICAL SIMOPS CONFLICT (Hot Work / Confined Space / Hydrocarbon Risk)'),
    ], string='SIMOPS Risk Level', compute='_compute_simops', store=True)
    simops_mitigation = fields.Text(string='SIMOPS Control Measures & Special Precautions')
    simops_authorized_by = fields.Many2one('res.users', string='SIMOPS Coordinator Sign-off')

    # Workflow & Sign-offs
    # Step 1: Performing Authority Request
    pa_signed_date = fields.Datetime(string='Performing Authority Signed Date')

    # Step 2: Area Authority Review & Issue
    issuer_id = fields.Many2one('res.users', string='Area Authority / Permit Issuer')
    issuer_signed_date = fields.Datetime(string='Permit Issued Date')

    # Step 3: HSE / Safety Authority Authorization
    safety_officer_id = fields.Many2one('res.users', string='Safety Approver / HSE Lead')
    safety_signed_date = fields.Datetime(string='Safety Approval Date')

    # Work Completion & Handback
    handback_inspected_by = fields.Many2one('res.users', string='Area Inspected By')
    handback_housekeeping_ok = fields.Boolean(string='Area Cleared & Good Housekeeping Confirmed')
    handback_isolations_removed = fields.Boolean(string='Isolations De-isolated / Restored')
    handback_datetime = fields.Datetime(string='Handback Date/Time')
    handback_comments = fields.Text(string='Work Completion / Handback Notes')

    suspension_reason = fields.Text(string='Stop Work / Suspension Reason')

    state = fields.Selection([
        ('draft', 'Draft Request'),
        ('requested', 'Submitted for Review'),
        ('reviewed', 'Safety / Area Reviewed'),
        ('approved', 'Approved & Issued'),
        ('active', 'Work In Progress (Active)'),
        ('suspended', 'Work Suspended (Stop Work)'),
        ('handback', 'Handback & Inspection'),
        ('closed', 'Completed & Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Permit Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.permit') or _('PTW-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime:
                delta = rec.end_datetime - rec.start_datetime
                rec.duration_hours = delta.total_seconds() / 3600.0
            else:
                rec.duration_hours = 0.0

    def action_submit(self):
        self.write({
            'state': 'requested',
            'pa_signed_date': fields.Datetime.now()
        })

    def action_review(self):
        self.write({
            'state': 'reviewed',
            'issuer_id': self.env.user.id,
            'issuer_signed_date': fields.Datetime.now()
        })

    def action_approve(self):
        self.write({
            'state': 'approved',
            'safety_officer_id': self.env.user.id,
            'safety_signed_date': fields.Datetime.now()
        })

    @api.depends('location_id', 'start_datetime', 'end_datetime', 'state', 'permit_type')
    def _compute_simops(self):
        for rec in self:
            if not rec.location_id or not rec.start_datetime or not rec.end_datetime:
                rec.has_simops_conflict = False
                rec.conflicting_permit_ids = [(5, 0, 0)]
                rec.simops_risk_level = 'none'
                continue

            # Check other active/approved permits in same location profile
            conflicts = self.search([
                ('id', '!=', rec.id or 0),
                ('location_id', '=', rec.location_id.id),
                ('state', 'in', ['approved', 'active', 'requested', 'reviewed']),
                ('start_datetime', '<=', rec.end_datetime),
                ('end_datetime', '>=', rec.start_datetime),
            ])

            if conflicts:
                rec.conflicting_permit_ids = [(6, 0, conflicts.ids)]
                rec.has_simops_conflict = True
                
                # Check for high-risk combination (e.g. hot work with anything flammable or confined space)
                types = set(conflicts.mapped('permit_type') + [rec.permit_type])
                if 'hot_work' in types and ('confined_space' in types or 'chemical' in types or len(conflicts) >= 2):
                    rec.simops_risk_level = 'high'
                else:
                    rec.simops_risk_level = 'medium'
            else:
                rec.conflicting_permit_ids = [(5, 0, 0)]
                rec.has_simops_conflict = False
                rec.simops_risk_level = 'none'

    def action_start_work(self):
        if self.has_simops_conflict and self.simops_risk_level == 'high' and not self.simops_authorized_by:
            raise UserError(_("CRITICAL SIMOPS CONFLICT: Simultaneous hazardous operations detected at %s. SIMOPS Coordinator authorization is required before commencing work.") % (self.location_id.name))
        self.write({'state': 'active'})

    def action_suspend(self):
        self.write({'state': 'suspended'})

    def action_handback(self):
        self.write({
            'state': 'handback',
            'handback_inspected_by': self.env.user.id,
            'handback_datetime': fields.Datetime.now(),
            'handback_housekeeping_ok': True,
        })

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class HSEPermitGasTest(models.Model):
    _name = 'hse.permit.gas.test'
    _description = 'Permit Atmospheric Gas Test'
    _order = 'test_time desc'

    permit_id = fields.Many2one('hse.permit', string='Permit to Work', ondelete='cascade', required=True)
    test_time = fields.Datetime(string='Sample Timestamp', required=True, default=fields.Datetime.now)
    tester_name = fields.Char(string='Authorized Gas Tester (AGT)', required=True)
    tester_certification_no = fields.Char(string='AGT Certificate #')
    instrument_serial_no = fields.Char(string='Multi-Gas Detector S/N & Cal Date')

    oxygen_percent = fields.Float(string='Oxygen O₂ (19.5% - 23.5% safe)', default=20.9)
    lel_percent = fields.Float(string='Flammable / LEL % (< 10% safe, 0% hot work)', default=0.0)
    h2s_ppm = fields.Float(string='Hydrogen Sulfide H₂S ppm (< 5 ppm safe)', default=0.0)
    co_ppm = fields.Float(string='Carbon Monoxide CO ppm (< 25 ppm safe)', default=0.0)
    toxic_gas_name = fields.Char(string='Other Toxic Gas (e.g. VOC / SO₂)')
    toxic_gas_ppm = fields.Float(string='Toxic Reading (ppm)', default=0.0)

    is_safe_to_work = fields.Boolean(string='Atmosphere Verified Safe for Work', compute='_compute_safe', store=True)

    @api.depends('oxygen_percent', 'lel_percent', 'h2s_ppm', 'co_ppm')
    def _compute_safe(self):
        for rec in self:
            rec.is_safe_to_work = (
                19.5 <= rec.oxygen_percent <= 23.5 and
                rec.lel_percent < 5.0 and
                rec.h2s_ppm < 5.0 and
                rec.co_ppm < 25.0
            )
