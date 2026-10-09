# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import math

class HseDispersionScenario(models.Model):
    _name = 'hse.dispersion.scenario'
    _description = 'Chemical Dispersion & Quantitative Consequence Scenario'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Scenario Title', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Location / Asset', required=True)
    sds_id = fields.Many2one('hse.sds', string='Safety Data Sheet (SDS)')

    chemical_name = fields.Char(string='Chemical / Hydrocarbon Name', required=True, default='Propane')
    molecular_weight = fields.Float(string='Molecular Weight (g/mol)', default=44.1)
    boiling_point_c = fields.Float(string='Boiling Point (°C)', default=-42.1)
    vapor_pressure_kpa = fields.Float(string='Vapor Pressure at 25°C (kPa)', default=950.0)

    release_phase = fields.Selection([
        ('gas', 'Gas / Vapor'),
        ('liquid', 'Pressurized Liquid'),
        ('two_phase', 'Two-Phase Flashing Jet'),
    ], string='Release Phase', default='two_phase', required=True)

    release_type = fields.Selection([
        ('instantaneous_puff', 'Catastrophic Rupture (Instantaneous Puff)'),
        ('continuous_plume', 'Continuous Pipeline / Pinhole Leak (Plume)'),
        ('pool_fire', 'Hydrocarbon Pool Fire'),
        ('jet_fire', 'High-Pressure Gas Jet Fire'),
        ('vce_explosion', 'Vapor Cloud Explosion (VCE)'),
    ], string='Consequence Type', default='continuous_plume', required=True)

    total_mass_kg = fields.Float(string='Inventory Mass (kg)', default=5000.0)
    release_rate_kg_s = fields.Float(string='Release Rate (kg/s)', default=15.0)

    # Meteorological Conditions
    wind_speed_m_s = fields.Float(string='Wind Speed (m/s)', default=3.0, required=True)
    wind_direction_deg = fields.Integer(string='Wind Direction (°)', default=180,
                                        help='0=North, 90=East, 180=South, 270=West')
    stability_class = fields.Selection([
        ('a', 'A - Extremely Unstable (Strong Sun, Low Wind)'),
        ('b', 'B - Moderately Unstable'),
        ('c', 'C - Slightly Unstable'),
        ('d', 'D - Neutral (Overcast / High Wind)'),
        ('e', 'E - Slightly Stable (Night, Light Cloud)'),
        ('f', 'F - Moderately Stable (Night, Clear Sky, Low Wind)'),
    ], string='Pasquill-Gifford Stability Class', default='d', required=True)
    ambient_temp_c = fields.Float(string='Ambient Temp (°C)', default=25.0)
    relative_humidity_pct = fields.Float(string='Relative Humidity (%)', default=65.0)

    # Toxic Endpoints (ppm)
    erpg_3_ppm = fields.Float(string='ERPG-3 / AEGL-3 (Life Threatening ppm)', default=100.0)
    erpg_2_ppm = fields.Float(string='ERPG-2 / AEGL-2 (Irreversible Effects ppm)', default=30.0)
    erpg_1_ppm = fields.Float(string='ERPG-1 / AEGL-1 (Odor / Mild Irritation ppm)', default=5.0)

    # Flammable Limits (%)
    lfl_percent = fields.Float(string='Lower Flammable Limit (LFL %)', default=2.1)

    # Computed Dispersion Hazard Distances (Meters downwind)
    erpg_3_dist_m = fields.Float(string='ERPG-3 Red Danger Zone (m)', compute='_compute_dispersion_footprint', store=True)
    erpg_2_dist_m = fields.Float(string='ERPG-2 Orange Warning Zone (m)', compute='_compute_dispersion_footprint', store=True)
    erpg_1_dist_m = fields.Float(string='ERPG-1 Yellow Advisory Zone (m)', compute='_compute_dispersion_footprint', store=True)

    lfl_100_dist_m = fields.Float(string='100% LFL Flammable Cloud Distance (m)', compute='_compute_dispersion_footprint', store=True)
    lfl_50_dist_m = fields.Float(string='50% LFL Flammable Safety Margin (m)', compute='_compute_dispersion_footprint', store=True)

    # Thermal Radiation Hazard Zones (Meters)
    rad_37_5_kw_m = fields.Float(string='37.5 kW/m² Radius (Equipment Destruction)', compute='_compute_dispersion_footprint', store=True)
    rad_12_5_kw_m = fields.Float(string='12.5 kW/m² Radius (Fatal in 60s)', compute='_compute_dispersion_footprint', store=True)
    rad_4_7_kw_m = fields.Float(string='4.7 kW/m² Radius (Pain in 15-20s)', compute='_compute_dispersion_footprint', store=True)
    rad_1_6_kw_m = fields.Float(string='1.6 kW/m² Radius (Safe Continuous Exposure)', compute='_compute_dispersion_footprint', store=True)

    # Blast Overpressure Zones (Meters)
    blast_10_psi_m = fields.Float(string='10 psi Blast Radius (Heavy Structural Collapse)', compute='_compute_dispersion_footprint', store=True)
    blast_3_psi_m = fields.Float(string='3 psi Blast Radius (Moderate Wall Failure)', compute='_compute_dispersion_footprint', store=True)
    blast_1_psi_m = fields.Float(string='1 psi Blast Radius (Window Shatter / Injury)', compute='_compute_dispersion_footprint', store=True)

    recommended_evacuation_radius_m = fields.Float(string='Public Evacuation Exclusion Radius (m)',
                                                  compute='_compute_dispersion_footprint', store=True)
    shelter_in_place_instructions = fields.Text(string='Shelter-In-Place Protocol',
                                                default='Immediate shutdown of all HVAC air intakes; close exterior doors and seal windows; assemble in interior control room.')

    state = fields.Selection([
        ('draft', 'Draft Modeling'),
        ('modeled', 'Simulation Complete'),
        ('verified', 'Verified by Process Safety Lead'),
        ('active_emergency', 'Active Scenario in Emergency Response'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('release_type', 'release_rate_kg_s', 'total_mass_kg', 'wind_speed_m_s', 'stability_class',
                 'erpg_3_ppm', 'erpg_2_ppm', 'erpg_1_ppm', 'lfl_percent')
    def _compute_dispersion_footprint(self):
        # Atmospheric stability dispersion coefficient multiplier
        stab_factors = {'a': 0.6, 'b': 0.8, 'c': 1.0, 'd': 1.25, 'e': 1.6, 'f': 2.1}
        for rec in self:
            u = max(rec.wind_speed_m_s or 3.0, 0.5)
            s_mult = stab_factors.get(rec.stability_class, 1.25)
            q_rate = max(rec.release_rate_kg_s or 10.0, 0.1)
            mass = max(rec.total_mass_kg or 1000.0, 1.0)

            # Plume Toxic dispersion approximations
            if rec.erpg_3_ppm > 0:
                rec.erpg_3_dist_m = round(math.sqrt(q_rate * 5000.0 / (u * rec.erpg_3_ppm)) * s_mult, 1)
            else:
                rec.erpg_3_dist_m = 0.0

            if rec.erpg_2_ppm > 0:
                rec.erpg_2_dist_m = round(math.sqrt(q_rate * 15000.0 / (u * rec.erpg_2_ppm)) * s_mult, 1)
            else:
                rec.erpg_2_dist_m = 0.0

            if rec.erpg_1_ppm > 0:
                rec.erpg_1_dist_m = round(math.sqrt(q_rate * 35000.0 / (u * rec.erpg_1_ppm)) * s_mult, 1)
            else:
                rec.erpg_1_dist_m = 0.0

            # Flammable vapor dispersion
            lfl = max(rec.lfl_percent or 2.0, 0.5)
            rec.lfl_100_dist_m = round(math.sqrt(q_rate * 4500.0 / (u * lfl * 100)) * s_mult, 1)
            rec.lfl_50_dist_m = round(rec.lfl_100_dist_m * 1.55, 1)

            # Thermal radiation (Pool/Jet fire based on heat release rate)
            # Radiant heat Q_rad ~ 0.3 * m_dot * Hc
            pool_factor = math.sqrt(q_rate * 120.0)
            rec.rad_37_5_kw_m = round(pool_factor * 2.2, 1)
            rec.rad_12_5_kw_m = round(pool_factor * 3.8, 1)
            rec.rad_4_7_kw_m = round(pool_factor * 6.2, 1)
            rec.rad_1_6_kw_m = round(pool_factor * 10.5, 1)

            # Vapor Cloud Explosion Overpressure (TNT Equivalent W_tnt = mass * 0.1 * 46/4.68)
            tnt_equiv = mass * 0.1 * 9.8
            tnt_cbrt = (tnt_equiv) ** (1.0 / 3.0)
            rec.blast_10_psi_m = round(tnt_cbrt * 3.8, 1)
            rec.blast_3_psi_m = round(tnt_cbrt * 6.5, 1)
            rec.blast_1_psi_m = round(tnt_cbrt * 14.2, 1)

            # Evacuation radius is the envelope maximum of key hazards
            rec.recommended_evacuation_radius_m = max(
                rec.erpg_2_dist_m,
                rec.lfl_50_dist_m,
                rec.rad_4_7_kw_m,
                rec.blast_1_psi_m,
                100.0
            )

    def action_model(self):
        self._compute_dispersion_footprint()
        self.write({'state': 'modeled'})

    def action_verify(self):
        self.write({'state': 'verified'})

    def action_activate_emergency(self):
        self.write({'state': 'active_emergency'})
