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

class AccountMove(models.Model):
    _inherit = "account.move"

    import_form_num = fields.Char(string='Import form number')
    import_dossier = fields.Char(string='Import dossier number')
    import_date = fields.Char(string='Import date')
    currency_id2 = fields.Many2one('res.currency', string='Moneda Secundaria')
    amount_total_signed_rate = fields.Monetary(compute="_compute_amount_all_rate", currency_field='currency_id2',
                                               store=True)
    amount_untaxed_signed_rate = fields.Monetary(compute="_compute_amount_all_rate", currency_field='currency_id2',
                                                 store=True)
    amount_total_signed_aux_rate = fields.Monetary(compute="_compute_amount_all_rate", currency_field='currency_id2',
                                                   store=True)
    amount_residual_signed_rate = fields.Monetary(compute="_compute_amount_all_rate", currency_field='currency_id2',
                                                  store=True)
    amount_tax_rate = fields.Monetary(compute="_compute_amount_all_rate", currency_field='currency_id2', store=True)
    doc_type = fields.Selection(related='partner_id.doc_type')
    vat = fields.Char(related='partner_id.vat')

    @api.constrains('currency_id')
    @api.onchange('currency_id')
    def _onchange_currency_second(self):
        for move in self:
            if move.company_id.currency_id2 == move.currency_id:
                move.currency_id2 = move.company_id.currency_id
            if move.company_id.currency_id == move.currency_id:
                move.currency_id2 = move.company_id.currency_id2

    @api.constrains('date')
    @api.onchange('date')
    def _check_date_account_entry(self):
        for move in self:
            if move.move_type == 'entry':
                rate_obj = self.env['res.currency.rate'].search([
                    ('name', '<=', move.date),
                    ('currency_id', '=', 2)], limit=1)
                move.os_currency_rate = rate_obj.sell_rate

    @api.depends(
        'amount_total_signed',
        'amount_untaxed_signed',
        'amount_residual_signed',
        'amount_tax_signed',
        'currency_id2',
        'os_currency_rate'
    )
    def _compute_amount_all_rate(self):
        for move in self:
            if move.company_id.currency_id2 == move.currency_id:
                move.update({
                    'amount_untaxed_signed_rate': (move.amount_untaxed * move.os_currency_rate),
                    'amount_tax_rate': (move.amount_tax * move.os_currency_rate),
                    'amount_total_signed_rate': (move.amount_total * move.os_currency_rate),
                    'amount_residual_signed_rate': (move.amount_residual * move.os_currency_rate),
                    'amount_total_signed_aux_rate': (move.amount_total * move.os_currency_rate),
                })
            if move.company_id.currency_id == move.currency_id:
                if move.os_currency_rate:
                    move.update({
                        'amount_untaxed_signed_rate': (move.amount_untaxed / move.os_currency_rate),
                        'amount_tax_rate': (move.amount_tax / move.os_currency_rate),
                        'amount_total_signed_rate': (move.amount_total / move.os_currency_rate),
                        'amount_residual_signed_rate': (move.amount_residual / move.os_currency_rate),
                        'amount_total_signed_aux_rate': (move.amount_total / move.os_currency_rate),
   
                    })

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'amount_residual')
    def _compute_amount(self):
        res=super()._compute_amount()
        for selff in self:
            if selff.amount_residual_signed==0:
                selff.payment_state='paid'
                selff.amount_residual=0

    #@api.onchange('amount_residual')
    def actualiza_reconciliazion(self):
        #raise UserError(_('resultado'))
        amount2=0
        #para facturas clientes
        if self.move_type in ('out_invoice','out_receipt','out_refund'):
            cuenta_persona=self.partner_id.property_account_receivable_id.id
        #para facturas proveedores
        if self.move_type in ('in_invoice','in_receipt','in_refund'):
            cuenta_persona=self.partner_id.property_account_payable_id.id
        #raise UserError(_('cuentas3=%s')%self.partner_id.name)
        if self.move_type!='entry':
            move_fact_id=self.env['account.move.line'].search([('account_id','=',cuenta_persona),('move_id','=',self.id)],limit=1)
            #para facturas clientes
            if self.move_type in ('out_invoice','out_receipt'):
                busca_conciliacion = self.env['account.partial.reconcile'].search([('debit_move_id','=',move_fact_id.id)])
                if busca_conciliacion:
                    valor=0
                    for item in busca_conciliacion:
                        move_pago_id=item.credit_move_id.id
                        monto=item.credit_move_id.move_id.amount_total
                        tasa=item.credit_move_id.move_id.os_currency_rate if item.credit_move_id.move_id.currency_id==self.company_id.currency_id else 1
                        ## condicion aplica si la factura en $ y el pago es Bs
                        if item.credit_move_id.move_id.currency_id==self.env.company.currency_id and self.currency_id!=self.company_id.currency_id:
                            #item.debit_amount_currency=item.amount/tasa#self.os_currency_rate
                            item.amount=monto
                            item.debit_amount_currency=monto/tasa
                            item.credit_amount_currency=monto/tasa
                        valor=valor+item.debit_amount_currency
                    self.amount_residual=self.amount_total-valor
                    self.amount_residual_signed=(self.amount_total-valor)*tasa
            #para facturas proveedores
            if self.move_type in ('in_invoice','in_receipt'):
                busca_conciliacion = self.env['account.partial.reconcile'].search([('credit_move_id','=',move_fact_id.id)])
                if busca_conciliacion:
                    valor=0
                    for item in busca_conciliacion:
                        move_pago_id=item.debit_move_id.id
                        monto=item.debit_move_id.move_id.amount_total
                        tasa=item.debit_move_id.move_id.os_currency_rate if item.debit_move_id.move_id.currency_id==self.company_id.currency_id else 1
                        ## condicion aplica si la factura en $ y el pago es Bs
                        if item.debit_move_id.move_id.currency_id==self.env.company.currency_id and self.currency_id!=self.company_id.currency_id:
                            #item.credit_amount_currency=item.amount/tasa #self.os_currency_rate
                            item.amount=monto
                            item.debit_amount_currency=monto/tasa
                            item.credit_amount_currency=monto/tasa
                        valor=valor+item.credit_amount_currency
                        #amount2=item.amount/self.os_currency_rate
                    self.amount_residual=self.amount_total-valor
                    self.amount_residual_signed=(self.amount_total-valor) if self.currency_id==self.company_id.currency_id else (self.amount_total-valor)*tasa
            #raise UserError(_('resultado=%s')%busca)
        return amount2

    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget = json.dumps(False)
            move.invoice_has_outstanding = False

            if move.state != 'posted' \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True):
                continue

            pay_term_lines = move.line_ids\
                .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

            domain = [
                ('account_id', 'in', pay_term_lines.account_id.ids),
                ('parent_state', '=', 'posted'),
                ('partner_id', '=', move.commercial_partner_id.id),
                ('reconciled', '=', False),
                '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
            ]

            payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}

            if move.is_inbound():
                domain.append(('balance', '<', 0.0))
                payments_widget_vals['title'] = _('Outstanding credits')
            else:
                domain.append(('balance', '>', 0.0))
                payments_widget_vals['title'] = _('Outstanding debits')

            for line in self.env['account.move.line'].search(domain):

                if line.currency_id == move.currency_id:
                    # Same foreign currency.
                    amount = abs(line.amount_residual_currency)
                else:
                    # Different foreign currencies.
                    ## INICIO MODIFICACION CODIGO PARA TASA PERSONALIZADA
                    if line.move_id.custom_rate!=True:
                        amount = move.company_currency_id._convert(
                            abs(line.amount_residual),
                            move.currency_id,
                            move.company_id,
                            line.date,
                        )
                    else:
                        if move.currency_id.id!=move.company_id.currency_id.id:
                            amount=abs(line.amount_residual/(line.move_id.os_currency_rate+0.0000000000000000001))
                        else:
                            amount=abs(line.amount_residual)
                    ## FIN MODIFICACION CODIGO PARA TASA PERSONALIZADA

                if move.currency_id.is_zero(amount):
                    continue

                payments_widget_vals['content'].append({
                    'journal_name': line.ref or line.move_id.name,
                    'amount': amount,
                    'currency': move.currency_id.symbol,
                    'id': line.id,
                    'move_id': line.move_id.id,
                    'position': move.currency_id.position,
                    'digits': [69, move.currency_id.decimal_places],
                    'date': fields.Date.to_string(line.date),
                    'account_payment_id': line.payment_id.id,
                })

            if not payments_widget_vals['content']:
                continue

            move.invoice_outstanding_credits_debits_widget = json.dumps(payments_widget_vals)
            move.invoice_has_outstanding = True
            """if self.move_type!='entry':
            lista=self.env['account.partial.reconcile'].search([('amount','=',0)])
            #raise UserError(_('resultado=%s')%lista)
            if lista:
                for roc in lista:
                    roc.with_context(force_delete=True).unlink()"""
        self.actualiza_reconciliazion()


    ##################################################################
    def pago_fact(self):
        return self.env['account.invoice.payment']\
            .with_context(active_ids=self.ids, active_model='account.move', active_id=self.id)\
            .action_register_invoice_payment()
