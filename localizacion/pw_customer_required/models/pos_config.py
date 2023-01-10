# -*- coding: utf-8 -*-

from odoo import models, fields, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    customer_required = fields.Boolean(string='Cliente requerido')
