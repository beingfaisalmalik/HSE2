from odoo import models,api


class RiskAssessment(models.Model):
    _name = "ra_jsa.model"
    _inherit = ["ra_jsa.model", "tier.validation"]
    _state_from = ["draft", "in_process"]
    _state_to = ["in_process", "approved"]

    _tier_validation_manual_config = False


class TierDefinition(models.Model):
    _inherit = "tier.definition"

    @api.model
    def _get_tier_validation_model_names(self):
        res = super()._get_tier_validation_model_names()
        res.append("ra_jsa.model")
        return res