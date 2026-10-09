from odoo import models, fields, api
from odoo.exceptions import UserError


class TransitWizard(models.TransientModel):
    _name = 'transit.wizard'
    _description = 'Transit Date Range Wizard'

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    department_ids = fields.Many2many('hse.meeting.department', string="Departments", required=True)

    def print_report(self):
        if self.from_date > self.to_date:
            raise UserError("From Date cannot be after To Date.")

        data = {
            'from_date': self.from_date.strftime('%d %B %Y'),
            'to_date': self.to_date.strftime('%d %B %Y'),
            'department_ids': self.department_ids.ids,
        }

        return self.env.ref('hse_meeting.action_transit_report_pdf').report_action(self, data=data)
