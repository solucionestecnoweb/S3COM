# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings

#forbidden fields
INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')
#_logger = logging.getLogger('__name__')


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_number_next = fields.Char(string='Nro Invoice', copy=False, tracking=True)
    invoice_number_control = fields.Char(string='Nro Control', copy=False, tracking=True)
    invoice_number_unique = fields.Char(string='Nro Control Unique', copy=False, tracking=True)
    delivery_note_next_number = fields.Char(string='Nro. Nota de Entrega',tracking=True)
    is_delivery_note = fields.Boolean(default=False, tracking=True)
    is_delivery_note_aux = fields.Char()
    is_control_unique = fields.Boolean(related='company_id.is_control_unique')
    is_manual = fields.Boolean(string='Numeracion Manual', tracking=True)
    hide_book = fields.Boolean(string='Excluir de Libros', tracking=True, default=False)
    reason = fields.Char('Referencia de Factura')
    is_branch_office = fields.Boolean(string='Tiene sucursal', tracking=True)

    @api.onchange('is_delivery_note')
    def delivery_note_daily(self):
        for i in self:
            if i.is_delivery_note == True:
                i.journal_id = self.busca_diario_nota(i.move_type)

    def busca_diario_nota(self,move_type):
        id_d=0
        if move_type in ('in_invoice','in_refund','in_receipt'):
            tipo='purchase'
        if move_type in ('out_invoice','out_refund','out_receipt'):
            tipo='sale'
        lista=self.env['account.journal'].search([('type','=',tipo),('nota_entrega','=',True)])
        if lista:
            for det in lista:
                id_d=det.id
        return id_d

    @api.onchange('move_type')
    def _onchange_default_manual(self):
        if self.move_type in ['in_invoice', 'in_refund']:
            self.is_manual = True

    @api.onchange('is_delivery_note')
    def _onchange_hide_books(self):
        if self.is_delivery_note:
            self.hide_book = True
        else:
            self.hide_book = False



    def action_post(self):
        res = super(AccountMove, self).action_post()
        #if self.is_delivery_note and not self.delivery_note_next_number:
        if self.move_type!='entry':
            if self.is_delivery_note:
                if not self.delivery_note_next_number:
                    self.delivery_note_next_number = self.get_nro_nota_entrega()
                self.name=self.journal_id.code+ "/" + self.delivery_note_next_number
            else:
                self.invoice_number_seq()
                self.invoice_control()
                self.name= self.invoice_number_next
                #self.name= self.journal_id.code + "/" +self.invoice_number_next
                #self.payment_reference=self.invoice_number_next
            for det_line_asiento in self.line_ids:
                if det_line_asiento.account_id.user_type_id.type in ('receivable','payable'):
                    #det_line_asiento.name = self.journal_id.code + "/" + self.delivery_note_next_number if self.delivery_note_next_number else self.invoice_number_next
                    det_line_asiento.name = self.journal_id.code + "/" + self.delivery_note_next_number if self.delivery_note_next_number else self.invoice_number_next
                    #det_line_asiento.nro_doc=nro_factura
        return res

    def invoice_number_seq(self):
        if not self.is_manual:
            if self.move_type in ('out_invoice','out_refund','out_receipt','in_invoice','in_refund','in_receipt'):
                if not self.invoice_number_next or self.invoice_number_next==0:
                    #self.invoice_number_next=self.journal_id.code + "/" +self.get_invoice_nro_fact()
                    self.invoice_number_next=self.get_invoice_nro_fact()
                #else:
                    #self.name=str(self.invoice_number_next)

    def invoice_control(self):
        if not self.is_manual:
            if self.move_type in ('out_invoice','out_refund','out_receipt','in_invoice','in_refund','in_receipt'):
                if not self.invoice_number_control or self.invoice_number_control==0:
                    self.invoice_number_control=self.get_invoice_number_control()

    def get_invoice_nro_fact(self):
        name=''
        if not self.journal_id.doc_sequence_id:
            raise UserError(_('Este diario no tiene configurado el Nro de Documento. Vaya al diario, pestaña *Configuracion sec. Facturación* y en el campo *Proximo Nro Documento* agregue uno'))
        else:
            if not self.journal_id.doc_sequence_id.code:
                raise UserError(_('La secuencia del Nro documento llamado * %s * de este diario, no tiene configurada el Código se secuencias')%self.journal_id.doc_sequence_id.name)
            else:
                SEQUENCE_CODE=self.journal_id.doc_sequence_id.code
                company_id = self.company_id.id
                IrSequence = self.env['ir.sequence'].with_context(force_company=company_id)
                name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name

    def get_invoice_number_control(self):
        name=''            
        if not self.journal_id.ctrl_sequence_id:
            raise UserError(_('Este diario no tiene configurado el Nro de control. vaya al diario, pestaña *Configuracion sec. Facturación* y en el campo *Proximo Nro control* agregue uno'))
        else:
            if not self.journal_id.ctrl_sequence_id.code:
                raise UserError(_('La secuencia del Nro control llamado * %s * de este diario, no tiene configurada el Código se secuencias')%self.journal_id.ctrl_sequence_id.name)
            else:
                SEQUENCE_CODE=self.journal_id.ctrl_sequence_id.code
                company_id = self.company_id.id
                IrSequence = self.env['ir.sequence'].with_context(force_company=company_id)
                name = IrSequence.next_by_code(SEQUENCE_CODE)

        return name

    def get_nro_nota_entrega(self):
        name=''
        if self.journal_id.nota_entrega!=True:
            raise UserError(_('Este diario no esta configurado para nota de entrega. Vaya al diario, pestaña *Configuracion sec. Facturación* y habilite el campo nota de entrega'))
        if not self.journal_id.doc_sequence_id:
            raise UserError(_('Este diario no tiene configurado el Nro de nota de entrega. Vaya al diario, pestaña *Configuracion sec. Facturación* y en el campo *Proximo Nro Documento* agregue uno'))
        else:
            if not self.journal_id.doc_sequence_id.code:
                raise UserError(_('La secuencia del Nro documento llamado * %s * de este diario, no tiene configurada el Código se secuencias')%self.journal_id.doc_sequence_id.name)
            else:
                SEQUENCE_CODE=self.journal_id.doc_sequence_id.code
                company_id = self.company_id.id
                IrSequence = self.env['ir.sequence'].with_context(force_company=company_id)
                name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name
