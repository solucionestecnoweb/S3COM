# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
from odoo.exceptions import UserError
_logger = logging.getLogger('__name__')


class AccountMove(models.Model):
    _inherit = 'account.move'

    alicuota_ids = fields.One2many('alicuota', 'move_id', string='Alicuotas',
                                   states={'draft': [('readonly', True)],
                                           'posted': [('readonly', True)],
                                           'cancel': [('readonly', True)]
                                           }
                                   )

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.action_alicuota()
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for l in self.alicuota_ids:
            l.unlink()
        return res

    def button_cancel(self):
        res = super(AccountMove, self).button_draft()
        self.action_cancel_alicuota()
        return res

    def action_alicuota(self):
        values = {}
        base = 0.0
        total = 0.0
        total_tax = 0.0
        total_exempt = 0.0
        total_ret_iva = 0.0
        ali_additional = 0.0
        ali_reduced = 0.0
        ali_general = 0.0
        base_general = 0.0
        base_reduced = 0.0
        base_additional = 0.0
        detained_general = 0.0
        detained_reduced = 0.0
        detained_additional = 0.0
        valor_iva = 0.0
        if self.move_type in ['in_invoice', 'in_refund', 'out_refund', 'out_invoice']:

            if self.move_type == 'in_invoice' or self.move_type == 'out_invoice':
                values.update({'type_doc': "01"})
            elif self.move_type == 'in_refund' or self.move_type == 'out_refund':
                values.update({'type_doc': "03"})
            elif (self.move_type == 'in_invoice' and self.debit_origin_id) or\
                    (self.move_type == 'out_invoice' and self.debit_origin_id):
                values.update({'type_doc': "02"})

            for move in self.invoice_line_ids:
                if not move.tax_ids and move.display_type!="line_note":                
                    raise UserError('Las Lineas de la Factura con productos deben tener un tipo de alicuota o impuestos')
                for tax in move.tax_ids.filtered(lambda x: x.type_tax_use in ['sale', 'purchase']):

                    base += move.price_subtotal
                    total += move.price_total
                    total_tax += move.price_total - move.price_subtotal

                    if tax.aliquot == "general":
                        ali_general += move.price_total - move.price_subtotal
                        base_general += move.price_subtotal
                        valor_iva += tax.amount
                    if tax.aliquot == "exempt":
                        total_exempt += move.price_subtotal
                    if tax.aliquot == "reduced":
                        ali_reduced += move.price_total - move.price_subtotal
                        base_reduced += move.price_subtotal
                    if tax.aliquot == "additional":
                        ali_additional += move.price_total - move.price_subtotal
                        base_additional += move.price_subtotal

                total_ret_iva += (total_tax * self.partner_id.retention_iva_rate) / 100
                detained_general += (ali_general * self.partner_id.retention_iva_rate) / 100
                detained_reduced += (ali_reduced * self.partner_id.retention_iva_rate) / 100
                detained_additional += (ali_additional * self.partner_id.retention_iva_rate) / 100

                if self.move_type in ['in_refund', 'out_refund']:
                    base *= -1
                    total *= -1
                    total_tax *= -1
                    ali_general *= -1
                    valor_iva *= -1
                    total_exempt *= -1
                    ali_reduced *= -1
                    ali_additional *= -1
                    total_ret_iva *= -1
                    base_additional *= -1
                    base_reduced *= -1
                    base_general *= -1
                    detained_general *= -1
                    detained_reduced *= -1
                    detained_additional *= -1
                values.update({
                    'total_amount_iva': total,
                    'total_base': base,
                    'total_valor_iva': total_tax,
                    'tax_ids': move.tax_ids,
                    'move_id': self.id,
                    'retention_iva_id': self.retention_iva_id.id,
                    'percentage_ret': self.partner_id.retention_iva_rate,
                    'total_ret_iva': total_ret_iva,
                    'total_exempt': total_exempt,
                    'ali_reduced': ali_reduced,
                    'ali_additional': ali_additional,
                    'ali_general': ali_general,
                    'date_invoice': self.date,
                    'base_additional': base_additional,
                    'base_reduced': base_reduced,
                    'base_general': base_general,
                    'detained_general': detained_general,
                    'detained_reduced': detained_reduced,
                    'detained_additional': detained_additional,
                })
            self.alicuota_ids = [(0, 0, values)]
            return self.alicuota_ids

    def action_cancel_alicuota(self):
        values = {}
        base = 0.0
        total = 0.0
        total_tax = 0.0
        total_exempt = 0.0
        total_ret_iva = 0.0
        ali_additional = 0.0
        ali_reduced = 0.0
        ali_general = 0.0
        base_general = 0.0
        base_reduced = 0.0
        base_additional = 0.0
        detained_general = 0.0
        detained_reduced = 0.0
        detained_additional = 0.0

        if self.move_type in ['in_invoice', 'in_refund', 'out_refund', 'out_invoice']:
            if self.move_type == 'in_invoice' or self.move_type == 'out_invoice':
                values.update({'type_doc': "01"})
            elif self.move_type == 'in_refund' or self.move_type == 'out_refund':
                values.update({'type_doc': "03"})
            elif (self.move_type == 'in_invoice' and self.debit_origin_id) or \
                     (self.move_type == 'out_invoice' and self.debit_origin_id):
                values.update({'type_doc': "02"})
            for move in self.invoice_line_ids:
                values.update({
                    'total_amount_iva': total,
                    'total_base': base,
                    'total_valor_iva': total_tax,
                    'tax_ids': move.tax_ids,
                    'move_id': self.id,
                    'retention_iva_id': self.retention_iva_id.id,
                    'percentage_ret': self.partner_id.retention_iva_rate,
                    'total_ret_iva': total_ret_iva,
                    'total_exempt': total_exempt,
                    'ali_reduced': ali_reduced,
                    'ali_additional': ali_additional,
                    'ali_general': ali_general,
                    'date_invoice': self.date,
                    'base_additional': base_additional,
                    'base_reduced': base_reduced,
                    'base_general': base_general,
                    'detained_general': detained_general,
                    'detained_reduced': detained_reduced,
                    'detained_additional': detained_additional,
                })
            self.alicuota_ids = [(0, 0, values)]
            return self.alicuota_ids
