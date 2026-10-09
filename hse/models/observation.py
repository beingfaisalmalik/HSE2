from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class Observation(models.Model):
    _name = 'observation.observation'
    _inherit = ['mail.thread']
    _description = 'Observation'

    name = fields.Char(string="Observation Reference", copy=False, default='New')
    observation_date = fields.Datetime(string="Observation Date", default=fields.Datetime.now)

    def get_today(self):
        return datetime.now().strftime('%m-%d-%y %H:%M:%S')

    observer_id = fields.Many2one('res.users', string="Observer", default=lambda self: self.env.user)
    observation_type = fields.Selection([
        ('inspection', 'Inspection'),
        ('random', 'Random Observation'),
    ], string="Observation Type", default='random')

    priority = fields.Selection([
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
    ], string="Priority", default='1')
    hazard_type = fields.Selection([
        ('physical', 'Physical'),
        ('chemical', 'Chemical'),
        ('biological', 'Biological'),
        ('other', 'Other'),
    ], string="Hazard Type")
    severity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string="Severity Level")

    select_severity_level = fields.Many2one(
        comodel_name='severity.level',
        string='Select Severity Level',
        required=False)
    observation = fields.Text('Observation')
    employee_observer_name = fields.Char(
        string='Employee Observer Name',
        required=False)
    employee_code = fields.Char(
        string='Employee Code',
        required=False)
    description = fields.Text("Description")
    hazard_photo = fields.Binary(string="Hazard Photo / Site Evidence", attachment=True)
    hazard_photo_filename = fields.Char(string="Hazard Photo Filename")
    location_id = fields.Many2one('hse.location.profile', string="Plant Area / Location")

    user_id = fields.Many2one('res.users', string='Submitted By', default=lambda self: self.env.user)
    immediate_action = fields.Text(string="Immediate Action Taken")
    responsible_user_id = fields.Many2one('res.users', string="Assigned User")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_process', 'In Process'),
        ('locked', 'Locked'),
        ('rejected', 'Rejected'),
        ('reopen', 'Re-Open'),
    ], string='Status', default='draft',
        group_expand='_expand_stage')

    def _expand_stage(self, states, domain, order):
        return [key for key, val in self._fields['state'].selection]

    hazard_observation_ids = fields.One2many(
        comodel_name='ra_jsa.hazard',
        inverse_name='observation_id',
        string='Hazard_observation_ids',
        required=False)
    capa_ids = fields.One2many('hse.capa.model', 'observation_id', string='Linked CAPA')
    view_corrective_actions = fields.Char(string="Corrective Actions", compute="_compute_corrective_actions",
                                          readonly=True)
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
    
    show_pre_risk_level = fields.Boolean(
        string='Show Risk Level',
        required=False)
    
    show_pictogram = fields.Boolean(
        string='Show Pictograms',
        required=False)

    img_acid = fields.Boolean(
        required=False)
    img_bottle = fields.Boolean(
        required=False)
    img_exclam = fields.Boolean(
        required=False)
    img_explos = fields.Boolean(
        required=False)
    img_flamme = fields.Boolean(
        required=False)
    img_pollu = fields.Boolean(
        required=False)
    img_rondflam = fields.Boolean(
        required=False)
    img_silhouette = fields.Boolean(
        required=False)
    img_skull = fields.Boolean(
        required=False)

    selected_hazard_ids = fields.One2many("observation.hazard", "observation_id", string="Selected Hazards")
    selected_hazard_images = fields.Html(compute="_compute_selected_hazard_images", string="Selected Hazard Images")
    image_path = fields.Char("Image Path")


    def action_toggle_hazards(self):
        """Update selected hazards when the button is clicked."""
        selected_hazards = [(5, 0, 0)]  # Clears existing records before adding new ones

        hazard_images = {
            'img_acid': "/hse/static/src/img/GHS-pictogram-acid.svg.png",
            'img_bottle': "/hse/static/src/img/GHS-pictogram-bottle.svg.png",
            'img_exclam': "/hse/static/src/img/GHS-pictogram-exclam.svg.png",
            'img_explos': "/hse/static/src/img/GHS-pictogram-explos.svg.png",
            'img_flamme': "/hse/static/src/img/GHS-pictogram-flamme.svg.png",
            'img_pollu': "/hse/static/src/img/GHS-pictogram-pollu.svg.png",
            'img_rondflam': "/hse/static/src/img/GHS-pictogram-rondflam.svg.png",
            'img_silhouette': "/hse/static/src/img/GHS-pictogram-silhouette.svg.png"
        }

        for field_name, image_path in hazard_images.items():
            if getattr(self, field_name):
                selected_hazards.append((0, 0, {'image_path': image_path}))

        self.write({'selected_hazard_ids': selected_hazards})
        return True

    @api.depends("selected_hazard_ids")
    def _compute_selected_hazard_images(self):
        for record in self:
            images_html = "".join(
                f'<img src="{hazard.image_path}" width="100" height="100" style="margin-right: 10px;"/>'
                for hazard in record.selected_hazard_ids if hazard.image_path
            )
            record.selected_hazard_images = images_html
    image_path = fields.Char("Image Path")

    dept_head = fields.Many2one(
        comodel_name='res.users',
        string='Department Head',
        required=False)

    def _compute_corrective_actions(self):
        for record in self:
            record.view_corrective_actions = len(record.capa_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('observation') or 'New'
        return super(Observation, self).create(vals_list)

    # Method for Corrective Action
    def open_corrective_form(self):
        view = self.env.ref('hse.view_capa_form')
        hazards_data = []
        for hazard in self.hazard_observation_ids:
            control_ids = hazard.control_ids.mapped('id')
            hazards_data.append(({
                'hazards_selection': hazard.hazards_selection.name,
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
            'context': {'default_observation_id': self.id,
                        'default_ra_reference_number': self.name,
                        'default_name': self.observation,
                        'default_hazard_corrective_ids': hazards_data,
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
            'context': {'default_observation_id': self.id,
                        'default_ra_reference_number': self.name}  # Pass current RA/JSA ID
        }

    def action_view_corrective_actions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Corrective Actions',
            'view_mode': 'tree,form',
            'res_model': 'hse.capa.model',
            'domain': [('observation_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }

    def action_view_preventive_actions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Preventive Actions',
            'view_mode': 'tree,form',
            'res_model': 'hse.preventive.model',
            'domain': [('observation_id', '=', self.id)],
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

    def action_in_reject(self):
        for record in self:
            if record.state == 'rejected':
                raise UserError("This record is already rejected.")
            record.state = 'rejected'
        return True

    @api.depends('select_department')
    def _get_responsible_user_domain(self):
        for record in self:
            if record.select_department:
                employee_ids = self.env['hr.employee'].search(
                    [('department_id', '=', record.select_department.id)]).mapped('user_id.id')
                return [('id', 'in', employee_ids)]
            else:
                return []


class ObservationHazard(models.Model):
    _name = "observation.hazard"
    _description = "Selected Hazard"

    observation_id = fields.Many2one("observation.observation", string="Observation")
    image_path = fields.Char("Image Path")
