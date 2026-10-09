from odoo import models, fields

class LocationForm(models.Model):
    _name = 'location.form'
    _description = 'Location Form'

    name = fields.Char(string='Location Name', required=False)
    address = fields.Char(string='Street Address', required=False)
    city = fields.Char(string='City')
    country = fields.Char(string='Country', required=False)
