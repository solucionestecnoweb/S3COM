# -*- coding: utf-8 -*-
from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    retention_islr = fields.Selection(related='company_id.retention_islr', readonly=False)
    is_islr = fields.Boolean(related='company_id.is_islr', readonly=False)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        params_obj = self.env['ir.config_parameter']
        params_obj.sudo().set_param("retention_islr", self.retention_islr)
        params_obj.sudo().set_param("is_islr", self.is_islr)
        return res


