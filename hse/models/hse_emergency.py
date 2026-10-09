# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEEmergencyPlan(models.Model):
    _name = 'hse.emergency.plan'
    _description = 'Facility Emergency Response Plan (ERP)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='ERP Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Plan Title', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Covered Facility', required=True)
    incident_commander_id = fields.Many2one('res.users', string='Primary Incident Commander (IC)', required=True)
    deputy_commander_id = fields.Many2one('res.users', string='Deputy Incident Commander', required=True)

    emergency_type = fields.Selection([
        ('hydrocarbon_fire', 'Tier 3 Major Hydrocarbon Fire / BLEVE'),
        ('toxic_gas_cloud', 'Toxic Gas Release (H2S / Chlorine / Ammonia Plume)'),
        ('explosion', 'Vapor Cloud Explosion (VCE)'),
        ('spill_water', 'Major Environmental Marine / River Spill'),
        ('medical_mass', 'Mass Casualty Incident (MCI)'),
        ('weather', 'Severe Hurricane / Cyclone / Flood'),
        ('security', 'Hostile Infiltration / Security Breach'),
    ], string='Scenario Category', required=True, default='hydrocarbon_fire')

    response_actions = fields.Text(string='Immediate Emergency Protocol & Alarm Sequence', required=True)
    internal_callout_list = fields.Text(string='ERT Callout & Crisis Management Notification Hierarchy', required=True)
    external_agencies = fields.Text(string='External Emergency Services (Municipal Fire, Coast Guard, Police, Hospitals)', required=True)
    muster_stations = fields.Text(string='Primary & Secondary Evacuation Muster Points', required=True)

    drill_ids = fields.One2many('hse.emergency.drill', 'plan_id', string='Executed Response Drills')
    drill_count = fields.Integer(string='Drills Conducted', compute='_compute_drill_count', store=True)

    state = fields.Selection([
        ('draft', 'Draft Plan'),
        ('active', 'Approved & Active in Operation'),
        ('under_review', 'Annual Review in Progress'),
        ('archived', 'Superseded'),
    ], string='Plan Status', default='active', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.emergency.plan') or _('ERP-%04d') % self.env['hse.emergency.plan'].search_count([])
        return super().create(vals_list)

    @api.depends('drill_ids')
    def _compute_drill_count(self):
        for rec in self:
            rec.drill_count = len(rec.drill_ids)


class HSEEmergencyDrill(models.Model):
    _name = 'hse.emergency.drill'
    _description = 'Emergency Response Simulation Drill & Muster Accountability'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'drill_date desc, id desc'

    name = fields.Char(string='Drill Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    plan_id = fields.Many2one('hse.emergency.plan', string='Emergency Response Plan', required=True)
    title = fields.Char(string='Drill Exercise Title', required=True, tracking=True)
    drill_date = fields.Date(string='Drill Date', default=fields.Date.today, required=True)
    lead_evaluator_id = fields.Many2one('res.users', string='Lead HSE Evaluator', required=True, default=lambda self: self.env.user)

    drill_scope = fields.Selection([
        ('tabletop', 'Tabletop Scenario Exercise'),
        ('functional', 'Functional Unit Drill (e.g. Foam System Deployment)'),
        ('full_scale', 'Full-Scale Unannounced Site Evacuation & Live Fire Drill'),
    ], string='Drill Scale', default='full_scale', required=True)

    alarm_activation_time = fields.Datetime(string='Sirens / Alarm Sounded Time', default=fields.Datetime.now, required=True)
    all_clear_time = fields.Datetime(string='All-Clear Sounded Time', default=fields.Datetime.now, required=True)

    # Response Times & Headcount
    ert_response_time_minutes = fields.Float(string='ERT Response & On-Scene Time (Minutes)', default=3.5, required=True)
    total_personnel_on_site = fields.Integer(string='Total Personnel on Site (Badge Gate Count)', default=120, required=True)
    total_personnel_mustered = fields.Integer(string='Personnel Accounted for at Muster Points', default=120, required=True)
    headcount_completion_minutes = fields.Float(string='Headcount Completion Time (Minutes)', default=4.2, required=True)
    unaccounted_personnel = fields.Integer(string='Unaccounted Personnel (Missing)', compute='_compute_headcount', store=True)

    # Performance Grading
    drill_score_percent = fields.Float(string='Overall Drill Effectiveness Score (%)', default=92.0, required=True)
    strengths_observed = fields.Text(string='Key Operational Strengths Observed', required=True)
    areas_for_improvement = fields.Text(string='Deficiencies & Gaps Identified for Corrective Action', required=True)

    state = fields.Selection([
        ('scheduled', 'Drill Scheduled'),
        ('executed', 'Simulation Executed'),
        ('critiqued', 'Post-Drill Debrief Completed'),
        ('closed', 'Corrective Actions Verified & Closed'),
    ], string='Status', default='executed', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.emergency.drill') or _('DRILL-%04d') % self.env['hse.emergency.drill'].search_count([])
        return super().create(vals_list)

    @api.depends('total_personnel_on_site', 'total_personnel_mustered')
    def _compute_headcount(self):
        for rec in self:
            rec.unaccounted_personnel = max(0, rec.total_personnel_on_site - rec.total_personnel_mustered)

    def action_critique(self):
        self.write({'state': 'critiqued'})

    def action_close(self):
        self.write({'state': 'closed'})


class HSEEmergencyTeam(models.Model):
    _name = 'hse.emergency.team'
    _description = 'Emergency Response Team (ERT) Member & Specialist Role'
    _order = 'role asc, name asc'

    name = fields.Char(string='Member Name', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Link')
    user_id = fields.Many2one('res.users', string='System User Link')
    phone = fields.Char(string='Emergency 24/7 Phone Number', required=True)
    radio_call_sign = fields.Char(string='Emergency Radio UHF Channel / Call Sign', required=True)

    role = fields.Selection([
        ('incident_commander', 'Incident Commander (IC)'),
        ('safety_officer', 'Safety Officer (SO)'),
        ('fire_team_leader', 'Fire Brigade Team Leader'),
        ('firefighter', 'Industrial Firefighter'),
        ('hazmat_technician', 'Hazmat Specialist / Spill Responder'),
        ('first_aid_medic', 'Paramedic / First Aid Specialist'),
        ('search_rescue', 'Search & Rescue / Breathing Apparatus Specialist'),
        ('scribe', 'Crisis Command Scribe'),
    ], string='ERT Role', required=True, default='firefighter')

    scba_certified = fields.Boolean(string='SCBA Breathing Apparatus Certified', default=True)
    last_certification_date = fields.Date(string='Last Live Fire / Hazmat Recertification Date', default=fields.Date.today)
    is_on_call = fields.Boolean(string='Currently On-Call / Ready to Deploy', default=True)
