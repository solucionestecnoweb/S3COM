# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from itertools import product
import json
from datetime import datetime, timedelta
import base64
from io import StringIO
from odoo import api, fields, models
from datetime import date
from odoo.tools.float_utils import float_round
from odoo.exceptions import Warning

import time

class ProductProduct(models.Model):
	_inherit = "product.product"

	# @api.onchange('modelo','iva','type_cauchos','tarps','load_speed','service_in','filler','brand_id','group_id','qty_hq','deote')
	# def values_onchange(self):
	# 	self.update_values()

	# @api.constrains('modelo','iva','type_cauchos','tarps','load_speed','service_in','filler','brand_id','group_id','qty_hq','deote')
	# def values_constrains(self):
	# 	self.update_values()

	# def update_values(self):
	# 	product = self.env['product.template'].search([('id', '=', self.product_tmpl_id.id)], limit=1)
	# 	product.modelo = self.modelo
	# 	product.iva = self.iva
	# 	product.type_cauchos = self.type_cauchos
	# 	product.tarps = self.tarps
	# 	product.load_speed = self.load_speed
	# 	product.service_in = self.service_in
	# 	product.filler = self.filler
	# 	product.brand_id = self.brand_id.id
	# 	product.group_id = self.group_id.id
	# 	product.qty_hq = self.qty_hq
	# 	product.deote = self.deote

	modelo = fields.Char(string='Modelo')
	iva = fields.Char(string='I.V.A.')
	type_cauchos = fields.Char(string='Tipo de Caucho')
	tarps = fields.Char(string='Lonas')
	load_speed = fields.Char(string='Load/Speed')
	service_in = fields.Char(string='Service Index')
	filler = fields.Float(string='Nro. Filler', digits=(12, 4))
	brand_id = fields.Many2one('product.brand', string='Marca')
	group_id = fields.Many2one('product.group', string='Grupo')
	qty_hq = fields.Char(string='Qty Of 40HQ')
	deote = fields.Date(string='Fecha de Fabricación')
	rin = fields.Float(string='Rin')
	medidas = fields.Char(string='Medidas')
	construction_type = fields.Selection(string='Tipo de Construcción', selection=[('c', 'C'), ('r', 'R'),])
	stock_inicial = fields.Float(string='Stock Inicial', compute='compute_stock_inicial', store=True)
	no_despachado = fields.Float(string='No Despachado', compute='compute_no_despachado', store=True)
	tier = fields.Selection(string='TIER', selection=[('1', 'TIER-1'), ('2', 'TIER-2'), ('3', 'TIER-3'), ('4', 'TIER-4'), ('5', 'TIER-5')])
	clase = fields.Char(string='Clase', size=6)

	def compute_stock_inicial(self):
		for item in self:
			item.stock_inicial = 0
			item.ver_kardex()
			xdate = datetime.now().month
			xdate = str(datetime.now().year) + '-' + str(xdate) + '-01' 
			xfind = item.env['product.product.kardex.line'].search([('name', '=', item.id), ('fecha', '<', xdate)], limit=1, order='fecha desc, id desc')
			if len(xfind) == 0:
				xdate = datetime.now().month + 1
				years = datetime.now().year
				if xdate == 13:
					xdate = 1
					years += 1
				xdate = str(years) + '-' + str(xdate) + '-01' 
				xfind = item.env['product.product.kardex.line'].search([('name', '=', item.id), ('fecha', '<', xdate)], limit=1, order='fecha asc, id asc')
			if xfind:
				item.stock_inicial = xfind[0].total

	def compute_no_despachado(self):
		for item in self:
			item.no_despachado = 0
			xfind = item.env['stock.picking'].search([
				('product_id', '=', item.id),
				('picking_type_id.code', '=', 'outgoing'),
				('location_dest_id.usage', '=', 'customer'),
				('state','in',('waiting', 'confirmed', 'assigned'))
			])
			for line in xfind.move_ids_without_package:
				item.no_despachado += line.product_uom_qty

	
