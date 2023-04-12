# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cost_usd = fields.Float(string='Coste $')
    os_currency_rate = fields.Float()

    """@api.onchange('standard_price')
    @api.constrains('standard_price')
    def _check_rate_cost_usd(self):
        for product in self:
            if product.standard_price > 0.0 and product.os_currency_rate:
                rate = product.standard_price / product.os_currency_rate
                product.cost_usd = rate"""

    """@api.onchange('cost_usd')
    @api.constrains('cost_usd')
    def _check_rate_cost_bs(self):
        for product in self:
            if product.cost_usd > 0.0 and product.os_currency_rate:
                rate = product.cost_usd * product.os_currency_rate
                product.standard_price = rate"""