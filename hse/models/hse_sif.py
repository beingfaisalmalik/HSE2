# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HseSif(models.Model):
    _name = 'hse.sif'
    _description = 'Safety Instrumented Function (SIF) - IEC 61508/61511'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='SIF Tag Number', required=True, tracking=True)
    description = fields.Char(string='Safety Function Description', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Unit / Location', required=True)
    hazard_scenario = fields.Text(string='Hazard Scenario & Consequences', required=True)
    target_safe_state = fields.Text(string='Target Safe State', required=True,
                                    default='De-energize solenoid valve and close ESD valve within 2.0s')

    # Subsystem Architectures
    subsystem_sensor_type = fields.Selection([
        ('pressure', 'Pressure Transmitter (PT)'),
        ('temperature', 'Temperature Transmitter (TT)'),
        ('level', 'Level Radar/Displacer (LT)'),
        ('flow', 'Flow Transmitter (FT)'),
        ('gas', 'Toxic / Flammable Gas Detector'),
        ('flame', 'Optical Flame Detector (IR3/UV-IR)'),
    ], string='Sensor Technology', default='pressure', required=True)

    sensor_voting = fields.Selection([
        ('1oo1', '1oo1 (Simplex)'),
        ('1oo2', '1oo2 (Redundant)'),
        ('2oo2', '2oo2 (High Availability)'),
        ('2oo3', '2oo3 (Triple Modular Redundant - TMR)'),
    ], string='Sensor Subsystem Voting', default='1oo2', required=True)

    logic_solver_voting = fields.Selection([
        ('1oo1', '1oo1 Standard Logic Solver'),
        ('1oo2d', '1oo2D Dual Redundant with Diagnostics'),
        ('2oo3', '2oo3 TMR Safety PLC'),
    ], string='Logic Solver Architecture', default='1oo2d', required=True)

    final_element_voting = fields.Selection([
        ('1oo1', '1oo1 Single Final Element'),
        ('1oo2', '1oo2 Dual Final Elements in Series'),
    ], string='Final Element Architecture', default='1oo1', required=True)

    # Reliability Parameters
    sensor_lambda_du = fields.Float(string='Sensor λdu (/hr)', default=1.5e-6, digits=(12, 9),
                                    help='Dangerous Undetected failure rate per hour')
    logic_solver_pfd = fields.Float(string='Logic Solver PFDavg', default=1.0e-4, digits=(12, 6))
    final_element_lambda_du = fields.Float(string='Final Element λdu (/hr)', default=2.8e-6, digits=(12, 9),
                                           help='Dangerous Undetected failure rate per hour')
    common_cause_beta = fields.Float(string='Common Cause Factor (β)', default=0.05,
                                     help='Beta factor for common cause failures (typically 0.02 - 0.10)')

    proof_test_interval_months = fields.Float(string='Proof Test Interval (TI Months)', default=12.0)
    mean_time_to_restore_hours = fields.Float(string='MTTR (Hours)', default=8.0)

    # Computed PFDavg and SIL
    pfd_sensor = fields.Float(string='Sensor Subsystem PFDavg', compute='_compute_sif_pfd', store=True, digits=(12, 6))
    pfd_final_element = fields.Float(string='Final Element PFDavg', compute='_compute_sif_pfd', store=True, digits=(12, 6))
    total_pfd_avg = fields.Float(string='Total SIF PFDavg', compute='_compute_sif_pfd', store=True, digits=(12, 6), tracking=True)
    risk_reduction_factor = fields.Float(string='Risk Reduction Factor (RRF)', compute='_compute_sif_pfd', store=True)
    calculated_sil = fields.Selection([
        ('sil1', 'SIL 1 (1e-2 <= PFD < 1e-1)'),
        ('sil2', 'SIL 2 (1e-3 <= PFD < 1e-2)'),
        ('sil3', 'SIL 3 (1e-4 <= PFD < 1e-3)'),
        ('sil4', 'SIL 4 (1e-5 <= PFD < 1e-4)'),
        ('none', 'Does Not Meet SIL 1'),
    ], string='Calculated SIL', compute='_compute_sif_pfd', store=True, tracking=True)

    required_sil = fields.Selection([
        ('sil1', 'SIL 1'),
        ('sil2', 'SIL 2'),
        ('sil3', 'SIL 3'),
        ('sil4', 'SIL 4'),
    ], string='Required SIL Target (SRS)', default='sil2', required=True)

    sil_compliant = fields.Boolean(string='SIL Compliant', compute='_compute_sif_pfd', store=True)
    safe_failure_fraction = fields.Float(string='Safe Failure Fraction (SFF %)', default=93.5)
    hardware_fault_tolerance = fields.Integer(string='Hardware Fault Tolerance (HFT)', default=1)

    state = fields.Selection([
        ('draft', 'Draft Specification'),
        ('active', 'Active & Armed in Service'),
        ('testing', 'Proof Testing in Progress'),
        ('impaired', 'Impaired / Defeated'),
        ('decommissioned', 'Decommissioned'),
    ], string='Status', default='draft', tracking=True)

    demand_ids = fields.One2many('hse.sif.demand', 'sif_id', string='Operational Demands & Trips')
    demand_count = fields.Integer(string='Trip Demand Count', compute='_compute_demand_count')

    @api.depends('demand_ids')
    def _compute_demand_count(self):
        for rec in self:
            rec.demand_count = len(rec.demand_ids)

    @api.depends('sensor_voting', 'sensor_lambda_du', 'final_element_voting', 'final_element_lambda_du',
                 'proof_test_interval_months', 'common_cause_beta', 'logic_solver_pfd', 'required_sil')
    def _compute_sif_pfd(self):
        for rec in self:
            ti_hours = (rec.proof_test_interval_months or 12.0) * 730.0  # ~8760 hrs/yr
            beta = rec.common_cause_beta or 0.05
            lam_s = rec.sensor_lambda_du or 1.5e-6
            lam_f = rec.final_element_lambda_du or 2.8e-6

            # Sensor Subsystem PFDavg
            if rec.sensor_voting == '1oo1':
                pfd_s = lam_s * (ti_hours / 2.0)
            elif rec.sensor_voting == '1oo2':
                pfd_s = (((lam_s * ti_hours) ** 2) / 3.0) + (beta * lam_s * (ti_hours / 2.0))
            elif rec.sensor_voting == '2oo2':
                pfd_s = lam_s * ti_hours
            elif rec.sensor_voting == '2oo3':
                pfd_s = ((lam_s * ti_hours) ** 2) + (beta * lam_s * (ti_hours / 2.0))
            else:
                pfd_s = lam_s * (ti_hours / 2.0)

            # Final Element Subsystem PFDavg
            if rec.final_element_voting == '1oo1':
                pfd_f = lam_f * (ti_hours / 2.0)
            elif rec.final_element_voting == '1oo2':
                pfd_f = (((lam_f * ti_hours) ** 2) / 3.0) + (beta * lam_f * (ti_hours / 2.0))
            else:
                pfd_f = lam_f * (ti_hours / 2.0)

            pfd_logic = rec.logic_solver_pfd or 1.0e-4
            tot_pfd = pfd_s + pfd_logic + pfd_f

            rec.pfd_sensor = pfd_s
            rec.pfd_final_element = pfd_f
            rec.total_pfd_avg = tot_pfd
            rec.risk_reduction_factor = 1.0 / tot_pfd if tot_pfd > 0 else 0.0

            # SIL determination
            if tot_pfd < 1e-4:
                rec.calculated_sil = 'sil4'
            elif tot_pfd < 1e-3:
                rec.calculated_sil = 'sil3'
            elif tot_pfd < 1e-2:
                rec.calculated_sil = 'sil2'
            elif tot_pfd < 1e-1:
                rec.calculated_sil = 'sil1'
            else:
                rec.calculated_sil = 'none'

            # Compliance check
            sil_ranks = {'none': 0, 'sil1': 1, 'sil2': 2, 'sil3': 3, 'sil4': 4}
            req_rank = sil_ranks.get(rec.required_sil, 2)
            calc_rank = sil_ranks.get(rec.calculated_sil, 0)
            rec.sil_compliant = calc_rank >= req_rank

    def action_activate(self):
        self.write({'state': 'active'})

    def action_proof_test(self):
        self.write({'state': 'testing'})

    def action_complete_test(self):
        self.write({'state': 'active'})

    def action_impair(self):
        self.write({'state': 'impaired'})

    def action_decommission(self):
        self.write({'state': 'decommissioned'})


class HseSifDemand(models.Model):
    _name = 'hse.sif.demand'
    _description = 'SIF Trip Demand & Actuation Log'
    _order = 'demand_date desc'

    sif_id = fields.Many2one('hse.sif', string='Safety Instrumented Function', required=True, ondelete='cascade')
    demand_date = fields.Datetime(string='Demand Timestamp', default=fields.Datetime.now, required=True)
    demand_type = fields.Selection([
        ('real_process_trip', 'Real Process Demand / Transient Trip'),
        ('spurious_trip', 'Spurious / False Trip (Safe Failure)'),
        ('proof_test', 'Proof Test Scheduled Demand'),
    ], string='Demand Type', default='real_process_trip', required=True)
    trip_cause = fields.Text(string='Root Trip Cause', required=True)
    actuation_time_seconds = fields.Float(string='Actuation Response Time (s)', default=1.4)
    success = fields.Boolean(string='Successful Safe Shutdown Execution', default=True)
    notes = fields.Text(string='Post-Trip Inspection Findings')
