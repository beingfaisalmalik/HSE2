# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta

class HSEPersonnelCertification(models.Model):
    _name = 'hse.personnel.certification'
    _description = 'Personnel Safety Certification & License Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc, id desc'

    name = fields.Char(string='Certificate Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    certification_name = fields.Char(string='Certification Title (e.g. BOSIET Offshore Safety)', required=True, tracking=True)
    certificate_number = fields.Char(string='License / Certificate #', required=True, tracking=True)

    certification_type = fields.Selection([
        ('bosiet', 'BOSIET / OPITO Offshore Survival'),
        ('huet', 'Helicopter Underwater Escape (HUET)'),
        ('first_aid', 'First Aid, CPR & AED Certified'),
        ('h2s_alive', 'H2S Alive / Toxic Gas Safety'),
        ('confined_space', 'Confined Space Entry & Rescue'),
        ('working_at_height', 'Fall Protection / Working at Height'),
        ('crane_rigging', 'Certified Crane Operator / Rigger'),
        ('scaffold_inspector', 'Certified Scaffolding Inspector'),
        ('electrical_license', 'Master Electrician / HV Authorized'),
        ('medical_fitness', 'Medical Fitness Certificate (OGUK / Offshore)'),
        ('ndt_inspector', 'Non-Destructive Testing (NDT Level II)'),
        ('other', 'Other Statutory License'),
    ], string='Certification Category', required=True, tracking=True)

    person_type = fields.Selection([
        ('employee', 'Internal Company Employee'),
        ('contractor', 'Contractor Personnel'),
    ], string='Personnel Type', default='employee', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    contractor_person_name = fields.Char(string='Contractor Worker Name')
    contractor_company = fields.Char(string='Contractor Employer')

    issuing_body = fields.Char(string='Issuing Organization / Training Center (e.g. OPITO, Red Cross)', required=True)
    issue_date = fields.Date(string='Issue Date', required=True, default=fields.Date.today)
    expiry_date = fields.Date(string='Expiration Date', required=True, tracking=True)

    days_to_expire = fields.Integer(string='Days Until Expiration', compute='_compute_expiration', store=True)
    is_expired = fields.Boolean(string='Expired', compute='_compute_expiration', store=True)
    is_expiring_soon = fields.Boolean(string='Expiring in 60 Days', compute='_compute_expiration', store=True)

    certificate_document = fields.Binary(string='Certificate Scan / PDF Attachment', attachment=True)
    document_filename = fields.Char(string='Attachment Filename')
    verification_url = fields.Char(string='Online Credential Verification URL')

    state = fields.Selection([
        ('valid', 'Valid & Certified'),
        ('expiring', 'Expiring Soon (< 60 Days)'),
        ('expired', 'Expired (Work Disqualified)'),
        ('suspended', 'Suspended / Revoked'),
    ], string='Credential Status', compute='_compute_expiration', store=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.personnel.certification') or _('CERT-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
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
