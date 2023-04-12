# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        return self.env['stock.warehouse'].search([
            ('branch_office_id', '=', self.branch_office_id.id), ('company_id', '=', self.company_id.id)], limit=1)

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal', required=True,
                                       domain="[('company_id', '=', company_id)]")
    journal_id = fields.Many2one('account.journal', string="Diario de ventas",
                                 domain="[('branch_office_id', '=', branch_office_id), ('type', '=', 'sale')]",
                                 required=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True)

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['branch_office_id'] = self.branch_office_id.id
        res['journal_id'] = self.journal_id.id
        return res

    @api.onchange('branch_office_id', 'company_id')
    def _onchange_company_id(self):
        if self.branch_office_id:
            self.warehouse_id = self._default_warehouse_id()

    @api.onchange('user_id')
    def onchange_user_id(self):
        super().onchange_user_id()
        if self.state in ['draft', 'sent']:
            self.warehouse_id = self._default_warehouse_id()

    # @api.onchange('branch_office_id')
    # def onchange_account_analytic(self):
    #     if not self.analytic_account_id:
    #         analytic_obj = self.env['account.analytic.account'].search([
    #             ('branch_office_id', '=', self.branch_office_id.id)], limit=1)
    #         self.write({'analytic_account_id': analytic_obj.id})
