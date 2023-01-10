# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import base64
import logging
_logger = logging.getLogger('__name__')


class AccountMove(models.Model):
    _inherit = 'account.move'

    retention_id = fields.Many2one('isrl.retention', string='ISLR', readonly="True", copy=False)
    state_email_islr = fields.Selection([('send', 'Enviado')], copy=False)
    islr_send_file = fields.Many2one('ir.attachment', string='ISLR Send file', copy=False)

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.post_retention()
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        if self.retention_id.move_entry_id:
            self.retention_id.move_entry_id.write({'state': "draft"})
            for move in self.retention_id.move_entry_id.line_ids:
                move.unlink()
            self.retention_id.move_entry_id.with_context(force_delete=True).unlink()
        for ret in self.retention_id.line_ids:
            ret.unlink()
        self.retention_id.unlink()
        return res

    def post_retention(self):
        concept = False
        for move in self.invoice_line_ids:
            if move.product_id.concept_isrl_id:
                concept = True
        if concept:
            self.pre_retention()

    def pre_retention(self):
        if not self.retention_id:
            retention_obj = self.env['isrl.retention']
            retention_line_obj = self.env['isrl.retention.line']
            if self.move_type not in ['entry']  \
                    and self.partner_id.property_account_receivable_isrl_id \
                    and self.partner_id.property_account_payable_isrl_id and self.partner_id.people_type != 'na':
                journal = self.env['account.journal'].search([('type', '=', 'islr')])
                self.retention_id = retention_obj.create({
                    'move_id': self.id,
                    'partner_id': self.partner_id.id,
                    'journal_id': journal.id,
                    'move_date': self.date,
                    'isrl_date': self.date,
                    'move_type': self.move_type,
                    'islr_type': 'out_islr' if self.move_type in ['out_refund', 'out_invoice']
                    else 'in_islr'
                })

                for move in self.invoice_line_ids:
                    for r in move.rate_ids:
                        base = (move.price_subtotal * r.subtotal) / 100
                        subtotal = (base * r.retention_percentage / 100)
                        total = subtotal
                        if self.partner_id.people_type == r.people_type:
                            retention_line_obj.create({
                                'islr_concept_id': move.concept_isrl_id.id,
                                'code': r.code,
                                'retention_id': self.retention_id.id,
                                'qty': r.retention_percentage,
                                'base': base,
                                'qty_retention': subtotal,
                                'subtracting': r.subtract,
                                'total': total
                            })
                if self.move_type in ['in_invoice', 'in_refund']:
                    self.retention_id.action_post()

    def amount_rate_retention(self, amount):
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

    def send_retention_islr(self):
        attach = {}
        if not self.partner_id.email:
            raise ValidationError('Debe tener un correo antes de poder enviar el comprobante')
        template = self.env.ref('l10n_ve_isrl_retention.email_template_retention_islr_send_email', False)
        result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
            'l10n_ve_isrl_retention.report_islr_retention')._render_qweb_pdf(self.retention_id.id)
        attach['name'] = 'Comprobante de ISLR.pdf'
        attach['type'] = 'binary'
        attach['datas'] = base64.b64encode(result_pdf)
        attach['res_id'] = self.retention_id.id
        attach['res_model'] = 'isrl.retention'
        attachment_id = self.env['ir.attachment'].create(attach)
        self.retention_id.write({'islr_send_file': attachment_id.id})
        mail = template.send_mail(self.retention_id.id, force_send=True)
        if mail:
            self.message_post(body="Enviado email al Cliente: %s" % self.partner_id.name,
                              attachments_ids=[attachment_id.id])
            self.write({'state_email_islr': 'send'})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    concept_isrl_id = fields.Many2one('islr.concept', string='ISLR Concepto', compute='compute_product_id', store=True)
    retention_id = fields.Many2one(related='move_id.retention_id', string='ISLR', copy=False, store=True)
    rate_ids = fields.Many2many('islr.rate', string='Rates', compute='compute_rate', store=True)

    @api.depends('product_id')
    def compute_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue
            line.concept_isrl_id = line.product_id.concept_isrl_id.id

    @api.depends('concept_isrl_id')
    def compute_rate(self):
        for line in self:
            if line.concept_isrl_id.rate_ids:
                line.rate_ids = line.concept_isrl_id.rate_ids
