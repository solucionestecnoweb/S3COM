# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import ValidationError
import logging
import base64
_logger = logging.getLogger('__name__')


class AccountMove(models.Model):
    _inherit = 'account.move'

    retention_iva_id = fields.Many2one('retention.iva', string='Retencion IVA', readonly=True, copy=False)
    state_email_iva = fields.Selection([('send', 'Enviado')])

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.post_retention_iva()
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        if self.retention_iva_id.move_entry_id:
            self.retention_iva_id.move_entry_id.write({'state': "draft"})
            for move in self.retention_iva_id.move_entry_id.line_ids:
                move.unlink()
            self.retention_iva_id.move_entry_id.with_context(force_delete=True).unlink()
        for ret in self.retention_iva_id.line_ids:
            ret.unlink()
        self.retention_iva_id.unlink()
        return res

    def post_retention_iva(self):
        concept = False
        for move in self.invoice_line_ids:
            if move.tax_ids.filtered(lambda x: x.aliquot == 'na'):
                raise ValidationError('Configure el tipo de alicuota por cada impuesto para poder generar la retencion')
            if move.tax_ids.filtered(lambda x: x.aliquot != 'exempt'):
                concept = True
        if concept:
            self.action_retention()

    def action_retention(self):
        if not self.retention_iva_id:
            retention_iva_obj = self.env['retention.iva']
            if self.move_type not in ['entry'] and self.partner_id.people_type \
                    and self.partner_id.property_account_payable_vat_id \
                    and self.partner_id.property_account_receivable_vat_id:
                journal = self.env['account.journal'].search([('type', '=', 'ret_iva')])
                ret = retention_iva_obj.create({
                    'partner_id': self.partner_id.id,
                    'move_id': self.id,
                    'move_date': self.date,
                    'iva_date': self.date,
                    'journal_id': journal.id,
                    'iva_type': 'out_iva' if self.move_type in ['out_refund', 'out_invoice']
                    else 'in_iva'
                })
                self.write({'retention_iva_id': ret.id})
                self.tax_aliquot_general(ret)
                self.tax_aliquot_reduced(ret)
                self.tax_aliquot_additional(ret)
                if self.move_type in ['in_invoice', 'in_refund']:
                     self.retention_iva_id.action_post()
        return self.retention_iva_id

    def tax_aliquot_general(self, ret):
        base = 0.0
        amount_iva = 0.0
        rate = self.partner_id.retention_iva_rate
        for move in self.invoice_line_ids.filtered(lambda x: x.tax_ids.aliquot == 'general'):
            base += move.price_subtotal
            amount_iva += (move.price_total - move.price_subtotal)
            ret.write({
                'line_ids': [(0, 0, {
                    'retention_iva_id': ret.id,
                    'amount_tax': amount_iva,
                    'amount_retention': (amount_iva * rate) / 100,
                    'retention_rate': rate,
                    'base': base,
                    'tax_ids': move.tax_ids.ids,
                    'amount_untaxed': base
                })]
            })

    def tax_aliquot_reduced(self, ret):
        base = 0.0
        amount_iva = 0.0
        rate = self.partner_id.retention_iva_rate
        for move in self.invoice_line_ids.filtered(lambda x: x.tax_ids.aliquot == 'reduced'):
            base += move.price_subtotal
            amount_iva += (move.price_total - move.price_subtotal)
            ret.write({
                'line_ids': [(0, 0, {
                    'retention_iva_id': ret.id,
                    'amount_tax': amount_iva,
                    'amount_retention': (amount_iva * rate) / 100,
                    'retention_rate': rate,
                    'base': base,
                    'tax_ids': move.tax_ids.ids,
                    'amount_untaxed': base
                })]
            })

    def tax_aliquot_additional(self, ret):
        base = 0.0
        amount_iva = 0.0
        rate = self.partner_id.retention_iva_rate
        for move in self.invoice_line_ids.filtered(lambda x: x.tax_ids.aliquot == 'additional'):
            base += move.price_subtotal
            amount_iva += (move.price_total - move.price_subtotal)
            ret.write({
                'line_ids': [(0, 0, {
                    'retention_iva_id': ret.id,
                    'amount_tax': amount_iva,
                    'amount_retention': (amount_iva * rate) / 100,
                    'retention_rate': rate,
                    'base': base,
                    'tax_ids': move.tax_ids.ids,
                    'amount_untaxed': base
                })]
            })

    # def amount_rate_retention_iva(self, amount):
    #     amount_aux = 0.0
    #     result = 0.0
    #     rate = self.env['res.currency.rate'].search(
    #         [('currency_id', '=', self.currency_id.id), ('name', '<=', self.date)], order="name asc")
    #     if self.currency_id != self.company_id.currency_id:
    #         for r in rate:
    #             if self.date >= r.name:
    #                 amount_aux += r.rate
    #         rate = round(1 / amount_aux, 2)
    #         result += amount * rate
    #     else:
    #         result += amount
    #     return result

    def send_retention_iva(self):
        attach = {}
        if not self.partner_id.email:
            raise ValidationError('Debe tener un correo antes de poder enviar el comprobante')

        template = self.env.ref('l10n_ve_iva_retention.email_template_retention_iva_send_email', False)
        result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
            'l10n_ve_iva_retention.report_iva_retention')._render_qweb_pdf(self.retention_iva_id.id)
        attach['name'] = 'Comprobante de IVA.pdf'
        attach['type'] = 'binary'
        attach['datas'] = base64.b64encode(result_pdf)
        attach['res_id'] =  self.retention_iva_id.id
        attach['res_model'] = 'retention.iva'
        attachment_id = self.env['ir.attachment'].create(attach)
        self.retention_iva_id.write({'iva_send_file': attachment_id.id})
        mail = template.send_mail(self.retention_iva_id.id, force_send=True)
        if mail:
            self.message_post(body="Enviado email al Cliente: %s" % self.partner_id.name,
                              attachments_ids=[attachment_id.id])
            self.write({'state_email_iva': 'send'})

    def _reverse_moves(self, default_values_list=None, cancel=False):
        res = super(AccountMove, self)._reverse_moves(default_values_list, cancel)
        res.write({
            'ref': res.id
        })
        return res

    def _check_balanced(self):
        """ Assert the move is fully balanced debit = credit.
            An error is raised if it's not the case.
        """
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(self.env['account.move.line']._fields)
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
