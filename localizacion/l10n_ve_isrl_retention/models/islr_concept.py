# -*- coding: utf-8 -*-
from odoo import fields, models


class IsrlConcepts(models.Model):
    _name = 'islr.concept'
    _description = " Isrl concept"
    _rec_name = 'name'

    name = fields.Char(string='Retention concept', required=True,
                       help="Name of Retention Concept, Example: Profesional fees")
    is_retention = fields.Boolean(string='Withhold', default=True,
                                  help="Check if the concept  withholding is withheld or not.")
    property_account_payable_isrl_id = fields.Many2one('account.account', string="Account Payable Retention",)
    rate_ids = fields.One2many('islr.rate', 'concept_id', 'Rate', help="Retention Concept rate")