##################################################################
    
    def action_post(self):
        res=super().action_post()
        for det in self.line_ids:
            det._compute_accounting_rate()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    balance_rate = fields.Monetary(currency_field='currency_id2', compute='_compute_accounting_rate', store=True)
    credit_rate = fields.Monetary(currency_field='currency_id3', compute='_compute_accounting_rate', store=True)
    debit_rate = fields.Monetary(currency_field='currency_id3', compute='_compute_accounting_rate', store=True)
    currency_id2 = fields.Many2one(related='move_id.currency_id2', depends=['move_id.currency_id2'], store=True)
    currency_id3 = fields.Many2one(related='move_id.currency_id2', depends=['move_id.company_id.currency_id2'])
    price_subtotal_rate = fields.Monetary(string='Subtotal', currency_field='currency_id2',
                                          compute='_compute_amount_rate_line', store=True)
    price_unit_rate = fields.Monetary(string='Precio unidad', currency_field='currency_id2',
                                      compute='_compute_amount_rate_line', store=True)

    @api.depends('move_id.os_currency_rate', 'currency_id2', 'price_unit', 'price_subtotal')
    def _compute_amount_rate_line(self):
        for line in self:
            if line.move_id.company_id.currency_id2 == line.move_id.currency_id:
                line.update({
                    'price_unit_rate': (line.price_unit * line.move_id.os_currency_rate),
                    'price_subtotal_rate': (line.price_subtotal * line.move_id.os_currency_rate),
                })
            if line.move_id.company_id.currency_id == line.move_id.currency_id:
                if line.move_id.os_currency_rate:
                    line.update({
                        'price_unit_rate': (line.price_unit / line.move_id.os_currency_rate),
                        'price_subtotal_rate': (line.price_subtotal / line.move_id.os_currency_rate)
                    })

    ##@api.depends('credit', 'debit', 'balance', 'currency_id', 'move_id.date')
    def _compute_accounting_rate(self):
        for line in self:
            if line.move_id.move_type == 'entry' and line.currency_id == 2:
                if line.debit > 0.0:
                    line.debit = (line.amount_currency / line.move_id.os_currency_rate)
                if line.credit > 0.0:
                    line.credit = (line.amount_currency / line.move_id.os_currency_rate)
                if line.balance > 0.0:
                    line.balance = (line.balance / line.move_id.os_currency_rate)
            if line.balance > 0.0 and line.move_id.os_currency_rate:
                line.balance_rate = (line.balance / line.move_id.os_currency_rate)
            if line.move_id.os_currency_rate:
                line.credit_rate = (line.credit / line.move_id.os_currency_rate)
                line.debit_rate = (line.debit / line.move_id.os_currency_rate)


