# -*- coding: utf-8 -*-

from odoo import fields, models
import logging
_logger = logging.getLogger('__name__')


class AccountMove(models.Model):
    _inherit = 'account.move'

    municipal_id = fields.Many2one('tax.municipal', string='Retencion Municipal', readonly=True, copy=False)
    state_email_municipal = fields.Selection([('send', 'Enviado')])

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.post_retention_municipal()
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        if self.municipal_id.move_entry_id:
            self.municipal_id.move_entry_id.write({'state': "draft"})
            for move in self.municipal_id.move_entry_id.line_ids:
                move.unlink()
            self.municipal_id.move_entry_id.with_context(force_delete=True).unlink()
        for ret in self.municipal_id.line_mun_ids:
            ret.unlink()
        self.municipal_id.unlink()
        return res

    def post_retention_municipal(self):
        concept = False
        for move in self.invoice_line_ids:
            if move.concept_id.aliquot > 0:
                concept = True
        if concept:
            self.action_retention_municipal()

    def action_retention_municipal(self):
        if not self.municipal_id:
            retention_municipal_obj = self.env['tax.municipal']
            retention_municipal_lne_obj = self.env['tax.municipal.line']
            if self.move_type not in ['entry'] and self.partner_id.people_type \
                    and self.partner_id.property_account_payable_municipal_id \
                    and self.partner_id.property_account_receivable_municipal_id:
                journal = self.env['account.journal'].search([('type', '=', 'mun_tax')])
                self.municipal_id = retention_municipal_obj.create({
                    'partner_id': self.partner_id.id,
                    'move_id': self.id,
                    'journal_id': journal.id,
                    'mun_tax_type': 'out_tax' if self.move_type in ['out_refund', 'out_invoice']
                    else 'in_tax'
                })
                for move in self.invoice_line_ids:
                    if move.concept_id.aliquot > 0:
                        retention_municipal_lne_obj.create({
                            'code': move.concept_id.code,
                            'aliquot': move.concept_id.aliquot,
                            'concept_id': move.concept_id.id,
                            'base_tax': self.amount_rate_retention_municipal(move.price_subtotal),
                            'mun_tax_id': self.municipal_id.id,
                        })
                if self.move_type in ['in_invoice', 'in_refund']:
                    self.municipal_id.action_post()

    def amount_rate_retention_municipal(self, amount):
        amount_aux = 0.0
        result = 0.0
        rate = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency_id.id), ('name', '<=', self.date)], order="name asc")
        if self.currency_id != self.company_id.currency_id:
            for r in rate:
                if self.date >= r.name:
                    amount_aux += r.rate
            rate = round(1 / amount_aux, 2)
            result += amount * rate
        else:
            result += amount
        return result

    def send_retention_municipal(self):
        pass
        # attachment_ids = []
        # attach = {}
        # if self.retention_id:
        #     template = self.env.ref('l10n_ve_municipal_tax.email_template_retention_municipal_send_email', False)
        #     result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
        #         'l10n_ve_municipal_tax.report_iva_retention')._render_qweb_pdf(self.retention_iva_id.id)
        #     attach['name'] = 'Comprobante de IVA.pdf'
        #     attach['type'] = 'binary'
        #     attach['datas'] = base64.b64encode(result_pdf)
        #     attach['res_model'] = 'mail.compose.message'
        #     attachment_id = self.env['ir.attachment'].create(attach)
        #     attachment_ids.append(attachment_id.id)
        #
        #     mail = template.send_mail(self.id, force_send=True, email_values={'attachment_ids': attachment_ids})
        #     if mail:
        #         self.message_post(body="Enviado email al Cliente: %s" % self.partner_id.name,
        #                           attachments_ids=[attachment_id.id])
        #         self.write({'state_email_iva': 'send'})


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    concept_id = fields.Many2one('municipal.concept', string="Retention concept", copy=False)
