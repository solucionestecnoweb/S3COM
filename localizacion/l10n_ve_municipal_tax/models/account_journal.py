# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
_logger = logging.getLogger('__name__')


class AccountJournal(models.Model):
    _inherit = "account.journal"

    type = fields.Selection(selection_add=[('mun_tax', 'Retention Municipal')],
                            ondelete={"mun_tax": "cascade"})
