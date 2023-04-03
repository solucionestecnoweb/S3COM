# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.exceptions import Warning
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import datetime, timedelta



class AccountMove(models.Model):
    _inherit = 'res.partner'

    vat = fields.Char(required=True)
    


    