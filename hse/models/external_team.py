from odoo import models, fields

class ExternalTeam(models.Model):
    _name = 'external.team'
    _description = 'External Team'

    name = fields.Char(string='Name', required=True)