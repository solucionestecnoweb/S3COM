# -*- coding: utf-8 -*-

from odoo import fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    branch_office_id = fields.Many2one(related='default_location_dest_id.branch_office_id',
                                       string='Sucursal', store=True)
