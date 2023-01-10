# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models
_logger = logging.getLogger('__name__')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    concept_isrl_id = fields.Many2one('islr.concept', string='ISLR Concept')