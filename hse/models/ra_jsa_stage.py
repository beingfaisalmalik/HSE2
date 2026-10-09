from odoo import models, fields

class RaJsaStage(models.Model):
    _name = 'ra_jsa.stage'
    _description = 'RA JSA Stages'
    _order = 'sequence, id'  # Sorting stages

    name = fields.Char('Stage Name', required=True)
    sequence = fields.Integer('Sequence', default=1)  # Sorting order
    fold = fields.Boolean('Folded in Kanban', default=False)  # Collapse the column
    color = fields.Integer('Color')
