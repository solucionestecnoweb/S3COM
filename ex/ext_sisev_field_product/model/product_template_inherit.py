# -*- coding: utf-8 -*-


import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError




class Productos(models.Model):
    _inherit = 'product.template'

    #sublineas=fields.Char(string="Sub Lineas")
    #modelo_id = fields.Many2one('stock.modelo')
   

    #tipo_id = fields.Many2one('stock.tipo')
    

   
    #forma_id = fields.Many2one('stock.forma')

    #color=fields.Many2one('stock.color',string="Color")

    #formato=fields.Many2one('stock.formato',string="Formato")

    #uso=fields.Many2one('stock.uso',string="Uso")
    #material=fields.Many2one('stock.material',string="Material")
    marca_comercial=fields.Many2one('stock.marca',string="Marca")
    #calidad=fields.Many2one('stock.calidad',string="Calidad")

 
    #uni_neg_id = fields.Many2one('stock.unidad.negocio')

"""class ModeloStock(models.Model):
    _name = 'stock.modelo'

    name=fields.Char()

class TipoStock(models.Model):
    _name = 'stock.tipo'

    name=fields.Char()

class TipoStock(models.Model):
    _name = 'stock.forma'

    name=fields.Char()

class ColorStock(models.Model):
    _name = 'stock.color'

    name=fields.Char()

class FormatoStock(models.Model):
    _name = 'stock.formato'

    name=fields.Char()

class UsoStock(models.Model):
    _name = 'stock.uso'

    name=fields.Char()

class MaterialStock(models.Model):
    _name = 'stock.material'

    name=fields.Char()"""


class marcaStock(models.Model):
    _name = 'stock.marca'

    name=fields.Char()

"""class CalidadStock(models.Model):
    _name = 'stock.calidad'

    name=fields.Char()

class UnidadNegocioStock(models.Model):
    _name = 'stock.unidad.negocio'

    name=fields.Char()"""
        