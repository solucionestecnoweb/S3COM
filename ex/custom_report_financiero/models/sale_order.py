from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
import xlwt
import base64
from datetime import datetime
from io import BytesIO
from collections import defaultdict
from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.tools import float_compare
from itertools import groupby
from dateutil.relativedelta import relativedelta
import json



class PurchaseOrder(models.Model):
    _inherit = "purchase.request"

    sale_id = fields.Many2one(
        comodel_name='sale.order', string='Pedido de venta')

    def button_to_approve(self):
        self.to_approve_allowed_check()
        self.sale_id.state = 'done_req'
        return self.write({"state": "to_approve"})


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)],'draft_req': [('readonly', False)],'done_req': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1,
        help="If you change the pricelist, only newly added lines will be affected.")

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

    state = fields.Selection([
        ('draft', 'Presupuesto'),
        ('draft_req', 'Pendiente por Requisicion'),
        ('done_req', 'Requisicion Confirmada'),
        ('sent', 'Presupuesto Enviado'),
        ('sale', 'Pedido de Venta'),
        ('done', 'Bloqueado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', readonly=True, copy=False, index=True, tracking=3, default='draft')
    line_request_ids = fields.One2many(
        'sale.request.line', 'sale_id', string='lineas de requisicion')
    resquest_id = fields.Many2one(
        comodel_name="purchase.request",
        string="Requisicion Compra",

    )
    purchase_req_count = fields.Integer(
        string="Purchases count", compute="_compute_purchase_re_count", readonly=True
    )
    date_ad = fields.Datetime(string='Fecha de adjudicacion', readonly=True)
    offer_received = fields.Boolean(string='Oferta recibida')
    offer_validity = fields.Char(string='Validez de la Oferta')
    payment_method = fields.Char(string='Metodo de pago')
    place_delivery = fields.Char(string='Lugar de Entrega')
    purchase_id = fields.Many2one(comodel_name='purchase.order', string='Compra')
    line_ids = fields.One2many('pre.sale.line', 'sale_id', string='Lineas')
    tax_totals_json_line_ids = fields.Char(compute='_compute_tax_totals_json_line_ids')
    amount_tax_line_ids = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all_line_ids')
    amount_total_line_ids = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all_line_ids')
    amount_untaxed_line_ids = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all_line_ids', tracking=True)
    
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

    @api.depends("resquest_id")
    def _compute_purchase_re_count(self):
        for rec in self:
            rec.purchase_req_count = len(rec.mapped("resquest_id"))

    def action_view_req(self):
        """
        :return dict: dictionary value for created view
        """

        return {
            "name": _("RFQ"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.request",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.resquest_id.ids)],
        }

    def create_req(self):
        if self.line_request_ids:

            resquest_id = self.env['purchase.request'].create({
                'requested_by': self.env.user.id,
                'origin': self.name,
                'sale_id': self.id

            })
            self.resquest_id = resquest_id.id
            self.state = 'draft_req'
            for line in self.line_request_ids:
                resquest_id.write({
                    'line_ids': [(0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom_id': line.product_uom_id.id,
                        'product_qty': line.product_qty,
                        'estimated_cost': line.estimated_cost,
                        'request_id': resquest_id.id,

                    })]
                })
        else:
            raise UserError(
                _("No puede crear una requisicion sin lineas de requisicion.")
            )


    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        self.date_ad = fields.Datetime.now()

        return res
    

    
    def create_offer(self):
        if self.purchase_id:
            if self.purchase_id.line_ids:
                self.offer_validity = self.purchase_id.offer_validity
                self.payment_method = self.purchase_id.payment_method
                self.place_delivery = self.purchase_id.place_delivery
                for line in self.purchase_id.line_ids:
                    self.write({
                        'line_ids': [(0, 0, {
                            'product_id': line.product_id.id,
                            'name': line.name,
                            'name_offer': line.name_offer,
                            'brand': line.brand,
                            'product_uom_id': line.product_uom_id.id,
                            'product_qty': line.product_qty,
                            'price_unit':line.price_unit,
                            'warranty': line.warranty,
                            'delivery_time': line.delivery_time,
                            'price_subtotal': line.product_qty * line.price_unit
                        })]
                    })
            else:
                raise UserError(
                _("La oferta aun no ha sido creada")
            )
    


class PreRequsitionLine(models.Model):
    _name = "pre.sale.line"

    sale_id = fields.Many2one(comodel_name='sale.order', string='Orden')
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
            'currency': self.sale_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.sale_id.partner_id,
        }



class ReportSaleOrderXlsx(models.TransientModel):

    _name = "sale.order.xlsx.report"

    name = fields.Char('Nombre')
    date_from = fields.Date('Desde')
    date_to = fields.Date('Hasta')

    def generate_report_sale_xlsx(self):

        workbook = xlwt.Workbook(encoding="utf-8")
        sheet = workbook.add_sheet("Reporte")
        today = datetime.now().date()
        file_name = "Reporte" + str(today)
        sheet.write(0, 0, 'Orden')
        sheet.write(0, 1, 'Fecha Cotizacion')
        sheet.write(0, 2, 'Mes')
        sheet.write(0, 3, 'Semestre')
        sheet.write(0, 4, 'Cliente')
        sheet.write(0, 5, 'Tipo cliente')
        sheet.write(0, 6, 'Monto Cotizacion USD')
        sheet.write(0, 7, 'Cotizacion adjudicable USD')
        sheet.write(0, 8, 'Item')
        sheet.write(0, 9, 'Categoria')
        sheet.write(0, 10, 'Validez oferta dias')
        sheet.write(0, 11, 'Plazo de entrega')
        sheet.write(0, 12, 'Fecha Entrega')
        sheet.write(0, 13, 'Fecha Cobro')

        line = 1
        
        
        order_id = self.env['sale.order'].search([('state', 'in', ['draft', 'sale']),('date_order', '>=', self.date_from),('date_order', '<=', self.date_to)])
        for order in order_id:
            for order_line in order.order_line:
                delivery_time = order.line_ids.filtered(lambda r: r.product_id == order_line.product_id).delivery_time
                date = delivery_time.strftime('%d-%m-%Y') if delivery_time else ''
                sheet.write(line, 0, order.name) 
                sheet.write(line, 1, order.date_order.strftime('%d-%m-%Y')) # Fecha
                sheet.write(line, 2, order.date_order.strftime('%m')) # Proveedor
                sheet.write(line, 3, '1' if order.date_order.month < 6 else '2') # Proveedor
                sheet.write(line, 4, order.partner_id.name) # Representante de compra
                sheet.write(line, 5, 'Individual' if order.partner_id.type =='person' else 'Compañia ')
                sheet.write(line, 6,  order.amount_total_signed_rate if order.state == 'draft' else 0)
                sheet.write(line, 7,  order.amount_total_signed_rate if order.state == 'sale' else 0)
                sheet.write(line, 8,  order_line.product_id.name)
                sheet.write(line, 9,  order_line.product_id.categ_id.name)
                sheet.write(line, 10, order.validity_date.strftime('%d')if order.validity_date else '')
                sheet.write(line, 11,  order.payment_term_id.name or '')
                sheet.write(line, 12, date)
                sheet.write(line, 13, order.payment_term_id.name or '')
                line += 1
                    

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        data_b64 = base64.encodestring(data)
        doc = self.env['ir.attachment'].create({
            'name': '%s.xls' % (file_name),
            'datas': data_b64,
            'store_fname': '%s.xls' % (file_name),
            'type': 'url'
        })
        return {
            'type': "ir.actions.act_url",
            'url': "web/content/?model=ir.attachment&id=" + str(
                doc.id) + "&filename_field=datas_fname&field=datas&download=true&filename=" + str(doc.name),
            'target': "current",
            'no_destroy': False,
        }
 
class StockRule(models.Model):
    _inherit = 'stock.rule'



    @api.model
    def _run_buy(self, procurements):
        procurements_by_po_domain = defaultdict(list)
        errors = []
        for procurement, rule in procurements:

            # Get the schedule date in order to find a valid seller
            procurement_date_planned = fields.Datetime.from_string(procurement.values['date_planned'])

            supplier = False
            if procurement.values.get('supplierinfo_id'):
                supplier = procurement.values['supplierinfo_id']
            else:
                supplier = procurement.product_id.with_company(procurement.company_id.id)._select_seller(
                    partner_id=procurement.values.get("supplierinfo_name"),
                    quantity=procurement.product_qty,
                    date=procurement_date_planned.date(),
                    uom_id=procurement.product_uom)

            # Fall back on a supplier for which no price may be defined. Not ideal, but better than
            # blocking the user.
            supplier = supplier or procurement.product_id._prepare_sellers(False).filtered(
                lambda s: not s.company_id or s.company_id == procurement.company_id
            )[:1]

            if not supplier:
                msg = _('There is no matching vendor price to generate the purchase order for product %s (no vendor defined, minimum quantity not reached, dates not valid, ...). Go on the product form and complete the list of vendors.') % (procurement.product_id.display_name)
                errors.append((procurement, msg))

            partner = supplier.name
            # we put `supplier_info` in values for extensibility purposes
            procurement.values['supplier'] = supplier
            procurement.values['propagate_cancel'] = rule.propagate_cancel

            domain = rule._make_po_get_domain(procurement.company_id, procurement.values, partner)
            procurements_by_po_domain[domain].append((procurement, rule))

        if errors:
            raise ProcurementException(errors)

        for domain, procurements_rules in procurements_by_po_domain.items():
            # Get the procurements for the current domain.
            # Get the rules for the current domain. Their only use is to create
            # the PO if it does not exist.
            procurements, rules = zip(*procurements_rules)

            # Get the set of procurement origin for the current domain.
            origins = set([p.origin for p in procurements])
            # Check if a PO exists for the current domain.
            po = self.env['purchase.order'].sudo().search([dom for dom in domain], limit=1)
            if origins:
                so = self.env['sale.order'].search([('name', '=', ', '.join(origins))], limit=1)
                so.purchase_id = po.id if so and po else False
        
            company_id = procurements[0].company_id
            if not po:
                positive_values = [p.values for p in procurements if float_compare(p.product_qty, 0.0, precision_rounding=p.product_uom.rounding) >= 0]
                if positive_values:
                    # We need a rule to generate the PO. However the rule generated
                    # the same domain for PO and the _prepare_purchase_order method
                    # should only uses the common rules's fields.
                    vals = rules[0]._prepare_purchase_order(company_id, origins, positive_values)
                    # The company_id is the same for all procurements since
                    # _make_po_get_domain add the company in the domain.
                    # We use SUPERUSER_ID since we don't want the current user to be follower of the PO.
                    # Indeed, the current user may be a user without access to Purchase, or even be a portal user.
                    po = self.env['purchase.order'].with_company(company_id).with_user(SUPERUSER_ID).create(vals)
            else:
                # If a purchase order is found, adapt its `origin` field.
                if po.origin:
                    missing_origins = origins - set(po.origin.split(', '))
                    if missing_origins:
                        po.write({'origin': po.origin + ', ' + ', '.join(missing_origins)})
                else:
                    po.write({'origin': ', '.join(origins)})

            procurements_to_merge = self._get_procurements_to_merge(procurements)
            procurements = self._merge_procurements(procurements_to_merge)

            po_lines_by_product = {}
            grouped_po_lines = groupby(po.order_line.filtered(lambda l: not l.display_type and l.product_uom == l.product_id.uom_po_id).sorted(lambda l: l.product_id.id), key=lambda l: l.product_id.id)
            for product, po_lines in grouped_po_lines:
                po_lines_by_product[product] = self.env['purchase.order.line'].concat(*list(po_lines))
            po_line_values = []
            for procurement in procurements:
                po_lines = po_lines_by_product.get(procurement.product_id.id, self.env['purchase.order.line'])
                po_line = po_lines._find_candidate(*procurement)

                if po_line:
                    # If the procurement can be merge in an existing line. Directly
                    # write the new values on it.
                    vals = self._update_purchase_order_line(procurement.product_id,
                        procurement.product_qty, procurement.product_uom, company_id,
                        procurement.values, po_line)
                    po_line.write(vals)
                else:
                    if float_compare(procurement.product_qty, 0, precision_rounding=procurement.product_uom.rounding) <= 0:
                        # If procurement contains negative quantity, don't create a new line that would contain negative qty
                        continue
                    # If it does not exist a PO line for current procurement.
                    # Generate the create values for it and add it to a list in
                    # order to create it in batch.
                    partner = procurement.values['supplier'].name
                    po_line_values.append(self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
                        procurement.product_id, procurement.product_qty,
                        procurement.product_uom, procurement.company_id,
                        procurement.values, po))
                    # Check if we need to advance the order date for the new line
                    order_date_planned = procurement.values['date_planned'] - relativedelta(
                        days=procurement.values['supplier'].delay)
                    if fields.Date.to_date(order_date_planned) < fields.Date.to_date(po.date_order):
                        po.date_order = order_date_planned
            self.env['purchase.order.line'].sudo().create(po_line_values)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    guarantee = fields.Char(string="Garantia")
    delivery_time = fields.Date(string="Tiempo de entrega")
    brand = fields.Char(string="Marca", related='product_id.marca_comercial.name')
        


