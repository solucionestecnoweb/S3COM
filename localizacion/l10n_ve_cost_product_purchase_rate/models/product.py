# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    

    cost_usd = fields.Float(string='Coste $')
    os_currency_rate = fields.Float(string='Tipo de Cambio', default=lambda x: x.env['res.currency.rate'].search(
        [('name', '<=', fields.Date.today()), ('currency_id', '=', 2)], limit=1).sell_rate, digits=(12, 2), readonly=True)