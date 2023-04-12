# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
_logger = logging.getLogger('__name__')


class Bank(models.Model):
    _inherit = 'res.bank'

    url_bank = fields.Char(string='Url Bank', readonly="True")
    vat = fields.Char(string='Rif')
    doc_type = fields.Selection([('e', 'E'), ('j', 'J'),  ('g', 'G')], required=True, default='j')
