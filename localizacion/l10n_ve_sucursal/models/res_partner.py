# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
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

    #_sql_constraints = [('unique_vat', 'unique(vat)', 'Ya existe este documento registrado')]
    _sql_constraints = [('unique_vat', 'Check(1=1)', 'pasa')]
