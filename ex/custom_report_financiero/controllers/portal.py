
from odoo import http
from odoo.http import request
from odoo.http import Controller, request, route
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.addons.portal.controllers.portal import CustomerPortal

class PreFormCustomerPortal(CustomerPortal):

    @http.route(['/my/pre/<int:id>'], type='http', auth="public", website=True)
    def portal_my_pre_form(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        pre_id = request.env['purchase.order'].sudo().search([('id', '=', kw['id'])], limit=1),
        records_lines = [{'product': line.product_id.name,
                            'product_id': line.product_id.id,
                            'name': line.name,
                            'product_uom_id': line.product_uom.id,
                            'product_uom': line.product_uom.name,
                            'product_qty': line.product_qty,
                            'price_total': line.price_subtotal,
                            'id': line.id
                   
        
        
         } for line in pre_id[0].order_line]
        values = {
            'id': kw['id'],
            'offer_received': pre_id[0].offer_received,
            'name': pre_id[0].name,
            'partner_id': pre_id[0].partner_id.name,
            'records_lines': records_lines
           
        }
        return request.render(" .tmp_pre_form_data", values)



    @http.route(['/asociate_offen'], type='http', auth="public", methods=['GET', 'POST'],  website=True, csrf=False)
    def create_offen(self, redirect=None, **kwargs,):
        po = request.env['purchase.order'].sudo().search([('id', '=', kwargs['id'])], limit=1),
        for line in po[0].order_line:
            product_id = 'product' + str(line.id)
            descripcion = 'descripcion' + str(line.id)
            brand = 'brand' + str(line.id)
            product_uom_id = 'product_uom_id' + str(line.id)
            product_qty = 'product_qty' + str(line.id)
            price_unit = 'price_unit' + str(line.id)
            warranty = 'warranty' + str(line.id)
            delivery_time = 'delivery_time' + str(line.id)
            date = datetime.strptime(kwargs[delivery_time], '%Y-%m-%d').date()
            po[0].offer_validity = kwargs['offer_validity']
            po[0].payment_method = kwargs['payment_method']
            po[0].place_delivery = kwargs['place_delivery']
            po[0].offer_received = True
            po[0].write({
                'line_ids': [(0, 0, {
                    'product_id': int(kwargs[product_id]),
                    'name': line.name,
                    'name_offer': kwargs[descripcion],
                    'brand': kwargs[brand],
                    'product_uom_id': kwargs[product_uom_id],
                    'product_qty': float(kwargs[product_qty]),
                    'price_unit': float(kwargs[price_unit]),
                    'warranty': kwargs[warranty],
                    'delivery_time': date,
                    'price_subtotal': float(kwargs[product_qty]) * float(kwargs[price_unit])
                })]
            })
      

       
        return request.render("custom_report_financiero.tmp_pre_form_data_success", {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Registro Enviado con Exito',
                    'type': 'rainbow_man',
                }
            })
    

