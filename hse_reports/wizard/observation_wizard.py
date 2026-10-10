from odoo import models, fields
from odoo.addons.hse.tools.report_dates import date_range_domain

class ObservationWizard(models.TransientModel):
    #
    _name = 'observation.wizard'
    _description = 'Observation Wizard'

    start_date = fields.Date(string='From Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date(string='To Date', default=fields.Date.context_today, required=True)

    def printhsereport(self):
        self.ensure_one()

        observation_data=self.env['observation.observation'].search(date_range_domain(self.env, 'create_date', self.start_date, self.end_date))
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

        return self.env.ref('hse_reports.observation_report_action').report_action(self,data=data)
