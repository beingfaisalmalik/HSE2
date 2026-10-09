# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

# =============================================================================
# 1. Similar Exposure Groups (SEGs)
# =============================================================================
class HSEIhSeg(models.Model):
    _name = 'hse.ih.seg'
    _description = 'Similar Exposure Group (SEG)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='SEG Title', required=True, tracking=True)
    code = fields.Char(string='SEG Code (e.g. SEG-WELD-01)', required=True)
    location_id = fields.Many2one('hse.location.profile', string='Facility / Operational Area', required=True)
    job_description = fields.Text(string='Work Tasks & Activities Carried Out', required=True)
    
    # Stressors
    stressor_chemical = fields.Boolean(string='Chemical Vapors / Dusts / Fumes', default=True)
    stressor_noise = fields.Boolean(string='High Noise Exposure (> 85 dBA)', default=True)
    stressor_radiation = fields.Boolean(string='Ionizing / Non-Ionizing Radiation', default=False)
    stressor_thermal = fields.Boolean(string='Heat Stress / Cold Stress', default=False)
    stressor_ergonomic = fields.Boolean(string='Ergonomic Strain / Repetitive Lifting', default=True)

    worker_count = fields.Integer(string='Estimated Workers in SEG', default=5)
    sample_ids = fields.One2many('hse.ih.sample', 'seg_id', string='Exposure Samples')
    sample_count = fields.Integer(string='Samples Logged', compute='_compute_sample_count', store=True)

    @api.depends('sample_ids')
    def _compute_sample_count(self):
        for rec in self:
            rec.sample_count = len(rec.sample_ids)


