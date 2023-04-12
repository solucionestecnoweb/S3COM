# -*- coding: utf-8 -*-

from odoo import fields, models, api


class Users(models.Model):
    _inherit = 'res.users'

    branch_office_ids = fields.Many2many(
        'res.sucursal', 'res_sucursal_security_users_rel', 'user_id', 'branch_office_id', string="Sucursales",
        default=lambda self: self.env['res.sucursal'].search([('company_id', 'in', self.company_ids)]))
    branch_offices_count = fields.Integer(compute='_compute_branch_offices_count', string="Numeros de Sucursales")

    def _compute_branch_offices_count(self):
        self.branch_offices_count = self.env['res.sucursal'].sudo().search_count([])
