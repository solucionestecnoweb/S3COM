# -*- coding: utf-8 -*-

from odoo import fields, models
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class AccountDiaryBook(models.TransientModel):
    _name = 'account.diary.book'
    _description = 'Diary Book'
    _rec_name = 'id'

    f_inicio = fields.Date("Fecha de inicio", required=True, copy=False)
    f_fin = fields.Date("Fecha final", required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    def action_print_book(self):
        start_time = datetime.now()
        lines = []
        total_debit = 0.0
        total_credit = 0.0
        account_obj = self.env['account.account'].search([], order="code asc")
        for account in account_obj.filtered(lambda x: x.current_balance > 0.0):
            amount_debit = 0.0
            amount_credit = 0.0
            line_obj = self.env['account.move.line'].search(
                [('date', '>=', self.f_inicio), ('date', '<=', self.f_fin), ('account_id', '=', account.id),
                 ('parent_state', '=', 'posted')])
            for line in line_obj:
                amount_debit += line.debit
                amount_credit += line.credit
                total_debit += line.debit
                total_credit += line.credit
            if line_obj:
                lines.append({
                    'code': account.code,
                    'name': account.name,
                    'account_id': account.id,
                    'debit': amount_debit,
                    'total_debit': total_debit,
                    'credit': amount_credit,
                    'total_credit': total_credit,
                })

        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'action_print_book',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return lines

    def print_report(self):
        return self.env.ref('l10n_ve_diary_book.action_account_diary_book_report').report_action(self)
