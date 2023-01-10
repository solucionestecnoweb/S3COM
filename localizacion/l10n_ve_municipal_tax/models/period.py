# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
_logger = logging.getLogger('__name__')


class MunicipalPeriodMonth(models.Model):
    _name = 'municipal.period.month'
    _description = 'Periodo Municipal Mensual'

    name = fields.Char(string='Months')
    months_number = fields.Char(string='Number')


class MunicipalPeriodYear(models.Model):
    _name = 'municipal.period.year'
    _description = 'Periodo Municipal Anual'
    _rec_name = 'name'

    name = fields.Char(string='year')
