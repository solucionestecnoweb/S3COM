# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_picking_type(self):
        return ''

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal')
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=Purchase.READONLY_STATES,
                                      required=True, default=_default_picking_type,
                                      domain="[(branch_office_id', '=', branch_office_id)]",
                                      help="This will determine operation type of incoming shipment")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        p_type = self.picking_type_id
        if not(p_type and p_type.code == 'incoming' and (p_type.branch_office_id == self.branch_office_id)):
            self.picking_type_id = p_type.branch_office_id.id


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    branch_office_id = fields.Many2one('res.sucursal', related='order_id.branch_office_id',
                                       string='Sucursal', store=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        if not self.account_analytic_id:
            analytic_obj = self.env['account.analytic.account'].search([
                ('branch_office_id', '=', self.branch_office_id.id)], limit=1)
            self.write({'account_analytic_id': analytic_obj.id})
        return res