class PurchaseRequestLine(models.Model):

    _name = "sale.request.line"

    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    @api.model
    def _default_picking_type(self):
        type_obj = self.env["stock.picking.type"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        types = type_obj.search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id)]
        )
        if not types:
            types = type_obj.search(
                [("code", "=", "incoming"), ("warehouse_id", "=", False)]
            )
        return types[:1]

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Producto",
        domain=[("purchase_ok", "=", True)],
        tracking=True,
    )
    name = fields.Char(string="Descripcion", tracking=True, required=True)
    product_uom_category_id = fields.Many2one(
        related="product_id.uom_id.category_id")
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UdM",
        tracking=True,
        domain="[('category_id', '=', product_uom_category_id)]",
    )
    product_qty = fields.Float(
        string="Cantidad", tracking=True, digits="Product Unit of Measure", required=True,
    )
    sale_id = fields.Many2one(
        comodel_name="sale.order",
        string="orden de venta",
        ondelete="cascade",
        readonly=True,
        index=True,
        auto_join=True,
    )
    estimated_cost = fields.Monetary(
        currency_field="currency_id",
        string="Costo Estimado",
        default=0.0,
        help="Estimated cost of Purchase Request Line, not propagated to PO.",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="sale_id.company_id",
        string="Company",
        store=True,
    )
    resquest_id = fields.Many2one(
        comodel_name="purchase.request",
        string="Requisicion Compra",

    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = "[{}] {}".format(self.product_id.code, name)
            if self.product_id.description_purchase:
                name += "\n" + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name
