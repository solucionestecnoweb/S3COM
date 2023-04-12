# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
import PyCNE
_logger = logging.getLogger('__name__')


class Partner(models.Model):
    _inherit = "res.partner"

    taxpayer = fields.Selection([('True', 'Si'), ('False', 'No')], required='True', default='True')
    people_type = fields.Selection([
        ('na', 'N/A'),
        ('resident_nat_people', 'PNRE Residente Natural Person'),
        ('non_resit_nat_people', 'PNNR Non-resident Natural Person'),
        ('domi_ledal_entity', 'PJDO Domiciled Legal Entity'),
        ('legal_ent_not_domicilied', 'PJDO Legal Entity Not Domiciled')],
        string='People type', required="True", default='na')
    doc_type = fields.Selection([('v', 'V'), ('e', 'E'), ('j', 'J'), ('g', 'G'), ('p', 'P'), ('c', 'C')],
                                required=True, default='v')
    seniat_url = fields.Char(string='GO SENIAT', readonly="True",
                             default="http://contribuyente.seniat.gob.ve/BuscaRif/BuscaRif.jsp")
    vendor = fields.Selection([('national', 'National'), ('international', 'International')],
                              required=True, default='national')
    facebook = fields.Char(string='Facebook')
    twitter = fields.Char(string='Twitter')
    skype = fields.Char(string='Skype')
    linkedin = fields.Char(string='Linkedin')
    mastodon = fields.Char(string='Mastodon')
    discord = fields.Char(string='Discord')
    reddit = fields.Char(string='Reddit')
    forum = fields.Char(string='Forum')
    youtube = fields.Char(string='Youtube')

    def get_record_partner_cne(self):
        for partner in self:
            try:
                response = PyCNE.consulta('V', int(partner.vat))
                res = response.info.get('cedula', False)
                if res:
                    partner.message_post(
                        body=(
                            'Datos Consultados CNE:<br/>'
                            '<ul>'
                            '<li> <strong>Nombre: </strong> <span>{0}</span></li>'
                            '<li> <strong>Cedula :</strong> <span>{1}</span></li>'
                            '<li> <strong>Estado: </strong> <span>{2}</span></li>'
                            '<li> <strong>Municipio: </strong> <span>{3}</span></li>'
                            '<li> <strong>Parroquia: </strong> <span>{4}</span></li>'
                            '<li> <strong>Centro de Votacion: </strong> <span>{5}</span></li>'
                            '</ul>.'.format(
                                response.info.get('nombre'),
                                response.info.get('cedula'),
                                response.info.get('estado'),
                                response.info.get('municipio'),
                                response.info.get('parroquia'),
                                response.info.get('centro'),
                            )
                        )
                    )
            except:
                pass
        return True
