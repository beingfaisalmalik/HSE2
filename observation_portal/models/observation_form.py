from odoo import models, fields

class ObservationForm(models.Model):
    _name = 'observation.form'
    _description = 'Observation Portal Form Data'

    name = fields.Char('Name', required=True)
    email = fields.Char('Email', required=True)
    observation = fields.Text('Observation', required=True)
    user_id = fields.Many2one('res.users', string='Submitted by', default=lambda self: self.env.user)
