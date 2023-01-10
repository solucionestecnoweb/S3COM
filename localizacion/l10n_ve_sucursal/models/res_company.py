# -*- coding: utf-8 -*-

from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    currency_id2 = fields.Many2one('res.currency', string='Moneda Secundaria', default=lambda x: x.env.ref('base.USD'))
    doc_type = fields.Selection([('v', 'V'), ('e', 'E'), ('j', 'J'), ('g', 'G'), ('p', 'P'), ('c', 'C')],
                                required=True, default='j')
