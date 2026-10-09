from odoo import models,fields,api

class InjuryCreateLevel(models.Model):
    _name = "injury.create.level"
    _description = "Injury Create/Level"
    
    name = fields.Char(
        string='Name', 
        required=False)
    code = fields.Char(
        string='Code', 
        required=False)
    description = fields.Text(
        string="Description",
        required=False)