# =============================================================================
# 2. Exposure Monitoring & Sampling
# =============================================================================
class HSEIhSample(models.Model):
    _name = 'hse.ih.sample'
    _description = 'Industrial Hygiene Exposure Monitoring & Air/Noise Sampling'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sample_date desc, id desc'

    name = fields.Char(string='Sample ID', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    seg_id = fields.Many2one('hse.ih.seg', string='Similar Exposure Group (SEG)', required=True)
    employee_id = fields.Many2one('hr.employee', string='Monitored Worker')
    hygienist_id = fields.Many2one('res.users', string='Certified Industrial Hygienist (CIH)', default=lambda self: self.env.user)
    sample_date = fields.Date(string='Sampling Date', default=fields.Date.today, required=True)

    sampling_type = fields.Selection([
        ('air_chemical', 'Personal Air Sampling (Chemical / VOC / Vapor)'),
        ('air_particulate', 'Particulate (Respirable Dust, Silica, Asbestos)'),
        ('noise_dosimetry', 'Personal Noise Dosimetry (dBA TWA)'),
        ('heat_stress', 'Thermal Heat Stress (WBGT Index)'),
        ('radiation', 'Radiation Dosimeter Badge'),
    ], string='Sampling Type', default='air_chemical', required=True)

    agent_name = fields.Char(string='Contaminant / Stressor Measured (e.g. Benzene, H2S, Silica, Noise)', required=True)
    sampling_duration_minutes = fields.Float(string='Sampling Duration (Minutes)', default=480.0, required=True)

    # Quantitative Result
    measured_concentration = fields.Float(string='Measured Concentration (ppm, mg/m³, or dBA)', required=True)
    unit_of_measure = fields.Selection([
        ('ppm', 'Parts Per Million (ppm)'),
        ('mg_m3', 'Milligrams per Cubic Meter (mg/m³)'),
        ('ug_m3', 'Micrograms per Cubic Meter (µg/m³)'),
        ('dba', 'Decibels A-Weighted (dBA)'),
        ('celsius', 'WBGT (°C)'),
    ], string='Concentration Unit', default='ppm', required=True)

    # 8-Hour TWA Calculation
    twa_8hr = fields.Float(string='Calculated 8-Hour TWA', compute='_compute_twa', store=True)

    # Occupational Exposure Limits (OEL)
    osha_pel = fields.Float(string='OSHA Permissible Exposure Limit (PEL)', required=True)
    acgih_tlv = fields.Float(string='ACGIH Threshold Limit Value (TLV)', required=True)
    action_level = fields.Float(string='Action Level (Typically 50% of PEL)', compute='_compute_action_level', store=True)

    # Compliance Evaluation
    exceeds_pel = fields.Boolean(string='Exceeds OSHA PEL', compute='_compute_compliance', store=True)
    exceeds_action_level = fields.Boolean(string='Exceeds Action Level', compute='_compute_compliance', store=True)
    exposure_rating = fields.Selection([
        ('acceptable', 'Acceptable (< 50% OEL)'),
        ('action_required', 'Action Level Reached (50% - 100% OEL - Medical Surveillance Triggered)'),
        ('unacceptable', 'Unacceptable Overexposure (> 100% OEL - Immediate Controls Mandatory)'),
    ], string='Exposure Classification', compute='_compute_compliance', store=True)

    corrective_control = fields.Text(string='Engineering Controls / Respiratory Protection Upgrades Required')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.ih.sample') or _('IH-%05d') % self.env['hse.ih.sample'].search_count([])
        return super().create(vals_list)

    @api.depends('measured_concentration', 'sampling_duration_minutes')
    def _compute_twa(self):
        for rec in self:
            mins = rec.sampling_duration_minutes if rec.sampling_duration_minutes > 0 else 480.0
            rec.twa_8hr = round((rec.measured_concentration * mins) / 480.0, 3)

    @api.depends('osha_pel')
    def _compute_action_level(self):
        for rec in self:
            rec.action_level = round((rec.osha_pel or 0.0) * 0.5, 3)

    @api.depends('twa_8hr', 'osha_pel', 'action_level')
    def _compute_compliance(self):
        for rec in self:
            twa = rec.twa_8hr
            pel = rec.osha_pel
            al = rec.action_level
            rec.exceeds_pel = bool(pel and twa > pel)
            rec.exceeds_action_level = bool(al and twa >= al)
            if pel and twa > pel:
                rec.exposure_rating = 'unacceptable'
            elif al and twa >= al:
                rec.exposure_rating = 'action_required'
            else:
                rec.exposure_rating = 'acceptable'


# =============================================================================
# 3. Audiometry & Hearing Conservation Program (OSHA 1910.95)
# =============================================================================
class HSEIhAudiometry(models.Model):
    _name = 'hse.ih.audiometry'
    _description = 'Audiometric Hearing Test & Standard Threshold Shift (STS)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'test_date desc, id desc'

    name = fields.Char(string='Audiogram Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Worker', required=True)
    test_date = fields.Date(string='Examination Date', default=fields.Date.today, required=True)
    audiologist_name = fields.Char(string='Certified Audiologist / Technician', required=True)
    test_type = fields.Selection([
        ('baseline', 'Baseline Audiogram'),
        ('annual', 'Annual Periodic Audiogram'),
        ('retest', 'Confirmation Retest (Within 30 Days)'),
        ('exit', 'Exit / Termination Audiogram'),
    ], string='Test Type', default='annual', required=True)

    # Pure Tone Hearing Thresholds (dB at Frequencies Hz) - Left Ear
    l_500 = fields.Float(string='Left 500 Hz (dB)', default=15.0)
    l_1000 = fields.Float(string='Left 1000 Hz (dB)', default=15.0)
    l_2000 = fields.Float(string='Left 2000 Hz (dB)', default=15.0)
    l_3000 = fields.Float(string='Left 3000 Hz (dB)', default=20.0)
    l_4000 = fields.Float(string='Left 4000 Hz (dB)', default=20.0)
    l_6000 = fields.Float(string='Left 6000 Hz (dB)', default=25.0)

    # Right Ear
    r_500 = fields.Float(string='Right 500 Hz (dB)', default=15.0)
    r_1000 = fields.Float(string='Right 1000 Hz (dB)', default=15.0)
    r_2000 = fields.Float(string='Right 2000 Hz (dB)', default=15.0)
    r_3000 = fields.Float(string='Right 3000 Hz (dB)', default=20.0)
    r_4000 = fields.Float(string='Right 4000 Hz (dB)', default=20.0)
    r_6000 = fields.Float(string='Right 6000 Hz (dB)', default=25.0)

    # OSHA Average at 2000, 3000, 4000 Hz
    left_avg_234 = fields.Float(string='Left Ear Average (2, 3, 4 kHz)', compute='_compute_averages', store=True)
    right_avg_234 = fields.Float(string='Right Ear Average (2, 3, 4 kHz)', compute='_compute_averages', store=True)

    baseline_audiogram_id = fields.Many2one('hse.ih.audiometry', string='Reference Baseline Audiogram')
    has_sts = fields.Boolean(string='Standard Threshold Shift (STS Detected)', compute='_compute_sts', store=True)
    is_osha_recordable_sts = fields.Boolean(string='OSHA 300 Recordable Hearing Loss', compute='_compute_sts', store=True)
    recommendations = fields.Text(string='Hearing Protection Upgrade & ENT Physician Referral')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.ih.audiometry') or _('AUDIO-%05d') % self.env['hse.ih.audiometry'].search_count([])
        return super().create(vals_list)

    @api.depends('l_2000', 'l_3000', 'l_4000', 'r_2000', 'r_3000', 'r_4000')
    def _compute_averages(self):
        for rec in self:
            rec.left_avg_234 = round((rec.l_2000 + rec.l_3000 + rec.l_4000) / 3.0, 1)
            rec.right_avg_234 = round((rec.r_2000 + rec.r_3000 + rec.r_4000) / 3.0, 1)

    @api.depends('left_avg_234', 'right_avg_234', 'baseline_audiogram_id')
    def _compute_sts(self):
        for rec in self:
            base = rec.baseline_audiogram_id
            if base:
                l_diff = rec.left_avg_234 - base.left_avg_234
                r_diff = rec.right_avg_234 - base.right_avg_234
                # Standard Threshold Shift: average shift of 10 dB or more at 2000, 3000, 4000 Hz
                sts = (l_diff >= 10.0 or r_diff >= 10.0)
                rec.has_sts = sts
                # OSHA Recordable: STS + overall hearing level of 25 dB or higher from audiometric zero
                rec.is_osha_recordable_sts = (sts and (rec.left_avg_234 >= 25.0 or rec.right_avg_234 >= 25.0))
            else:
                rec.has_sts = False
                rec.is_osha_recordable_sts = False


# =============================================================================
# 4. Respiratory Protection & Fit Testing (OSHA 1910.134)
# =============================================================================
class HSEIhRespirator(models.Model):
    _name = 'hse.ih.respirator'
    _description = 'Respirator Medical Clearance & Fit Test Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fit_test_date desc, id desc'

    name = fields.Char(string='Fit Test Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    fit_test_date = fields.Date(string='Fit Test Date', default=fields.Date.today, required=True)
    next_due_date = fields.Date(string='Annual Expiration Date', required=True)

    medical_clearance_status = fields.Selection([
        ('cleared', 'Cleared for Respirator Use by Physician (PLHCP)'),
        ('restricted', 'Cleared with Specific Physical Restrictions'),
        ('denied', 'Medically Unfit for Respirator Use'),
    ], string='Physician Medical Clearance', default='cleared', required=True)

    respirator_type = fields.Selection([
        ('n95', 'Filtering Facepiece (N95 / FFP2)'),
        ('half_mask', 'Half-Mask Elastomeric Air-Purifying Respirator'),
        ('full_face', 'Full-Facepiece Elastomeric Respirator'),
        ('papr', 'Powered Air-Purifying Respirator (PAPR)'),
        ('scba', 'Self-Contained Breathing Apparatus (SCBA)'),
    ], string='Respirator Type', default='full_face', required=True)

    manufacturer_model = fields.Char(string='Respirator Make & Model (e.g. 3M 6800 Series)', required=True)
    mask_size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ], string='Assigned Mask Size', default='medium', required=True)

    test_method = fields.Selection([
        ('qualitative_bitrex', 'Qualitative: Bitrex (Denatonium Benzoate)'),
        ('qualitative_saccharin', 'Qualitative: Saccharin Aerosol'),
        ('quantitative_portacount', 'Quantitative: CNC Particle Counting (TSI PortaCount)'),
    ], string='Fit Test Protocol', default='quantitative_portacount', required=True)

    quantitative_fit_factor = fields.Float(string='Quantitative Fit Factor (Pass >= 500 for Full-Face, >= 100 for Half-Face)', default=1250.0)
    fit_test_passed = fields.Boolean(string='Fit Test Passed Successfully', default=True, required=True)
    clean_shaven_verified = fields.Boolean(string='Verified Clean-Shaven (No Facial Hair Seal Interference)', default=True, required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.ih.respirator') or _('RESP-%05d') % self.env['hse.ih.respirator'].search_count([])
        return super().create(vals_list)


# =============================================================================
# 5. Ergonomics Assessment (REBA, RULA & NIOSH Lifting Equation)
# =============================================================================
class HSEIhErgonomics(models.Model):
    _name = 'hse.ih.ergonomics'
    _description = 'Ergonomics Assessment (REBA, RULA & NIOSH Lifting Equation)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'assessment_date desc, id desc'

    name = fields.Char(string='Ergo Assessment Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    job_task_name = fields.Char(string='Job Task / Workstation Title', required=True)
    location_id = fields.Many2one('hse.location.profile', string='Department / Unit', required=True)
    assessor_id = fields.Many2one('res.users', string='Ergonomist / Evaluator', default=lambda self: self.env.user)
    assessment_date = fields.Date(string='Assessment Date', default=fields.Date.today, required=True)

    assessment_tool = fields.Selection([
        ('reba', 'REBA (Rapid Entire Body Assessment)'),
        ('rula', 'RULA (Rapid Upper Limb Assessment)'),
        ('niosh', 'NIOSH Lifting Equation (Manual Material Handling)'),
    ], string='Assessment Tool', default='reba', required=True)

    # REBA / RULA Scoring
    reba_score = fields.Integer(string='REBA Total Score (1 - 15)', default=4)
    rula_score = fields.Integer(string='RULA Total Score (1 - 7)', default=3)

    # NIOSH Equation Fields
    load_weight_kg = fields.Float(string='Actual Load Weight (L kg)', default=18.0)
    horizontal_distance_cm = fields.Float(string='Horizontal Distance (H cm)', default=30.0)
    vertical_height_cm = fields.Float(string='Vertical Origin Height (V cm)', default=75.0)
    vertical_travel_cm = fields.Float(string='Vertical Travel Distance (D cm)', default=50.0)
    asymmetry_angle_deg = fields.Float(string='Asymmetry Twisting Angle (A deg)', default=15.0)
    lifting_frequency_min = fields.Float(string='Lifting Frequency (lifts/min)', default=2.0)

    recommended_weight_limit = fields.Float(string='Recommended Weight Limit (RWL kg)', compute='_compute_niosh', store=True)
    lifting_index = fields.Float(string='Lifting Index (LI = L / RWL)', compute='_compute_niosh', store=True)

    risk_level = fields.Selection([
        ('negligible', 'Negligible Risk (Score 1 / LI < 1.0)'),
        ('low', 'Low Risk - Change May Be Needed (LI 1.0 - 1.5)'),
        ('medium', 'Medium Risk - Further Investigation & Redesign Soon (LI 1.5 - 2.5)'),
        ('high', 'High Risk - Redesign Immediate (Score 8-10 / LI 2.5 - 3.0)'),
        ('very_high', 'Very High Risk - Change Immediately (Score > 11 / LI > 3.0)'),
    ], string='Ergonomic Risk Level', compute='_compute_ergo_risk', store=True)

    remedial_measures = fields.Text(string='Workstation Engineering & Administrative Controls Required')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.ih.ergonomics') or _('ERGO-%05d') % self.env['hse.ih.ergonomics'].search_count([])
        return super().create(vals_list)

    @api.depends('load_weight_kg', 'horizontal_distance_cm')
    def _compute_niosh(self):
        for rec in self:
            # Simplified NIOSH: LC = 23 kg, HM = 25/H, VM, DM, AM, FM, CM
            h = max(rec.horizontal_distance_cm, 25.0)
            hm = min(1.0, 25.0 / h)
            rwl = round(23.0 * hm * 0.9 * 0.85, 2)
            rec.recommended_weight_limit = rwl
            if rwl > 0:
                rec.lifting_index = round(rec.load_weight_kg / rwl, 2)
            else:
                rec.lifting_index = 1.0

    @api.depends('assessment_tool', 'reba_score', 'rula_score', 'lifting_index')
    def _compute_ergo_risk(self):
        for rec in self:
            if rec.assessment_tool == 'reba':
                s = rec.reba_score
                if s <= 1: rec.risk_level = 'negligible'
                elif s <= 3: rec.risk_level = 'low'
                elif s <= 7: rec.risk_level = 'medium'
                elif s <= 10: rec.risk_level = 'high'
                else: rec.risk_level = 'very_high'
            elif rec.assessment_tool == 'rula':
                s = rec.rula_score
                if s <= 2: rec.risk_level = 'negligible'
                elif s <= 4: rec.risk_level = 'low'
                elif s <= 6: rec.risk_level = 'medium'
                else: rec.risk_level = 'very_high'
            else:
                li = rec.lifting_index
                if li < 1.0: rec.risk_level = 'negligible'
                elif li <= 1.5: rec.risk_level = 'low'
                elif li <= 2.5: rec.risk_level = 'medium'
                elif li <= 3.0: rec.risk_level = 'high'
                else: rec.risk_level = 'very_high'
