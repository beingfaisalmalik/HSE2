from odoo import models, fields, api

class HseWizardReport(models.TransientModel):
    #
    _name = 'hse.wizard.report'
    _description = 'HSE Wizard Report'

    start_date = fields.Date(string='From Date', store=True)
    end_date = fields.Date(string='To Date', store=True)

    def printhsereport(self):
        print(self.start_date)


        ra_jsa_data=self.env['ra_jsa.model'].search([('create_date', '>=', self.start_date),
            ('create_date', '<=', self.end_date)])
        dic={}
        for rec in ra_jsa_data:
            dic[rec.id] = {

                'name': rec.name,
                'type': rec.type,
                'description': rec.description,
                'due_date': rec.due_date,
                'select_department.name': rec.select_department.name,
                'responsible_person.name': rec.responsible_person.name,
                # 'team_member_id.name': rec.team_member_id.name,
                'team_members': ', '.join([member.name for member in rec.team_member_id]),
                'state': rec.state,
                'set_priority': rec.set_priority,
            }

        data = {'data': dic}
        print(data)

        return self.env.ref('hse_reports.ra_jsa_report_action').report_action(self,data=data)




