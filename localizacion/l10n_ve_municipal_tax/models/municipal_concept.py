# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
_logger = logging.getLogger('__name__')


class MunicipalConcept(models.Model):
    _name = 'municipal.concept'
    _description = 'Concepto Municipal'

    name = fields.Char(string="Description", required=True)
    code = fields.Char(string='Activity code', required=True)
    aliquot = fields.Float(string='Aliquot', required=True)
    month_ucim = fields.Char(string='UCIM per month')
    year_ucim = fields.Char(string='UCIM per year')
