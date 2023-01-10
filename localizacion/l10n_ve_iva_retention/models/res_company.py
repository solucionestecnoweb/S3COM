# -*- coding: utf-8 -*-
from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    retention_iva = fields.Selection([('company', 'The company'), ('provider', 'from the provider')],
                                           string="Retencion IVA", default='provider')
    is_iva = fields.Boolean(string='Retencion IVA')
