# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal')
