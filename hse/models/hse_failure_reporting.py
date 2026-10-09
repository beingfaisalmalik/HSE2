# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HSEFailureReport(models.Model):
    _name = 'hse.failure.report'
    _description = 'ISO 14224 Equipment Failure Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'failure_date desc, id desc'

    name = fields.Char(string='Failure Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    asset_id = fields.Many2one('assets.form', string='Failed Asset / Equipment Tag', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Area / Unit', required=True)
    failure_date = fields.Datetime(string='Failure Timestamp', default=fields.Datetime.now, required=True, tracking=True)

    # ISO 14224 Equipment Taxonomy
    equipment_class = fields.Selection([
        ('pump', 'Centrifugal / Positive Displacement Pump'),
        ('compressor', 'Centrifugal / Reciprocating Compressor'),
        ('gas_turbine', 'Gas / Steam Turbine'),
        ('motor', 'Electric Motor / Drive'),
        ('heat_exchanger', 'Shell & Tube / Plate Heat Exchanger'),
        ('pressure_vessel', 'Separator / Pressure Vessel / Column'),
        ('valve_control', 'Control Valve / ESD Isolation Valve'),
        ('piping', 'Process Piping / Flange / Spool'),
        ('instrument', 'Pressure / Temp / Level Transmitter / Sensor'),
    ], string='ISO 14224 Equipment Class', default='pump', required=True, tracking=True)

    failed_component = fields.Char(string='Sub-component (e.g. Mechanical Seal, Thrust Bearing, Impeller)')

    # Failure Mode (How failure manifested)
    failure_mode = fields.Selection([
        ('ext_leak', 'EL: External Leakage / Loss of Containment'),
        ('fail_start', 'FTS: Failure to Start on Demand'),
        ('fail_stop', 'STP: Failure to Stop / Trip on Demand'),
        ('vib_high', 'VIB: Excessive Vibration / Harmonic Oscillation'),
        ('temp_high', 'TMP: High Bearing / Casing Temperature Trip'),
        ('seized', 'SEZ: Seized / Mechanical Binding'),
        ('spurious_trip', 'SPT: Spurious / False Safety Trip'),
        ('low_output', 'LOP: Degraded Output / Low Flow / Low Pressure'),
        ('elec_fault', 'ELF: Electrical Short / Insulation Ground Fault'),
    ], string='Failure Mode', default='ext_leak', required=True, tracking=True)

    # Failure Mechanism (Physical degradation process)
    failure_mechanism = fields.Selection([
        ('corrosion', 'Corrosion / Chemical Pitting / H2S Embrittlement'),
        ('erosion', 'Erosion / Sand Abrasion / Cavitation'),
        ('fatigue', 'Cyclic Mechanical / Thermal Fatigue Cracking'),
        ('wear', 'Normal Mechanical Wear / Friction Fretting'),
        ('overheating', 'Thermal Degradation / Dry Run Overheating'),
        ('fouling', 'Fouling / Scale Build-up / Coke Plugging'),
        ('vibration', 'Unbalance / Shaft Misalignment Resonance'),
    ], string='Failure Mechanism', default='wear', required=True)

    # Failure Cause (Underlying technical root trigger)
    failure_cause = fields.Selection([
        ('design', 'Design Inadequacy / Under-specified Metallurgy'),
        ('fabrication', 'Fabrication / Casting / Welding Defect'),
        ('operation', 'Operating Beyond Safe Operating Limits (SOL)'),
        ('maintenance', 'Incorrect Assembly / Improper Torque / Misalignment'),
        ('lubrication', 'Lubrication Starvation / Contaminated Oil'),
        ('aging', 'End of Design Fatigue Life'),
    ], string='Underlying Cause', default='maintenance', required=True)

    # Detection Method
    detection_method = fields.Selection([
        ('continuous', 'Online Continuous Vibration / Condition Monitoring'),
        ('alarm', 'Control Room DCS Alarm Tripped'),
        ('operator', 'Operator Field Round / Senses (Sound, Smell, Visual)'),
        ('periodic_pm', 'Periodic Preventive Maintenance / Offline Inspection'),
        ('functional_test', 'Scheduled Emergency Functional Proof Test'),
    ], string='Detection Method', default='operator', required=True)

    # Impact & Reliability Metrics
    impact_level = fields.Selection([
        ('shutdown', 'Total Unit / Plant Shutdown'),
        ('derated', 'Production Rate Derated / Turndown'),
        ('standby_switch', 'Switched to Installed Standby Unit (Zero Loss)'),
        ('none', 'No Direct Production Impact'),
    ], string='Operational Impact', default='shutdown', required=True)

    operating_hours = fields.Float(string='Operating Hours Run Since Last Overhaul')
    downtime_hours = fields.Float(string='Asset Downtime (Hours)', default=0.0)
    repair_time_hours = fields.Float(string='Mean Time to Repair - MTTR (Hours)', default=0.0)

    remedial_action_taken = fields.Text(string='Remedial Repair Action Executed')
    reported_by_id = fields.Many2one('res.users', string='Reported By', default=lambda self: self.env.user)

    state = fields.Selection([
        ('reported', 'Failure Reported'),
        ('under_analysis', 'Reliability Analysis In Progress'),
        ('rcfa', 'Root Cause RCFA Initiated'),
        ('repaired', 'Repaired & Re-commissioned'),
        ('closed', 'Reliability Record Closed'),
    ], string='Status', default='reported', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.failure.report') or _('FAIL-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def action_analyze(self):
        self.write({'state': 'under_analysis'})

    def action_repaired(self):
        self.write({'state': 'repaired'})

    def action_close(self):
        self.write({'state': 'closed'})
