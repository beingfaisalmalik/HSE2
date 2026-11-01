# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HseIncidentLog(models.Model):
    _name = 'hse.incident.log'
    _inherit = ['hse.log.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Incident Log (Non-Injury)'
    _order = 'date desc, name desc'
    _rec_name = 'name'

    name = fields.Char(string='Incident ID', required=True, copy=False, default='/')
    incident_type = fields.Selection(
        [('property_damage', 'Property Damage'),
         ('environmental', 'Environmental'),
         ('fire_explosion', 'Fire / Explosion'),
         ('process_safety', 'Process Safety'),
         ('security', 'Security'),
         ('other', 'Other')],
        string='Type', required=True, default='other')
    area_asset = fields.Char(string='Area / Asset Involved')
    estimated_impact = fields.Char(
        string='Estimated Impact', help="Free text, e.g. 'PKR 60,000 est.'")
    root_cause = fields.Text(string='Root Cause')

    _sql_constraints = [('name_uniq', 'unique(name)', 'Incident ID must be unique.')]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].next_by_code('hse.incident.log')
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = seq or '/'
                seq = self.env['ir.sequence'].next_by_code('hse.incident.log')
        return super().create(vals_list)

    def _type_label(self):
        return self._selection_label('incident_type')
