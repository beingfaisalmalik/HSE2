# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HseUacLog(models.Model):
    _name = 'hse.uac.log'
    _inherit = ['hse.log.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Unsafe Act & Unsafe Condition Log'
    _order = 'date desc, name desc'
    _rec_name = 'name'

    name = fields.Char(string='Observation ID', required=True, copy=False, default='/')
    uac_type = fields.Selection(
        [('unsafe_act', 'Unsafe Act'), ('unsafe_condition', 'Unsafe Condition')],
        string='Type', required=True, default='unsafe_act',
        help="Controlled drop-down — replaces the Excel free-text column that "
             "allowed invalid labels (data-health check 8).")
    reported_by = fields.Char(string='Reported By')
    immediate_action = fields.Text(string='Immediate Action Taken')

    _sql_constraints = [('name_uniq', 'unique(name)', 'Observation ID must be unique.')]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].next_by_code('hse.uac.log')
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = seq or '/'
                seq = self.env['ir.sequence'].next_by_code('hse.uac.log')
        return super().create(vals_list)

    def _type_label(self):
        return self._selection_label('uac_type')
