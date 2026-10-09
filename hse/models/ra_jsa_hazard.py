from pkg_resources import require

from odoo import _,models, fields, api

class RaJsaHazard(models.Model):
    _name = 'ra_jsa.hazard'
    _description = 'Hazard'
    _rec_name = "name"

    name = fields.Char(string="Hazard")
    risk_level = fields.Char(
        string='Risk Level',
        compute='_compute_risk_level',
        store=True,
    )
    ra_id = fields.Many2one('ra_jsa.model', string="RA Reference", ondelete='cascade')  # This field is important!
    description = fields.Char(
        string='Hazardeous Event',
        required=False)
    consequences= fields.Char(
        string='Consequences', 
        required=False)
    likelihood = fields.Selection(
        [
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
        ],
        string='Likelihood',
        default='1',  # Default to Medium
        required=True,
    )

    severity_level = fields.Selection(
        [
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
        ],
        string='Severity Level',
        default='1',  # Default to Medium
        required=True,
    )
    post_likelihood = fields.Selection(
        [
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
        ],
        string='Post Likelihood',
        default='3',  # Default to Medium
        required=True,
    )

    post_severity_level = fields.Selection(
        [
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
        ],
        string='Post Severity Level',
        default='3',  # Default to Medium
        required=True,
    )

    control_description = fields.Char(
        string='Control Description',
        required=False)
    risk_level_ = fields.Char(
        string='Residual Risk Level',
        compute='_compute_risk_level_',
        store=True,
    )
    severity_level_id = fields.Many2one('severity.level', string='Severity Level Reference')
    control_ids = fields.Many2many('ra_jsa.control', string="Controls")  # Link multiple controls for this hazard
    hazards_selection = fields.Many2one(
        comodel_name='hazard.setting.model',
        string='Select Hazard',
        required=False)
    observation_id = fields.Many2one(
        comodel_name='observation.observation',
        string='Observation',
        required=False)
    observation_try_id = fields.Many2one(
        comodel_name='observation.observation',
        string='Observation Link',
        required=False)

    incident_reporting_id = fields.Many2one(
        comodel_name='incident.reporting',
        string='Incident_Reporting_id',
        required=False)
    incident_investigation_id = fields.Many2one(
        comodel_name='incident.investigation',
        string='Incident_Investigation_id',
        required=False)
    corrective_id = fields.Many2one(
        comodel_name='hse.capa.model',
        string='Corrective_id',
        required=False)
    preventive_id = fields.Many2one(
        comodel_name='hse.preventive.model',
        string='Preventive_id',
        required=False)




    @api.depends('likelihood', 'severity_level')
    def _compute_risk_level(self):
        for record in self:
            # Convert string values to integers for calculation
            likelihood = int(record.likelihood) if record.likelihood else 0
            severity_level = int(record.severity_level) if record.severity_level else 0
            risk_score = likelihood * severity_level

            # Define risk level based on risk score
            if risk_score <= 10:
                record.risk_level = 'Low'
            elif 11 <= risk_score <= 20:
                record.risk_level = 'Medium'
            else:
                record.risk_level = 'High'

    @api.depends('post_likelihood', 'post_severity_level')
    def _compute_risk_level_(self):
        for record in self:
            # Convert string values to integers for calculation
            likelihood = int(record.post_likelihood) if record.post_likelihood else 0
            severity_level = int(record.post_severity_level) if record.post_severity_level else 0
            risk_score = likelihood * severity_level

            # Define risk level based on risk score
            if risk_score <= 10:
                record.risk_level_ = 'Low'
            elif 11 <= risk_score <= 20:
                record.risk_level_ = 'Medium'
            else:
                record.risk_level_ = 'High'

    def action_show_details(self):
        self.ensure_one()
        view = self.env.ref('hse.control_description_view_form')
        control_desc = self.env['control.description'].search([('rel_hazards_ids', '=', self.id)], limit=1)

        if not control_desc:
            # Create a new Control Description record if none exists
            control_desc = self.env['control.description'].create({
                'name': f'Control for Hazard {self.id}',
                'rel_hazards_ids': self.id,
            })

        return {
            'name': _('Control Description'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'control.description',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': control_desc.id,  # Open the existing or newly created record
            'context': {'default_rel_hazards_ids': self.id},
        }
    
    def action_control_details(self):
        self.ensure_one()
        view = self.env.ref('hse.control_description_view_form')
        control_desc = self.env['control.description'].search([('rel_observation_ids', '=', self.id)], limit=1)

        if not control_desc:
            # Create a new Control Description record if none exists
            control_desc = self.env['control.description'].create({
                'name': f'Control for Hazard {self.id}',
                'rel_observation_ids': self.id,
            })

        return {
            'name': _('Control Description'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'control.description',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': control_desc.id,  # Open the existing or newly created record
            'context': {'default_rel_observation_ids': self.id},
        }
    
    
    


class RaJsaControl(models.Model):
    _name = 'ra_jsa.control'
    _description = 'Control'
    _rec_name = "control_measure"

    control_measure = fields.Char(string="Control Measure", required=True)
    code = fields.Char(string='Code', required=False)
    supporting_information = fields.Text(string="Supporting Information")


class ControlDescription(models.Model):
    _name = 'control.description'
    _description = 'Control Description'

    name = fields.Char(string="Name", required=False)  # Add this field
    select_control = fields.Many2one(
        comodel_name='ra_jsa.control',
        string='Control',
        required=False)

    control_detail = fields.Text(string="control Detail", required=False)
    select_control_ids = fields.One2many(
        comodel_name='control.description.line',
        inverse_name='control_desc_ids',
        string='Select_control_ids',
        required=False)
    rel_hazards_ids = fields.Many2one(
        comodel_name='ra_jsa.hazard',
        string='rel_hazards_ids',
        required=False)
    
    rel_observation_ids = fields.Many2one(
        comodel_name='observation.observation',
        string='rel_observation_ids',
        required=False)


class ControlDescriptionLines(models.Model):
    _name = 'control.description.line'
    _description = 'Control Description Line'

    select_control = fields.Many2one(
        comodel_name='ra_jsa.control',
        string='Control',
        required=False)

    control_detail = fields.Text(string="control Detail", required=False)
    control_desc_ids= fields.Many2one(
        comodel_name='control.description',
        string='control_desc_ids',
        required=False)




