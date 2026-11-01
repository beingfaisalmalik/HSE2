# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HseNearMissLog(models.Model):
    _name = 'hse.near.miss.log'
    _inherit = ['hse.log.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Near-Miss Log'
    _order = 'date desc, name desc'
    _rec_name = 'name'

    name = fields.Char(string='Near-Miss ID', required=True, copy=False, default='/')
    potential_severity = fields.Selection(
        [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        string='Potential Severity', default='medium')
    reported_by = fields.Char(string='Reported By')

    _sql_constraints = [('name_uniq', 'unique(name)', 'Near-Miss ID must be unique.')]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].next_by_code('hse.near.miss.log')
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = seq or '/'
                seq = self.env['ir.sequence'].next_by_code('hse.near.miss.log')
        return super().create(vals_list)
