# -*- coding: utf-8 -*-


import logging
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Register Payment'


    #def action_create_payments(self):
        #super().action_create_payments()
        #self.retencion_igtf()


    def retencion_igtf(self):
        retencion=0
        if self.payment_method_id:
            for rec in self.payment_method_id:
                if rec.calculate_wh_itf==True:
                    if self.currency_id.id==self.env.company.currency_id.id:
                        monto_base=self.amount
                        retencion=monto_base*rec.wh_porcentage/100
                        if rec.journal_transi.id:
                            diario_tempo=rec.journal_transi.id
                        else:
                            raise UserError(_('No existe diario transitorio del igtf para un modo de pago, favor vaya a la configuracion de modos de pagos y asignar una'))
                    else:
                        monto_base=self.amount*self.busca_tasa()
                        retencion=monto_base*rec.wh_porcentage/100
                        if rec.journal_transi.id:
                            diario_tempo=rec.journal_transi.id
                        else:
                            raise UserError(_('No existe diario transitorio del igtf para un modo de pago, favor vaya a la configuracion de modos de pagos y asignar una'))
                        #raise UserError(_('retencion=%s')%retencion)
                    if not rec.account_wh_itf_id:
                        raise UserError(_('En este Método de pago tiene habilitado para descuento del igtf, pero no tiene asociado una cuenta, favor vaya a la configuracion de modos de pagos y asignar una'))
                    else:  
                        #------------------- CON ESTO EVITO QUE SE DUPLIQUE LA SECUENCIA DEL PAGO DEL BANCO CON LO DEL IGTF 
                        """actualiza_pago=self.env['account.move'].search([('ref','=',self.communication)])
                        if actualiza_pago:
                            for act in actualiza_pago:
                                act.name=self.journal_id.code+"/"+self.communication"""
                                #ids_igtf=act.igtf_ids
                        #---------------------------------------------------------
                        busca_factura=self.env['account.move'].search([('name','=',self.communication)])
                        if busca_factura:
                            for det in busca_factura:
                                factura_id=det.id
                                ids_igtf=det.igtf_ids
                        secuencia=self.get_name_igtf_clie()
                        #raise UserError(_('secuencia=%s')%secuencia)
                        cuenta_igtf=rec.account_wh_itf_id
                        cuenta_otra=self.journal_id.payment_debit_account_id
                        #raise UserError(_('ceunta_otra=%s')%ceunta_otra.name)
                        id_move=self.registro_movimiento_asiento(retencion,secuencia,diario_tempo)
                        idv_move=id_move.id
                        valor=self.registro_movimiento_linea(idv_move,retencion,cuenta_igtf,cuenta_otra)
                        moves= self.env['account.move'].search([('id','=',idv_move)])
                        moves.action_post()
                        #raise UserError(_('ceunta_otra=%s')%factura_id)
                        vols={
                        'move_id':factura_id,
                        'asiento_igtf':moves.id,
                        'metodo_pago':rec.id,
                        'monto_base_usd':monto_base/self.busca_tasa(),
                        'tasa':self.busca_tasa(),
                        'monto_base':monto_base,
                        'porcentaje':rec.wh_porcentage,
                        'monto_ret':retencion,
                        }
                        ids_igtf=self.env['account.payment.igtf'].create(vols) 
                        ##moves.button_draft()
                        ##moves.journal_id=self.journal_id.id
                        ##moves.action_post()

    def registro_movimiento_asiento(self,amont_totall,secuencia,diario_tempo):
        #raise UserError(_('darrell = %s')%self.partner_id.vat_retention_rate)
        name = secuencia
        signed_amount_total=0
        signed_amount_total=amont_totall
        id_journal=self.journal_id.id#loca14
        #raise UserError(_('papa = %s')%signed_amount_total)
        value = {
            'name': name,
            'date': self.payment_date,#listo
            #'amount_total':self.vat_retentioned,# LISTO
            'partner_id': self.company_id.partner_id.id, #LISTO
            'journal_id':diario_tempo, #id_journal,
            'ref': "Pago de igtf %s" % (self.communication),
            #'amount_total':self.vat_retentioned,# LISTO
            'amount_total_signed':signed_amount_total,# LISTO
            'move_type': "entry",# estte campo es el que te deja cambiar y almacenar valores
            'company_id':self.env.company.id,#loca14
            'currency_id':3,
        }
        #raise UserError(_('value= %s')%value)
        move_obj = self.env['account.move']
        move_id = move_obj.create(value)    
        return move_id

    def registro_movimiento_linea(self,id_movv,retencion,cuenta_igtf,cuenta_otra):
        #raise UserError(_('ID MOVE = %s')%id_movv)
        name = "IGTF del doc: "+self.communication
        valores = retencion #self.conv_div_extranjera(self.vat_retentioned) #VALIDAR CONDICION
        #raise UserError(_('valores = %s')%valores)
        cero = 0.0
              
        ### para clientes
        if self.payment_type=="inbound":
            cuenta_haber=cuenta_igtf.id
            cuenta_debe=cuenta_otra.id

        ### para proveedores
        if self.payment_type=="outbound":
            cuenta_haber=cuenta_otra.id
            cuenta_debe=cuenta_igtf.id

        balances=cero-valores
        value = {
             'name': name,
             'ref' : "Pago de igtf de %s" % (self.communication),
             'move_id': int(id_movv),
             'date': self.payment_date,
             'partner_id': self.env.company.partner_id.id,
             'account_id': cuenta_haber,
             #'currency_id':self.invoice_id.currency_id.id,
             #'amount_currency': 0.0,
             #'date_maturity': False,
             'credit': valores,
             'debit': 0.0, # aqi va cero   EL DEBITO CUNDO TIENE VALOR, ES QUE EN ACCOUNT_MOVE TOMA UN VALOR
             'balance':-valores, # signo negativo
             'price_unit':balances,
             'price_subtotal':balances,
             'price_total':balances,
             'currency_id':self.currency_id.id if self.currency_id.id!=self.company_currency_id.id else "",
             'amount_currency': -1*self.amount if self.currency_id.id!=self.company_currency_id.id else "",

        }

        move_line_obj = self.env['account.move.line']
        move_line_id1 = move_line_obj.create(value)

        balances=valores-cero
        value['name'] = " "
        value['account_id'] = cuenta_debe
        value['credit'] = 0.0 # aqui va cero
        value['debit'] = valores
        value['balance'] = valores
        value['price_unit'] = balances
        value['price_subtotal'] = balances
        value['price_total'] = balances
        value['currency_id'] = self.currency_id.id if self.currency_id.id!=self.company_currency_id.id else ""
        value['amount_currency'] = self.amount if self.currency_id.id!=self.company_currency_id.id else ""

        move_line_id2 = move_line_obj.create(value)


    def busca_tasa(self):
        tasa=1
        busca=self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id),('name','<=',self.payment_date)],order='name asc')
        if busca:
            for det in busca:
                tasa=1/det.rate
        return tasa

    def get_name_igtf_clie(self):
        '''metodo que crea el Nombre del asiento contable si la secuencia no esta creada, crea una con el
        nombre: 'l10n_account_withholding_itf'''

        self.ensure_one()
        SEQUENCE_CODE = 'IGTF_CLI'
        company_id = self._get_company()
        IrSequence = self.env['ir.sequence'].with_context(force_company=company_id.id)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        # si aún no existe una secuencia para esta empresa, cree una
        if not name:
            IrSequence.sudo().create({
                'prefix': 'IGTF/Cliente/',
                'name': 'Impuesto ITF %s' % company_id.id,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 8,
                'number_increment': 1,
                'company_id': company_id.id,
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name

    @api.model
    def _get_company(self):
        '''Método que busca el id de la compañia'''
        company_id = self.env['res.users'].browse(self.env.uid).company_id
        return company_id
