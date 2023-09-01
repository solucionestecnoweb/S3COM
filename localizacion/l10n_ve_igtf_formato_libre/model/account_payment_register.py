# -*- coding: utf-8 -*-


import logging
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Register Payment'

    move_id = fields.Many2one('account.move')



    def action_create_payments(self):
        super().action_create_payments()
        self.registar_asiento_igtf()

    def registar_asiento_igtf(self):
        busca_factura=self.env['account.move'].search([('name','=',self.communication)],limit=1)
        if busca_factura:
            self.move_id=busca_factura.id
        #raise UserError(_('metodo=%s')%self.payment_method_line_id.payment_method_id.calculate_wh_itf)
        if self.payment_method_line_id.payment_method_id.calculate_wh_itf==True and self.move_id.is_delivery_note!=True:
            cuenta_cli=self.move_id.partner_id.property_account_receivable_id.id # cliente
            cuenta_prov=self.move_id.partner_id.property_account_payable_id.id # proveedor
            if self.move_id.move_type in ('out_invoice','out_refund'):
                cuenta_gene=cuenta_cli
            if self.move_id.move_type in ('in_invoice','in_refund'):
                cuenta_gene=cuenta_prov
            # CLIENTES
            if self.move_id.move_type in ('out_invoice','out_refund','in_invoice','in_refund'):
                for rec in self.move_id.line_ids:
                    if rec.account_id.id==cuenta_gene:
                        id_move=rec.id
                if self.move_id.state=='posted':
                    if self.move_id.move_type in ('out_invoice','out_refund'):
                        cursor=self.env['account.partial.reconcile'].search([('debit_move_id','=',id_move)])
                    if self.move_id.move_type in ('in_invoice','in_refund'):
                        cursor=self.env['account.partial.reconcile'].search([('credit_move_id','=',id_move)])
                else:
                    cursor=""
                if cursor:
                    for rec in cursor:
                        if self.move_id.move_type in ('out_invoice','out_refund'):
                            pago_move_id=rec.credit_move_id.move_id.payment_id
                        if self.move_id.move_type in ('in_invoice','in_refund'):
                            pago_move_id=rec.debit_move_id.move_id.payment_id
            #### AQUI ACOMODA LOS MONTOS DEL ASIENTO IGTF SEGUN TASA
            pago_move_id.asiento_cobro_igtf.os_currency_rate=self.os_currency_rate
            pago_move_id.asiento_cobro_igtf.custom_rate=True
            pago_move_id.asiento_cobro_igtf.amount_total=self.amount*self.os_currency_rate*self.payment_method_line_id.payment_method_id.wh_porcentage/100
            pago_move_id.asiento_cobro_igtf.amount_total_signed=self.amount*self.os_currency_rate*self.payment_method_line_id.payment_method_id.wh_porcentage/100
            for tem in pago_move_id.asiento_cobro_igtf.line_ids:
                tem._compute_accounting_rate()
            #### FIN ACOMODA LOS MONTOS DEL ASIENTO IGTF SEGUN TASA
            vals=({
                'move_id':self.move_id.id,
                'asiento_igtf':pago_move_id.asiento_cobro_igtf.id,
                'metodo_pago':self.payment_method_line_id.payment_method_id.id,
                'monto_base_usd':self.amount,
                'tasa':self.os_currency_rate,
                'monto_base':self.amount*self.os_currency_rate,
                'porcentaje':self.payment_method_line_id.payment_method_id.wh_porcentage,
                'monto_ret':self.amount*self.os_currency_rate*self.payment_method_line_id.payment_method_id.wh_porcentage/100,
                })
            payment_igtf_id=self.env['account.payment.igtf'].create(vals)
