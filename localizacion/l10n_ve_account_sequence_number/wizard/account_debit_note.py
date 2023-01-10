from odoo import models


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def _prepare_default_values(self, move):
        res = super(AccountDebitNote, self)._prepare_default_values(move)
        res['reason'] = move.invoice_number_next
        # if res['move_type'] == 'out_invoice':
        #     res.update({'move_type': 'out_debit'})
        return res

    def create_debit(self):
        res = super(AccountDebitNote, self).create_debit()
        if res['context']['default_move_type'] == 'out_invoice' and self.move_type == 'out_invoice':
            self.write({'move_type': 'out_debit'})
            res['context']['default_move_type'] = 'out_debit'
        return res
