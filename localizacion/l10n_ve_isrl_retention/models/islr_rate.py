# -*- coding: utf-8 -*-
from odoo import fields, models


class IslrRate(models.Model):
    _name = 'islr.rate'
    _description = " Isrl Rate"

    name = fields.Char(string='Rate')
    code = fields.Char(string='Cod. Concepto', size=3, required=True, help="Concept code")
    subtotal = fields.Float('No tax amount', required=True, digits='Retention ISLR',
                            help=" '%' of the amount on which to apply the retention")
    min = fields.Float('Minimum Amount', required=True, digits='Retention ISLR',
                       help="Minimum amount,  from which it will determine whether you" "withholded")
    retention_percentage = fields.Float('Cantidad %', required=True, digits='Retention ISLR',
                                        help="The percentage to apply to taxable withold income throw the"
                                             " amount to withhold")
    subtract = fields.Float(string='Subtraendos', digits='Retention ISLR', required=True)
    concept_id = fields.Many2one('islr.concept', 'Retention  Concept', ondelete='cascade',
                                 help="Retention concept associated with this rate")

    rate2 = fields.Boolean('Rate 2', help='Rate Used for Foreign Entities')
    people_type = fields.Selection(string='Tipo Persona', selection=[
        ('resident_nat_people', 'PNRE'),
        ('non_resit_nat_people', 'PNNR'),
        ('domi_ledal_entity', 'PJDO'),
        ('legal_ent_not_domicilied', 'PJND'),
        ('legal_entity_not_incorporated', 'PJNCD'),
    ])
    natural_person = fields.Boolean(string='Persona Natural')
    residence = fields.Boolean(string='Residente')

    def name_get(self):
        """ The _rec_name class attribute is replaced to concatenate several fields of the object
            :return list: the concatenation of the new _rec_name
        """
        res = [(r.id, '[{}]'.format(r.code or 'S/N')) for r in self]
        return res
