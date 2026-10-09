from odoo import models, fields

class Assets(models.Model):
    _name = 'assets.form'
    _description = 'Assets Form'

    name = fields.Char('Asset Name', required=True)
    description = fields.Text('Description')
    assets_type = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment'),
        ('building', 'Building'),
    ], string='Asset Type')
    location = fields.Char('Location')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active')
