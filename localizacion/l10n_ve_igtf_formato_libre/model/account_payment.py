# coding: utf-8
###########################################################################

import logging

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

#_logger = logging.getLogger(__name__)
class account_payment(models.Model):

    _inherit = 'account.payment'
    asiento_igtf_cliente=fields.Many2one('account.move')
    asiento_igtf_proveedor=fields.Many2one('account.move')
    asiento_cobro_igtf=fields.Many2one('account.move')
    asiento_prov_igtf_bank=fields.Many2one('account.move')

    def action_post(self):
        super().action_post()
        #self.igtf_provee_bank()
        self.retencion_igtf_divisas()

        

    def igtf_provee_bank(self):
        if self.payment_type=='outbound' and self.partner_type=="supplier":
            if self.journal_id.tipo_bank=="na" and self.journal_id.calculate_wh_itf==True:
                monto_base=self.amount
                if self.currency_id.id==self.env.company.currency_id.id:
                    monto_base=self.amount
                else:
                    monto_base=self.amount*self.busca_tasa()
                retencion=monto_base*self.journal_id.wh_porcentage/100
                diario_tempo=self.journal_id.journal_igtf_id.id
                cuenta_igtf=self.journal_id.account_wh_itf_id
                cuenta_otra=self.journal_id.payment_credit_account_id # Proveedores
                secuencia=self.get_name_igtf_clie()
                # cliente
                if self.payment_type=='inbound':
                    cuenta_otra=self.journal_id.payment_debit_account_id
                # Proveedores
                if self.payment_type=='outbound':
                    cuenta_otra=self.journal_id.payment_credit_account_id
                id_move=self.registro_movimiento_asiento_igtf(retencion,secuencia,diario_tempo)
                idv_move=id_move.id
                valor=self.registro_movimiento_linea_igtf(idv_move,retencion,cuenta_igtf,cuenta_otra)
                moves= self.env['account.move'].search([('id','=',idv_move)])
                moves.action_post()
                self.asiento_prov_igtf_bank=id_move



    def retencion_igtf_divisas(self):
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
                       
                        secuencia=self.get_name_igtf_clie()
                        #raise UserError(_('secuencia=%s')%secuencia)
                        cuenta_igtf=rec.account_wh_itf_id
                        # cliente
                        if self.payment_type=='inbound':
                            cuenta_otra=self.busca_cuenta_metodo(rec,self.journal_id,self.payment_type)#self.journal_id.payment_debit_account_id darrell
                        # Proveedores
                        if self.payment_type=='outbound':
                            cuenta_otra=self.busca_cuenta_metodo(rec,self.journal_id,self.payment_type)#self.journal_id.payment_credit_account_id
                        #raise UserError(_('ceunta_otra=%s')%cuenta_otra.name)
                        id_move=self.registro_movimiento_asiento_igtf(retencion,secuencia,diario_tempo)
                        idv_move=id_move.id
                        valor=self.registro_movimiento_linea_igtf(idv_move,retencion,cuenta_igtf,cuenta_otra)
                        moves= self.env['account.move'].search([('id','=',idv_move)])
                        #moves.action_post() # AQUI PUBLICO DE UNA VEZ
                        self.asiento_cobro_igtf=id_move
                        #raise UserError(_('ceunta_otra=%s')%factura_id)
                        
    def busca_cuenta_metodo(self,metodo,journal,type_payment):
        #valor=''
        if type_payment=='inbound':
            for det in journal.inbound_payment_method_line_ids:
                if det.payment_method_id.id==metodo.id:
                    valor=det.payment_account_id

        if type_payment=='outbound':
            for det in journal.outbound_payment_method_line_ids:
                if det.payment_method_id.id==metodo.id:
                    valor=det.payment_account_id
        if not valor:
            raise UserError(_('Falta configurar cuentas de recibos y de pago en los diarios para pagos en divisas. Vaya a estas pestañas del diario y configure'))
        return valor



    def registro_movimiento_asiento_igtf(self,amont_totall,secuencia,diario_tempo):
        #raise UserError(_('darrell = %s')%self.partner_id.vat_retention_rate)
        name = secuencia
        signed_amount_total=0
        signed_amount_total=amont_totall
        id_journal=self.journal_id.id#loca14
        #raise UserError(_('papa = %s')%signed_amount_total)
        value = {
            'name': name,
            'date': self.date, #self.payment_date,#listo
            #'amount_total':self.vat_retentioned,# LISTO
            'partner_id': self.company_id.partner_id.id, #LISTO
            'journal_id':diario_tempo, #id_journal,
            #'ref': "Pago de igtf %s" % (self.communication),
            #'amount_total':signed_amount_total,# LISTO
            'amount_total_signed':signed_amount_total,# LISTO
            'move_type': "entry",# estte campo es el que te deja cambiar y almacenar valores
            'company_id':self.env.company.id,#loca14
            'currency_id':3, #self.currency_id.id if self.currency_id.id!=self.company_currency_id.id else "",
        }
        #raise UserError(_('value= %s')%value)
        move_obj = self.env['account.move']
        move_id = move_obj.create(value)    
        return move_id

    def registro_movimiento_linea_igtf(self,id_movv,retencion,cuenta_igtf,cuenta_otra):
        #raise UserError(_('ID MOVE = %s')%id_movv)
        name = "IGTF del pago: "#+self.communication
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
             'ref' : "Pago de igtf ",
             'move_id': int(id_movv),
             'date': self.date,#self.payment_date,
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
        busca=self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id),('name','<=',self.date)],order='name asc')
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
                'prefix': 'IGTF/Divisas/',
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

    def action_draft(self):
        super().action_draft()
        self.asiento_cobro_igtf.filtered(lambda move: move.state == 'posted').button_draft()
        self.asiento_cobro_igtf.with_context(force_delete=True).unlink()
        self.asiento_prov_igtf_bank.filtered(lambda move: move.state == 'posted').button_draft()
        self.asiento_prov_igtf_bank.with_context(force_delete=True).unlink()