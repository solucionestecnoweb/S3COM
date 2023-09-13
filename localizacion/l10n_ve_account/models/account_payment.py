# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    os_currency_rate = fields.Float(string='Tipo de Cambio', default=lambda x: x.env['res.currency.rate'].search([
        ('name', '<=', fields.Date.today()),
        ('currency_id', '=', 2)], limit=1).sell_rate, digits=(12, 4))
    custom_rate = fields.Boolean(string='¿Usar Tasa de Cambio Personalizada?')


    def action_post_provi(self):
        res = super(AccountPayment, self).action_post()
        if self.custom_rate==True and self.currency_id!=self.company_id.currency_id:
            #self.move_id.button_draft()
            self.move_id.write({'os_currency_rate':self.os_currency_rate,'custom_rate':True,})


    def action_post(self):
        res = super(AccountPayment, self).action_post()
        if self.custom_rate==True and self.currency_id!=self.company_id.currency_id:
            self.move_id.button_draft()
            self.move_id.write({'os_currency_rate':self.os_currency_rate,'custom_rate':True,})
            #self.move_id.button_draft()
            for det in self.move_id.line_ids:
                if det.debit>0:
                    #det.write({'debit':self.amount*self.os_currency_rate,})
                    det.write({'debit':abs(det.amount_currency)*self.os_currency_rate,})
                if det.credit>0:
                    #det.write({'credit':self.amount*self.os_currency_rate,})
                    det.write({'credit':abs(det.amount_currency)*self.os_currency_rate,})
            self.move_id._post(soft=False)
        else:
            self.move_id.write({'os_currency_rate':self.os_currency_rate,'custom_rate':True,})
        for item in self.move_id.line_ids:
            item._compute_accounting_rate()
        return res


    @api.onchange('date')
    def actualiza_tasa(self):
        if self.custom_rate==False:
            valor=1
            busca=self.env['res.currency.rate'].search([('name', '<=', self.date), ('currency_id', '=', 2)], limit=1)
            if busca:
                valor=busca.inverse_company_rate
            self.os_currency_rate=valor
