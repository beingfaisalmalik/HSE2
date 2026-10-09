# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSESds(models.Model):
    _name = 'hse.sds'
    _description = 'Chemical Safety Data Sheet (SDS / GHS HazCom)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'product_name asc'

    product_name = fields.Char(string='Product Trade Name', required=True, tracking=True)
    chemical_formula = fields.Char(string='Chemical Name / Formula')
    cas_number = fields.Char(string='CAS Registry Number', required=True, tracking=True)
    un_number = fields.Char(string='UN Number (DOT / IMDG)', default='UN 1993')
    manufacturer_supplier = fields.Char(string='Manufacturer / Importer', required=True)
    emergency_phone = fields.Char(string='24-Hour Emergency Response Hotline (e.g. CHEMTREC)', required=True)

    revision_date = fields.Date(string='SDS Revision Date', default=fields.Date.today, required=True, tracking=True)
    next_review_date = fields.Date(string='Next Mandatory 3-Year Review Date', required=True)

    # GHS Classification (Section 2)
    signal_word = fields.Selection([
        ('danger', 'DANGER'),
        ('warning', 'WARNING'),
        ('none', 'None'),
    ], string='GHS Signal Word', default='danger', required=True)

    # GHS Pictograms
    ghs_exploding_bomb = fields.Boolean(string='Exploding Bomb (Explosive / Self-Reactive)')
    ghs_flame = fields.Boolean(string='Flame (Flammable / Pyrophoric)', default=True)
    ghs_flame_over_circle = fields.Boolean(string='Flame Over Circle (Oxidizer)')
    ghs_gas_cylinder = fields.Boolean(string='Gas Cylinder (Compressed Gas)')
    ghs_corrosion = fields.Boolean(string='Corrosion (Corrosive to Skin & Metals)')
    ghs_skull_crossbones = fields.Boolean(string='Skull & Crossbones (Acute Fatal Toxicity)', default=True)
    ghs_health_hazard = fields.Boolean(string='Health Hazard (Carcinogen / Mutagen / Organ Toxicity)')
    ghs_exclamation_mark = fields.Boolean(string='Exclamation Mark (Irritant / Skin Sensitizer)')
    ghs_environment = fields.Boolean(string='Environment (Aquatic Toxicity)', default=True)

    hazard_statements = fields.Text(string='GHS Hazard Statements (H-Statements)', required=True)
    precautionary_statements = fields.Text(string='GHS Precautionary Statements (P-Statements)', required=True)

    # Physical / Chemical Properties (Section 9)
    physical_state = fields.Selection([
        ('gas', 'Compressed / Liquefied Gas'),
        ('liquid', 'Liquid'),
        ('solid', 'Solid / Powder'),
    ], string='Physical State', default='liquid', required=True)

    flash_point_c = fields.Float(string='Flash Point (°C)', default=-10.0)
    boiling_point_c = fields.Float(string='Boiling Point (°C)', default=65.0)
    auto_ignition_temp_c = fields.Float(string='Auto-Ignition Temperature (°C)', default=260.0)
    lower_explosive_limit = fields.Float(string='Lower Explosive Limit - LEL (%)', default=1.1)
    upper_explosive_limit = fields.Float(string='Upper Explosive Limit - UEL (%)', default=7.6)
    vapor_density = fields.Float(string='Vapor Density (Air = 1.0)', default=2.8)
    specific_gravity = fields.Float(string='Specific Gravity (Water = 1.0)', default=0.78)

    # First Aid & Firefighting (Sections 4 & 5)
    first_aid_inhalation = fields.Text(string='First Aid: Inhalation')
    first_aid_skin = fields.Text(string='First Aid: Skin Contact')
    first_aid_eye = fields.Text(string='First Aid: Eye Contact')
    first_aid_ingestion = fields.Text(string='First Aid: Ingestion')
    extinguishing_media = fields.Text(string='Suitable Extinguishing Media (AFFF Foam, Dry Chemical, CO2)')

    # Handling, Storage & Incompatibilities (Sections 7 & 10)
    storage_conditions = fields.Text(string='Safe Handling & Storage Protocols', required=True)
    incompatible_materials = fields.Text(string='Incompatible Materials & Conditions to Avoid', required=True)
    reactivity_group = fields.Selection([
        ('hydrocarbon_flammable', 'Hydrocarbons & Flammable Liquids'),
        ('strong_acid', 'Inorganic Strong Acids (HCl, H2SO4, HNO3)'),
        ('strong_base', 'Strong Bases / Caustics (NaOH, KOH)'),
        ('oxidizer', 'Strong Oxidizers (Peroxides, Chlorates, Nitrates)'),
        ('water_reactive', 'Water-Reactive Substances'),
        ('toxic_gas', 'Toxic Compressed Gases (H2S, Cl2, NH3)'),
    ], string='Chemical Reactivity Group', default='hydrocarbon_flammable', required=True)

    # PPE Requirements (Section 8)
    req_respirator = fields.Char(string='Respiratory Protection (e.g. Organic Vapor Cartridge / SCBA)')
    req_gloves = fields.Char(string='Hand Protection (e.g. Nitrile / Neoprene / Butyl)')
    req_eye_face = fields.Char(string='Eye/Face Protection (e.g. Chemical Splash Goggles + Face Shield)')
    req_body = fields.Char(string='Protective Clothing (e.g. Nomex FRC / Level B Hazmat Suit)')

    sds_file = fields.Binary(string='Official PDF Safety Data Sheet')
    sds_filename = fields.Char(string='SDS File Name')

    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('current', 'Active & Current'),
        ('review_due', 'Review Required (Nearing 3 Years)'),
        ('archived', 'Archived / Obsolete'),
    ], string='Status', default='current', tracking=True)


class HSESdsCompatibility(models.Model):
    _name = 'hse.sds.compatibility'
    _description = 'Chemical Reactivity Compatibility Rule'
    _order = 'group_a asc'

    group_a = fields.Selection([
        ('hydrocarbon_flammable', 'Hydrocarbons & Flammable Liquids'),
        ('strong_acid', 'Inorganic Strong Acids'),
        ('strong_base', 'Strong Bases / Caustics'),
        ('oxidizer', 'Strong Oxidizers'),
        ('water_reactive', 'Water-Reactive Substances'),
        ('toxic_gas', 'Toxic Compressed Gases'),
    ], string='Chemical Group A', required=True)

    group_b = fields.Selection([
        ('hydrocarbon_flammable', 'Hydrocarbons & Flammable Liquids'),
        ('strong_acid', 'Inorganic Strong Acids'),
        ('strong_base', 'Strong Bases / Caustics'),
        ('oxidizer', 'Strong Oxidizers'),
        ('water_reactive', 'Water-Reactive Substances'),
        ('toxic_gas', 'Toxic Compressed Gases'),
    ], string='Chemical Group B', required=True)

    compatibility_status = fields.Selection([
        ('compatible', 'Compatible - Co-storage Permitted'),
        ('caution', 'Caution - Physical Separation Barrier Advised'),
        ('forbidden', 'FORBIDDEN - Violent Reactivity / Explosion Hazard (Segregated Dedicated Bunker Required)'),
    ], string='Compatibility Evaluation', required=True, default='forbidden')

    reaction_hazard = fields.Text(string='Consequence of Mixing (e.g. Spontaneous ignition, toxic gas release)', required=True)
