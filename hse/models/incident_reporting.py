from odoo import models, fields, api
from odoo.exceptions import UserError

class IncidentReporting(models.Model):
    _name = 'incident.reporting'
    _inherit = ['mail.thread']
    _description = 'Incident Reporting'

    name = fields.Char(string="Incident #", required=True, default="New")
    incident_type = fields.Selection([
        ('injury', 'Injury'),
        ('near_miss', 'Near Miss'),
        ('fire', 'Fire'),
        ('transport', 'Transport'),
    ], string='Incident Type', required=False)
    view_last_updated_date = fields.Boolean(string="View Last Updated Date", default=False)
    priority = fields.Selection([
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
    ], string="Priority", default='1')

    near_miss_harm_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Level of Potential Harm')

    is_injury = fields.Boolean(string='Is Injury Incident', default=False)
    body_part = fields.Selection([
        ('head', 'Head'),
        ('arm', 'Arm'),
        ('leg', 'Leg'),
        ('back', 'Back'),
    ], string='Body Part')

    injury_category = fields.Selection([
        ('cut', 'Cut'),
        ('burn', 'Burn'),
        ('fracture', 'Fracture'),
        ('strain', 'Strain'),
    ], string='Category of Injury')

    treatment_provided = fields.Text(string='Treatment Provided')
    treatment_provider = fields.Char(string='Treatment Provider')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_process', 'In Process'),
        ('locked', 'Locked'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft',
        group_expand='_expand_stage')

    def _expand_stage(self, states, domain, order):
        return [key for key, val in self._fields['state'].selection]

    assigned_to = fields.Many2one('res.users', string='Assigned To')
    incident_report_date = fields.Datetime(string='Incident Report Date')
    incident_processing_date = fields.Datetime(
        string='Incident Processing Date',
        default=fields.Datetime.now
    )
    select_severity_level = fields.Many2one(
        comodel_name='severity.level',
        string='Select Severity Level',
        required=False)

    hazard_incident_reporting_ids = fields.One2many(
        comodel_name='ra_jsa.hazard',
        inverse_name='incident_reporting_id',
        string='Hazard_Incident_Reporting_ids',
        required=False)

    ir_description = fields.Char(
        string='Incident Descriptions',
        required=False)

    hazard_ids = fields.One2many('ra_jsa.hazard', 'incident_reporting_id',
                                 string="Hazards")  # Multiple Hazards Linked to RA

    reported_by_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Reported By',
        default=lambda self: self.env.user.employee_id.id,
        required=False)

    select_emp_type = fields.Selection(
        string='Select Employee',
        selection=[('internal', 'INTERNAL'), ('external', 'EXTERNAL'), ],
        default='internal',
        required=False, )

    location = fields.Many2one(
        comodel_name='location.form',
        string='Main Location',
        required=False)

    exact_location = fields.Text(
        string="Exact Location",
        required=False)

    person_impacted = fields.Many2one(
        comodel_name='hr.employee',
        string='Person Impacted',
        required=False)

    rel_email = fields.Char(
        string='Impacted Person Email',
        related='person_impacted.work_email',
        required=False)
    rel_phone = fields.Char(
        string='Impacted Person Phone',
        related='person_impacted.mobile_phone',
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
    task_performed = fields.Char(
        string='Task Performed',
        required=False)

    external_company_name = fields.Char(
        string='External Company Name',
        required=False)
    external_employee_name = fields.Char(
        string='External Employee Name',
        required=False)

    select_body_part = fields.Many2one(
        comodel_name='ir.body.part',
        string='Injured Body Part',
        required=False)

    reportable_injury_or_illness = fields.Boolean(
        string='Reportable Injury or Illness?',
        required=False)
    date_of_injury = fields.Date(string="Date of Injury")
    time_of_injury = fields.Datetime(
        string='Time of Injury',
        required=False)
    directly_harmed_the_employee = fields.Html(
        string='Describe the Object or the substance that directly harmed the employee?',
        required=False)
    time_cannot_be_determined = fields.Boolean(string="Time Cannot Be Determined")
    time_employee_started_work = fields.Float(string="Time Employee Started Work")
    employee_activity_before_incident = fields.Html(
        string="Describe What the Employee Was Doing Just Before the Incident")
    describe_the_injury = fields.Html(
        string="Describe the Injury or the Illness")
    injury_illness = fields.Selection(
        string='Injury/Illness High Level Grouping',
        selection=[('injury?', 'Injury?'),
                   ('skin_disorder', 'Skin Disorder?'),
                   ('respiratory_condition', 'Respiratory Condition?'),
                   ('poisoning', 'Poisoning?'),
                   ('hearing_lose', 'Hearing Lose?'),
                   ('other', 'Other?'), ],
        required=False, )
    summary_of_incident = fields.Char(string='Summary of Incident', required=False)
    incident_detail = fields.Text(string='Incident Detail', required=False)

    impacted_body_part = fields.Char(string="Impacted Body Part")
    if_fatality = fields.Boolean(
        string='If Fatality',
        required=False)
    date_of_death = fields.Date(string="Date of Death, if applicable?")
    days_out_transferred_restricted = fields.Integer(string="Days Out/Transferred/Restricted")
    transfer_restriction_details = fields.Html(string="Transfer or Restriction Details")

    # Treatment/Services Provided Details
    physician_name = fields.Char(string="Physician or Healthcare Provider")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    facility_name = fields.Char(string="Name of Facility")
    street_address = fields.Char(string="Street Address")
    city = fields.Char(string="City")
    category_id = fields.Many2one('incident.category', string='Category', required=False)
    no_of_person_exposed_to_hazards = fields.Integer(
        string='No of Person Exposed to Hazards',
        required=False)
    incident_date = fields.Date(string='Incident Date', required=False)
    reported_date = fields.Date(string='Reported Date', default=fields.Date.context_today)

    role_in_incident = fields.Text(
        string='Describe Their Role in the Incident',
        required=False)
    person_treatment = fields.Text(
        string='What Happened to the Person After Treatment',
        required=False)

    test_time = fields.Float(
        string='Test_time',
        required=False)
    capa_ids = fields.One2many('hse.capa.model', 'incident_reporting_id', string='Linked CAPA')
    view_corrective_actions = fields.Char(string="Corrective Actions", compute="_compute_corrective_actions",
                                          readonly=True)

    def _compute_corrective_actions(self):
        for record in self:
            record.view_corrective_actions = len(record.capa_ids)

    post_treatment = fields.Selection(
        string='Post Treatment Action',
        selection=[('1', 'Sent Back to Work'),
                   ('2', 'Sent for Rest '),
                   ('3', 'Restricted Work '),
                   ],
        required=False)
    injury_type = fields.Selection([
        ('injury', 'Injury'),
        ('non_injury', 'Non-Injury')
    ], string=" Select Injury Type", required=False, default='injury')

    injury_create_level = fields.Many2one(
        comodel_name='injury.create.level',
        string='Injury Grade/Level',
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

    treatement_provider = fields.Selection(
        string='Treatement From',
        selection=[('in_house', 'In House'),
                   ('outside', 'Outside'), ],
        required=False, )
    ext_contact_no = fields.Char(
        string='Contact No#',
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

    def action_send_email(self):
        template = self.env.ref('hse.email_template_of_incident_reporting')
        template.send_mail(self.id, force_send=True)

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
            'context': {'default_incident_reporting_id': self.id,
                        'default_ra_reference_number': self.name,
                        'default_description': self.incident_detail,
                        'default_assigned_person':self.assigned_to,
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
            'context': {'default_incident_reporting_pre_id': self.id,
                        'default_ra_reference_number': self.name}  # Pass current RA/JSA ID
        }

    def action_view_corrective_actions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Corrective Actions',
            'view_mode': 'tree,form',
            'res_model': 'hse.capa.model',
            'domain': [('incident_reporting_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }

    def action_view_preventive_actions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Preventive Actions',
            'view_mode': 'tree,form',
            'res_model': 'hse.preventive.model',
            # 'domain': [('incident_reporting_pre_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('incident.reporting') or 'New'
        return super(IncidentReporting, self).create(vals_list)

    def action_start_investigation(self):
        return {
            'name': 'Incident Investigation',
            'type': 'ir.actions.act_window',
            'res_model': 'incident.investigation',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_incident_id': self.id,
                'default_summary': self.summary_of_incident,
                'default_injury_type': self.injury_type,
                'default_exact_location': self.exact_location,
                'default_priority': self.priority,
                'default_name': self.name,
                'default_location': self.location.id,
                'default_reported_by_id': self.reported_by_id.id,
                'default_assigned_to': self.assigned_to.id,
                'default_incident_report_date': self.incident_report_date,
                'default_incident_processing_date': self.incident_processing_date,
                'default_select_emp_type': self.select_emp_type,
                'default_person_impacted': self.person_impacted.id,
                'default_rel_phone': self.rel_phone,
                'default_rel_email': self.rel_email,
                'default_rel_gender': self.rel_gender,
                'default_rel_dob': self.rel_dob,
                'default_rel_job_position': self.rel_job_position.id,
                'default_role_in_incident': self.role_in_incident,
                'default_select_body_part': self.select_body_part.id,
                'default_injury_create_level': self.injury_create_level.id,
                'default_employee_activity_before_incident': self.employee_activity_before_incident,
                'default_directly_harmed_the_employee': self.directly_harmed_the_employee,
                'default_incident_detail': self.incident_detail,
                'default_no_of_person_exposed_to_hazards': self.no_of_person_exposed_to_hazards,
                'default_if_fatality': self.if_fatality,
                'default_date_of_death': self.date_of_death,
                'default_treatement_provider': self.treatement_provider,
                'default_physician_name': self.physician_name,
                'default_facility_name': self.facility_name,
                'default_email': self.email,
                'default_phone': self.phone,
                'default_city': self.city,
                'default_street_address': self.street_address,
                'default_post_treatment': self.post_treatment,
                'default_restricted_area': self.restricted_area,
                'default_no_of_days': self.no_of_days,
                'default_precautions_description': self.precautions_description,
                'default_external_company_name': self.external_company_name,
                'default_external_employee_name': self.external_employee_name,
                'default_ext_contact_no': self.ext_contact_no,
            }
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


class IrBodyPart(models.Model):
    _name = 'ir.body.part'
    _description = 'Body Part'
    _rec_name = 'ir_body_part'

    ir_body_part = fields.Char(string='Body Part', required=False)
    ir_body_des = fields.Char(
        string='Description',
        required=False)


class IrInjuryType(models.Model):
    _name = 'ir.injury.type'
    _description = 'Injury Type'
    _rec_name = 'injury_type'

    injury_type = fields.Char(string='Injury Type', required=False)
    injury_des = fields.Char(
        string='Description',
        required=False)


class IrAccidentType(models.Model):
    _name = 'ir.accident.type'
    _description = 'Accident Type'
    _rec_name = 'accident_type'

    accident_type = fields.Char(string='Accident Type', required=False)
    accident_des = fields.Char(
        string='Description',
        required=False)
