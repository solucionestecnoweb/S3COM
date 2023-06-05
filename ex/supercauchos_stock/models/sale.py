# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from itertools import product
import json
from datetime import datetime, timedelta
import base64
from io import StringIO
from odoo import api, fields, models
from datetime import date
from odoo.tools.float_utils import float_round
from odoo.exceptions import Warning

import time

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    filler = fields.Float(string='Filler', related='product_id.filler')
    fillert = fields.Float(string='FillerT')

    @api.onchange('product_id', 'product_uom_qty')
    def onchange_filler(self):
        self.calculate_filler()

    @api.constrains('product_id', 'product_uom_qty')
    def constrains_filler(self):
        self.calculate_filler()

    def calculate_filler(self):
        for line in self:
            line.fillert = line.filler * line.product_uom_qty

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    fillert = fields.Float(string='Filler Total', copy=False)
    situacion = fields.Selection(string='Situación', selection=[('Apartado', 'Apartado'), ('Analisis', 'Análisis')], track_visibility='onchange', copy=False)
    end_line = fields.Datetime(string='Fecha de confirmación', copy=False)
    
    def change_situacion_apartado(self):
        self.situacion = 'Apartado'
        self.end_line = datetime.now()

    def change_situacion_analisis(self):
        self.situacion = 'Analisis'

    @api.onchange('situacion')
    def update_picking_situacion(self):
        for item in self.picking_ids:
            s = self.env['stock.picking'].search([("name","=",item.name)])
            s.situacion = self.situacion

        for item in self.invoice_ids:
            s = self.env['account.move'].search([("name","=",item.name)])
            s.situacion = self.situacion

    def _create_invoices(self, grouped=False, final=False):
        res = super(SaleOrder, self)._create_invoices()
        res.situacion = self.situacion
        return res

    @api.onchange('order_line')
    def onchange_filler(self):
        self.calculate_filler()

    @api.constrains('order_line')
    def constrains_filler(self):
        self.calculate_filler()

    def calculate_filler(self):
        filler = 0
        for line in self.order_line:
            filler += line.fillert
        self.fillert = filler

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.change_situacion_apartado()
        return res