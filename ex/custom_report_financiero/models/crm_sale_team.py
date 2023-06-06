from odoo import fields, models, api
from datetime import datetime, date

class CrmSaleTeam(models.Model):
    _inherit = 'crm.team'
    

    invoiced_target_bs = fields.Integer('Meta de facturacion en Bs', currency_field='currency_id_bs')

    currency_id_bs = fields.Many2one('res.currency', 'currency', compute='_compute_currency_bs')
    currency_id_usd = fields.Many2one('res.currency', 'currency', compute='_compute_currency_dollars')


    @api.depends()       
    def _compute_currency_dollars(self):
        currency = self.env['res.currency'].search([('id','=',2)])
        self.currency_id_usd = currency.id
        
    @api.depends()       
    def _compute_currency_bs(self):
        currency = self.env['res.currency'].search([('id','=',3)])
        self.currency_id_bs = currency.id
        
    @api.onchange('invoiced_target')
    def onchange_conversion_invoiced_target_bs(self):
        currency = self.env['res.currency'].search([('id','=',2)])
        for record in self:
            if currency:
                for c in currency:
                    record.invoiced_target_bs = record.invoiced_target * c.sell_rate

    @api.onchange('invoiced_target_bs')
    def onchange_conversion_invoiced_target_dollar(self):
        currency = self.env['res.currency'].search([('id','=',2)])
        for record in self:
            if currency:
                for c in currency:
                    record.invoiced_target = record.invoiced_target_bs / c.sell_rate



