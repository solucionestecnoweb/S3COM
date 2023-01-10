# -*- coding: utf-8 -*-

from odoo import fields, models,tools,api

class pos_config(models.Model):
    _inherit = 'pos.config' 

    allow_payment_ref = fields.Boolean('Permitir la referencia de pago.',default=True)

class PosPayment(models.Model):
    _inherit = 'pos.payment' 

    payment_refer = fields.Char("Nro. de referencia de pago")

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _payment_fields(self, order, ui_paymentline):
        result = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        if 'payment_refer' in ui_paymentline:
            result['payment_refer'] = ui_paymentline['payment_refer']
        return result


