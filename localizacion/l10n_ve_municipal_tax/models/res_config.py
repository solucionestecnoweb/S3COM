# -*- coding: utf-8 -*-
from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    municipal_retention = fields.Selection(related='company_id.municipal_retention', readonly=False)
    is_municipal = fields.Boolean(related='company_id.is_municipal', readonly=False)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        params_obj = self.env['ir.config_parameter']
        params_obj.sudo().set_param("municipal_retention", self.municipal_retention)
        params_obj.sudo().set_param("is_municipal", self.is_municipal)
        return res


