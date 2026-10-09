from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HSESafetyMeeting(models.Model):
    _name = 'hse.meeting'
    _description = 'HSE Safety Meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Inherit mail.thread and mail.activity.mixin for chatter

    meeting_datetime = fields.Datetime(
        string='Meeting Datetime',
        required=True,
        default=fields.Datetime.now
    )
    duration = fields.Float(
        string='Duration (hrs)',
    )
    department_id = fields.Many2one(
        'hse.meeting.department',
        string='Department',
        required=True
    )
    total_employees = fields.Integer(
        string='Total no of Employees',
        compute='_compute_total_employees',
        store=True # Store the computed value in the database
    )
    present_employees = fields.Integer(
        string='Present Employees',
        required=True
    )
    meeting_attend_employees = fields.Integer(
        string='Employees in Meeting',
        required=True
    )
    percentage_total_attendees = fields.Float(

        compute='_compute_percentage_total_attendees',
        store=True # Store the computed value in the database
    )

    meeting_type_ids = fields.Many2one(
        comodel_name='hse.meeting.type',
        string='Meeting Type',
        required=False)

    topic = fields.Char(
        string='Meeting Topic / Toolbox Agenda',
        tracking=True
    )
    meeting_leader_id = fields.Many2one(
        'res.users',
        string='Meeting Leader / Facilitator',
        default=lambda self: self.env.user,
        tracking=True
    )
    attendee_ids = fields.Many2many(
        'hr.employee',
        'hse_meeting_employee_rel',
        'meeting_id',
        'employee_id',
        string='Attendees'
    )

    minutes_of_meeting = fields.Html( # Using Html for Odoo's textarea/HTML field
        string='Minutes of Meeting'
    )

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hse.meeting') or '/'
        return super().create(vals_list)

    @api.depends('department_id')
    def _compute_total_employees(self):
        for record in self:
            if record.department_id:
                record.total_employees = record.department_id.number_of_employees
            else:
                record.total_employees = 0

    @api.depends('present_employees', 'meeting_attend_employees')
    def _compute_percentage_total_attendees(self):
        for record in self:
            if record.present_employees > 0:
                record.percentage_total_attendees = round((record.meeting_attend_employees / record.present_employees) * 100, 1)
            else:
                record.percentage_total_attendees = 0

    @api.constrains('present_employees', 'meeting_attend_employees', 'total_employees')
    def _check_employee_counts(self):
        for record in self:
            if record.present_employees < 0 or record.meeting_attend_employees < 0:
                raise ValidationError("Number of employees cannot be negative.")
            if record.meeting_attend_employees > record.present_employees:
                raise ValidationError("Meeting attended employees cannot exceed present employees.")
            if record.present_employees > record.total_employees:
                raise ValidationError("Present employees cannot exceed the total number of employees in the department.")


    def open_corrective_form(self):
        view = self.env.ref('hse.view_capa_form')

        return {
            'name': 'CAPA Action',
            'type': 'ir.actions.act_window',
            'res_model': 'hse.capa.model',  # Model for Corrective Action
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context':{
                'default_ra_reference_number': self.name,
                'default_select_department': self.department_id.id if self.department_id else False,
                'default_rel_models': self._description,
            }
        }


class HSEDepartment(models.Model):
    _name = 'hse.meeting.department'
    _description = 'HSE Department'

    name = fields.Char(
        string='Department Name',
        required=True
    )
    number_of_employees = fields.Integer(
        string='Number of Employees',
        required=True,
        default=0
    )

    @api.constrains('number_of_employees')
    def _check_number_of_employees(self):
        for record in self:
            if record.number_of_employees < 0:
                raise ValidationError("Number of employees cannot be negative.")


class HseMeetingType(models.Model):
    _name = 'hse.meeting.type'
    _description = 'HSE Meeting Type'

    name = fields.Char(
        string='Meeting Type',
        required=True
    )

