from odoo import models, fields, api

class IncidentInvestigationWizard(models.Model):
    _name = 'incident.investigation.wizard'
    _description = 'Incident Investigation Wizard'

    start_date = fields.Date(string='From Date', store=True)
    end_date = fields.Date(string='To Date', store=True)

    def printhsereport(self):
        print(self.start_date)

        incident_investigation_data = self.env['incident.investigation'].search(
            [('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)])
        dic = {}
        for rec in incident_investigation_data:
            dic[rec.id] = {

                'ref_name': rec.ref_name,
                'incident_id.name': rec.incident_id.name,
                'investigation_leader.name': rec.investigation_leader.name,
                'target_date': rec.target_date,
                'actual_completion_date': rec.actual_completion_date,
                'state': rec.state,
            }

        data = {'data': dic}
        print(data)

        return self.env.ref('hse_reports.incident_investigation_report_action').report_action(self, data=data)





