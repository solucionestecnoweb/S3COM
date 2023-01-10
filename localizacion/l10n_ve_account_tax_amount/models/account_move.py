# -*- coding: utf-8 -*-

from odoo import api, fields, models
# from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    iva_no_tax_credit = fields.Float(string='Sin Crédito Fiscal', compute='amount_tax_aliquot', store=True)
    iva_exempt = fields.Float(string='Exento', compute='amount_tax_aliquot', store=True)
    iva_general = fields.Float(string='General', compute='amount_tax_aliquot', store=True)
    iva_reduced = fields.Float(string='Reducida', compute='amount_tax_aliquot', store=True)
    iva_additional = fields.Float(string='General + Adicional', compute='amount_tax_aliquot', store=True)

    @api.depends('amount_total', 'amount_tax', 'amount_untaxed', 'state')
    def amount_tax_aliquot(self):
        for item in self:
            iva_no_tax_credit = 0.0
            iva_exempt = 0.0
            iva_general = 0.0
            iva_reduced = 0.0
            iva_additional = 0.0
            for line in item.invoice_line_ids:
                for tax in line.tax_ids:
                    if tax.aliquot == 'no_tax_credit':
                        iva_no_tax_credit += (line.price_subtotal * tax.amount) / 100
                    if tax.aliquot == 'exempt':
                        iva_exempt += (line.price_subtotal * tax.amount) / 100
                    if tax.aliquot == 'general':
                        iva_general += (line.price_subtotal * tax.amount) / 100
                    if tax.aliquot == 'reduced':
                        iva_reduced += (line.price_subtotal * tax.amount) / 100
                    if tax.aliquot == 'additional':
                        iva_additional += (line.price_subtotal * tax.amount) / 100
            item.iva_no_tax_credit = iva_no_tax_credit
            item.iva_exempt = iva_exempt
            item.iva_general = iva_general
            item.iva_reduced = iva_reduced
            item.iva_additional = iva_additional
