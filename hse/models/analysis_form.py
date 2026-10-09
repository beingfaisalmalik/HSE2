from odoo import models, fields

class AnalysisForm(models.Model):
    _name = 'analysis.form'
    _description = 'Analysis Form'

    name = fields.Char(string='Name', required=True)