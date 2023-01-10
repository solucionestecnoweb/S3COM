# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal')
