from odoo import models, fields,api
from odoo.exceptions import UserError,ValidationError

class CorrectiveAction(models.Model):
    _name = 'hse.capa.model'
    _inherit = ['mail.thread']
    _description = 'CAPA Action'

    ra_jsa_id = fields.Many2one('ra_jsa.model', string='Linked RA/JSA', readonly=True)
    observation_id = fields.Many2one('observation.observation', string="Observation")
    incident_reporting_id = fields.Many2one('incident.reporting', string="Incident Reporting")
    incident_investigation_id = fields.Many2one('incident.investigation', string="Incident Investigation")

    name = fields.Char(string='Action Title')
    ra_reference_number = fields.Char(string="Reference", store=True, readonly=True)
    risk_assessment_id = fields.Many2one('ra_jsa.model', string='Risk Assessment')
    description = fields.Text(string='Description')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('in_progress', 'In Progress'),
        ('cancel', 'Cancel'),
        ('completed', 'Completed')
    ], string='Status', default='draft',
        group_expand='_expand_stage')

    def _expand_stage(self, states, domain, order):
        return [key for key, val in self._fields['status'].selection]

    due_date = fields.Date(string='Due Date')
    responsible_user_id = fields.Many2one('res.users', string='Assigned User')
    comments = fields.Text(string='Comments')
    completion_date = fields.Date(string='Completion Date')
    action_type = fields.Selection(
        [('corrective', 'Corrective'),
         ('preventive', 'Preventive')],
        string="Action Type"
    )
    assigned_person = fields.Many2one(
        comodel_name='hr.employee',
        string='Assigned To',
        required=True)

    hazard_corrective_ids = fields.One2many(
        comodel_name='ra_jsa.hazard',
        inverse_name='corrective_id',
        string='Hazard_Corrective_ids',
        required=False)

    select_department = fields.Many2one(
        comodel_name='hr.department',
        string='Select Department',
        required=False)

    responsible_person = fields.Many2one(
        comodel_name='hr.employee',
        string='Responsible Person',
        required=False,
        domain="[('department_id', '=', select_department)]"
    )

    priority = fields.Selection([
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
    ], string="Priority", default='1')

    def action_in_progress(self):
        for record in self:
            if record.status == 'in_progress':
                raise UserError("This record is already in process.")
            record.status = 'in_progress'
        return True

    def action_in_cancel(self):
        """Action to cancel the process."""
        for record in self:
            if record.status not in ['in_progress', 'completed']:
                record.status = 'cancel'
            else:
                record.status = 'cancel'


    def action_completed(self):
        for record in self:
            if record.status == 'completed':
                raise UserError("This record is already in process.")
            record.status = 'completed'
        return True

    @api.model
    def default_get(self, fields):
        res = super(CorrectiveAction, self).default_get(fields)
        if self._context.get('default_risk_assessment_id'):
            ra = self.env['ra_jsa.model'].browse(self._context.get('default_risk_assessment_id'))
            res['ra_reference_number'] = ra.name

            if self._context.get('default_rel_models'):
                res['rel_models'] = self._context.get('default_rel_models')

            return res
        return res

    # ra_jsa_id = fields.Many2one('ra_jsa.model', string='RA/JSA Reference' )
    select_capa  = fields.Selection(
        string='Select Action ',
        selection=[('corrective', 'Corrective'),
                   ('preventive', 'Preventive'), ],
        required=False, )
    # hse_source_id = fields.Many2one('hse.source', string="Related Record")
    # rel_model = fields.Many2one(
    #     comodel_name='ir.model',
    #     string='Rel_model',
    #     required=False)

    rel_models = fields.Char("Source Model")


    @api.onchange('due_date','completion_date' )
    def _onchange_due_date(self):
        if self.due_date and self.due_date < fields.Date.today():
            raise ValidationError("Due Date cannot be in the past.")
        if self.completion_date and self.completion_date < fields.Date.today():
            raise ValidationError("Due Date cannot be in the past.")




    # source_form_name = fields.Char(string="Form Name", compute="_compute_source_form", store=True)
    #
    # @api.depends('ra_jsa_id', 'risk_assessment_id', 'observation_id', 'incident_reporting_id',
    #              'incident_investigation_id')
    # def _compute_source_form(self):
    #     for record in self:
    #         if record.ra_jsa_id:
    #             record.source_form_name = f"RA/JSA - {record.ra_jsa_id.name}"
    #         elif record.risk_assessment_id:
    #             record.source_form_name = f"Risk Assessment - {record.risk_assessment_id.name}"
    #         elif record.observation_id:
    #             record.source_form_name = f"Observation - {record.observation_id.name}"
    #         elif record.incident_reporting_id:
    #             record.source_form_name = f"Incident Report - {record.incident_reporting_id.name}"
    #         elif record.incident_investigation_id:
    #             record.source_form_name = f"Incident Investigation - {record.incident_investigation_id.name}"
    #         else:
    #             record.source_form_name = "Unknown"
    #
    #
