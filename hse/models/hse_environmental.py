# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta

# =============================================================================
# 1. Air Emissions & Greenhouse Gas (GHG) Accounting
# =============================================================================
class HSEEnvAirEmission(models.Model):
    _name = 'hse.env.air.emission'
    _description = 'Air Emissions & Greenhouse Gas (GHG) Monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reporting_date desc, id desc'

    name = fields.Char(string='Emission Log Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    reporting_date = fields.Date(string='Monitoring Date', default=fields.Date.today, required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Emission Source / Plant', required=True)
    emission_point = fields.Char(string='Stack / Flare / Source Identifier (e.g. Flare FL-101, Boiler B-201)', required=True)

    scope = fields.Selection([
        ('scope1', 'Scope 1: Direct Emissions (Boilers, Furnaces, Flares, Fugitives)'),
        ('scope2', 'Scope 2: Indirect Emissions (Purchased Electricity & Steam)'),
        ('scope3', 'Scope 3: Value Chain (Logistics, Purchased Goods, Waste Disposal)'),
    ], string='GHG Scope Protocol', default='scope1', required=True)

    source_type = fields.Selection([
        ('stationary_combustion', 'Stationary Combustion (Fuel Gas / Diesel)'),
        ('flare', 'Process Flaring & Emergency Relief'),
        ('fugitive', 'Fugitive Component Leaks (Valves, Flanges, Seals)'),
        ('venting', 'Process Purge & Tank Venting'),
        ('cems', 'Continuous Emission Monitoring System (CEMS Stream)'),
    ], string='Emission Source Category', default='stationary_combustion', required=True)

    # Activity Data
    fuel_type = fields.Char(string='Fuel / Gas Type (Natural Gas, Refinery Off-gas, Diesel)')
    fuel_consumed = fields.Float(string='Fuel / Volume Consumed', default=0.0)
    fuel_unit = fields.Selection([
        ('mmbtu', 'MMBtu'),
        ('scf', 'Standard Cubic Feet (scf)'),
        ('nm3', 'Normal Cubic Meters (Nm³)'),
        ('liters', 'Liters'),
        ('kg', 'Kilograms'),
    ], string='Unit of Measure', default='scf')

    # Calculated Greenhouse Gases (Metric Tonnes)
    co2_tonnes = fields.Float(string='CO₂ Emitted (Metric Tonnes)', compute='_compute_emissions', store=True)
    ch4_tonnes = fields.Float(string='CH₄ Emitted (Metric Tonnes)', compute='_compute_emissions', store=True)
    n2o_tonnes = fields.Float(string='N₂O Emitted (Metric Tonnes)', compute='_compute_emissions', store=True)
    co2e_tonnes = fields.Float(string='Total CO₂e (Carbon Equivalent Tonnes)', compute='_compute_emissions', store=True)

    # Criteria Air Pollutants (kg)
    nox_kg = fields.Float(string='Nitrogen Oxides (NOₓ kg)', default=0.0)
    sox_kg = fields.Float(string='Sulfur Oxides (SOₓ kg)', default=0.0)
    voc_kg = fields.Float(string='Volatile Organic Compounds (VOC kg)', default=0.0)
    pm10_kg = fields.Float(string='Particulate Matter (PM₁₀ kg)', default=0.0)

    permit_limit_exceeded = fields.Boolean(string='Regulatory Permit Limit Exceeded', default=False, tracking=True)
    exceedance_notes = fields.Text(string='Exceedance Investigation & Regulatory Notification Details')

    state = fields.Selection([
        ('draft', 'Draft Entry'),
        ('calculated', 'GHG Computed'),
        ('verified', 'Third-Party / Internal Audit Verified'),
        ('reported', 'Reported to Environmental Agency'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.env.air.emission') or _('GHG-%05d') % self.env['hse.env.air.emission'].search_count([])
        return super().create(vals_list)

    @api.depends('fuel_consumed', 'source_type', 'fuel_unit')
    def _compute_emissions(self):
        # Standard EPA / IPCC emission factors (simplified for natural gas / fuel combustion)
        for rec in self:
            qty = rec.fuel_consumed or 0.0
            if qty > 0:
                # E.g., ~0.000055 tonnes CO2 per scf of fuel gas
                rec.co2_tonnes = round(qty * 0.0000544, 3)
                rec.ch4_tonnes = round(qty * 0.000000001, 5)
                rec.n2o_tonnes = round(qty * 0.0000000001, 6)
                # GWP: CH4=28, N2O=265
                rec.co2e_tonnes = round(rec.co2_tonnes + (rec.ch4_tonnes * 28) + (rec.n2o_tonnes * 265), 3)
            else:
                rec.co2_tonnes = 0.0
                rec.ch4_tonnes = 0.0
                rec.n2o_tonnes = 0.0
                rec.co2e_tonnes = 0.0

    def action_verify(self):
        self.write({'state': 'verified'})

    def action_report(self):
        self.write({'state': 'reported'})


# =============================================================================
# 2. Wastewater & Effluent Quality Monitoring
# =============================================================================
class HSEEnvWaterMonitoring(models.Model):
    _name = 'hse.env.water.monitoring'
    _description = 'Industrial Wastewater & Effluent Quality Monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sample_datetime desc, id desc'

    name = fields.Char(string='Water Sample Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    location_id = fields.Many2one('hse.location.profile', string='Sampling Facility / Outfall Point', required=True)
    outfall_number = fields.Char(string='Outfall / Discharge Point ID (e.g. Outfall-001 Stormwater, Outfall-002 ETP)', required=True)
    sample_datetime = fields.Datetime(string='Sampling Date & Time', default=fields.Datetime.now, required=True)
    sampled_by = fields.Many2one('res.users', string='Sampler', default=lambda self: self.env.user)
    lab_reference = fields.Char(string='Accredited Analytical Lab Report #')

    # Water Quality Parameters
    ph_level = fields.Float(string='pH (Safe Limit: 6.0 - 9.0)', default=7.2, required=True)
    temperature_c = fields.Float(string='Discharge Temperature (°C)', default=25.0)
    flow_rate_m3_day = fields.Float(string='Discharge Flow Rate (m³/day)', default=1200.0)

    bod_mg_l = fields.Float(string='Biological Oxygen Demand BOD₅ (mg/L)', default=18.0)
    cod_mg_l = fields.Float(string='Chemical Oxygen Demand COD (mg/L)', default=45.0)
    tss_mg_l = fields.Float(string='Total Suspended Solids TSS (mg/L)', default=22.0)
    oil_grease_mg_l = fields.Float(string='Oil & Grease (mg/L - Limit < 10)', default=2.5)
    ammonia_n_mg_l = fields.Float(string='Ammonia Nitrogen NH₃-N (mg/L)', default=1.2)
    heavy_metals_ppm = fields.Float(string='Total Heavy Metals (ppm)', default=0.05)

    is_compliant = fields.Boolean(string='Within Discharge Permit Limits', compute='_compute_compliance', store=True)
    exceedance_parameters = fields.Char(string='Parameters in Violation', compute='_compute_compliance', store=True)

    state = fields.Selection([
        ('draft', 'Sample Logged'),
        ('analyzed', 'Lab Results Entered'),
        ('compliant', 'Permit Compliant'),
        ('exceedance', 'Exceedance Violation Alert'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.env.water.monitoring') or _('H2O-%05d') % self.env['hse.env.water.monitoring'].search_count([])
        return super().create(vals_list)

    @api.depends('ph_level', 'bod_mg_l', 'cod_mg_l', 'tss_mg_l', 'oil_grease_mg_l')
    def _compute_compliance(self):
        for rec in self:
            violations = []
            if not (6.0 <= rec.ph_level <= 9.0):
                violations.append(f"pH ({rec.ph_level})")
            if rec.bod_mg_l > 30.0:
                violations.append(f"BOD ({rec.bod_mg_l} mg/L)")
            if rec.cod_mg_l > 125.0:
                violations.append(f"COD ({rec.cod_mg_l} mg/L)")
            if rec.tss_mg_l > 50.0:
                violations.append(f"TSS ({rec.tss_mg_l} mg/L)")
            if rec.oil_grease_mg_l > 10.0:
                violations.append(f"Oil & Grease ({rec.oil_grease_mg_l} mg/L)")

            if violations:
                rec.is_compliant = False
                rec.exceedance_parameters = ", ".join(violations)
                rec.state = 'exceedance'
            else:
                rec.is_compliant = True
                rec.exceedance_parameters = 'None (Fully Compliant)'
                rec.state = 'compliant'


# =============================================================================
# 3. Hazardous Waste Manifest Tracking (EPA RCRA Cradle-to-Grave)
# =============================================================================
class HSEEnvWasteManifest(models.Model):
    _name = 'hse.env.waste.manifest'
    _description = 'EPA RCRA Industrial Hazardous Waste Manifest Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'shipment_date desc, id desc'

    name = fields.Char(string='Manifest Tracking #', required=True, copy=False, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Generating Facility', required=True)
    generator_epa_id = fields.Char(string='Generator EPA ID Number', required=True)
    waste_type = fields.Selection([
        ('hazardous', 'EPA RCRA Hazardous Waste'),
        ('universal', 'Universal Waste (Batteries, Lamps, Mercury)'),
        ('non_hazardous', 'Non-Hazardous Industrial Waste'),
        ('medical', 'Biohazard / Medical Sharps'),
    ], string='Regulatory Category', default='hazardous', required=True)

    waste_description = fields.Char(string='DOT Proper Shipping Name & Waste Description', required=True)
    epa_waste_codes = fields.Char(string='EPA Waste Codes (e.g. D001, D008, F003)', required=True)
    container_type = fields.Selection([
        ('dm', 'Drums (DM)'),
        ('tt', 'Tank Trucks (TT)'),
        ('cm', 'Metal Boxes (CM)'),
        ('totes', 'Intermediate Bulk Totes (IBC)'),
        ('roll_off', 'Roll-off Containers'),
    ], string='Container Type', default='dm', required=True)

    container_count = fields.Integer(string='Number of Containers', default=1, required=True)
    total_quantity = fields.Float(string='Total Weight / Volume', required=True)
    unit_of_measure = fields.Selection([
        ('kg', 'Kilograms'),
        ('pounds', 'Pounds (lbs)'),
        ('tonnes', 'Metric Tonnes'),
        ('gallons', 'Gallons'),
    ], string='Unit', default='kg', required=True)

    # 90-Day Storage Clock (Large Quantity Generators)
    accumulation_start_date = fields.Date(string='Accumulation Start Date', default=fields.Date.today, required=True)
    storage_limit_deadline = fields.Date(string='90-Day Legal Storage Deadline', compute='_compute_storage_deadline', store=True)
    storage_days_remaining = fields.Integer(string='Days Remaining in Storage', compute='_compute_storage_deadline', store=True)

    # Transporter & TSDF Facility
    transporter_company = fields.Char(string='Certified Transporter Company Name', required=True)
    transporter_epa_id = fields.Char(string='Transporter EPA ID', required=True)
    shipment_date = fields.Date(string='Date Shipped Off-Site', tracking=True)

    tsdf_facility_name = fields.Char(string='Designated TSDF Facility (Disposal Site)', required=True)
    tsdf_epa_id = fields.Char(string='TSDF EPA ID', required=True)
    management_method = fields.Selection([
        ('incineration', 'High-Temp Thermal Incineration'),
        ('landfill', 'Class 1 Hazardous Waste Landfill'),
        ('recycling', 'Fuel Blending / Solvent Recovery'),
        ('treatment', 'Chemical Neutralization / Solidification'),
    ], string='Treatment & Disposal Method', default='incineration', required=True)

    certificate_of_disposal_received = fields.Boolean(string='Certificate of Final Destruction Received', default=False, tracking=True)
    certificate_date = fields.Date(string='Date Destruction Certified')

    state = fields.Selection([
        ('storage', 'In On-Site Storage (Clock Running)'),
        ('manifested', 'Manifest Signed & Shipped'),
        ('in_transit', 'In Transit to TSDF'),
        ('accepted', 'Accepted at TSDF'),
        ('destroyed', 'Cradle-to-Grave Complete (Certified)'),
    ], string='Manifest Status', default='storage', tracking=True)

    @api.depends('accumulation_start_date')
    def _compute_storage_deadline(self):
        today = fields.Date.today()
        for rec in self:
            if rec.accumulation_start_date:
                deadline = rec.accumulation_start_date + timedelta(days=90)
                rec.storage_limit_deadline = deadline
                rec.storage_days_remaining = (deadline - today).days
            else:
                rec.storage_limit_deadline = False
                rec.storage_days_remaining = 0

    def action_ship(self):
        self.write({'state': 'in_transit', 'shipment_date': fields.Date.today()})

    def action_tsdf_accept(self):
        self.write({'state': 'accepted'})

    def action_certify_destruction(self):
        self.write({
            'state': 'destroyed',
            'certificate_of_disposal_received': True,
            'certificate_date': fields.Date.today(),
        })


# =============================================================================
# 4. Chemical Spill & Environmental Release Remediation
# =============================================================================
class HSEEnvSpill(models.Model):
    _name = 'hse.env.spill'
    _description = 'Chemical / Hydrocarbon Spill & Environmental Remediation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'spill_datetime desc, id desc'

    name = fields.Char(string='Spill Incident Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Spill Title', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Facility / Area', required=True)
    spill_datetime = fields.Datetime(string='Spill Time', default=fields.Datetime.now, required=True, tracking=True)

    substance_name = fields.Char(string='Spilled Material (e.g. Light Crude Oil, Caustic Soda)', required=True)
    cas_number = fields.Char(string='CAS Registry Number')
    media_impacted = fields.Selection([
        ('secondary_containment', 'Secondary Containment / Concrete Bund (No Ground Impact)'),
        ('soil', 'Unpaved Ground / Soil Contamination'),
        ('water_body', 'Surface Water / River / Marine Environment'),
        ('groundwater', 'Groundwater Aquifer'),
    ], string='Impacted Environmental Media', default='secondary_containment', required=True)

    spill_source = fields.Selection([
        ('pipe_rupture', 'Pipeline / Flange Rupture'),
        ('tank_overflow', 'Atmospheric Tank Overflow'),
        ('drum_leak', 'Drum Puncture / Handling Mishap'),
        ('truck_rollover', 'Road Tanker Loading / Unloading'),
        ('equipment_seal', 'Pump / Compressor Mechanical Seal Failure'),
    ], string='Source of Release', default='pipe_rupture', required=True)

    volume_released = fields.Float(string='Estimated Volume Released', required=True)
    volume_recovered = fields.Float(string='Volume Successfully Recovered', default=0.0)
    unit_of_measure = fields.Selection([
        ('liters', 'Liters'),
        ('barrels', 'Barrels (bbl)'),
        ('gallons', 'Gallons'),
        ('kg', 'Kilograms'),
    ], string='Unit', default='liters', required=True)

    recovery_percentage = fields.Float(string='Recovery Efficiency (%)', compute='_compute_recovery', store=True)

    # Regulatory Reporting
    cercla_rq = fields.Float(string='CERCLA Reportable Quantity (RQ)', default=100.0)
    is_reportable = fields.Boolean(string='National Response Center (NRC) Reportable', compute='_compute_reportable', store=True)
    nrc_incident_number = fields.Char(string='NRC / Regulatory Agency Report Number')

    containment_measures = fields.Text(string='Immediate Containment (Booms, Absorbents, Vacuum Trucks)', required=True)
    remediation_plan = fields.Text(string='Long-Term Soil/Water Remediation & Bioremediation Plan')

    state = fields.Selection([
        ('active', 'Spill Active / Containment in Progress'),
        ('contained', 'Contained & Stopped'),
        ('recovering', 'Vacuuming & Excavation Active'),
        ('remediated', 'Site Restored & Sampling Verified Clean'),
        ('closed', 'Regulatory Closure Endorsed'),
    ], string='Remediation Lifecycle', default='active', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.env.spill') or _('SPILL-%04d') % self.env['hse.env.spill'].search_count([])
        return super().create(vals_list)

    @api.depends('volume_released', 'volume_recovered')
    def _compute_recovery(self):
        for rec in self:
            if rec.volume_released and rec.volume_released > 0:
                rec.recovery_percentage = round((rec.volume_recovered / rec.volume_released) * 100.0, 1)
            else:
                rec.recovery_percentage = 0.0

    @api.depends('volume_released', 'cercla_rq')
    def _compute_reportable(self):
        for rec in self:
            rec.is_reportable = bool(rec.volume_released and rec.cercla_rq and rec.volume_released >= rec.cercla_rq)

    def action_contain(self):
        self.write({'state': 'contained'})

    def action_start_recovery(self):
        self.write({'state': 'recovering'})

    def action_remediate(self):
        self.write({'state': 'remediated'})

    def action_close(self):
        self.write({'state': 'closed'})
