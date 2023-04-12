# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.exceptions import Warning
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import datetime, timedelta

class AccountPaymentIgtf(models.TransientModel):
    _name = "account.igtf.payment"

    journal_id=fields.Many2one('account.journal')
    importe_igtf_aux=fields.Monetary(compute='_compute_importe_igtf',store=True)
    importe_igtf=fields.Monetary()
    fecha=fields.Datetime(default=lambda *a:(datetime.now() + timedelta(days=(0))).strftime('%Y-%m-%d'))
    currency_id=fields.Many2one('res.currency',default=3)
    move_id = fields.Many2one('account.move',compute='_compute_factura')

    def action_register_igtf_payment(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        #raise UserError(_('valor=%s')%active_ids[0])
        #self.sale_ext_order_id=active_ids[0]
        return {
            'name': _('Register Payment'),
            'res_model': len(active_ids) == 1 and 'account.igtf.payment',
            'view_mode': 'form',
            'view_id': len(active_ids) != 1 and self.env.ref('vista_from_igtf_pago').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.onchange('journal_id')
    def _compute_factura(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        if active_ids:
            valida=self.env['account.move'].search([('id','=',active_ids[0])])
            if valida:
                self.move_id=active_ids[0]


    @api.onchange('journal_id')
    def _compute_importe_igtf(self):
        monto=0
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        if active_ids:
            valida=self.env['account.move'].search([('id','=',active_ids[0])])
            if valida:
                for det in valida:
                    monto=det.impuesto_igtf
                    if det.currency_id.id!=det.company_id.currency_id.id:
                        monto=det.impuesto_igtf*self.busca_tasa(det)#*det.os_currency_rate
                    else:
                        monto=det.impuesto_igtf
        self.importe_igtf=monto
        self.importe_igtf_aux=monto


    def busca_tasa(self,det):
        tasa=1
        if self.currency_id.id==self.env.company.currency_id.id:
            busca=self.env['res.currency.rate'].search([('currency_id','=',2),('name','<=',det.invoice_date)],order='name asc')
            if busca:
                for det in busca:
                    tasa=1/det.rate
        else:
            if self.amount_total or self.amount_total!=0:
                tasa=self.amount_total_signed/self.amount_total
        return tasa


    def pagar(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        #raise UserError(_('id=%s')%active_ids)
        if active_ids:
            busca=self.env['account.move'].search([('id','=',active_ids[0])],limit=1)
            if busca:
                for rec in busca:
                    rec.write({
                        'igtf_pagado':"True",
                        'payment_state':"paid",
                        })
                    if rec.igtf_ids:
                        for line in rec.igtf_ids:
                            line.asiento_igtf.button_draft()
                            line.asiento_igtf.posted_before=False
                            line.asiento_igtf.name='/'
                            line.asiento_igtf.journal_id=self.journal_id.id
                            # si es fact cliente
                            if rec.move_type in ('out_invoice','out_refund'):
                                for item in line.asiento_igtf.line_ids:
                                     if item.credit==0:
                                        item.account_id=self.journal_id.default_account_id.id
                                        item.name='IGTF del pago'
                            # si es fact proveedor
                            if rec.move_type in ('in_invoice','in_refund'):
                                for item in line.asiento_igtf.line_ids:
                                     if item.debit==0:
                                        item.account_id=self.journal_id.default_account_id.id
                                        item.name='IGTF del pago'
                            line.asiento_igtf.action_post()

class AccountMove(models.Model):
    _name = "account.move"
    _inherit = "account.move"

    igtf_ids=fields.One2many('account.payment.igtf','move_id', string='Cobros IGTF')

    amount_exento = fields.Monetary(compute='_compute_exento')
    amount_imponible = fields.Monetary(compute='_compute_exento')
    amount_exento_signed = fields.Monetary(default=0)

    espacio = fields.Char(default=" ")   
    
    
    ########### CAMPOS DEL GRUPO 1 NORMAL #############
    total_lineas_org = fields.Monetary(compute='_compute_total_lineas_org')
    total_impuesto_org = fields.Monetary(compute='_compute_total_tax_org')
    base_imponible_org = fields.Monetary(compute='_compute_total_lineas_org')
    exemto_org = fields.Monetary(compute='_compute_total_lineas_org')
    sub_total_org = fields.Monetary(compute='_compute_sub_total_org')

    pago_bs = fields.Monetary(compute='_compute_pago_bs')
    pago_divisa = fields.Monetary(compute='_compute_pago_div')
    impuesto_igtf = fields.Monetary(compute='_compute_pago_div')
    total_pagar = fields.Monetary(compute='_compute_total_paga')
    total_adeudado_org = fields.Monetary(compute='_compute_adeudado_org')

    ########## CAMPOS EQUIVALENTE DEL GROUP 2 ########
    total_lineas_eq = fields.Float(compute='_compute_total_lineas')
    #amount_by_group_eq = fields.Binary(string="Tax amount by group",compute='_compute_taxes_group')
    total_impuesto_eq = fields.Float(compute='_compute_total_tax_eq')
    base_imponible_eq = fields.Float()
    exemto_eq = fields.Float()
    sub_total_eq = fields.Float(compute='_compute_sub_total_eq')
    pago_bs_eq = fields.Float(compute='_compute_pago_bs_eq')
    pago_usd_eq = fields.Float(compute='_compute_pago_usd_eq')
    impuesto_igtf_eq = fields.Float(compute='_compute_igtf_eq')
    total_pagar_eq = fields.Float(compute='_compute_total_eq')
    total_adeudado_eq = fields.Float(compute='_compute_adeudado_eq')
    igtf_pagado = fields.Char(default='False')
    sub_total_pagado = fields.Char(default='False') # Nuevo

########## FUNCIONES DE CAMPOS EQUIVALENTE DEL GROUP 1 ########
    def _compute_total_lineas_org(self):
        for selff in self:
            total_lineas=total_imponible=total_exemto=0
            for rec in selff.invoice_line_ids:
                total_lineas=total_lineas+rec.price_subtotal
                if rec.tax_ids:
                    for det in rec.tax_ids:
                        if det.amount!=0:
                            total_imponible=total_imponible+rec.price_subtotal
                        else:
                            total_exemto=total_exemto+rec.price_subtotal
            selff.total_lineas_org=total_lineas
            selff.base_imponible_org=total_imponible
            selff.exemto_org=total_exemto

    def _compute_total_tax_org(self):
        valor=0
        for selff in self:
            for line in selff.invoice_line_ids:
                if line.tax_ids:
                    for det in line.tax_ids:
                        valor=valor+line.price_subtotal*det.amount/100
            selff.total_impuesto_org=valor

    def _compute_sub_total_org(self):
        for selff in self:
            selff.sub_total_org=self.amount_total #selff.total_impuesto_org+selff.total_lineas_org

    def _compute_adeudado_org(self):
        for selff in self:
            selff.total_adeudado_org=selff.amount_residual

 ########## FUNCIONES DE CAMPOS EQUIVALENTE DEL GROUP 2 ########
    def _compute_total_lineas(self):
        total_lineas=total_imponible=total_exemto=0
        for rec in self.invoice_line_ids:
            total_lineas=total_lineas+rec.price_subtotal
            if rec.tax_ids:
                for det in rec.tax_ids:
                    if det.amount!=0:
                        total_imponible=total_imponible+rec.price_subtotal
                    else:
                        total_exemto=total_exemto+rec.price_subtotal
        self.total_lineas_eq=abs(total_lineas*self.busca_tasa()) if self.currency_id.id!=self.env.company.currency_id.id else abs(total_lineas/self.busca_tasa())
        self.base_imponible_eq=abs(total_imponible*self.busca_tasa()) if self.currency_id.id!=self.env.company.currency_id.id else abs(total_imponible/self.busca_tasa())
        self.exemto_eq=abs(total_exemto*self.busca_tasa()) if self.currency_id.id!=self.env.company.currency_id.id else abs(total_exemto/self.busca_tasa())

    def _compute_sub_total_eq(self):
        if self.currency_id.id==self.env.company.currency_id.id:
            self.sub_total_eq=abs(self.amount_total/self.busca_tasa())
        else:
            self.sub_total_eq=abs(self.amount_total*self.busca_tasa())

    def _compute_total_tax_eq(self):
        if self.currency_id.id==self.env.company.currency_id.id:
            self.total_impuesto_eq=abs(self.total_impuesto_org/self.busca_tasa())
        else:
            self.total_impuesto_eq=abs(self.total_impuesto_org*self.busca_tasa())

    def _compute_pago_bs_eq(self):
        if self.currency_id.id==self.env.company.currency_id.id:
            self.pago_bs_eq=abs(self.pago_bs/self.busca_tasa())
        else:
            self.pago_bs_eq=abs(self.pago_bs*self.busca_tasa())

    def _compute_pago_usd_eq(self):
        """if self.currency_id.id==self.env.company.currency_id.id:
            self.pago_usd_eq=abs(self.pago_divisa/self.busca_tasa())
        else:
            self.pago_usd_eq=abs(self.pago_divisa*self.busca_tasa())"""
        valor=igtf=0
        for selff in self:
            if selff.igtf_ids:
                for rec in selff.igtf_ids:
                    if selff.currency_id.id==selff.env.company.currency_id.id:
                        valor=valor+round(rec.monto_base_usd,1)
                        #igtf=igtf+rec.monto_ret
                    else:
                        valor=valor+rec.monto_base
                        #igtf=igtf+rec.monto_ret/rec.tasa
            selff.pago_usd_eq=valor
            #selff.impuesto_igtf=igtf

    def _compute_igtf_eq(self):
        """if self.currency_id.id==self.env.company.currency_id.id:
            self.impuesto_igtf_eq=abs(self.impuesto_igtf/self.busca_tasa())
        else:
            self.impuesto_igtf_eq=abs(self.impuesto_igtf*self.busca_tasa())"""
        valor=igtf=0
        for selff in self:
            if selff.igtf_ids:
                for rec in selff.igtf_ids:
                    if selff.currency_id.id==selff.env.company.currency_id.id:
                        igtf=igtf+rec.monto_ret/rec.tasa
                    else:
                        igtf=igtf+rec.monto_ret
            selff.impuesto_igtf_eq=igtf

    def _compute_total_eq(self):
        if self.currency_id.id==self.env.company.currency_id.id:
            self.total_pagar_eq=abs(self.total_pagar/self.busca_tasa())
        else:
            self.total_pagar_eq=abs(self.total_pagar*self.busca_tasa())

    def _compute_adeudado_eq(self):
        if self.currency_id.id==self.env.company.currency_id.id:
            self.total_adeudado_eq=abs(self.total_adeudado_org/self.busca_tasa())
        else:
            self.total_adeudado_eq=abs(self.total_adeudado_org*self.busca_tasa())

    def busca_tasa(self):
        tasa=1
        """if self.currency_id.id==self.env.company.currency_id.id:
            busca=self.env['res.currency.rate'].search([('currency_id','=',2),('name','<=',self.invoice_date)],order='name asc')
            if busca:
                for det in busca:
                    tasa=det.inverse_company_rate
        else:
            if self.amount_total or self.amount_total!=0:
                tasa=self.amount_total_signed/self.amount_total"""
        tasa=self.os_currency_rate
        return tasa

    def _compute_taxes_group(self):
        ''' Helper to get the taxes grouped according their account.tax.group.
        This method is only used when printing the invoice.
        '''
        for move in self:
            lang_env = move.with_context(lang=move.partner_id.lang).env
            tax_lines = move.line_ids.filtered(lambda line: line.tax_line_id)
            tax_balance_multiplicator = -1 if move.is_inbound(True) else 1
            res = {}
            # There are as many tax line as there are repartition lines
            done_taxes = set()
            for line in tax_lines:
                res.setdefault(line.tax_line_id.tax_group_id, {'base': 0.0, 'amount': 0.0})
                ##res[line.tax_line_id.tax_group_id]['amount'] += tax_balance_multiplicator * (line.amount_currency if line.currency_id else line.balance)
                res[line.tax_line_id.tax_group_id]['amount'] += abs(line.balance)/self.busca_tasa() if self.currency_id.id==self.env.company.currency_id.id else abs(line.balance)
                tax_key_add_base = tuple(move._get_tax_key_for_group_add_base(line))
                if tax_key_add_base not in done_taxes:
                    if line.currency_id and line.company_currency_id and line.currency_id != line.company_currency_id:
                        amount = line.company_currency_id._convert(line.tax_base_amount, line.currency_id, line.company_id, line.date or fields.Date.context_today(self))
                    else:
                        amount = line.tax_base_amount
                    res[line.tax_line_id.tax_group_id]['base'] += amount
                    # The base should be added ONCE
                    done_taxes.add(tax_key_add_base)

            # At this point we only want to keep the taxes with a zero amount since they do not
            # generate a tax line.
            for line in move.line_ids:
                for tax in line.tax_ids.flatten_taxes_hierarchy():
                    if tax.tax_group_id not in res:
                        res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})
                        res[tax.tax_group_id]['base'] += tax_balance_multiplicator * (line.amount_currency if line.currency_id else line.balance)

            res = sorted(res.items(), key=lambda l: l[0].sequence)
            move.amount_by_group_eq = [(
                group.name, amounts['amount'],
                amounts['base'],
                formatLang(lang_env, amounts['amount']),
                formatLang(lang_env, amounts['base']),
                ##formatLang(lang_env, amounts['amount'], currency_obj=move.company_id.currency_id),
                ##formatLang(lang_env, amounts['base'], currency_obj=move.company_id.currency_id),
                len(res),
                group.id
            ) for group, amounts in res]
##################################################################
    def pago_igtf(self):
        return self.env['account.igtf.payment']\
            .with_context(active_ids=self.ids, active_model='account.move', active_id=self.id)\
            .action_register_igtf_payment()
##################################################################
    def _compute_exento(self):
        valor_exemto=valor_imponible=0
        for selff in self:
            for rec in selff.invoice_line_ids:
                if rec.tax_ids.amount==0:
                    valor_exemto=valor_exemto+rec.price_subtotal
                if rec.tax_ids.amount!=0:
                    valor_imponible=valor_imponible+rec.price_subtotal
            selff.amount_exento=valor_exemto
            selff.amount_imponible=valor_imponible

    def _compute_pago_div(self):
        valor=igtf=0
        for selff in self:
            if selff.igtf_ids:
                for rec in selff.igtf_ids:
                    if selff.currency_id.id==selff.env.company.currency_id.id:
                        valor=valor+round(rec.monto_base,1)
                        igtf=igtf+rec.monto_ret
                    else:
                        valor=valor+rec.monto_base_usd
                        igtf=igtf+rec.monto_ret/rec.tasa
            selff.pago_divisa=valor
            selff.impuesto_igtf=igtf

    def _compute_pago_bs(self):
        monto_bs=0
        self.pago_bs=abs(self.total_pagar-self.pago_divisa)-self.total_adeudado_org
        """if self.currency_id.id==self.env.company.currency_id.id:
            self.pago_bs=abs(self.total_pagar-self.pago_divisa)-self.total_adeudado_org #*self.busca_tasa()
        else:
            self.pago_bs=abs(self.amount_total-self.pago_divisa)-self.amount_residual"""

    def _compute_total_paga(self):
        self.total_pagar=self.amount_total+self.impuesto_igtf


    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(['debit', 'credit', 'move_id'])
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(debit - credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(debit - credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
            #raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))

    @api.constrains('amount_total')  #'amount_total',
    def asocia_asiento_igtf_factura_clie(self):
        #raise UserError(_('Enra aqui 1'))
        for selff in self:
            if selff.is_delivery_note!=True:
                if selff.sub_total_pagado=='False':
                    #raise UserError(_('Enra aqui 2'))
                ### CODIGO QUE LIMPIA INICIALMENTE EL CAMPO DONDE SE GUARDAS LOS ASIENTOS IGTF ASOCIADOS A LA FACT
                    for limpia_linea in selff.igtf_ids:
                        limpia_linea.unlink()
                         #raise UserError(_('Enra aqui 3'))
                    ### fin
                    cuenta_cli=selff.partner_id.property_account_receivable_id.id # cliente
                    cuenta_prov=selff.partner_id.property_account_payable_id.id # proveedor
                    if selff.move_type in ('out_invoice','out_refund'):
                        cuenta_gene=cuenta_cli
                    if selff.move_type in ('in_invoice','in_refund'):
                        cuenta_gene=cuenta_prov
                    # CLIENTES
                    if selff.move_type in ('out_invoice','out_refund','in_invoice','in_refund'):
                        for rec in selff.line_ids:
                            if rec.account_id.id==cuenta_gene:
                                id_move=rec.id
                        #raise UserError(_('cursor3=%s')%id_move)
                        if selff.state=='posted':
                            if selff.move_type in ('out_invoice','out_refund'):
                                cursor=selff.env['account.partial.reconcile'].search([('debit_move_id','=',id_move)])
                            if selff.move_type in ('in_invoice','in_refund'):
                                cursor=selff.env['account.partial.reconcile'].search([('credit_move_id','=',id_move)])
                        else:
                            cursor=""##selff.env['account.partial.reconcile'].search([('debit_move_id','=',0)])
                        if cursor:
                            for rec in cursor:
                                if selff.move_type in ('out_invoice','out_refund'):
                                    pago_move_id=rec.credit_move_id.move_id.payment_id
                                if selff.move_type in ('in_invoice','in_refund'):
                                    pago_move_id=rec.debit_move_id.move_id.payment_id
                                monto=pago_move_id.amount
                                #raise UserError(_('Entra 3=%s')%pago_move_id.id)
                                if pago_move_id.payment_method_id.calculate_wh_itf==True:
                                    #raise UserError(_('Entra 4'))
                                    if pago_move_id.currency_id.id!=self.company_currency_id.id:
                                        busca=selff.env['res.currency.rate'].search([('currency_id','=',2),('name','<=',pago_move_id.date)],order='name asc')
                                        if busca:
                                            for det in busca:
                                                tasa=det.inverse_company_rate
                                                if pago_move_id.currency_id.id!=self.env.company.currency_id.id:
                                                    monto_base=pago_move_id.amount*tasa
                                                    monto_base_usd=pago_move_id.amount
                                                else:
                                                    monto_base=pago_move_id.amount
                                                    monto_base_usd=pago_move_id.amount/tasa
                                    retencion=monto_base*pago_move_id.payment_method_id.wh_porcentage/100
                                    vols={
                                    'move_id':selff.id,
                                    'asiento_igtf':pago_move_id.asiento_cobro_igtf.id,
                                    'metodo_pago':pago_move_id.payment_method_id.id,
                                    'monto_base_usd':monto_base_usd,
                                    'tasa':tasa,
                                    'monto_base':monto_base,
                                    'porcentaje':pago_move_id.payment_method_id.wh_porcentage,
                                    'monto_ret':retencion,
                                    }
                                    verifica_asiento_igtf_fact=self.env['account.payment.igtf'].search([('asiento_igtf','=',pago_move_id.asiento_cobro_igtf.id)])
                                    #raise UserError(_('Entra 5'))
                                    if not verifica_asiento_igtf_fact:
                                        crear=selff.env['account.payment.igtf'].create(vols)
                                        selff.igtf_ids=selff.env['account.payment.igtf'].search([('move_id','=',selff.id)])
                                    #raise UserError(_('credit=%s')%pago_move_id)
                if selff.sub_total_pagado=='False':
                    selff.amount_residual=selff.amount_total-selff.valor_pagado()+selff.calculo_igtf()
                    if selff.currency_id.id==selff.env.company.currency_id.id:
                        selff.amount_residual_signed=selff.amount_residual
                    else:
                        selff.amount_residual_signed=selff.amount_residual*selff.tasa()
                                        
                    if selff.amount_residual>0:
                        selff.payment_state='partial'

    @api.constrains('amount_residual')  #amount_total
    def varifica(self):
        for item in self:
            if (item.amount_total-item.valor_pagado())==0 and item.payment_state=='partial':
                    item.sub_total_pagado='True'
            if (item.amount_total-item.valor_pagado())>0:
                item.sub_total_pagado='False'

    @api.constrains('payment_state')
    def act_adeudado(self):
        for selff in self:
            if selff.payment_state=='in_payment' or selff.payment_state=='paid':
                selff.amount_residual=0
                selff.amount_residual_signed=0
                selff.payment_state=='paid'
                #raise UserError(_('ANGEL SOJO2'))

    def tasa(self):
        #if self.custom_rate!=True:
        tasa=1
        busca=self.env['res.currency.rate'].search([('currency_id','=',2),('name','<=',self.invoice_date)],order='name asc')
        if busca:
            for det in busca:
                tasa=1/det.rate
        return tasa


    def calculo_igtf(self):
        valor=0
        for selff in self:
            if selff.igtf_ids:
                for det in selff.igtf_ids:
                    valor=valor+det.monto_ret
            if selff.currency_id.id!=selff.env.company.currency_id.id:
                    valor=valor/selff.tasa()
        return valor

    def valor_pagado(self):
        valor=0
        for selff in self: 
            #factura cliente
            if selff.move_type in ('out_invoice','out_refund'):
                busca=selff.env['account.move.line'].search([('move_id','=',selff.id),('account_id','=',selff.partner_id.property_account_receivable_id.id)])
                if busca:
                    for roc in busca:
                        line_id=roc.id
                        busca2=selff.env['account.partial.reconcile'].search([('debit_move_id','=',roc.id)])
                        if busca2:
                            for rec in busca2:
                                if selff.currency_id.id==selff.env.company.currency_id.id:
                                    valor=valor+rec.amount
                                else:
                                    valor=valor+rec.debit_amount_currency
            #factura proveedor
            if selff.move_type in ('in_invoice','in_refund'):
                busca=selff.env['account.move.line'].search([('move_id','=',selff.id),('account_id','=',selff.partner_id.property_account_payable_id.id)])
                if busca:
                    for roc in busca:
                        line_id=roc.id
                        busca2=selff.env['account.partial.reconcile'].search([('credit_move_id','=',roc.id)])
                        if busca2:
                            for rec in busca2:
                                if selff.currency_id.id==selff.env.company.currency_id.id:
                                    valor=valor+rec.amount
                                else:
                                    valor=valor+rec.credit_amount_currency
            #raise UserError(_('busca2=%s')%valor).
            return valor

class AccountMoveIgtf(models.Model):

    _name = 'account.payment.igtf'

    move_id = fields.Many2one('account.move')
    asiento_igtf = fields.Many2one('account.move')
    metodo_pago = fields.Many2one('account.payment.method')
    monto_base_usd = fields.Float()
    tasa = fields.Float()
    monto_base = fields.Float()
    porcentaje = fields.Float()
    monto_ret = fields.Float()