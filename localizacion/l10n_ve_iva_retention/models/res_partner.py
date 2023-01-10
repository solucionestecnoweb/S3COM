# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    retention_iva_rate = fields.Float(string='Tasa de Retencion')
    property_account_payable_vat_id = fields.Many2one('account.account', string="Account Payable",
                                                      company_dependent=True, domain="["
                                                      "('internal_type', '=', 'other')," "('deprecated', '=', False),"
                                                      "('company_id', '=', current_company_id)]",
                                                      help="This account will be used instead of"
                                                           "the default one as the payable account"
                                                           "for the current partner")
    property_account_receivable_vat_id = fields.Many2one('account.account', company_dependent=True,
                                                         string="Account Receivable",
                                                         domain="[""('internal_type', '=', 'other'),"
                                                                "('deprecated', '=', False),"
                                                                "('company_id', '=', current_company_id)]",
                                                         help="This account will be used instead of the default one as"
                                                              "the receivable account for the current partner")

    @api.model
    def _commercial_fields(self):
        return super(Partner, self)._commercial_fields() + \
            ['property_account_payable_vat_id', 'property_account_receivable_vat_id']
