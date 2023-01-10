# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
_logger = logging.getLogger('__name__')


class AccountJournal(models.Model):
    _inherit = "account.journal"

    inv_sequence_id = fields.Many2one('ir.sequence', string='Secuencia Nro Documento', copy=False)
    ctrl_sequence_id = fields.Many2one('ir.sequence', string='Secuencia Nro Control', copy=False)
    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal')
