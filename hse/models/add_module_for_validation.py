from odoo import models


class RiskAssessment(models.Model):
    _name = "ra_jsa.model"
    _inherit = ["ra_jsa.model", "tier.validation"]
    _state_from = ["draft","in_process","date_extention"]
    _state_to = ["in_process","locked"]

    _tier_validation_manual_config = False




class HseObservation(models.Model):
    _name = "observation.observation"
    _inherit = ["observation.observation", "tier.validation"]
    _state_from = ["draft","in_process"]
    _state_to = ["in_process","locked"]

    _tier_validation_manual_config = False

class IncidentReporting(models.Model):
    _name = "incident.reporting"
    _inherit = ["incident.reporting", "tier.validation"]
    _state_from = ["draft","in_process"]
    _state_to = ["in_process","locked"]

    _tier_validation_manual_config = False

class IncidentInvestigation(models.Model):
    _name = "incident.investigation"
    _inherit = ["incident.investigation", "tier.validation"]
    _state_from = ["draft","in_process"]
    _state_to = ["in_process","locked"]

    _tier_validation_manual_config = False

