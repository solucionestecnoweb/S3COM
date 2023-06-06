# -*- coding: utf-8 -*-

from odoo import api, fields, models
from random import randint


class ResPartner(models.Model):
    _inherit = "res.partner"
    
    comercial_designation = fields.Many2one('comercial.designation', string='Denominación Comercial')
    commercial_references = fields.Binary(string="Referencias Comerciales")
    bank_references = fields.Binary(string='Referencias Bancarias')
    guarantee = fields.Char(string='Garantías')
    # categ_supplier_type = fields.Selection([
    #     ('1', 'Electromecánica y maquinaria'),
    #     ('2', 'Ferretería, plomería y filtros de agua'),
    #     ('3', 'Materiales para el agro y fumigación'),
    #     ('4', 'Artículos de seguridad'),
    #     ('5', 'Mobiliario equipos suministros y mobiliario'),
    #     ('6', 'Artículos de limpieza, higiene y antiséptico'),
    #     ('7', 'Enseres del hogar, uniformes y textiles'),
    #     ('8', 'Cuidado integral para la salud'),
    #     ('9', 'Energía (eléctrica y solar)'),
    #     ('10', 'Electrónica y equipos de Computación, sistemas de seguridad, impresoras y consumibles'),
    #     ('11', 'Papelería, material POP, visibilidad y artículos de oficina'),
    #     ('12', 'Material de embalaje y empaquetado'),
    #     ('13', 'Multipropósito (Campo para registrar varias categorías del Proveedor) otros.')

    # ], 'Categoria del proveedor')  
    category_customer_ids = fields.Many2many(comodel_name='categ.customer.type', string='Categoria de cliente')
    
    responsible = fields.Many2one('res.users', string='Responsable')
    president = fields.Char(string="Presidente")
    supplier_code = fields.Char(string="Código del Proveedor")
    opening_date = fields.Date(string="Fecha de Apertura")
    registered_by = fields.Char(string='Registrado por')
    document_number = fields.Char(string='Cedula del Representante legal')
    tax_payer  = fields.Char(string='Grupo Contribuyente')
    commercial_registry_date = fields.Date(string='Fecha mercantil')
    commercial_registry = fields.Char(string='Registro mercantil')
    days = fields.Char('Días')
    weeks = fields.Char('Semanas')
    months = fields.Char('Meses')
    linkedin = fields.Char('Linkedin')
    contact_person = fields.Char('Persona Contacto')
    attention_hours = fields.Char(string='Horario de atención')
    search_channel = fields.Char('Canal de busqueda')
    description_product = fields.Char('Descripcion del producto o servicio')
    warehouse_address  = fields.Char('Dirección de Almacén o Planta')
    bank_instruments = fields.Char('Instrumentos Bancarios para el pago')
    process_certification = fields.Char('Certificación del Proceso')
    product_certification = fields.Char('Certificación del Producto')
    doc_type = fields.Selection([('v', 'V'), ('e', 'E'), ('j', 'J'), ('g', 'G'), ('p', 'P'), ('c', 'C'), ('SFL', 'SFL'),],
                                required=True, default='v')
    
class ComercialDesignation(models.Model):
    _name = "comercial.designation"
    
    name = fields.Char(string='Nombre')
    
class CategCustomerType(models.Model):
    _name = 'categ.customer.type'


    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Nombre', required=True, translate=True)
    color = fields.Integer(string='Color', default=_get_default_color)