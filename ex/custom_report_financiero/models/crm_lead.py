from odoo import fields, models, api
from datetime import datetime, date

class CrmSaleTeam(models.Model):
    _inherit = 'crm.lead'
    
    expected_income_dollars = fields.Monetary(string='Ingreso esperado en dolares', currency_field='currency_id_usd')
    currency_id_usd = fields.Many2one('res.currency', 'currency', compute='_compute_currency_dollars')
    category_customer_ids = fields.Many2many(comodel_name='categ.customer.type', related="partner_id.category_customer_ids", string='Categoria de cliente')


    @api.depends()       
    def _compute_currency_dollars(self):
        currency = self.env['res.currency'].search([('id','=',2)])
        self.currency_id_usd = currency.id

    @api.onchange('expected_income_dollars')
    def onchange_conversion_expected_income_bs(self):
        currency = self.env['res.currency'].search([('id','=',2)])
        for record in self:
            if currency:
                for c in currency:
                    record.expected_revenue = record.expected_income_dollars * c.sell_rate

    @api.onchange('expected_revenue')
    def onchange_conversion_expected_income_dollar(self):
        currency = self.env['res.currency'].search([('id','=',2)])
        for record in self:
             if currency:
                for c in currency:
                    record.expected_income_dollars = record.expected_revenue / c.sell_rate
            
