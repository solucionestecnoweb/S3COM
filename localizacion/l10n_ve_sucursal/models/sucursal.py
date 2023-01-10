# -*- coding: utf-8 -*-

from odoo import fields, models, api


class Sucursal(models.Model):
    _name = "res.sucursal"

    name = fields.Char('Nombre')
    code = fields.Char('codigo')
    address = fields.Text('Direccion')
    active = fields.Boolean(string='Activo', default=True)
    company_id = fields.Many2one('res.company')

    def name_get(self):
        """ The _rec_name class attribute is replaced to concatenate several fields of the object
            :return list: the concatenation of the new _rec_name
        """
        res = [(r.id, '[{}] {}'.format(r.code or 'S/N', r.name)) for r in self]
        return res

    @api.model
    def create(self, vals):
        """
        This method is create for sequence wise name.
        :param vals: values
        :return:super
        """
        res = super(Sucursal, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code('code.res.sucursal')
        return res
