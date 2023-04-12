# -*- coding: utf-8 -*-
from odoo import models, fields,api, _
from odoo.exceptions import UserError, ValidationError

class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'
    _description = 'Immediate Transfer'

    def process(self):
        super().process()
        #raise UserError(_('id es=%s')%self.pick_ids)
        valor=self.actualiza_costo()

    def actualiza_costo(self):
    	for rec in self.pick_ids:
    		tasa=1
    		if not rec.sale_id:
    			compras=self.env['purchase.order'].search([('name','=',rec.origin)])
    			if compras:
    				for item in compras:
    					tasa=item.rate
    					moneda_orden=item.currency_id
    					moneda_company=item.company_id.currency_id
    					moneda_company2=item.company_id.currency_id2
    		for det in rec.move_ids_without_package:
    			if det.product_id.product_tmpl_id.categ_id.property_cost_method=='average':
    				det.product_id.product_tmpl_id.cost_usd=det.product_id.product_tmpl_id.standard_price/tasa