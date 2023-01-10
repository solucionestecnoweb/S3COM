# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger('__name__')


class RetentionIva(models.Model):
    _name = 'retention.iva'
    _description = "Retention Iva"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
        if self._context.get('default_move_type', 'out_iva') or self._context.get('default_move_type', 'in_iva'):
            journal_types = ['ret_iva']
            journal = self._search_default_journal(journal_types)
            return journal

    name = fields.Char(string='Voucher number',  default='00000000', copy=False, tracking=True)
    number_retention = fields.Char(string='manual hold', copy=False)
    move_type = fields.Selection(related='move_id.move_type', store=True, readonly=True, tracking=True)
    invoice_number_next = fields.Char(related='move_id.invoice_number_next', store=True, readonly=True, tracking=True)
    invoice_number_control = fields.Char(related='move_id.invoice_number_control', store=True, readonly=True,
                                         tracking=True)
    invoice_number_unique = fields.Char(related='move_id.invoice_number_unique', store=True, readonly=True,
                                        tracking=True)
    debit_origin_id = fields.Many2one(related='move_id.debit_origin_id', store=True, readonly=True, tracking=True)
    ref = fields.Char(related='move_id.ref', store=True, readonly=True, tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='states', default='draft', tracking=True)
    iva_type = fields.Selection([('out_iva', 'Retention Iva Customer'), ('in_iva', 'Retention Iva Vendor')],
                                required=True, store=True, index=True, readonly=True, tracking=True,
                                default="out_iva", change_default=True)
    move_date = fields.Date(string='Date Move', tracking=True)
    iva_date = fields.Date(string='Date Retention Iva', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Client', copy=False, tracking=True)
    move_id = fields.Many2one('account.move', string='Invoice', copy=False, tracking=True)
    move_entry_id = fields.Many2one('account.move', string='Entry', copy=False, tracking=True, readonly=True,
                                    domain="[('move_type', '=', 'entry')]")
    company_id = fields.Many2one('res.company', store=True, readonly=True,
                                 default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True,
                              tracking=True, default=lambda self: self.env.user)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Currency',
                                          readonly=True, store=True, help='Utility field to express amount currency')
    company_currency_id2 = fields.Many2one(related='company_id.currency_id2', string='Secondary currency',
                                           readonly=True, store=True, help='Utility field to express amount currency')
    is_currency_rate = fields.Boolean(string='Usar Tasa Personalizada?')
    os_currency_rate = fields.Float(string='Tipo de Cambio', default=lambda x: x.env['res.currency.rate'].search(
        [('name', '<=', fields.Date.today()), ('currency_id', '=', 2)], limit=1).sell_rate, digits=(12, 4))
    journal_id = fields.Many2one('account.journal', string='Journal', copy=False,
                                 check_company=True, domain="[('id', 'in', suitable_journal_ids)]",
                                 states={'draft': [('readonly', False)]}, default=_get_default_journal)
    line_ids = fields.One2many('retention.iva.line', 'retention_iva_id', string='Retention Lines', copy=True,
                               readonly=True, states={'draft': [('readonly', False)]})
    suitable_journal_ids = fields.Many2many('account.journal', compute='_compute_suitable_journal_ids')
    retention_filter_type_domain = fields.Char(compute='_compute_retention_iva_filter_type_domain')
    amount_untaxed = fields.Monetary(string='Base Imponible', readonly=True, store=True, compute='_compute_all_amount',
                                     currency_field='company_currency_id', copy=False, tracking=True)
    amount_total_retention = fields.Monetary(string='Iva Retenido',  store=True, readonly=True,
                                             compute='_compute_all_amount', currency_field='company_currency_id',
                                             copy=False, tracking=True)
    amount_untaxed_usd = fields.Monetary(string='Base Imponible', readonly=True, store=True,
                                         compute='_compute_all_amount',
                                         currency_field='company_currency_id2', copy=False, tracking=True)
    amount_total_retention_usd = fields.Monetary(string='Iva Retenido', store=True, readonly=True,
                                                 compute='_compute_all_amount', currency_field='company_currency_id2',
                                                 copy=False, tracking=True)
    iva_send_file = fields.Many2one('ir.attachment', string='IVA Send file', copy=False)

    @api.model
    def create(self, vals):
        res = super(RetentionIva, self).create(vals)
        if res.move_type in ['in_invoice', 'in_refund']:
            res.name = self.env['ir.sequence'].next_by_code('iva.retention.supplier')
        else:
            res.number_retention = self.env['ir.sequence'].next_by_code('iva.retention.customer')
        return res

    def action_post(self):
        if self.company_id.is_iva:
            self.retention_movement()
        else:
            raise UserError("Disculpe!!!! Active la configuracion para poder Publicar las retenciones")

    def action_cancel(self):
        if self.move_id.state == 'cancel':
            self.write({'state': 'cancel'})
        else:
            raise ValidationError("Disculpe!!! Cancele primero la factura")

    def retention_movement(self):
        line = []
        zero = 0.0
        move_obj = self.env['account.move']
        iva_withheld = self.amount_total_retention
        balances = zero - iva_withheld
        value = {
            'name': self.name,
            'date': self.move_id.date,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'retention_iva_id': self.id,
            'ref': "Retencion del %s %% IVA de la Factura %s" % (self.partner_id.name, self.move_id.name),
            'move_type': "entry",
        }
        move = move_obj.create(value)

        if self.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
            line.append((0, 0, {
                'name': move.name,
                'ref': "Retención del %s %% ISLR de la Factura %s" % (self.partner_id.name, self.move_id.name),
                'move_id': self.move_id.id,
                'date': self.move_id.date,
                'partner_id': self.partner_id.id,
                'account_id': self.partner_id.property_account_receivable_vat_id.id if
                self.move_type in ['out_refund'] else
                self.partner_id.property_account_receivable_id.id,
                'credit': iva_withheld,
                'debit': 0.0,
                'balance': -iva_withheld,
                'price_unit': balances,
                'price_subtotal': balances,
                'price_total': balances

            }))
            line.append((0, 0, {
                'name': move.name,
                'ref': "Retención del %s %% ISLR de la Factura %s" % (self.partner_id.name, self.move_id.name),
                'move_id': self.move_id.id,
                'date': self.move_id.date,
                'partner_id': self.partner_id.id,
                'account_id': self.partner_id.property_account_receivable_id.id if
                self.move_type in ['out_refund'] else
                self.partner_id.property_account_receivable_vat_id.id,
                'debit': iva_withheld,
                'credit': 0.0,
                'balance': iva_withheld,
                'price_unit': balances,
                'price_subtotal': balances,
                'price_total': balances
            }))

        if self.move_type in ['in_invoice', 'in_refund']:
            if self.company_id.retention_iva == 'provider':

                line.append((0, 0, {
                    'name': self.name,
                    'ref': "Retención del %s %% IVA de la Factura %s" % (self.partner_id.name, self.move_id.name),
                    'move_id': self.move_id.id,
                    'date': self.move_id.date,
                    'partner_id': self.partner_id.id,
                    'account_id': self.partner_id.property_account_payable_id.id if
                    self.move_type in ['in_refund'] else
                    self.partner_id.property_account_payable_vat_id.id,
                    'credit': iva_withheld,
                    'debit': 0.0,
                    'balance': -iva_withheld,
                    'price_unit': balances,
                    'price_subtotal': balances,
                    'price_total': balances
                }))
                line.append((0, 0, {
                    'name': self.name,
                    'ref': "Retención del %s %% IVA de la Factura %s" % (self.partner_id.name, self.move_id.name),
                    'move_id': self.move_id.id,
                    'date': self.move_id.date,
                    'partner_id': self.partner_id.id,
                    'account_id': self.partner_id.property_account_payable_vat_id.id if
                    self.move_type in ['in_refund'] else
                    self.partner_id.property_account_payable_id.id,
                    'debit': iva_withheld,
                    'credit': 0.0,
                    'balance': iva_withheld,
                    'price_unit': balances,
                    'price_subtotal': balances,
                    'price_total': balances
                })),

            if self.company_id.retention_iva == 'company':
                line.append((0, 0, {
                    'name': self.name,
                    'ref': "Retención del %s %% IVA de la Factura %s" % (self.partner_id.name, self.move_id.name),
                    'move_id': self.move_id.id,
                    'date': self.move_id.date,
                    'partner_id': self.partner_id.id,
                    'account_id': self.company_id.partner_id.property_account_payable_id.id if
                    self.move_type in ['in_refund'] else
                    self.company_id.partner_id.property_account_payable_vat_id.id,
                    'credit': iva_withheld,
                    'debit': 0.0,
                    'balance': -iva_withheld,
                    'price_unit': balances,
                    'price_subtotal': balances,
                    'price_total': balances
                }))
                line.append((0, 0, {
                        'name': self.name,
                        'ref': "Retención del %s %% IVA de la Factura %s" % (self.partner_id.name, self.move_id.name),
                        'move_id': self.move_id.id,
                        'date': self.move_id.date,
                        'partner_id': self.partner_id.id,
                        'account_id': self.company_id.partner_id.property_account_payable_vat_id.id if
                        self.move_type in ['in_refund'] else
                        self.partner_id.company_id.property_account_payable_id.id,
                        'debit': iva_withheld,
                        'credit': 0.0,
                        'balance': iva_withheld,
                        'price_unit': balances,
                        'price_subtotal': balances,
                        'price_total': balances
                        })),

        move.write({'line_ids': line})
        self.write({'move_entry_id': move.id, 'state': 'done'})
        self.move_entry_id._post(soft=False)
        self.action_partial_reconcile(move)
        return move

    def action_partial_reconcile(self, move):
        vals = {}
        amount_debit = 0.0
        amount_credit = 0.0
        total = 0.0
        move_obj = self.env['account.move'].search([('retention_iva_id', '=', self.id),
                                                    ('move_type', '=', self.move_type)])
        move_line_obj = self.env['account.move.line'].search([('move_id', '=', move_obj.id)])
        for line in move_line_obj:

            if line.account_internal_type == 'payable' and line.debit == 0.0:
                vals.update({'credit_move_id': line.id})
                amount_credit += line.credit

            if line.account_internal_type == 'payable' and line.credit == 0.0:
                vals.update({'debit_move_id': line.id})
                amount_debit += line.debit

            if line.account_internal_type == 'receivable' and line.debit == 0.0:
                vals.update({'credit_move_id': line.id})
                amount_credit += line.credit

            if line.account_internal_type == 'receivable' and line.credit == 0.0:
                vals.update({'debit_move_id': line.id})
                amount_debit += line.debit

            for l in move.line_ids:

                if l.account_internal_type in ['payable', 'other'] and line.account_id.id == l.account_id.id\
                        and l.credit == 0.0:
                    vals.update({'debit_move_id': l.id})
                    amount_debit += l.debit

                if l.account_internal_type in ['payable', 'other'] and line.account_id.id == l.account_id.id\
                        and l.debit == 0.0:
                    vals.update({'credit_move_id': l.id})
                    amount_credit += l.credit

                if l.account_internal_type in ['receivable', 'other'] and line.account_id.id == l.account_id.id\
                        and l.debit == 0.0:
                    vals.update({'credit_move_id': l.id})
                    amount_credit += l.credit

                if l.account_internal_type in ['receivable', 'other'] and line.account_id.id == l.account_id.id\
                        and l.credit == 0.0:
                    vals.update({'debit_move_id': l.id})
                    amount_debit += l.debit

        if self.move_type in ['in_invoice', 'out_refund']:
            total += amount_debit

        elif self.move_type in ['out_invoice', 'in_refund']:
            total += amount_credit

        vals.update({
            'amount': total,
            'debit_amount_currency': self.amount_rate_retention_islr(total) if self.move_type == 'out_invoice'
            else total,
            'credit_amount_currency': self.amount_rate_retention_islr(total) if self.move_type == 'in_invoice'
            else total,
            'max_date': self.move_date,
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

    def print_report_iva(self):
        return self.env.ref('l10n_ve_iva_retention.action_iva_retention_report').report_action(self)

    @api.depends('iva_type')
    def _compute_retention_iva_filter_type_domain(self):
        for ret in self:
            if ret.islr_type in ['out_iva']:
                ret.retention_filter_type_domain = 'ret_iva'
            elif ret.islr_type in ['in_iva']:
                ret.retention_filter_type_domain = 'ret_iva'
            else:
                ret.retention_filter_type_domain = False

    @api.depends('company_id', 'retention_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = m.retention_filter_type_domain
            company_id = m.company_id.id or self.env.company.id
            domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

    @api.depends('line_ids.amount_tax', 'line_ids.amount_retention', 'os_currency_rate')
    def _compute_all_amount(self):
        for ret in self:
            amount_untaxed = 0.0
            amount_total_retention = 0.0
            for line in self.line_ids:
                amount_untaxed += line.amount_tax
                amount_total_retention += line.amount_retention
            ret.amount_untaxed = amount_untaxed
            ret.amount_total_retention = amount_total_retention
            if ret.os_currency_rate > 0.0 or ret.is_currency_rate:
                ret.amount_untaxed_usd = (ret.amount_untaxed / ret.os_currency_rate)
                ret.amount_total_retention_usd = (ret.amount_total_retention / ret.os_currency_rate)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        config = self.env['ir.config_parameter']
        if not config.get_param('is_iva'):
            msg = (
                'You cannot generate any retention IVA if it is not configured, Contact your administrator.')
            raise UserError(msg)
        elif config.get_param('retention_iva') == 'provider' and self.partner_id:
            rec_account = self.partner_id.property_account_receivable_vat_id
            pay_account = self.partner_id.property_account_payable_vat_id
            if not rec_account and not pay_account:
                msg = (
                    'Cant find a chart of accounts for this Client, you need to set it up.')
                raise UserError(msg)
        elif config.get_param('retention_iva') == 'company' and self.company_id.partner_id:
            rec_account = self.company_id.partner_id.property_account_receivable_vat_id
            pay_account = self.company_id.partner_id.property_account_payable_vat_id
            if not rec_account and not pay_account:
                msg = ('Cannot find a chart of accounts for this company, You should configure it.'
                       '\nPlease go to Account Configuration.')
                raise UserError(msg)

    @api.onchange('move_type')
    def onchange_islr_type(self):
        if self.move_type in ['in_invoice', 'in_refund'] and self.iva_type in ['out_iva']:
            msg = ('Excuse me!!! You can only enter customer invoices, corrective invoices and debits.'
                   '\ngo to the menu Accounting / Suppliers / Withholding Iva suppliers.')
            raise UserError(msg)
        if self.move_type in ['out_invoice', 'out_refund'] and self.iva_type in ['in_iva']:
            msg = ('Excuse me!!! You can only enter Customer Suppliers, Corrective Invoices Suppliers and Debits.'
                   '\ngo to the menu Accounting / Customer / Withholding Iva Customer.')
            raise UserError(msg)


class RetentionIvaLine(models.Model):
    _description = "Retention Iva Line"
    _name = 'retention.iva.line'
    _rec_name = 'retention_iva_id'

    retention_iva_id = fields.Many2one('retention.iva', readonly=True, invisible=True)
    state = fields.Selection(related='retention_iva_id.state', invisible=True)
    base = fields.Float(string='Base')
    amount_tax = fields.Float(string='Importe del Impuesto')
    amount_retention = fields.Float('retentcion')
    amount_untaxed = fields.Float(string='Monto sin impuestos')
    retention_rate = fields.Float(string='Rate',
                                  help="The retention rate can vary between 75% al 100% depending on the taxpayer.")
    tax_ids = fields.Many2many(comodel_name='account.tax', string="Taxes",
                               help="Taxes that apply on the base amount")
