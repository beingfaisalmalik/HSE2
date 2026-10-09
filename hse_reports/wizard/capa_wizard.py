from odoo import models, fields, api

class CAPAWizard(models.Model):
    _name = 'capa.wizard'
    _description = 'CAPA Wizard'

    start_date = fields.Date(string='From Date', store=True)
    end_date = fields.Date(string='To Date', store=True)

    def printhsereport(self):
        print(self.start_date)

        capa_data = self.env['hse.capa.model'].search([('create_date', '>=', self.start_date),('create_date', '<=', self.end_date)])
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
        print(data)

        return self.env.ref('hse_reports.capa_report_action').report_action(self, data=data)