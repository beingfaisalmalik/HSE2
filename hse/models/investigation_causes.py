# -*- coding: utf-8 -*-
from odoo import models, fields,api


class EventType(models.Model):
    _name = 'event.type'
    _description = 'Type of Event'
    _rec_name = 'name'

    code = fields.Char(
        string='Code',
        required=False)
    name = fields.Char(string='Event Type', required=False)
    event_type_ids= fields.Many2one(
        comodel_name='incident.investigation',
        string='event_type_ids',
        required=False)
    event_ics_code = fields.Char(
        string='Event_ics_code', 
        required=False)


class ImmediateCause(models.Model):
    _name = 'immediate.cause'
    _description = 'Immediate/Direct Cause'
    _rec_name= 'name'

    code = fields.Char(
        string='Code',
        required=False)
    name = fields.Char(string='Immediate Cause', required=False)
    event_type_id = fields.Many2many('event.type', string='Event Type', required=False)
    immediate_bcs_code = fields.Char(
        string='Immediate_bcs_code', 
        required=False)

    @api.onchange('event_type_id')
    def onchange_method(self):
        extract_code = self.env['event.type'].search([])
        print(extract_code)


class RootCause(models.Model):
    _name = 'root.cause'
    _description = 'Basic/Root Cause'

    code = fields.Char(
        string='Code',
        required=False)
    name = fields.Char(string='Root Cause', required=False)
    immediate_cause_id = fields.Many2many('immediate.cause', string='Immediate Cause', required=False)
