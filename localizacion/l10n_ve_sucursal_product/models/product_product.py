# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal', domain="[('company_id', '=', company_id)]")
