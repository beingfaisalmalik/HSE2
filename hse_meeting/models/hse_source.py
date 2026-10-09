from odoo import models, fields

class HseSource(models.Model):
    _name = 'hse.source'
    _description = 'HSE Source Records'

    name = fields.Char("Description")
    code = fields.Char(
        string='Code',
        required=False)