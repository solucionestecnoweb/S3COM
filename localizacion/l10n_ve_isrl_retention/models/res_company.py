# -*- coding: utf-8 -*-
from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    retention_islr = fields.Selection([('company', 'The company'), ('provider', 'from the provider')],
                                           string="Retencion ISLR", default='provider')
    is_islr = fields.Boolean(string='Retencion ISLR')
