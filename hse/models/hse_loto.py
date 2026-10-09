# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HSELotoPlan(models.Model):
    _name = 'hse.loto.plan'
    _description = 'Lock Out & Tag Out Isolation Plan (LOTO)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='LOTO Plan Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Isolation Scheme Title', required=True, tracking=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant / Operating Area', required=True)
    asset_id = fields.Many2one('assets.form', string='Target Equipment / Asset')
    system_description = fields.Text(string='System / Boundary Description', required=True)

    # Energy Sources Checked
    energy_electrical = fields.Boolean(string='Electrical Energy (High/Low Voltage)')
    energy_mechanical = fields.Boolean(string='Mechanical / Kinetic Energy (Rotating / Springs)')
    energy_hydraulic = fields.Boolean(string='Hydraulic Pressure')
    energy_pneumatic = fields.Boolean(string='Pneumatic / Compressed Air')
    energy_chemical = fields.Boolean(string='Chemical / Toxic Fluids')
    energy_thermal = fields.Boolean(string='Thermal (High Temp Steam / Cryogenic)')
    energy_gravitational = fields.Boolean(string='Gravitational Potential (Elevated Loads/Weights)')

    # Step-by-Step Isolation Points
    point_ids = fields.One2many('hse.loto.point', 'plan_id', string='Isolation Points')

    # Zero Energy State Verification
    zero_energy_method = fields.Selection([
        ('multimeter', 'Multimeter Voltage Test (Zero Potential)'),
        ('bleed_vent', 'Open Bleeder / Vent to Zero PSI'),
        ('visual_drain', 'Visual Drain Verification & Spool Removal'),
        ('try_start', 'Pushbutton Local Start Test (Zero Movement)'),
        ('combination', 'Multi-Method Zero Energy Verification'),
    ], string='Zero Energy Verification Method', default='combination', required=True)
    zero_energy_verified = fields.Boolean(string='Zero Energy State Formally Verified', default=False, tracking=True)
    zero_energy_verified_by = fields.Many2one('res.users', string='Verified By (Authorized Person)')
    zero_energy_verified_date = fields.Datetime(string='Zero Energy Verification Date')

    # Master Lockbox
    master_lockbox_no = fields.Char(string='Master Lockbox / Key Safe ID')
    lead_isolation_officer_id = fields.Many2one('res.users', string='Authorized Isolation Officer', required=True, default=lambda self: self.env.user)

    # De-isolation Safety Checks
    deisolate_inspected_by = fields.Many2one('res.users', string='De-Isolation Inspected By')
    deisolate_tools_cleared = fields.Boolean(string='All Locks, Tags, Grounds & Tools Cleared', default=False)
    deisolate_guards_replaced = fields.Boolean(string='Machine Guards, Covers & Access Hatches Secured', default=False)
    deisolate_personnel_clear = fields.Boolean(string='All Personnel Accounted for & Outside Danger Zone', default=False)
    deisolate_datetime = fields.Datetime(string='De-Isolation Sign-off Time')

    state = fields.Selection([
        ('draft', 'Draft Isolation Scheme'),
        ('approved', 'Scheme Approved'),
        ('isolated', 'Equipment Isolated & Locked Out'),
        ('de-isolated', 'De-Isolated & Restored to Service'),
        ('cancelled', 'Cancelled'),
    ], string='Isolation State', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.loto.plan') or _('LOTO-') + str(self.env['ir.sequence'].next_by_code('seq_observation'))
        return super().create(vals_list)

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_isolate(self):
        if not self.zero_energy_verified:
            raise UserError(_("You must verify and confirm the Zero Energy State before placing the plan into Isolated state."))
        self.write({'state': 'isolated'})

    def action_deisolate(self):
        if not (self.deisolate_tools_cleared and self.deisolate_guards_replaced and self.deisolate_personnel_clear):
            raise UserError(_("Before de-isolating, you must verify all three safety checks:\n1. All tools & grounds cleared\n2. Machine guards replaced\n3. All personnel clear of the danger zone."))
        self.write({
            'state': 'de-isolated',
            'deisolate_inspected_by': self.env.user.id,
            'deisolate_datetime': fields.Datetime.now(),
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class HSELotoPoint(models.Model):
    _name = 'hse.loto.point'
    _description = 'LOTO Physical Isolation Point'
    _order = 'sequence asc, id asc'

    plan_id = fields.Many2one('hse.loto.plan', string='LOTO Plan', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Step #', default=10)
    point_identifier = fields.Char(string='Tag / Equipment ID (e.g. V-102, BKR-4A)', required=True)
    isolation_type = fields.Selection([
        ('valve_closed', 'Valve Locked Closed (Car Seal / Padlock)'),
        ('valve_open', 'Valve Locked Open (Bleed Path)'),
        ('breaker_open', 'Circuit Breaker Locked Open (Padlock)'),
        ('fuse_removed', 'Fuses Pulled & Stored'),
        ('blind_installed', 'Spectacle Blind / Spade Flange Inserted'),
        ('disconnect_plug', 'Physical Disconnect / Plug Locked'),
    ], string='Isolation Method', required=True, default='valve_closed')
    location_desc = fields.Char(string='Physical Location / Floor / MCC')
    lock_number = fields.Char(string='Padlock Number', required=True)
    tag_number = fields.Char(string='Danger Tag Number', required=True)
    applied_by = fields.Char(string='Applied By (Tech Name)')
    applied_datetime = fields.Datetime(string='Applied Time', default=fields.Datetime.now)
    verified_by = fields.Char(string='Witnessed / Verified By')
    is_restored = fields.Boolean(string='De-isolated / Normalized', default=False)
