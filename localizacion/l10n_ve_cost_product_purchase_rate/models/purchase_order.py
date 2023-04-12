# -*- coding: utf-8 -*-
from odoo import models, fields,api, _
from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self.cost_product_usd()
        return res


    def cost_product_usd(self):
        for line in self.order_line:
            #raise UserError(_('Entro aqui 0'))
            if line.product_id.product_tmpl_id.categ_id.property_cost_method=='fifo':
                #raise UserError(_('Entro aqui 1'))
                if self.currency_id == self.company_id.currency_id:
                    #raise UserError(_('Entro aqui 2'))
                    if line.price_unit > line.product_id.product_tmpl_id.standard_price:
                        #raise UserError(_('Entro aqui 3'))
                        line.product_id.product_tmpl_id.standard_price = line.price_unit
                        line.product_id.product_tmpl_id.os_currency_rate = self.rate
                        line.product_id.product_tmpl_id.cost_usd = line.price_unit / self.rate
                if self.currency_id == self.company_id.currency_id2:
                    if (line.price_unit * self.rate ) > line.product_id.standard_price:
                        line.product_id.product_tmpl_id.standard_price = line.price_unit * self.rate
                        line.product_id.product_tmpl_id.os_currency_rate = self.rate
                        line.product_id.product_tmpl_id.cost_usd = line.price_unit

            if line.product_id.product_tmpl_id.categ_id.property_cost_method=='average':
                #if self.currency_id == self.company_id.currency_id:
                line.product_id.product_tmpl_id.os_currency_rate = self.rate
                # El calculo de el costo se hace en el archivo stock_inmediate_transfer.py
                     #line.product_id.product_tmpl_id.cost_usd = line.product_id.product_tmpl_id.standard_price / self.rate