class ProductTemplate(models.Model):
	_inherit = "product.template"

	modelo = fields.Char(string='Modelo')
	iva = fields.Char(string='I.V.A.')
	type_cauchos = fields.Char(string='Tipo de Caucho')
	tarps = fields.Char(string='Lonas')
	load_speed = fields.Char(string='Load/Speed')
	service_in = fields.Char(string='Service Index')
	filler = fields.Float(string='Nro. Filler', digits=(12, 4))
	brand_id = fields.Many2one('product.brand', string='Marca')
	group_id = fields.Many2one('product.group', string='Grupo')
	qty_hq = fields.Char(string='Qty Of 40HQ')
	deote = fields.Date(string='Fecha de Fabricación')
	rin = fields.Float(string='Rin')
	medidas = fields.Char(string='Medidas')
	construction_type = fields.Selection(string='Tipo de Construcción', selection=[('c', 'C'), ('r', 'R'),])
	tier = fields.Selection(string='TIER', selection=[('1', 'TIER-1'), ('2', 'TIER-2'), ('3', 'TIER-3'), ('4', 'TIER-4'), ('5', 'TIER-5')])
	clase = fields.Char(string='Clase', size=6)

	# @api.onchange('modelo','iva','type_cauchos','tarps','load_speed','service_in','filler','brand_id','group_id','qty_hq','deote')
	# def values_onchange(self):
	# 	self.update_values()

	# @api.constrains('modelo','iva','type_cauchos','tarps','load_speed','service_in','filler','brand_id','group_id','qty_hq','deote')
	# def values_constrains(self):
	# 	self.update_values()
	
	def _create_variant_ids(self):
		res = super(ProductTemplate, self)._create_variant_ids()

		for item in self.product_variant_ids:
			product = item
			product.modelo = self.modelo
			product.iva = self.iva
			product.type_cauchos = self.type_cauchos
			product.tarps = self.tarps
			product.load_speed = self.load_speed
			product.service_in = self.service_in
			product.filler = self.filler
			product.brand_id = self.brand_id.id
			product.group_id = self.group_id.id
			product.qty_hq = self.qty_hq
			product.deote = self.deote
			product.rin = self.rin
			product.medidas = self.medidas
			product.construction_type = self.construction_type
			product.tier = self.tier
			product.clase = self.clase

		return res

	@api.constrains('modelo','iva','type_cauchos','tarps','load_speed','service_in','filler','brand_id','group_id','qty_hq','deote', 'rin', 'medidas', 'construction_type', 'stock_inicial', 'no_despachado', 'tier', 'clase')
	def update_products(self):

		for item in self.product_variant_ids:
			product = item
			product.modelo = self.modelo
			product.iva = self.iva
			product.type_cauchos = self.type_cauchos
			product.tarps = self.tarps
			product.load_speed = self.load_speed
			product.service_in = self.service_in
			product.filler = self.filler
			product.brand_id = self.brand_id.id
			product.group_id = self.group_id.id
			product.qty_hq = self.qty_hq
			product.deote = self.deote
			product.rin = self.rin
			product.medidas = self.medidas
			product.construction_type = self.construction_type
			product.tier = self.tier
			product.clase = self.clase

class MarcasProductos(models.Model):
	_name = 'product.brand'

	name = fields.Char(string='Nombre')

class GruposProductos(models.Model):
	_name = 'product.group'

	name = fields.Char(string='Nombre')

class InventarioProductos(models.Model):
	_inherit = "stock.picking"

	filler_per = fields.Float(string='Filler Facturado (%)', compute='_compute_filler_per')
	situacion = fields.Selection(string='Situación', selection=[('Apartado', 'Apartado'), ('Analisis', 'Análisis'),], track_visibility='onchange')
	entregado = fields.Boolean(string='¿Entregado?', track_visibility='onchange')
	
	def change_situacion_apartado(self):
		self.situacion = 'Apartado'

	def change_situacion_analisis(self):
		self.situacion = 'Analisis'

	def _compute_filler_per(self):
		for item in self:
			item.filler_per = 0
			filler = 0
			for line in item.move_ids_without_package:
				filler += (line.quantity_done * line.product_id.filler)
				item.filler_per = filler

	def get_product_price(self, origen, producto):
		if origen:
			pedido = self.env['sale.order'].search([('name', '=', origen)])
			for line in pedido.order_line:
				if line.product_id.id == producto:
					iva = 0
					if line.tax_id:
						iva = (line.tax_id[0].amount * line.price_unit) / 100
					monto = line.price_unit + iva
					descuento = (monto * line.discount) / 100 
					precio = (monto - descuento) * pedido.rate
					return precio
		else:
			return False

class AutomaticLot(models.Model):
	_inherit = 'stock.quant'

	@api.onchange('location_id','inventory_quantity')
	def _onchange_location_id(self):
		if not self.lot_id and self.inventory_quantity > 0:
			value = {
				'product_id': self.product_id.id,
				'company_id': self.env['res.company']._company_default_get('stock.quant').id,
				'product_qty': self.inventory_quantity
			}
			self.lot_id = self.env['stock.production.lot'].create(value)

class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'

	analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Cuenta analítica')