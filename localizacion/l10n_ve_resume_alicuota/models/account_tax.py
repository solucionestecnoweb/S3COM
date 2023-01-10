# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
_logger = logging.getLogger('__name__')


class AccountTax(models.Model):
    _inherit = 'account.tax'

    aliquot = fields.Selection(selection=[
        ('exempt', 'exento'),
        ('general', 'Aliquiota General'),
        ('reduced', 'Aliquota Reducida'),
        ('additional', 'Aliquiota General/Adicional'),
    ], string='Aliquota', default='exempt')
