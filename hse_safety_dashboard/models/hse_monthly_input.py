# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HseMonthlyFigure(models.Model):
    """One row per (year, month): man-hours + leading indicators.
    Replaces the Excel 'KPI Calculations' column B and the 'Leading
    Indicators' sheet input cells — a single clean input table."""
    _name = 'hse.monthly.figure'
    _description = 'HSE Monthly Figures (Man-Hours & Leading Indicators)'
    _order = 'year, month'
    _rec_name = 'label'

    year = fields.Integer(string='Year', required=True, default=lambda self: fields.Date.context_today(self).year)
    month = fields.Selection(
        [(str(i), n) for i, n in enumerate(
            ['January', 'February', 'March', 'April', 'May', 'June', 'July',
             'August', 'September', 'October', 'November', 'December'], start=1)],
        string='Month', required=True)
    label = fields.Char(string='Label', compute='_compute_label', store=True)

    man_hours = fields.Float(string='Man-Hours Worked', default=0.0)
    planned_inspections = fields.Integer(string='Inspections Planned', default=0)
    completed_inspections = fields.Integer(string='Inspections Completed', default=0)
    toolbox_talks = fields.Integer(string='Toolbox Talks', default=0)
    ptw_issued = fields.Integer(string='Permits to Work Issued', default=0)
    training_hours = fields.Float(string='Training Hours', default=0.0)
    audit_score = fields.Float(
        string='Internal Audit Score', digits=(16, 2),
        help="Score between 0 and 1 (e.g. 0.92 = 92%).")

    _sql_constraints = [
        ('year_month_uniq', 'unique(year, month)',
         'Only one figure row is allowed per year/month.')]

    @api.depends('year', 'month')
    def _compute_label(self):
        for rec in self:
            rec.label = '%s %s' % (rec.month or '', rec.year or '')

    @api.constrains('month')
    def _check_month(self):
        for rec in self:
            if not rec.month or not (1 <= int(rec.month) <= 12):
                raise ValidationError(_('Invalid month'))

    @api.model
    def _find(self, year, month_no):
        return self.search([('year', '=', year), ('month', '=', str(month_no))], limit=1)
