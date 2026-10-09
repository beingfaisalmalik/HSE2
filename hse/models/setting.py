from odoo import models, fields

class HazardSetting(models.Model):
    _name = 'hazard.setting.model'
    _description = 'Hazard Settings'

    name = fields.Char(string="Hazard Name", required=True)  # Hazard name
    description = fields.Text(string="Description")  # Hazard description
    severity = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string="Severity", default='low')  # Severity level
    category = fields.Selection([('chemical', 'Chemical'), ('physical', 'Physical'), ('biological', 'Biological'), ('ergonomic', 'Ergonomic')], string="Category")  # Hazard category
    is_active = fields.Boolean(string="Active", default=True)  # Whether hazard is active or not
