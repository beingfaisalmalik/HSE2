# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HseIhBiologicalMonitoring(models.Model):
    _name = 'hse.ih.biological.monitoring'
    _description = 'Occupational Health Biological Exposure Monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sample_date desc'

    employee_id = fields.Many2one('hr.employee', string='Worker', required=True)
    chemical_agent = fields.Selection([
        ('benzene_spma', 'Benzene (S-Phenylmercapturic acid in urine)'),
        ('lead_blood', 'Inorganic Lead (Blood Lead Level - BLL)'),
        ('mercury_urine', 'Mercury (Inorganic in urine)'),
        ('toluene_hippuric', 'Toluene (o-Cresol / Hippuric acid in urine)'),
        ('co_cohb', 'Carbon Monoxide (Carboxyhemoglobin in blood)'),
        ('organophosphate_ach', 'Organophosphates (RBC Acetylcholinesterase)'),
    ], string='Chemical Biological Agent', required=True)

    sample_date = fields.Date(string='Sampling Date', default=fields.Date.today, required=True)
    measured_value = fields.Float(string='Biological Level Measured', required=True)
    unit_of_measure = fields.Char(string='Unit of Measure', required=True, default='μg/g creatinine')
    bei_limit = fields.Float(string='ACGIH BEI Threshold Limit', required=True, default=25.0)

    exceeds_bei = fields.Boolean(string='Exceeds Biological Exposure Index', compute='_compute_exceedance', store=True)
    occupational_physician_notes = fields.Text(string='Occupational Physician Clinical Notes')
    medical_removal_required = fields.Boolean(string='Medical Removal from Exposure Mandated', default=False)

    state = fields.Selection([
        ('draft', 'Sample Collected'),
        ('normal', 'Normal Acceptable Level'),
        ('elevated', 'Elevated (Follow-up Required)'),
        ('medical_removal', 'Medical Removal Protection Active'),
    ], string='Health Surveillance Status', default='draft', tracking=True)

    @api.depends('measured_value', 'bei_limit')
    def _compute_exceedance(self):
        for rec in self:
            rec.exceeds_bei = rec.measured_value > rec.bei_limit
            if rec.exceeds_bei:
                rec.state = 'medical_removal' if rec.medical_removal_required else 'elevated'
            elif rec.measured_value > 0:
                rec.state = 'normal'


class HseIhRadiationDosimetry(models.Model):
    _name = 'hse.ih.radiation.dosimetry'
    _description = 'Ionizing Radiation Personnel Dosimetry Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, monitoring_period desc'

    employee_id = fields.Many2one('hr.employee', string='Radiation Worker', required=True)
    tld_badge_number = fields.Char(string='TLD Dosimeter Badge ID', required=True)
    year = fields.Integer(string='Monitoring Year', default=lambda self: fields.Date.context_today(self).year, required=True)
    monitoring_period = fields.Selection([
        ('q1', 'Quarter 1 (Jan - Mar)'),
        ('q2', 'Quarter 2 (Apr - Jun)'),
        ('q3', 'Quarter 3 (Jul - Sep)'),
        ('q4', 'Quarter 4 (Oct - Dec)'),
    ], string='Badge Wear Period', default='q1', required=True)

    deep_dose_hp10_msv = fields.Float(string='Deep Dose Equivalent Hp(10) (mSv)', default=0.45, required=True)
    shallow_dose_hp07_msv = fields.Float(string='Shallow Skin Dose Hp(0.07) (mSv)', default=0.60)
    eye_dose_hp3_msv = fields.Float(string='Eye Lens Dose Hp(3) (mSv)', default=0.30)

    annual_cumulative_dose_msv = fields.Float(string='Annual Cumulative Dose (mSv)',
                                             compute='_compute_cumulative_dose', store=True)
    annual_limit_msv = fields.Float(string='Regulatory Annual Limit (mSv/yr)', default=20.0)
    action_level_msv = fields.Float(string='ALARA Investigation Level (mSv/yr)', default=5.0)

    is_action_level_exceeded = fields.Boolean(string='ALARA Action Level Exceeded',
                                             compute='_compute_cumulative_dose', store=True)
    is_limit_exceeded = fields.Boolean(string='Regulatory Dose Limit Exceeded',
                                      compute='_compute_cumulative_dose', store=True)

    state = fields.Selection([
        ('normal', 'Compliant (Below Action Level)'),
        ('action_level', 'ALARA Investigation Required'),
        ('limit_exceeded', 'REGULATORY OVEREXPOSURE VIOLATION'),
    ], string='Dosimetry Status', default='normal', tracking=True)

    @api.depends('employee_id', 'year', 'deep_dose_hp10_msv')
    def _compute_cumulative_dose(self):
        for rec in self:
            badges = self.search([
                ('employee_id', '=', rec.employee_id.id),
                ('year', '=', rec.year),
            ])
            tot = sum(b.deep_dose_hp10_msv for b in badges)
            rec.annual_cumulative_dose_msv = tot
            rec.is_limit_exceeded = tot >= (rec.annual_limit_msv or 20.0)
            rec.is_action_level_exceeded = tot >= (rec.action_level_msv or 5.0)

            if rec.is_limit_exceeded:
                rec.state = 'limit_exceeded'
            elif rec.is_action_level_exceeded:
                rec.state = 'action_level'
            else:
                rec.state = 'normal'
