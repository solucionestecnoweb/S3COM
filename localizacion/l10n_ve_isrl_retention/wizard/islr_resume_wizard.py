from odoo import fields, models
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class IslrResumeWizard(models.TransientModel):
    _name = 'islr.resume.wizard'
    _description = 'Resume'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    from_date = fields.Date(string='Date From', default=lambda *a: datetime.now().strftime('%Y-%m-%d'))
    to_date = fields.Date('Date To', default=lambda *a: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
    resident_nat_people = fields.Boolean(string='PNRE', default=True)
    non_resit_nat_people = fields.Boolean(string='PNNR', default=True)
    domi_ledal_entity = fields.Boolean(string='PJDO', default=True)
    legal_ent_not_domicilied = fields.Boolean(string='PJND', default=True)
    legal_entity_not_incorporated = fields.Boolean(string='PJNCD', default=True)

    def get_non_resit_nat_people(self):
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query = """
            SELECT
                islr.id,
                r.people_type,
                r.code,
                islr.isrl_date,
                islr.move_date,
                islr.invoice_number_next,
                islr.invoice_number_control,
                islr.invoice_number_unique,
                islr.amount_total_retention,
                islr.amount_total_signed,
                islr.move_id,
                co.name AS concept,
                line.base,
                line.qty,
                partner.name,
                partner.doc_type,
                partner.vat
            from isrl_retention AS islr
            INNER JOIN isrl_retention_line AS line
            ON islr.id = line.retention_id
            INNER JOIN islr_concept AS co
            ON line.islr_concept_id = co.id
            INNER JOIN islr_rate AS r
            ON co.id = r.concept_id
            INNER JOIN res_partner AS partner
            ON islr.partner_id = partner.id
            WHERE islr.isrl_date BETWEEN '%s' AND '%s'
            AND islr.move_type in ('in_invoice', 'in_refund')
            AND islr.state = 'done'
            AND r.code = line.code
            AND r.people_type = 'non_resit_nat_people'
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        for q in obj_query:
            q['amount_total_signed'] = abs(q['amount_total_signed'])
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'get_islr_arc',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return obj_query

    def get_resident_nat_people(self):
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query = """
            SELECT
                islr.id,
                r.people_type,
                r.code,
                islr.isrl_date,
                islr.move_date,
                islr.invoice_number_next,
                islr.invoice_number_control,
                islr.invoice_number_unique,
                islr.amount_total_retention,
                islr.amount_total_signed,
                islr.move_id,
                co.name AS concept,
                line.base,
                line.qty,
                partner.name,
                partner.doc_type,
                partner.vat
            from isrl_retention AS islr
            INNER JOIN isrl_retention_line AS line
            ON islr.id = line.retention_id
            INNER JOIN islr_concept AS co
            ON line.islr_concept_id = co.id
            INNER JOIN islr_rate AS r
            ON co.id = r.concept_id
            INNER JOIN res_partner AS partner
            ON islr.partner_id = partner.id
            WHERE islr.isrl_date BETWEEN '%s' AND '%s'
            AND islr.move_type in ('in_invoice', 'in_refund')
            AND islr.state = 'done'
            and r.code = line.code
            and r.people_type = 'resident_nat_people'
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        for q in obj_query:
            q['amount_total_signed'] = abs(q['amount_total_signed'])
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'get_islr_arc',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return obj_query

    def get_domi_ledal_entity(self):
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query = """
            SELECT
                islr.id,
                r.people_type,
                r.code,
                islr.isrl_date,
                islr.move_date,
                islr.invoice_number_next,
                islr.invoice_number_control,
                islr.invoice_number_unique,
                islr.amount_total_retention,
                islr.amount_total_signed,
                islr.move_id,
                co.name AS concept,
                line.base,
                line.qty,
                partner.name,
                partner.doc_type,
                partner.vat
            from isrl_retention AS islr
            INNER JOIN isrl_retention_line AS line
            ON islr.id = line.retention_id
            INNER JOIN islr_concept AS co
            ON line.islr_concept_id = co.id
            INNER JOIN islr_rate AS r
            ON co.id = r.concept_id
            INNER JOIN res_partner AS partner
            ON islr.partner_id = partner.id
            WHERE islr.isrl_date BETWEEN '%s' AND '%s'
            AND islr.move_type in ('in_invoice', 'in_refund')
            AND islr.state = 'done'
            AND r.code = line.code
            AND r.people_type = 'domi_ledal_entity'
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        for q in obj_query:
            q['amount_total_signed'] = abs(q['amount_total_signed'])
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'get_islr_arc',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return obj_query

    def get_legal_ent_not_domicilied(self):
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query = """
            SELECT
                islr.id,
                r.people_type,
                r.code,
                islr.isrl_date,
                islr.move_date,
                islr.invoice_number_next,
                islr.invoice_number_control,
                islr.invoice_number_unique,
                islr.amount_total_retention,
                islr.amount_total_signed,
                islr.move_id,
                co.name AS concept,
                line.base,
                line.qty,
                partner.name,
                partner.doc_type,
                partner.vat
            from isrl_retention AS islr
            INNER JOIN isrl_retention_line AS line
            ON islr.id = line.retention_id
            INNER JOIN islr_concept AS co
            ON line.islr_concept_id = co.id
            INNER JOIN islr_rate AS r
            ON co.id = r.concept_id
            INNER JOIN res_partner AS partner
            ON islr.partner_id = partner.id
            WHERE islr.isrl_date BETWEEN '%s' AND '%s'
            AND islr.move_type in ('in_invoice', 'in_refund')
            AND islr.state = 'done'
            AND r.code = line.code
            AND r.people_type = 'legal_ent_not_domicilied'
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        for q in obj_query:
            q['amount_total_signed'] = abs(q['amount_total_signed'])
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'get_islr_arc',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return obj_query

    def get_legal_entity_not_incorporated(self):
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query = """
            SELECT
                islr.id,
                r.people_type,
                r.code,
                islr.isrl_date,
                islr.move_date,
                islr.invoice_number_next,
                islr.invoice_number_control,
                islr.invoice_number_unique,
                islr.amount_total_retention,
                islr.amount_total_signed,
                islr.move_id,
                co.name AS concept,
                line.base,
                line.qty,
                partner.name,
                partner.doc_type,
                partner.vat
            from isrl_retention AS islr
            INNER JOIN isrl_retention_line AS line
            ON islr.id = line.retention_id
            INNER JOIN islr_concept AS co
            ON line.islr_concept_id = co.id
            INNER JOIN islr_rate AS r
            ON co.id = r.concept_id
            INNER JOIN res_partner AS partner
            ON islr.partner_id = partner.id
            WHERE islr.isrl_date BETWEEN '%s' AND '%s'
            AND islr.move_type in ('in_invoice', 'in_refund')
            AND islr.state = 'done'
            AND r.code = line.code
            AND r.people_type = 'legal_entity_not_incorporated'
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        for q in obj_query:
            q['amount_total_signed'] = abs(q['amount_total_signed'])
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'get_islr_arc',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return obj_query

    def print_report(self):
        return self.env.ref('l10n_ve_isrl_retention.action_islr_retention_resume_report').report_action(self)
