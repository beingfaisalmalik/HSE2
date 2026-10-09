from odoo import models, fields


class ReqExtentDate(models.Model):
    _name = 'req.date.ext'
    _description = 'Request Extended Date'

    req_ext_date = fields.Date(string='Request Extention Date')
    reason = fields.Text(string='Reason for Extensiont')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending')

    rel_ra_jsa = fields.Many2one(
        comodel_name='ra_jsa.model',
        string='rel_ra_jsa',
        required=False)