from odoo import models, fields
from odoo.addons.hse.tools.report_dates import date_range_domain


class TransitWizard(models.TransientModel):
    _name = 'transit.wizard'
    _description = 'Transit Date Range Wizard'

    from_date = fields.Date(string='From Date', required=True, default=fields.Date.context_today)
    to_date = fields.Date(string='To Date', required=True, default=fields.Date.context_today)
    department_ids = fields.Many2many('hse.meeting.department', string="Departments", required=True)

    def print_report(self):
        self.ensure_one()
        date_range_domain(self.env, 'meeting_datetime', self.from_date, self.to_date)

        data = {
            'from_date': fields.Date.to_string(self.from_date),
            'to_date': fields.Date.to_string(self.to_date),
            'department_ids': self.department_ids.ids,
        }

        return self.env.ref('hse_meeting.action_transit_report_pdf').report_action(self, data=data)
