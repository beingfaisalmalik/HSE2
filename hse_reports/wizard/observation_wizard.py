from odoo import models, fields, api

class ObservationWizard(models.TransientModel):
    #
    _name = 'observation.wizard'
    _description = 'Observation Wizard'

    start_date = fields.Date(string='From Date', store=True)
    end_date = fields.Date(string='To Date', store=True)

    def printhsereport(self):
        print(self.start_date)


        observation_data=self.env['observation.observation'].search([('create_date', '>=', self.start_date),
            ('create_date', '<=', self.end_date)])
        dic={}
        for rec in observation_data:
            dic[rec.id] = {

                'name': rec.name,
                'observation_type': rec.observation_type,
                'observation': rec.observation,
                'observation_date': rec.observation_date,
                'observer_id.name': rec.observer_id.name,
                'state': rec.state,
            }

        data = {'data': dic}
        print(data)

        return self.env.ref('hse_reports.observation_report_action').report_action(self,data=data)




