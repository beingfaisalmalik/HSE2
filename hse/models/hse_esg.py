# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HseEsgAccounting(models.Model):
    _name = 'hse.esg.accounting'
    _description = 'ESG Carbon Accounting & Environmental Resource Balance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reporting_year desc, reporting_period desc'

    name = fields.Char(string='Report Reference', required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('hse.esg.accounting') or _('New'))
    reporting_year = fields.Integer(string='Reporting Year', default=lambda self: fields.Date.context_today(self).year, required=True)
    reporting_period = fields.Selection([
        ('annual', 'Full Calendar Year'),
        ('q1', 'Quarter 1 (Jan - Mar)'),
        ('q2', 'Quarter 2 (Apr - Jun)'),
        ('q3', 'Quarter 3 (Jul - Sep)'),
        ('q4', 'Quarter 4 (Oct - Dec)'),
    ], string='Reporting Period', default='annual', required=True)

    location_id = fields.Many2one('hse.location.profile', string='Facility / Operating Unit', required=True)

    # Scope 1 Direct GHG Emissions (Metric Tonnes CO2e)
    scope1_fuel_gas_tonnes = fields.Float(string='Stationary Fuel Gas Combustion (tCO₂e)', default=12500.0)
    scope1_diesel_tonnes = fields.Float(string='Mobile Fleet & Generators Diesel (tCO₂e)', default=850.0)
    scope1_flaring_tonnes = fields.Float(string='Process Flaring & Venting (tCO₂e)', default=3200.0)
    scope1_fugitive_tonnes = fields.Float(string='Fugitive Component Leaks (LDAR) (tCO₂e)', default=450.0)
    total_scope1_co2e = fields.Float(string='Total Scope 1 Emissions (tCO₂e)', compute='_compute_ghg_totals', store=True)

    # Scope 2 Indirect GHG Emissions (Purchased Electricity)
    electricity_consumed_mwh = fields.Float(string='Purchased Grid Electricity (MWh)', default=45000.0)
    grid_emission_factor_kg_kwh = fields.Float(string='Grid Emission Factor (kg CO₂e/kWh)', default=0.42)
    renewable_energy_recs_mwh = fields.Float(string='Renewable Energy Certificates / PPAs (MWh)', default=15000.0)
    scope2_location_based_co2e = fields.Float(string='Scope 2 (Location-Based) (tCO₂e)', compute='_compute_ghg_totals', store=True)
    scope2_market_based_co2e = fields.Float(string='Scope 2 (Market-Based) (tCO₂e)', compute='_compute_ghg_totals', store=True)

    # Scope 3 Value Chain Emissions (GHG Protocol Corporate Standard)
    scope3_cat1_purchased_goods = fields.Float(string='Cat 1: Raw Materials & Chemicals (tCO₂e)', default=8500.0)
    scope3_cat3_fuel_energy = fields.Float(string='Cat 3: Well-to-Tank Upstream Fuels (tCO₂e)', default=2100.0)
    scope3_cat4_logistics = fields.Float(string='Cat 4: Upstream Product Logistics (tCO₂e)', default=3400.0)
    scope3_cat5_waste = fields.Float(string='Cat 5: Waste Sent for Treatment (tCO₂e)', default=650.0)
    scope3_cat6_travel = fields.Float(string='Cat 6: Corporate Business Travel (tCO₂e)', default=120.0)
    scope3_cat7_commuting = fields.Float(string='Cat 7: Employee Daily Commuting (tCO₂e)', default=480.0)
    total_scope3_co2e = fields.Float(string='Total Scope 3 Emissions (tCO₂e)', compute='_compute_ghg_totals', store=True)

    # Carbon Offsets & Net Footprint
    total_gross_ghg_co2e = fields.Float(string='Total Gross GHG Inventory (tCO₂e)', compute='_compute_ghg_totals', store=True)
    carbon_credits_purchased_t = fields.Float(string='Verified Carbon Offsets / Credits (tCO₂e)', default=2500.0)
    carbon_capture_storage_t = fields.Float(string='Carbon Capture & Utilization (CCUS) (tCO₂e)', default=1000.0)
    total_net_ghg_co2e = fields.Float(string='Total Net Corporate GHG (tCO₂e)', compute='_compute_ghg_totals', store=True)

    # Water Stewardship & Balance
    water_fresh_withdrawn_m3 = fields.Float(string='Fresh Water Withdrawn (m³)', default=850000.0)
    water_recycled_m3 = fields.Float(string='Treated Effluent Recycled & Reused (m³)', default=340000.0)
    water_discharged_m3 = fields.Float(string='Final Outfall Discharge (m³)', default=510000.0)
    water_recycling_ratio_pct = fields.Float(string='Water Circularity / Recycling Ratio (%)',
                                            compute='_compute_ghg_totals', store=True)

    # Solid Waste & Circular Economy
    hazardous_waste_t = fields.Float(string='Hazardous Waste Generated (Metric Tonnes)', default=420.0)
    non_hazardous_waste_t = fields.Float(string='Non-Hazardous Industrial Waste (Tonnes)', default=1850.0)
    waste_recycled_t = fields.Float(string='Total Waste Diverted / Recycled (Tonnes)', default=1580.0)
    waste_landfilled_t = fields.Float(string='Waste Sent to Landfill (Tonnes)', default=690.0)
    landfill_diversion_rate_pct = fields.Float(string='Zero-Waste-to-Landfill Diversion Rate (%)',
                                              compute='_compute_ghg_totals', store=True)

    # Production Intensity KPIs
    production_output_tonnes = fields.Float(string='Total Facility Finished Production (Tonnes)', default=250000.0)
    ghg_intensity_per_tonne = fields.Float(string='Carbon Intensity (tCO₂e / Tonne Product)',
                                          compute='_compute_ghg_totals', store=True)
    water_intensity_per_tonne = fields.Float(string='Water Intensity (m³ / Tonne Product)',
                                            compute='_compute_ghg_totals', store=True)

    state = fields.Selection([
        ('draft', 'Draft Calculation'),
        ('internal_review', 'Internal Environmental Audit'),
        ('third_party_assured', 'Third-Party Verified (ISO 14064 / ISAE 3000)'),
        ('published', 'Published in Annual ESG Report'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('scope1_fuel_gas_tonnes', 'scope1_diesel_tonnes', 'scope1_flaring_tonnes', 'scope1_fugitive_tonnes',
                 'electricity_consumed_mwh', 'grid_emission_factor_kg_kwh', 'renewable_energy_recs_mwh',
                 'scope3_cat1_purchased_goods', 'scope3_cat3_fuel_energy', 'scope3_cat4_logistics',
                 'scope3_cat5_waste', 'scope3_cat6_travel', 'scope3_cat7_commuting', 'carbon_credits_purchased_t',
                 'carbon_capture_storage_t', 'water_fresh_withdrawn_m3', 'water_recycled_m3', 'waste_recycled_t',
                 'hazardous_waste_t', 'non_hazardous_waste_t', 'production_output_tonnes')
    def _compute_ghg_totals(self):
        for rec in self:
            # Scope 1
            s1 = (rec.scope1_fuel_gas_tonnes or 0.0) + (rec.scope1_diesel_tonnes or 0.0) + \
                 (rec.scope1_flaring_tonnes or 0.0) + (rec.scope1_fugitive_tonnes or 0.0)
            rec.total_scope1_co2e = s1

            # Scope 2
            mwh = rec.electricity_consumed_mwh or 0.0
            recs = min(rec.renewable_energy_recs_mwh or 0.0, mwh)
            ef = rec.grid_emission_factor_kg_kwh or 0.42

            rec.scope2_location_based_co2e = mwh * ef
            rec.scope2_market_based_co2e = (mwh - recs) * ef

            # Scope 3
            s3 = (rec.scope3_cat1_purchased_goods or 0.0) + (rec.scope3_cat3_fuel_energy or 0.0) + \
                 (rec.scope3_cat4_logistics or 0.0) + (rec.scope3_cat5_waste or 0.0) + \
                 (rec.scope3_cat6_travel or 0.0) + (rec.scope3_cat7_commuting or 0.0)
            rec.total_scope3_co2e = s3

            # Total Gross & Net
            gross = s1 + rec.scope2_market_based_co2e + s3
            rec.total_gross_ghg_co2e = gross
            offsets = (rec.carbon_credits_purchased_t or 0.0) + (rec.carbon_capture_storage_t or 0.0)
            rec.total_net_ghg_co2e = max(gross - offsets, 0.0)

            # Water
            withdrawn = rec.water_fresh_withdrawn_m3 or 0.0
            recycled = rec.water_recycled_m3 or 0.0
            rec.water_recycling_ratio_pct = round((recycled / (withdrawn + recycled)) * 100.0, 1) if (withdrawn + recycled) > 0 else 0.0

            # Waste
            tot_waste = (rec.hazardous_waste_t or 0.0) + (rec.non_hazardous_waste_t or 0.0)
            rec_waste = rec.waste_recycled_t or 0.0
            rec.landfill_diversion_rate_pct = round((rec_waste / tot_waste) * 100.0, 1) if tot_waste > 0 else 0.0

            # Intensities
            prod = rec.production_output_tonnes or 1.0
            rec.ghg_intensity_per_tonne = round(gross / prod, 4)
            rec.water_intensity_per_tonne = round(withdrawn / prod, 3)

    def action_internal_review(self):
        self.write({'state': 'internal_review'})

    def action_third_party_assure(self):
        self.write({'state': 'third_party_assured'})

    def action_publish(self):
        self.write({'state': 'published'})
