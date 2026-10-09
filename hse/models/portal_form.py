from odoo import models, fields

class CustomForm(models.Model):
    _name = 'my.custom.model'
    _description = 'Custom Form Model'

    name = fields.Char('Name', required=True)
    email = fields.Char('Email', required=True)
    message = fields.Text('Message')
