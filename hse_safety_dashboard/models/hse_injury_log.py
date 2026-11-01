# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HseInjuryLog(models.Model):
    _name = 'hse.injury.log'
    _inherit = ['hse.log.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Injury Log'
    _order = 'date desc, name desc'
    _rec_name = 'name'

    name = fields.Char(string='Injury ID', required=True, copy=False, default='/')
    injury_type = fields.Selection(
        [('lti', 'Lost Time Injury'),
         ('mtc', 'Medical Treatment Case'),
         ('first_aid', 'First Aid Case')],
        string='Type', required=True, default='mtc')
    person_involved = fields.Char(string='Person Involved')
    lost_workdays = fields.Integer(string='Lost Workdays', default=0)
    root_cause = fields.Text(string='Root Cause')

    _sql_constraints = [('name_uniq', 'unique(name)', 'Injury ID must be unique.')]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].next_by_code('hse.injury.log')
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = seq or '/'
                seq = self.env['ir.sequence'].next_by_code('hse.injury.log')
        return super().create(vals_list)

    def _type_label(self):
        return self._selection_label('injury_type')
