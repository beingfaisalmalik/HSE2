from odoo import models


class HseRaJsaReportXlsx(models.AbstractModel):
    _name = 'report.hse.wizard.report.hse_ra_jsa_report'
    _description = 'RA/JSA Summary Report XLSX'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet('RA-JSA')
        bold = workbook.add_format({'bold': True})
        wrap = workbook.add_format({'text_wrap': True, 'valign': 'top'})

        headings = ['Name', 'Type', 'Description', 'Due Date', 'Department',
                    'Responsible Person', 'Team Members', 'Status', 'Priority']
        for col, heading in enumerate(headings):
            sheet.write(0, col, heading, bold)
        sheet.set_column(0, 0, 32)
        sheet.set_column(1, 1, 16)
        sheet.set_column(2, 2, 55)
        sheet.set_column(3, 3, 14)
        sheet.set_column(4, 5, 24)
        sheet.set_column(6, 6, 36)
        sheet.set_column(7, 8, 14)

        rows = (data or {}).get('data') or {}
        row_index = 1
        for rec_id in sorted(rows, key=lambda rid: str(rid)):
            rec = rows[rec_id] or {}
            values = [
                rec.get('name') or '',
                rec.get('type') or '',
                rec.get('description') or '',
                rec.get('due_date') or '',
                rec.get('select_department.name') or '',
                rec.get('responsible_person.name') or '',
                rec.get('team_members') or '',
                rec.get('state') or '',
                rec.get('set_priority') or '',
            ]
            for col, value in enumerate(values):
                fmt = wrap if col == 2 else None
                sheet.write(row_index, col, str(value), fmt)
            row_index += 1

        if row_index == 1:
            sheet.write(1, 0, 'No RA/JSA records found for the selected date range.', bold)
