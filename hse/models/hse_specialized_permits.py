# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# =============================================================================
# 1. Critical Lift & Heavy Rigging Permit
# =============================================================================
class HSEPermitCriticalLift(models.Model):
    _name = 'hse.permit.critical.lift'
    _description = 'Critical Lift Plan & Heavy Rigging Authorization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'lift_date desc, id desc'

    name = fields.Char(string='Lift Plan Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Lift Description & Load Tag', required=True, tracking=True)
    permit_id = fields.Many2one('hse.permit', string='Master Work Permit')
    location_id = fields.Many2one('hse.location.profile', string='Lift Location', required=True)
    lift_date = fields.Date(string='Scheduled Lift Date', default=fields.Date.today, required=True)

    # Crane Specifications
    crane_model = fields.Char(string='Crane Make, Model & Serial # (e.g. Liebherr LTM 1300-6.2)', required=True)
    crane_capacity_tonnes = fields.Float(string='Rated Maximum Crane Capacity (Tonnes)', required=True)
    boom_length_meters = fields.Float(string='Operating Boom Length (Meters)', required=True)
    operating_radius_meters = fields.Float(string='Maximum Operating Radius (Meters)', required=True)

    # Load Details
    net_load_weight_tonnes = fields.Float(string='Net Object Weight (Tonnes)', required=True)
    rigging_tackle_weight_tonnes = fields.Float(string='Rigging Hardware, Block & Ball Weight (Tonnes)', required=True, default=1.5)
    total_gross_load_tonnes = fields.Float(string='Total Gross Load (Tonnes)', compute='_compute_lift_capacity', store=True)
    rated_capacity_at_radius = fields.Float(string='Crane Chart Capacity at Radius (Tonnes)', required=True)
    lift_capacity_percentage = fields.Float(string='Lift Capacity Utilization (%)', compute='_compute_lift_capacity', store=True)

    is_critical_lift = fields.Boolean(string='Critical Lift Classification (> 75% Capacity or Tandem Lift)', compute='_compute_lift_capacity', store=True)
    lift_type = fields.Selection([
        ('single_crane', 'Single Crane Standard Heavy Lift'),
        ('tandem_lift', 'Tandem Two-Crane Engineered Lift'),
        ('over_live_plant', 'Lifting Over Live Hydrocarbon Process Equipment'),
        ('blind_lift', 'Blind Lift (Radio / Camera Directed)'),
    ], string='Lift Category', default='single_crane', required=True)

    # Safety Controls
    max_allowable_wind_speed_knots = fields.Float(string='Maximum Allowable Wind Speed (Knots)', default=15.0)
    measured_wind_speed_knots = fields.Float(string='Measured Wind Speed at Boom Tip (Knots)', default=5.0)
    outrigger_mats_verified = fields.Boolean(string='Outrigger Timber/Steel Spreader Mats Verified', default=True)
    ground_bearing_capacity_verified = fields.Boolean(string='Soil / Ground Bearing Pressure Capacity Verified', default=True)
    exclusion_zone_barricaded = fields.Boolean(string='360-Degree Swing Radius Exclusion Zone Barricaded', default=True)

    rigging_engineer_id = fields.Many2one('res.users', string='Certified Rigging Engineer / Appointed Person', required=True)
    crane_operator_id = fields.Many2one('res.users', string='Certified Crane Operator', required=True)

    state = fields.Selection([
        ('draft', 'Engineering Draft'),
        ('approved', 'Approved by Rigging Engineer & HSE'),
        ('active', 'Lift Authorized & Underway'),
        ('completed', 'Lift Completed Safely'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.permit.critical.lift') or _('LIFT-%04d') % self.env['hse.permit.critical.lift'].search_count([])
        return super().create(vals_list)

    @api.depends('net_load_weight_tonnes', 'rigging_tackle_weight_tonnes', 'rated_capacity_at_radius')
    def _compute_lift_capacity(self):
        for rec in self:
            gross = (rec.net_load_weight_tonnes or 0.0) + (rec.rigging_tackle_weight_tonnes or 0.0)
            rec.total_gross_load_tonnes = gross
            chart = rec.rated_capacity_at_radius or 1.0
            pct = round((gross / chart) * 100.0, 1)
            rec.lift_capacity_percentage = pct
            rec.is_critical_lift = (pct >= 75.0 or rec.lift_type == 'tandem_lift' or rec.lift_type == 'over_live_plant')

    def action_approve(self):
        if self.lift_capacity_percentage > 95.0:
            raise UserError(_("Lift capacity utilization exceeds 95% safety margin! Re-rig with larger crane capacity."))
        self.write({'state': 'approved'})

    def action_start(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})


# =============================================================================
# 2. Excavation & Trenching Safety Permit (OSHA 1926 Subpart P)
# =============================================================================
class HSEPermitExcavation(models.Model):
    _name = 'hse.permit.excavation'
    _description = 'Excavation & Trenching Safety Permit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(string='Excavation Permit Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Excavation Scope & Purpose', required=True, tracking=True)
    permit_id = fields.Many2one('hse.permit', string='Master PTW Permit')
    location_id = fields.Many2one('hse.location.profile', string='Plant Area', required=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.today, required=True)
    expected_completion = fields.Date(string='Expected Backfill Date', required=True)

    # Dimensions
    excavation_length_m = fields.Float(string='Length (Meters)', default=10.0, required=True)
    excavation_width_m = fields.Float(string='Width (Meters)', default=3.0, required=True)
    excavation_depth_m = fields.Float(string='Depth (Meters)', default=1.8, required=True)

    # Soil Classification
    soil_type = fields.Selection([
        ('stable_rock', 'Solid Stable Rock (Vertical Walls Acceptable)'),
        ('type_a', 'Type A Soil (Clay, Silty Clay - Compressive Strength >= 1.5 tsf)'),
        ('type_b', 'Type B Soil (Silt, Sandy Loam, Previously Disturbed - 0.5 to 1.5 tsf)'),
        ('type_c', 'Type C Soil (Gravel, Sand, Submerged Soil - < 0.5 tsf)'),
    ], string='OSHA Soil Classification', default='type_b', required=True)

    # Protective Systems (> 1.2m / 4 ft mandatory)
    protective_system = fields.Selection([
        ('sloping_benching', 'Sloping / Benching (Angled Side Cuts)'),
        ('hydraulic_shoring', 'Hydraulic Aluminum Shoring Cylinders'),
        ('trench_box', 'Certified Steel Trench Box / Shield'),
        ('none_shallow', 'None Required (Depth < 1.2m and no cave-in hazard)'),
    ], string='Cave-in Protective System', default='hydraulic_shoring', required=True)

    # Underground Utility Clearances
    call_811_ticket_number = fields.Char(string='One-Call / 811 Underground Utility Ticket #', required=True)
    utility_scan_conducted = fields.Boolean(string='Ground Penetrating Radar (GPR) / Cable Locator Scan Completed', default=True)
    hand_digging_only = fields.Boolean(string='Potholing / Hand Digging Mandatory Within 1m of Known Utilities', default=True)

    # Safe Access / Egress (Ladder within 25 ft / 7.5m)
    ladder_access_verified = fields.Boolean(string='Safe Ladders Installed within 7.5m (25 ft) of all Workers', default=True)
    spoil_pile_setback_verified = fields.Boolean(string='Spoil Pile & Equipment Setback >= 0.6m (2 ft) from Lip', default=True)
    atmospheric_testing_required = fields.Boolean(string='Atmospheric Testing Required (Depth > 1.2m or Near Hydrocarbon Lines)', default=True)

    competent_person_id = fields.Many2one('res.users', string='OSHA Competent Person (Excavations)', required=True)

    state = fields.Selection([
        ('draft', 'Draft Clearance'),
        ('inspected', 'Inspected by Competent Person'),
        ('authorized', 'Excavation Authorized & Open'),
        ('backfilled', 'Backfilled & Restored'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.permit.excavation') or _('EXC-%04d') % self.env['hse.permit.excavation'].search_count([])
        return super().create(vals_list)

    def action_inspect(self):
        self.write({'state': 'inspected'})

    def action_authorize(self):
        self.write({'state': 'authorized'})

    def action_backfill(self):
        self.write({'state': 'backfilled'})


# =============================================================================
# 3. Industrial Radiography & NDT Permit
# =============================================================================
class HSEPermitRadiography(models.Model):
    _name = 'hse.permit.radiography'
    _description = 'Industrial Radiography & Non-Destructive Testing Permit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'shoot_datetime desc, id desc'

    name = fields.Char(string='Radiography Permit Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Radiography Inspection Scope (e.g. Weld X-Ray on Pipe Spool)', required=True, tracking=True)
    permit_id = fields.Many2one('hse.permit', string='Master PTW Permit')
    location_id = fields.Many2one('hse.location.profile', string='Plant Unit', required=True)
    shoot_datetime = fields.Datetime(string='Scheduled Shoot Time (Typically Night Shift)', default=fields.Datetime.now, required=True)

    # Radiation Source Details
    source_type = fields.Selection([
        ('ir192', 'Iridium-192 (Ir-192 Gamma Source)'),
        ('co60', 'Cobalt-60 (Co-60 High Energy Gamma Source)'),
        ('se75', 'Selenium-75 (Se-75 Gamma Source)'),
        ('xray_tube', 'Electronic Industrial X-Ray Generator'),
    ], string='Radiation Source Type', default='ir192', required=True)

    source_serial_no = fields.Char(string='Source Capsule / Camera Serial #', required=True)
    activity_curies = fields.Float(string='Current Source Activity (Curies / Ci)', required=True, default=45.0)

    # Controlled Boundary Calculation
    controlled_boundary_radius_m = fields.Float(string='Calculated 20 µSv/h Radiation Exclusion Radius (Meters)', compute='_compute_boundary', store=True)
    flashing_beacons_erected = fields.Boolean(string='Flashing Amber/Red Beacons & Danger Radiation Signs Posted', default=True)
    sentry_personnel_posted = fields.Boolean(string='Continuous Sentry Guards Posted at all Access Ways', default=True)
    survey_meter_calibrated = fields.Boolean(string='Calibrated Radiation Survey Meter Verified & Operational', default=True)

    radiation_protection_officer_id = fields.Many2one('res.users', string='Certified Radiation Protection Officer (RPO)', required=True)
    radiographer_name = fields.Char(string='Certified Radiographer Level II / III', required=True)

    state = fields.Selection([
        ('draft', 'Prepared'),
        ('approved', 'Approved by RPO'),
        ('shooting', 'Active Exposure in Progress (Sentry On Duty)'),
        ('source_secured', 'Source Safely Retracted in Pig & Surveyed Zero (Closed)'),
    ], string='Permit Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.permit.radiography') or _('RAD-%04d') % self.env['hse.permit.radiography'].search_count([])
        return super().create(vals_list)

    @api.depends('source_type', 'activity_curies')
    def _compute_boundary(self):
        for rec in self:
            # Radiation constant: Ir-192 = 0.48 R-m2/h-Ci. Safe boundary = 2 mR/h (20 uSv/h).
            curies = rec.activity_curies or 1.0
            if rec.source_type == 'ir192':
                radius = round(( (0.48 * curies) / 0.002 ) ** 0.5, 1)
            elif rec.source_type == 'co60':
                radius = round(( (1.30 * curies) / 0.002 ) ** 0.5, 1)
            else:
                radius = round(( (0.20 * curies) / 0.002 ) ** 0.5, 1)
            rec.controlled_boundary_radius_m = radius

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_start_shoot(self):
        self.write({'state': 'shooting'})

    def action_secure_source(self):
        self.write({'state': 'source_secured'})
