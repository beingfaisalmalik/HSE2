from odoo import models, fields

class IncidentCategory(models.Model):
    _name = 'incident.category'
    _description = 'Incident Category'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')