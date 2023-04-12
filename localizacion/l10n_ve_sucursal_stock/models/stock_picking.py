# -*- coding: utf-8 -*-

from odoo import fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    branch_office_id = fields.Many2one(related='warehouse_id.branch_office_id',
                                       string='Sucursal', store=True)


class Picking(models.Model):
    _inherit = "stock.picking"

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal', domain="[('company_id', '=', company_id)]")
