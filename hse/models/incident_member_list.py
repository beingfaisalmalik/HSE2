from odoo import models, fields, api

class IncidentMemberList(models.Model):
    _name = 'incident.member.list'
    _description = 'Incident Member List'

    name = fields.Char(
        string='Name', 
        required=False)
    
    description = fields.Text(
        string="Description",
        required=False)




