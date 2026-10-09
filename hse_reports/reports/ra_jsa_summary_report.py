from odoo import fields, models, api

class HseReportXlsx(models.AbstractModel):
    _name = 'report.hse.wizard.report.hse_ra_jsa_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):

        sheet = workbook.add_worksheet('Summary Reports')
        floating_point = workbook.add_format({'num_format': '#,##0.00'})
        bold = workbook.add_format({'bold': True})
        centered_format = workbook.add_format({'align': 'center', 'valign': 'vcenter','bold': True})

        # Define the headings
        headings = ['Name',  'type']
        for x in data:
            print(x)
        col = 0
        for i in headings:
            if col <= len(headings):
                row = 2
                col += 1
                sheet.write(row, col, i, bold)
            else:
                break

