from odoo import models, _


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        res['reason'] = move.invoice_number_next
        res['delivery_note_next_number'] = move.delivery_note_next_number
        return res

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()
        for move in self.new_move_ids:
            if not move.is_delivery_note:
                move.invoice_number_seq()
                move.invoice_control()
                move.invoice_number_control_unique()
        return res
