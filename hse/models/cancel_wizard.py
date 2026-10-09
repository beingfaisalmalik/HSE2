from odoo import models, fields

class CancelWizard(models.TransientModel):
    _name = 'ra_jsa.cancel_wizard'
    _description = 'Cancel Wizard'

    reason = fields.Text(string='Reason for Cancellation', required=True)

    def action_cancel(self):
        # Get the active record (RA/JSA record) and set its state to 'cancelled' with the cancellation reason
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        record = self.env[active_model].browse(active_id)
        record.write({'state': 'cancelled', 'reason_for_cancel': self.reason})

        return {'type': 'ir.actions.act_window_close'}
