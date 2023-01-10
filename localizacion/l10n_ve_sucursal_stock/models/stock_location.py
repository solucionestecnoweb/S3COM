# -*- coding: utf-8 -*-
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class Location(models.Model):
    _inherit = 'stock.location'

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal')