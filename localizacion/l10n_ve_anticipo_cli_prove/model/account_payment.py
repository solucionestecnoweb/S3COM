# coding: utf-8
###########################################################################

import logging

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.exceptions import Warning

#_logger = logging.getLogger(__name__)

class account_payment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'
    #name =fields.Char(compute='_valor_anticipo')

    #Este campo es para el modulo IGTF
    move_itf_id = fields.Many2one('account.move', 'Asiento contable')

    #Estos Campos son para el modulo de anticipo
    tipo = fields.Char()
    anticipo = fields.Boolean(defaul=False)
    usado = fields.Boolean(defaul=False)
    anticipo_move_id = fields.Many2one('account.move', 'Id de Movimiento de anticipo donde pertenece dicho pago')
    saldo_disponible = fields.Monetary(string='Saldo Disponible') # valor en bs/$
    saldo_disponible_signed = fields.Float() # valor solo en bs #fields.Float(compute='_compute_saldo')
    move_id = fields.Many2one('account.move', 'Id de Movimiento o factura donde pertenece dicho pago')

    #line_account_move = fields.Many2many('account.move.payment','payment_id', compute='_compute_documentos')
    line_account_move = fields.Many2many('account.move.payment')
    line_account_move_aux = fields.Char(compute='_compute_documentos')
    
    #invoice_ids = fields.Many2many('account.move') ##temporal
    #payment_difference = fields.Float() ## temporal

    def _compute_documentos(self):
        #raise UserError(_('fact_org_id '))
        self.env['account.move.payment'].search([]).unlink()
        asiento_pago_id=self.move_id.id
        if self.anticipo!=True:
            move_line=self.env['account.move.line'].search([('move_id','=',asiento_pago_id),('matching_number','=','P')])
            if move_line:
                for m_line in move_line:
                    fact_id=m_line.id
                ######## si es pago de clientes
                if self.payment_type=='inbound':
                    conciliacion=self.env['account.partial.reconcile'].search([('credit_move_id','=',fact_id)])
                    if conciliacion:
                        for det in conciliacion:
                            ref_id=det.debit_move_id
                        conciliacion2=self.env['account.partial.reconcile'].search([('debit_move_id','=',ref_id.id)])
                        if conciliacion2:
                            for rec in conciliacion2:
                                rec.credit_move_id.move_id.id
                                valor=({
                                    'move_id':rec.credit_move_id.move_id.id,
                                    'payment_id':self.id,
                                    'monto':-1*rec.credit_move_id.move_id.amount_total_signed/rec.credit_move_id.move_id.os_currency_rate,
                                    })
                                self.env['account.move.payment'].create(valor)
                            conte=({
                                'move_id':ref_id.move_id.id,
                                'payment_id':self.id,
                                'monto':abs(ref_id.move_id.amount_total_signed/ref_id.move_id.os_currency_rate),
                                })
                            self.env['account.move.payment'].create(conte)

                ######## si es pago de proveedores
                if self.payment_type=='outbound':
                    conciliacion=self.env['account.partial.reconcile'].search([('debit_move_id','=',fact_id)])
                    if conciliacion:
                        for det in conciliacion:
                            ref_id=det.credit_move_id
                        conciliacion2=self.env['account.partial.reconcile'].search([('credit_move_id','=',ref_id.id)])
                        if conciliacion2:
                            for rec in conciliacion2:
                                rec.debit_move_id.move_id.id
                                valor=({
                                    'move_id':rec.debit_move_id.move_id.id,
                                    'payment_id':self.id,
                                    'monto':-1*rec.debit_move_id.move_id.amount_total_signed/rec.debit_move_id.move_id.os_currency_rate,
                                    })
                                self.env['account.move.payment'].create(valor)
                            conte=({
                                'move_id':ref_id.move_id.id,
                                'payment_id':self.id,
                                'monto':abs(ref_id.move_id.amount_total_signed/ref_id.move_id.os_currency_rate)
                                })
                            self.env['account.move.payment'].create(conte)

        else:
            busca_anti_fact=self.env['account.payment.anticipo'].search([('payment_id','=',self.id),('confirmado','=','si')])
            if busca_anti_fact:
                for item in busca_anti_fact:
                    fact_org_id=item.move_id.id
                #raise UserError(_('fact_org_id = %s')%fact_org_id)
                busca_line_move=self.env['account.move.line'].search([('move_id','=',fact_org_id),('matching_number','=','P')])
                if busca_line_move:
                    for roc in busca_line_move:
                        fact_id=roc.id
                    #raise UserError(_('fact_id = %s')%fact_id)
                ######## si es pago de clientes
                if self.payment_type=='inbound':
                    conciliacion=self.env['account.partial.reconcile'].search([('debit_move_id','=',fact_id)])
                    if conciliacion:
                        for det in conciliacion:
                            ref_id=det.debit_move_id
                        conciliacion2=self.env['account.partial.reconcile'].search([('debit_move_id','=',ref_id.id)])
                        if conciliacion2:
                            for rec in conciliacion2:
                                valor=({
                                    'move_id':rec.credit_move_id.move_id.id,
                                    'payment_id':self.id,
                                    'monto':-1*rec.credit_move_id.move_id.amount_total_signed/rec.credit_move_id.move_id.os_currency_rate,
                                    })
                                self.env['account.move.payment'].create(valor)
                            conte=({
                                'move_id':ref_id.move_id.id,
                                'payment_id':self.id,
                                'monto':abs(ref_id.move_id.amount_total_signed/ref_id.move_id.os_currency_rate),
                                })
                            self.env['account.move.payment'].create(conte)

                ######## si es pago de proveedor
                if self.payment_type=='outbound':
                    conciliacion=self.env['account.partial.reconcile'].search([('credit_move_id','=',fact_id)])
                    if conciliacion:
                        for det in conciliacion:
                            ref_id=det.credit_move_id
                        conciliacion2=self.env['account.partial.reconcile'].search([('credit_move_id','=',ref_id.id)])
                        if conciliacion2:
                            for rec in conciliacion2:
                                valor=({
                                    'move_id':rec.debit_move_id.move_id.id,
                                    'payment_id':self.id,
                                    'monto':-1*rec.debit_move_id.move_id.amount_total_signed/rec.debit_move_id.move_id.os_currency_rate,
                                    })
                                self.env['account.move.payment'].create(valor)
                            conte=({
                                'move_id':ref_id.move_id.id,
                                'payment_id':self.id,
                                'monto':abs(ref_id.move_id.amount_total_signed/ref_id.move_id.os_currency_rate),
                                })
                            self.env['account.move.payment'].create(conte)

        self.line_account_move=self.env['account.move.payment'].search([])
        self.line_account_move_aux='a'



    """def _compute_saldo(self):
        for selff in self:
            if selff.currency_id.id!=self.env.company.currency_id.id:
                selff.saldo_disponible_signed=selff.saldo_disponible*selff.rate
            else:
                selff.saldo_disponible_signed=selff.saldo_disponible"""

    def _valor_anticipo(self):
        nombre=self.name
        saldo=self.saldo_disponible
        self.name=nombre
    
    def float_format_anti(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result
        

    def action_post(self):
        super().action_post()
        for selff in self:
            pago_id=selff.id
            selff.direccionar_cuenta_anticipo(pago_id)


    def direccionar_cuenta_anticipo(self,id_pago):
        cuenta_anti_cliente = self.partner_id.account_anti_receivable_id.id
        cuenta_anti_proveedor = self.partner_id.account_anti_payable_id.id
        cuenta_cobrar = self.partner_id.property_account_receivable_id.id
        cuenta_pagar = self.partner_id.property_account_payable_id.id
        anticipo = self.anticipo
        tipo_persona = self.partner_type
        tipo_pago = self.payment_type
        #raise UserError(_('tipo_persona = %s')%tipo_persona)
        if anticipo==True:
            if tipo_persona=="supplier":
                tipoo='in_invoice'
            if tipo_persona=="customer":
                tipoo='out_invoice'
            self.tipo=tipoo
            if not cuenta_anti_proveedor:
                raise UserError(_('Esta Empresa no tiene asociado una cuenta de anticipo para proveedores/clientes. Vaya al modelo res.partner, pestaña contabilidad y configure'))
            if not cuenta_anti_cliente:
                raise UserError(_('Esta Empresa no tiene asociado una cuenta de anticipo para proveedores/clientes. Vaya al modelo res.partner, pestaña contabilidad y configure'))
            if cuenta_anti_cliente and cuenta_anti_proveedor:
                if tipo_persona=="supplier":
                    cursor_move_line = self.env['account.move.line'].search([('payment_id','=',self.id),('account_id','=',cuenta_pagar)])
                    for det_cursor in cursor_move_line:
                        self.env['account.move.line'].browse(det_cursor.id).write({
                            'account_id':cuenta_anti_proveedor,
                            })
                    #raise UserError(_('cuenta id = %s')%cursor_move_line.account_id.id)
                if tipo_persona=="customer":
                    cursor_move_line = self.env['account.move.line'].search([('payment_id','=',self.id),('account_id','=',cuenta_cobrar)])
                    for det_cursor in cursor_move_line:
                        self.env['account.move.line'].browse(det_cursor.id).write({
                            'account_id':cuenta_anti_cliente,
                            })
                    #raise UserError(_('cuenta id = %s')%cursor_move_line.account_id.id)
                self.saldo_disponible=self.amount
                self.saldo_disponible_signed=self.amount if self.currency_id.id==self.env.company.currency_id.id else self.amount*self.os_currency_rate
        else:
            return 0


class account_move_payment(models.Model):
    _name = 'account.move.payment'

    payment_id = fields.Many2one('account.payment')
    move_id = fields.Many2one('account.move')
    monto = fields.Float()

    def float_format_anti(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result

