# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HseCorrectiveAction(models.Model):
    _name = 'hse.corrective.action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Corrective Action'
    _order = 'state, target_date, name'
    _rec_name = 'name'

    name = fields.Char(string='CA ID', required=True, copy=False, default='/')
    related_ref = fields.Char(
        string='Related Log Entry ID', index=True,
        help="Excel-style reference (e.g. INJ-001, UAC-002). The dashboard "
             "attributes this action to the month of the linked entry's date.")
    related_date = fields.Date(
        string='Linked Entry Date', compute='_compute_related', store=False,
        help="Date of the log entry this action is linked to (via Related Log "
             "Entry ID or via the entry's Corrective Action field).")
    related_display = fields.Char(
        string='Linked Entry', compute='_compute_related', store=False)
    action_description = fields.Text(string='Action Description', required=True)
    responsible_person = fields.Char(string='Responsible Person')
    target_date = fields.Date(string='Target Date')
    state = fields.Selection(
        [('open', 'Open'), ('in_progress', 'In Progress'), ('closed', 'Closed')],
        string='Status', default='open', required=True, tracking=True)
    closure_date = fields.Date(string='Closure Date', tracking=True)
    verification = fields.Text(string='Verification / Comments')
    overdue = fields.Boolean(
        string='Overdue', compute='_compute_overdue', store=False,
        help="Open past its target date (Excel 'Overdue?' column).")

    _sql_constraints = [('name_uniq', 'unique(name)', 'CA ID must be unique.')]

    # ------------------------------------------------------------------
    # Related-entry resolution — mirrors Excel CalcRows AO
    # (MATCH against Injury → UnsafeAct → NearMiss → Incident)
    # ------------------------------------------------------------------
    def _resolve_related(self):
        self.ensure_one()
        # Direct Many2one links set from the log entries
        link_fields = [
            ('hse.injury.log', 'corrective_action_id'),
            ('hse.uac.log', 'corrective_action_id'),
            ('hse.near.miss.log', 'corrective_action_id'),
            ('hse.incident.log', 'corrective_action_id'),
        ]
        for model, field_name in link_fields:
            rec = self.env[model].search(
                [(field_name, '=', self.id)], limit=1)
            if rec:
                return rec, "%s (%s)" % (rec.name, model)
        # Fall back to the text reference (Excel-style Related Log Entry ID)
        if self.related_ref:
            for model in ('hse.injury.log', 'hse.uac.log',
                          'hse.near.miss.log', 'hse.incident.log'):
                rec = self.env[model].search([('name', '=', self.related_ref)], limit=1)
                if rec:
                    return rec, "%s (%s)" % (rec.name, model)
        return None, False

    @api.depends('related_ref')
    def _compute_related(self):
        for ca in self:
            rec, label = ca._resolve_related()
            ca.related_date = rec.date if rec else False
            ca.related_display = label or (ca.related_ref or '')

    @api.depends('state', 'target_date', 'closure_date')
    def _compute_overdue(self):
        today = fields.Date.context_today(self)
        for ca in self:
            ca.overdue = bool(
                ca.state != 'closed' and ca.target_date and ca.target_date < today)

    # ------------------------------------------------------------------
    # Workflow: Open → In Progress → Closed
    # ------------------------------------------------------------------
    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_close(self):
        today = fields.Date.context_today(self)
        for ca in self:
            vals = {'state': 'closed'}
            if not ca.closure_date:
                vals['closure_date'] = today
            ca.write(vals)

    def action_reopen(self):
        self.write({'state': 'open', 'closure_date': False})

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].next_by_code('hse.corrective.action')
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = seq or '/'
                seq = self.env['ir.sequence'].next_by_code('hse.corrective.action')
        records = super().create(vals_list)
        # Schedule a review activity when a target date is set (workflow)
        for ca in records:
            if ca.target_date and ca.state != 'closed':
                ca.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=ca.target_date,
                    summary=_('Complete corrective action %s') % ca.name)
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'target_date' in vals:
            for ca in self:
                activity = ca.activity_ids.filtered(
                    lambda a: a.activity_type_id.code == 'mail.mail_activity_data_todo'
                    and not a.date_deadline == vals.get('target_date'))
                if ca.target_date and ca.state != 'closed' and not activity:
                    ca.activity_schedule(
                        'mail.mail_activity_data_todo',
                        date_deadline=ca.target_date,
                        summary=_('Complete corrective action %s') % ca.name)
        return res
