from odoo import models, fields

class SeverityLevel(models.Model):
    _name = 'severity.level'
    _description = 'Severity Level'

    name = fields.Char(string='Severity Level', required=True)
    description = fields.Text(string='Description')
