# -*- coding: utf-8 -*-

from odoo import models, fields, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    vat_required = fields.Boolean(string='Cedula requerido')
    phone_required = fields.Boolean(string='Telefono requerido')
    street_required = fields.Boolean(string='Direccion requerido')
    customer_recepit_required = fields.Boolean(string='Cliente en recibo')
    customer_recepit_phone_required = fields.Boolean(string='Telefono en recibo')
    customer_recepit_vat_required = fields.Boolean(string='Cedula en recibo')
