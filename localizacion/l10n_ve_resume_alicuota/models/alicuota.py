# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
_logger = logging.getLogger('__name__')


class Alicuota(models.Model):
    _name = "alicuota"
    _description = 'Alicuota'

    move_id = fields.Many2one('account.move', string='Factura', store=True, copy=False)
    retention_iva_id = fields.Many2one('retention.iva', string='Retencion IVA', copy=False)
    move_type = fields.Selection(related='move_id.move_type', store=True, readonly=True)
    state = fields.Selection(related='move_id.state', store=True, readonly=True)
    currency_id = fields.Many2one(related='move_id.currency_id', store=True, readonly=True)
    partner_id = fields.Many2one(related='move_id.partner_id', store=True, readonly=True, invisible=True)
    vat = fields.Char(related='partner_id.vat', store=True, readonly=True, invisible=True)
    partner_name = fields.Char(related='partner_id.name', store=True, readonly=True, invisible=True)
    doc_type = fields.Selection(related='partner_id.doc_type', store=True, readonly=True, invisible=True)
    invoice_number_next = fields.Char(related='move_id.invoice_number_next', store=True, readonly=True, invisible=True)
    invoice_number_control = fields.Char(related='move_id.invoice_number_control', store=True, readonly=True,
                                         invisible=True)
    invoice_number_unique = fields.Char(related='move_id.invoice_number_unique', store=True, readonly=True,
                                        invisible=True)
    retention_iva_state = fields.Selection(related='retention_iva_id.state', store=True, readonly=True)
    retention_iva_name = fields.Char(related='retention_iva_id.name', string='Nro. Comprobante',
                                     store=True, readonly=True)

    ali_general = fields.Float(string='Alicuota General')
    ali_reduced = fields.Float(string='Alicuota Reducida')
    ali_additional = fields.Float(string='Alicuota General/Reducida')

    detained_general = fields.Float(string='Retenido General')
    detained_reduced = fields.Float(string='Retenido Reducida')
    detained_additional = fields.Float(string='Retenido General/Reducida')

    tax_ids = fields.Many2many('account.tax', string='Impuestos')
    total_exempt = fields.Float(string='Total Excento')
    base_additional = fields.Float(string='Total Base General + Reducida')
    base_general = fields.Float(string='Total Base General')
    base_reduced = fields.Float(string='Total Base Reducida')
    total_amount_iva = fields.Float(string='Total con IVA')
    total_valor_iva = fields.Float(string='Total IVA')
    total_ret_iva = fields.Float(string='Total IVA Retenido')
    total_base = fields.Float(string='Total Base Imponible')
    percentage_ret = fields.Float(string='Porcentaje de Retencion IVA')

    type_doc = fields.Char(string='Tipo de Documento')
    date_invoice = fields.Date(string='Fecha de Factura')
    date_voucher = fields.Date(related='retention_iva_id.iva_date', string='Fecha de Comprobante',
                               store=True, readonly=True)
