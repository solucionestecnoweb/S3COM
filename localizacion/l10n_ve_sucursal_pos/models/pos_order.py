# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
_logger = logging.getLogger('__name__')


class PosOrder(models.Model):
    _inherit = "pos.order"

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal', domain="[('company_id', '=', company_id)]",
                                       readpnly=True)

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({'branch_office_id': res.session_id.config_id.branch_office_id})
        return res
