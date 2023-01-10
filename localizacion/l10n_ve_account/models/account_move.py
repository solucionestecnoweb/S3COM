# -*- coding: utf-8 -*-

from odoo import api, fields, models


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

    @api.depends('credit', 'debit', 'balance', 'currency_id', 'move_id.date')
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

