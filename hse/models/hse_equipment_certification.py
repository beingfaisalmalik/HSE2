# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta

class HSEEquipmentCertification(models.Model):
    _name = 'hse.equipment.certification'
    _description = 'Plant Equipment Statutory Certification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc, id desc'

    name = fields.Char(string='Cert Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    certificate_number = fields.Char(string='Official Certificate / Stamp #', required=True, tracking=True)
    title = fields.Char(string='Certification Description', required=True, tracking=True)

    asset_id = fields.Many2one('assets.form', string='Target Equipment / Asset', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Area / Unit', required=True)

    cert_type = fields.Selection([
        ('pressure_vessel', 'Statutory Pressure Vessel / Boiler Inspection (ASME/PED)'),
        ('relief_valve', 'Pressure Safety Relief Valve (PSV) Bench Test Certificate'),
        ('lifting_equipment', 'Crane, Hoist & Rigging Proof Load Test (LOLER)'),
        ('atex_hazardous', 'Hazardous Area Explosion-Proof Certification (ATEX/IECEx)'),
        ('piping_ndt', 'Statutory Piping Hydrotest & NDT Inspection'),
        ('emissions_permit', 'Environmental Emissions & Stack Discharge Permit'),
    ], string='Certification Type', default='pressure_vessel', required=True, tracking=True)

    certifying_authority = fields.Char(string='Inspection Agency / Notified Body (e.g. DNV, TÜV, Lloyd’s)', required=True)
    inspector_name = fields.Char(string='Certified Inspector Name')

    issue_date = fields.Date(string='Inspection / Issue Date', required=True, default=fields.Date.today)
    expiry_date = fields.Date(string='Certification Expiry Date', required=True, tracking=True)
    inspection_interval_months = fields.Integer(string='Inspection Interval (Months)', default=12)

    # Technical Test Parameters
    design_pressure_psi = fields.Float(string='Design Pressure (PSI / Bar)')
    test_pressure_psi = fields.Float(string='Hydrostatic Test Pressure (PSI / Bar)')
    safe_working_load_ton = fields.Float(string='Safe Working Load (SWL Metric Tons)')
    inspection_findings = fields.Text(string='Inspection Findings & Wall Thickness Readings')

    certificate_file = fields.Binary(string='Inspection Certificate PDF Attachment', attachment=True)
    file_name = fields.Char(string='Attachment Filename')

    days_to_expire = fields.Integer(string='Days to Expiry', compute='_compute_expiration', store=True)
    is_expired = fields.Boolean(string='Expired', compute='_compute_expiration', store=True)
    is_expiring_soon = fields.Boolean(string='Expiring in 60 Days', compute='_compute_expiration', store=True)

    state = fields.Selection([
        ('valid', 'Valid & Certified for Operation'),
        ('expiring', 'Inspection Due Soon (< 60 Days)'),
        ('renewal', 'Renewal Inspection In Progress'),
        ('expired', 'EXPIRED - STATUTORY RISK (Do Not Operate)'),
        ('retired', 'Equipment Decommissioned'),
    ], string='Certificate Status', compute='_compute_expiration', store=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.equipment.certification') or _('EQC-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    @api.depends('expiry_date')
    def _compute_expiration(self):
        today = date.today()
        for rec in self:
            if rec.expiry_date:
                delta = (rec.expiry_date - today).days
                rec.days_to_expire = delta
                if delta < 0:
                    rec.is_expired = True
                    rec.is_expiring_soon = False
                    rec.state = 'expired'
                elif delta <= 60:
                    rec.is_expired = False
                    rec.is_expiring_soon = True
                    rec.state = 'expiring'
                else:
                    rec.is_expired = False
                    rec.is_expiring_soon = False
                    rec.state = 'valid'
            else:
                rec.days_to_expire = 9999
                rec.is_expired = False
                rec.is_expiring_soon = False
                rec.state = 'valid'

    def action_schedule_renewal(self):
        self.write({'state': 'renewal'})
