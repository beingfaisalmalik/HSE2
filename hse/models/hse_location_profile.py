# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSELocationProfile(models.Model):
    _name = 'hse.location.profile'
    _description = 'HSE Location Safety Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Location / Unit Name', required=True, tracking=True)
    code = fields.Char(string='Area / Tag Code', required=True)
    parent_id = fields.Many2one('hse.location.profile', string='Parent Plant / Facility')
    location_type = fields.Selection([
        ('plant', 'Process Plant / Refinery'),
        ('unit', 'Operating Unit / Train'),
        ('platform', 'Offshore Platform / Rig'),
        ('building', 'Building / Substation / Control Room'),
        ('storage', 'Tank Farm / Chemical Storage'),
        ('pipeline', 'Pipeline Corridor / ROW'),
        ('workshop', 'Maintenance Workshop'),
    ], string='Facility Type', default='unit', required=True)

    # Hazardous Area Classification (ATEX / NEC)
    hazardous_zone = fields.Selection([
        ('zone0', 'Zone 0 / Class I Div 1 (Continuous Flammable Atmosphere)'),
        ('zone1', 'Zone 1 / Class I Div 1 (Likely in Normal Operations)'),
        ('zone2', 'Zone 2 / Class I Div 2 (Unlikely, Short Duration Only)'),
        ('safe', 'Safe Area / Non-Hazardous Area'),
    ], string='Hazardous Area Zone', default='zone2', required=True, tracking=True)

    # Safety and Environmental Critical Elements (SECE)
    is_sece = fields.Boolean(string='SECE Designated Area (Safety Critical)', default=False, tracking=True)
    sece_classification = fields.Char(string='SECE Barrier Group Ref')

    # Barriers & Safety Systems Present
    has_gas_detection = fields.Boolean(string='Toxic / Flammable Gas Detection System', default=True)
    has_fire_deluge = fields.Boolean(string='Active Deluge / Fire Water Spray System', default=False)
    has_blast_wall = fields.Boolean(string='Blast Resistant Barriers / Walls', default=False)
    has_emergency_shutdown = fields.Boolean(string='ESD Pushbutton Stations', default=True)
    has_eyewash_shower = fields.Boolean(string='Safety Shower & Eyewash Station', default=True)

    # Emergency & Evacuation
    muster_station_primary = fields.Char(string='Primary Muster Station', default='Muster Area Alpha')
    muster_station_secondary = fields.Char(string='Secondary Muster Station', default='Muster Area Bravo')
    evacuation_route = fields.Text(string='Evacuation Route Instructions')
    wind_sock_location = fields.Char(string='Nearest Windsock Location')

    # Environmental Sensitivities
    environmental_sensitivity = fields.Selection([
        ('low', 'Low Sensitivity'),
        ('medium', 'Medium (Close to Drainage / Outfall)'),
        ('high', 'High (Adjacent to Waterway / Marine Environment)'),
        ('critical', 'Critical Eco-Protected Zone'),
    ], string='Environmental Sensitivity', default='medium')
    containment_capacity_m3 = fields.Float(string='Secondary Containment / Bund Capacity (m³)')

    # Operational Status
    operating_state = fields.Selection([
        ('normal', 'Normal Online Operations'),
        ('turnaround', 'Plant Turnaround / Major Outage'),
        ('shutdown', 'Cold Shutdown / De-energized'),
        ('startup', 'Commissioning / Startup Phase'),
        ('mothballed', 'Mothballed / Decommissioned'),
    ], string='Operating State', default='normal', tracking=True)

    manager_id = fields.Many2one('res.users', string='Area Authority / Manager')
    safety_officer_id = fields.Many2one('res.users', string='Area HSE Lead')

    # Real-time counts
    active_permit_count = fields.Integer(string='Active Permits to Work', compute='_compute_active_counters')
    active_bypass_count = fields.Integer(string='Active Safety Bypasses', compute='_compute_active_counters')
    active_loto_count = fields.Integer(string='Active LOTO Isolations', compute='_compute_active_counters')

    # Chemical / Hazardous Substance Inventory
    chemical_ids = fields.One2many('hse.location.chemical', 'location_id', string='Hazardous Chemicals Inventory')
    chemical_count = fields.Integer(string='Chemicals Count', compute='_compute_chemical_count')

    notes = fields.Html(string='Safety & Operational Notes')

    def _compute_chemical_count(self):
        for rec in self:
            rec.chemical_count = len(rec.chemical_ids)

    def _compute_active_counters(self):
        for rec in self:
            rec.active_permit_count = self.env['hse.permit'].search_count([
                ('location_id', '=', rec.id),
                ('state', 'in', ['approved', 'active'])
            ]) if 'hse.permit' in self.env else 0

            rec.active_bypass_count = self.env['hse.bypass'].search_count([
                ('location_id', '=', rec.id),
                ('state', '=', 'active')
            ]) if 'hse.bypass' in self.env else 0

            rec.active_loto_count = self.env['hse.loto.plan'].search_count([
                ('location_id', '=', rec.id),
                ('state', '=', 'isolated')
            ]) if 'hse.loto.plan' in self.env else 0

    def action_view_permits(self):
        self.ensure_one()
        return {
            'name': _('Permits for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hse.permit',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }

    def action_view_bypasses(self):
        self.ensure_one()
        return {
            'name': _('Bypasses for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hse.bypass',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }

    def action_view_loto(self):
        self.ensure_one()
        return {
            'name': _('LOTO Plans for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hse.loto.plan',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }

    def action_view_incidents(self):
        self.ensure_one()
        return {
            'name': _('Incidents for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'incident.reporting',
            'view_mode': 'tree,form',
            'domain': [('location_profile_id', '=', self.id)],
            'context': {'default_location_profile_id': self.id},
        }


class HSELocationChemical(models.Model):
    _name = 'hse.location.chemical'
    _description = 'Location Hazardous Chemical / Substance Inventory'
    _order = 'chemical_name asc'

    location_id = fields.Many2one('hse.location.profile', string='Location', ondelete='cascade', required=True)
    chemical_name = fields.Char(string='Chemical / Substance Name', required=True)
    cas_number = fields.Char(string='CAS Registry # (e.g. 7783-06-4 for H₂S)')
    physical_state = fields.Selection([
        ('gas', 'Compressed Gas / Vapor'),
        ('liquified_gas', 'Liquefied Gas (LPG/LNG)'),
        ('liquid', 'Liquid'),
        ('solid', 'Solid / Powder'),
    ], string='Physical State', default='liquid', required=True)

    # NFPA 704 Standard Rating (0 - 4)
    nfpa_health = fields.Integer(string='Health Hazard (0-4)', default=2)
    nfpa_flammability = fields.Integer(string='Flammability (0-4)', default=3)
    nfpa_instability = fields.Integer(string='Instability / Reactivity (0-4)', default=0)
    nfpa_special = fields.Selection([
        ('none', 'None'),
        ('w', 'W - Reacts violently with water'),
        ('ox', 'OX - Oxidizer'),
        ('sa', 'SA - Simple Asphyxiant gas'),
        ('cor', 'COR - Corrosive'),
    ], string='Special Hazard', default='none')

    # Inventory Quantities
    quantity_stored = fields.Float(string='Current Inventory Stored', default=0.0)
    max_threshold = fields.Float(string='PSM / Seveso Threshold Quantity')
    unit_of_measure = fields.Char(string='Unit of Measure (kg, Ton, Gallons, Bbl)', default='kg')
    sds_url = fields.Char(string='Safety Data Sheet (SDS) URL / Document Link')

    # Hazard GHS Classifications
    ghs_flammable = fields.Boolean(string='Flammable')
    ghs_toxic = fields.Boolean(string='Acute Toxic')
    ghs_corrosive = fields.Boolean(string='Corrosive')
    ghs_explosive = fields.Boolean(string='Explosive')
    ghs_carcinogen = fields.Boolean(string='Carcinogen / CMR')

