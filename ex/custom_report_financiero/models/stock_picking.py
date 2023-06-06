from odoo import api, fields, models




class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_devolution = fields.Boolean(string='Es Devolucion')
    flaw = fields.Char(string='Por desperfecto de Fabricacion')
    date_expiration = fields.Char(string='Por Fecha de Expiracion')
    other = fields.Char(string='Otros')



class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        new_picking, pick_type_id = super(StockReturnPicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        picking.write({'is_devolution': True})
        return new_picking, pick_type_id