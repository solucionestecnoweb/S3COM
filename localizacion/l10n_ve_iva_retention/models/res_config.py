# -*- coding: utf-8 -*-
from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    retention_iva = fields.Selection(related='company_id.retention_iva', readonly=False)
    is_iva = fields.Boolean(related='company_id.is_iva', readonly=False)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        params_obj = self.env['ir.config_parameter']
        params_obj.sudo().set_param("retention_iva", self.retention_iva)
        params_obj.sudo().set_param("is_iva", self.is_iva)
        return res
