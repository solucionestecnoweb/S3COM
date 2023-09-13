# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from json import dumps

import ast
import json
import re
import warnings


class AccountMove(models.Model):
    _inherit = 'account.move'

    total_bs = fields.Float(compute='_compute_bs',store=True)
    total_divisas = fields.Float(compute='_compute_divisas',store=True)

    @api.depends(
        'amount_total_signed',
        'amount_untaxed_signed',
        'amount_residual_signed',
        'amount_tax_signed',
        'currency_id2',
        'os_currency_rate'
    )
    def _compute_bs(self):
        for selff in self:
            selff.total_bs=selff.amount_total_signed

    @api.depends(
        'amount_total_signed',
        'amount_untaxed_signed',
        'amount_residual_signed',
        'amount_tax_signed',
        'currency_id2',
        'os_currency_rate'
    )
    def _compute_divisas(self):
        for selff in self:
            if selff.currency_id==selff.company_id.currency_id:
                if selff.os_currency_rate!=0:
                    selff.total_divisas=selff.amount_total_signed/selff.os_currency_rate
                else:
                    selff.total_divisas=selff.amount_total_signed/1
            else:
                selff.total_divisas=selff.amount_total

    