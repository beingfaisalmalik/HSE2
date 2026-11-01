# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HseSafetySettings(models.Model):
    """Global dashboard settings — mirrors the Excel 'Settings' sheet
    (C3 reporting year, C4 rate base, C5 today)."""
    _name = 'hse.safety.settings'
    _description = 'HSE Safety Dashboard Settings'
    _rec_name = 'label'

    label = fields.Char(default='Dashboard Settings', required=True, help='Internal label')
    reporting_year = fields.Integer(
        string='Reporting Year', default=lambda self: fields.Date.context_today(self).year,
        required=True,
        help='Year the dashboard reports on (Excel Settings!C3).')
    rate_base = fields.Float(
        string='Rate Base (man-hours)', default=200000.0, required=True,
        help='Hours base for LTIFR / TRIR / Severity, per million-equivalent practice '
             'used by the workbook (Excel Settings!C4).')

    @api.model
    def get_settings(self):
        """Singleton accessor — creates the record on first use."""
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({'label': 'Dashboard Settings'})
        return settings
