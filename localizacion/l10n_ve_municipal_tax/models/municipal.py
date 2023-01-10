# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger('__name__')


class TAxMunicipal(models.Model):
    _name = "tax.municipal"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Municipal'

    @api.model
    def _search_default_journal(self, journal_types):
        company_id = self._context.get('default_company_id', self.env.company.id)
        domain = [('company_id', '=', company_id), ('type', 'in', journal_types)]

        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            company = self.env['res.company'].browse(company_id)

            error_msg = _(
                "No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
                company_name=company.display_name,
                journal_types=', '.join(journal_types),
            )
            raise UserError(error_msg)

        return journal

    @api.model
    def _get_default_journal(self):
        if self._context.get('default_move_type', 'out_tax') or self._context.get('default_move_type', 'in_tax'):
            journal_types = ['mun_tax']
            journal = self._search_default_journal(journal_types)
            return journal

    name = fields.Char(string='Voucher number', default='/', copy=False, tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled')], string='Status',
                             readonly=True, copy=False, default='draft', tracking=True)
    mun_tax_type = fields.Selection([('out_tax', 'Municipal tax Customer'), ('in_tax', 'Municipal tax Vendor')],
                                    required=True, store=True, index=True, readonly=True, tracking=True,
                                    default="out_tax", change_default=True)
    transaction_date = fields.Date(string='Transaction Date', default=datetime.now(), tracking=True)
    partner_id = fields.Many2one('res.partner', string='Client', copy=False, tracking=True)
    move_id = fields.Many2one('account.move', string='Invoice', copy=False, tracking=True)
    move_entry_id = fields.Many2one('account.move', string='Entry', copy=False, tracking=True, readonly=True,
                                    domain="[('move_type', '=', 'entry')]")
    line_mun_ids = fields.One2many('tax.municipal.line', 'mun_tax_id', string='Municipal Line', tracking=True)
    move_type = fields.Selection(related='move_id.move_type', store=True, readonly=True, tracking=True)
    invoice_number_next = fields.Char(related='move_id.invoice_number_next', store=True, readonly=True, tracking=True)
    invoice_number_control = fields.Char(related='move_id.invoice_number_control', store=True, readonly=True,
                                         tracking=True)
    invoice_number_unique = fields.Char(related='move_id.invoice_number_unique', store=True, readonly=True,
                                        tracking=True)
    company_id = fields.Many2one('res.company', store=True, readonly=True,
                                 default=lambda self: self.env.company)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Currency',
                                          readonly=True, store=True, help='Utility field to express amount currency')
    company_currency_id2 = fields.Many2one(related='company_id.currency_id2', string='Secondary currency',
                                           readonly=True, store=True, help='Utility field to express amount currency')
    os_currency_rate = fields.Float(string='Tipo de Cambio', default=lambda x: x.env['res.currency.rate'].search(
        [('name', '<=', fields.Date.today()), ('currency_id', '=', 2)], limit=1).sell_rate, digits=(12, 4))
    journal_id = fields.Many2one('account.journal', string='Journal', copy=False,
                                 check_company=True, domain="[('id', 'in', suitable_journal_ids)]",
                                 states={'draft': [('readonly', False)]}, default=_get_default_journal)
    suitable_journal_ids = fields.Many2many('account.journal', compute='_compute_suitable_journal_ids')
    retention_filter_type_domain = fields.Char(compute='_compute_mun_tax_filter_type_domain')
    amount = fields.Monetary(string='Amount', compute='_compute_all_amount', readonly=True, store=True,
                             currency_field='company_currency_id', copy=False, tracking=True)
    withheld_amount = fields.Monetary(string='Withheld Amount', compute='_compute_all_amount', readonly=True,
                                      store=True, currency_field='company_currency_id', copy=False, tracking=True)
    amount_usd = fields.Monetary(string='Amount', compute='_compute_all_amount', readonly=True, store=True,
                             currency_field='company_currency_id', copy=False, tracking=True)
    withheld_amount_usd = fields.Monetary(string='Withheld Amount', compute='_compute_all_amount', readonly=True,
                                      store=True, currency_field='company_currency_id', copy=False, tracking=True)

    @api.model
    def create(self, vals):
        """
        This method is create for sequence wise name.
        :param vals: values
        :return:super
        """
        res = super(TAxMunicipal, self).create(vals)
        if res.move_type in ['in_invoice', 'in_refund']:
            res.name = self.env['ir.sequence'].next_by_code('retention.municipal.supplier')
        if res.move_type in ['out_invoice', 'out_refund']:
            res.name = self.env['ir.sequence'].next_by_code('retention.municipal.customer')
        return res

    def action_post(self):
        line = []
        move_obj = self.env['account.move']
        zero = 0.0
        balance = self.amount
        move = self.env['ir.sequence'].next_by_code('retention.municipal.account')
        value = {
            'name': move,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'ref': "Retencion Municipal de la Factura %s " % self.move_id.name,
            'municipal_id': self.id,
            'move_type': "entry",
        }
        move = move_obj.create(value)
        if self.move_type in ['out_invoice', 'out_refund']:
            line.append((0, 0, {
                'name': move,
                'ref': "Retencion Municipal de la Factura %s " % self.move_id.name,
                'move_id': self.move_id.id,
                'date': self.move_id.date,
                'partner_id': self.partner_id.id,
                'account_id': self.partner_id.property_account_receivable_municipal_id.id if
                self.move_type in ['out_refund'] else
                self.partner_id.property_account_receivable_id.id,
                'credit': balance,
                'debit': 0.0,
                'balance': -balance,
                'price_unit': zero - balance,
                'price_subtotal': zero - balance,
                'price_total': zero - balance,
            }))

            line.append((0, 0, {
                'name': move,
                'ref': "Retencion Municipal de la Factura %s " % self.move_id.name,
                'move_id': self.move_id.id,
                'date': self.move_id.date,
                'partner_id': self.partner_id.id,
                'account_id': self.partner_id.property_account_receivable_id.id if
                self.move_type in ['in_invoice', 'in_receipt', 'in_refund'] else
                self.partner_id.property_account_receivable_municipal_id.id,
                'debit': balance,
                'credit': 0.0,
                'balance': balance,
                'price_unit': zero - balance,
                'price_subtotal': zero - balance,
                'price_total': zero - balance,
                }))
        if self.move_type in ['in_invoice', 'in_refund']:
            if self.company_id.retention_iva == 'provider':
                line.append((0, 0, {
                    'name': move,
                    'ref': "Retencion Municipal de la Factura %s " % self.move_id.name,
                    'move_id': self.move_id.id,
                    'date': self.move_id.date,
                    'partner_id': self.partner_id.id,
                    'account_id': self.partner_id.property_account_payable_id.id if
                    self.move_type in ['out_refund'] else
                    self.partner_id.property_account_payable_municipal_id.id,
                    'credit': balance,
                    'debit': 0.0,
                    'balance': -balance,
                    'price_unit': zero - balance,
                    'price_subtotal': zero - balance,
                    'price_total': zero - balance,
                }))

                line.append((0, 0, {
                    'name': move,
                    'ref': "Retencion Municipal de la Factura %s " % self.move_id.name,
                    'move_id': self.move_id.id,
                    'date': self.move_id.date,
                    'partner_id': self.partner_id.id,
                    'account_id': self.partner_id.property_account_payable_municipal_id.id if
                    self.move_type in ['in_invoice', 'in_receipt', 'in_refund'] else
                    self.partner_id.property_account_payable_id.id,
                    'debit': balance,
                    'credit': 0.0,
                    'balance': balance,
                    'price_unit': zero - balance,
                    'price_subtotal': zero - balance,
                    'price_total': zero - balance,
                }))
            if self.company_id.retention_iva == 'company':
                line.append((0, 0, {
                    'name': move,
                    'ref': "Retencion Municipal de la Factura %s " % self.move_id.name,
                    'move_id': self.move_id.id,
                    'date': self.move_id.date,
                    'partner_id': self.partner_id.id,
                    'account_id': self.company_id.partner_id.property_account_payable_id.id if
                    self.move_type in ['out_refund'] else
                    self.company_id.partner_id.property_account_payable_municipal_id.id,
                    'credit': balance,
                    'debit': 0.0,
                    'balance': -balance,
                    'price_unit': zero - balance,
                    'price_subtotal': zero - balance,
                    'price_total': zero - balance,
                }))

                line.append((0, 0, {
                    'name': move,
                    'ref': "Retencion Municipal de la Factura %s " % self.move_id.name,
                    'move_id': self.move_id.id,
                    'date': self.move_id.date,
                    'partner_id': self.partner_id.id,
                    'account_id': self.company_id.partner_id.property_account_payable_municipal_id.id if
                    self.move_type in ['in_invoice', 'in_receipt', 'in_refund'] else
                    self.company_id.partner_id.property_account_payable_id.id,
                    'debit': balance,
                    'credit': 0.0,
                    'balance': balance,
                    'price_unit': zero - balance,
                    'price_subtotal': zero - balance,
                    'price_total': zero - balance,
                }))

        move.write({'line_ids': line})
        self.write({'move_entry_id': move.id, 'state': 'done'})
        self.move_entry_id._post(soft=False)
        self.action_partial_reconcile(move)
        return move

    def action_cancel(self):
        if self.move_id.state == 'cancel':
            self.write({'state': 'cancel'})
        else:
            raise ValidationError("Disculpe!!! Cancele primero la factura")

    def action_partial_reconcile(self, move):
        vals = {}
        amount_debit = 0.0
        amount_credit = 0.0
        total = 0.0
        move_obj = self.env['account.move'].search([('municipal_id', '=', self.id), ('move_type', '=', self.move_type)])
        move_line_obj = self.env['account.move.line'].search([('move_id', '=', move_obj.id)])
        for line in move_line_obj:
            if line.account_internal_type == 'payable' and line.debit == 0.0:
                vals.update({'credit_move_id': line.id})
                amount_credit += line.credit
            elif line.account_internal_type == 'receivable' and line.credit == 0.0:
                vals.update({'debit_move_id': line.id})
                amount_debit += line.debit
            for l in move.line_ids:
                if l.account_internal_type == 'payable' and line.account_id.id == l.account_id.id and l.credit == 0.0:
                    vals.update({'debit_move_id': l.id})
                    amount_debit += l.debit
                elif l.account_internal_type == 'receivable' and line.account_id.id == l.account_id.id and l.debit == 0.0:
                    vals.update({'credit_move_id': l.id})
                    amount_credit += l.credit
        if self.move_type in ['in_invoice', 'out_refund']:
            total += amount_debit

        elif self.move_type in ['out_invoice', 'in_refund']:
            total += amount_credit

        vals.update({
            'amount': total,
            'debit_amount_currency': self.amount_rate_retention_islr(total) if
            self.move_type == 'out_invoice' else total,
            'credit_amount_currency': self.amount_rate_retention_islr(total) if
            self.move_type == 'in_invoice' else total,
            'max_date': self.transaction_date,
        })
        return self.env['account.partial.reconcile'].create(vals)

    def amount_rate_retention_islr(self, amount):
        move_date = self.move_id.date
        valor_aux = 0.0
        result = 0.0
        if self.move_id.currency_id.id != self.company_id.currency_id.id:
            tasa = self.env['res.currency.rate'].search([('currency_id', '=', self.move_id.currency_id.id),
                                                         ('name', '<=', self.move_id.date)], order="name asc")
            for det_tasa in tasa:
                if move_date >= det_tasa.name:
                    valor_aux += det_tasa.rate
            rate = round(1/valor_aux, 2)
            result += amount/rate
        else:
            result += amount
        return result

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        config = self.env['ir.config_parameter']
        if not config.get_param('is_municipal'):
            msg = (
                'You cannot generate any Municipal retention if it is not configured, Contact your administrator.')
            raise UserError(msg)
        elif config.get_param('municipal_retention') == 'provider' and self.partner_id:
            rec_account = self.partner_id.property_account_receivable_municipal_id
            pay_account = self.partner_id.property_account_payable_municipal_id
            if not rec_account and not pay_account:
                msg = (
                    'Cant find a chart of accounts for this Client, you need to set it up.')
                raise UserError(msg)
        elif config.get_param('municipal_retention') == 'company' and self.company_id.partner_id:
            rec_account = self.company_id.partner_id.property_account_receivable_municipal_id
            pay_account = self.company_id.partner_id.property_account_payable_municipal_id
            if not rec_account and not pay_account:
                msg = ('Cannot find a chart of accounts for this company, You should configure it.'
                       '\nPlease go to Account Configuration.')
                raise UserError(msg)

    @api.onchange('move_type')
    def onchange_municipal_type(self):
        if self.move_type in ['in_invoice', 'in_refund', 'in_receipt'] and self.mun_tax_type in ['in_tax']:
            msg = ('Excuse me!!! You can only enter customer invoices, corrective invoices and debits.'
                   '\ngo to the menu Accounting / Suppliers / Withholding Municipal suppliers.')
            raise UserError(msg)

        if self.move_type in ['out_invoice', 'out_refund', 'out_receipt'] and self.mun_tax_type in ['out_tax']:
            msg = ('Excuse me!!! You can only enter Customer Suppliers, Corrective Invoices Suppliers and Debits.'
                   '\ngo to the menu Accounting / Customer / Withholding Municipal Customer.')
            raise UserError(msg)

    @api.depends('mun_tax_type')
    def _compute_mun_tax_filter_type_domain(self):
        for ret in self:
            if ret.islr_type in ['out_tax']:
                ret.retention_filter_type_domain = 'mun_tax'
            elif ret.islr_type in ['in_tax']:
                ret.retention_filter_type_domain = 'mun_tax'
            else:
                ret.retention_filter_type_domain = False

    @api.depends('company_id', 'retention_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = m.retention_filter_type_domain
            company_id = m.company_id.id or self.env.company.id
            domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

    @api.depends('line_mun_ids.base_tax', 'line_mun_ids.aliquot')
    def _compute_all_amount(self):
        withheld_amount = 0.0
        amount = 0.0
        for m in self:
            for line in self.line_mun_ids:
                withheld_amount += line.wh_amount
                amount += line.wh_amount
            m.withheld_amount = withheld_amount
            m.amount = amount
            if m.os_currency_rate > 0.0:
                m.withheld_amount_usd = (m.withheld_amount / m.os_currency_rate)
                m.amount_usd = (m.amount / m.os_currency_rate)


class TaxMunicipalLine(models.Model):
    _name = 'tax.municipal.line'
    _description = 'Municipal Line'

    concept_id = fields.Many2one('municipal.concept', string="Retention concept", copy=False, tracking=True)
    code = fields.Char(string='Activity code', store=True, tracking=True)
    aliquot = fields.Float(string='Aliquot', tracking=True)
    base_tax = fields.Float(string='Base Tax', tracking=True)
    wh_amount = fields.Float(compute="_compute_wh_amount", string='Withholding Amount', store=True, copy=False,
                             tracking=True)
    mun_tax_id = fields.Many2one('tax.municipal', string='Municipal', readonly=True, invisible=True)
    state = fields.Selection(related='mun_tax_id.state', store=True, copy=False, invisible=True, tracking=True)

    @api.depends('base_tax', 'aliquot')
    def _compute_wh_amount(self):
        withheld_amount = 0.0
        for item in self:
            retention = (item.base_tax * item.aliquot) / 100
            item.wh_amount = retention
