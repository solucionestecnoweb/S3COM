# -*- coding: utf-8 -*-


import logging
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError




class Partners(models.Model):
    _inherit = 'account.journal'

    tipo_bank = fields.Selection([('ex', 'Extranjero'),('na', 'Nacional')],default='ex')

    calculate_wh_itf= fields.Boolean(
            string='Retención automática de IGTF',
            help='Cuando es cierto, la retención de IGTF del proveedor se comprobará y '
                 'validar automáticamente', default=False)
    wh_porcentage = fields.Float(string="Percentage IGTF", help="El porcentaje a aplicar para retener ")

    account_wh_itf_id = fields.Many2one('account.account', string="Cuenta IGTF", help="Esta cuenta se usará en lugar de la predeterminada"
                                                       "uno como la cuenta por pagar para el socio actual")
    journal_igtf_id = fields.Many2one('account.journal')