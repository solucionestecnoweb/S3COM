from odoo import api, fields, models, _
import json
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang, get_lang, format_amount


    

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    state = fields.Selection([
        ('draft', 'Petición presupuesto'),
        ('reprocura', 'Reprocura'),
        ('sent', 'Solicitud de presupuesto enviada'),
        ('to approve', 'Para aprobar'),
        ('purchase', 'Pedido de venta'),
        ('done', 'Bloqueado'),
        ('cancel', 'Cancelado')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)


    
    def copy(self, default=None):
        ctx = dict(self.env.context)
        ctx.pop('default_product_id', None)
        self = self.with_context(ctx)
        new_po = super(PurchaseOrder, self).copy(default=default)
        new_po.origin = self.origin

        for line in new_po.order_line:
            if line.product_id:
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id, quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(), uom_id=line.product_uom)
                line.date_planned = line._get_date_planned(seller)

        return new_po

    
    @api.depends('line_ids.price_total')
    def _amount_all_line_ids(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.line_ids:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'amount_untaxed_line_ids': currency.round(amount_untaxed),
                'amount_tax_line_ids': currency.round(amount_tax),
                'amount_total_line_ids': amount_untaxed + amount_tax,
        })


    line_ids = fields.One2many('pre.purchase.line', 'purchase_id', string='Lineas')
    tax_totals_json_line_ids = fields.Char(compute='_compute_tax_totals_json_line_ids')
    amount_tax_line_ids = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all_line_ids')
    amount_total_line_ids = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all_line_ids')
    amount_untaxed_line_ids = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all_line_ids', tracking=True)
    offer_validity = fields.Char(string='Validez de la Oferta')
    payment_method = fields.Char(string='Metodo de pago')
    place_delivery = fields.Char(string='Lugar de Entrega')
    offer_received = fields.Boolean(string='Oferta recibida')
    is_reprocura = fields.Boolean(string='Reprocura')
    crog_payments_ids = fields.One2many(comodel_name='purchase.order.imports.payment', inverse_name='purchase_id', string='Cronograma de Pagos de Importaciones')
    ci_payments_ids = fields.One2many(comodel_name='purchase.order.imports.importations', inverse_name='purchase_id', string='Ciclo de Importaciones')
    
  
    
    
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'reprocura', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def button_draft(self):
        if self.is_reprocura:
            self.write({'state': 'reprocura'})
        else:
            self.write({'state': 'draft'})
        return {}

    
    def button_cancel(self):
        ret = super(PurchaseOrder, self).button_cancel()
        for record in self:
            record.is_reprocura = True
        return ret

    @api.depends('line_ids.taxes_id', 'line_ids.price_subtotal', 'amount_total_line_ids', 'amount_untaxed_line_ids')
    def  _compute_tax_totals_json_line_ids(self):
        def compute_taxes(line_ids):
            return line_ids.taxes_id._origin.compute_all(**line_ids._prepare_compute_all_values())

        account_move = self.env['account.move']
        currency = self.env['res.currency'].search([('id','=',2)])

        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.line_ids, compute_taxes)
            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total_line_ids, order.amount_untaxed_line_ids, currency)
            order.tax_totals_json_line_ids = json.dumps(tax_totals)

    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.purchase_type == 'national':
                template_id = ir_model_data._xmlid_lookup('custom_report_financiero.email_template_edi_pre')[2]
            else:
                template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase')[2]
           
     
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
   


class PreRequsition(models.Model):
    _name = "pre.requisition"

class PreRequsitionLine(models.Model):
    _name = "pre.purchase.line"

    purchase_id = fields.Many2one(comodel_name='purchase.order', string='pedido')
    product_id = fields.Many2one('product.product', string='Item')
    name = fields.Char('Descripcion Solicitada')
    name_offer = fields.Char('Descripcion Ofertada')
    brand = fields.Char(string='Marca')
    product_uom_id = fields.Many2one('uom.uom', string='Unidad de medida')
    product_qty = fields.Float(string='Cantidad')
    price_unit = fields.Float(string='Precio Unitario')

    taxes_id = fields.Many2many('account.tax', string='Impuestos')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
        compute='_compute_currency_dollars')
    warranty = fields.Char(string='Garantia')
    delivery_time = fields.Date(string='Tiempo de Entrega')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)

 
    @api.depends()       
    def _compute_currency_dollars(self):
        currency = self.env['res.currency'].search([('id','=',2)])
        for record in self:

            record.currency_id = currency.id


    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(**line._prepare_compute_all_values())
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency': self.purchase_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.purchase_id.partner_id,
        }

   
    


class PurchaseOrderImportsPayment(models.Model):
    _inherit = "purchase.order.imports.payment"
        



    purchase_id = fields.Many2one(comodel_name='purchase.order', string='compra')


    @api.onchange('name')
    def _onchange_name(self): 
        for line in self.purchase_id.order_line:
            brand = [record.import_brand  for record in self.purchase_id.crog_payments_ids]
            self.name = self.purchase_id.partner_id.id
            if line.product_id.marca_comercial.name not in brand and not self.import_brand:
                self.import_brand = line.product_id.marca_comercial.name or False

        


class PurchaseOrderImportations(models.Model):
    _inherit = "purchase.order.imports.importations"
        
    purchase_id = fields.Many2one(comodel_name='purchase.order', string='compra')


    @api.onchange('name')
    def _onchange_name(self): 
        for line in self.purchase_id.order_line:
            brand = [record.importation_brand  for record in self.purchase_id.ci_payments_ids]
            self.name = self.purchase_id.partner_id.id
            if line.product_id.marca_comercial.name not in brand and not self.importation_brand:
                self.importation_brand = line.product_id.marca_comercial.name or False
    

class PurchaseComparedPricesLines(models.Model):
    _inherit = 'purchase.compared.prices.lines'

    delivery_time = fields.Date(string='tiempo de entrega')


