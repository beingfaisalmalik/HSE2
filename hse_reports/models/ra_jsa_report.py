
from odoo import models, fields

class HseReports(models.Model):
    _name = 'hse_reports.hse_reports'
    _description = 'HSE Reports'

    name = fields.Char(string="Report Name")

