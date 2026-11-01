# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HseLogMixin(models.AbstractModel):
    """Common behaviour of the four event logs (Injury, Near Miss,
    Unsafe Act/Condition, Incident) — mirrors the Excel entry sheets:
    ID · Date · (Type) · Department · Description · … · CA · Status."""
    _name = 'hse.log.mixin'
    _description = 'HSE Log Mixin'

    date = fields.Date(
        string='Date', index=True,
        help="Date of the entry. Entries with no date (or a date outside the "
             "reporting year) are flagged by the data-health checks.")
    department = fields.Char(string='Department')
    description = fields.Text(string='Description / Observation')
    corrective_action_id = fields.Many2one(
        'hse.corrective.action', string='Corrective Action',
        ondelete='set null', index=True)
    status = fields.Selection(
        [('open', 'Open'), ('closed', 'Closed')],
        string='Status', default='open', required=True)

    def action_mark_closed(self):
        self.write({'status': 'closed'})

    def action_mark_open(self):
        self.write({'status': 'open'})

    def _selection_label(self, field_name):
        """Human label of a selection value on this record."""
        return dict(self._fields[field_name].selection).get(
            getattr(self, field_name), '') or ''
