from odoo import models, fields,api
from odoo.exceptions import UserError

class PreventiveAction(models.Model):
    _name = 'hse.preventive.model'
    _description = 'Preventive Action'

    name = fields.Char(string='Action Title', required=True)
    ra_reference_number = fields.Char(string="Reference", store=True,readonly=True)
    risk_assessment_id = fields.Many2one('ra_jsa.model', string='Risk Assessment')
    action_description = fields.Text(string='Action Description')
    status = fields.Selection([
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Status', default='open')
    due_date = fields.Date(string='Due Date')
    responsible_user_id = fields.Many2one('res.users', string='Responsible Person')
    comments = fields.Text(string='Comments')
    completion_date = fields.Date(string='Completion Date')
    ra_jsa_id = fields.Many2one('ra_jsa.model', string='RA/JSA Reference')
    observation_id = fields.Many2one('observation.observation', string="Observation")
    incident_reporting_pre_id = fields.Many2one('incident.reporting', string="Incident Reporting")

    hazard_preventive_ids = fields.One2many(
        comodel_name='ra_jsa.hazard',
        inverse_name='preventive_id',
        string='Hazard_Preventive_ids',
        required=False)

    def action_in_progress(self):
        for record in self:
            if record.status == 'in_progress':
                raise UserError("This record is already in process.")
            record.status = 'in_progress'
        return True

    def action_completed(self):
        for record in self:
            if record.status == 'completed':
                raise UserError("This record is already in process.")
            record.status = 'completed'
        return True

    @api.model
    def default_get(self, fields):
        res = super(PreventiveAction, self).default_get(fields)
        if self._context.get('default_risk_assessment_id'):
            ra = self.env['ra_jsa.model'].browse(self._context.get('default_risk_assessment_id'))
            res['ra_reference_number'] = ra.name
        return res


