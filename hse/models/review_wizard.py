from odoo import models, fields

class ReviewWizard(models.TransientModel):
    _name = 'ra_jsa.review_wizard'
    _description = 'Review Wizard'

    reason = fields.Text(string='Reason for Review', required=True)

    def action_cancel(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        record = self.env[active_model].browse(active_id)
        record.write({'state': 'review', 'reason_for_review': self.reason})

        return {'type': 'ir.actions.act_window_close'}
