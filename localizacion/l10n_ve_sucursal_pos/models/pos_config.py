# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
_logger = logging.getLogger('__name__')


class PosConfig(models.Model):
    _inherit = 'pos.config'

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal', domain="[('company_id', '=', company_id)]")

