from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    branch_office_id = fields.Many2one('res.sucursal', string='Sucursal', domain="[('company_id', '=', company_id)]")

    def _prepare_variant_values(self, combination):
        res = super(ProductTemplate, self)._prepare_variant_values(combination)
        res.update({
            'branch_office_id': self.branch_office_id.id
        })
        return res
