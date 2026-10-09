from odoo import models

class HseMeetingReport(models.AbstractModel):
    _name = 'report.hse_meeting.report_transit_filtered_pdf'
    _description = 'Hse Meeting Report'

    def _get_report_values(self, docids, data=None):
        from_date = data['from_date']
        to_date = data['to_date']
        department_ids = data.get('department_ids', [])

        # Build the domain
        domain = [
            ('meeting_datetime', '>=', from_date),
            ('meeting_datetime', '<=', to_date),
        ]
        if department_ids:
            domain.append(('department_id', 'in', department_ids))

        docs = self.env['hse.meeting'].search(domain)

        return {
            'doc_ids': docs.ids,
            'doc_model': 'hse.meeting',
            'docs': docs,
            'data': data,
        }
