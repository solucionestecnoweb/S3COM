# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api
_logger = logging.getLogger('__name__')


class AccountMove(models.Model):
    _inherit = 'account.move'

    branch_office_id = fields.Many2one(related='journal_id.branch_office_id')

    @api.constrains('branch_office_id')
    @api.onchange('branch_office_id')
    def _onchange_branch_office(self):
        for move in self:
            if move.is_branch_office:
                move.is_branch_office = True
            else:
                move.is_branch_office = False

    def invoice_number_seq(self):
        res = super(AccountMove, self).invoice_number_seq()
        for move in self:
            if move.is_branch_office:
                if self.move_type in ['out_invoice'] and not self.debit_origin_id and not self.invoice_number_next:
                    self.invoice_number_next = self.get_invoice_number_branch_office()
                if self.move_type in ['out_refund'] and not self.invoice_number_next:
                    self.invoice_number_next = self.get_refund_number_branch_office()
                if self.move_type in ['out_invoice'] and self.debit_origin_id and not self.invoice_number_next:
                    self.invoice_number_next = self.get_receipt_number_branch_office()
        return res

    def invoice_control(self):
        res = super(AccountMove, self).invoice_control()
        for move in self:
            if move.is_branch_office:
                if not self.is_control_unique or not self.is_manual or not self.is_branch_office:
                    if self.move_type in ['out_invoice'] and not self.debit_origin_id and not self.invoice_number_control:
                        self.invoice_number_control = self.get_invoice_number_control_branch_office()
                    if self.move_type in ['out_refund'] and not self.invoice_number_control:
                        self.invoice_number_control = self.get_refund_number_branch_office()
                    if self.move_type in ['out_invoice'] and self.debit_origin_id and not self.invoice_number_control:
                        self.invoice_number_control = self.get_refund_number_control_branch_office()
        return res

    def get_invoice_number_branch_office(self):
        self.ensure_one()
        if not self.is_delivery_note and self.journal_id.inv_sequence_id:
            sequence_code = self.journal_id.inv_sequence_id.code
            sequence_obj = self.env['ir.sequence'].with_context(force_company= self.company_id.id)
            name = sequence_obj.next_by_code(sequence_code)
            return name
        return ''

    def get_refund_number_branch_office(self):
        if not self.is_delivery_note and self.journal_id.inv_sequence_id:
            sequence_code = self.journal_id.inv_sequence_id.code
            sequence_obj = self.env['ir.sequence'].with_context(force_company= self.company_id.id)
            name = sequence_obj.next_by_code(sequence_code)
            return name
        return ''

    def get_receipt_number_branch_office(self):
        if not self.is_delivery_note and self.journal_id.inv_sequence_id:
            sequence_code = self.journal_id.inv_sequence_id.code
            sequence_obj = self.env['ir.sequence'].with_context(force_company= self.company_id.id)
            name = sequence_obj.next_by_code(sequence_code)
            return name
        return ''

    def get_invoice_number_control_branch_office(self):
        if not self.is_delivery_note and self.journal_id.ctrl_sequence_id:
            sequence_code = self.journal_id.ctrl_sequence_id.code
            sequence_obj = self.env['ir.sequence'].with_context(force_company= self.company_id.id)
            name = sequence_obj.next_by_code(sequence_code)
            return name
        return ''

    def get_refund_number_branch_office(self):
        if not self.is_delivery_note and self.journal_id.ctrl_sequence_id:
            sequence_code = self.journal_id.ctrl_sequence_id.code
            sequence_obj = self.env['ir.sequence'].with_context(force_company= self.company_id.id)
            name = sequence_obj.next_by_code(sequence_code)
            return name
        return ''

    def get_refund_number_control_branch_office(self):
        if not self.is_delivery_note and self.journal_id.ctrl_sequence_id:
            sequence_code = self.journal_id.ctrl_sequence_id.code
            sequence_obj = self.env['ir.sequence'].with_context(force_company= self.company_id.id)
            name = sequence_obj.next_by_code(sequence_code)
            return name
        return ''
