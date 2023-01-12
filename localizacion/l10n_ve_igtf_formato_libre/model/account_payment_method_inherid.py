# -*- coding: utf-8 -*-


import logging
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class AccountPaymentMethodo(models.Model):
    _inherit = 'account.payment.method'

    calculate_wh_itf= fields.Boolean(
            string='Retención automática de IGTF',
            help='Cuando es cierto, la retención de IGTF del cliente se comprobará y '
                 'validar automáticamente', default=False)
    wh_porcentage = fields.Float(string="Percentage IGTF", help="El porcentaje a aplicar para retener ")

    account_wh_itf_id = fields.Many2one('account.account', string="Cuenta cuenta IGTF", help="Esta cuenta se usará en lugar de la predeterminada"
                                                       "uno como la cuenta por cobrar para el cliente")

    journal_transi = fields.Many2one('account.journal',help="Esta cuenta se coloca de forma temporal para que haga el asiento"
                                                        "y luego se pasa al diario del pago")