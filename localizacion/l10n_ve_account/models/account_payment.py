# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    os_currency_rate = fields.Float(string='Tipo de Cambio', default=lambda x: x.env['res.currency.rate'].search([
        ('name', '<=', fields.Date.today()),
        ('currency_id', '=', 2)], limit=1).sell_rate, digits=(12, 2))
    custom_rate = fields.Boolean(string='¿Usar Tasa de Cambio Personalizada?')

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for p in self.move_id.line_ids:
            if p.balance > 0.0 and self.custom_rate:
                p.update({'balance_rate': (p.balance / self.os_currency_rate)})
            if p.debit > 0.0 and self.custom_rate:
                p.update({'debit_rate': (p.debit / self.os_currency_rate)})
            if p.credit > 0.0 and self.custom_rate:
                p.update({'credit_rate': (p.credit / self.os_currency_rate)})
            p.update({'currency_id2': 2})
        return res