class AccountPaymentIgtf(models.TransientModel):
    _name = "account.invoice.payment"

    account_journal_id = fields.Many2one('account.journal',string="Diario")
    payment_method_id = fields.Many2one('account.payment.method.line')

    method_generi_id = fields.Many2one('account.payment.method')

    cliente_proveedor_id=fields.Many2one('res.partner')
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.company.id)

    monto=fields.Monetary()
    monto_aux=fields.Float()
    currency_id = fields.Many2one('res.currency',default=2,string="Moneda de pago")
    tasa=fields.Float()
    monto_signed=fields.Float()
    monto_signed_uds=fields.Float()
    move_id = fields.Many2one('account.move')
    payment_date = fields.Date()

    @api.onchange('account_journal_id')
    def actualiza_metodos_pagos(self):
        for det in self.account_journal_id.inbound_payment_method_line_ids:
            det.tipo_metodo='int'

    def action_register_invoice_payment(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        #raise UserError(_('valor=%s')%active_ids[0])
        self.move_id=active_ids[0]
        return {
            'name': _('Register Payment'),
            'res_model': len(active_ids) == 1 and 'account.invoice.payment',
            'view_mode': 'form',
            'view_id': len(active_ids) != 1 and self.env.ref('vista_from_move_pago').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.onchange('company_id')
    def datos_fact(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        self.move_id=active_ids[0]
        self.cliente_proveedor_id=self.move_id.partner_id.id
        self.tasa = self.move_id.os_currency_rate
        self.currency_id=self.move_id.currency_id.id
        self.payment_date=self.move_id.invoice_date
        ##### si la factura esta en dolares
        if self.move_id.currency_id!=self.company_id.currency_id:
            self.monto=self.move_id.amount_residual
            self.monto_aux=self.move_id.amount_residual
        ##### si la factrura esta en bs
        if self.move_id.currency_id==self.company_id.currency_id:
            self.monto=self.move_id.amount_residual #self.move_id.amount_residual_signed
            self.monto_aux=self.move_id.amount_residual #self.move_id.amount_residual_signed

    @api.onchange('currency_id','tasa')
    def recalcula_monto(self):
        #raise UserError(_('resultado'))
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        self.move_id=active_ids[0]
        ##### si la factura esta en Bs
        if self.move_id.currency_id==self.company_id.currency_id:
            ## si la moneda de pago es bs
            if self.currency_id==self.company_id.currency_id:
                self.monto=self.monto_aux
            ## si la moneda de pago en divisas
            if self.currency_id!=self.company_id.currency_id:
                self.monto=self.monto_aux/self.tasa
        ##### si la factura esta en dolares
        if self.move_id.currency_id!=self.company_id.currency_id:
            ## si la moneda de pago es bs
            if self.currency_id==self.company_id.currency_id:
                self.monto=self.monto_aux*self.tasa
            ## si la moneda de pago en en divisas
            if self.currency_id!=self.company_id.currency_id:
                self.monto=self.monto_aux

    @api.onchange('payment_date')
    def actualiza_tasa(self):
        valor=1
        busca=self.env['res.currency.rate'].search([('name', '<=', self.payment_date), ('currency_id', '=', 2)], limit=1)
        if busca:
            valor=busca.inverse_company_rate
        self.tasa=valor


    def pagar(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        self.move_id=active_ids[0]
        #raise UserError(_('resultado=%s')%self.move_id)
        ### cuando se reicibe dinero
        if self.move_id.move_type in ('out_invoice','out_receipt','in_refund'):
            payment_type='inbound'
        ### cuando se entrega dinero
        if self.move_id.move_type in ('in_invoice','in_receipt','out_refund'):
            payment_type='outbound'
        vals=({
            'partner_id':self.move_id.partner_id.id,
            'amount':self.monto,
            'date':self.payment_date,
            'journal_id':self.account_journal_id.id,
            'payment_method_line_id':self.payment_method_id.id,
            'payment_type':payment_type,
            #'move_id':self.move_id.id,
            'custom_rate':True,
            'os_currency_rate':self.tasa,
            'currency_id':self.currency_id.id,
            })
        id_pago=self.env['account.payment'].create(vals)
        id_pago.action_post()
        self.create_conciliacion_fact(id_pago) # darrell

    #  codigo darrell
    def create_conciliacion_fact(self,id_pago):
        #raise UserError(_('resultado=%s')%self.move_id)
        move_entry_id=self.env['account.move'].search([('payment_id','=',id_pago.id)],limit=1)
        factor=1
        if self.company_id.currency_id.id!=self.move_id.currency_id.id:
            factor=self.tasa
        ### para proveedores
        if self.move_id.move_type in ('in_invoice','out_refund','in_receipt'):
            cuenta_ref=self.move_id.partner_id.property_account_payable_id.id
            id_move_credit=self.env['account.move.line'].search([('move_id','=',self.move_id.id),('account_id','=',cuenta_ref)],limit=1)
            id_move_debit=self.env['account.move.line'].search([('move_id','=',move_entry_id.id),('account_id','=',cuenta_ref)],limit=1)
        ### para clientes
        if self.move_id.move_type in ('out_invoice','in_refund','out_receipt'):
            cuenta_ref=self.move_id.partner_id.property_account_receivable_id.id
            id_move_credit=self.env['account.move.line'].search([('move_id','=',move_entry_id.id),('account_id','=',cuenta_ref)],limit=1)
            id_move_debit=self.env['account.move.line'].search([('move_id','=',self.move_id.id),('account_id','=',cuenta_ref)],limit=1)
            #raise UserError(_('valor=%s')%id_move_debit)
        if self.currency_id==self.company_id.currency_id:
            monto=self.monto #self.vat_retentioned
        else:
            monto=self.monto*self.tasa
        #raise UserError(_('resultado=%s')%id_move_credit)
        value=({
            'debit_move_id':id_move_debit.id,
            'credit_move_id':id_move_credit.id,
            'amount':monto, # siempre va en bs
            'debit_amount_currency':monto/factor,
            'credit_amount_currency':monto/factor,
            'max_date':self.payment_date,
            #'credit_currency_id':3,
            #'debit_currency_id':3,
            })
        self.env['account.partial.reconcile'].create(value)

class AccountPaymentMothodLine(models.Model):
    _inherit = 'account.payment.method.line'

    tipo_metodo=fields.Char()