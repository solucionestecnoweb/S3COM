# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, float_is_zero, date_utils, email_split, email_re, html_escape, is_html_empty
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.osv import expression

from datetime import date, timedelta
from collections import defaultdict
from contextlib import contextmanager
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings



class AccountPaymentIgtf(models.TransientModel):
    _inherit = "account.invoice.payment"


    def pagar(self):
        super().pagar()
        self.registar_asiento_igtf()



    def registar_asiento_igtf(self):
        #raise UserError(_('metodo=%s')%self.payment_method_id.payment_method_id.calculate_wh_itf)
        if self.payment_method_id.payment_method_id.calculate_wh_itf==True and self.move_id.is_delivery_note!=True:
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
            vals=({
                'move_id':self.move_id.id,
                'asiento_igtf':pago_move_id.asiento_cobro_igtf.id,
                'metodo_pago':self.payment_method_id.payment_method_id.id,
                'monto_base_usd':self.monto,
                'tasa':self.tasa,
                'monto_base':self.monto*self.tasa,
                'porcentaje':self.payment_method_id.payment_method_id.wh_porcentage,
                'monto_ret':self.monto*self.tasa*self.payment_method_id.payment_method_id.wh_porcentage/100,
                })
            payment_igtf_id=self.env['account.payment.igtf'].create(vals)
        #raise UserError(_('factura=%s')%self.move_id.id)