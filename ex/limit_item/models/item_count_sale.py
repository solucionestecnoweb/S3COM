# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_line_count = fields.Integer(string='Cantidad de líneas', compute='_compute_lines_count')

    @api.depends('order_line')
    def _compute_lines_count(self):
        for record in self:
            record.invoice_line_count = len(record.order_line)

    @api.onchange('order_line')
    def _onchange_invoice_lines(self):
        if self.env.user.company_id.sale_invoice_line_limit and self.invoice_line_count > self.env.user.company_id.sale_invoice_line_limit:
            raise ValidationError("Ha excedido de líneas para ésta factura.")
