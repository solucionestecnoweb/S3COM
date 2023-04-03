# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.exceptions import Warning
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import datetime, timedelta



class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    date_actual = fields.Date(default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    act_nota_entre=fields.Boolean(default=False)
    correlativo_nota_entrega = fields.Char(required=False)
    doc_currency_id = fields.Many2one("res.currency", string="Moneda del documento Físico")


    def float_format(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result = "0,00"
        return result


    def action_post(self):
        super().action_post()
        if self.act_nota_entre==True:
            self.correlativo_nota_entrega=self.get_nro_nota_entrega()

    def get_nro_nota_entrega(self):
        '''metodo que crea el Nombre del asiento contable si la secuencia no esta creada, crea una con el
        nombre: 'l10n_ve_cuenta_retencion_iva'''

        self.ensure_one()
        SEQUENCE_CODE = 'l10n_ve_nro_control_nota_entrega'
        company_id = 1
        IrSequence = self.env['ir.sequence'].with_context(force_company=1)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        # si aún no existe una secuencia para esta empresa, cree una
        if not name:
            IrSequence.sudo().create({
                'prefix': '00-',
                'name': 'Localización Venezolana Nro control Nota entrega %s' % 1,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 4,
                'number_increment': 1,
                'company_id': 1,
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        #self.refuld_number_pro=name
        return name
    def formato_fecha(self,date):
        fecha = str(date)
        fecha_aux=fecha
        ano=fecha_aux[0:4]
        mes=fecha[5:7]
        dia=fecha[8:10]  
        resultado=dia+"/"+mes+"/"+ano
        return resultado

    def doc_cedula(self,aux):
            #nro_doc=self.partner_id.vat
            busca_partner = self.env['res.partner'].search([('id','=',aux)])
            for det in busca_partner:
                tipo_doc=busca_partner.doc_type
                if busca_partner.vat:
                    nro_doc=str(busca_partner.vat)
                else:
                    nro_doc="00000000"
                tipo_doc=busca_partner.doc_type
            nro_doc=nro_doc.replace('V','')
            nro_doc=nro_doc.replace('v','')
            nro_doc=nro_doc.replace('E','')
            nro_doc=nro_doc.replace('e','')
            nro_doc=nro_doc.replace('G','')
            nro_doc=nro_doc.replace('g','')
            nro_doc=nro_doc.replace('J','')
            nro_doc=nro_doc.replace('j','')
            nro_doc=nro_doc.replace('P','')
            nro_doc=nro_doc.replace('p','')
            nro_doc=nro_doc.replace('-','')
            
            if tipo_doc=="v":
                tipo_doc="V"
            if tipo_doc=="e":
                tipo_doc="E"
            if tipo_doc=="g":
                tipo_doc="G"
            if tipo_doc=="j":
                tipo_doc="J"
            if tipo_doc=="p":
                tipo_doc="P"
            resultado=str(tipo_doc)+"-"+str(nro_doc)
            return resultado

    def valida_iva(self,ret_iva_id):
        valor=0
        if ret_iva_id:
            valor=ret_iva_id.amount_total_retention_usd
        return valor

    def valida_islr(self,ret_islr_id):
        valor=0
        if ret_islr_id:
            valor=ret_islr_id.amount_total_retention_usd
        return valor

   


