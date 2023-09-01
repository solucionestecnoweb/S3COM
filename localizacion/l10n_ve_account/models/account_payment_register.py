# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, frozendict


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    os_currency_rate = fields.Float(string='Tipo de Cambio', digits=(12, 4),default=0)
    custom_rate = fields.Boolean(string='¿Usar Tasa de Cambio Personalizada?')

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date','os_currency_rate')
    def _compute_amount(self):
        for wizard in self:
            tasa=1
            for det in wizard.line_ids:
                tasa=det.move_id.os_currency_rate
                monto_adeudado=det.move_id.amount_residual #det.move_id.total_adeudado_org
                factura_id=det.move_id
                #monto_adeudado_signed=det.move_id.amount_residual_signed
            if wizard.os_currency_rate==0:
                wizard.os_currency_rate=tasa

            if wizard.source_currency_id == wizard.currency_id:
                #trae monto original de la factura si la moneda del wizar =moneda factura
                wizard.amount =  monto_adeudado#wizard.source_amount_currency
            elif wizard.currency_id == wizard.company_id.currency_id:
                #trae monto bs de la factura, si la moneda del wizar =moneda compañia y moneda factuar esta en $
                #wizard.amount = wizard.source_amount
                wizard.amount = monto_adeudado*wizard.os_currency_rate
            else:
                # si la fact esta en bs, y la moneda del wizar en $, lleva el monto bs a equivalente en usd segun tasa.
                amount_payment_currency = wizard.source_amount/wizard.os_currency_rate#wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date or fields.Date.today())
                wizard.amount = amount_payment_currency

    @api.depends('amount')
    def _compute_payment_difference(self):
        for wizard in self:
            for det in wizard.line_ids:
                tasa=det.move_id.os_currency_rate
                monto_adeudado=det.move_id.amount_residual
                factura_id=det.move_id
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.payment_difference = monto_adeudado - wizard.amount
                #wizard.payment_difference = wizard.source_amount_currency - wizard.amount
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                #wizard.payment_difference = wizard.source_amount - wizard.amount
                wizard.payment_difference = monto_adeudado*wizard.os_currency_rate - wizard.amount #wizard.source_amount - wizard.amount
                #if wizard.payment_difference==0:
                    #factura_id.payment_state='paid'
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                amount_payment_currency = wizard.source_amount/wizard.os_currency_rate#wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date or fields.Date.today())
                wizard.payment_difference = amount_payment_currency - wizard.amount

    @api.onchange('payment_date')
    def actualiza_tasa(self):
        valor=1
        busca=self.env['res.currency.rate'].search([('name', '<=', self.payment_date), ('currency_id', '=', 2)], limit=1)
        if busca:
            valor=busca.inverse_company_rate
        self.os_currency_rate=valor


    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)
        to_process = []

        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            to_process.append({
                'create_vals': payment_vals,
                'to_reconcile': batches[0]['lines'],
                'batch': batches[0],
            })
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'payment_values': {
                                **batch_result['payment_values'],
                                'payment_type': 'inbound' if line.balance > 0 else 'outbound'
                            },
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })

        payments = self._init_payments(to_process, edit_mode=edit_mode)
        #raise UserError(_("valor=%s")%payments)
        self.actualiza_pago_con_tasa(payments)
        self._post_payments(to_process, edit_mode=edit_mode)
        self._reconcile_payments(to_process, edit_mode=edit_mode)
        return payments


    def actualiza_pago_con_tasa(self,payments):
        payments.os_currency_rate=self.os_currency_rate
        payments.custom_rate=True
        #payments.move_id.
