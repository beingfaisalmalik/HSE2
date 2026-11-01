from odoo import models


class HseObservationReportXlsx(models.AbstractModel):
    _name = 'report.hse.observation.wizard.report.hse_observation_report'
    _description = 'Observation Summary Report XLSX'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet('Observations')
        bold = workbook.add_format({'bold': True})
        wrap = workbook.add_format({'text_wrap': True, 'valign': 'top'})

        headings = ['Name', 'Observation Type', 'Observation', 'Observation Date',
                    'Observer', 'Status']
        for col, heading in enumerate(headings):
            sheet.write(0, col, heading, bold)
        sheet.set_column(0, 0, 28)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 60)
        sheet.set_column(3, 3, 18)
        sheet.set_column(4, 4, 24)
        sheet.set_column(5, 5, 14)

        rows = (data or {}).get('data') or {}
        row_index = 1
        for rec_id in sorted(rows, key=lambda rid: str(rid)):
            rec = rows[rec_id] or {}
            values = [
                rec.get('name') or '',
                rec.get('observation_type') or '',
                rec.get('observation') or '',
                rec.get('observation_date') or '',
                rec.get('observer_id.name') or '',
                rec.get('state') or '',
            ]
            for col, value in enumerate(values):
                fmt = wrap if col == 2 else None
                sheet.write(row_index, col, str(value), fmt)
            row_index += 1

        if row_index == 1:
            sheet.write(1, 0, 'No observations found for the selected date range.', bold)
