# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_line_count = fields.Integer(string='Cantidad de líneas', compute='_compute_lines_count')

    @api.depends('invoice_line_ids')
    def _compute_lines_count(self):
        for record in self:
            record.invoice_line_count = len(record.invoice_line_ids)

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_lines(self):
        if self.move_type in ['out_invoice', 'out_refund', 'out_receipt'] and self.env.user.company_id.sale_invoice_line_limit and self.invoice_line_count > self.env.user.company_id.sale_invoice_line_limit:
            raise ValidationError("Ha excedido de líneas para ésta factura.")
