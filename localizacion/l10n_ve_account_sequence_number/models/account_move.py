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
    delivery_note_next_number = fields.Char(string='Nro. Nota de Entrega', copy=False, tracking=True)
    is_delivery_note = fields.Boolean(default=False, tracking=True)
    is_delivery_note_aux = fields.Char(compute='_compute_nota')
    is_control_unique = fields.Boolean(related='company_id.is_control_unique')
    is_manual = fields.Boolean(string='Numeracion Manual', tracking=True)
    hide_book = fields.Boolean(string='Excluir de Libros', tracking=True, default=False)
    reason = fields.Char('Referencia de Factura')
    is_branch_office = fields.Boolean(string='Tiene sucursal', tracking=True)

    @api.onchange('move_type')
    def _compute_nota(self):
        for selff in self:
            if selff.move_type=='out_invoice':
                selff.is_delivery_note=False
            selff.is_delivery_note_aux='1'



    @api.onchange('is_delivery_note')
    def delivery_note_daily(self):
        for i in self:
            if i.is_delivery_note == True:
                i.journal_id = self.busca_diario_nota()

    def busca_diario_nota(self):
        id_d=0
        lista=self.env['account.journal'].search([('type','=','sale'),('nota_entrega','=',True)])
        if lista:
            for det in lista:
                id_d=det.id
        return id_d


    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        if self.move_type in ('in_invoice','in_refund','in_invoice','entry'):
            def journal_key(move):
                return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

            def date_key(move):
                return (move.date.year, move.date.month)

            grouped = defaultdict(  # key: journal_id, move_type
                lambda: defaultdict(  # key: first adjacent (date.year, date.month)
                    lambda: {
                        'records': self.env['account.move'],
                        'format': False,
                        'format_values': False,
                        'reset': False
                    }
                )
            )
            self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
            highest_name = self[0]._get_last_sequence() if self else False

            # Group the moves by journal and month
            for move in self:
                if not highest_name and move == self[0] and not move.posted_before and move.date:
                    # In the form view, we need to compute a default sequence so that the user can edit
                    # it. We only check the first move as an approximation (enough for new in form view)
                    pass
                elif (move.name and move.name != '/') or move.state != 'posted':
                    try:
                        if not move.posted_before:
                            move._constrains_date_sequence()
                        # Has already a name or is not posted, we don't add to a batch
                        continue
                    except ValidationError:
                        # Has never been posted and the name doesn't match the date: recompute it
                        pass
                group = grouped[journal_key(move)][date_key(move)]
                if not group['records']:
                    # Compute all the values needed to sequence this whole group
                    move._set_next_sequence()
                    group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
                    group['reset'] = move._deduce_sequence_number_reset(move.name)
                group['records'] += move

            # Fusion the groups depending on the sequence reset and the format used because `seq` is
            # the same counter for multiple groups that might be spread in multiple months.
            final_batches = []
            for journal_group in grouped.values():
                journal_group_changed = True
                for date_group in journal_group.values():
                    if (
                        journal_group_changed
                        or final_batches[-1]['format'] != date_group['format']
                        or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
                    ):
                        final_batches += [date_group]
                        journal_group_changed = False
                    elif date_group['reset'] == 'never':
                        final_batches[-1]['records'] += date_group['records']
                    elif (
                        date_group['reset'] == 'year'
                        and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
                    ):
                        final_batches[-1]['records'] += date_group['records']
                    else:
                        final_batches += [date_group]

            # Give the name based on previously computed values
            for batch in final_batches:
                for move in batch['records']:
                    move.name = batch['format'].format(**batch['format_values'])
                    batch['format_values']['seq'] += 1
                batch['records']._compute_split_sequence()

            self.filtered(lambda m: not m.name).name = '/'
        else:
            self.name="/"
          


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
        if self.is_delivery_note:
            if not self.delivery_note_next_number:
                self.delivery_note_next_number = self.get_nro_nota_entrega()
            if self.name == "/":
                self.name=self.journal_id.code+ "/" + self.delivery_note_next_number
        else:
            self.invoice_number_seq()
            self.invoice_control()
            #self.invoice_number_control_unique()
        for det_line_asiento in self.line_ids:
            if det_line_asiento.account_id.user_type_id.type in ('receivable','payable'):
                det_line_asiento.name = self.journal_id.code + "/" + self.delivery_note_next_number if self.delivery_note_next_number else self.invoice_number_next
                #det_line_asiento.nro_doc=nro_factura
        return res

    """def invoice_number_seq(self):
        if not self.is_manual:
            if self.move_type in ['out_invoice'] and not self.debit_origin_id and not self.invoice_number_next:
                self.invoice_number_next = self.get_invoice_number()
            if self.move_type in ['out_refund'] and not self.invoice_number_next:
                self.invoice_number_next = self.get_refund_number()
            if self.move_type in ['out_invoice'] and self.debit_origin_id and not self.invoice_number_next:
                self.invoice_number_next = self.get_receipt_number()"""

    def invoice_number_seq(self):
        if not self.is_manual:
            if self.move_type in ('out_invoice','out_refund','out_invoice','in_invoice','in_refund','in_invoice'):
                if not self.invoice_number_next or self.invoice_number_next==0:
                    self.invoice_number_next=self.get_invoice_nro_fact()
                    self.name=self.journal_id.code+"/"+str(self.invoice_number_next)

    def invoice_control(self):
        if not self.is_manual:
            if self.move_type in ('out_invoice','out_refund','out_invoice','in_invoice','in_refund','in_invoice'):
                if not self.invoice_number_control or self.invoice_number_control==0:
                    self.invoice_number_control=self.get_invoice_number_control()




    """def invoice_control(self):
        if not self.is_control_unique or not self.is_manual or not self.is_branch_office:
            if self.move_type in ['out_invoice'] and not self.debit_origin_id and not self.invoice_number_control:
                self.invoice_number_control = self.get_invoice_number_control()
            if self.move_type in ['out_refund'] and not self.invoice_number_control:
                self.invoice_number_control = self.get_refund_number_control()
            if self.move_type in ['out_invoice'] and self.debit_origin_id and not self.invoice_number_control:
                self.invoice_number_control = self.get_receipt_number_control()"""

    def invoice_number_control_unique(self):
        if self.is_control_unique and not self.is_manual or not self.is_branch_office:
            if self.move_type in ['out_invoice'] and not self.debit_origin_id and not self.invoice_number_unique:
                self.invoice_number_unique = self.get_number_control_unique()
            if self.move_type in ['out_refund'] and not self.invoice_number_unique:
                self.invoice_number_unique = self.get_number_control_unique()
            if self.move_type in ['out_invoice'] and self.debit_origin_id and not self.invoice_number_unique:
                self.invoice_number_unique = self.get_number_control_unique()

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

    def get_invoice_number(self):
        self.ensure_one()
        if not self.is_delivery_note:
            seq = self.env['ir.sequence'].get('account.out.invoice')
            return seq
        return ''

    #def get_invoice_number_control(self):
        #self.ensure_one()
        #if not self.is_delivery_note:
            #seq = self.env['ir.sequence'].get('account.out.invoice.control')
            #return seq
        #return ''

    def get_refund_number(self):
        self.ensure_one()
        if not self.is_delivery_note:
            seq = self.env['ir.sequence'].get('account.credit.note')
            return seq
        return ''

    def get_refund_number_control(self):
        self.ensure_one()
        if not self.is_delivery_note:
            seq = self.env['ir.sequence'].get('account.credit.note.control')
            return seq
        return ''

    def get_receipt_number(self):
        self.ensure_one()
        if not self.is_delivery_note:
            seq = self.env['ir.sequence'].get('account.debit.note.cli')
            return seq
        return ''

    def get_receipt_number_control(self):
        self.ensure_one()
        if not self.is_delivery_note:
            seq = self.env['ir.sequence'].get('account.debit.note.control')
            return seq
        return ''

    def get_number_control_unique(self):
        self.ensure_one()
        if not self.is_delivery_note:
            seq = self.env['ir.sequence'].get('account.control.unique')
            return seq
        return ''

    """def get_nro_nota_entrega(self):
                    self.ensure_one()
                    seq = self.env['ir.sequence'].get('account.delivery.note.sequence')
                    return seq"""

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
