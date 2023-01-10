# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        return ''
    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal', required=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True)

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['branch_office_id'] = self.branch_office_id.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            return ''
            # warehouse_id = self.env['ir.default'].get_model_defaults('sale.order').get('warehouse_id')
            # elf.warehouse_id = warehouse_id or self.user_id.with_company(self.company_id.id)._get_default_warehouse_id().id

    @api.onchange('user_id')
    def onchange_user_id(self):
        super().onchange_user_id()
        if self.state in ['draft', 'sent']:
            return ''

    @api.onchange('branch_office_id')
    def onchange_account_analytic(self):
        if not self.analytic_account_id:
            analytic_obj = self.env['account.analytic.account'].search([
                ('branch_office_id', '=', self.branch_office_id.id)], limit=1)
            self.write({'analytic_account_id': analytic_obj.id})
