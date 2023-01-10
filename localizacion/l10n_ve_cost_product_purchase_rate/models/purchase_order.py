# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self.cost_product_usd()
        return res


    def cost_product_usd(self):
        for line in self.order_line:
            if self.currency_id == self.company_id.currency_id:
                if line.price_unit > line.product_id.standard_price and line.product_id.standard_price > 0.0:
                    line.product_id.standard_price = line.price_unit
                    line.product_id.os_currency_rate = self.rate
                    line.product_id.cost_usd = line.price_unit * self.rate
            if self.currency_id == self.company_id.currency_id2:
                if line.price_unit > line.product_id.standard_price and line.product_id.standard_price > 0.0:
                    det_line.product_id.standard_price = line.price_unit * self.rate
                    det_line.product_id.os_currency_rate = self.rate
                    det_line.product_id.cost_usd = line.price_unit
