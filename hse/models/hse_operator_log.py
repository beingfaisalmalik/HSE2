# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HSEOperatorLog(models.Model):
    _name = 'hse.operator.log'
    _description = 'Control Room & Field Operator Shift Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'shift_date desc, shift_type asc, id desc'

    name = fields.Char(string='Shift Log Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    location_id = fields.Many2one('hse.location.profile', string='Operating Plant / Unit', required=True)
    shift_date = fields.Date(string='Shift Date', default=fields.Date.today, required=True, tracking=True)
    shift_type = fields.Selection([
        ('day', 'Day Shift (06:00 - 18:00)'),
        ('night', 'Night Shift (18:00 - 06:00)'),
        ('morning', 'Morning Shift (07:00 - 15:00)'),
        ('evening', 'Evening Shift (15:00 - 23:00)'),
    ], string='Shift Watch', default='day', required=True, tracking=True)

    # Shift Personnel
    supervisor_id = fields.Many2one('res.users', string='Shift Supervisor', required=True, default=lambda self: self.env.user)
    board_operator_id = fields.Many2one('res.users', string='Lead Board / DCS Operator')
    field_operators = fields.Char(string='Outside / Field Operators on Duty')

    # Operational Parameters & Production Summary
    operating_status = fields.Selection([
        ('normal', 'Steady State / Normal Production'),
        ('turndown', 'Turndown / Partial Production'),
        ('startup', 'Startup in Progress'),
        ('shutdown', 'Unit Shutdown / Trip Response'),
        ('maintenance', 'Planned Maintenance Outage'),
    ], string='Unit Operating State', default='normal', required=True)
    production_output = fields.Char(string='Shift Production Summary (e.g. 45,000 BPD / 120 MW)')

    # Chronological Log Entries
    entry_ids = fields.One2many('hse.operator.log.entry', 'log_id', string='Chronological Shift Events')
    round_ids = fields.One2many('hse.operator.log.round', 'log_id', string='Equipment Inspection Rounds')
    alarm_ids = fields.One2many('hse.operator.log.alarm', 'log_id', string='Defeated / Standing Alarms')

    # Handover Protocol
    active_permits_count = fields.Integer(string='Permits Active at Handover', compute='_compute_active_permits')
    active_bypasses_count = fields.Integer(string='Bypasses Active at Handover', compute='_compute_active_bypasses')
    handover_standing_orders = fields.Text(string='Standing Orders & Instructions for Next Shift')
    handover_critical_alarms = fields.Text(string='Inhibited Alarms & Critical Deficiencies')

    # Two-Party Shift Relief Sign-off
    outgoing_operator_signed = fields.Boolean(string='Outgoing Shift Handover Formally Signed', default=False)
    outgoing_sign_time = fields.Datetime(string='Outgoing Handover Time')
    relieving_operator_id = fields.Many2one('res.users', string='Incoming Relieving Operator')
    relieving_operator_signed = fields.Boolean(string='Incoming Shift Relief Formally Accepted', default=False)
    relieving_sign_time = fields.Datetime(string='Relief Accepted Time')

    state = fields.Selection([
        ('open', 'Shift In Progress (Logging Active)'),
        ('handover_review', 'Handover Review & Debrief'),
        ('relieved', 'Shift Relieved & Closed'),
    ], string='Log Status', default='open', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.operator.log') or _('LOG-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def _compute_active_permits(self):
        for rec in self:
            rec.active_permits_count = self.env['hse.permit'].search_count([
                ('location_id', '=', rec.location_id.id),
                ('state', 'in', ['approved', 'active'])
            ]) if 'hse.permit' in self.env and rec.location_id else 0

    def _compute_active_bypasses(self):
        for rec in self:
            rec.active_bypasses_count = self.env['hse.bypass'].search_count([
                ('location_id', '=', rec.location_id.id),
                ('state', '=', 'active')
            ]) if 'hse.bypass' in self.env and rec.location_id else 0

    def action_initiate_handover(self):
        self.write({
            'state': 'handover_review',
            'outgoing_operator_signed': True,
            'outgoing_sign_time': fields.Datetime.now(),
        })

    def action_accept_handover(self):
        if not self.relieving_operator_id:
            raise UserError(_("Please identify the incoming relieving operator before accepting handover."))
        self.write({
            'state': 'relieved',
            'relieving_operator_signed': True,
            'relieving_sign_time': fields.Datetime.now(),
        })


class HSEOperatorLogEntry(models.Model):
    _name = 'hse.operator.log.entry'
    _description = 'Operator Shift Log Entry'
    _order = 'entry_time desc, id desc'

    log_id = fields.Many2one('hse.operator.log', string='Shift Log', ondelete='cascade', required=True)
    entry_time = fields.Datetime(string='Log Timestamp', default=fields.Datetime.now, required=True)
    category = fields.Selection([
        ('routine', 'Routine Operational Event / Shift Walk'),
        ('upset', 'Process Upset / Rate Change'),
        ('alarm', 'High / Critical Process Alarm Tripped'),
        ('bypass', 'Safety System Inhibit / Override Applied'),
        ('trip', 'Equipment Trip / Unplanned Shutdown'),
        ('maintenance', 'Maintenance Crew Handover / PTW Handback'),
        ('environmental', 'Flaring / Environmental Release'),
        ('weather', 'Adverse Weather / Environmental Condition'),
    ], string='Event Category', default='routine', required=True)

    priority = fields.Selection([
        ('low', 'Low / Information'),
        ('medium', 'Notice / Warning'),
        ('high', 'High / Critical Operational Upset'),
    ], string='Priority', default='low')

    asset_id = fields.Many2one('assets.form', string='Asset / Equipment Involved')
    description = fields.Text(string='Event Description & Operator Actions Taken', required=True)
    logged_by_id = fields.Many2one('res.users', string='Logged By', default=lambda self: self.env.user)


class HSEOperatorLogRound(models.Model):
    _name = 'hse.operator.log.round'
    _description = 'Operator Inspection Round & Field Reading'
    _order = 'id asc'

    log_id = fields.Many2one('hse.operator.log', string='Shift Log', ondelete='cascade', required=True)
    asset_id = fields.Many2one('assets.form', string='Equipment / Tag', required=True)
    parameter_name = fields.Char(string='Parameter (e.g. Suction Pressure, Bearing Temp)', required=True)
    recorded_value = fields.Float(string='Field Value', required=True)
    unit_of_measure = fields.Char(string='Unit (PSI, °C, RPM, Bar)', default='PSI')
    min_limit = fields.Float(string='Normal Min Limit')
    max_limit = fields.Float(string='Normal Max Limit')
    is_abnormal = fields.Boolean(string='Out of Operating Limits (Alarm)', compute='_compute_abnormal', store=True)

    @api.depends('recorded_value', 'min_limit', 'max_limit')
    def _compute_abnormal(self):
        for rec in self:
            if rec.max_limit and rec.recorded_value > rec.max_limit:
                rec.is_abnormal = True
            elif rec.min_limit and rec.recorded_value < rec.min_limit:
                rec.is_abnormal = True
            else:
                rec.is_abnormal = False


class HSEOperatorLogAlarm(models.Model):
    _name = 'hse.operator.log.alarm'
    _description = 'Shift Handover Defeated & Standing Alarms Log (ISA 18.2 / EEMUA 191)'
    _order = 'priority desc, tag_number asc'

    log_id = fields.Many2one('hse.operator.log', string='Shift Log', ondelete='cascade', required=True)
    tag_number = fields.Char(string='Alarm Tag # (e.g. TAHH-104, PAHH-202)', required=True)
    description = fields.Char(string='Alarm Service / Description', required=True)
    priority = fields.Selection([
        ('critical', 'Critical (Emergency Shutdown / Safeguard)'),
        ('high', 'High (Immediate Operator Action Required)'),
        ('medium', 'Medium (Prompt Action Required)'),
        ('low', 'Low / Advisory'),
    ], string='Alarm Priority', default='high', required=True)

    status = fields.Selection([
        ('standing', 'Standing Active Alarm (Continuous Unresolved Condition)'),
        ('suppressed', 'Shelved / Suppressed by Operator (Time Limited)'),
        ('defeated', 'Bypassed / Hardware Defeated Interlock'),
    ], string='Alarm State', default='standing', required=True)

    reason = fields.Char(string='Reason for Standing / Suppressed State', required=True)
    compensating_measure = fields.Char(string='Compensating Manual Monitoring / Watch')

