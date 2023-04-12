# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cost_usd = fields.Float(string='Coste $')
    os_currency_rate = fields.Float(string='Tipo de Cambio')
