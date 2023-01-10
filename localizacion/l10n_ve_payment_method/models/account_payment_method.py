# -*- coding: utf-8 -*-

from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super(AccountPaymentMethod, self)._get_payment_method_information()
        res['cash_dollar'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        res['cash_bs'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        res['transfers_dollar'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        res['transfers_bs'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        res['zelle'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        res['check'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        res['mobile_payment'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        res['venmo'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        res['paypal'] = {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]}
        return res
