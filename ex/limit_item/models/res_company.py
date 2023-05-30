# coding: utf-8
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    # sale_invoice_line_limit = fields.Integer(string='Líneas por factura de venta', compute="_check_sale_invoice_line_limit")
    sale_invoice_line_limit = fields.Integer(string='Líneas por factura de venta')

    @api.constrains('sale_invoice_line_limit')
    def _check_sale_invoice_line_limit(self):
        if self.sale_invoice_line_limit == 0:
            raise ValidationError('Límite por factura de venta no puede ser menor a 0')