# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TaxUnit(models.Model):
    _name = 'tax.unit'
    _description = "Tax Unit"
    _rec_name = 'name'

    name = fields.Char(string='Reference Number', required=True, help='Gazette number')
    date = fields.Date(string='Date', required=True, help='Gazetter publication date')
    tax_unit_amount = fields.Float(string='Amount', required=True, digits='Bs per UT')

    @api.model
    def create(self, vals):
        res = super(TaxUnit, self).create(vals)
        concept = self.env['islr.rate'].search([])
        for item in concept:
            if item.subtract > 0.0:
                item.subtract = res.tax_unit_amount * 83.3334 * (item.retention_percentage / 100)
        return res