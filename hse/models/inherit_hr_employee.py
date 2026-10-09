from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    rel_inc_inv_ids = fields.Many2one(
        comodel_name='incident.investigation',
        string='Rel Incident Investigation',
        required=False)