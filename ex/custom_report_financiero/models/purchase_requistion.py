from odoo import fields, models

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'
    
    categ_supplier_type = fields.Many2many('res.partner.category', string="Categoria del proveedor")
    is_guarantee = fields.Selection(string='Garantia', selection=[('1', 'si'), ('0', 'No')], default='0')

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition.line'
        
    guarantee = fields.Char(string='Garantías')

