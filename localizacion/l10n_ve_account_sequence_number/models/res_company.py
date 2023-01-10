# -*- coding: utf-8 -*-

from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_control_unique = fields.Boolean('Numero de Control Unico')
