from odoo import models, fields
from odoo.addons.hse.tools.report_dates import date_range_domain

class CAPAWizard(models.Model):
    _name = 'capa.wizard'
    _description = 'CAPA Wizard'

    start_date = fields.Date(string='From Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date(string='To Date', default=fields.Date.context_today, required=True)

    def printhsereport(self):
        self.ensure_one()

        capa_data = self.env['hse.capa.model'].search(date_range_domain(self.env, 'create_date', self.start_date, self.end_date))
        dic = {}
        for rec in capa_data:
            dic[rec.id] = {

                'name': rec.name,
                'ra_reference_number': rec.ra_reference_number,
                'select_capa': rec.select_capa,
                'status': rec.status,
                'due_date': rec.due_date,
                'responsible_user_id.name': rec.responsible_user_id.name,
                'completion_date': rec.completion_date,

            }

        data = {'data': dic}

        return self.env.ref('hse_reports.capa_report_action').report_action(self, data=data)
