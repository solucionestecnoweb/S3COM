from odoo import fields, models
class PosPaymentMeth(models.Model):
    _inherit = "pos.payment.method"

    """  
        no hago uso del campo 'split_transactions' nativo de odoo porque es usado
        para otro comportamiento en el sistema, el cual no necesariamente se desea
    """
    is_dollar_payment = fields.Boolean('Pago en divisa') 
