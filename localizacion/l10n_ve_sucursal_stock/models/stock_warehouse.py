# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal', domain="[('company_id', '=', company_id)]")

    @api.model
    def create(self, vals):
        res = super(Warehouse, self).create(vals)
        if res.branch_office_id:
            res.view_location_id.branch_office_id = res.branch_office_id
            res.lot_stock_id.branch_office_id = res.branch_office_id
            res.wh_input_stock_loc_id.branch_office_id = res.branch_office_id
            res.wh_qc_stock_loc_id.branch_office_id = res.branch_office_id
            res.wh_output_stock_loc_id.branch_office_id = res.branch_office_id
            res.wh_pack_stock_loc_id.branch_office_id = res.branch_office_id
        return res

    def write(self, vals):
        res = super(Warehouse, self).write(vals)
        if 'branch_office_id' in vals:
            self.view_location_id.branch_office_id = vals.get('branch_office_id', False)
            self.lot_stock_id.branch_office_id = vals.get('branch_office_id', False)
            self.wh_input_stock_loc_id.branch_office_id = vals.get('branch_office_id', False)
            self.wh_qc_stock_loc_id.branch_office_id = vals.get('branch_office_id', False)
            self.wh_output_stock_loc_id.branch_office_id = vals.get('branch_office_id', False)
            self.wh_pack_stock_loc_id.branch_office_id = vals.get('branch_office_id', False)
        return res
