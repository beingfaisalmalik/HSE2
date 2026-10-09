# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HSERiskMatrix(models.Model):
    _name = 'hse.risk.matrix'
    _description = 'HSE Dynamic Risk Matrix'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Matrix Name', required=True, default='Standard 5x5 Risk Matrix')
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    dimension = fields.Selection([
        ('5x5', '5x5 Standard Matrix'),
        ('4x4', '4x4 Matrix'),
        ('3x3', '3x3 Matrix'),
    ], string='Dimensions', default='5x5', required=True)
    consequence_ids = fields.One2many('hse.risk.matrix.consequence', 'matrix_id', string='Consequence Levels')
    likelihood_ids = fields.One2many('hse.risk.matrix.likelihood', 'matrix_id', string='Likelihood Levels')
    cell_ids = fields.One2many('hse.risk.matrix.cell', 'matrix_id', string='Matrix Cells')

    @api.model
    def calculate_risk(self, consequence_level, likelihood_level):
        """Helper method to calculate risk score and risk level from consequence and likelihood levels (1-5)"""
        score = consequence_level * likelihood_level
        if score >= 16:
            level = 'critical'
            label = 'Critical / Extreme'
            color = '#dc3545' # Red
        elif score >= 10:
            level = 'high'
            label = 'High Risk'
            color = '#fd7e14' # Orange
        elif score >= 4:
            level = 'medium'
            label = 'Medium Risk'
            color = '#ffc107' # Yellow
        else:
            level = 'low'
            label = 'Low Risk'
            color = '#28a745' # Green
        return {'score': score, 'level': level, 'label': label, 'color': color}


class HSERiskMatrixConsequence(models.Model):
    _name = 'hse.risk.matrix.consequence'
    _description = 'Risk Matrix Consequence / Severity Level'
    _order = 'level desc'

    matrix_id = fields.Many2one('hse.risk.matrix', string='Risk Matrix', ondelete='cascade')
    level = fields.Integer(string='Severity Level (1-5)', required=True)
    name = fields.Char(string='Severity Rating', required=True)
    people_impact = fields.Text(string='Health & Safety Impact')
    environment_impact = fields.Text(string='Environmental Impact')
    asset_impact = fields.Text(string='Asset & Financial Impact')
    reputation_impact = fields.Text(string='Reputational Impact')


class HSERiskMatrixLikelihood(models.Model):
    _name = 'hse.risk.matrix.likelihood'
    _description = 'Risk Matrix Likelihood / Probability Level'
    _order = 'level desc'

    matrix_id = fields.Many2one('hse.risk.matrix', string='Risk Matrix', ondelete='cascade')
    level = fields.Integer(string='Likelihood Level (1-5)', required=True)
    name = fields.Char(string='Likelihood Rating', required=True)
    frequency_description = fields.Text(string='Frequency Criteria')
    probability_percentage = fields.Float(string='Estimated Probability (%)')


class HSERiskMatrixCell(models.Model):
    _name = 'hse.risk.matrix.cell'
    _description = 'Risk Matrix Cell Mapping'
    _order = 'risk_score desc'

    matrix_id = fields.Many2one('hse.risk.matrix', string='Risk Matrix', ondelete='cascade')
    consequence_level = fields.Integer(string='Consequence Level', required=True)
    likelihood_level = fields.Integer(string='Likelihood Level', required=True)
    risk_score = fields.Integer(string='Risk Score', compute='_compute_cell_score', store=True)
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Risk Category', compute='_compute_cell_score', store=True)
    color = fields.Char(string='Display Color', compute='_compute_cell_score', store=True)
    action_required = fields.Text(string='Action & Governance Required')
    timeframe_to_close = fields.Char(string='Mandatory Resolution Timeframe')

    @api.depends('consequence_level', 'likelihood_level')
    def _compute_cell_score(self):
        for record in self:
            res = self.env['hse.risk.matrix'].calculate_risk(record.consequence_level, record.likelihood_level)
            record.risk_score = res['score']
            record.risk_level = res['level']
            record.color = res['color']
