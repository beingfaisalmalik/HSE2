from email.policy import default
from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import UserError
import logging
from datetime import timedelta
from odoo.exceptions import UserError,ValidationError


from odoo.tools.speedscope import shorten

_logger = logging.getLogger(__name__)
class RiskAssessmentJSA(models.Model):
    _name = 'ra_jsa.model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Risk Assessment and Job Safety Analysis'

    name = fields.Char(string='Reference Number', required=True,
                       index=True, default='New')

    set_priority = fields.Selection([
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
    ], string="Priority Rating", default='1')

    # Field to identify if it's RA or JSA
    type = fields.Selection([
        ('risk_assessment', 'Risk Assessment'),
        ('job_safety_analysis', 'Job Safety Analysis')
    ], string='Assessment Type', required=True, default='risk_assessment')

    analysis = fields.Many2one(
        comodel_name='analysis.form',
        string='Analysis For',
        required=False)

    team_lead_ids = fields.Many2one('hr.employee', string='Assigned Team Lead', required=False)
    team_member_id = fields.Many2many('hr.employee', string='Team Members')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('in_process', 'In Process'),
        ('locked', 'Locked'),
        ('r_approved', 'Review Locked'),
        ('cancelled', 'Cancelled'),
        ('reopen', 'Re-Open'),
        ('date_extention', 'Date Extension')
    ], string='Status', default='draft',
        group_expand='_expand_stage',
        tracking=True,)

    def _expand_stage(self, states, domain, order):
        return [key for key, val in self._fields['state'].selection]
    stage_id = fields.Many2one('ra_jsa.stage', string="Stage")
    color = fields.Integer('Color')
    repair_type = fields.Selection([
        ('repair', 'Repair'),
        ('service', 'Service')],
        string="Type")

    reviewer_id = fields.Many2one('res.users', string='Reviewer')
    lock = fields.Boolean(string='Locked', default=False)
    capa_ids = fields.One2many('hse.capa.model', 'ra_jsa_id', string='Linked CAPA')
    hazard_ids = fields.One2many('ra_jsa.hazard', 'ra_id', string="Hazards")  # Multiple Hazards Linked to RA
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent','Urgent')
    ], string='Priority', default='medium', help="Priority of the risk assessment")

    external_team = fields.Many2many('external.team', string='External Team', required=False)
    external_team_ = fields.Text(
        string="External Team Details",
        required=False)
    select_team_type = fields.Selection(
        string='Team',
        selection=[('internal', 'Internal'), ('external', 'External')],
        default='internal',
        required=False, )

    due_date = fields.Date(string='Due Date', required=False)
    extended_date = fields.Date(string='Extended Date', required=False)

    reason_for_cancel = fields.Char(
        string='Reason For Cancel',
        required=False)

    version = fields.Char(
        string='Version',
        tracking=True,
        required=False)

    select_severity_level = fields.Many2one(
        comodel_name='severity.level',
        string='Select Severity Level',
        required=False)

    description = fields.Char(
        string='Description',
        required=False)

    location = fields.Many2one(
        comodel_name='location.form',
        string='Main Location',
        required=False)

    exact_location = fields.Text(
        string="Exact Location",
        required=False)

    assets = fields.Many2one(
        comodel_name='assets.form',
        string='Assets',
        required=False)

    select_department = fields.Many2one(
        comodel_name='hr.department',
        string='Select Department',
        required=False)

    # responsible_person = fields.Many2one(
    #     comodel_name='hr.employee',
    #     string='Responsible Person',
    #     required=False,
    #     domain="[('department_id', '=', select_department)]"
    # )

    responsible_person = fields.Many2one(
        comodel_name='res.users',
        string='Responsible Person',
        default=lambda self: self.env.user,
        required=False)
    dept_head = fields.Many2one(
        comodel_name='res.users',
        string='Dept head',
        required=False,
        domain="[('department_id', '=', select_department)]"
    )
    # sec_head = fields.Many2one(
    #     comodel_name='hr.employee',
    #     string='Section head',
    #     required=False,
    #     domain="[('department_id', '=', select_department)]"
    # )
    sec_head_ids = fields.Many2one(
        comodel_name='res.users',
        string='Section Head',
        required=False)

    reason_for_review = fields.Text(string='Reason for Review', tracking=True,)

    show_pre_control = fields.Boolean(
        string='Show pre control',
        default=False, )

    def generate_report(self):
        # This function can be used to trigger custom behavior before report generation
        return self.env.ref('hse_reports.action_report_ra_jsa').report_action(self)

    # # Define the missing field
    view_corrective_actions = fields.Char(string="Corrective Actions", compute="_compute_corrective_actions",
                                          readonly=True)

    def _compute_corrective_actions(self):
        for record in self:
            record.view_corrective_actions = len(record.capa_ids)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('ra_jsa.model') or 'New'
        return super(RiskAssessmentJSA, self).create(vals_list)

    # Method for Corrective Action
    def open_corrective_form(self):
        view = self.env.ref('hse.view_capa_form')
        hazards_data = []
        for hazard in self.hazard_ids:
            control_ids = hazard.control_ids.mapped('id')
            hazards_data.append(({
                'hazards_selection': hazard.hazards_selection.id,
                'description': hazard.description,
                'consequences': hazard.consequences,
                'likelihood': hazard.likelihood,
                'control_description': hazard.control_description,
                'risk_level_': hazard.risk_level_,
                'risk_level': hazard.risk_level,
                'control_ids': control_ids,

            }))
        print(hazards_data)
        return {
            'name': 'Corrective Action',
            'type': 'ir.actions.act_window',
            'res_model': 'hse.capa.model',  # Model for Corrective Action
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context':
                {'default_ra_jsa_id': self.id,
                 'default_risk_assessment_id': self.id,
                 'default_hazard_corrective_ids': hazards_data,
                 'default_select_department': self.select_department.id,
                 'default_responsible_person': self.responsible_person.id,
                 'default_description': self.description,
                 'default_assigned_person': self.team_lead_ids.id,
                 'default_rel_models': self._description,

                 }
        }

    # Method for Preventive Action
    def open_preventive_form(self):
        return {
            'name': 'Preventive Action',
            'type': 'ir.actions.act_window',
            'res_model': 'hse.preventive.model',  # Model for Preventive Action
            'view_mode': 'form',
            'target': 'new',
            'context':
                {'default_ra_jsa_id': self.id,
                 'default_risk_assessment_id': self.id,
                 'default_rel_models': self._name,
                 }  # Pass current RA/JSA ID
        }

    def action_view_corrective_actions(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Corrective Actions',
            'view_mode': 'tree,form',
            'res_model': 'hse.capa.model',
            'domain': [('ra_jsa_id', '=', self.id), ('risk_assessment_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }

    def action_view_preventive_actions(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Preventive Actions',
            'view_mode': 'tree,form',
            'res_model': 'hse.preventive.model',
            'domain': [('ra_jsa_id', '=', self.id), ('risk_assessment_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }



        # Method to handle the "In Process" button click

    def action_in_process(self):
        for record in self:
            if record.state == 'in_process':
                raise UserError("This record is already in process.")
            record.state = 'in_process'
        return True

    def action_in_locked(self):
        for record in self:
            if record.state == 'locked':
                raise UserError("This record is already in process.")
            record.state = 'locked'
        return True

    def action_reopen(self):
        for record in self:
            record.state = 'reopen'

    def action_in_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_send_email(self):
        template = self.env.ref('hse.email_template_name')
        template.send_mail(self.id, force_send=True)

    def action_review_wizard(self):
        for record in self:
            record.state = 'locked'

    def action_in_r_approved(self):
        for record in self:
            record.state = 'r_approved'

    show_extended_date = fields.Boolean(compute="_compute_show_extended_date", store=True, default=False)

    @api.depends('due_date' ,'show_extended_date')
    def _compute_show_extended_date(self):
        today = fields.Date.today()
        for record in self:
            record.show_extended_date = record.due_date and (record.due_date - today).days == 1

    def request_extension_date(self):
        for record in self:
            record.state = 'date_extention'

        self.ensure_one()
        view = self.env.ref('hse.req_date_ext_view_form')
        return {
            'name': _('Request Extension Date'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'req.date.ext',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'default_rel_ra_jsa': self.id},
        }

    def write(self, vals):
        result = super().write(vals)

        if 'state' in vals and vals['state'] == 'date_extention':
            for record in self:
                req_ext = self.env['req.date.ext'].search([('rel_ra_jsa', '=', record.id)], order='req_ext_date desc',
                                                          limit=1)
                print(req_ext.req_ext_date)
                print(req_ext.reason)
                if req_ext:
                    message = _(
                        "Request for extension date has been initiated.<br/><br/>"
                        "<b>Requested Date:</b> %s<br/>"
                        "<b>Reason:</b> %s"
                    ) % (req_ext.req_ext_date or 'N/A', req_ext.reason or 'N/A')

                    record.message_post(
                        body=message,
                        subtype_xmlid="mail.mt_comment",
                    )

        return result


    def action_request_date(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Extension Date',
            'view_mode': 'tree,form',
            'res_model': 'req.date.ext',
            'domain': [('rel_ra_jsa', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }


    approved_date = fields.Date(string="Approved Date", readonly=True, default=date.today())
    next_review_date = fields.Datetime(string="Next Review Date After One Year", readonly=True, compute="_compute_next_review_date", store=True)

    @api.depends('approved_date')
    def _compute_next_review_date(self):
        for record in self:
            if record.approved_date:
                record.next_review_date = record.approved_date + timedelta(days=365)
            else:
                record.next_review_date = False

    @api.model
    def write(self, vals):
        # When state changes to 'approve', set approve_date
        if 'state' in vals and vals['state'] == 'approved' and not self.approved_date:
            vals['approved_date'] = fields.Datetime.now()
        return super(RiskAssessmentJSA, self).write(vals)

    def action_open_review_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Review Wizard',
            'res_model': 'ra_jsa.review_wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.onchange('due_date')
    def _onchange_due_date(self):
        if self.due_date and self.due_date < fields.Date.today():
            raise ValidationError("Due Date cannot be in the past.")




