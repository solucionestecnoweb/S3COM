# -*- coding: utf-8 -*-
from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    municipal_retention = fields.Selection([('company', 'The company'), ('provider', 'from the provider')],
                                           string="Comprobante Retencion Municipal", default='provider')
    is_municipal = fields.Boolean(string='Retencion Municipal')
