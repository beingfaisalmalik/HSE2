# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HsePtwRegister(models.Model):
    """Permit-to-Work register — the Excel 'Aug-Sep 26' sheet, both column
    layouts supported by the import wizard."""
    _name = 'hse.ptw.register'
    _description = 'Permit to Work Register'
    _order = 'date_issue desc, name'
    _rec_name = 'name'

    name = fields.Char(string='PTW No.', required=True, copy=False, default='/')
    date_issue = fields.Date(string='Date of Issue', index=True)
    department = fields.Char(string='Department')
    contractor = fields.Char(string='Company / Contractor')
    nature_of_work = fields.Char(string='Nature of Work')
    type_text = fields.Char(
        string='Permit Type (combined)',
        help="Combined text as in the workbook, e.g. 'Cold Work / Work at "
             "Height'. The dashboard counts keyword matches in this text.")
    location = fields.Char(string='Location')
    status = fields.Selection(
        [('open', 'Open'), ('closed', 'Closed'), ('expired', 'Expired')],
        string='Status', default='open')

    # NOTE: no unique constraint on name — the client's register restarts
    # permit numbering every month section (two rows can both be "1").

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].next_by_code('hse.ptw.register')
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = seq or '/'
                seq = self.env['ir.sequence'].next_by_code('hse.ptw.register')
        return super().create(vals_list)

    @api.model
    def _keyword_count(self, keyword, month_no, year):
        """COUNTIFS(type_text, '*keyword*', month) — exact Excel semantics."""
        start = fields.Date.to_date('%04d-%02d-01' % (year, month_no))
        from calendar import monthrange
        end = fields.Date.to_date('%04d-%02d-%02d' % (year, month_no,
                                                      monthrange(year, month_no)[1]))
        return self.search_count([
            ('type_text', 'ilike', keyword),
            ('date_issue', '>=', start), ('date_issue', '<=', end)])
