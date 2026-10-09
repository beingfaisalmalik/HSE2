from odoo import models,api


class TierDefinition(models.Model):
    _inherit = "tier.definition"

    @api.model
    def _get_tier_validation_model_names(self):
        res = super(TierDefinition, self)._get_tier_validation_model_names()
        res.append("ra_jsa.model")
        res.append("observation.observation")
        res.append("incident.reporting")
        res.append("incident.investigation")
        return res
