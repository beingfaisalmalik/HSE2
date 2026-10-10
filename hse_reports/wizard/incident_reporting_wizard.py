from odoo import models, fields
from odoo.addons.hse.tools.report_dates import date_range_domain

class IncidentReportingWizard(models.Model):
    _name = 'incident.reporting.wizard'
    _description = 'Incident Reporting Wizard'

    start_date = fields.Date(string='From Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date(string='To Date', default=fields.Date.context_today, required=True)

    def printhsereport(self):
        self.ensure_one()

        incident_reporting_data = self.env['incident.reporting'].search(date_range_domain(self.env, 'create_date', self.start_date, self.end_date))
        dic = {}
        for rec in incident_reporting_data:
            dic[rec.id] = {

                'name': rec.name,
                'incident_type': rec.incident_type,
                'ir_description': rec.ir_description,
                'incident_report_date': rec.incident_report_date,
                'near_miss_harm_level': rec.near_miss_harm_level,
                'assigned_to.name': rec.assigned_to.name,
                'injury_type': rec.injury_type,
            }

        data = {'data': dic}

        return self.env.ref('hse_reports.incident_reporting_report_action').report_action(self, data=data)
