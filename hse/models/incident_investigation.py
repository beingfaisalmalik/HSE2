from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import UserError


class IncidentInvestigation(models.Model):
    _name = 'incident.investigation'
    _description = 'Incident Investigation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    ref_name = fields.Char(string="Investigation Reference", required=True,
                           default=lambda self: self.env['ir.sequence'].next_by_code('incident.investigation'))
    incident_id = fields.Many2one('incident.reporting', string="Incident", ondelete='cascade')
    investigation_leader = fields.Many2one('hr.employee', string="Investigation Leader")
    team_members = fields.Many2many('hr.employee', string="Team Members")

    capa_ids = fields.One2many('hse.capa.model', 'incident_investigation_id', string='Linked CAPA')
    view_corrective_actions = fields.Char(string="Corrective Actions", compute="_compute_corrective_actions",
                                          readonly=True)

    def _compute_corrective_actions(self):
        for record in self:
            record.view_corrective_actions = len(record.capa_ids)

    # Function to calculate target date (14 days from today)
    def _get_target_date(self):
        return fields.Date.to_string(fields.Date.today() + timedelta(days=14))

    actual_completion_date = fields.Date(string="Actual Completion Date")
    delay_days = fields.Integer(string="Delay (in days)", compute="_compute_delay_days", store=True)
    immediate_cause = fields.Text(string="Immediate Cause")
    underlying_cause = fields.Text(string="Underlying Cause")
    root_cause = fields.Text(string="Root Cause")
    investigation_notes = fields.Text(string="Investigation Notes")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_process', 'In Process'),
        ('locked', 'Locked'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft',
        group_expand='_expand_stage')

    def _expand_stage(self, states, domain, order):
        return [key for key, val in self._fields['state'].selection]

    hazard_ids = fields.One2many('ra_jsa.hazard', 'incident_investigation_id',
                                 string="Hazards")  # Multiple Hazards Linked to RA

    hazard_incident_investigation_ids = fields.One2many(
        comodel_name='ra_jsa.hazard',
        inverse_name='incident_investigation_id',
        string='Hazard_Incident_Investigation_ids',
        required=False)

    select_severity_level = fields.Many2one(
        comodel_name='severity.level',
        string='Select Severity Level',
        required=False)

    # User Information
    reported_by = fields.Many2one('res.users', string="Reported By (User)")
    name_ = fields.Char(string="Name")
    line_supervisor_to = fields.Many2one('res.users', string="Line Supervisor/TO")
    investigation_lead = fields.Many2one('hr.employee', string="Investigation Lead")
    name = fields.Char(string="Name")
    out_of_employee = fields.Many2one('hr.employee', string="Out of Employee")

    # Membership List
    member_list_ids = fields.Many2many(
        comodel_name='incident.member.list',
        string='Member List')
    member_list = fields.Many2one(
        comodel_name='incident.member.list',
        string='Primary Member',
        required=False)

    priority = fields.Selection([
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
    ], string="Priority", default='1')

    name = fields.Char(string="Incident #", required=True, default="New")
    incident_type = fields.Selection([
        ('injury', 'Injury'),
        ('near_miss', 'Near Miss'),
        ('fire', 'Fire'),
        ('transport', 'Transport'),
    ], string='Incident Type', required=False)

    # Incident Details
    summary = fields.Char(string="Summary")
    details = fields.Text(
        string='Details',
        required=False)
    asset = fields.Many2one('assets.form', string="Asset")
    # location = fields.Many2one('location.form', string="Location")
    incident_location = fields.Char(string="Incident Location")
    remarks = fields.Text(string="Remarks")
    department_head_remarks = fields.Text(string="Department Head Remarks")
    section_head_remarks = fields.Text(string="Section Head Remarks")
    section_head = fields.Many2one('hr.employee', string="Section Head")
    department_head = fields.Many2one('hr.employee', string="Department Head")
    f3_form_done = fields.Boolean(string="F3 Form Done?")
    actual_score_f3 = fields.Float(string="Actual Score of PSC F3 Form")
    closure_remarks = fields.Text(string="Closure Remarks")
    target_date = fields.Date('Target Date', default=_get_target_date)
    normal_extension_date = fields.Date('Normal Extension Date')
    previous_target_date = fields.Date('Previous Target Date')
    reason_for_normal_extension = fields.Text('Reason for Normal Extension')
    extension_until_date = fields.Date('Extension Until Date')
    reason_for_special_extension = fields.Text('Reason for Special Extension')

    # investigation detail
    executive_summary = fields.Html('Executive Summary')

    # dates
    assigned_date = fields.Datetime('Assigned Date')
    last_modified_date = fields.Datetime('Last Modified Date', tracking=True)
    changed_by = fields.Many2one('res.users', string='Changed By')

    select_employee_members = fields.One2many(
        comodel_name='hr.employee',
        inverse_name='rel_inc_inv_ids',
        string='Select_employee_members',
        required=False
    )
    check_last_date = fields.Boolean(
        string='Check Last Modified Date',
        required=False)

    select_event_type_ids = fields.One2many(
        comodel_name='incident.investigation.cause',
        inverse_name='investigation_causes_ids',
        string='Event Type',
        required=False)

    inv_conclusion = fields.Html(
        string='Conclusion',
        required=False)

    injury_type = fields.Selection([
        ('injury', 'Injury'),
        ('non_injury', 'Non-Injury')
    ], string=" Select Injury Type", required=False, default='injury')

    location = fields.Many2one(
        comodel_name='location.form',
        string='Main Location',
        required=False)

    exact_location = fields.Text(
        string="Exact Location",
        required=False)

    reported_by_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Reported By (Employee)',
        required=False)

    assigned_to = fields.Many2one('res.users', string='Assigned To')
    incident_report_date = fields.Datetime(string='Incident Report Date')
    incident_processing_date = fields.Datetime(
        string='Incident Processing Date',
        default=fields.Datetime.now
    )

    incident_report_date = fields.Datetime(string='Incident Report Date')
    incident_processing_date = fields.Datetime(
        string='Incident Processing Date',
        default=fields.Datetime.now
    )

    incident_report_date = fields.Datetime(string='Incident Report Date')
    incident_processing_date = fields.Datetime(
        string='Incident Processing Date',
        default=fields.Datetime.now)

    incident_processing_date = fields.Datetime(
        string='Incident Processing Date',
        default=fields.Datetime.now)

    select_emp_type = fields.Selection(
        string='Select Employee',
        selection=[('internal', 'INTERNAL'), ('external', 'EXTERNAL'), ],
        default='internal',
        required=False, )

    person_impacted = fields.Many2one(
        comodel_name='hr.employee',
        string='Person Impacted',
        required=False)

    rel_phone = fields.Char(
        string='Impacted Person Phone',
        related='person_impacted.mobile_phone',
        required=False)

    rel_email = fields.Char(
        string='Impacted Person Email',
        related='person_impacted.work_email',
        required=False)

    rel_gender = fields.Selection(
        string='Gender',
        related='person_impacted.gender',
        required=False, )

    rel_dob = fields.Date(
        string='Date of Birth',
        related='person_impacted.birthday',
        required=False)

    rel_job_position = fields.Many2one(
        string='Job Position',
        related='person_impacted.job_id',
        required=False)

    external_company_name = fields.Char(
        string='External Company Name',
        required=False)

    external_employee_name = fields.Char(
        string='External Employee Name',
        required=False)
    ext_contact_no = fields.Char(
        string='Contact No#',
        required=False)


    role_in_incident = fields.Text(
        string='Describe Their Role in the Incident',
        required=False)

    select_body_part = fields.Many2one(
        comodel_name='ir.body.part',
        string='Body Part',
        required=False)

    injury_create_level = fields.Many2one(
        comodel_name='injury.create.level',
        string='Injury Grade/Level',
        required=False)
    employee_activity_before_incident = fields.Html(
        string="Describe What the Employee Was Doing Just Before the Incident")
    directly_harmed_the_employee = fields.Html(
        string='Describe the Object or the substance that directly harmed the employee?',
        required=False)
    summary_of_incident = fields.Char(string='Summary of Incident', required=False)
    incident_detail = fields.Text(string='Incident Detail', required=False)
    no_of_person_exposed_to_hazards = fields.Integer(
        string='No of Person Exposed to Hazards',
        required=False)
    if_fatality = fields.Boolean(
        string='If Fatality',
        required=False)
    treatement_provider = fields.Selection(
        string='Treatement From',
        selection=[('in_house', 'In House'),
                   ('outside', 'Outside'), ],
        required=False, )
    physician_name = fields.Char(string="Physician or Healthcare Provider")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    facility_name = fields.Char(string="Name of Facility")
    street_address = fields.Char(string="Street Address")
    city = fields.Char(string="City")
    post_treatment = fields.Selection(
        string='Post Treatment Action',
        selection=[('1', 'Sent Back to Work'),
                   ('2', 'Sent for Rest '),
                   ('3', 'Restricted Work '),
                   ],
        required=False)
    no_of_days = fields.Integer(
        string='No Of Days',
        required=False)

    restricted_area = fields.Text(
        string="Restricted Area",
        required=False)

    precautions_description = fields.Text(
        string="Precautions Description",
        required=False)
    date_of_death = fields.Date(string="Date of Death, if applicable?")

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
        string='Section Head User',
        required=False)
    @api.depends('target_date', 'actual_completion_date')
    def _compute_delay_days(self):
        for record in self:
            if record.actual_completion_date and record.target_date:
                delay = (record.actual_completion_date - record.target_date).days
                record.delay_days = delay if delay > 0 else 0
            else:
                record.delay_days = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('incident.investigation') or 'New'
        return super(IncidentInvestigation, self).create(vals_list)

    # Method for Corrective Action
    def open_corrective_form(self):
        view = self.env.ref('hse.view_capa_form')

        return {
            'name': 'Corrective Action',
            'type': 'ir.actions.act_window',
            'res_model': 'hse.capa.model',  # Model for Corrective Action
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context': {'default_incident_investigation_id': self.id,
                        'default_ra_reference_number': self.name,
                        }  # Pass current RA/JSA ID
        }

    # Method for Preventive Action
    def open_preventive_form(self):
        return {
            'name': 'Preventive Action',
            'type': 'ir.actions.act_window',
            'res_model': 'hse.preventive.model',  # Model for Preventive Action
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ra_reference_number': self.name}  # Pass current RA/JSA ID
        }

    def action_view_corrective_actions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Corrective Actions',
            'view_mode': 'tree,form',
            'res_model': 'hse.capa.model',
            'domain': [('incident_investigation_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }

    def action_view_preventive_actions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Preventive Actions',
            'view_mode': 'tree,form',
            'res_model': 'hse.preventive.model',
            # 'domain': [('incident_investigation_pre_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }

    # Method to handle the "In Process" button click
    def action_in_process(self):
        for record in self:
            if record.state == 'in_process':
                raise UserError("This record is already in process.")
            record.state = 'in_process'
        return True

    def action_in_lock(self):
        for record in self:
            if record.state == 'locked':
                raise UserError("This record is already in process.")
            record.state = 'locked'
        return True

    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'

    def action_in_reject(self):
        for record in self:
            if record.state == 'rejected':
                raise UserError("This record is already rejected.")
            record.state = 'rejected'
        return True


class IncidentInvestigationCause(models.Model):
    _name = 'incident.investigation.cause'
    _description = 'Incident Investigation'

    investigation_causes_ids = fields.Many2one(
        comodel_name='incident.investigation',
        string='Investigation_causes_ids',
        required=False)

    event_type_id = fields.Many2one('event.type', string='Event Type', required=True)
    immediate_cause_id = fields.Many2one('immediate.cause', string='Immediate Cause',
                                         domain="[('event_type_id', '=', event_type_id)]", required=True)
    root_cause_id = fields.Many2one('root.cause', string='Root Cause',
                                    domain="[('immediate_cause_id', '=', immediate_cause_id)]", required=True)