class PurchaseCompareMultiple(models.Model):
    _inherit = 'purchase.compare.multiple'

    
    def compare_price(self):
        for selff in self:
            if len(selff.purchase_order_ids) != 3:
                raise ValidationError(_("There must be three records in the purchase orders to be able to compare"))
            else:
                t = selff.env['purchase.compared.prices.lines']
                t.search([]).unlink()
                for item in selff.purchase_order_ids: #Inicia el ciclo para comparar precios
                    for line in item.order_line: #Ubica en las lineas de productos
                       
                        values = {
                            'product_id': line.product_id.id,
                            'provider_id': item.partner_id.id,
                            'qty': line.product_qty,
                            'currency_id': line.currency_id.id,
                            'rate': item.rate,
                          
                        }
                        if item.line_ids:
                            for itemm in item.line_ids:
                                #aux=item.line_ids.filtered(lambda r: r.product_id == line.product_id).delivery_time
                                #raise UserError(_("prueba1=%s")%aux)
                                values['delivery_time'] = itemm.filtered(lambda r: r.product_id == line.product_id).delivery_time
                                values['price'] = itemm.filtered(lambda r: r.product_id == line.product_id).price_unit
                            t.create(values)
                selff._compare_lines()




    def _compare_lines(self):
        self.env['purchase.compared.prices'].search([('purchase_compare_multiple_id', '=', self.id)]).unlink()
        xfind = self.env['purchase.compared.prices.lines'].search([])

        provider_l = 0
        qtyl = 0
        delivery_time1 = False
        price_l = 0
        currency_l = 0
        rate_l = 0

        provider_m = 0
        qtym = 0
        delivery_time2 = False
        price_m = 0
        currency_m = 0
        rate_m = 0

        provider_h = 0
        qtyh = 0
        delivery_time3 = False
        price_h = 0
        currency_h = 0
        rate_h = 0

        product_temporal = ''

        for item in xfind.sorted(key=lambda a: a.product_id.id): #Recorremos las lineas y asignamos valor a las variables
            #Evaluación de Registro de Lineas

            provider_l = 0
            price_l = 0
            currency_l = 0
            provider_m = 0
            price_m = 0
            currency_m = 0
            provider_h = 0
            price_h = 0
            currency_h = 0

            temp_currency = 0
            temp_price1 = 0
            temp_price2 = 0
            temp_price3 = 0
            temp_price4 = 0
            if product_temporal != item.product_id.id: #Aseguramos si cambio de producto
                product_temporal = item.product_id.id #Asignamos nuevo producto

                pfind = self.env['purchase.compared.prices.lines'].search([('product_id', '=', product_temporal)])
                
                for line in pfind:
                    if line.currency_id.id == 3:
                        if line.currency_id.id == currency_l or currency_l == 0:
                            temp_price1 = line.price
                        else:
                            temp_price2 = line.price / line.rate
                    else:
                        if line.currency_id.id == currency_l or currency_l == 0:
                            temp_price1 = line.price
                        else:
                            temp_price2 = line.price * line.rate

                    if line.currency_id.id == 3:
                        if line.currency_id.id == currency_h or currency_h == 0:
                            temp_price3 = line.price
                        else:
                            temp_price4 = line.price / line.rate
                    else:
                        if line.currency_id.id == currency_h or currency_h == 0:
                            temp_price3 = line.price
                        else:
                            temp_price4 = line.price * line.rate
                    

                    #Comparativa de precios
                    
                    if currency_l == 3:
                        if temp_price1 == price_l and temp_price3 == price_h:
                            price_h = line.price
                            provider_h = line.provider_id.id
                            qtyh = line.qty
                            delivery_time3 = line.delivery_time
                            currency_h = line.currency_id.id
                            rate_h = line.rate                            
                    else:
                        if temp_price2 == price_l and temp_price4 == price_h:
                            price_h = line.price
                            provider_h = line.provider_id.id
                            qtyh = line.qty
                            delivery_time3 = line.delivery_time
                            currency_h = line.currency_id.id
                            rate_h = line.rate


                    if currency_l == line.currency_id.id or currency_l == 0:
                        if temp_price1 < price_l or price_l == 0:
                            price_l = line.price
                            provider_l = line.provider_id.id
                            qtyl = line.qty
                            delivery_time1 = line.delivery_time
                            currency_l = line.currency_id.id
                            rate_l = line.rate
                    else:
                        if temp_price2 < price_l or price_l == 0:
                            price_l = line.price
                            provider_l = line.provider_id.id
                            qtyl = line.qty
                            delivery_time1 = line.delivery_time
                            currency_l = line.currency_id.id
                            rate_l = line.rate

                    if currency_h == line.currency_id.id or currency_h == 0:
                        if temp_price3 > price_h or price_h == 0:
                            price_h = line.price
                            provider_h = line.provider_id.id
                            qtyh = line.qty
                            delivery_time3 = line.delivery_time
                            currency_h = line.currency_id.id
                            rate_h = line.rate
                    else:
                        if temp_price4 > price_h or price_h == 0:
                            price_h = line.price
                            provider_h = line.provider_id.id
                            qtyh = line.qty
                            delivery_time3 = line.delivery_time
                            currency_h = line.currency_id.id
                            rate_h = line.rate

                #Calculo de precio promedio
                if price_m == 0:
                    price_count = 0
                    find_lines = self.env['purchase.compared.prices.lines'].search([('product_id', '=', product_temporal)])
                    for line in find_lines:
                        price_count += line.price
                    price_count = price_count / len(find_lines)
                    find_mid_price = self.env['purchase.compared.prices.lines'].search([('product_id', '=', product_temporal), ('provider_id', 'not in', (provider_l,provider_h))], limit=1)
                    for lines in find_mid_price:
                        price_m = lines.price
                        provider_m = lines.provider_id.id
                        qtym = lines.qty
                        delivery_time2 = lines.delivery_time
                        currency_m = lines.currency_id.id
                        rate_m = lines.rate

                values ={
                    'product_id': product_temporal,
                    'provider_id1': provider_l,
                    'qty1': qtyl,
                    'delivery_time1': delivery_time1,
                    'price1': price_l,
                    'currency_id1': currency_l,
                    'rate1': rate_l,
                    'provider_id2': provider_m,
                    'qty2': qtym,
                    'delivery_time2': delivery_time2,
                    'price2': price_m,
                    'currency_id2': currency_m,
                    'rate2': rate_m,
                    'provider_id3': provider_h,
                    'qty3': qtyh,
                    'delivery_time3': delivery_time3,
                    'price3': price_h,
                    'currency_id3': currency_h,
                    'rate3': rate_h,
                    'purchase_compare_multiple_id': self.id,
                }
                self.env['purchase.compared.prices'].create(values)     